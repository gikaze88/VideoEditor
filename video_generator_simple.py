#!/usr/bin/env python3
"""
Video Generator Wave Sub - Avec Auto-Fix Colorspace
====================================================
Génère des vidéos avec mini-vidéo centrée.
Détecte et corrige automatiquement les problèmes de colorspace.
"""

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

# Configuration layout (identique à l'original)
LOGO_ZONE_HEIGHT = 960
SPACING_TOP = 100
SPACING_BOTTOM = 100
MAX_MINI_VIDEO_HEIGHT = 760
AVAILABLE_HEIGHT = 1920 - LOGO_ZONE_HEIGHT - SPACING_TOP - SPACING_BOTTOM
assert AVAILABLE_HEIGHT == MAX_MINI_VIDEO_HEIGHT, "Erreur calcul hauteur disponible"

MIN_VIDEO_WIDTH = 600
MAX_VIDEO_WIDTH = 680
MAX_WIDTH = MAX_VIDEO_WIDTH
BORDER_WIDTH = 3

# Configuration GPU
USE_GPU = True
GPU_ENCODER = "h264_nvenc"
AUDIO_SPEED = 1.0

# Créer dossiers
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)
    print(f"📁 Dossier de travail créé : {WORKING_DIR}")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"📁 Dossier de sortie créé : {OUTPUT_DIR}")

##############################
# DÉTECTION COLORSPACE
##############################

def check_colorspace(video_path):
    """Vérifie si la vidéo a des problèmes de colorspace."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=color_space,color_primaries,color_transfer',
        '-of', 'json',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            return False, "Impossible de lire les métadonnées"
        
        data = json.loads(result.stdout)
        if 'streams' not in data or len(data['streams']) == 0:
            return False, "Aucun flux vidéo trouvé"
        
        stream = data['streams'][0]
        
        # Vérifier valeurs problématiques
        issues = []
        color_space = stream.get('color_space', 'unknown')
        color_primaries = stream.get('color_primaries', 'unknown')
        color_transfer = stream.get('color_transfer', 'unknown')
        
        if color_space in ['unknown', 'reserved', 'unspecified', '']:
            issues.append(f"color_space={color_space}")
        if color_primaries in ['unknown', 'reserved', 'unspecified', '']:
            issues.append(f"color_primaries={color_primaries}")
        if color_transfer in ['unknown', 'reserved', 'unspecified', '']:
            issues.append(f"color_transfer={color_transfer}")
        
        if issues:
            return False, ", ".join(issues)
        
        return True, "OK"
        
    except Exception as e:
        return False, str(e)

def fix_colorspace(input_file):
    """Corrige les problèmes de colorspace en ré-encodant avec setparams."""
    base_name = os.path.basename(input_file)
    name, ext = os.path.splitext(base_name)
    output_file = os.path.join(WORKING_DIR, f"{name}_fixed{ext}")
    
    print(f"🔧 Correction des métadonnées de couleur...")
    
    # SOLUTION: Utiliser setparams pour FORCER les métadonnées en entrée
    # Cela contourne l'erreur swscaler en disant à FFmpeg "traite ça comme bt709"
    cmd = [
        'ffmpeg', '-y',
        '-i', input_file,
        '-vf', 'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',
        '-colorspace', 'bt709',
        '-color_primaries', 'bt709',
        '-color_trc', 'bt709',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        output_file
    ]
    
    print(f"   🔧 Forçage colorspace avec setparams filter...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            print(f"❌ Erreur lors de la correction:")
            print(result.stderr[:1000])  # Afficher plus de détails
            return None
        
        input_size = os.path.getsize(input_file) / (1024*1024)
        output_size = os.path.getsize(output_file) / (1024*1024)
        
        print(f"✅ Fichier corrigé!")
        print(f"   Original: {input_size:.1f} MB → Corrigé: {output_size:.1f} MB")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

##############################
# FONCTIONS UTILITAIRES
##############################

def get_video_dimensions(video_path):
    """Récupère les dimensions (largeur, hauteur) et l'aspect ratio d'une vidéo."""
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
        return 1920, 1080, 1.78, False

def get_video_fps(video_path):
    """Détecte le FPS de la vidéo."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        fps_str = result.stdout.strip()
        num, den = map(int, fps_str.split('/'))
        fps = num / den
        
        return fps
    except Exception as e:
        print(f"⚠️  Impossible de détecter FPS: {e}, utilisation 30fps par défaut")
        return 30.0

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
        if file.startswith("temp_accelerated_"):
            continue
        if file.endswith("_fixed.mp4"):  # ✅ Ignorer les fichiers déjà fixés
            continue
        if is_audio_file(file_path) or is_video_file(file_path):
            input_file = file_path
            break
    
    return background_video, input_file

