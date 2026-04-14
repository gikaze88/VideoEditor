"""
Pipeline: wave — waveform animée + fond vidéo.
Modes: audio | mini | hybrid
Styles: sine, bars, point, p2p, spectrum, spectrum_line, rainbow

Correction décalage audio/vidéo :
- L'ancien code extrayait l'audio en MP3 (libmp3lame) avant l'assemblage.
  Ce ré-encodage introduit un délai d'encodeur et une dérive sur longue durée.
- Fix : l'audio est pris directement depuis le fichier source (1:a ou 2:a).
  Si le fichier source est une vidéo, l'audio est extrait dans le filter_complex.
  L'atempo (accélération) est appliqué directement dans le filter_complex,
  avec asplit pour alimenter à la fois la waveform et le stream de sortie.
  → aucun ré-encodage intermédiaire, sync parfaite.
"""
import os
import subprocess
from pathlib import Path
from ._ffmpeg import check_ffmpeg, run_ffmpeg, slug_from_title

CANVAS_W = 1080
CANVAS_H = 1920
WAVE_H   = 300
WAVE_Y   = CANVAS_H - WAVE_H - 80
MINI_W   = 800
MINI_H   = 450
MINI_Y   = WAVE_Y - MINI_H - 40

WAVE_STYLE_CFG = {
    "sine":          {"uses_showwaves": True,  "mode": "line",  "rainbow": False},
    "bars":          {"uses_showwaves": True,  "mode": "cline", "rainbow": False},
    "point":         {"uses_showwaves": True,  "mode": "point", "rainbow": False},
    "p2p":           {"uses_showwaves": True,  "mode": "p2p",   "rainbow": False},
    "spectrum":      {"uses_showwaves": False, "mode": "bar",   "rainbow": False},
    "spectrum_line": {"uses_showwaves": False, "mode": "line",  "rainbow": False},
    "rainbow":       {"uses_showwaves": False, "mode": "bar",   "rainbow": True},
}


