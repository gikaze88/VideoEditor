import os
import subprocess
import datetime
import sys
import ctypes.util
import json
from pathlib import Path

# --- Monkey-patch for Windows (Whisper) ---
_orig_find_library = ctypes.util.find_library
def patched_find_library(name):
    result = _orig_find_library(name)
    if name == "c" and result is None:
        return "msvcrt"
    return result
ctypes.util.find_library = patched_find_library

# Définir les dossiers de travail
WORKING_DIR = os.path.join(os.getcwd(), "working_dir_wave_sub")
OUTPUT_DIR = os.path.join(os.getcwd(), "video_generator_wave_sub_output")

# Configuration des modes vidéo
VIDEO_MODES = {
    "audio": "Mode audio pur avec visualisation (waveform)",
    "mini": "Mode mini-vidéo : vidéo redimensionnée en bas",
    "hybrid": "Mode hybride : mini-vidéo + waveform côte à côte",
}

DEFAULT_VIDEO_MODE = "audio"

# Dimensions de la mini-vidéo pour mode mini (ajustable)
MINI_VIDEO_WIDTH = 800
MINI_VIDEO_HEIGHT = 450
MINI_VIDEO_MARGIN_BOTTOM = 150  # Distance depuis le bas

# Dimensions pour le mode hybride (ajustable)
HYBRID_VIDEO_WIDTH = 700   # Largeur de la mini-vidéo en mode hybride
HYBRID_VIDEO_HEIGHT = 800  # Hauteur de la mini-vidéo (augmentée pour format portrait)
HYBRID_WAVEFORM_HEIGHT = 120  # Hauteur de la waveform (réduite)
HYBRID_SPACING = 10  # Espacement entre vidéo et waveform (réduit)
HYBRID_MARGIN_BOTTOM = 80  # Distance depuis le bas (réduite pour descendre le bloc)

# Configuration des styles de visualisation audio
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
    "fire": "0xFF0000|0xFF8000|0xFFFF00",
    "ocean": "0x000080|0x0000FF|0x00FFFF",
    "sunset": "0xFF00FF|0xFF0080|0xFF8000|0xFFFF00",
    "forest": "0x006400|0x00FF00|0x90EE90",
    "rainbow": "0xFF0000|0xFF8000|0xFFFF00|0x00FF00|0x0000FF|0x8000FF|0xFF00FF",
    "purple": "0x4B0082|0x9B59B6|0xE6B0FF",
    "ice": "0xFFFFFF|0x87CEEB|0x0000FF",
}

# Couleurs prédéfinies
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
DEFAULT_OPACITY = 0.4

# Créer les dossiers s'ils n'existent pas
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)
    print(f"📁 Dossier de travail créé : {WORKING_DIR}")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"📁 Dossier de sortie créé : {OUTPUT_DIR}")

##############################
# FONCTIONS UTILITAIRES
##############################

def get_video_dimensions(video_path):
    """
    Récupère les dimensions (largeur, hauteur) et l'aspect ratio d'une vidéo.
    Retourne: (width, height, aspect_ratio, is_portrait)
    """
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        data = json.loads(result.stdout)
        width = data['streams'][0]['width']
        height = data['streams'][0]['height']
        aspect_ratio = width / height
        is_portrait = height > width
        
        print(f"📐 Dimensions vidéo détectées : {width}x{height} (ratio: {aspect_ratio:.2f}, {'portrait' if is_portrait else 'paysage'})")
        
        return width, height, aspect_ratio, is_portrait
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture des dimensions : {e}")
        # Valeurs par défaut si erreur
        return 1920, 1080, 1.78, False

