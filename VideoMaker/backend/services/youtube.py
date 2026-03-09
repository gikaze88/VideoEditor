"""
Service d'intégration YouTube (OAuth web-redirect + upload).

Flux OAuth "web-redirect" :
1. Le backend génère une URL d'autorisation Google (get_auth_url)
2. Le frontend ouvre cette URL dans un nouvel onglet du navigateur en cours
3. Google redirige vers http://localhost:8001/api/youtube/oauth-callback?code=...
4. Le backend échange le code contre un token (exchange_code)
5. Le frontend poll /api/youtube/auth-status pour détecter la connexion

Avantage: l'utilisateur est redirigé dans le navigateur qu'il utilise déjà,
ce qui lui permet de choisir le compte Google correspondant.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from ..config import CLIENT_SECRETS_PATH, YOUTUBE_TOKEN_PATH

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

OAUTH_REDIRECT_URI = "http://localhost:8001/api/youtube/oauth-callback"


# ─── Credentials management ──────────────────────────────────────────────────

def _load_credentials() -> Optional[Credentials]:
    if not YOUTUBE_TOKEN_PATH.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(YOUTUBE_TOKEN_PATH), SCOPES)
    except Exception:
        return None


def _save_credentials(creds: Credentials) -> None:
    YOUTUBE_TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")


def is_authenticated() -> bool:
    """Vrai si un token valide ou rafraîchissable existe."""
    creds = _load_credentials()
    if not creds:
        return False
    if creds.valid:
        return True
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
            return True
        except Exception:
            return False
    return False


def _get_valid_credentials() -> Credentials:
    """Retourne des credentials valides (refresh si nécessaire). Lève si absent."""
    creds = _load_credentials()
    if not creds:
        raise RuntimeError("Non authentifié — lancez le flux OAuth d'abord.")
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)
    return creds


# ─── OAuth web-redirect flow ─────────────────────────────────────────────────

import threading

_pending_flow: Optional[Flow] = None
_flow_lock = threading.Lock()


def _create_flow() -> Flow:
    """Crée un Flow OAuth avec redirect URI pointant vers le backend."""
    if not CLIENT_SECRETS_PATH.exists():
        raise RuntimeError("client_secrets.json introuvable dans le dossier VideoMaker.")

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRETS_PATH),
        scopes=SCOPES,
        redirect_uri=OAUTH_REDIRECT_URI,
    )
    return flow


def get_auth_url() -> str:
    """Génère l'URL d'autorisation Google que le frontend ouvrira dans un onglet.

    Le Flow est conservé en mémoire pour être réutilisé par exchange_code()
    (le state OAuth doit correspondre).
    """
    global _pending_flow
    flow = _create_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    with _flow_lock:
        _pending_flow = flow
    return auth_url


def exchange_code(code: str) -> None:
    """Échange le code d'autorisation contre un token et le sauvegarde."""
    global _pending_flow
    with _flow_lock:
        flow = _pending_flow
        _pending_flow = None

    if flow is None:
        flow = _create_flow()

    flow.fetch_token(code=code)
    _save_credentials(flow.credentials)


# ─── YouTube API client ───────────────────────────────────────────────────────

def get_youtube_client():
    creds = _get_valid_credentials()
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def get_playlists() -> List[Dict[str, str]]:
    """Liste les playlists de la chaîne."""
    yt = get_youtube_client()
    playlists: List[Dict[str, str]] = []

    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req is not None:
        resp = req.execute()
        for p in resp.get("items", []):
            playlists.append(
                {
                    "id": p["id"],
                    "title": p["snippet"]["title"],
                }
            )
        req = yt.playlists().list_next(req, resp)
    return playlists


# ─── Upload ───────────────────────────────────────────────────────────────────

def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    privacy: str = "private",
    category_id: str = "27",
    thumbnail_path: Optional[Path] = None,
    playlist_id: Optional[str] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """Upload une vidéo sur YouTube et retourne son video_id."""
    def log(msg: str) -> None:
        if log_callback:
            log_callback(msg)

    yt = get_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description or "",
            "tags": [t.strip() for t in (tags or []) if t.strip()],
            "categoryId": category_id or "27",
        },
        "status": {
            "privacyStatus": privacy or "private",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=50 * 1024 * 1024,
        resumable=True,
        mimetype="video/mp4",
    )

    request = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    log("Upload YouTube en cours...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            log(f"   Upload {pct}%")

    video_id = response["id"]
    log(f"Video uploadee, id={video_id}")

    if thumbnail_path is not None and thumbnail_path.exists():
        try:
            log("Envoi de la miniature...")
            thumb_media = MediaFileUpload(str(thumbnail_path))
            yt.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
        except HttpError:
            log("Impossible de definir la miniature (erreur YouTube).")

    if playlist_id:
        try:
            log(f"Ajout a la playlist {playlist_id}...")
            yt.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
        except HttpError:
            log("Impossible d'ajouter la video a la playlist.")

    return video_id
