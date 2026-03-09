"""
Service d'intégration YouTube (OAuth + upload).

Basé sur le flux InstalledApp / Desktop app :
- client_secrets.json à la racine du projet
- youtube_token.json généré après le premier login (non versionné)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from ..config import CLIENT_SECRETS_PATH, YOUTUBE_TOKEN_PATH

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


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


def get_credentials() -> Credentials:
    """Retourne des credentials valides, en lançant le flux OAuth si besoin."""
    creds = _load_credentials()

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)
        return creds

    if not CLIENT_SECRETS_PATH.exists():
        raise RuntimeError("client_secrets.json introuvable à la racine du projet.")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_PATH),
        SCOPES,
    )
    # Ouvre le navigateur local pour autoriser l'appli
    creds = flow.run_local_server(port=0)
    _save_credentials(creds)
    return creds


def get_youtube_client():
    creds = get_credentials()
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
    """
    Upload une vidéo sur YouTube et retourne son video_id.
    """
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
    log("📤 Début de l'upload vers YouTube...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            log(f"   ▸ Upload {pct}%")

    video_id = response["id"]
    log(f"✅ Vidéo uploadée, id={video_id}")

    # Thumbnail
    if thumbnail_path is not None and thumbnail_path.exists():
        try:
            log("🖼️ Envoi de la miniature...")
            thumb_media = MediaFileUpload(str(thumbnail_path))
            yt.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
        except HttpError:
            log("⚠️ Impossible de définir la miniature (erreur YouTube).")

    # Playlist
    if playlist_id:
        try:
            log(f"📂 Ajout à la playlist {playlist_id}...")
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
            log("⚠️ Impossible d'ajouter la vidéo à la playlist.")

    return video_id