def calculate_smart_crop(src_width, src_height, target_width, target_height):
    """
    Calcule le meilleur crop/scale pour remplir les dimensions cibles.
    
    Stratégie:
    - Si la vidéo est déjà 9:16 (portrait) → scale proportionnel SANS crop
    - Si la vidéo est 16:9 et qu'on veut du 16:9 → simple scale
    - Sinon → crop intelligent pour remplir
    
    Retourne le filtre FFmpeg pour crop + scale.
    """
    src_ratio = src_width / src_height
    target_ratio = target_width / target_height
    
    print(f"   🎯 Calcul du traitement vidéo:")
    print(f"      Source: {src_width}x{src_height} (ratio {src_ratio:.2f})")
    print(f"      Cible: {target_width}x{target_height} (ratio {target_ratio:.2f})")
    
    # Détecter si la vidéo source est portrait (9:16 ou similaire)
    is_source_portrait = src_height > src_width
    is_target_portrait = target_height > target_width
    
    # CAS SPÉCIAL: Vidéo source est portrait (9:16) et target est aussi portrait
    if is_source_portrait and is_target_portrait:
        # On veut garder le format portrait sans cropper
        # Scale proportionnellement pour que la largeur = target_width
        # La hauteur sera calculée automatiquement pour garder le ratio
        
        # Calculer la nouvelle hauteur en gardant le ratio
        new_height = int((src_height / src_width) * target_width)
        
        print(f"      ✅ Vidéo portrait détectée - Scale proportionnel SANS crop")
        print(f"      📐 Nouvelle taille: {target_width}x{new_height} (ratio préservé)")
        
        # Si la nouvelle hauteur dépasse la target, on scale pour fitter la hauteur
        if new_height > target_height:
            print(f"      ⚠️  Hauteur calculée ({new_height}px) > target ({target_height}px)")
            print(f"      🔧 Ajustement: scale à la hauteur target")
            return f"scale=-1:{target_height}"  # -1 = calculer auto pour garder ratio
        else:
            # Scale pour que la largeur = target_width, hauteur auto
            return f"scale={target_width}:-1"
    
    # Si ratios similaires (différence < 10%), simple scale
    if abs(src_ratio - target_ratio) < 0.1:
        print(f"      ✅ Ratios similaires, scale direct")
        return f"scale={target_width}:{target_height}"
    
    # Si source plus étroite que target (ex: 9:16 source → 16:9 target)
    elif src_ratio < target_ratio:
        # Crop en hauteur, garder toute la largeur
        crop_height = int(src_width / target_ratio)
        crop_y = (src_height - crop_height) // 2
        print(f"      ✂️  Crop vertical: {src_width}x{crop_height} (enlève {src_height - crop_height}px en hauteur)")
        return f"crop={src_width}:{crop_height}:0:{crop_y},scale={target_width}:{target_height}"
    
    # Si source plus large que target (ex: 16:9 source → 9:16 target)
    else:
        # Crop en largeur, garder toute la hauteur
        crop_width = int(src_height * target_ratio)
        crop_x = (src_width - crop_width) // 2
        print(f"      ✂️  Crop horizontal: {crop_width}x{src_height} (enlève {src_width - crop_width}px en largeur)")
        return f"crop={crop_width}:{src_height}:{crop_x}:0,scale={target_width}:{target_height}"

def parse_color(color_input):
    """Parse une couleur depuis différents formats."""
    color_input = str(color_input).strip()
    
    if color_input in WAVE_GRADIENTS:
        return WAVE_GRADIENTS[color_input]
    
    if color_input in WAVE_COLORS:
        return WAVE_COLORS[color_input]
    
    if color_input.startswith("0x") and len(color_input) == 8:
        return color_input
    
    if color_input.startswith("#"):
        hex_value = color_input[1:]
        if len(hex_value) == 6:
            return f"0x{hex_value.upper()}"
    
    if "," in color_input:
        try:
            parts = color_input.split(",")
            if len(parts) == 3:
                r, g, b = [int(x.strip()) for x in parts]
                if all(0 <= c <= 255 for c in [r, g, b]):
                    return f"0x{r:02X}{g:02X}{b:02X}"
        except ValueError:
            pass
    
    print(f"⚠️  Couleur '{color_input}' non reconnue, utilisation du blanc par défaut")
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
    """Trouve les fichiers d'entrée dans le dossier de travail."""
    if not os.path.exists(WORKING_DIR):
        print(f"❌ Le dossier {WORKING_DIR} n'existe pas!")
        return None, None
    
    files = os.listdir(WORKING_DIR)
    background_video = None
    input_file = None
    
    for file in files:
        if file.lower() == "background_video.mp4":
            background_video = os.path.join(WORKING_DIR, file)
            break
    
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
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            output_audio_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Audio extrait : {output_audio_path}")
        return output_audio_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'extraction audio : {e}")
        return None

def smart_word_split(text):
    """
    Divise intelligemment le texte en mots en gardant la ponctuation attachée aux mots appropriés.
    Conserve les espaces originaux entre les signes de ponctuation.
    
    Args:
        text: Le texte à diviser
        
    Returns:
        List[str]: Liste des mots avec ponctuation correctement attachée
    """
    import re
    # 1. Split initial par espaces
    tokens = text.split()
    
    # 2. Définir les types de ponctuation
    end_punctuation = {'.', '!', '?', ';', ':', ',', '>>', '<<', '...', '--', '→', '»', ')', ']', '}'}
    start_punctuation = {'(', '[', '{', '"', "'", '«'}
    all_punctuation = end_punctuation | start_punctuation
    
    # 3. Post-traitement pour grouper la ponctuation logiquement
    processed_tokens = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        # Si c'est un mot normal (pas de ponctuation pure)
        if token not in all_punctuation:
            processed_tokens.append(token)
        else:
            # C'est de la ponctuation pure
            if token in start_punctuation:
                # Ponctuation d'ouverture: collecter jusqu'au prochain mot non-ponctuation
                punctuation_group = [token]
                j = i + 1
                
                # Collecter la séquence de ponctuation qui suit
                while j < len(tokens) and tokens[j] in all_punctuation:
                    punctuation_group.append(tokens[j])
                    j += 1
                
                # Attacher au mot suivant s'il existe
                if j < len(tokens):
                    combined = ' '.join(punctuation_group) + ' ' + tokens[j]
                    processed_tokens.append(combined)
                    i = j  # Skip tous les tokens traités
                else:
                    # Pas de mot suivant, garder la ponctuation groupée
                    processed_tokens.append(' '.join(punctuation_group))
                    i = j - 1
            else:
                # Ponctuation de fin: collecter toute la séquence qui suit
                punctuation_group = [token]
                j = i + 1
                
                # Collecter toute la séquence de ponctuation consécutive
                while j < len(tokens) and tokens[j] in all_punctuation:
                    punctuation_group.append(tokens[j])
                    j += 1
                
                # Attacher au mot précédent s'il existe
                if processed_tokens:
                    processed_tokens[-1] += ' ' + ' '.join(punctuation_group)
                else:
                    # Pas de mot précédent, garder la ponctuation groupée
                    processed_tokens.append(' '.join(punctuation_group))
                
                i = j - 1  # Skip tous les tokens de ponctuation traités
        
        i += 1
    
    return processed_tokens

