"""
Router assets : config, outputs, et jobs de préparation réutilisables.
"""
import os
from pathlib import Path
from fastapi import APIRouter
from ..config import OUTPUTS_DIR, JOB_STYLES, WAVE_STYLES, VIDEO_MODES, AVAILABLE_SPEED_FACTORS
from ..database import get_connection, row_to_dict

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("/config")
def get_config():
    """Retourne la configuration disponible (styles, options)."""
    return {
        "job_styles": JOB_STYLES,
        "wave_styles": WAVE_STYLES,
        "video_modes": VIDEO_MODES,
        "speed_factors": AVAILABLE_SPEED_FACTORS,
    }


@router.get("/prep-jobs")
def get_prep_jobs():
    """
    Retourne les jobs terminés dont l'output peut être réutilisé comme source.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, style, title, output_video_path, completed_at
               FROM jobs
               WHERE status = 'completed'
                 AND style IN ('extract', 'crop', 'merge', 'portrait', 'landscape', 'wave', 'podcast')
                 AND output_video_path IS NOT NULL
               ORDER BY completed_at DESC
               LIMIT 30"""
        ).fetchall()
    return [row_to_dict(r) for r in rows]


@router.get("/outputs")
def list_outputs():
    """Liste les dossiers d'output existants."""
    if not OUTPUTS_DIR.exists():
        return {"outputs": []}

    outputs = []
    for job_dir in sorted(OUTPUTS_DIR.iterdir()):
        if not job_dir.is_dir():
            continue
        files = [f.name for f in job_dir.iterdir() if f.is_file() and f.suffix == ".mp4"]
        outputs.append({"job_id": job_dir.name, "files": files})

    return {"outputs": outputs}
