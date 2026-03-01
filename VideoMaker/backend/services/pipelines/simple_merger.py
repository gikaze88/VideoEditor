"""
Pipeline: merge
Concatène plusieurs vidéos en un seul fichier (stream copy).
"""
import subprocess
import tempfile
import os
from pathlib import Path


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    """
    params attendus:
        video_paths    : list[str] — chemins absolus dans l'ordre de fusion
        reverse_order  : bool      — inverser l'ordre (défaut: False)
    """
    video_paths: list[str] = params["video_paths"]
    if params.get("reverse_order", False):
        video_paths = list(reversed(video_paths))

    if not video_paths:
        raise ValueError("Aucun fichier vidéo fourni pour la fusion")

    output_file = output_dir / f"merge_{job_id}.mp4"

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[merge] {len(video_paths)} fichier(s) à fusionner\n")
        for i, p in enumerate(video_paths, 1):
            log.write(f"[merge]   {i}. {p}\n")

        if len(video_paths) == 1:
            cmd = ["ffmpeg", "-y", "-i", video_paths[0], "-c", "copy", str(output_file)]
            log.write(f"[merge] Fichier unique — copie directe\n")
        else:
            # Créer le fichier concat temporaire
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                for p in video_paths:
                    abs_path = os.path.abspath(p).replace("\\", "/")
                    f.write(f"file '{abs_path}'\n")
                concat_file = f.name

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                str(output_file),
            ]

        log.write(f"[merge] Commande: {' '.join(cmd)}\n")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        log.write(result.stdout)

        # Nettoyage du fichier concat
        if len(video_paths) > 1:
            try:
                os.unlink(concat_file)
            except Exception:
                pass

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg a échoué (code {result.returncode})")

        log.write(f"[merge] Succès → {output_file}\n")

    return output_file
