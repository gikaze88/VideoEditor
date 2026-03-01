"""
Router sources : upload et streaming des vidéos sources pour l'éditeur.
Chaque source uploadée est conservée dans sources/{source_id}/{filename}.
Le streaming supporte les requêtes Range (seeking vidéo).
"""
import json
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config import SOURCES_DIR

router = APIRouter(prefix="/api/sources", tags=["sources"])

MIME_TYPES: dict[str, str] = {
    ".mp4":  "video/mp4",
    ".m4v":  "video/mp4",
    ".mkv":  "video/x-matroska",
    ".webm": "video/webm",
    ".avi":  "video/x-msvideo",
    ".mov":  "video/quicktime",
    ".ts":   "video/mp2t",
    ".flv":  "video/x-flv",
    ".wmv":  "video/x-ms-wmv",
}


def _get_video_info(path: Path) -> dict:
    """Récupère durée et dimensions via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        str(path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=30,
        )
        data = json.loads(result.stdout)
    except Exception:
        return {"duration": 0, "width": 0, "height": 0}

    duration = float(data.get("format", {}).get("duration", 0))
    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    width  = video_stream.get("width",  0) if video_stream else 0
    height = video_stream.get("height", 0) if video_stream else 0
    fps_raw = video_stream.get("r_frame_rate", "0/1") if video_stream else "0/1"
    try:
        num, den = fps_raw.split("/")
        fps = round(int(num) / int(den), 2) if int(den) else 0
    except Exception:
        fps = 0

    return {"duration": duration, "width": width, "height": height, "fps": fps}


# ─── POST /api/sources/upload ────────────────────────────────────────────────

@router.post("/upload")
async def upload_source(file: UploadFile = File(...)):
    """Upload une vidéo source. Retourne source_id, durée, dimensions."""
    source_id = str(uuid.uuid4())
    dest_dir = SOURCES_DIR / source_id
    dest_dir.mkdir(parents=True)

    dest = dest_dir / (file.filename or "source.mp4")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    info = _get_video_info(dest)

    return {
        "source_id": source_id,
        "filename":  file.filename,
        "path":      str(dest),
        **info,
    }


# ─── GET /api/sources/{source_id}/stream ─────────────────────────────────────

@router.get("/{source_id}/stream")
async def stream_source(source_id: str):
    """
    Sert la vidéo source avec support des requêtes Range (seeking).
    FileResponse de Starlette gère automatiquement Accept-Ranges et 206 Partial Content.
    """
    source_dir = SOURCES_DIR / source_id
    if not source_dir.exists():
        raise HTTPException(404, "Source introuvable")

    files = [f for f in source_dir.iterdir() if f.is_file()]
    if not files:
        raise HTTPException(404, "Fichier source introuvable")

    video_file = files[0]
    mime = MIME_TYPES.get(video_file.suffix.lower(), "video/mp4")

    return FileResponse(str(video_file), media_type=mime)


# ─── DELETE /api/sources/{source_id} ─────────────────────────────────────────

@router.delete("/{source_id}")
def delete_source(source_id: str):
    """Supprime une source uploadée (libère de l'espace disque)."""
    source_dir = SOURCES_DIR / source_id
    if source_dir.exists():
        shutil.rmtree(source_dir, ignore_errors=True)
    return {"detail": "Source supprimée"}
