from pathlib import Path

# Racine du projet VideoMaker (dossier contenant backend/ et frontend/)
PROJECT_ROOT = Path(__file__).parent.parent

# Dossier des outputs (vidéos générées par job)
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Base de données SQLite
DB_PATH = Path(__file__).parent / "jobs.db"

# Accélération audio disponible
AVAILABLE_SPEED_FACTORS = [1.0, 1.25, 1.5]

# Styles de waveform disponibles
WAVE_STYLES = [
    "sine",
    "bars",
    "point",
    "p2p",
    "spectrum",
    "spectrum_line",
    "rainbow",
]

# Modes vidéo pour le générateur wave
VIDEO_MODES = ["audio", "mini", "hybrid"]

# Styles de job disponibles
JOB_STYLES = {
    "extract":  "Extraire un segment vidéo",
    "crop":     "Recadrer (supprimer des bordures)",
    "merge":    "Fusionner plusieurs vidéos",
    "podcast":  "Vidéo podcast (fond + audio)",
    "wave":     "Vidéo avec waveform animée",
    "portrait": "Vidéo portrait 1080×1920",
}
