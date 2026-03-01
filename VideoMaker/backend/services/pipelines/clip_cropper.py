"""
Pipeline: crop
Recadre une vidéo en supprimant des pixels de chaque côté.
GPU (h264_nvenc) avec fallback CPU automatique.
"""
import subprocess
import json
from pathlib import Path
from ._ffmpeg import check_ffmpeg, run_ffmpeg


def _get_dimensions(video_path: str) -> tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "json", video_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    data = json.loads(result.stdout)
    return data["streams"][0]["width"], data["streams"][0]["height"]


def _parse_value(val, dimension: int) -> int:
    s = str(val).strip()
    if s.endswith("%"):
        return int(dimension * float(s[:-1]) / 100)
    return int(float(s))


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    video_path = params["video_path"]
    use_gpu    = params.get("use_gpu", True)

    src_w, src_h = _get_dimensions(video_path)

    top    = _parse_value(params.get("top",    0), src_h)
    bottom = _parse_value(params.get("bottom", 0), src_h)
    left   = _parse_value(params.get("left",   0), src_w)
    right  = _parse_value(params.get("right",  0), src_w)

    out_w = src_w - left - right
    out_h = src_h - top  - bottom

    if out_w <= 0 or out_h <= 0:
        raise ValueError(f"Valeurs de crop invalides : résultat {out_w}×{out_h}")

    crop_filter = f"crop={out_w}:{out_h}:{left}:{top}"
    output_file = output_dir / f"crop_{job_id}.mp4"

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[crop] Source : {video_path} ({src_w}×{src_h})\n")
        log.write(f"[crop] Supprimé : top={top} bottom={bottom} left={left} right={right}\n")
        log.write(f"[crop] Résultat : {out_w}×{out_h}\n")
        log.write(f"[crop] GPU : {use_gpu}\n")
        log.flush()

    # ── Tentative GPU ────────────────────────────────────────────────────────
    if use_gpu:
        cmd_gpu = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", crop_filter,
            "-c:v", "h264_nvenc",
            "-preset", "p4",        # bon équilibre vitesse/qualité (p1=rapide → p7=lent)
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "19",
            "-b:v", "0",
            "-maxrate", "20M",
            "-bufsize", "40M",
            "-profile:v", "high",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-pix_fmt", "yuv420p",
            str(output_file),
        ]
        code = run_ffmpeg(cmd_gpu, log_path)
        if code == 0:
            with open(log_path, "a") as log:
                log.write(f"[crop] ✓ GPU réussi → {output_file}\n")
            return output_file

        with open(log_path, "a") as log:
            log.write(f"[crop] GPU échoué (code {code}) — fallback CPU...\n")
            log.flush()

    # ── Fallback / mode CPU ──────────────────────────────────────────────────
    cmd_cpu = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", crop_filter,
        "-c:v", "libx264",
        "-preset", "medium",    # raisonnable : qualité correcte, vitesse acceptable
        "-crf", "18",
        "-profile:v", "high",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-pix_fmt", "yuv420p",
        str(output_file),
    ]
    check_ffmpeg(cmd_cpu, log_path, "Encodage CPU échoué")

    with open(log_path, "a") as log:
        log.write(f"[crop] ✓ CPU réussi → {output_file}\n")

    return output_file