##############################
# PRÉ-ACCÉLÉRATION
##############################

def accelerate_video_properly(input_path, output_path, speed=1.25):
    """Pré-accélère la vidéo avec synchronisation garantie."""
    print(f"\n⚡ PRÉ-ACCÉLÉRATION À {speed}x (SYNC GARANTIE + GPU OPTIMISÉ)")
    print(f"   📂 Input: {os.path.basename(input_path)}")
    
    try:
        original_fps = get_video_fps(input_path)
        new_fps = original_fps * speed
        
        original_duration = get_audio_duration(input_path)
        expected_duration = original_duration / speed
        
        print(f"   🎬 FPS: {original_fps:.2f} → {new_fps:.2f}")
        print(f"   ⏱️  Durée: {original_duration:.2f}s → {expected_duration:.2f}s (attendu)")
        
        video_filter = f"setpts={1/speed}*PTS,fps={new_fps}"
        audio_filter = f"atempo={speed}"
        
        print(f"   🔧 Vidéo: {video_filter}")
        print(f"   🔧 Audio: {audio_filter}")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", video_filter,
            "-af", audio_filter,
        ]
        
        if USE_GPU:
            print(f"   🚀 Encodage GPU ({GPU_ENCODER} preset P4 pour vitesse)")
            cmd.extend([
                "-c:v", GPU_ENCODER,
                "-preset", "p4",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "0",
                "-maxrate", "15M",
                "-bufsize", "30M",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                output_path
            ])
        else:
            print(f"   💻 Encodage CPU")
            cmd.extend([
                "-c:v", "libx264",
                "-crf", "19",
                "-preset", "faster",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "256k",
                output_path
            ])
        
        print(f"   🔄 Génération vidéo accélérée...")
        subprocess.run(cmd, check=True, capture_output=True)
        
        new_duration = get_audio_duration(output_path)
        actual_ratio = original_duration / new_duration
        
        print(f"   ✅ Vidéo accélérée créée!")
        print(f"   ⏱️  Durée réelle: {new_duration:.2f}s")
        print(f"   📊 Ratio: {actual_ratio:.3f}x (attendu: {speed:.3f}x)")
        
        error = abs(actual_ratio - speed) / speed * 100
        if error < 1:
            print(f"   ✅ Précision: {error:.2f}% (excellent!)")
        elif error < 3:
            print(f"   ⚠️  Précision: {error:.2f}% (acceptable)")
        else:
            print(f"   ❌ Précision: {error:.2f}% (vérifier sync)")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Erreur FFmpeg")
        if e.stderr:
            stderr = e.stderr.decode('utf-8', errors='ignore')
            print(f"   Détails: {stderr[:500]}")
        
        if USE_GPU:
            print(f"   🔄 Tentative avec CPU...")
            try:
                cmd_cpu = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-vf", video_filter,
                    "-af", audio_filter,
                    "-c:v", "libx264",
                    "-crf", "19",
                    "-preset", "faster",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "256k",
                    output_path
                ]
                subprocess.run(cmd_cpu, check=True, capture_output=True)
                print(f"   ✅ Accélération CPU réussie")
                return output_path
            except:
                pass
        
        raise
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        raise

##############################
# BACKGROUND ET GÉNÉRATION
##############################

def prepare_background_video(background_video_path, target_duration, output_video_path):
    """Prépare la vidéo de fond en la bouclant avec accélération GPU si disponible."""
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
        ]
        
        if USE_GPU:
            print(f"   🚀 Accélération GPU activée avec qualité maximale")
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

