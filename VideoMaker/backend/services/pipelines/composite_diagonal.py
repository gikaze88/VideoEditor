"""
Pipeline composite_diagonal : fond vidéo + 3 intervenants en escalier diagonal.

Disposition :
    - Gauche  : haut-gauche  (joue en 1er)
    - Centre  : milieu-centre (joue en 2ème)
    - Droite  : bas-droite   (joue en 3ème)
Les trois sont toujours visibles ; lecture séquentielle avec freeze.

params :
    background_video_path : str   — vidéo de fond
    video_left_path       : str   — intervenant gauche (1er)
    video_center_path     : str   — intervenant centre (2ème)
    video_right_path      : str   — intervenant droite (3ème)
    size_percent          : int   — taille des speakers en % (défaut 28)
    crf                   : int   — qualité CRF libx264 (défaut 23)
    fps                   : int   — fps de sortie (défaut 30)
"""
from pathlib import Path
from ._ffmpeg import check_ffmpeg, get_duration

OUT_W, OUT_H = 1920, 1080

# Positions par défaut en % (identiques aux scripts originaux)
LEFT_X_PCT   = 5
LEFT_Y_PCT   = 8
CENTER_X_PCT = 36
CENTER_Y_PCT = 36
RIGHT_X_PCT  = 67
RIGHT_Y_PCT  = 64


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> str:
    bg_path     = Path(params["background_video_path"])
    left_path   = Path(params["video_left_path"])
    center_path = Path(params["video_center_path"])
    right_path  = Path(params["video_right_path"])
    size_pct    = int(params.get("size_percent", 28))
    crf         = int(params.get("crf", 23))
    fps         = int(params.get("fps", 30))

    left_dur   = get_duration(left_path)
    center_dur = get_duration(center_path)
    right_dur  = get_duration(right_path)
    total_dur  = left_dur + center_dur + right_dur

    w  = int(OUT_W * size_pct / 100)
    h  = int(OUT_H * size_pct / 100)
    lx = int(OUT_W * LEFT_X_PCT   / 100)
    ly = int(OUT_H * LEFT_Y_PCT   / 100)
    cx = int(OUT_W * CENTER_X_PCT / 100)
    cy = int(OUT_H * CENTER_Y_PCT / 100)
    rx = int(OUT_W * RIGHT_X_PCT  / 100)
    ry = int(OUT_H * RIGHT_Y_PCT  / 100)

    output = output_dir / "composite_diagonal.mp4"

    # Chaque vidéo étendue pour couvrir la durée totale :
    # - gauche  : joue left_dur, figée pour (center+right)_dur
    # - centre  : figée left_dur, joue center_dur, figée right_dur
    # - droite  : figée (left+center)_dur, joue right_dur
    filter_complex = (
        f"[0:v]loop=loop=-1:size=32767:start=0,"
        f"scale={OUT_W}:{OUT_H},fps={fps}[bg_loop];"
        f"[1:v]scale={w}:{h},fps={fps}[lv];"
        f"[2:v]scale={w}:{h},fps={fps}[cv];"
        f"[3:v]scale={w}:{h},fps={fps}[rv];"
        f"[lv]tpad=stop_mode=clone:stop_duration={center_dur + right_dur}[lv_ext];"
        f"[cv]tpad=start_duration={left_dur}:start_mode=clone,"
        f"tpad=stop_mode=clone:stop_duration={right_dur}[cv_ext];"
        f"[rv]tpad=start_duration={left_dur + center_dur}:start_mode=clone[rv_ext];"
        f"[bg_loop][lv_ext]overlay=x={lx}:y={ly}[bg_l];"
        f"[bg_l][cv_ext]overlay=x={cx}:y={cy}[bg_lc];"
        f"[bg_lc][rv_ext]overlay=x={rx}:y={ry}[final_video];"
        f"[1:a]apad=pad_dur={center_dur + right_dur}[la];"
        f"[2:a]adelay={int(left_dur * 1000)}|{int(left_dur * 1000)},"
        f"apad=pad_dur={right_dur}[ca];"
        f"[3:a]adelay={int((left_dur + center_dur) * 1000)}|{int((left_dur + center_dur) * 1000)}[ra];"
        f"[la][ca][ra]amix=inputs=3:duration=longest[final_audio]"
    )

    check_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", str(bg_path),
            "-i", str(left_path),
            "-i", str(center_path),
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
        "Erreur encodage composite diagonal",
    )

    return str(output)
