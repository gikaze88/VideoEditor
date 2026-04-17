"""
Gestion asynchrone des jobs avec ThreadPoolExecutor.
max_workers=1 → un seul job en cours à la fois (usage personnel).
Les jobs continuent même si le client se déconnecte.
"""
import json
import uuid
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ..database import get_connection
from ..config import OUTPUTS_DIR
from . import pipelines
from . import youtube as yt_service


executor = ThreadPoolExecutor(max_workers=1)


def create_job(style: str, title: str | None = None) -> dict:
    job_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()

    output_dir = OUTPUTS_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = str(output_dir / "job.log")

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO jobs
               (id, style, title, status, created_at, output_dir, log_file)
               VALUES (?, ?, ?, 'pending', ?, ?, ?)""",
            (job_id, style, title, now, str(output_dir), log_file),
        )
        conn.commit()

    return {"id": job_id, "output_dir": str(output_dir), "log_file": log_file}


def submit_job(job_id: str, style: str, params: dict):
    """Soumet un job dans le ThreadPoolExecutor (non-bloquant)."""
    executor.submit(_run_job, job_id, style, params)


def _run_job(job_id: str, style: str, params: dict):
    """Exécuté dans un thread séparé."""
    now = datetime.datetime.utcnow().isoformat()

    # Marquer running
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status='running', started_at=? WHERE id=?",
            (now, job_id),
        )
        conn.commit()

    # Récupérer les chemins
    with get_connection() as conn:
        row = conn.execute(
            "SELECT output_dir, log_file, title FROM jobs WHERE id=?", (job_id,)
        ).fetchone()

    output_dir = Path(row["output_dir"])
    log_path = Path(row["log_file"])

    # Injecter le titre dans params pour que les pipelines puissent nommer leur sortie
    if row["title"] and "title" not in params:
        params = {**params, "title": row["title"]}

    try:
        # Ouvrir le log
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"=== Job {job_id} — style={style} ===\n")
            log.write(f"Démarré à: {now}\n")
            log.write(f"Params: {params}\n\n")

        # Dispatcher vers le bon pipeline
        output_video = _dispatch(style, job_id, params, output_dir, log_path)

        # Succès
        done = datetime.datetime.utcnow().isoformat()
        with get_connection() as conn:
            conn.execute(
                """UPDATE jobs
                   SET status='completed', completed_at=?, output_video_path=?
                   WHERE id=?""",
                (done, str(output_video), job_id),
            )
            conn.commit()

        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n=== TERMINÉ à {done} ===\n")
            log.write(f"Output: {output_video}\n")

        # Auto-upload YouTube si configuré
        _maybe_auto_upload(job_id, output_video, log_path)

    except Exception as exc:
        err = str(exc)
        done = datetime.datetime.utcnow().isoformat()
        with get_connection() as conn:
            conn.execute(
                """UPDATE jobs
                   SET status='failed', completed_at=?, error_message=?
                   WHERE id=?""",
                (done, err, job_id),
            )
            conn.commit()

        try:
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"\n=== ERREUR à {done} ===\n{err}\n")
        except Exception:
            pass


def _maybe_auto_upload(job_id: str, output_video: Path, log_path: Path) -> None:
    """Déclenche l'upload YouTube automatique si youtube_params est configuré."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT youtube_params FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        yt_params_json = row["youtube_params"] if row else None
        if not yt_params_json:
            return
        yt_params = json.loads(yt_params_json)
        if not yt_params.get("auto_upload"):
            return
        if not yt_service.is_authenticated():
            with open(log_path, "a", encoding="utf-8") as log:
                log.write("[YT] Auto-upload ignore : non authentifie YouTube.\n")
            return

        # Préférer le fichier overlay si disponible (débat, etc.)
        video_path = _resolve_best_video(output_video)

        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"[YT] Demarrage auto-upload : {video_path.name}\n")

        _auto_upload_youtube(job_id, video_path, yt_params, log_path)

    except Exception as exc:
        try:
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"[YT] Erreur auto-upload : {exc}\n")
        except Exception:
            pass


def _resolve_best_video(output_video: Path) -> Path:
    """Retourne le fichier overlay s'il existe dans le même dossier, sinon output_video."""
    output_dir = output_video.parent
    overlay_files = sorted(output_dir.glob("*overlay*"))
    if overlay_files:
        return overlay_files[0]
    return output_video


def _auto_upload_youtube(job_id: str, video_path: Path, yt_params: dict, log_path: Path) -> None:
    """Lance l'upload YouTube et met à jour le statut en base."""
    def log_cb(msg: str) -> None:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[YT] {msg}\n")
        except Exception:
            pass

    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET youtube_status='uploading' WHERE id=?", (job_id,)
        )
        conn.commit()

    try:
        tags_raw = yt_params.get("tags", "")
        tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]

        video_id = yt_service.upload_video(
            video_path=video_path,
            title=yt_params.get("title", ""),
            description=yt_params.get("description", ""),
            tags=tags_list,
            privacy=yt_params.get("privacy", "private"),
            category_id=yt_params.get("category_id", "25"),
            language=yt_params.get("language", "fr"),
            license_type=yt_params.get("license", "youtube"),
            embeddable=yt_params.get("embeddable", True),
            playlist_id=yt_params.get("playlist_id") or None,
            log_callback=log_cb,
        )

        with get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET youtube_video_id=?, youtube_status='uploaded' WHERE id=?",
                (video_id, job_id),
            )
            conn.commit()

        log_cb(f"Upload termine ! video_id={video_id}")

    except Exception as exc:
        with get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET youtube_status='upload_failed' WHERE id=?", (job_id,)
            )
            conn.commit()
        log_cb(f"ERREUR upload : {exc}")


def _dispatch(style: str, job_id: str, params: dict, output_dir: Path, log_path: Path):
    """Appelle le bon pipeline selon le style."""
    pipeline_map = {
        "extract":            pipelines.clip_extractor,
        "crop":               pipelines.clip_cropper,
        "merge":              pipelines.simple_merger,
        "podcast":            pipelines.podcast,
        "wave":               pipelines.wave,
        "portrait":           pipelines.portrait,
        "landscape":          pipelines.landscape,
        "batch_extract":      pipelines.batch_extract,
        "debate_single":      pipelines.composite_single,
        "debate_double":      pipelines.composite_double,
        "debate_diagonal":    pipelines.composite_diagonal,
    }

    pipeline = pipeline_map.get(style)
    if pipeline is None:
        raise ValueError(f"Style inconnu: '{style}'")

    return pipeline.run(job_id, params, output_dir, log_path)
