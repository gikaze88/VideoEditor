"""
Pipeline: podcast
Génère une vidéo podcast (fond vidéo en boucle + audio).
Option : accélération audio (speed_factor).
Adapté de video_generator_podcast.py et video_generator_podcast_acc.py.
"""
import subprocess
import os
from pathlib import Path


def _get_duration(file_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return float(result.stdout.strip())


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    """
    params attendus:
        background_video_path : str
        audio_path            : str   (fichier audio ou vidéo dont on extrait l'audio)
        speed_factor          : float (1.0 = normal, 1.25 = accéléré)
    """
    bg_path = params["background_video_path"]
    input_path = params["audio_path"]
    speed = float(params.get("speed_factor", 1.0))

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[podcast] Background: {bg_path}\n")
        log.write(f"[podcast] Input: {input_path}\n")
        log.write(f"[podcast] Speed factor: {speed}\n")

        # Étape 1 : extraire l'audio si la source est une vidéo
        if _is_video(input_path):
            audio_path = str(output_dir / f"audio_{job_id}.mp3")
            log.write(f"[podcast] Extraction audio depuis vidéo...\n")
            cmd_audio = [
                "ffmpeg", "-y", "-i", input_path,
                "-vn", "-acodec", "libmp3lame", "-q:a", "2",
                audio_path,
            ]
            r = subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace")
            log.write(r.stdout)
            if r.returncode != 0:
                raise RuntimeError("Extraction audio échouée")
        else:
            audio_path = input_path

        # Étape 2 : appliquer l'accélération si nécessaire
        if speed != 1.0:
            sped_audio = str(output_dir / f"audio_sped_{job_id}.mp3")
            log.write(f"[podcast] Accélération audio x{speed}...\n")
            cmd_speed = [
                "ffmpeg", "-y", "-i", audio_path,
                "-filter:a", f"atempo={speed}",
                "-acodec", "libmp3lame", "-q:a", "2",
                sped_audio,
            ]
            r = subprocess.run(cmd_speed, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace")
            log.write(r.stdout)
            if r.returncode != 0:
                raise RuntimeError("Accélération audio échouée")
            audio_path = sped_audio

        # Étape 3 : durée de l'audio final
        duration = _get_duration(audio_path)
        log.write(f"[podcast] Durée audio: {duration:.1f}s\n")

        # Étape 4 : préparer la vidéo de fond bouclée
        looped_bg = str(output_dir / f"bg_looped_{job_id}.mp4")
        bg_duration = _get_duration(bg_path)
        loops = int(duration / bg_duration) + 1
        log.write(f"[podcast] Boucles background nécessaires: {loops}\n")

        cmd_loop = [
            "ffmpeg", "-y",
            "-stream_loop", str(loops),
            "-i", bg_path,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an",
            looped_bg,
        ]
        r = subprocess.run(cmd_loop, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, encoding="utf-8", errors="replace")
        log.write(r.stdout)
        if r.returncode != 0:
            raise RuntimeError("Boucle background échouée")

        # Étape 5 : combiner vidéo + audio
        suffix = f"_x{speed}" if speed != 1.0 else ""
        output_file = output_dir / f"podcast{suffix}_{job_id}.mp4"
        cmd_final = [
            "ffmpeg", "-y",
            "-i", looped_bg,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_file),
        ]
        r = subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, encoding="utf-8", errors="replace")
        log.write(r.stdout)
        if r.returncode != 0:
            raise RuntimeError("Assemblage final échoué")

        # Nettoyage fichiers intermédiaires
        for tmp in [looped_bg]:
            try:
                os.remove(tmp)
            except Exception:
                pass

        log.write(f"[podcast] Succès → {output_file}\n")

    return output_file
