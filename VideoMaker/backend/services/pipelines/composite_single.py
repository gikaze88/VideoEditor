"""
Pipeline composite_single : fond vidéo + 1 intervenant centré.

Cas d'usage : débat / présentation avec un seul speaker.

params :
    background_video_path : str   — vidéo de fond
    video_path            : str   — vidéo du speaker (centré)
    size_percent          : int   — taille du speaker en % de l'écran (défaut 55)
    crf                   : int   — qualité CRF libx264 (défaut 23)
    fps                   : int   — fps de sortie (défaut 30)
"""
from pathlib import Path
from ._ffmpeg import check_ffmpeg, get_duration

OUT_W, OUT_H = 1920, 1080


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> str:
    bg_path    = Path(params["background_video_path"])
    vid_path   = Path(params["video_path"])
    size_pct   = int(params.get("size_percent", 55))
    crf        = int(params.get("crf", 23))
    fps        = int(params.get("fps", 30))

    duration = get_duration(vid_path)

    # Dimensions : speaker centré
    w  = int(OUT_W * size_pct / 100)
    h  = int(OUT_H * size_pct / 100)
    cx = int(OUT_W * (100 - size_pct) / 200)
    cy = int(OUT_H * (100 - size_pct) / 200)

    output = output_dir / "composite_single.mp4"

    filter_complex = (
        f"[0:v]loop=loop=-1:size=32767:start=0,"
        f"scale={OUT_W}:{OUT_H},fps={fps}[bg_loop];"
        f"[1:v]scale={w}:{h},fps={fps}[spk_scaled];"
        f"[bg_loop][spk_scaled]overlay=x={cx}:y={cy}[final_video];"
        f"[1:a]aresample=async=1[final_audio]"
    )

    check_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", str(bg_path),
            "-i", str(vid_path),
            "-filter_complex", filter_complex,
            "-map", "[final_video]",
            "-map", "[final_audio]",
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-r", str(fps),
            "-c:a", "aac", "-b:a", "128k",
            str(output),
        ],
        log_path,
        "Erreur encodage composite single",
    )

    return str(output)
