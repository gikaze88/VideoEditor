import os
import subprocess
import datetime
import sys
from pathlib import Path

# Définir les dossiers de travail
WORKING_DIR = os.path.join(os.getcwd(), "working_dir_wave")
OUTPUT_DIR = os.path.join(os.getcwd(), "video_generator_wave_output")

# Configuration des styles de visualisation audio
# Les couleurs sont maintenant personnalisables et incluent la transparence
WAVE_STYLES = {
    "sine": {
        "name": "Ondes Sinusoïdales",
        "description": "Ondes classiques qui suivent l'amplitude audio",
        "mode": "line",
        "uses_showwaves": True,
        "supports_gradient": False,
    },
    "bars": {
        "name": "Barres Verticales",
        "description": "Barres verticales style égaliseur",
        "mode": "cline",
        "uses_showwaves": True,
        "supports_gradient": False,
    },
    "point": {
        "name": "Points",
        "description": "Visualisation en points",
        "mode": "point",
        "uses_showwaves": True,
        "supports_gradient": False,
    },
    "p2p": {
        "name": "Point à Point",
        "description": "Connexions point à point",
        "mode": "p2p",
        "uses_showwaves": True,
        "supports_gradient": False,
    },
    "spectrum": {
        "name": "Spectre de Fréquences",
        "description": "Analyse fréquentielle colorée (supporte gradient)",
        "mode": "bar",
        "uses_showwaves": False,
        "supports_gradient": True,
    },
    "spectrum_line": {
        "name": "Spectre Linéaire",
        "description": "Analyse fréquentielle en lignes (supporte gradient)",
        "mode": "line",
        "uses_showwaves": False,
        "supports_gradient": True,
    },
    "rainbow": {
        "name": "Arc-en-ciel",
        "description": "Barres multicolores automatiques (gradient arc-en-ciel)",
        "mode": "bar",
        "uses_showwaves": False,
        "supports_gradient": True,
        "auto_gradient": True,
    },
    "centered": {
        "name": "Barres Centrées Symétriques",
        "description": "Barres verticales centrées qui réagissent au volume (depuis le centre)",
        "mode": "cline",
        "uses_showwaves": True,
        "supports_gradient": True,
        "centered": True,
    },
    "centered_bars": {
        "name": "Barres Centrées Symétriques",
        "description": "Barres symétriques depuis le centre (haut et bas)",
        "mode": "cline",
        "uses_showwaves": True,
        "supports_gradient": True,
        "centered": True,
    },
    "bars_gradient": {
        "name": "Barres avec Gradient Vertical",
        "description": "Barres avec dégradé de couleur vertical sur chaque barre (rouge en haut, jaune en bas)",
        "mode": "bar",
        "uses_showwaves": False,
        "supports_gradient": True,
        "vertical_gradient": True,
    },
    "volume": {
        "name": "Indicateur de Volume",
        "description": "Barre de volume simple",
        "mode": "volume",
        "uses_showwaves": False,
        "supports_gradient": False,
    },
}

# Gradients prédéfinis
WAVE_GRADIENTS = {
    "fire": "0xFF0000|0xFF8000|0xFFFF00",  # Rouge -> Orange -> Jaune
    "ocean": "0x000080|0x0000FF|0x00FFFF",  # Bleu foncé -> Bleu -> Cyan
    "sunset": "0xFF00FF|0xFF0080|0xFF8000|0xFFFF00",  # Rose -> Orange -> Jaune
    "forest": "0x006400|0x00FF00|0x90EE90",  # Vert foncé -> Vert -> Vert clair
    "rainbow": "0xFF0000|0xFF8000|0xFFFF00|0x00FF00|0x0000FF|0x8000FF|0xFF00FF",  # Arc-en-ciel complet
    "purple": "0x4B0082|0x9B59B6|0xE6B0FF",  # Indigo -> Violet -> Violet clair
    "ice": "0xFFFFFF|0x87CEEB|0x0000FF",  # Blanc -> Bleu ciel -> Bleu
}

