"""
Pipeline: podcast
Génère une vidéo podcast (fond vidéo en boucle + audio, option accélération).

Correction décalage audio/vidéo :
- L'ancien code extrayait l'audio en MP3 (libmp3lame) si l'input était une vidéo.
  Ce ré-encodage intermédiaire introduit un délai d'encodeur.
- Fix : l'audio est pris directement depuis le fichier source avec -map 1:a.
  L'atempo (accélération) est appliqué dans le filter_complex si speed != 1.0.
"""
import os
import subprocess
from pathlib import Path
from ._ffmpeg import check_ffmpeg, run_ffmpeg, slug_from_title


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        stdin=subprocess.DEVNULL,
    )
    return float(r.stdout.strip())


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    bg_path    = params["background_video_path"]
    input_path = params["audio_path"]
    speed      = float(params.get("speed_factor", 1.0))

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[podcast] bg={bg_path}\n")
        log.write(f"[podcast] input={input_path}\n")
        log.write(f"[podcast] speed={speed}\n")
        log.flush()

    # Durée depuis le fichier source directement (pas de MP3 intermédiaire)
    source_duration = _get_duration(input_path)
    duration = source_duration / speed if speed != 1.0 else source_duration

    # Boucler le background
    bg_dur    = _get_duration(bg_path)
    loops     = int(duration / bg_dur) + 1
    looped_bg = str(output_dir / f"bg_{job_id}.mp4")

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
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

    title = params.get("title")
    if title:
        base = slug_from_title(title)
        speed_suffix = f"_x{speed}" if speed != 1.0 else ""
        output_file = output_dir / f"{base}{speed_suffix}.mp4"
    else:
        suffix = f"_x{speed}" if speed != 1.0 else ""
        output_file = output_dir / f"podcast{suffix}_{job_id}.mp4"

    # Assemblage : audio pris directement depuis input_path sans re-encodage
    # Si speed != 1.0, atempo est appliqué dans le filter_complex
    if speed != 1.0:
        # Appliquer l'accélération directement dans le filter_complex
        check_ffmpeg(
            ["ffmpeg", "-y",
             "-i", looped_bg, "-i", input_path,
             "-filter_complex", f"[1:a]atempo={speed}[aout]",
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
             "-shortest",
             str(output_file)],
            log_path, "Assemblage final échoué"
        )
    else:
        check_ffmpeg(
            ["ffmpeg", "-y",
             "-i", looped_bg, "-i", input_path,
             "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
             "-shortest",
             str(output_file)],
            log_path, "Assemblage final échoué"
        )

    try:
        os.remove(looped_bg)
    except Exception:
        pass

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[podcast] OK -> {output_file}\n")

    return output_file