def optimize_srt_for_shorts(input_srt, output_srt, max_words_per_line=3):
    """
    Optimise le fichier SRT pour le format vertical (9:16) en divisant les lignes longues.
    Divise les sous-titres en segments plus courts pour une meilleure lisibilité (max 3 mots par ligne).
    
    Args:
        input_srt: Chemin du fichier SRT d'entrée
        output_srt: Chemin du fichier SRT de sortie optimisé
        max_words_per_line: Nombre maximum de mots par ligne (défaut: 3)
    """
    import re
    
    print(f"📝 Optimisation des sous-titres pour format 9:16 (max {max_words_per_line} mots par ligne)...")
    
    with open(input_srt, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Séparer les blocs de sous-titres
    subtitle_blocks = re.split(r'\n\s*\n', content.strip())
    
    new_blocks = []
    subtitle_id = 1
    
    for block in subtitle_blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
            
        # Extraire les informations du bloc
        original_id = lines[0]
        timecode_line = lines[1]
        text_lines = ' '.join(lines[2:])  # Joindre toutes les lignes de texte
        
        # Extraire les timecodes
        timecode_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', timecode_line)
        if not timecode_match:
            # Si on ne peut pas parser le timecode, garder le bloc original
            new_blocks.append(f"{subtitle_id}\n{block[len(original_id)+1:]}")
            subtitle_id += 1
            continue
        
        # Convertir les timecodes en millisecondes
        start_h, start_m, start_s, start_ms = map(int, timecode_match.groups()[:4])
        end_h, end_m, end_s, end_ms = map(int, timecode_match.groups()[4:])
        
        start_total_ms = (start_h * 3600 + start_m * 60 + start_s) * 1000 + start_ms
        end_total_ms = (end_h * 3600 + end_m * 60 + end_s) * 1000 + end_ms
        total_duration_ms = end_total_ms - start_total_ms
        
        # Diviser le texte en segments plus courts avec gestion intelligente de la ponctuation
        words = smart_word_split(text_lines)
        
        if len(words) <= max_words_per_line:
            # Si le texte est déjà assez court, garder tel quel
            new_blocks.append(f"{subtitle_id}\n{timecode_line}\n{text_lines}")
            subtitle_id += 1
        else:
            # Diviser en segments plus courts
            segments = []
            for i in range(0, len(words), max_words_per_line):
                segment = ' '.join(words[i:i + max_words_per_line])
                segments.append(segment)
            
            # Distribuer le temps uniformément entre les segments
            segment_duration_ms = total_duration_ms // len(segments)
            
            for i, segment in enumerate(segments):
                segment_start_ms = start_total_ms + (i * segment_duration_ms)
                segment_end_ms = segment_start_ms + segment_duration_ms
                
                # Pour le dernier segment, s'assurer qu'il se termine au bon moment
                if i == len(segments) - 1:
                    segment_end_ms = end_total_ms
                
                # Convertir back en format timecode
                def ms_to_timecode(total_ms):
                    hours = total_ms // (3600 * 1000)
                    minutes = (total_ms % (3600 * 1000)) // (60 * 1000)
                    seconds = (total_ms % (60 * 1000)) // 1000
                    milliseconds = total_ms % 1000
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
                
                start_tc = ms_to_timecode(segment_start_ms)
                end_tc = ms_to_timecode(segment_end_ms)
                
                new_blocks.append(f"{subtitle_id}\n{start_tc} --> {end_tc}\n{segment}")
                subtitle_id += 1
    
    # Écrire le nouveau fichier SRT
    with open(output_srt, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(new_blocks))
        if new_blocks:  # Ajouter une ligne vide à la fin
            f.write('\n\n')
    
    total_blocks = len(new_blocks)
    print(f"✅ Fichier SRT optimisé sauvegardé: {os.path.basename(output_srt)}")
    print(f"   📊 {total_blocks} sous-titres optimisés (max {max_words_per_line} mots par ligne)")

def generate_srt_with_whisper(audio_file, output_srt):
    """
    Génère le fichier SRT avec Whisper.
    Optimise automatiquement les sous-titres pour le format 9:16 (max 3 mots par ligne).
    """
    print("🔄 Génération des sous-titres avec Whisper...")
    
    sys.path.insert(0, os.path.join(os.getcwd(), "subs_generator"))
    try:
        from srt_generator import generate_srt
        
        # Générer le SRT initial
        temp_srt = output_srt.replace('.srt', '_temp.srt')
        generated_srt_path = generate_srt(audio_file, temp_srt)
        
        if not generated_srt_path:
            return None
        
        print(f"✅ Fichier SRT généré avec succès: {os.path.basename(generated_srt_path)}")
        
        # Optimiser les sous-titres pour format 9:16 (max 3 mots par ligne)
        optimize_srt_for_shorts(temp_srt, output_srt, max_words_per_line=3)
        
        # Supprimer le fichier temporaire
        try:
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
        except:
            pass
        
        return output_srt
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération SRT: {e}")
        return None
    finally:
        if os.path.join(os.getcwd(), "subs_generator") in sys.path:
            sys.path.remove(os.path.join(os.getcwd(), "subs_generator"))

def prepare_background_video(background_video_path, target_duration, output_video_path):
    """Prépare la vidéo de fond en la bouclant."""
    print(f"🔄 Préparation de la vidéo de fond pour une durée de {target_duration:.1f} secondes...")
    
    original_duration = get_audio_duration(background_video_path)
    print(f"📊 Durée vidéo originale : {original_duration:.1f}s")
    
    loop_count = int(target_duration / original_duration) + 1
    print(f"🔁 Nombre de boucles nécessaires : {loop_count}")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loop_count),
            "-i", background_video_path,
            "-t", str(target_duration),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-an",
            output_video_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo de fond préparée : {output_video_path}")
        
        return output_video_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la préparation de la vidéo de fond: {e}")
        return None

