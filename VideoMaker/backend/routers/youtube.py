"""
Router YouTube : authentification OAuth et upload d'une vidéo issue d'un job.
"""
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool

from ..database import get_connection, row_to_dict
from ..config import OUTPUTS_DIR, YOUTUBE_TOKEN_PATH
from ..services import youtube as yt_service

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


def _get_job_or_404(job_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return row_to_dict(row)


@router.get("/auth-status")
def auth_status():
    return {"authenticated": yt_service.is_authenticated()}


@router.post("/auth")
async def auth():
    # Lance le flux OAuth dans un thread bloquant
    await run_in_threadpool(yt_service.get_credentials)
    return {"authenticated": True, "message": "Authentification YouTube réussie"}


@router.post("/revoke")
def revoke():
    if YOUTUBE_TOKEN_PATH.exists():
        YOUTUBE_TOKEN_PATH.unlink()
    return {"revoked": True}


@router.get("/playlists")
async def playlists():
    if not yt_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Non authentifié sur YouTube")
    pls = await run_in_threadpool(yt_service.get_playlists)
    return {"playlists": pls}


@router.post("/upload/{job_id}")
async def upload_job_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    privacy: str = Form("private"),
    category_id: str = Form("27"),
    playlist_id: Optional[str] = Form(None),
    filename: str = Form(""),
    thumbnail: Optional[UploadFile] = File(None),
):
    job = _get_job_or_404(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job pas encore terminé")

    # Résoudre le fichier vidéo à uploader
    base_dir = Path(job["output_dir"] or OUTPUTS_DIR / job_id)
    if filename:
        video_path = base_dir / filename
    else:
        if not job.get("output_video_path"):
            raise HTTPException(status_code=400, detail="Chemin vidéo de sortie introuvable")
        video_path = Path(job["output_video_path"])

    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Fichier vidéo introuvable: {video_path.name}")

    # Sauvegarder la miniature si fournie
    thumb_path: Optional[Path] = None
    if thumbnail is not None and thumbnail.filename:
        thumb_path = base_dir / f"thumb_{job_id}{Path(thumbnail.filename).suffix or '.jpg'}"
        with open(thumb_path, "wb") as f:
            f.write(await thumbnail.read())

    # Construire les tags
    tags_list: List[str] = [t.strip() for t in tags.split(",")] if tags else []

    logs: List[str] = []

    def log_cb(msg: str):
        logs.append(msg)

    async def do_upload():
        try:
            video_id = await run_in_threadpool(
                yt_service.upload_video,
                video_path,
                title,
                description,
                tags_list,
                privacy,
                category_id,
                thumb_path,
                playlist_id,
                log_cb,
            )
            with get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET youtube_video_id=?, youtube_status=? WHERE id=?",
                    (video_id, "uploaded", job_id),
                )
                conn.commit()
            logs.append("✅ Upload YouTube terminé")
            return {
                "video_id": video_id,
                "url": f"https://youtu.be/{video_id}",
                "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
                "privacy": privacy,
                "logs": logs,
            }
        except Exception as exc:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET youtube_status=? WHERE id=?",
                    ("failed", job_id),
                )
                conn.commit()
            logs.append(f"❌ Erreur upload YouTube: {exc}")
            raise

    # On exécute réellement l'upload dans le même handler (pour renvoyer le résultat)
    result = await do_upload()
    return result


@router.get("/job/{job_id}")
def youtube_job_status(job_id: str):
    job = _get_job_or_404(job_id)
    vid = job.get("youtube_video_id")
    status = job.get("youtube_status")
    if not vid:
        return {
            "youtube_video_id": None,
            "youtube_status": None,
            "url": None,
            "studio_url": None,
        }
    return {
        "youtube_video_id": vid,
        "youtube_status": status,
        "url": f"https://youtu.be/{vid}",
        "studio_url": f"https://studio.youtube.com/video/{vid}/edit",
    }

