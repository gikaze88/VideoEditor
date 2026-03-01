"""
Pipeline: crop
Recadre une vidéo en supprimant des pixels de chaque côté.
Supporte l'encodage GPU (h264_nvenc) avec fallback CPU.
"""
import subprocess
import json
from pathlib import Path


def _get_dimensions(video_path: str) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            video_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    data = json.loads(result.stdout)
    w = data["streams"][0]["width"]
    h = data["streams"][0]["height"]
    return w, h


def _parse_value(val: str | int, dimension: int) -> int:
    s = str(val).strip()
    if s.endswith("%"):
        return int(dimension * float(s[:-1]) / 100)
    return int(s)


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    """
    params attendus:
        video_path : str
        top        : str|int  (px ou %)
        bottom     : str|int
        left       : str|int
        right      : str|int
        use_gpu    : bool  (défaut: True)
    """
    video_path = params["video_path"]
    use_gpu = params.get("use_gpu", True)

    src_w, src_h = _get_dimensions(video_path)

    top    = _parse_value(params.get("top",    0), src_h)
    bottom = _parse_value(params.get("bottom", 0), src_h)
    left   = _parse_value(params.get("left",   0), src_w)
    right  = _parse_value(params.get("right",  0), src_w)

    out_w = src_w - left - right
    out_h = src_h - top - bottom

    if out_w <= 0 or out_h <= 0:
        raise ValueError(f"Valeurs de crop invalides: résultat {out_w}x{out_h}")

    crop_filter = f"crop={out_w}:{out_h}:{left}:{top}"
    output_file = output_dir / f"crop_{job_id}.mp4"

    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", crop_filter]

    if use_gpu:
        cmd += [
            "-c:v", "h264_nvenc",
            "-preset", "p7",
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "19",
            "-b:v", "0",
            "-maxrate", "20M",
            "-bufsize", "40M",
            "-profile:v", "high",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
        ]
    else:
        cmd += [
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-crf", "18",
            "-profile:v", "high",
        ]

    cmd += [
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-pix_fmt", "yuv420p",
        str(output_file),
    ]

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[crop] Source: {video_path} ({src_w}x{src_h})\n")
        log.write(f"[crop] Crop: top={top} bottom={bottom} left={left} right={right}\n")
        log.write(f"[crop] Résultat: {out_w}x{out_h}\n")
        log.write(f"[crop] GPU: {use_gpu}\n")
        log.write(f"[crop] Commande: {' '.join(cmd)}\n")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        log.write(result.stdout)

        if result.returncode != 0:
            if use_gpu:
                log.write("[crop] GPU échoué — fallback CPU...\n")
                # Fallback CPU
                cmd_cpu = ["ffmpeg", "-y", "-i", video_path, "-vf", crop_filter,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-c:a", "aac", "-b:a", "256k", "-pix_fmt", "yuv420p",
                           str(output_file)]
                log.write(f"[crop] Fallback: {' '.join(cmd_cpu)}\n")
                result2 = subprocess.run(
                    cmd_cpu,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                log.write(result2.stdout)
                if result2.returncode != 0:
                    raise RuntimeError(f"FFmpeg CPU a échoué (code {result2.returncode})")
            else:
                raise RuntimeError(f"FFmpeg a échoué (code {result.returncode})")

        log.write(f"[crop] Succès → {output_file}\n")

    return output_file
