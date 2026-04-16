"""
Pipeline: merge
Concatène plusieurs vidéos (stream copy).
"""
import os
import tempfile
from pathlib import Path
from ._ffmpeg import check_ffmpeg, slug_from_title


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    video_paths: list[str] = params["video_paths"]
    if params.get("reverse_order", False):
        video_paths = list(reversed(video_paths))

    if not video_paths:
        raise ValueError("Aucun fichier vidéo fourni")

    title = params.get("title")
    base = slug_from_title(title) if title else f"merge_{job_id}"
    output_file = output_dir / f"{base}.mp4"

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[merge] {len(video_paths)} fichier(s)\n")
        for i, p in enumerate(video_paths, 1):
            log.write(f"[merge]   {i}. {p}\n")
        log.flush()

    if len(video_paths) == 1:
        cmd = ["ffmpeg", "-y", "-i", video_paths[0], "-c", "copy", str(output_file)]
    else:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for p in video_paths:
                f.write(f"file '{os.path.abspath(p).replace(chr(92), '/')}'\n")
            concat_file = f.name
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            str(output_file),
        ]

    try:
        check_ffmpeg(cmd, log_path, "Fusion échouée")
    finally:
        if len(video_paths) > 1:
            try:
                os.unlink(concat_file)
            except Exception:
                pass

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[merge] OK -> {output_file}\n")

    return output_file