def generate_waveform_video(audio_path, output_video_path, style="sine", color="white", opacity=DEFAULT_OPACITY, height=200):
    """Génère une vidéo de visualisation audio avec hauteur personnalisable."""
    print(f"🌊 Génération de la visualisation audio...")
    print(f"   Style: {WAVE_STYLES[style]['name']}")
    print(f"   Hauteur: {height}px")
    
    style_info = WAVE_STYLES[style]
    parsed_color = parse_color(color)
    is_gradient = "|" in parsed_color
    
    # Construire le filtre
    if style_info["uses_showwaves"]:
        if is_gradient and style_info.get("centered"):
            colors_with_opacity = "|".join([f"{c}@{opacity}" for c in parsed_color.split("|")])
            color_hex = colors_with_opacity
        else:
            if is_gradient:
                color_hex = parsed_color.split("|")[0]
            else:
                color_hex = f"{parsed_color}@{opacity}"
        
        if style_info.get("centered"):
            wave_filter = (
                f"[0:a]showwaves=s=1080x{height}:mode=cline:colors={color_hex},"
                f"colorkey=0x000000:0.01:0.1,format=rgba,colorchannelmixer=aa={opacity}"
            )
        else:
            wave_filter = (
                f"[0:a]showwaves=s=1080x{height}:mode={style_info['mode']}:colors={color_hex},"
                f"colorkey=0x000000:0.01:0.1,format=rgba,colorchannelmixer=aa={opacity}"
            )
    
    elif style_info.get("mode") in ["bar", "line"] and not style_info["uses_showwaves"]:
        if is_gradient:
            colors_with_opacity = "|".join([f"{c}@{opacity}" for c in parsed_color.split("|")])
            color_param = colors_with_opacity
        else:
            color_param = f"{parsed_color}@{opacity}"
        
        if style == "rainbow" or style_info.get("auto_gradient"):
            wave_filter = (
                f"[0:a]showfreqs=s=1080x{height}:mode=bar:fscale=log:colors=channel,"
                f"format=rgba,colorchannelmixer=aa={opacity}"
            )
        else:
            wave_filter = (
                f"[0:a]showfreqs=s=1080x{height}:mode={style_info['mode']}:fscale=log:colors={color_param},"
                f"format=rgba"
            )
    else:
        if is_gradient:
            color_hex = parsed_color.split("|")[0]
        else:
            color_hex = parsed_color
        
        alpha_hex = format(int(opacity * 255), '02x')
        wave_filter = (
            f"[0:a]showvolume=w=1080:h={height}:t=0:v=0:dm=1:ds=log:c={color_hex}{alpha_hex},"
            f"format=rgba"
        )
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-filter_complex", wave_filter,
            "-c:v", "qtrle",
            "-pix_fmt", "argb",
            "-an",
            output_video_path.replace('.mp4', '.mov')
        ]
        
        output_file = output_video_path.replace('.mp4', '.mov')
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Visualisation audio générée : {output_file}")
        return output_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la génération de la visualisation audio : {e}")
        return None