# Couleurs prédéfinies (format hex sans alpha)
WAVE_COLORS = {
    "white": "0xFFFFFF",
    "blue": "0x4A90E2",
    "green": "0x50C878",
    "purple": "0x9B59B6",
    "orange": "0xE67E22",
    "pink": "0xFF69B4",
    "yellow": "0xF1C40F",
    "cyan": "0x00CED1",
    "red": "0xFF4444",
}

# Style par défaut
DEFAULT_STYLE = "sine"

# Opacité par défaut (réduite pour un effet plus subtil)
DEFAULT_OPACITY = 0.4  # 40% - Plus discret qu'avant (était 0.6)

# Créer les dossiers s'ils n'existent pas
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)
    print(f"📁 Dossier de travail créé : {WORKING_DIR}")
    print("⚠️  Veuillez placer vos fichiers dans ce dossier:")
    print("   - background_video.mp4 (vidéo de fond)")
    print("   - votre fichier audio ou vidéo (podcast)")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"📁 Dossier de sortie créé : {OUTPUT_DIR}")

##############################
# FONCTIONS UTILITAIRES
##############################

def parse_color(color_input):
    """
    Parse une couleur depuis différents formats:
    - Nom prédéfini: "blue", "red", "white", etc.
    - Hex avec 0x: "0xFF8000"
    - Hex avec #: "#FF8000"
    - RGB: "255,128,0"
    - Gradient prédéfini: "fire", "ocean", "rainbow", etc.
    
    Retourne le format 0xRRGGBB ou un gradient si applicable
    """
    color_input = str(color_input).strip()
    
    # Si c'est un gradient prédéfini
    if color_input in WAVE_GRADIENTS:
        return WAVE_GRADIENTS[color_input]
    
    # Si c'est un nom de couleur prédéfini
    if color_input in WAVE_COLORS:
        return WAVE_COLORS[color_input]
    
    # Si c'est déjà au format hex avec 0x
    if color_input.startswith("0x") and len(color_input) == 8:
        return color_input
    
    # Si c'est au format hex avec #
    if color_input.startswith("#"):
        hex_value = color_input[1:]
        if len(hex_value) == 6:
            return f"0x{hex_value.upper()}"
    
    # Si c'est au format RGB (ex: "255,128,0")
    if "," in color_input:
        try:
            parts = color_input.split(",")
            if len(parts) == 3:
                r, g, b = [int(x.strip()) for x in parts]
                if all(0 <= c <= 255 for c in [r, g, b]):
                    return f"0x{r:02X}{g:02X}{b:02X}"
        except ValueError:
            pass
    
    # Format non reconnu, retourner blanc par défaut
    print(f"⚠️  Couleur '{color_input}' non reconnue, utilisation du blanc par défaut")
    print(f"   Formats acceptés:")
    print(f"   - Noms: {', '.join(WAVE_COLORS.keys())}")
    print(f"   - Gradients: {', '.join(WAVE_GRADIENTS.keys())}")
    print(f"   - Hex: 0xRRGGBB ou #RRGGBB")
    print(f"   - RGB: R,G,B (ex: 255,128,0)")
    return WAVE_COLORS["white"]

