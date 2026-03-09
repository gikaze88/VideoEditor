"""
Pipeline: portrait
Génère une vidéo portrait 1080×1920 avec mini-vidéo centrée.

Version VideoMaker :
- Log UTF-8 (évite les erreurs 'charmap' sous Windows)
- Encodage CPU (libx264 medium) avec option GPU (h264_nvenc) + fallback automatique
"""
import subprocess
import os
from pathlib import Path
from ._ffmpeg import check_ffmpeg, run_ffmpeg

CANVAS_W    = 1080
CANVAS_H    = 1920
LOGO_H      = 960
SPACING_TOP = 100
SPACING_BOTTOM = 100
MAX_MINI_H  = 760   # hauteur dispo entre logo et bas (identique à l'original)
MIN_VIDEO_W = 600
MAX_VIDEO_W = 680
BORDER_W    = 3


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    return float(r.stdout.strip())


def _get_dimensions(path: str) -> tuple[int, int, float]:
    """Retourne (w, h, ratio) de la vidéo, comme dans le script original."""
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"Dimensions introuvables pour {path}")
    w = int(lines[0].strip())
    h = int(lines[1].strip())
    return w, h, w / h


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    bg_path    = params["background_video_path"]
    content    = params["content_path"]
    audio_only = params.get("audio_only", False)
    border_col = params.get("border_color", "white")
    use_gpu    = bool(params.get("use_gpu", True))

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[portrait] bg={bg_path}\n")
        log.write(f"[portrait] content={content}\n")
        log.write(f"[portrait] audio_only={audio_only} gpu={use_gpu}\n")
        log.flush()

    # 1. Extraire l'audio
    if _is_video(content):
        audio_path = str(output_dir / f"audio_{job_id}.mp3")
        check_ffmpeg(
            ["ffmpeg", "-y", "-i", content, "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path],
            log_path, "Extraction audio échouée"
        )
    else:
        audio_path = content

    # 2. Background bouclé
    duration  = _get_duration(audio_path)
    bg_dur    = _get_duration(bg_path)
    loops     = int(duration / bg_dur) + 1
    looped_bg = str(output_dir / f"bg_{job_id}.mp4")

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[portrait] durée={duration:.1f}s boucles={loops}\n")
        log.flush()

    # Préparation du background (CPU, car coût raisonnable)
    check_ffmpeg(
        [
            "ffmpeg", "-y",
            "-stream_loop", str(loops), "-i", bg_path,
            "-t", str(duration),
            "-vf", (
                f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
                f"crop={CANVAS_W}:{CANVAS_H}"
            ),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an",
            looped_bg,
        ],
        log_path,
        "Boucle background échouée",
    )

    output_file = output_dir / f"portrait_{job_id}.mp4"

    # 3. Assemblage
    if audio_only or not _is_video(content):
        check_ffmpeg(
            ["ffmpeg", "-y",
             "-i", looped_bg, "-i", audio_path,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
             str(output_file)],
            log_path, "Assemblage audio échoué"
        )
    else:
        # Calcul des dimensions de la mini‑vidéo exactement comme dans video_generator_simple.py
        src_w, src_h, src_ratio = _get_dimensions(content)

        # Espace dispo vertical pour la mini (entre logo et bas)
        available_h = CANVAS_H - LOGO_H - SPACING_TOP - SPACING_BOTTOM
        assert int(available_h) == MAX_MINI_H

        # Largeur max théorique
        width_from_max        = MAX_VIDEO_W
        height_from_max_width = int(MAX_VIDEO_W / src_ratio)

        height_from_max       = MAX_MINI_H
        width_from_max_height = int(MAX_MINI_H * src_ratio)

        if height_from_max_width <= MAX_MINI_H:
            ideal_w = width_from_max
            ideal_h = height_from_max_width
        else:
            ideal_w = width_from_max_height
            ideal_h = height_from_max

        if ideal_w < MIN_VIDEO_W:
            mini_w = MIN_VIDEO_W
            mini_h = MAX_MINI_H
            # Scale en largeur fixe puis crop vertical centré (supprime les bandes noires internes)
            crop_filter = (
                f"scale={mini_w}:-1,"
                f"crop={mini_w}:{mini_h}:0:(in_h-{mini_h})/2"
            )
        else:
            mini_w = ideal_w
            mini_h = ideal_h
            crop_filter = f"scale={mini_w}:{mini_h}"

        bw2 = BORDER_W * 2
        mini_total_w = mini_w + bw2
        mini_total_h = mini_h + bw2

        # Position horizontale : centré
        border_x = (CANVAS_W - mini_total_w) // 2

        # Position verticale : centré dans la zone disponible sous le logo
        remaining = available_h - mini_total_h
        vertical_center = int(remaining // 2)
        border_y = LOGO_H + SPACING_TOP + vertical_center

        vf = (
            f"[1:v]{crop_filter},"
            f"pad={mini_total_w}:{mini_total_h}:{BORDER_W}:{BORDER_W}:color={border_col}[mini];"
            f"[0:v][mini]overlay={border_x}:{border_y}[outv]"
        )

        # Tentative GPU (h264_nvenc) inspirée de video_generator_simple / crop
        if use_gpu:
            cmd_gpu = [
                "ffmpeg", "-y",
                "-i", looped_bg, "-i", content, "-i", audio_path,
                "-filter_complex", vf,
                "-map", "[outv]", "-map", "2:a",
                "-c:v", "h264_nvenc",
                "-preset", "p4",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "0",
                "-maxrate", "15M",
                "-bufsize", "30M",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_file),
            ]
            code = run_ffmpeg(cmd_gpu, log_path)
            if code == 0:
                with open(log_path, "a", encoding="utf-8", errors="replace") as log:
                    log.write(f"[portrait] ✓ GPU réussi → {output_file}\n")
                return output_file

            with open(log_path, "a", encoding="utf-8", errors="replace") as log:
                log.write(f"[portrait] GPU échoué (code {code}) — fallback CPU...\n")
                log.flush()

        # Fallback CPU (libx264 medium, qualité un peu meilleure que background)
        check_ffmpeg(
            [
                "ffmpeg", "-y",
                "-i", looped_bg, "-i", content, "-i", audio_path,
                "-filter_complex", vf,
                "-map", "[outv]", "-map", "2:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(output_file),
            ],
            log_path,
            "Assemblage portrait échoué",
        )

    try:
        os.remove(looped_bg)
    except Exception:
        pass

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[portrait] ✓ → {output_file}\n")

    return output_file
