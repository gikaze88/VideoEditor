from pathlib import Path

# Racine du projet VideoMaker (dossier contenant backend/ et frontend/)
PROJECT_ROOT = Path(__file__).parent.parent

# Dossier des outputs (vidéos générées par job)
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Dossier des vidéos sources uploadées pour l'éditeur
SOURCES_DIR = PROJECT_ROOT / "sources"
SOURCES_DIR.mkdir(exist_ok=True)

# Base de données SQLite
DB_PATH = Path(__file__).parent / "jobs.db"

# YouTube API (client OAuth installé)
CLIENT_SECRETS_PATH = PROJECT_ROOT / "client_secrets.json"
YOUTUBE_TOKEN_PATH  = PROJECT_ROOT / "youtube_token.json"

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
    # Préparation
    "extract":          "Extraire un segment vidéo",
    "crop":             "Recadrer (supprimer des bordures)",
    "merge":            "Fusionner plusieurs vidéos",
    # Génération standard
    "podcast":          "Vidéo podcast (fond + audio)",
    "wave":             "Vidéo avec waveform animée",
    "portrait":         "Vidéo portrait 1080×1920",
    "landscape":        "Vidéo paysage 1920×1080",
    # Débat / composite
    "debate_single":    "Débat — 1 intervenant (centré)",
    "debate_double":    "Débat — 2 intervenants (diagonal)",
    "debate_diagonal":  "Débat — 3 intervenants (escalier)",
}

# Niveaux de qualité CRF pour les composites
COMPOSITE_QUALITY = {
    "haute":   18,
    "bonne":   23,
    "rapide":  28,
}
