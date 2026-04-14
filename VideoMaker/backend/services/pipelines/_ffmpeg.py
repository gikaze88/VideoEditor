"""
Utilitaire FFmpeg — compatible Windows/threads background.

Approche : stdout + stderr redirigés DIRECTEMENT dans le fichier log
(pas de pipe Python), stdin fermé via DEVNULL.

Pourquoi :
- stdin=DEVNULL → FFmpeg ne bloque jamais en attendant une saisie clavier
- stdout/stderr → fichier directement → pas de buffering Python, le log
  est visible en temps réel dès que le frontend poll (sans pipe qui tient
  tout en mémoire jusqu'à la fin du process)
- Évite le problème Windows où l'itération `for line in proc.stdout`
  bloque car FFmpeg écrit avec \\r (carriage return) pas \\n
"""
import json
import re
import subprocess
import unicodedata
from pathlib import Path


def slug_from_title(title: str) -> str:
    """Convertit un titre humain en nom de fichier sûr.

    Exemples :
        "Mon Meilleur Titre" → "mon_meilleur_titre"
        "Débat : L'avenir ?"  → "debat_l_avenir"
    """
    s = unicodedata.normalize("NFKD", title)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s\-]+", "_", s)
    s = s.strip("_")
    return s or "output"


def run_ffmpeg(cmd: list, log_path: Path) -> int:
    """
    Lance FFmpeg et retourne son code de sortie.
    Toute la sortie (stdout + stderr) va directement dans log_path.
    """
    str_cmd = [str(c) for c in cmd]

    # Entête en mode texte
    with open(log_path, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n$ {' '.join(str_cmd)}\n")

    # Lancer FFmpeg — stdout/stderr vont directement dans le fichier log (binaire)
    with open(log_path, "ab") as f:
        proc = subprocess.Popen(
            str_cmd,
            stdin=subprocess.DEVNULL,   # critique : empêche FFmpeg de bloquer sur stdin
            stdout=f,                   # sortie directement dans le fichier
            stderr=f,                   # idem pour les erreurs / la progression
        )
        return proc.wait()


def check_ffmpeg(cmd: list, log_path: Path, error_msg: str):
    """Lance FFmpeg, lève RuntimeError si le code de retour != 0."""
    code = run_ffmpeg(cmd, log_path)
    if code != 0:
        raise RuntimeError(f"{error_msg} (code FFmpeg: {code})")


def get_duration(path: Path) -> float:
    """Retourne la durée en secondes d'un fichier vidéo/audio via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(path),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        stdin=subprocess.DEVNULL, timeout=30,
    )
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Impossible d'obtenir la durée de {path.name}: {e}")
