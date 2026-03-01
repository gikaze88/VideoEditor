"""
Pipeline batch_extract : extrait N segments d'une vidéo source et les fusionne.

params attendus :
    source_path : str         — chemin absolu vers la vidéo source
    clips       : list[dict]  — [{start: float, end: float}, ...]  (secondes)
    merge       : bool        — True = concaténer tous les clips en un seul fichier
"""
from pathlib import Path
from ._ffmpeg import check_ffmpeg


def run(job_id: str, params: dict, output_dir: Path, log_path: Path) -> str:
    source_path = Path(params["source_path"])
    clips: list[dict] = params["clips"]
    do_merge: bool = params.get("merge", True)

    if not clips:
        raise ValueError("Aucun clip à extraire")
    if not source_path.exists():
        raise ValueError(f"Source introuvable : {source_path}")

    clip_files: list[Path] = []

    for i, clip in enumerate(clips):
        start = float(clip["start"])
        end   = float(clip["end"])
        if end <= start:
            raise ValueError(f"Clip {i + 1} : fin ({end}s) ≤ début ({start}s)")

        out = output_dir / f"clip_{i + 1:02d}.mp4"

        # -ss avant -i = seek rapide (keyframe) ; -to est relatif au début du clip
        check_ffmpeg(
            [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-to", str(end),
                "-i", str(source_path),
                "-c", "copy",
                str(out),
            ],
            log_path,
            f"Erreur extraction clip {i + 1} ({start:.1f}s → {end:.1f}s)",
        )
        clip_files.append(out)

    if not do_merge or len(clip_files) == 1:
        return str(clip_files[-1])

    # Fusion de tous les clips avec concat demuxer (sans ré-encodage)
    concat_file = output_dir / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for cf in clip_files:
            f.write(f"file '{cf.as_posix()}'\n")

    merged = output_dir / "merged.mp4"
    check_ffmpeg(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(merged),
        ],
        log_path,
        "Erreur lors de la fusion des clips",
    )

    return str(merged)
