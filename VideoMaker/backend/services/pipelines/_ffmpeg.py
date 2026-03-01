"""
Utilitaire FFmpeg partagé par tous les pipelines.
Lance FFmpeg en streamant chaque ligne vers le fichier log en temps réel
→ le frontend peut voir la progression dès que FFmpeg écrit.
"""
import subprocess
from pathlib import Path


def run_ffmpeg(cmd: list, log_path: Path) -> int:
    """
    Lance FFmpeg et écrit chaque ligne de sortie dans log_path immédiatement.
    Retourne le code de retour du process.
    """
    str_cmd = [str(c) for c in cmd]

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"\n$ {' '.join(str_cmd)}\n")
        log.flush()

        proc = subprocess.Popen(
            str_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,          # line-buffered
        )

        for line in proc.stdout:
            log.write(line)
            log.flush()         # écriture immédiate → polling frontend voit la progression

        proc.wait()
        return proc.returncode


def check_ffmpeg(cmd: list, log_path: Path, error_msg: str):
    """Lance FFmpeg et lève RuntimeError si le code de retour != 0."""
    code = run_ffmpeg(cmd, log_path)
    if code != 0:
        raise RuntimeError(f"{error_msg} (code {code})")
