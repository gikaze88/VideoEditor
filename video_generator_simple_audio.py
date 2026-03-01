import os
import subprocess
import datetime
import sys
import json
import argparse
from pathlib import Path

# Définir les dossiers de travail
WORKING_DIR = os.path.join(os.getcwd(), "working_dir_wave_sub")
OUTPUT_DIR = os.path.join(os.getcwd(), "video_generator_wave_sub_output")

# ═══════════════════════════════════════════════════════════════════════
# TEMPLATE POUR BACKGROUND AVEC LOGO INTÉGRÉ
# ═══════════════════════════════════════════════════════════════════════
# Le background contient déjà le logo "NEWS DU 237" qui occupe ~50% du haut
# Layout:
#   - Logo (intégré au background) : 0 → 960px
#   - Espace haut                  : 960 → 1060px (100px)
#   - Photo/Wave (adaptative)      : 1060 → 1820px (760px max)
#   - Espace bas                   : 1820 → 1920px (100px)

LOGO_ZONE_HEIGHT = 960              # Logo occupe ~50% de la hauteur (960px)
SPACING_TOP = 100                   # Espace entre logo et contenu
SPACING_BOTTOM = 100                # Espace entre contenu et bas
MAX_CONTENT_HEIGHT = 760            # Hauteur max disponible pour photo/wave

# Calcul automatique de l'espace disponible
AVAILABLE_HEIGHT = 1920 - LOGO_ZONE_HEIGHT - SPACING_TOP - SPACING_BOTTOM
assert AVAILABLE_HEIGHT == MAX_CONTENT_HEIGHT, "Erreur calcul hauteur disponible"

# Dimensions photo (si présente)
PHOTO_WIDTH = 600                   # Largeur photo (même que MIN_VIDEO_WIDTH)
PHOTO_HEIGHT = 600                  # Hauteur photo
BORDER_WIDTH = 3                    # Épaisseur de la bordure blanche

# Configuration GPU (pour accélération)
USE_GPU = True                      # Activer l'accélération GPU (NVIDIA/AMD/Intel)
GPU_ENCODER = "h264_nvenc"          # Options: h264_nvenc (NVIDIA), h264_amf (AMD), h264_qsv (Intel)

# Configuration Waveform
USE_WAVEFORM = False                # Par défaut désactivé (mettre True pour activer)
WAVEFORM_HEIGHT = 200               # Hauteur waveform si activée

# Accélération audio (défaut 1.0 = normal, modifié par --acc)
AUDIO_SPEED = 1.0

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

def is_image_file(file_path):
    """Vérifie si le fichier est une image."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return Path(file_path).suffix.lower() in image_extensions

def find_input_files():
    """Trouve les fichiers d'entrée dans le dossier de travail."""
    if not os.path.exists(WORKING_DIR):
        print(f"❌ Le dossier {WORKING_DIR} n'existe pas!")
        return None, None, None
    
    files = os.listdir(WORKING_DIR)
    background_video = None
    input_file = None
    photo_file = None
    
    # Chercher background
    for file in files:
        if file.lower() == "background_video.mp4":
            background_video = os.path.join(WORKING_DIR, file)
            break
    
    # Chercher fichier input (vidéo ou audio)
    for file in files:
        file_path = os.path.join(WORKING_DIR, file)
        if file.lower() == "background_video.mp4":
            continue
        # Ignorer les images (on les traite après)
        if is_image_file(file_path):
            continue
        if file.startswith("temp_accelerated_"):
            continue
        if is_audio_file(file_path) or is_video_file(file_path):
            input_file = file_path
            break
    
    # Chercher photo (optionnelle) - N'IMPORTE QUELLE image (sauf background)
    for file in files:
        file_path = os.path.join(WORKING_DIR, file)
        # Accepter n'importe quelle image
        if is_image_file(file_path):
            photo_file = file_path
            break
    
    return background_video, input_file, photo_file

##############################
# PRÉ-ACCÉLÉRATION AUDIO (NOUVEAU)
##############################

