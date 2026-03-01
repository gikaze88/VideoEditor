"""
Pipeline: wave
Génère une vidéo avec visualisation audio animée (waveform / spectre).
Adapté de video_generator_wave.py, wave_acc.py, wave_mini_vid.py.

Modes vidéo:
  "audio"  → fond vidéo + waveform seulement
  "mini"   → fond vidéo + waveform + mini-vidéo en overlay
  "hybrid" → fond vidéo + mini-vidéo et waveform côte à côte

Styles waveform: sine, bars, point, p2p, spectrum, spectrum_line, rainbow
"""
import subprocess
import os
import json
from pathlib import Path


# ─── Configuration des styles ────────────────────────────────────────────────

WAVE_STYLE_CFG = {
    "sine":          {"filter": "showwaves", "mode": "line",  "uses_showwaves": True},
    "bars":          {"filter": "showwaves", "mode": "cline", "uses_showwaves": True},
    "point":         {"filter": "showwaves", "mode": "point", "uses_showwaves": True},
    "p2p":           {"filter": "showwaves", "mode": "p2p",   "uses_showwaves": True},
    "spectrum":      {"filter": "showspectrum", "mode": "bar",  "uses_showwaves": False},
    "spectrum_line": {"filter": "showspectrum", "mode": "line", "uses_showwaves": False},
    "rainbow":       {"filter": "showspectrum", "mode": "bar",  "uses_showwaves": False, "rainbow": True},
}

# Dimensions canvas portrait
CANVAS_W = 1080
CANVAS_H = 1920
WAVE_H   = 300   # hauteur de la bande waveform
WAVE_Y   = CANVAS_H - WAVE_H - 80   # position verticale

# Mini-vidéo (mode mini/hybrid)
MINI_W = 800
MINI_H = 450
MINI_Y = WAVE_Y - MINI_H - 40


# ─── Utilitaires ─────────────────────────────────────────────────────────────

def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    return float(r.stdout.strip())


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def _extract_audio(input_path: str, out_path: str, log) -> str:
    log.write(f"[wave] Extraction audio depuis {input_path}...\n")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-vn", "-acodec", "libmp3lame", "-q:a", "2", out_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    log.write(r.stdout)
    if r.returncode != 0:
        raise RuntimeError("Extraction audio échouée")
    return out_path


def _speed_audio(audio_path: str, speed: float, out_path: str, log) -> str:
    log.write(f"[wave] Accélération audio x{speed}...\n")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", audio_path,
         "-filter:a", f"atempo={speed}",
         "-acodec", "libmp3lame", "-q:a", "2", out_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    log.write(r.stdout)
    if r.returncode != 0:
        raise RuntimeError("Accélération audio échouée")
    return out_path


