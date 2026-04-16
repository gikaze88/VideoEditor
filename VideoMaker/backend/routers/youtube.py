"""
Router YouTube : authentification OAuth (web-redirect) et upload de vidéos.

Flux OAuth :
  1. GET  /api/youtube/auth-url        → retourne { auth_url }
  2. Frontend ouvre auth_url dans un nouvel onglet (même navigateur)
  3. Google redirige vers GET /api/youtube/oauth-callback?code=...&state=...
  4. Le backend échange le code, sauvegarde le token, affiche une page HTML
     qui ferme l'onglet automatiquement.
  5. Le frontend poll /api/youtube/auth-status pour détecter la connexion.
"""
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse

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


# ─── OAuth endpoints ──────────────────────────────────────────────────────────

@router.get("/auth-status")
def auth_status():
    return {"authenticated": yt_service.is_authenticated()}


@router.get("/auth-url")
async def auth_url():
    """Retourne l'URL Google à ouvrir dans le navigateur de l'utilisateur."""
    url = await run_in_threadpool(yt_service.get_auth_url)
    return {"auth_url": url}


@router.get("/oauth-callback")
async def oauth_callback(code: str = "", error: str = ""):
    """Callback appelé par Google après autorisation. Échange le code et ferme l'onglet."""
    if error:
        html = f"""<!DOCTYPE html><html><body>
        <h2>Erreur d'authentification</h2><p>{error}</p>
        <p>Vous pouvez fermer cet onglet.</p>
        </body></html>"""
        return HTMLResponse(content=html, status_code=400)

    if not code:
        raise HTTPException(status_code=400, detail="Paramètre 'code' manquant")

    try:
        await run_in_threadpool(yt_service.exchange_code, code)
    except Exception as exc:
        html = f"""<!DOCTYPE html><html><body>
        <h2>Erreur lors de l'échange du code</h2><p>{exc}</p>
        <p>Vous pouvez fermer cet onglet.</p>
        </body></html>"""
        return HTMLResponse(content=html, status_code=500)

    html = """<!DOCTYPE html>
<html>
<head><title>Authentification YouTube</title></head>
<body style="font-family:system-ui;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#0f172a;color:white;">
  <div style="text-align:center;">
    <h2 style="color:#22c55e;">Authentification reussie !</h2>
    <p>Vous pouvez fermer cet onglet.<br>L'application a bien recu votre autorisation.</p>
    <script>setTimeout(()=>window.close(),2000);</script>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.post("/revoke")
def revoke():
    if YOUTUBE_TOKEN_PATH.exists():
        YOUTUBE_TOKEN_PATH.unlink()
    return {"revoked": True}


# ─── Playlists & Upload ──────────────────────────────────────────────────────

@router.get("/playlists")
async def playlists():
    if not yt_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Non authentifie sur YouTube")
    pls = await run_in_threadpool(yt_service.get_playlists)
    return {"playlists": pls}


@router.get("/meta")
def youtube_meta():
    """Retourne les catégories et langues disponibles."""
    return {
        "categories": yt_service.CATEGORIES,
        "languages": yt_service.LANGUAGES,
    }


@router.post("/upload/{job_id}")
async def upload_job_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    privacy: str = Form("private"),
    category_id: str = Form("25"),
    playlist_id: Optional[str] = Form(None),
    filename: str = Form(""),
    language: str = Form("fr"),
    license_type: str = Form("youtube"),
    embeddable: str = Form("true"),
    thumbnail: Optional[UploadFile] = File(None),
):
    job = _get_job_or_404(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job pas encore termine")

    base_dir = Path(job["output_dir"] or OUTPUTS_DIR / job_id)
    if filename:
        video_path = base_dir / filename
    else:
        if not job.get("output_video_path"):
            raise HTTPException(status_code=400, detail="Chemin video de sortie introuvable")
        video_path = Path(job["output_video_path"])

    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Fichier video introuvable: {video_path.name}")

    thumb_path: Optional[Path] = None
    if thumbnail is not None and thumbnail.filename:
        thumb_path = base_dir / f"thumb_{job_id}{Path(thumbnail.filename).suffix or '.jpg'}"
        with open(thumb_path, "wb") as f:
            f.write(await thumbnail.read())

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
                language,
                license_type,
                embeddable.lower() == "true",
                log_cb,
            )
            with get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET youtube_video_id=?, youtube_status=? WHERE id=?",
                    (video_id, "uploaded", job_id),
                )
                conn.commit()
            logs.append("Upload YouTube termine")
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
            logs.append(f"Erreur upload YouTube: {exc}")
            raise

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
