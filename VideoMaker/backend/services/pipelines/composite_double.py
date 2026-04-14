"""
Pipeline composite_double : fond vidéo + 2 intervenants en diagonal.

Disposition :
    - Gauche : haut-gauche de l'écran
    - Droite  : bas-droite de l'écran
Lecture séquentielle : gauche joue (droite figée) → droite joue (gauche figée).
Les deux restent toujours visibles à l'écran.

params :
    background_video_path : str   — vidéo de fond
    video_left_path       : str   — vidéo intervenant gauche (joue en premier)
    video_right_path      : str   — vidéo intervenant droite (joue en second)
    size_percent          : int   — taille des speakers en % (défaut 35)
    crf                   : int   — qualité CRF libx264 (défaut 23)
    fps                   : int   — fps de sortie (défaut 30)
"""
from pathlib import Path
from ._ffmpeg import check_ffmpeg, get_duration, slug_from_title

OUT_W, OUT_H = 1920, 1080

# Positions par défaut en % du canvas
# Speaker gauche : ancré coin haut-gauche → grandit vers la droite et le bas
LEFT_X_PCT    = 2.6
LEFT_Y_PCT    = 4.6
# Speaker droit  : ancré par son coin bas-droit → grandit vers la gauche et le haut
# Les valeurs correspondent au coin bas-droit du bloc à la taille par défaut (35%).
# Formule : rx = int(OUT_W * RIGHT_X_END_PCT/100) - w
#            ry = int(OUT_H * RIGHT_Y_END_PCT/100) - h
RIGHT_X_END_PCT = 97.4   # bord droit fixé à ~97 % du canvas (1870 px)
RIGHT_Y_END_PCT = 95.4   # bord bas  fixé à ~95 % du canvas (1030 px)


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> str:
    bg_path    = Path(params["background_video_path"])
    left_path  = Path(params["video_left_path"])
    right_path = Path(params["video_right_path"])
    size_pct   = int(params.get("size_percent", 35))
    crf        = int(params.get("crf", 23))
    fps        = int(params.get("fps", 30))

    left_dur  = get_duration(left_path)
    right_dur = get_duration(right_path)
    total_dur = left_dur + right_dur

    w  = int(OUT_W * size_pct / 100)
    h  = int(OUT_H * size_pct / 100)
    lx = int(OUT_W * LEFT_X_PCT    / 100)
    ly = int(OUT_H * LEFT_Y_PCT    / 100)
    # Droit : bord bas-droit fixe → le bloc grandit vers la gauche et le haut
    rx = max(0, int(OUT_W * RIGHT_X_END_PCT / 100) - w)
    ry = max(0, int(OUT_H * RIGHT_Y_END_PCT / 100) - h)

    title = params.get("title")
    base = slug_from_title(title) if title else f"composite_double_{job_id}"
    output = output_dir / f"{base}.mp4"

    # Gauche : joue puis se fige pendant right_dur
    # Droite  : figée pendant left_dur puis joue
    filter_complex = (
        f"[0:v]loop=loop=-1:size=32767:start=0,"
        f"scale={OUT_W}:{OUT_H},fps={fps}[bg_loop];"
        f"[1:v]scale={w}:{h},fps={fps}[left_scaled];"
        f"[2:v]scale={w}:{h},fps={fps}[right_scaled];"
        f"[left_scaled]tpad=stop_mode=clone:stop_duration={right_dur}[left_ext];"
        f"[right_scaled]tpad=start_duration={left_dur}:start_mode=clone[right_ext];"
        f"[bg_loop][left_ext]overlay=x={lx}:y={ly}[bg_left];"
        f"[bg_left][right_ext]overlay=x={rx}:y={ry}[final_video];"
        f"[1:a]apad=pad_dur={right_dur}[la];"
        f"[2:a]adelay={int(left_dur * 1000)}|{int(left_dur * 1000)}[ra];"
        f"[la][ra]amix=inputs=2:duration=longest[final_audio]"
    )

    check_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", str(bg_path),
            "-i", str(left_path),
            "-i", str(right_path),
            "-filter_complex", filter_complex,
            "-map", "[final_video]",
            "-map", "[final_audio]",
            "-t", str(total_dur),
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-r", str(fps),
            "-c:a", "aac", "-b:a", "128k",
            str(output),
        ],
        log_path,
        "Erreur encodage composite double",
    )

    return str(output)
