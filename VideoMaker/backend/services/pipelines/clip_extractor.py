"""
Pipeline: extract
Extrait un segment de vidéo par plage de temps (stream copy, sans ré-encodage).
"""
from pathlib import Path
from ._ffmpeg import check_ffmpeg


def _parse_time(time_str: str) -> int:
    s = str(time_str).strip()
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(s)


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    video_path = params["video_path"]
    start_sec  = _parse_time(params["start_time"])
    end_sec    = _parse_time(params["end_time"])
    duration   = end_sec - start_sec

    if duration <= 0:
        raise ValueError(f"end_time doit être après start_time")

    output_file = output_dir / f"extract_{job_id}.mp4"

    with open(log_path, "a") as log:
        log.write(f"[extract] {params['start_time']} → {params['end_time']} ({duration}s)\n")
        log.write(f"[extract] Source : {video_path}\n")
        log.flush()

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", video_path,
        "-t", str(duration),
        "-c", "copy",
        str(output_file),
    ]
    check_ffmpeg(cmd, log_path, "Extraction échouée")

    with open(log_path, "a") as log:
        log.write(f"[extract] ✓ → {output_file}\n")

    return output_file