def _get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        stdin=subprocess.DEVNULL,
    )
    return float(r.stdout.strip())


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def _wave_filter(style: str, w: int, h: int, color: str) -> str:
    cfg = WAVE_STYLE_CFG.get(style, WAVE_STYLE_CFG["sine"])
    if cfg["uses_showwaves"]:
        return f"showwaves=s={w}x{h}:mode={cfg['mode']}:colors={color}:scale=sqrt,format=rgba"
    elif cfg["rainbow"]:
        return f"showspectrum=s={w}x{h}:mode={cfg['mode']}:color=rainbow:scale=sqrt,format=rgba"
    else:
        return f"showspectrum=s={w}x{h}:mode={cfg['mode']}:color=intensity:scale=sqrt,format=rgba"


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> Path:
    input_path = params["audio_path"]
    bg_path    = params.get("background_video_path")
    style      = params.get("wave_style", "sine")
    mode       = params.get("video_mode", "audio")
    mini_path  = params.get("content_video_path")
    speed      = float(params.get("speed_factor", 1.0))
    color      = params.get("wave_color", "white")
    use_gpu    = bool(params.get("use_gpu", True))

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[wave] style={style} mode={mode} speed={speed} color={color} gpu={use_gpu}\n")
        log.flush()

    # Durée prise directement depuis le fichier source (pas de MP3 intermédiaire)
    duration = _get_duration(input_path)

    if speed != 1.0:
        # La durée réelle après accélération (pour la longueur du background)
        duration = duration / speed

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[wave] durée={duration:.1f}s\n")
        log.flush()

    looped_bg = str(output_dir / f"bg_{job_id}.mp4")

    # Background
    if bg_path:
        bg_dur = _get_duration(bg_path)
        loops  = int(duration / bg_dur) + 1
        check_ffmpeg(
            ["ffmpeg", "-y",
             "-stream_loop", str(loops), "-i", bg_path,
             "-t", str(duration),
             "-vf", f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=decrease,"
                    f"pad={CANVAS_W}:{CANVAS_H}:(ow-iw)/2:(oh-ih)/2",
             "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an",
             looped_bg],
            log_path, "Boucle background échouée"
        )
    else:
        check_ffmpeg(
            ["ffmpeg", "-y",
             "-f", "lavfi", "-i", f"color=c=black:s={CANVAS_W}x{CANVAS_H}:d={duration}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "23",
             looped_bg],
            log_path, "Génération fond noir échouée"
        )

    # Assemblage final
    wf = _wave_filter(style, CANVAS_W, WAVE_H, color)
    title = params.get("title")
    base = slug_from_title(title) if title else f"wave_{style}_{job_id}"
    output_file = output_dir / f"{base}.mp4"

    # Construction du filter_complex et des inputs.
    # L'audio est pris directement depuis input_path (video ou audio) sans re-encodage.
    # L'atempo est appliqué dans le filter_complex si speed != 1.0,
    # avec asplit pour alimenter à la fois la waveform et la sortie audio.
    if mode in ("mini", "hybrid") and mini_path:
        mini_x = (CANVAS_W - MINI_W) // 2
        # inputs: [0]=looped_bg, [1]=mini_path(video), [2]=input_path(audio/video)
        audio_label = "[2:a]"
        if speed != 1.0:
            # atempo dans le filter_complex, asplit pour waveform + output
            speed_prefix = f"{audio_label}atempo={speed},asplit=2[awave][aout];"
            wave_audio   = "[awave]"
            out_audio    = "[aout]"
        else:
            speed_prefix = ""
            wave_audio   = audio_label
            out_audio    = audio_label

        vf = (
            f"{speed_prefix}"
            f"[1:v]scale={MINI_W}:{MINI_H}[mini];"
            f"[0:v][mini]overlay={mini_x}:{MINI_Y}[bg_mini];"
            f"[bg_mini]{wave_audio}{wf}[wave];"
            f"[bg_mini][wave]overlay=0:{WAVE_Y}[outv]"
        )
        base_cmd = [
            "ffmpeg", "-y",
            "-i", looped_bg, "-i", mini_path, "-i", input_path,
            "-filter_complex", vf,
            "-map", "[outv]",
        ]
        if speed != 1.0:
            base_cmd += ["-map", out_audio]
        else:
            base_cmd += ["-map", "2:a"]

    else:
        # Mode audio uniquement
        # inputs: [0]=looped_bg, [1]=input_path(audio/video)
        audio_label = "[1:a]"
        if speed != 1.0:
            speed_prefix = f"{audio_label}atempo={speed},asplit=2[awave][aout];"
            wave_audio   = "[awave]"
            out_audio    = "[aout]"
        else:
            speed_prefix = ""
            wave_audio   = audio_label
            out_audio    = audio_label

        vf = (
            f"{speed_prefix}"
            f"[0:v]{wave_audio}{wf}[wave];"
            f"[0:v][wave]overlay=0:{WAVE_Y}[outv]"
        )
        base_cmd = [
            "ffmpeg", "-y",
            "-i", looped_bg, "-i", input_path,
            "-filter_complex", vf,
            "-map", "[outv]",
        ]
        if speed != 1.0:
            base_cmd += ["-map", out_audio]
        else:
            base_cmd += ["-map", "1:a"]

    # Tentative GPU
    if use_gpu:
        cmd_gpu = [
            *base_cmd,
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "19",
            "-b:v", "0",
            "-maxrate", "15M",
            "-bufsize", "30M",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-shortest",
            str(output_file),
        ]
        code = run_ffmpeg(cmd_gpu, log_path)
        if code == 0:
            with open(log_path, "a", encoding="utf-8", errors="replace") as log:
                log.write(f"[wave] GPU reussi -> {output_file}\n")
            return output_file

        with open(log_path, "a", encoding="utf-8", errors="replace") as log:
            log.write(f"[wave] GPU echoue (code {code}) - fallback CPU...\n")
            log.flush()

    # Fallback CPU
    cmd_cpu = [
        *base_cmd,
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_file),
    ]
    check_ffmpeg(cmd_cpu, log_path, "Assemblage wave échoué")

    try:
        os.remove(looped_bg)
    except Exception:
        pass

    with open(log_path, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"[wave] OK -> {output_file}\n")

    return output_file
