"""
Pipeline: portrait
Génère une vidéo portrait 1080×1920 avec mini-vidéo centrée.

Correction décalage audio/vidéo :
- L'ancien code extrayait l'audio en MP3 (ré-encodage libmp3lame)
  puis l'utilisait comme source audio séparée. Ce ré-encodage introduit
  un délai d'encodeur (~576 échantillons) et une dérive sur les longues vidéos.
- Fix : l'audio est pris DIRECTEMENT depuis le fichier content (-map 1:a)
  exactement comme dans video_generator_simple.py (ligne ""-map", "1:a"").
  Aucune extraction intermédiaire → sync parfaite video+audio.
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
MAX_MINI_H  = 760
MIN_VIDEO_W = 600
MAX_VIDEO_W = 680
BORDER_W    = 3


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        stdin=subprocess.DEVNULL,
    )
    return float(r.stdout.strip())


def _get_dimensions(path: str) -> tuple[int, int, float]:
    """Retourne (w, h, ratio) de la vidéo, comme dans video_generator_simple.py."""
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
        stdin=subprocess.DEVNULL,
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

    # 1. Durée prise DIRECTEMENT sur le fichier content (aucune extraction MP3)
    #    → évite le délai d'encodeur libmp3lame et la dérive audio/vidéo
    duration = _get_duration(content)
    bg_dur   = _get_duration(bg_path)
    loops    = int(duration / bg_dur) + 1
    looped_bg = str(output_dir / f"bg_{job_id}.mp4")

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[portrait] durée={duration:.1f}s boucles={loops}\n")
        log.flush()

    # 2. Background bouclé (sans audio)
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
        # content est audio (ou forcé audio-only) → mux direct
        # Seuls 2 inputs : background bouclé + content audio
        check_ffmpeg(
            ["ffmpeg", "-y",
             "-i", looped_bg, "-i", content,
             "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
             "-shortest",
             str(output_file)],
            log_path, "Assemblage audio échoué"
        )
    else:
        # content est une vidéo → overlay mini-vidéo + audio pris de 1:a
        # (exactement comme video_generator_simple.py : "-map", "1:a")
        src_w, src_h, src_ratio = _get_dimensions(content)

        available_h = CANVAS_H - LOGO_H - SPACING_TOP - SPACING_BOTTOM
        assert int(available_h) == MAX_MINI_H

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

        border_x = (CANVAS_W - mini_total_w) // 2

        remaining = available_h - mini_total_h
        vertical_center = int(remaining // 2)
        border_y = LOGO_H + SPACING_TOP + vertical_center

        # filter_complex : uniquement 2 inputs [looped_bg, content]
        # [1:v] → mini-vidéo overlay
        # [1:a] → audio DIRECT depuis content (pas de MP3 intermédiaire)
        vf = (
            f"[1:v]{crop_filter},"
            f"pad={mini_total_w}:{mini_total_h}:{BORDER_W}:{BORDER_W}:color={border_col}[mini];"
            f"[0:v][mini]overlay={border_x}:{border_y}[outv]"
        )

        # Commandes communes pour GPU et CPU (2 inputs seulement)
        base_inputs = [
            "ffmpeg", "-y",
            "-i", looped_bg, "-i", content,
            "-filter_complex", vf,
            "-map", "[outv]", "-map", "1:a",   # ← audio direct depuis content
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-shortest",
        ]

        if use_gpu:
            cmd_gpu = [
                *base_inputs,
                "-c:v", "h264_nvenc",
                "-preset", "p4",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "0",
                "-maxrate", "15M",
                "-bufsize", "30M",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_file),
            ]
            code = run_ffmpeg(cmd_gpu, log_path)
            if code == 0:
                with open(log_path, "a", encoding="utf-8", errors="replace") as log:
                    log.write(f"[portrait] GPU reussi -> {output_file}\n")
                return output_file

            with open(log_path, "a", encoding="utf-8", errors="replace") as log:
                log.write(f"[portrait] GPU echoue (code {code}) - fallback CPU...\n")
                log.flush()

        # Fallback CPU
        check_ffmpeg(
            [
                *base_inputs,
                "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
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
        log.write(f"[portrait] OK -> {output_file}\n")

    return output_file
