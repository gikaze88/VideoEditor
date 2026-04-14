"""
Pipeline: landscape
Génère une vidéo paysage 1920×1080 avec mini-vidéo positionnée librement.
C'est le pendant paysage du pipeline portrait (1080×1920).

Paramètres :
    background_video_path : str   — vidéo de fond 1920×1080
    content_path          : str   — vidéo ou audio à intégrer
    audio_only            : bool  — si True, pas de mini-vidéo (audio seul)
    border_color          : str   — couleur de bordure (white, black, gold…)
    use_gpu               : bool  — tenter h264_nvenc, fallback CPU auto
    size_percent          : int   — taille de la mini-vidéo en % de son max (10-100, défaut 90)
    position_x_pct        : float — centre X de la mini-vidéo en % du canvas (0–100, défaut 75)
    position_y_pct        : float — centre Y de la mini-vidéo en % du canvas (0–100, défaut 75)

Sync audio/vidéo :
    L'audio est pris DIRECTEMENT depuis content (-map 1:a) sans extraction
    MP3 intermédiaire → pas de délai d'encodeur libmp3lame.
"""
import subprocess
import os
from pathlib import Path
from ._ffmpeg import check_ffmpeg, run_ffmpeg, slug_from_title

CANVAS_W    = 1920
CANVAS_H    = 1080
MAX_MINI_W  = 760   # largeur max mini-vidéo
MAX_MINI_H  = 680   # hauteur max (préserve les visages sur les formats variés)
MIN_VIDEO_H = 400   # hauteur minimale avant recadrage
BORDER_W    = 3
EDGE_MARGIN = 20    # marge minimale en pixels par rapport aux bords


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


def _compute_position_pct(
    mini_total_w: int, mini_total_h: int,
    x_pct: float, y_pct: float,
) -> tuple[int, int]:
    """Calcule (border_x, border_y) depuis des pourcentages de position (0.0–1.0).

    x_pct / y_pct représentent le centre de la mini-vidéo relativement au canvas 1920×1080.
    Le résultat est clampé pour ne jamais dépasser les bords (EDGE_MARGIN).
    """
    bx = int(CANVAS_W * x_pct - mini_total_w / 2)
    by = int(CANVAS_H * y_pct - mini_total_h / 2)
    bx = max(EDGE_MARGIN, min(CANVAS_W - mini_total_w - EDGE_MARGIN, bx))
    by = max(EDGE_MARGIN, min(CANVAS_H - mini_total_h - EDGE_MARGIN, by))
    return bx, by


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    bg_path    = params["background_video_path"]
    content    = params["content_path"]
    audio_only = params.get("audio_only", False)
    border_col = params.get("border_color", "white")
    use_gpu    = bool(params.get("use_gpu", True))
    size_pct   = max(10, min(100, int(params.get("size_percent", 90))))
    pos_x_pct  = max(0.0, min(1.0, float(params.get("position_x_pct", 75)) / 100))
    pos_y_pct  = max(0.0, min(1.0, float(params.get("position_y_pct", 50)) / 100))

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[landscape] bg={bg_path}\n")
        log.write(f"[landscape] content={content}\n")
        log.write(f"[landscape] audio_only={audio_only} gpu={use_gpu}\n")
        log.write(f"[landscape] size_percent={size_pct} pos_x={pos_x_pct:.2f} pos_y={pos_y_pct:.2f}\n")
        log.flush()

    duration  = _get_duration(content)
    bg_dur    = _get_duration(bg_path)
    loops     = int(duration / bg_dur) + 1
    looped_bg = str(output_dir / f"bg_{job_id}.mp4")

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[landscape] durée={duration:.1f}s boucles={loops}\n")
        log.flush()

    # Background bouclé (sans audio), recadré/scalé à 1920×1080
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
    base = slug_from_title(title) if title else f"landscape_{job_id}"
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
        src_w, src_h, src_ratio = _get_dimensions(content)

        # Adapter les dimensions mini-vidéo au ratio source, dans les limites MAX_MINI_W × MAX_MINI_H
        height_from_max_width = int(MAX_MINI_W / src_ratio)
        if height_from_max_width <= MAX_MINI_H:
            ideal_w = MAX_MINI_W
            ideal_h = height_from_max_width
        else:
            ideal_w = int(MAX_MINI_H * src_ratio)
            ideal_h = MAX_MINI_H

        if ideal_h < MIN_VIDEO_H:
            # Vidéo très large → forcer hauteur minimale et recadrer
            base_w = int(MIN_VIDEO_H * src_ratio)
            base_h = MIN_VIDEO_H
            mini_w = max(10, int(base_w * size_pct / 100))
            mini_h = max(10, int(base_h * size_pct / 100))
            crop_filter = (
                f"scale=-1:{mini_h},"
                f"crop={mini_w}:{mini_h}:(in_w-{mini_w})/2:0"
            )
        else:
            mini_w = max(10, int(ideal_w * size_pct / 100))
            mini_h = max(10, int(ideal_h * size_pct / 100))
            crop_filter = f"scale={mini_w}:{mini_h}"

        bw2          = BORDER_W * 2
        mini_total_w = mini_w + bw2
        mini_total_h = mini_h + bw2

        border_x, border_y = _compute_position_pct(mini_total_w, mini_total_h, pos_x_pct, pos_y_pct)

        with open(log_path, "a", encoding="utf-8", errors="replace") as log:
            log.write(f"[landscape] mini={mini_w}x{mini_h} pos=({border_x},{border_y})\n")
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
                    log.write(f"[landscape] GPU reussi -> {output_file}\n")
                return output_file

            with open(log_path, "a", encoding="utf-8", errors="replace") as log:
                log.write(f"[landscape] GPU echoue (code {code}) - fallback CPU...\n")
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
            "Assemblage landscape échoué",
        )

    try:
        os.remove(looped_bg)
    except Exception:
        pass

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[landscape] OK -> {output_file}\n")

    return output_file
