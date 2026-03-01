"""
Pipeline: podcast
Génère une vidéo podcast (fond vidéo en boucle + audio, option accélération).
"""
import os
import subprocess
from pathlib import Path
from ._ffmpeg import check_ffmpeg


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    return float(r.stdout.strip())


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    bg_path    = params["background_video_path"]
    input_path = params["audio_path"]
    speed      = float(params.get("speed_factor", 1.0))

    with open(log_path, "a") as log:
        log.write(f"[podcast] bg={bg_path}\n")
        log.write(f"[podcast] input={input_path}\n")
        log.write(f"[podcast] speed={speed}\n")
        log.flush()

    audio_path = str(output_dir / f"audio_{job_id}.mp3")

    # 1. Extraire l'audio si besoin
    if _is_video(input_path):
        check_ffmpeg(
            ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path],
            log_path, "Extraction audio échouée"
        )
    else:
        audio_path = input_path

    # 2. Accélération
    if speed != 1.0:
        sped = str(output_dir / f"audio_sped_{job_id}.mp3")
        check_ffmpeg(
            ["ffmpeg", "-y", "-i", audio_path, "-filter:a", f"atempo={speed}",
             "-acodec", "libmp3lame", "-q:a", "2", sped],
            log_path, "Accélération audio échouée"
        )
        audio_path = sped

    # 3. Boucler le background
    duration   = _get_duration(audio_path)
    bg_dur     = _get_duration(bg_path)
    loops      = int(duration / bg_dur) + 1
    looped_bg  = str(output_dir / f"bg_{job_id}.mp4")

    with open(log_path, "a") as log:
        log.write(f"[podcast] durée audio={duration:.1f}s boucles={loops}\n")
        log.flush()

    check_ffmpeg(
        ["ffmpeg", "-y",
         "-stream_loop", str(loops), "-i", bg_path,
         "-t", str(duration),
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an",
         looped_bg],
        log_path, "Boucle background échouée"
    )

    # 4. Combiner
    suffix      = f"_x{speed}" if speed != 1.0 else ""
    output_file = output_dir / f"podcast{suffix}_{job_id}.mp4"

    check_ffmpeg(
        ["ffmpeg", "-y",
         "-i", looped_bg, "-i", audio_path,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
         str(output_file)],
        log_path, "Assemblage final échoué"
    )

    try:
        os.remove(looped_bg)
    except Exception:
        pass

    with open(log_path, "a") as log:
        log.write(f"[podcast] ✓ → {output_file}\n")

    return output_file