def accelerate_audio_properly(input_path, output_path, speed=1.25):
    """
    Pré-accélère l'audio avec atempo.
    
    Pour l'audio, on utilise juste atempo (pas de setpts/fps car audio = pas de frames).
    C'est beaucoup plus simple que la vidéo !
    
    Args:
        input_path: Audio ou vidéo source
        output_path: Audio accéléré (MP3)
        speed: Facteur d'accélération (1.25 = 25% plus rapide)
    """
    print(f"\n⚡ PRÉ-ACCÉLÉRATION AUDIO À {speed}x")
    print(f"   📂 Input: {os.path.basename(input_path)}")
    
    try:
        original_duration = get_audio_duration(input_path)
        expected_duration = original_duration / speed
        
        print(f"   ⏱️  Durée: {original_duration:.2f}s → {expected_duration:.2f}s (attendu)")
        print(f"   🔧 Audio: atempo={speed}")
        
        # Commande simple pour audio
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vn",  # Pas de vidéo
            "-af", f"atempo={speed}",
            "-acodec", "libmp3lame",
            "-q:a", "2",  # Haute qualité
            output_path
        ]
        
        print(f"   🔄 Génération audio accéléré...")
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Vérifier résultat
        new_duration = get_audio_duration(output_path)
        actual_ratio = original_duration / new_duration
        
        print(f"   ✅ Audio accéléré créé!")
        print(f"   ⏱️  Durée réelle: {new_duration:.2f}s")
        print(f"   📊 Ratio: {actual_ratio:.3f}x (attendu: {speed:.3f}x)")
        
        # Vérifier précision
        error = abs(actual_ratio - speed) / speed * 100
        if error < 1:
            print(f"   ✅ Précision: {error:.2f}% (excellent!)")
        elif error < 3:
            print(f"   ⚠️  Précision: {error:.2f}% (acceptable)")
        else:
            print(f"   ❌ Précision: {error:.2f}% (vérifier)")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Erreur FFmpeg")
        if e.stderr:
            stderr = e.stderr.decode('utf-8', errors='ignore')
            print(f"   Détails: {stderr[:500]}")
        raise
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        raise

def extract_audio_from_video(video_path, output_audio_path):
    """Extrait l'audio d'une vidéo."""
    print(f"🎵 Extraction audio de la vidéo...")
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",                  # Pas de vidéo
            "-acodec", "libmp3lame",
            "-q:a", "2",            # Qualité audio
            output_audio_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Audio extrait : {output_audio_path}")
        return output_audio_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'extraction audio: {e}")
        return None