def get_audio_duration(file_path):
    """Retourne la durée du fichier audio/vidéo en secondes."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        duration = float(result.stdout.strip())
        return duration
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de la durée : {e}")
        return 0

def is_video_file(file_path):
    """Vérifie si le fichier est une vidéo."""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
    return Path(file_path).suffix.lower() in video_extensions

def is_audio_file(file_path):
    """Vérifie si le fichier est un audio."""
    audio_extensions = {'.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg', '.wma'}
    return Path(file_path).suffix.lower() in audio_extensions

def find_input_files():
    """
    Trouve les fichiers d'entrée dans le dossier de travail.
    Retourne: (background_video_path, audio_or_video_path)
    """
    if not os.path.exists(WORKING_DIR):
        print(f"❌ Le dossier {WORKING_DIR} n'existe pas!")
        return None, None
    
    files = os.listdir(WORKING_DIR)
    background_video = None
    input_file = None
    
    # Chercher le fichier background_video.mp4
    for file in files:
        if file.lower() == "background_video.mp4":
            background_video = os.path.join(WORKING_DIR, file)
            break
    
    # Chercher un fichier audio ou vidéo (autre que background_video.mp4)
    for file in files:
        file_path = os.path.join(WORKING_DIR, file)
        if file.lower() == "background_video.mp4":
            continue
        if is_audio_file(file_path) or is_video_file(file_path):
            input_file = file_path
            break
    
    return background_video, input_file

def extract_audio_from_video(video_path, output_audio_path):
    """Extrait l'audio d'une vidéo."""
    print(f"🎵 Extraction de l'audio depuis {os.path.basename(video_path)}...")
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",  # Pas de vidéo
            "-acodec", "libmp3lame",
            "-q:a", "2",  # Haute qualité
            output_audio_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Audio extrait : {output_audio_path}")
        return output_audio_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'extraction audio : {e}")
        return None

def prepare_background_video(background_video_path, target_duration, output_video_path):
    """
    Prépare la vidéo de fond en la bouclant pour correspondre à la durée de l'audio.
    """
    print(f"🔄 Préparation de la vidéo de fond pour une durée de {target_duration:.1f} secondes...")
    
    # Obtenir la durée de la vidéo de fond originale
    original_duration = get_audio_duration(background_video_path)
    print(f"📊 Durée vidéo originale : {original_duration:.1f}s")
    
    # Calculer le nombre de boucles nécessaires
    loop_count = int(target_duration / original_duration) + 1
    print(f"🔁 Nombre de boucles nécessaires : {loop_count}")
    
    # Boucler la vidéo et la couper à la durée exacte
    try:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loop_count),
            "-i", background_video_path,
            "-t", str(target_duration),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-an",  # Pas d'audio dans la vidéo de fond
            output_video_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo de fond préparée avec succès: {output_video_path}")
        
        # Vérifier la durée de la vidéo générée
        actual_duration = get_audio_duration(output_video_path)
        print(f"📊 Durée vidéo finale : {actual_duration:.1f}s (cible : {target_duration:.1f}s)")
        
        return output_video_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la préparation de la vidéo de fond: {e}")
        return None

def generate_waveform_video(audio_path, output_video_path, style="sine", color="white", opacity=DEFAULT_OPACITY):
    """
    Génère une vidéo de visualisation audio (waveform) à partir de l'audio avec fond transparent.
    
    Args:
        audio_path: Chemin du fichier audio
        output_video_path: Chemin de sortie pour la vidéo de waveform
        style: Style de visualisation (sine, bars, point, p2p, spectrum, rainbow, etc.)
        color: Couleur (nom, hex 0xRRGGBB, #RRGGBB, RGB r,g,b, ou gradient)
        opacity: Opacité de la wave (0.0 à 1.0, défaut: 0.4 pour un effet subtil)
    """
    print(f"🌊 Génération de la visualisation audio...")
    print(f"   Style: {WAVE_STYLES[style]['name']}")
    print(f"   Couleur: {color}")
    print(f"   Opacité: {opacity}")
    
    style_info = WAVE_STYLES[style]
    
    # Parser la couleur (supporte plusieurs formats)
    parsed_color = parse_color(color)
    
    # Vérifier si c'est un gradient (contient |)
    is_gradient = "|" in parsed_color
    
    # Afficher le type de couleur utilisé
    if is_gradient:
        colors_list = parsed_color.split("|")
        print(f"   Type: Gradient avec {len(colors_list)} couleurs")
    else:
        print(f"   Hex: {parsed_color}")
    
    # Construire le filtre selon le type de style
    if style_info["uses_showwaves"]:
        # Gérer les couleurs pour showwaves
        if is_gradient and not style_info.get("centered"):
            # Les styles non-centrés ne supportent pas les gradients
            color_hex = parsed_color.split("|")[0]
            print(f"   ⚠️  Ce style ne supporte pas les gradients, utilisation de la première couleur")
        elif is_gradient and style_info.get("centered"):
            # Les styles centrés supportent les gradients
            colors_with_opacity = "|".join([f"{c}@{opacity}" for c in parsed_color.split("|")])
            color_hex = colors_with_opacity
        else:
            color_hex = f"{parsed_color}@{opacity}"
        
        # Vérifier si c'est un style centré (symétrique)
        if style_info.get("centered"):
            # Mode cline crée des barres verticales centrées automatiquement
            # Chaque barre traverse la ligne centrale selon le volume
            wave_filter = (
                f"[0:a]showwaves=s=1080x200:mode=cline:colors={color_hex},"
                f"colorkey=0x000000:0.01:0.1,format=rgba"
            )
        else:
            # Style normal non-centré
            wave_filter = (
                f"[0:a]showwaves=s=1080x200:mode={style_info['mode']}:colors={color_hex},"
                f"colorkey=0x000000:0.01:0.1,format=rgba"
            )
    
    elif style_info.get("mode") in ["bar", "line"] and not style_info["uses_showwaves"]:
        # Pour showfreqs qui supporte les gradients
        if is_gradient:
            # Construire la chaîne de couleurs avec opacité
            colors_with_opacity = "|".join([f"{c}@{opacity}" for c in parsed_color.split("|")])
            color_param = colors_with_opacity
        else:
            color_param = f"{parsed_color}@{opacity}"
        
        if style == "rainbow" or style_info.get("auto_gradient"):
            # Mode arc-en-ciel automatique
            wave_filter = (
                f"[0:a]showfreqs=s=1080x200:mode=bar:fscale=log:colors=channel,"
                f"format=rgba,colorchannelmixer=aa={opacity}"
            )
        elif style_info.get("vertical_gradient"):
            # Gradient vertical sur chaque barre
            # showfreqs avec le mode magma/plasma crée automatiquement un gradient vertical basé sur les fréquences
            if is_gradient:
                colors_list = parsed_color.split("|")
                # Utiliser le gradient mais inverser pour avoir les couleurs chaudes en haut
                # Les fréquences basses (bas de l'écran) seront la dernière couleur
                # Les fréquences hautes (haut de l'écran) seront la première couleur
                colors_reversed = "|".join(reversed(colors_list))
                colors_with_opacity = "|".join([f"{c}@{opacity}" for c in colors_reversed.split("|")])
                
                wave_filter = (
                    f"[0:a]showfreqs=s=1080x200:mode=bar:fscale=log:colors={colors_with_opacity},"
                    f"format=rgba"
                )
                print(f"   ℹ️  Gradient vertical: bas → haut avec {len(colors_list)} couleurs")
            else:
                # Couleur unique
                wave_filter = (
                    f"[0:a]showfreqs=s=1080x200:mode=bar:fscale=log:colors={color_param},"
                    f"format=rgba"
                )
        else:
            wave_filter = (
                f"[0:a]showfreqs=s=1080x200:mode={style_info['mode']}:fscale=log:colors={color_param},"
                f"format=rgba"
            )
    
    else:
        # Pour l'indicateur de volume
        if is_gradient:
            color_hex = parsed_color.split("|")[0]
        else:
            color_hex = parsed_color
        
        alpha_hex = format(int(opacity * 255), '02x')
        wave_filter = (
            f"[0:a]showvolume=w=1080:h=200:t=0:v=0:dm=1:ds=log:c={color_hex}{alpha_hex},"
            f"format=rgba"
        )
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-filter_complex", wave_filter,
            "-c:v", "qtrle",  # Codec QuickTime qui supporte bien la transparence
            "-pix_fmt", "argb",
            "-an",  # Pas d'audio dans la vidéo de waveform
            output_video_path.replace('.mp4', '.mov')  # MOV supporte mieux la transparence
        ]
        
        output_file = output_video_path.replace('.mp4', '.mov')
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Visualisation audio générée : {output_file}")
        return output_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la génération de la visualisation audio : {e}")
        print(f"   Détails: {e.stderr if hasattr(e, 'stderr') else 'Pas de détails'}")
        return None

def overlay_waveform_on_video(background_video_path, waveform_video_path, audio_path, output_path, position="bottom"):
    """
    Superpose la visualisation audio sur la vidéo de fond avec transparence et ajoute l'audio.
    
    Args:
        background_video_path: Vidéo de fond
        waveform_video_path: Vidéo de la waveform (avec canal alpha)
        audio_path: Fichier audio
        output_path: Fichier de sortie
        position: Position de la waveform (top, center, bottom)
    """
    print(f"🎬 Superposition de la visualisation audio sur la vidéo (position: {position})...")
    
    # Calculer la position Y selon le choix
    # La vidéo fait 1080x1920 (largeur x hauteur)
    # La waveform fait 1080x200
    if position == "top":
        y_position = "100"
    elif position == "center":
        y_position = "(main_h-overlay_h)/2"
    else:  # bottom
        y_position = "main_h-overlay_h-100"
    
    try:
        # Utiliser overlay avec support alpha et forcer le format de sortie compatible
        cmd = [
            "ffmpeg", "-y",
            "-i", background_video_path,
            "-i", waveform_video_path,
            "-i", audio_path,
            "-filter_complex", f"[0:v][1:v]overlay=0:{y_position}:format=yuv420[outv]",
            "-map", "[outv]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",  # Format compatible avec tous les lecteurs
            "-profile:v", "high",   # Profile H.264 standard
            "-level", "4.0",        # Level compatible
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",         # Sample rate standard
            "-movflags", "+faststart",  # Optimisation pour la lecture web/streaming
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo finale générée : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la superposition : {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

def print_available_styles():
    """Affiche les styles de visualisation disponibles."""
    print("\n" + "=" * 70)
    print("🎨 STYLES DE VISUALISATION AUDIO DISPONIBLES")
    print("=" * 70)
    for key, style in WAVE_STYLES.items():
        default_marker = " (défaut)" if key == DEFAULT_STYLE else ""
        gradient_marker = " 🌈" if style.get("supports_gradient") else ""
        print(f"\n  {key}{default_marker}{gradient_marker}")
        print(f"    Nom: {style['name']}")
        print(f"    Description: {style['description']}")
    
    print("\n" + "=" * 70)
    print("🎨 COULEURS PRÉDÉFINIES")
    print("=" * 70)
    colors_list = ", ".join(WAVE_COLORS.keys())
    print(f"  {colors_list}")
    
    print("\n" + "=" * 70)
    print("🌈 GRADIENTS PRÉDÉFINIS (pour spectrum, spectrum_line, rainbow)")
    print("=" * 70)
    for key, value in WAVE_GRADIENTS.items():
        print(f"  {key:12} - {value}")
    
    print("\n" + "=" * 70)
    print("📐 FORMATS DE COULEUR SUPPORTÉS")
    print("=" * 70)
    print("  1. Nom prédéfini   : blue, red, white, cyan, etc.")
    print("  2. Hex avec 0x     : 0xFF8000")
    print("  3. Hex avec #      : #FF8000")
    print("  4. RGB             : 255,128,0")
    print("  5. Gradient        : fire, ocean, rainbow, sunset, etc.")
    
    print("\n" + "=" * 70)
    print("📍 USAGE")
    print("=" * 70)
    print("python video_generator_wave.py [style] [position] [couleur] [opacité]")
    
    print("\n💡 Exemples Basiques:")
    print("  python video_generator_wave.py")
    print("  python video_generator_wave.py bars bottom blue")
    print("  python video_generator_wave.py sine center cyan 0.3")
    
    print("\n🎨 Exemples avec Formats de Couleur:")
    print("  python video_generator_wave.py bars bottom 0xFF8000")
    print("  python video_generator_wave.py sine bottom #00CED1")
    print("  python video_generator_wave.py bars bottom 255,128,0")
    
    print("\n🌈 Exemples avec Gradients:")
    print("  python video_generator_wave.py spectrum bottom fire")
    print("  python video_generator_wave.py rainbow center")
    print("  python video_generator_wave.py spectrum_line bottom ocean 0.5")
    
    print("\n📋 Paramètres:")
    print("  style    : sine, bars, point, p2p, spectrum, spectrum_line, rainbow, volume")
    print("             (défaut: sine)")
    print("  position : top, center, bottom (défaut: bottom)")
    print("  couleur  : nom, 0xRRGGBB, #RRGGBB, R,G,B, ou gradient (défaut: white)")
    print("  opacité  : 0.0 à 1.0 (défaut: 0.4)")
    print("=" * 70 + "\n")

##############################
# PIPELINE PRINCIPAL
##############################

def main(style=DEFAULT_STYLE, position="bottom", color="white", opacity=DEFAULT_OPACITY):
    """
    Pipeline principal pour la génération de vidéos podcast avec visualisation audio.
    
    Args:
        style: Style de visualisation (sine, bars, point, p2p, spectrum, volume)
        position: Position de la waveform (top, center, bottom)
        color: Couleur de la wave (white, blue, green, purple, orange, pink, yellow, cyan, red)
        opacity: Opacité de la wave (0.0 à 1.0)
    """
    print("=" * 60)
    print("🎙️🌊 GÉNÉRATEUR DE VIDÉO PODCAST AVEC VISUALISATION AUDIO")
    print("=" * 60)
    print(f"Style sélectionné: {WAVE_STYLES[style]['name']}")
    print(f"Position: {position}")
    print(f"Couleur: {color}")
    print(f"Opacité: {opacity}")
    
    # Étape 1: Trouver les fichiers d'entrée
    print("\n📂 Recherche des fichiers d'entrée...")
    background_video_path, input_file_path = find_input_files()
    
    if not background_video_path:
        print("❌ Fichier background_video.mp4 introuvable dans le dossier de travail!")
        print(f"   Veuillez placer votre fichier dans : {WORKING_DIR}")
        return
    
    if not input_file_path:
        print("❌ Aucun fichier audio ou vidéo trouvé dans le dossier de travail!")
        print(f"   Veuillez placer votre fichier dans : {WORKING_DIR}")
        return
    
    print(f"✅ Vidéo de fond trouvée : {os.path.basename(background_video_path)}")
    print(f"✅ Fichier d'entrée trouvé : {os.path.basename(input_file_path)}")
    
    # Étape 2: Déterminer si c'est un audio ou une vidéo
    is_video = is_video_file(input_file_path)
    is_audio = is_audio_file(input_file_path)
    
    if not is_video and not is_audio:
        print("❌ Le fichier d'entrée n'est ni un audio ni une vidéo reconnu!")
        return
    
    # Étape 3: Extraire l'audio si nécessaire
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if is_video:
        print(f"\n🎥 Type de fichier détecté : VIDÉO")
        temp_audio_path = os.path.join(OUTPUT_DIR, f"extracted_audio_{timestamp}.mp3")
        audio_path = extract_audio_from_video(input_file_path, temp_audio_path)
        if not audio_path:
            return
    else:
        print(f"\n🎵 Type de fichier détecté : AUDIO")
        audio_path = input_file_path
    
    # Étape 4: Obtenir la durée de l'audio
    audio_duration = get_audio_duration(audio_path)
    if audio_duration == 0:
        print("❌ Impossible de déterminer la durée de l'audio!")
        return
    
    print(f"⏱️  Durée de l'audio : {audio_duration:.2f} secondes ({audio_duration/60:.2f} minutes)")
    
    # Étape 5: Préparer la vidéo de fond bouclée
    looped_video_path = os.path.join(OUTPUT_DIR, f"looped_background_wave_{timestamp}.mp4")
    looped_video = prepare_background_video(background_video_path, audio_duration, looped_video_path)
    if not looped_video:
        return
    
    # Étape 6: Générer la visualisation audio
    waveform_video_path = os.path.join(OUTPUT_DIR, f"waveform_{style}_{timestamp}.mp4")
    waveform_video = generate_waveform_video(audio_path, waveform_video_path, style, color, opacity)
    if not waveform_video:
        return
    
    # Étape 7: Superposer la waveform sur la vidéo de fond et ajouter l'audio
    input_basename = Path(input_file_path).stem
    final_output_path = os.path.join(OUTPUT_DIR, f"podcast_wave_{input_basename}_{style}_{timestamp}.mp4")
    final_video = overlay_waveform_on_video(looped_video, waveform_video, audio_path, final_output_path, position)
    
    if not final_video:
        print("❌ Échec de la génération de la vidéo finale!")
        return
    
    # Vérifier que le fichier final MP4 existe bien
    if not os.path.exists(final_output_path):
        print(f"❌ Le fichier final n'a pas été créé : {final_output_path}")
        return
    
    print(f"✅ Fichier final MP4 vérifié : {os.path.basename(final_output_path)} ({os.path.getsize(final_output_path) / (1024*1024):.2f} MB)")
    
    # Étape 8: Nettoyer les fichiers temporaires
    print("\n🧹 Nettoyage des fichiers temporaires...")
    try:
        # Supprimer le fichier .mov temporaire
        if os.path.exists(waveform_video):
            os.remove(waveform_video)
            print(f"   ✅ Fichier temporaire supprimé : {os.path.basename(waveform_video)}")
    except Exception as e:
        print(f"   ⚠️  Impossible de supprimer le fichier temporaire : {e}")
    
    # Étape 9: Résumé
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print(f"📹 Vidéo finale : {final_output_path}")
    print(f"🌊 Style de visualisation : {WAVE_STYLES[style]['name']}")
    print(f"🎨 Couleur : {color} (opacité {opacity})")
    print(f"📍 Position : {position}")
    print(f"📊 Durée : {audio_duration/60:.2f} minutes")
    print(f"📁 Dossier de sortie : {OUTPUT_DIR}")
    print("=" * 60)
    print(f"\n💡 Astuce: Le fichier final est en format MP4 et compatible avec tous les lecteurs")
    print("=" * 60)

if __name__ == "__main__":
    # Gestion des arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "help"]:
            print_available_styles()
            sys.exit(0)
        
        # Récupérer le style
        style_arg = sys.argv[1].lower()
        if style_arg not in WAVE_STYLES:
            print(f"❌ Style '{style_arg}' non reconnu!")
            print_available_styles()
            sys.exit(1)
        
        # Récupérer la position (optionnelle)
        position_arg = "bottom"
        if len(sys.argv) > 2:
            position_arg = sys.argv[2].lower()
            if position_arg not in ["top", "center", "bottom"]:
                print(f"❌ Position '{position_arg}' non reconnue! Utilisez: top, center, ou bottom")
                sys.exit(1)
        
        # Récupérer la couleur (optionnelle)
        color_arg = "white"
        if len(sys.argv) > 3:
            color_arg = sys.argv[3]
            # Ne pas faire de validation ici, parse_color() s'en chargera
            # Cela permet d'accepter tous les formats: noms, hex, RGB, gradients
        
        # Récupérer l'opacité (optionnelle)
        opacity_arg = DEFAULT_OPACITY
        if len(sys.argv) > 4:
            try:
                opacity_arg = float(sys.argv[4])
                if not (0.0 <= opacity_arg <= 1.0):
                    print(f"❌ L'opacité doit être entre 0.0 et 1.0 (reçu: {opacity_arg})")
                    sys.exit(1)
            except ValueError:
                print(f"❌ L'opacité doit être un nombre décimal (ex: 0.4)")
                sys.exit(1)
        
        print(f"🎯 Arguments détectés: style='{style_arg}', position='{position_arg}', couleur='{color_arg}', opacité={opacity_arg}")
        
        try:
            main(style=style_arg, position=position_arg, color=color_arg, opacity=opacity_arg)
        except KeyboardInterrupt:
            print("\n\n⚠️  Processus interrompu par l'utilisateur.")
        except Exception as e:
            print(f"\n\n❌ Erreur inattendue : {e}")
            import traceback
            traceback.print_exc()
    else:
        # Utiliser les valeurs par défaut
        print(f"🎯 Utilisation du style par défaut: '{DEFAULT_STYLE}', position: 'bottom'")
        print("💡 Astuce: Lancez 'python video_generator_wave.py --help' pour voir tous les styles disponibles")
        
        try:
            main(style=DEFAULT_STYLE, position="bottom")
        except KeyboardInterrupt:
            print("\n\n⚠️  Processus interrompu par l'utilisateur.")
        except Exception as e:
            print(f"\n\n❌ Erreur inattendue : {e}")
            import traceback
            traceback.print_exc()

