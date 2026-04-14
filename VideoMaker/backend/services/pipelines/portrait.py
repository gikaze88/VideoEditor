"""
Pipeline: portrait
Génère une vidéo portrait 1080×1920 avec mini-vidéo centrée.

Paramètres :
    background_video_path : str   — vidéo de fond 1080×1920
    content_path          : str   — vidéo ou audio à intégrer
    audio_only            : bool  — si True, pas de mini-vidéo (audio seul)
    border_color          : str   — couleur de bordure (white, black, gold…)
    use_gpu               : bool  — tenter h264_nvenc, fallback CPU auto
    size_percent          : int   — taille de la mini-vidéo en % de son max (10-100, défaut 90)
    position              : str   — position dans la zone basse :
                                    "top-left"    | "top"     | "top-right"
                                    "left"        | "center"  | "right"
                                    "bottom-left" | "bottom"  | "bottom-right"

Sync audio/vidéo :
    L'audio est pris DIRECTEMENT depuis content (-map 1:a) sans extraction
    MP3 intermédiaire → pas de délai d'encodeur libmp3lame.
"""
import subprocess
import os
from pathlib import Path
from ._ffmpeg import check_ffmpeg, run_ffmpeg, slug_from_title

CANVAS_W    = 1080
CANVAS_H    = 1920
LOGO_H      = 960
SPACING_TOP = 100
SPACING_BOTTOM = 100
MAX_MINI_H  = 760
MIN_VIDEO_W = 600
MAX_VIDEO_W = 680
BORDER_W    = 3
EDGE_MARGIN = 20   # marge minimale en pixels par rapport aux bords


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        stdin=subprocess.DEVNULL,
    )
    return float(r.stdout.strip())


def _get_dimensions(path: str) -> tuple[int, int, float]:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
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


def _parse_position(position: str) -> tuple[str, str]:
    """Retourne (h_align, v_align) depuis un preset de position.

    Exemples :
        "top-left"     → ("left",   "top")
        "center"       → ("center", "center")
        "bottom-right" → ("right",  "bottom")
    """
    pos = position.lower().strip()
    # aliases simples
    if pos in ("top", "bottom"):
        return "center", pos
    if pos in ("left", "right"):
        return pos, "center"
    if pos == "center":
        return "center", "center"

    parts = pos.split("-")
    v = next((p for p in parts if p in ("top", "bottom", "center")), "center")
    h = next((p for p in parts if p in ("left", "right", "center")), "center")
    return h, v


def _compute_position(
    mini_total_w: int, mini_total_h: int,
    h_align: str, v_align: str,
) -> tuple[int, int]:
    """Calcule (border_x, border_y) dans le canvas portrait.

    Zone disponible pour la mini-vidéo : de LOGO_H+SPACING_TOP à CANVAS_H-SPACING_BOTTOM.
    """
    zone_top = LOGO_H + SPACING_TOP
    zone_h   = CANVAS_H - SPACING_BOTTOM - zone_top
    remaining_h = max(0, zone_h - mini_total_h)
    remaining_w = CANVAS_W - mini_total_w

    if h_align == "left":
        bx = EDGE_MARGIN
    elif h_align == "right":
        bx = max(EDGE_MARGIN, CANVAS_W - mini_total_w - EDGE_MARGIN)
    else:
        bx = max(0, remaining_w // 2)

    if v_align == "top":
        by = zone_top + EDGE_MARGIN
    elif v_align == "bottom":
        by = zone_top + max(0, remaining_h - EDGE_MARGIN)
    else:
        by = zone_top + remaining_h // 2

    return bx, by


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    bg_path    = params["background_video_path"]
    content    = params["content_path"]
    audio_only = params.get("audio_only", False)
    border_col = params.get("border_color", "white")
    use_gpu    = bool(params.get("use_gpu", True))
    size_pct   = max(10, min(100, int(params.get("size_percent", 90))))
    position   = params.get("position", "center")

    h_align, v_align = _parse_position(position)

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[portrait] bg={bg_path}\n")
        log.write(f"[portrait] content={content}\n")
        log.write(f"[portrait] audio_only={audio_only} gpu={use_gpu}\n")
        log.write(f"[portrait] size_percent={size_pct} position={position} ({h_align},{v_align})\n")
        log.flush()

    # Durée prise directement sur le fichier content (pas d'extraction MP3)
    duration = _get_duration(content)
    bg_dur   = _get_duration(bg_path)
    loops    = int(duration / bg_dur) + 1
    looped_bg = str(output_dir / f"bg_{job_id}.mp4")

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[portrait] durée={duration:.1f}s boucles={loops}\n")
        log.flush()

    # Background bouclé (sans audio)
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

    title = params.get("title")
    base = slug_from_title(title) if title else f"portrait_{job_id}"
    output_file = output_dir / f"{base}.mp4"

    if audio_only or not _is_video(content):
        # content est audio → mux direct, pas d'overlay vidéo
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
        # content est une vidéo → overlay mini-vidéo
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

        # Appliquer size_percent sur les dimensions max calculées
        if ideal_w < MIN_VIDEO_W:
            base_w = MIN_VIDEO_W
            base_h = MAX_MINI_H
            mini_w = max(10, int(base_w * size_pct / 100))
            mini_h = max(10, int(base_h * size_pct / 100))
            crop_filter = (
                f"scale={mini_w}:-1,"
                f"crop={mini_w}:{mini_h}:0:(in_h-{mini_h})/2"
            )
        else:
            mini_w = max(10, int(ideal_w * size_pct / 100))
            mini_h = max(10, int(ideal_h * size_pct / 100))
            crop_filter = f"scale={mini_w}:{mini_h}"

        bw2 = BORDER_W * 2
        mini_total_w = mini_w + bw2
        mini_total_h = mini_h + bw2

        border_x, border_y = _compute_position(mini_total_w, mini_total_h, h_align, v_align)

        with open(log_path, "a", encoding="utf-8", errors="replace") as log:
            log.write(f"[portrait] mini={mini_w}x{mini_h} pos=({border_x},{border_y})\n")
            log.flush()

        vf = (
            f"[1:v]{crop_filter},"
            f"pad={mini_total_w}:{mini_total_h}:{BORDER_W}:{BORDER_W}:color={border_col}[mini];"
            f"[0:v][mini]overlay={border_x}:{border_y}[outv]"
        )

        base_inputs = [
            "ffmpeg", "-y",
            "-i", looped_bg, "-i", content,
            "-filter_complex", vf,
            "-map", "[outv]", "-map", "1:a",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-shortest",
        ]

        if use_gpu:
            cmd_gpu = [
                *base_inputs,
                "-c:v", "h264_nvenc",
                "-preset", "p4", "-tune", "hq",
                "-rc", "vbr", "-cq", "19",
                "-b:v", "0", "-maxrate", "15M", "-bufsize", "30M",
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
