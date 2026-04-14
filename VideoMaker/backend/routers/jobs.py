"""
Router jobs : CRUD + upload de fichiers + téléchargement.
"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from ..database import get_connection, row_to_dict
from ..models import JobResponse, JobLogsResponse
from ..services import job_runner
from ..config import OUTPUTS_DIR, SOURCES_DIR

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_job_or_404(job_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return row_to_dict(row)


def _resolve_job_ref(job_ref: Optional[str]) -> Optional[str]:
    """Résout un job ID en chemin absolu vers sa vidéo de sortie."""
    if not job_ref:
        return None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT output_video_path FROM jobs WHERE id=? AND status='completed'",
            (job_ref,)
        ).fetchone()
    if not row:
        return None
    path = row_to_dict(row).get("output_video_path")
    if path and Path(path).exists():
        return path
    return None


def _has_file(f: Optional[UploadFile]) -> bool:
    """Vérifie qu'un UploadFile contient réellement un fichier (filename non vide).
    FastAPI reçoit des UploadFile avec filename='' quand un <input type=file>
    est présent dans le form mais qu'aucun fichier n'a été sélectionné."""
    return f is not None and bool(f.filename)


def _save_upload(file: UploadFile, dest_dir: Path) -> str:
    """Sauvegarde un fichier uploadé. Lève ValueError si le fichier est vide."""
    if not _has_file(file):
        raise ValueError("Fichier manquant ou nom de fichier vide")
    dest = dest_dir / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return str(dest)


def _save_upload_optional(file: Optional[UploadFile], dest_dir: Path) -> Optional[str]:
    """Sauvegarde un fichier optionnel — retourne None si absent."""
    if not _has_file(file):
        return None
    return _save_upload(file, dest_dir)


# ─── POST /api/jobs ───────────────────────────────────────────────────────────

@router.post("", response_model=JobResponse)
async def create_job(
    style: str = Form(...),
    title: Optional[str] = Form(None),
    # extract
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    # crop
    crop_top: Optional[str] = Form("0"),
    crop_bottom: Optional[str] = Form("0"),
    crop_left: Optional[str] = Form("0"),
    crop_right: Optional[str] = Form("0"),
    use_gpu: Optional[str] = Form("true"),
    # merge
    reverse_order: Optional[str] = Form("false"),
    # podcast / wave / portrait
    speed_factor: Optional[str] = Form("1.0"),
    wave_style: Optional[str] = Form("sine"),
    video_mode: Optional[str] = Form("audio"),
    wave_color: Optional[str] = Form("white"),
    audio_only: Optional[str] = Form("false"),
    border_color: Optional[str] = Form("white"),
    # portrait : taille + position mini-vidéo
    portrait_size_percent: Optional[str] = Form("90"),
    portrait_position_x: Optional[str] = Form("50"),
    portrait_position_y: Optional[str] = Form("75"),
    # wave : taille + position mini-vidéo (modes mini/hybrid)
    mini_size_percent: Optional[str] = Form("100"),
    mini_position: Optional[str] = Form("center"),
    # fichiers uploadés
    video_file: Optional[UploadFile] = File(None),
    video_files: Optional[list[UploadFile]] = File(None),
    background_video: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    content_video: Optional[UploadFile] = File(None),
    # références vers des jobs précédents (évite de ré-uploader)
    video_job_ref: Optional[str] = Form(None),
    audio_job_ref: Optional[str] = Form(None),
    background_job_ref: Optional[str] = Form(None),
    content_job_ref: Optional[str] = Form(None),
    # débat / composite
    size_percent: Optional[str] = Form("35"),
    quality_crf:  Optional[str] = Form("23"),
    speaker_left:   Optional[UploadFile] = File(None),
    speaker_center: Optional[UploadFile] = File(None),
    speaker_right:  Optional[UploadFile] = File(None),
    speaker_left_job_ref:   Optional[str] = Form(None),
    speaker_center_job_ref: Optional[str] = Form(None),
    speaker_right_job_ref:  Optional[str] = Form(None),
):
    # Créer l'entrée en base et le dossier d'output
    job_info = job_runner.create_job(style, title)
    job_id = job_info["id"]
    output_dir = Path(job_info["output_dir"])

    # Résoudre les références vers des jobs précédents
    ref_video      = _resolve_job_ref(video_job_ref)
    ref_audio      = _resolve_job_ref(audio_job_ref)
    ref_background = _resolve_job_ref(background_job_ref)
    ref_content    = _resolve_job_ref(content_job_ref)

    # Sauvegarder les fichiers uploadés (priorité : upload > référence job)
    saved = {}
    if _has_file(video_file):
        saved["video_path"] = _save_upload(video_file, output_dir)
    elif ref_video:
        saved["video_path"] = ref_video

    if video_files:
        paths = [_save_upload_optional(f, output_dir) for f in video_files]
        saved["video_paths"] = [p for p in paths if p is not None]

    if _has_file(background_video):
        saved["background_video_path"] = _save_upload(background_video, output_dir)
    elif ref_background:
        saved["background_video_path"] = ref_background

    if _has_file(audio_file):
        saved["audio_path"] = _save_upload(audio_file, output_dir)
    elif ref_audio:
        saved["audio_path"] = ref_audio

    if _has_file(content_video):
        saved["content_video_path"] = _save_upload(content_video, output_dir)
        saved["content_path"] = saved["content_video_path"]
    elif ref_content:
        saved["content_video_path"] = ref_content
        saved["content_path"] = ref_content

    # Speakers débat (avec support job refs)
    ref_left   = _resolve_job_ref(speaker_left_job_ref)
    ref_center = _resolve_job_ref(speaker_center_job_ref)
    ref_right  = _resolve_job_ref(speaker_right_job_ref)

    if _has_file(speaker_left):
        saved["speaker_left"] = _save_upload(speaker_left, output_dir)
    elif ref_left:
        saved["speaker_left"] = ref_left

    if _has_file(speaker_center):
        saved["speaker_center"] = _save_upload(speaker_center, output_dir)
    elif ref_center:
        saved["speaker_center"] = ref_center

    if _has_file(speaker_right):
        saved["speaker_right"] = _save_upload(speaker_right, output_dir)
    elif ref_right:
        saved["speaker_right"] = ref_right

    # Construire les params selon le style
    if style == "extract":
        params = {
            "video_path": saved.get("video_path"),
            "start_time": start_time,
            "end_time": end_time,
        }
    elif style == "crop":
        params = {
            "video_path": saved.get("video_path"),
            "top": crop_top,
            "bottom": crop_bottom,
            "left": crop_left,
            "right": crop_right,
            "use_gpu": use_gpu.lower() == "true",
        }
    elif style == "merge":
        params = {
            "video_paths": saved.get("video_paths", []),
            "reverse_order": reverse_order.lower() == "true",
        }
    elif style == "podcast":
        params = {
            "background_video_path": saved.get("background_video_path"),
            "audio_path": saved.get("audio_path"),
            "speed_factor": float(speed_factor),
        }
    elif style == "wave":
        params = {
            "audio_path": saved.get("audio_path") or saved.get("video_path"),
            "background_video_path": saved.get("background_video_path"),
            "wave_style": wave_style,
            "video_mode": video_mode,
            "content_video_path": saved.get("content_video_path"),
            "speed_factor": float(speed_factor),
            "wave_color": wave_color,
            "mini_size_percent": int(mini_size_percent or 100),
            "mini_position": mini_position or "center",
        }
    elif style == "portrait":
        params = {
            "background_video_path": saved.get("background_video_path"),
            "content_path": saved.get("content_path") or saved.get("audio_path"),
            "audio_only": audio_only.lower() == "true",
            "border_color": border_color,
            "use_gpu": use_gpu.lower() == "true",
            "size_percent": int(portrait_size_percent or 90),
            "position_x_pct": float(portrait_position_x or 50),
            "position_y_pct": float(portrait_position_y or 75),
        }
    elif style == "debate_single":
        params = {
            "background_video_path": saved.get("background_video_path"),
            "video_path": saved.get("video_path") or saved.get("speaker_left"),
            "size_percent": int(size_percent or 55),
            "crf": int(quality_crf or 23),
        }
    elif style == "debate_double":
        params = {
            "background_video_path": saved.get("background_video_path"),
            "video_left_path":  saved.get("speaker_left"),
            "video_right_path": saved.get("speaker_right"),
            "size_percent": int(size_percent or 35),
            "crf": int(quality_crf or 23),
        }
    elif style == "debate_diagonal":
        params = {
            "background_video_path": saved.get("background_video_path"),
            "video_left_path":   saved.get("speaker_left"),
            "video_center_path": saved.get("speaker_center"),
            "video_right_path":  saved.get("speaker_right"),
            "size_percent": int(size_percent or 28),
            "crf": int(quality_crf or 23),
        }
    else:
        raise HTTPException(status_code=400, detail=f"Style inconnu: {style}")

    # Lancer le job en arrière-plan
    job_runner.submit_job(job_id, style, params)

    return _get_job_or_404(job_id)


# ─── POST /api/jobs/batch-extract ────────────────────────────────────────────

class ClipMark(BaseModel):
    start: float
    end:   float

class BatchExtractRequest(BaseModel):
    source_id: str
    clips:     list[ClipMark]
    merge:     bool = True
    title:     Optional[str] = None

@router.post("/batch-extract", response_model=JobResponse)
def create_batch_extract(req: BatchExtractRequest):
    """
    Extrait N segments d'une vidéo source et les fusionne optionnellement.
    Le source_id doit référencer une vidéo uploadée via /api/sources/upload.
    """
    source_dir = SOURCES_DIR / req.source_id
    if not source_dir.exists():
        raise HTTPException(400, "Source introuvable — uploadez d'abord la vidéo dans l'éditeur")

    source_files = [f for f in source_dir.iterdir() if f.is_file()]
    if not source_files:
        raise HTTPException(400, "Fichier source introuvable")

    source_path = str(source_files[0])
    n = len(req.clips)
    title = req.title or f"{n} clip{'s' if n > 1 else ''} extraits"

    job_info = job_runner.create_job("batch_extract", title)
    job_id   = job_info["id"]

    params = {
        "source_path": source_path,
        "clips":       [{"start": c.start, "end": c.end} for c in req.clips],
        "merge":       req.merge,
    }

    job_runner.submit_job(job_id, "batch_extract", params)
    return _get_job_or_404(job_id)


# ─── GET /api/jobs ────────────────────────────────────────────────────────────

@router.get("", response_model=list[JobResponse])
def list_jobs():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC"
        ).fetchall()
    return [row_to_dict(r) for r in rows]


# ─── GET /api/jobs/{id} ───────────────────────────────────────────────────────

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    return _get_job_or_404(job_id)


# ─── GET /api/jobs/{id}/logs ─────────────────────────────────────────────────

@router.get("/{job_id}/logs", response_model=JobLogsResponse)
def get_logs(job_id: str):
    job = _get_job_or_404(job_id)
    logs = ""
    if job.get("log_file") and Path(job["log_file"]).exists():
        with open(job["log_file"], "r", encoding="utf-8", errors="replace") as f:
            logs = f.read()
    return {
        "id": job_id,
        "status": job["status"],
        "logs": logs,
        "output_video_path": job.get("output_video_path"),
    }


# ─── GET /api/jobs/{id}/download ─────────────────────────────────────────────

@router.get("/{job_id}/download")
def download_video(job_id: str):
    job = _get_job_or_404(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job pas encore terminé")
    video_path = job.get("output_video_path")
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Fichier vidéo introuvable")
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=Path(video_path).name,
    )


# ─── DELETE /api/jobs/{id} ────────────────────────────────────────────────────

@router.delete("/{job_id}")
def delete_job(job_id: str):
    job = _get_job_or_404(job_id)

    # Supprimer le dossier output
    if job.get("output_dir"):
        output_dir = Path(job["output_dir"])
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)

    with get_connection() as conn:
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()

    return {"detail": "Job supprimé"}