def create_simple_video(background_video_path, original_video_path, output_path):
    """Crée une vidéo simple : background + mini-vidéo redimensionnée."""
    print(f"🎬 Génération vidéo simple (RAPIDE)...")
    
    src_w, src_h, src_ratio, is_portrait = get_video_dimensions(original_video_path)
    
    print(f"   📊 Vidéo source: {src_w}x{src_h} (ratio {src_ratio:.3f})")
    print(f"   📦 Espace disponible: {MIN_VIDEO_WIDTH}-{MAX_VIDEO_WIDTH}px large × {MAX_MINI_VIDEO_HEIGHT}px haut")
    
    # Calcul dimensions
    width_from_max = MAX_VIDEO_WIDTH
    height_from_max_width = int(MAX_VIDEO_WIDTH / src_ratio)
    
    height_from_max = MAX_MINI_VIDEO_HEIGHT
    width_from_max_height = int(MAX_MINI_VIDEO_HEIGHT * src_ratio)
    
    if height_from_max_width <= MAX_MINI_VIDEO_HEIGHT:
        ideal_width = width_from_max
        ideal_height = height_from_max_width
    else:
        ideal_width = width_from_max_height
        ideal_height = height_from_max
    
    if ideal_width < MIN_VIDEO_WIDTH:
        print(f"   ⚠️  Largeur calculée ({ideal_width}px) < minimum ({MIN_VIDEO_WIDTH}px)")
        print(f"   🔧 Application largeur minimale garantie : {MIN_VIDEO_WIDTH}px")
        
        mini_video_width = MIN_VIDEO_WIDTH
        mini_video_height = MAX_MINI_VIDEO_HEIGHT
        
        crop_filter = f"scale={mini_video_width}:-1,crop={mini_video_width}:{mini_video_height}:0:(in_h-{mini_video_height})/2"
        print(f"   ✂️  Scale largeur {MIN_VIDEO_WIDTH}px + crop hauteur {MAX_MINI_VIDEO_HEIGHT}px au centre")
    else:
        mini_video_width = ideal_width
        mini_video_height = ideal_height
        crop_filter = f"scale={mini_video_width}:{mini_video_height}"
    
    print(f"   ✅ Dimensions finales: {mini_video_width}x{mini_video_height}")
    print(f"   📐 Largeur dans plage [{MIN_VIDEO_WIDTH}, {MAX_VIDEO_WIDTH}]px ✅")
    print(f"   🎨 Filter: {crop_filter}")
    
    x_position = f"(main_w-{mini_video_width + BORDER_WIDTH*2})/2"
    
    remaining_space = AVAILABLE_HEIGHT - (mini_video_height + BORDER_WIDTH*2)
    vertical_centering = remaining_space // 2
    y_position = str(LOGO_ZONE_HEIGHT + SPACING_TOP + vertical_centering)
    
    print(f"   📍 Position: x=centré, y={y_position}px")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", background_video_path,
            "-i", original_video_path,
            "-filter_complex",
                f"[1:v]{crop_filter},"
                f"pad={mini_video_width + BORDER_WIDTH*2}:{mini_video_height + BORDER_WIDTH*2}:{BORDER_WIDTH}:{BORDER_WIDTH}:white"
                "[minivid];"
                f"[0:v][minivid]overlay={x_position}:{y_position}[outv]",
            "-map", "[outv]",
            "-map", "1:a",
        ]
        
        if USE_GPU:
            print(f"   🚀 Encodage final avec GPU - Qualité maximale")
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
        print(f"✅ Vidéo simple générée : {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        if USE_GPU:
            print(f"⚠️  Erreur GPU, réessai sans accélération...")
            cmd_fallback = [
                "ffmpeg", "-y",
                "-i", background_video_path,
                "-i", original_video_path,
                "-filter_complex",
                    f"[1:v]{crop_filter},"
                    f"pad={mini_video_width + BORDER_WIDTH*2}:{mini_video_height + BORDER_WIDTH*2}:{BORDER_WIDTH}:{BORDER_WIDTH}:white"
                    "[minivid];"
                    f"[0:v][minivid]overlay={x_position}:{y_position}[outv]",
                "-map", "[outv]",
                "-map", "1:a",
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
            try:
                subprocess.run(cmd_fallback, check=True, capture_output=True)
                print(f"✅ Vidéo simple générée (sans GPU) : {output_path}")
                return output_path
            except:
                pass
        
        print(f"❌ Erreur : {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Détails: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

##############################
# PIPELINE PRINCIPAL
##############################

def main():
    """Pipeline rapide : background + mini-vidéo avec option accélération."""
    global AUDIO_SPEED
    
    parser = argparse.ArgumentParser(description='Générateur Vidéo Simple NEWS DU 237')
    parser.add_argument('--acc', action='store_true',
                       help='Accélérer à 1.25x (sync garantie + GPU optimisé)')
    
    args = parser.parse_args()
    
    if args.acc:
        AUDIO_SPEED = 1.25
    
    print("=" * 60)
    print("🚀 GÉNÉRATEUR VIDÉO SIMPLE (RAPIDE)")
    print("=" * 60)
    print("Mode: Background + Mini-vidéo (pas de wave, pas de SRT)")
    if args.acc:
        print("⚡ ACCÉLÉRATION 1.25x ACTIVÉE")
        print("   ✅ Sync garantie: setpts + fps + atempo")
        print("   🚀 GPU optimisé: preset P4 pour pré-accel")
    print("=" * 60)
    
    # Trouver fichiers
    print("\n📂 Recherche des fichiers...")
    background_video_path, input_file_path = find_input_files()
    
    if not background_video_path or not input_file_path:
        print("❌ Fichiers manquants!")
        print(f"   Veuillez placer dans {WORKING_DIR}:")
        print(f"   - background_video.mp4")
        print(f"   - votre vidéo ou audio")
        return
    
    print(f"✅ Background: {os.path.basename(background_video_path)}")
    print(f"✅ Input: {os.path.basename(input_file_path)}")
    
    # Déterminer type
    is_video = is_video_file(input_file_path)
    is_audio = is_audio_file(input_file_path)
    
    if not is_video and not is_audio:
        print("❌ Type de fichier non reconnu!")
        return
    
    if is_audio:
        print("❌ Ce script nécessite une VIDÉO en entrée!")
        print("   Pour les fichiers audio, utilisez video_generator_wave_hybrid.py")
        return
    
    # ✅ AUTO-CHECK COLORSPACE
    print(f"\n🔍 Vérification des métadonnées...")
    is_ok, message = check_colorspace(input_file_path)
    
    working_video_path = input_file_path
    
    if not is_ok:
        print(f"⚠️  Problème détecté: {message}")
        fixed_file = fix_colorspace(input_file_path)
        
        if not fixed_file:
            print("❌ Impossible de corriger le fichier")
            return
        
        working_video_path = fixed_file
        print(f"📁 Utilisation du fichier corrigé: {os.path.basename(working_video_path)}")
    else:
        print(f"✅ Métadonnées OK: {message}")
    
    # Extraire timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n🎥 Vidéo détectée")
    
    # ÉTAPE 1: Pré-accélération si nécessaire
    if AUDIO_SPEED != 1.0:
        accelerated_path = os.path.join(WORKING_DIR, f"temp_accelerated_{os.path.basename(input_file_path)}")
        try:
            working_video_path = accelerate_video_properly(
                working_video_path,  # ✅ Utilise le fichier fixé si nécessaire
                accelerated_path,
                speed=AUDIO_SPEED
            )
        except Exception as e:
            print(f"\n❌ ÉCHEC PRÉ-ACCÉLÉRATION")
            print(f"Erreur: {e}")
            return
    
    # Sauvegarder durée originale AVANT génération
    original_duration_for_stats = get_audio_duration(input_file_path)
    
    # Durée de travail
    audio_duration = get_audio_duration(working_video_path)
    if audio_duration == 0:
        print("❌ Impossible de déterminer la durée de la vidéo")
        return
    
    print(f"⏱️  Durée: {audio_duration:.2f}s ({audio_duration/60:.2f} min)")
    
    # Préparer background
    looped_video_path = os.path.join(OUTPUT_DIR, f"looped_bg_{timestamp}.mp4")
    looped_video = prepare_background_video(background_video_path, audio_duration, looped_video_path)
    if not looped_video:
        return
    
    # Générer vidéo simple
    input_basename = Path(input_file_path).stem
    final_output_path = os.path.join(OUTPUT_DIR, f"podcast_simple_{input_basename}_{timestamp}.mp4")
    
    print(f"\n🎬 Génération de la vidéo finale...")
    final_video = create_simple_video(
        looped_video, working_video_path, final_output_path
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
    except:
        pass
    
    # Nettoyer vidéo accélérée
    if AUDIO_SPEED != 1.0:
        try:
            accelerated_path = os.path.join(WORKING_DIR, f"temp_accelerated_{os.path.basename(input_file_path)}")
            if os.path.exists(accelerated_path):
                os.remove(accelerated_path)
                print(f"   ✅ Vidéo accélérée temporaire supprimée")
        except:
            pass
    
    # Nettoyer fichier fixé (OPTIONNEL - tu peux le garder)
    # Si tu veux le garder pour debug, commente cette section
    try:
        if working_video_path != input_file_path and "_fixed" in working_video_path:
            if os.path.exists(working_video_path):
                os.remove(working_video_path)
                print(f"   ✅ Fichier corrigé temporaire supprimé")
    except:
        pass
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE!")
    print("=" * 60)
    print(f"📹 Fichier: {final_output_path}")
    print(f"🎬 Mode: Simple (rapide)")
    if AUDIO_SPEED != 1.0:
        gain = original_duration_for_stats - audio_duration
        print(f"⚡ Accélération: {AUDIO_SPEED}x")
        print(f"⏱️  Gain temps: {gain:.1f}s ({gain/original_duration_for_stats*100:.1f}%)")
    print(f"📐 Mini-vidéo centrée en bas avec bordure blanche")
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