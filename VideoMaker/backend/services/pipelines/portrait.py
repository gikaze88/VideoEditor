"""
Pipeline: portrait
Génère une vidéo portrait 1080×1920 avec mini-vidéo centrée.
Adapté de video_generator_simple.py et video_generator_simple_audio.py.

Layout fixe:
  - Zone logo (background) : 0 → 960px
  - Espace haut            : 960 → 1060px (100px)
  - Mini-vidéo/photo       : 1060 → 1820px (760px max)
  - Marge bas              : 1820 → 1920px (100px)
"""
import subprocess
import os
from pathlib import Path

# ─── Constantes layout ────────────────────────────────────────────────────────
CANVAS_W    = 1080
CANVAS_H    = 1920
LOGO_H      = 960
SPACING_TOP = 100
MAX_MINI_H  = 760
MAX_MINI_W  = 680
BORDER_W    = 3

MINI_Y = LOGO_H + SPACING_TOP   # 1060
MINI_X = (CANVAS_W - (MAX_MINI_W + BORDER_W * 2)) // 2


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    return float(r.stdout.strip())


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def _loop_background(bg_path: str, duration: float, out_path: str, log) -> str:
    bg_dur = _get_duration(bg_path)
    loops = int(duration / bg_dur) + 1
    log.write(f"[portrait] Boucle background: {loops} fois\n")
    r = subprocess.run(
        ["ffmpeg", "-y",
         "-stream_loop", str(loops), "-i", bg_path,
         "-t", str(duration),
         "-vf", f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
                f"crop={CANVAS_W}:{CANVAS_H}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an",
         out_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    log.write(r.stdout)
    if r.returncode != 0:
        raise RuntimeError("Boucle background échouée")
    return out_path


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    """
    params attendus:
        background_video_path : str       — vidéo de fond 1080×1920
        content_path          : str       — vidéo ou audio à intégrer
        audio_only            : bool      — True = pas de mini-vidéo, juste l'audio
        border_color          : str       — couleur de la bordure (défaut: white)
    """
    bg_path    = params["background_video_path"]
    content    = params["content_path"]
    audio_only = params.get("audio_only", False)
    border_col = params.get("border_color", "white")

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[portrait] bg={bg_path}\n")
        log.write(f"[portrait] content={content}\n")
        log.write(f"[portrait] audio_only={audio_only}\n")

        # 1. Extraire l'audio de la source (toujours nécessaire)
        if _is_video(content):
            audio_path = str(output_dir / f"audio_{job_id}.mp3")
            log.write(f"[portrait] Extraction audio...\n")
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", content,
                 "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
            log.write(r.stdout)
            if r.returncode != 0:
                raise RuntimeError("Extraction audio échouée")
        else:
            audio_path = content

        duration = _get_duration(audio_path)
        log.write(f"[portrait] Durée: {duration:.1f}s\n")

        # 2. Background bouclé
        looped_bg = str(output_dir / f"bg_{job_id}.mp4")
        _loop_background(bg_path, duration, looped_bg, log)

        output_file = output_dir / f"portrait_{job_id}.mp4"

        if audio_only or not _is_video(content):
            # Mode audio : fond + audio seulement
            log.write(f"[portrait] Mode audio pur\n")
            cmd = [
                "ffmpeg", "-y",
                "-i", looped_bg,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_file),
            ]
        else:
            # Mode vidéo : fond + mini-vidéo centrée + audio
            log.write(f"[portrait] Mode mini-vidéo centrée\n")
            # Filtre: redimensionner mini-vidéo + bordure blanche + overlay
            mini_with_border_w = MAX_MINI_W + BORDER_W * 2
            mini_with_border_h = MAX_MINI_H + BORDER_W * 2
            border_x = (CANVAS_W - mini_with_border_w) // 2
            border_y = MINI_Y - BORDER_W

            vf = (
                f"[1:v]scale={MAX_MINI_W}:{MAX_MINI_H}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={MAX_MINI_W}:{MAX_MINI_H}:(ow-iw)/2:(oh-ih)/2,"
                f"pad={mini_with_border_w}:{mini_with_border_h}:"
                f"{BORDER_W}:{BORDER_W}:color={border_col}[mini];"
                f"[0:v][mini]overlay={border_x}:{border_y}[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-i", looped_bg,
                "-i", content,
                "-i", audio_path,
                "-filter_complex", vf,
                "-map", "[outv]",
                "-map", "2:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(output_file),
            ]

        log.write(f"[portrait] Commande: {' '.join(cmd)}\n")
        r = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        log.write(r.stdout)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg portrait échoué (code {r.returncode})")

        try:
            os.remove(looped_bg)
        except Exception:
            pass

        log.write(f"[portrait] Succès → {output_file}\n")

    return output_file
