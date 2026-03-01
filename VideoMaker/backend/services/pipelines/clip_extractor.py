"""
Pipeline: extract
Extrait un segment de vidéo par plage de temps (stream copy, sans ré-encodage).
"""
import subprocess
from pathlib import Path


def _parse_time(time_str: str) -> int:
    """Convertit HH:MM:SS, MM:SS ou secondes en secondes."""
    s = str(time_str).strip()
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(s)


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    """
    params attendus:
        video_path  : str — chemin absolu vers la vidéo source
        start_time  : str — ex. "00:01:30" ou "90"
        end_time    : str — ex. "00:02:45" ou "165"
    """
    video_path = params["video_path"]
    start_sec = _parse_time(params["start_time"])
    end_sec = _parse_time(params["end_time"])
    duration = end_sec - start_sec

    if duration <= 0:
        raise ValueError(f"end_time ({params['end_time']}) doit être après start_time ({params['start_time']})")

    output_file = output_dir / f"extract_{job_id}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", video_path,
        "-t", str(duration),
        "-c", "copy",
        str(output_file),
    ]

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[extract] Commande: {' '.join(cmd)}\n")
        log.write(f"[extract] Source: {video_path}\n")
        log.write(f"[extract] Segment: {params['start_time']} → {params['end_time']} ({duration}s)\n")

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
            raise RuntimeError(f"FFmpeg a échoué (code {result.returncode})")

        log.write(f"[extract] Succès → {output_file}\n")

    return output_file