def _loop_background(bg_path: str, duration: float, out_path: str, log) -> str:
    bg_dur = _get_duration(bg_path)
    loops = int(duration / bg_dur) + 1
    log.write(f"[wave] Boucle background: {loops} fois sur {duration:.1f}s\n")
    r = subprocess.run(
        ["ffmpeg", "-y",
         "-stream_loop", str(loops), "-i", bg_path,
         "-t", str(duration),
         "-vf", f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=decrease,"
                f"pad={CANVAS_W}:{CANVAS_H}:(ow-iw)/2:(oh-ih)/2",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an",
         out_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    log.write(r.stdout)
    if r.returncode != 0:
        raise RuntimeError("Boucle background échouée")
    return out_path


def _build_wave_filter(style: str, w: int, h: int, color: str = "white") -> str:
    cfg = WAVE_STYLE_CFG.get(style, WAVE_STYLE_CFG["sine"])
    if cfg["uses_showwaves"]:
        return (f"showwaves=s={w}x{h}:mode={cfg['mode']}:"
                f"colors={color}:scale=sqrt,format=rgba")
    elif cfg.get("rainbow"):
        return (f"showspectrum=s={w}x{h}:mode={cfg['mode']}:"
                f"color=rainbow:scale=sqrt,format=rgba")
    else:
        return (f"showspectrum=s={w}x{h}:mode={cfg['mode']}:"
                f"color=intensity:scale=sqrt,format=rgba")


# ─── Pipeline principal ───────────────────────────────────────────────────────

def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    """
    params attendus:
        audio_path            : str         — fichier audio ou vidéo source
        background_video_path : str|None    — vidéo de fond (None = couleur noire)
        wave_style            : str         — sine|bars|point|p2p|spectrum|spectrum_line|rainbow
        video_mode            : str         — audio|mini|hybrid
        content_video_path    : str|None    — vidéo source du mini-overlay (mode mini/hybrid)
        speed_factor          : float       — 1.0 (normal) ou 1.25 (accéléré)
        wave_color            : str         — couleur waveform (défaut: white)
    """
    input_path = params["audio_path"]
    bg_path    = params.get("background_video_path")
    style      = params.get("wave_style", "sine")
    mode       = params.get("video_mode", "audio")
    mini_path  = params.get("content_video_path")
    speed      = float(params.get("speed_factor", 1.0))
    color      = params.get("wave_color", "white")

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[wave] style={style} mode={mode} speed={speed}\n")

        # 1. Extraire l'audio si besoin
        if _is_video(input_path):
            audio_path = _extract_audio(
                input_path, str(output_dir / f"audio_{job_id}.mp3"), log)
        else:
            audio_path = input_path

        # 2. Accélérer si nécessaire
        if speed != 1.0:
            audio_path = _speed_audio(
                audio_path, speed, str(output_dir / f"audio_sped_{job_id}.mp3"), log)

        duration = _get_duration(audio_path)
        log.write(f"[wave] Durée: {duration:.1f}s\n")

        # 3. Préparer le background
        if bg_path:
            looped_bg = str(output_dir / f"bg_{job_id}.mp4")
            _loop_background(bg_path, duration, looped_bg, log)
        else:
            # Fond noir généré
            looped_bg = str(output_dir / f"bg_{job_id}.mp4")
            log.write(f"[wave] Génération fond noir {CANVAS_W}x{CANVAS_H}...\n")
            r = subprocess.run(
                ["ffmpeg", "-y",
                 "-f", "lavfi", "-i",
                 f"color=c=black:s={CANVAS_W}x{CANVAS_H}:d={duration}",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                 looped_bg],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
            log.write(r.stdout)
            if r.returncode != 0:
                raise RuntimeError("Génération fond noir échouée")

        # 4. Construire le filtre FFmpeg selon le mode
        wave_filter = _build_wave_filter(style, CANVAS_W, WAVE_H, color)
        output_file = output_dir / f"wave_{style}_{job_id}.mp4"

        if mode == "audio":
            # Fond + waveform en overlay bas
            vf = (
                f"[0:v][1:a]{wave_filter}[wave];"
                f"[0:v][wave]overlay=0:{WAVE_Y}[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-i", looped_bg,
                "-i", audio_path,
                "-filter_complex", vf,
                "-map", "[outv]",
                "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_file),
            ]

        elif mode in ("mini", "hybrid") and mini_path:
            # Fond + mini-vidéo + waveform
            mini_x = (CANVAS_W - MINI_W) // 2
            vf = (
                f"[1:v]scale={MINI_W}:{MINI_H}[mini];"
                f"[0:v][mini]overlay={mini_x}:{MINI_Y}[bg_mini];"
                f"[bg_mini][2:a]{wave_filter}[wave];"
                f"[bg_mini][wave]overlay=0:{WAVE_Y}[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-i", looped_bg,
                "-i", mini_path,
                "-i", audio_path,
                "-filter_complex", vf,
                "-map", "[outv]",
                "-map", "2:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_file),
            ]
        else:
            # Fallback: mode audio si pas de mini-vidéo
            vf = (
                f"[0:v][1:a]{wave_filter}[wave];"
                f"[0:v][wave]overlay=0:{WAVE_Y}[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-i", looped_bg,
                "-i", audio_path,
                "-filter_complex", vf,
                "-map", "[outv]",
                "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_file),
            ]

        log.write(f"[wave] Commande: {' '.join(cmd)}\n")
        r = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        log.write(r.stdout)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg wave échoué (code {r.returncode})")

        # Nettoyage
        try:
            os.remove(looped_bg)
        except Exception:
            pass

        log.write(f"[wave] Succès → {output_file}\n")

    return output_file