def prepare_background_video(background_video_path, target_duration, output_video_path):
    """Prépare la vidéo de fond en la bouclant avec accélération GPU si disponible."""
    print(f"🔄 Préparation de la vidéo de fond pour une durée de {target_duration:.1f} secondes...")
    
    original_duration = get_audio_duration(background_video_path)
    print(f"📊 Durée vidéo originale : {original_duration:.1f}s")
    
    loop_count = int(target_duration / original_duration) + 1
    print(f"🔁 Nombre de boucles nécessaires : {loop_count}")
    
    try:
        # Commande de base
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loop_count),
            "-i", background_video_path,
            "-t", str(target_duration),
        ]
        
        # Ajouter encodage GPU si activé
        if USE_GPU:
            print(f"   🚀 Accélération GPU activée")
            cmd.extend([
                "-c:v", GPU_ENCODER,
                "-preset", "p7",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "0",
                "-maxrate", "15M",
                "-bufsize", "30M",
                "-spatial-aq", "1",
                "-temporal-aq", "1",
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryslow",
                "-crf", "18",
            ])
        
        cmd.extend([
            "-an",
            output_video_path
        ])
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo de fond préparée : {output_video_path}")
        
        return output_video_path
        
    except subprocess.CalledProcessError as e:
        # Fallback CPU
        if USE_GPU:
            print(f"⚠️  Erreur GPU, réessai sans accélération...")
            cmd_fallback = [
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
            try:
                subprocess.run(cmd_fallback, check=True, capture_output=True)
                print(f"✅ Vidéo de fond préparée (sans GPU) : {output_video_path}")
                return output_video_path
            except:
                pass
        
        print(f"❌ Erreur lors de la préparation de la vidéo de fond: {e}")
        return None

def create_audio_video_simple(background_video_path, audio_path, output_path, photo_path=None):
    """
    Crée une vidéo : background + audio + photo optionnelle (pas de waveform).
    Le plus simple et rapide.
    
    La photo a les MÊMES DIMENSIONS que la mini-vidéo (600x600).
    """
    print(f"🎬 Génération vidéo audio (SIMPLE - pas de waveform)...")
    
    try:
        if photo_path:
            # AVEC photo (même taille que mini-vidéo : 600x600)
            print(f"   📸 Photo détectée : {os.path.basename(photo_path)}")
            
            # Position Y = Logo + Espace + Centrage (même calcul que mini-vidéo)
            remaining_space = AVAILABLE_HEIGHT - (PHOTO_HEIGHT + BORDER_WIDTH*2)
            vertical_centering = remaining_space // 2 if remaining_space > 0 else 0
            y_position = LOGO_ZONE_HEIGHT + SPACING_TOP + vertical_centering
            x_position = f"(main_w-{PHOTO_WIDTH + BORDER_WIDTH*2})/2"
            
            print(f"   📐 Photo: {PHOTO_WIDTH}x{PHOTO_HEIGHT}")
            print(f"   📍 Position: x=centré, y={y_position}px")
            print(f"   🔲 Bordure: {BORDER_WIDTH}px blanche")
            
            cmd = [
                "ffmpeg", "-y",
                "-i", background_video_path,  # Input 0: background
                "-loop", "1",                  # Boucler la photo
                "-i", photo_path,              # Input 1: photo
                "-i", audio_path,              # Input 2: audio
                "-filter_complex",
                    # Préparer photo avec bordure (même style que mini-vidéo)
                    f"[1:v]scale={PHOTO_WIDTH}:{PHOTO_HEIGHT},"
                    f"pad={PHOTO_WIDTH + BORDER_WIDTH*2}:{PHOTO_HEIGHT + BORDER_WIDTH*2}:{BORDER_WIDTH}:{BORDER_WIDTH}:white"
                    "[photo];"
                    # Overlay sur background
                    f"[0:v][photo]overlay={x_position}:{y_position}:shortest=1[outv]",
                "-map", "[outv]",          # Vidéo
                "-map", "2:a",             # Audio (déjà accéléré si besoin)
            ]
        else:
            # SANS photo (juste background + audio)
            print(f"   ℹ️  Pas de photo - background uniquement")
            
            cmd = [
                "ffmpeg", "-y",
                "-i", background_video_path,  # Input 0: background
                "-i", audio_path,              # Input 1: audio (déjà accéléré si besoin)
                "-map", "0:v",                 # Vidéo du background
                "-map", "1:a",                 # Audio
            ]
        
        # Encodage GPU ou CPU
        if USE_GPU:
            print(f"   🚀 Encodage avec GPU")
            cmd.extend([
                "-c:v", GPU_ENCODER,
                "-preset", "p7",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "0",
                "-maxrate", "20M",
                "-bufsize", "40M",
                "-spatial-aq", "1",
                "-temporal-aq", "1",
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryslow",
                "-crf", "18",
            ])
        
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "5.1",
            "-c:a", "aac",
            "-b:a", "256k",
            "-ar", "48000",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ])
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo audio générée : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        # Fallback CPU
        if USE_GPU:
            print(f"⚠️  Erreur GPU, réessai sans accélération...")
            
            if photo_path:
                cmd_fallback = [
                    "ffmpeg", "-y",
                    "-i", background_video_path,
                    "-loop", "1",
                    "-i", photo_path,
                    "-i", audio_path,
                    "-filter_complex",
                        f"[1:v]scale={PHOTO_WIDTH}:{PHOTO_HEIGHT},"
                        f"pad={PHOTO_WIDTH + BORDER_WIDTH*2}:{PHOTO_HEIGHT + BORDER_WIDTH*2}:{BORDER_WIDTH}:{BORDER_WIDTH}:white"
                        "[photo];"
                        f"[0:v][photo]overlay={x_position}:{y_position}:shortest=1[outv]",
                    "-map", "[outv]",
                    "-map", "2:a",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    "-shortest",
                    output_path
                ]
            else:
                cmd_fallback = [
                    "ffmpeg", "-y",
                    "-i", background_video_path,
                    "-i", audio_path,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    "-shortest",
                    output_path
                ]
            
            try:
                subprocess.run(cmd_fallback, check=True, capture_output=True)
                print(f"✅ Vidéo audio générée (sans GPU) : {output_path}")
                return output_path
            except:
                pass
        
        print(f"❌ Erreur : {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

def create_audio_video_with_waveform(background_video_path, audio_path, output_path, photo_path=None):
    """
    Crée une vidéo : background + audio + waveform animée + photo optionnelle.
    Plus complexe mais avec visualisation audio.
    """
    print(f"🎬 Génération vidéo audio avec waveform...")
    
    try:
        # Calculer position Y pour waveform
        if photo_path:
            # Photo en haut (même position que mini-vidéo), waveform en bas
            remaining_space = AVAILABLE_HEIGHT - (PHOTO_HEIGHT + BORDER_WIDTH*2)
            vertical_centering = remaining_space // 2 if remaining_space > 0 else 0
            photo_y = LOGO_ZONE_HEIGHT + SPACING_TOP + vertical_centering
            wave_y = photo_y + PHOTO_HEIGHT + BORDER_WIDTH*2 + 20
            
            print(f"   📸 Photo: {PHOTO_WIDTH}x{PHOTO_HEIGHT} à y={photo_y}px")
            print(f"   🌊 Waveform: 800x{WAVEFORM_HEIGHT} à y={wave_y}px")
        else:
            # Waveform centrée
            wave_y = LOGO_ZONE_HEIGHT + SPACING_TOP + (AVAILABLE_HEIGHT - WAVEFORM_HEIGHT) // 2
            
            print(f"   🌊 Waveform: 800x{WAVEFORM_HEIGHT} à y={wave_y}px (centrée)")
        
        if photo_path:
            cmd = [
                "ffmpeg", "-y",
                "-i", background_video_path,  # Input 0: background
                "-loop", "1",
                "-i", photo_path,              # Input 1: photo
                "-i", audio_path,              # Input 2: audio (déjà accéléré si besoin)
                "-filter_complex",
                    # Photo avec bordure
                    f"[1:v]scale={PHOTO_WIDTH}:{PHOTO_HEIGHT},"
                    f"pad={PHOTO_WIDTH + BORDER_WIDTH*2}:{PHOTO_HEIGHT + BORDER_WIDTH*2}:{BORDER_WIDTH}:{BORDER_WIDTH}:white"
                    "[photo];"
                    # Waveform depuis audio (déjà accéléré)
                    f"[2:a]showwaves=s=800x{WAVEFORM_HEIGHT}:mode=line:rate=30:colors=white[wave];"
                    # Combiner tout
                    f"[0:v][photo]overlay=(main_w-{PHOTO_WIDTH + BORDER_WIDTH*2})/2:{photo_y}[tmp];"
                    f"[tmp][wave]overlay=(main_w-800)/2:{wave_y}:shortest=1[outv]",
                "-map", "[outv]",
                "-map", "2:a",  # Audio déjà accéléré
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", background_video_path,  # Input 0: background
                "-i", audio_path,              # Input 1: audio (déjà accéléré si besoin)
                "-filter_complex",
                    # Waveform uniquement
                    f"[1:a]showwaves=s=800x{WAVEFORM_HEIGHT}:mode=line:rate=30:colors=white[wave];"
                    f"[0:v][wave]overlay=(main_w-800)/2:{wave_y}:shortest=1[outv]",
                "-map", "[outv]",
                "-map", "1:a",
            ]
        
        # Encodage GPU ou CPU
        if USE_GPU:
            print(f"   🚀 Encodage avec GPU")
            cmd.extend([
                "-c:v", GPU_ENCODER,
                "-preset", "p7",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "0",
                "-maxrate", "20M",
                "-bufsize", "40M",
                "-spatial-aq", "1",
                "-temporal-aq", "1",
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryslow",
                "-crf", "18",
            ])
        
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "5.1",
            "-c:a", "aac",
            "-b:a", "256k",
            "-ar", "48000",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ])
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo audio avec waveform générée : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur génération waveform: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