def overlay_waveform_and_subtitles(background_video_path, waveform_video_path, audio_path, subtitle_file, output_path, position="bottom"):
    """Superpose waveform + sous-titres CENTRÉS."""
    print(f"🎬 Superposition waveform + sous-titres...")
    print(f"   Waveform: {position}")
    print(f"   Sous-titres: CENTRÉS (Alignment=10)")
    
    if position == "top":
        y_position = "100"
    elif position == "center":
        y_position = "(main_h-overlay_h)/2"
    else:
        y_position = "main_h-overlay_h-100"
    
    abs_sub = os.path.abspath(subtitle_file)
    if len(abs_sub) > 1 and abs_sub[1] == ':':
        drive_letter = abs_sub[0]
        path_remainder = abs_sub[2:].replace('\\', '/')
        abs_sub = drive_letter + '\\:' + path_remainder
    else:
        abs_sub = abs_sub.replace('\\', '/')
    
    # Sous-titres CENTRÉS avec Alignment=10
    subtitle_style = ("FontName=Arturo Trial,FontSize=15,"
                     "PrimaryColour=&HFFFFFF&,"
                     "BackColour=&H80000000&,"
                     "BorderStyle=1,Outline=0,Shadow=2,"
                     "Alignment=10,MarginV=0,MarginL=20,MarginR=20")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", background_video_path,
            "-i", waveform_video_path,
            "-i", audio_path,
            "-filter_complex", 
                f"[0:v][1:v]overlay=0:{y_position}:format=yuv420[vid];"
                f"[vid]subtitles=filename='{abs_sub}':force_style='{subtitle_style}'[outv]",
            "-map", "[outv]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.0",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo avec sous-titres centrés générée : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur : {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

def overlay_mini_video_and_subtitles(background_video_path, original_video_path, 
                                     audio_path, subtitle_file, output_path):
    """Mode mini avec crop intelligent et sous-titres centrés."""
    print(f"🎬 Mode Mini-Vidéo avec crop intelligent...")
    
    # Détecter dimensions de la vidéo originale
    src_w, src_h, src_ratio, is_portrait = get_video_dimensions(original_video_path)
    
    # Calculer le crop intelligent
    crop_filter = calculate_smart_crop(src_w, src_h, MINI_VIDEO_WIDTH, MINI_VIDEO_HEIGHT)
    
    x_position = f"(main_w-{MINI_VIDEO_WIDTH})/2"
    y_position = f"main_h-{MINI_VIDEO_HEIGHT}-{MINI_VIDEO_MARGIN_BOTTOM}"
    
    print(f"   Mini-vidéo: {MINI_VIDEO_WIDTH}x{MINI_VIDEO_HEIGHT}px")
    print(f"   Position: Centrée en bas ({MINI_VIDEO_MARGIN_BOTTOM}px du bas)")
    
    abs_sub = os.path.abspath(subtitle_file)
    if len(abs_sub) > 1 and abs_sub[1] == ':':
        drive_letter = abs_sub[0]
        path_remainder = abs_sub[2:].replace('\\', '/')
        abs_sub = drive_letter + '\\:' + path_remainder
    else:
        abs_sub = abs_sub.replace('\\', '/')
    
    # Sous-titres CENTRÉS
    subtitle_style = ("FontName=Arturo Trial,FontSize=15,"
                     "PrimaryColour=&HFFFFFF&,"
                     "BackColour=&H80000000&,"
                     "BorderStyle=1,Outline=0,Shadow=2,"
                     "Alignment=10,MarginV=0,MarginL=20,MarginR=20")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", background_video_path,
            "-i", original_video_path,
            "-i", audio_path,
            "-filter_complex",
                f"[1:v]{crop_filter}[scaled];"
                f"[0:v][scaled]overlay={x_position}:{y_position}[vid];"
                f"[vid]subtitles=filename='{abs_sub}':force_style='{subtitle_style}'[outv]",
            "-map", "[outv]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.0",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Mode mini avec sous-titres centrés généré : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur : {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

def overlay_hybrid_mode(background_video_path, original_video_path, waveform_video_path,
                       audio_path, subtitle_file, output_path, style="sine"):
    """
    Mode HYBRIDE : Mini-vidéo + Waveform côte à côte (superposés verticalement).
    Dimensions adaptatives selon le format de la vidéo source.
    """
    print(f"🎬 Mode HYBRIDE : Mini-vidéo + Waveform côte à côte...")
    
    # Détecter dimensions de la vidéo originale
    src_w, src_h, src_ratio, is_portrait = get_video_dimensions(original_video_path)
    
    # DIMENSIONS ADAPTATIVES selon le format source
    # Important : limiter la hauteur max pour ne pas déborder sur les sous-titres
    if is_portrait:
        # Vidéo portrait (9:16) → Mini-vidéo plus haute mais limitée
        mini_video_width = 650   # Largeur
        mini_video_height = 700  # Hauteur maximale (limité pour laisser place aux sous-titres)
        waveform_height = 100    # Waveform fine
        margin_bottom = 40       # Encore plus proche du bas (était 50, maintenant 40)
        border_width = 3         # Épaisseur de la bordure blanche
        print(f"   📱 Format portrait détecté → Mini-vidéo: {mini_video_width}x{mini_video_height}")
    else:
        # Vidéo landscape (16:9) → Mini-vidéo plus courte
        mini_video_width = 700
        mini_video_height = 400  # Hauteur normale pour landscape
        waveform_height = 120    # Waveform standard
        margin_bottom = 50
        border_width = 3         # Épaisseur de la bordure blanche
        print(f"   🖥️  Format landscape détecté → Mini-vidéo: {mini_video_width}x{mini_video_height}")
    
    print(f"   Layout: Mini-vidéo ({mini_video_width}x{mini_video_height}) + Bordure blanche + Waveform ({mini_video_width}x{waveform_height})")
    
    # Calculer le crop/scale intelligent pour la mini-vidéo
    # IMPORTANT: Forcer les dimensions exactes (pas de -1 pour auto)
    if is_portrait:
        # Pour portrait: scale à la largeur cible, puis crop si nécessaire
        # Calculer la hauteur proportionnelle
        calculated_height = int((src_h / src_w) * mini_video_width)
        
        if calculated_height > mini_video_height:
            # Trop haut, il faut crop verticalement
            # Scale d'abord pour avoir la bonne largeur
            # Puis crop au centre pour avoir la bonne hauteur
            print(f"      📐 Hauteur calculée ({calculated_height}px) > max ({mini_video_height}px)")
            print(f"      ✂️  Scale puis crop vertical au centre")
            crop_filter = f"scale={mini_video_width}:-1,crop={mini_video_width}:{mini_video_height}:0:(in_h-{mini_video_height})/2"
        else:
            # Pas besoin de crop, simple scale
            crop_filter = f"scale={mini_video_width}:{mini_video_height}"
    else:
        # Pour landscape: utiliser le crop intelligent existant
        crop_filter = calculate_smart_crop(src_w, src_h, mini_video_width, mini_video_height)
    
    # Positions - TOUT recalculé proprement
    spacing = 10  # Petit espacement entre vidéo et waveform
    
    # Position X (centré horizontalement) - Utiliser la largeur de la mini-vidéo
    x_video = f"(main_w-{mini_video_width})/2"
    x_wave = f"(main_w-{mini_video_width})/2"
    
    # Positions Y - Les deux éléments descendent ensemble
    # Waveform est à margin_bottom du bas
    y_waveform = f"main_h-{waveform_height}-{margin_bottom}"
    
    # Vidéo est juste au-dessus de la waveform (avec spacing)
    y_video = f"main_h-{waveform_height}-{spacing}-{mini_video_height}-{margin_bottom}"
    
    total_height = mini_video_height + spacing + waveform_height
    
    print(f"   Position mini-vidéo: x={x_video}, y={y_video}")
    print(f"   Position waveform: x={x_wave}, y={y_waveform}")
    print(f"   Bordure: {border_width}px blanche autour de la mini-vidéo")
    print(f"   Hauteur totale du bloc: {total_height}px (marge: {margin_bottom}px)")
    
    # Sous-titres CENTRÉS
    abs_sub = os.path.abspath(subtitle_file)
    if len(abs_sub) > 1 and abs_sub[1] == ':':
        drive_letter = abs_sub[0]
        path_remainder = abs_sub[2:].replace('\\', '/')
        abs_sub = drive_letter + '\\:' + path_remainder
    else:
        abs_sub = abs_sub.replace('\\', '/')
    
    subtitle_style = ("FontName=Arturo Trial,FontSize=12,"
                     "PrimaryColour=&HFFFFFF&,"
                     "BackColour=&H80000000&,"
                     "BorderStyle=1,Outline=0,Shadow=2,"
                     "Alignment=10,MarginV=0,MarginL=20,MarginR=20")
    
    try:
        # Filtre complexe avec bordure blanche autour de la vidéo
        cmd = [
            "ffmpeg", "-y",
            "-i", background_video_path,  # 0
            "-i", original_video_path,     # 1
            "-i", waveform_video_path,     # 2
            "-i", audio_path,              # 3
            "-filter_complex",
                # Préparer la mini-vidéo avec dimensions EXACTES + bordure blanche
                f"[1:v]{crop_filter},"
                f"pad={mini_video_width + border_width*2}:{mini_video_height + border_width*2}:{border_width}:{border_width}:white"
                "[minivid_bordered];"
                # Redimensionner la waveform aux dimensions EXACTES
                f"[2:v]scale={mini_video_width}:{waveform_height}[wave_scaled];"
                # Overlay mini-vidéo avec bordure sur background
                f"[0:v][minivid_bordered]overlay={x_video}-{border_width}:{y_video}-{border_width}[with_video];"
                # Overlay waveform en dessous
                f"[with_video][wave_scaled]overlay={x_wave}:{y_waveform}:format=yuv420[vid];"
                # Ajouter sous-titres centrés
                f"[vid]subtitles=filename='{abs_sub}':force_style='{subtitle_style}'[outv]",
            "-map", "[outv]",
            "-map", "3:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.0",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Mode hybride avec bordure et sous-titres centrés généré : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur : {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

def print_available_styles():
    """Affiche les options disponibles."""
    print("\n" + "=" * 70)
    print("🎬 MODES VIDÉO")
    print("=" * 70)
    for key, desc in VIDEO_MODES.items():
        default_marker = " (défaut)" if key == DEFAULT_VIDEO_MODE else ""
        print(f"  {key:10}{default_marker} - {desc}")
    
    print("\n" + "=" * 70)
    print("🎨 STYLES DE VISUALISATION AUDIO")
    print("=" * 70)
    for key, style in WAVE_STYLES.items():
        default_marker = " (défaut)" if key == DEFAULT_STYLE else ""
        print(f"  {key:15}{default_marker} - {style['name']}")
    
    print("\n" + "=" * 70)
    print("📍 USAGE")
    print("=" * 70)
    print("python video_generator_wave_hybrid.py [mode] [style] [couleur] [opacité]")
    
    print("\n💡 Exemples:")
    print("  python video_generator_wave_hybrid.py audio")
    print("  python video_generator_wave_hybrid.py mini")
    print("  python video_generator_wave_hybrid.py hybrid")
    print("  python video_generator_wave_hybrid.py hybrid bars blue 0.5")
    print("=" * 70 + "\n")

##############################
# PIPELINE PRINCIPAL
##############################

def main(style=DEFAULT_STYLE, color="white", opacity=DEFAULT_OPACITY, video_mode="audio"):
    """Pipeline principal."""
    print("=" * 60)
    print("🎙️ GÉNÉRATEUR VIDÉO PODCAST - VERSION HYBRIDE")
    print("=" * 60)
    print(f"Mode: {VIDEO_MODES[video_mode]}")
    
    if video_mode in ["audio", "hybrid"]:
        print(f"Style visualisation: {WAVE_STYLES[style]['name']}")
        print(f"Couleur: {color}")
        print(f"Opacité: {opacity}")
    
    print(f"Sous-titres: Whisper (CENTRÉS)")
    print("=" * 60)
    
    # Trouver fichiers
    print("\n📂 Recherche des fichiers...")
    background_video_path, input_file_path = find_input_files()
    
    if not background_video_path or not input_file_path:
        print("❌ Fichiers manquants!")
        return
    
    print(f"✅ Background: {os.path.basename(background_video_path)}")
    print(f"✅ Input: {os.path.basename(input_file_path)}")
    
    # Déterminer type
    is_video = is_video_file(input_file_path)
    is_audio = is_audio_file(input_file_path)
    
    if not is_video and not is_audio:
        print("❌ Type de fichier non reconnu!")
        return
    
    # Extraire audio si nécessaire
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if is_video:
        print(f"\n🎥 Vidéo détectée")
        temp_audio_path = os.path.join(OUTPUT_DIR, f"extracted_audio_{timestamp}.mp3")
        audio_path = extract_audio_from_video(input_file_path, temp_audio_path)
        if not audio_path:
            return
    else:
        print(f"\n🎵 Audio détecté")
        audio_path = input_file_path
    
    # Durée
    audio_duration = get_audio_duration(audio_path)
    if audio_duration == 0:
        return
    
    print(f"⏱️  Durée: {audio_duration:.2f}s ({audio_duration/60:.2f} min)")
    
    # Préparer background
    looped_video_path = os.path.join(OUTPUT_DIR, f"looped_bg_{timestamp}.mp4")
    looped_video = prepare_background_video(background_video_path, audio_duration, looped_video_path)
    if not looped_video:
        return
    
    # Générer sous-titres
    print(f"\n📝 Génération sous-titres...")
    subtitle_file = os.path.join(OUTPUT_DIR, f"subtitles_{timestamp}.srt")
    generated_srt = generate_srt_with_whisper(audio_path, subtitle_file)
    if not generated_srt:
        print("⚠️  Pas de sous-titres, continuation...")
    
    input_basename = Path(input_file_path).stem
    
    # Génération selon le mode
    if video_mode == "hybrid" and is_video:
        print(f"\n🎬 Mode HYBRIDE activé...")
        
        # Générer waveform avec hauteur adaptée
        waveform_path = os.path.join(OUTPUT_DIR, f"waveform_{style}_{timestamp}.mp4")
        waveform_video = generate_waveform_video(audio_path, waveform_path, style, color, opacity, HYBRID_WAVEFORM_HEIGHT)
        if not waveform_video:
            return
        
        final_output_path = os.path.join(OUTPUT_DIR, f"podcast_hybrid_{input_basename}_{style}_{timestamp}.mp4")
        
        if generated_srt:
            final_video = overlay_hybrid_mode(
                looped_video, input_file_path, waveform_video,
                audio_path, generated_srt, final_output_path, style
            )
        else:
            print("⚠️  Hybride sans sous-titres non implémenté")
            final_video = None
        
        # Nettoyer waveform .mov
        if os.path.exists(waveform_video):
            try:
                os.remove(waveform_video)
            except:
                pass
                
    elif video_mode == "hybrid" and is_audio:
        print("⚠️  Mode hybride nécessite une vidéo, basculement en mode audio...")
        video_mode = "audio"
        
    if video_mode == "mini" and is_video:
        print(f"\n📺 Mode MINI activé...")
        final_output_path = os.path.join(OUTPUT_DIR, f"podcast_mini_{input_basename}_{timestamp}.mp4")
        
        if generated_srt:
            final_video = overlay_mini_video_and_subtitles(
                looped_video, input_file_path, audio_path,
                generated_srt, final_output_path
            )
        else:
            print("⚠️  Mini sans sous-titres non implémenté")
            final_video = None
            
    elif video_mode == "mini" and is_audio:
        print("⚠️  Mode mini nécessite une vidéo, basculement en mode audio...")
        video_mode = "audio"
    
    if video_mode == "audio":
        print(f"\n🌊 Mode AUDIO activé...")
        
        waveform_path = os.path.join(OUTPUT_DIR, f"waveform_{style}_{timestamp}.mp4")
        waveform_video = generate_waveform_video(audio_path, waveform_path, style, color, opacity, 200)
        if not waveform_video:
            return
        
        final_output_path = os.path.join(OUTPUT_DIR, f"podcast_audio_{input_basename}_{style}_{timestamp}.mp4")
        
        if generated_srt:
            final_video = overlay_waveform_and_subtitles(
                looped_video, waveform_video, audio_path,
                generated_srt, final_output_path, "bottom"
            )
        else:
            print("⚠️  Audio sans sous-titres non implémenté")
            final_video = None
        
        # Nettoyer waveform .mov
        if os.path.exists(waveform_video):
            try:
                os.remove(waveform_video)
            except:
                pass
    
    if not final_video:
        print("❌ Échec génération!")
        return
    
    if not os.path.exists(final_output_path):
        print(f"❌ Fichier non créé!")
        return
    
    file_size = os.path.getsize(final_output_path) / (1024*1024)
    print(f"✅ Fichier vérifié: {os.path.basename(final_output_path)} ({file_size:.2f} MB)")
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE!")
    print("=" * 60)
    print(f"📹 Fichier: {final_output_path}")
    print(f"🎬 Mode: {VIDEO_MODES[video_mode]}")
    print(f"📝 Sous-titres: {'✅ Centrés' if generated_srt else '❌'}")
    print(f"⏱️  Durée: {audio_duration/60:.2f} min")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "help"]:
            print_available_styles()
            sys.exit(0)
        
        if sys.argv[1] in VIDEO_MODES:
            video_mode_arg = sys.argv[1]
            
            if video_mode_arg in ["mini", "audio"] and len(sys.argv) == 2:
                # Mode simple sans autres paramètres
                try:
                    main(video_mode=video_mode_arg)
                except KeyboardInterrupt:
                    print("\n⚠️  Interrompu")
                except Exception as e:
                    print(f"\n❌ Erreur: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # Mode avec paramètres (audio ou hybrid)
                style_arg = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_STYLE
                
                if style_arg not in WAVE_STYLES:
                    print(f"❌ Style '{style_arg}' non reconnu!")
                    sys.exit(1)
                
                color_arg = sys.argv[3] if len(sys.argv) > 3 else "white"
                
                opacity_arg = DEFAULT_OPACITY
                if len(sys.argv) > 4:
                    try:
                        opacity_arg = float(sys.argv[4])
                        if not (0.0 <= opacity_arg <= 1.0):
                            print(f"❌ Opacité entre 0.0 et 1.0")
                            sys.exit(1)
                    except ValueError:
                        print(f"❌ Opacité invalide")
                        sys.exit(1)
                
                try:
                    main(style=style_arg, color=color_arg, opacity=opacity_arg, video_mode=video_mode_arg)
                except KeyboardInterrupt:
                    print("\n⚠️  Interrompu")
                except Exception as e:
                    print(f"\n❌ Erreur: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"❌ Mode '{sys.argv[1]}' non reconnu!")
            print_available_styles()
            sys.exit(1)
    else:
        # Défaut
        try:
            main(video_mode=DEFAULT_VIDEO_MODE)
        except KeyboardInterrupt:
            print("\n⚠️  Interrompu")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()