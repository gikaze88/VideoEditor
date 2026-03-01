"""
Gestion asynchrone des jobs avec ThreadPoolExecutor.
max_workers=1 → un seul job en cours à la fois (usage personnel).
Les jobs continuent même si le client se déconnecte.
"""
import uuid
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ..database import get_connection
from ..config import OUTPUTS_DIR
from . import pipelines


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
            "SELECT output_dir, log_file FROM jobs WHERE id=?", (job_id,)
        ).fetchone()

    output_dir = Path(row["output_dir"])
    log_path = Path(row["log_file"])

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


def _dispatch(style: str, job_id: str, params: dict, output_dir: Path, log_path: Path):
    """Appelle le bon pipeline selon le style."""
    pipeline_map = {
        "extract": pipelines.clip_extractor,
        "crop":    pipelines.clip_cropper,
        "merge":   pipelines.simple_merger,
        "podcast": pipelines.podcast,
        "wave":    pipelines.wave,
        "portrait": pipelines.portrait,
    }

    pipeline = pipeline_map.get(style)
    if pipeline is None:
        raise ValueError(f"Style inconnu: '{style}'")

    return pipeline.run(job_id, params, output_dir, log_path)