##############################
# PIPELINE PRINCIPAL
##############################

def main():
    """Pipeline audio avec option accélération."""
    global AUDIO_SPEED
    
    # Parser arguments
    parser = argparse.ArgumentParser(description='Générateur Vidéo Audio NEWS DU 237')
    parser.add_argument('--acc', action='store_true',
                       help='Accélérer à 1.25x (audio uniquement)')
    
    args = parser.parse_args()
    
    if args.acc:
        AUDIO_SPEED = 1.25
    
    print("=" * 60)
    print("🎙️ GÉNÉRATEUR VIDÉO AUDIO (INTERVIEWS)")
    print("=" * 60)
    print("Mode: Background + Audio + Photo optionnelle")
    if AUDIO_SPEED != 1.0:
        print(f"⚡ ACCÉLÉRATION {AUDIO_SPEED}x ACTIVÉE")
    if USE_WAVEFORM:
        print("Waveform: ACTIVÉE 🌊")
    else:
        print("Waveform: DÉSACTIVÉE (mode simple)")
    print("=" * 60)
    
    # Trouver fichiers
    print("\n📂 Recherche des fichiers...")
    background_video_path, input_file_path, photo_path = find_input_files()
    
    if not background_video_path or not input_file_path:
        print("❌ Fichiers manquants!")
        print(f"   Veuillez placer dans {WORKING_DIR}:")
        print(f"   - background_video.mp4 (requis)")
        print(f"   - votre vidéo ou audio (requis)")
        print(f"   - photo.jpg ou photo.png (optionnel)")
        return
    
    print(f"✅ Background: {os.path.basename(background_video_path)}")
    print(f"✅ Input: {os.path.basename(input_file_path)}")
    
    if photo_path:
        print(f"✅ Photo: {os.path.basename(photo_path)}")
    else:
        print(f"ℹ️  Pas de photo (background uniquement)")
    
    # Déterminer type
    is_video = is_video_file(input_file_path)
    is_audio = is_audio_file(input_file_path)
    
    if not is_video and not is_audio:
        print("❌ Type de fichier non reconnu!")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extraire audio si vidéo
    if is_video:
        print(f"\n🎥 Vidéo détectée - extraction audio...")
        audio_path = os.path.join(OUTPUT_DIR, f"extracted_audio_{timestamp}.mp3")
        audio_path = extract_audio_from_video(input_file_path, audio_path)
        if not audio_path:
            return
    else:
        print(f"\n🎵 Audio détecté")
        audio_path = input_file_path
    
    # ÉTAPE 1: Pré-accélération audio si nécessaire
    working_audio_path = audio_path
    if AUDIO_SPEED != 1.0:
        accelerated_audio_path = os.path.join(OUTPUT_DIR, f"temp_audio_accelerated_{timestamp}.mp3")
        try:
            working_audio_path = accelerate_audio_properly(
                audio_path,
                accelerated_audio_path,
                speed=AUDIO_SPEED
            )
        except Exception as e:
            print(f"\n❌ ÉCHEC PRÉ-ACCÉLÉRATION AUDIO")
            print(f"Erreur: {e}")
            return
    
    # Sauvegarder durée originale AVANT nettoyage (pour stats)
    original_duration_for_stats = get_audio_duration(input_file_path)
    
    # Durée (de l'audio de travail, accéléré ou non)
    audio_duration = get_audio_duration(working_audio_path)
    if audio_duration == 0:
        print("❌ Impossible de déterminer la durée de l'audio")
        return
    
    print(f"⏱️  Durée: {audio_duration:.2f}s ({audio_duration/60:.2f} min)")
    
    # Préparer background
    looped_video_path = os.path.join(OUTPUT_DIR, f"looped_bg_{timestamp}.mp4")
    looped_video = prepare_background_video(background_video_path, audio_duration, looped_video_path)
    if not looped_video:
        return
    
    # Générer vidéo finale
    input_basename = Path(input_file_path).stem
    final_output_path = os.path.join(OUTPUT_DIR, f"podcast_audio_{input_basename}_{timestamp}.mp4")
    
    print(f"\n🎬 Génération de la vidéo finale...")
    
    if USE_WAVEFORM:
        # Avec waveform (plus complexe)
        final_video = create_audio_video_with_waveform(
            looped_video, working_audio_path, final_output_path, photo_path
        )
    else:
        # Simple (par défaut)
        final_video = create_audio_video_simple(
            looped_video, working_audio_path, final_output_path, photo_path
        )
    
    if not final_video:
        print("❌ Échec génération!")
        return
    
    if not os.path.exists(final_output_path):
        print(f"❌ Fichier non créé!")
        return
    
    file_size = os.path.getsize(final_output_path) / (1024*1024)
    print(f"✅ Fichier vérifié: {os.path.basename(final_output_path)} ({file_size:.2f} MB)")
    
    # Nettoyer fichiers temporaires
    print("\n🧹 Nettoyage...")
    try:
        if os.path.exists(looped_video_path):
            os.remove(looped_video_path)
            print(f"   ✅ Background bouclé supprimé")
        
        if is_video and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"   ✅ Audio extrait supprimé")
        
        # Nettoyer audio accéléré si existe
        if AUDIO_SPEED != 1.0:
            accelerated_audio_path = os.path.join(OUTPUT_DIR, f"temp_audio_accelerated_{timestamp}.mp3")
            if os.path.exists(accelerated_audio_path):
                os.remove(accelerated_audio_path)
                print(f"   ✅ Audio accéléré temporaire supprimé")
    except:
        pass
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE!")
    print("=" * 60)
    print(f"📹 Fichier: {final_output_path}")
    print(f"🎬 Mode: Audio" + (" + Waveform" if USE_WAVEFORM else " Simple"))
    if AUDIO_SPEED != 1.0:
        gain = original_duration_for_stats - audio_duration
        print(f"⚡ Accélération: {AUDIO_SPEED}x")
        print(f"⏱️  Gain temps: {gain:.1f}s ({gain/original_duration_for_stats*100:.1f}%)")
    if photo_path:
        print(f"📸 Photo: Incluse ({PHOTO_WIDTH}x{PHOTO_HEIGHT})")
    else:
        print(f"📸 Photo: Aucune (background uniquement)")
    print(f"⏱️  Durée: {audio_duration/60:.2f} min")
    print(f"💾 Taille: {file_size:.1f} MB")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()