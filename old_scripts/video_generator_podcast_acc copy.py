import os
import subprocess
import datetime
from pathlib import Path

# Définir les dossiers de travail
WORKING_DIR = os.path.join(os.getcwd(), "working_dir_podcast")
OUTPUT_DIR = os.path.join(os.getcwd(), "video_generator_podcast_output")

# Facteur d'accélération de l'audio
SPEED_FACTOR = 1.5

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

def accelerate_audio(input_audio_path, output_audio_path, speed_factor=1.5):
    """
    Accélère l'audio en utilisant le filtre atempo de FFmpeg.
    Le facteur de vitesse doit être entre 0.5 et 2.0.
    
    Args:
        input_audio_path: Chemin du fichier audio d'entrée
        output_audio_path: Chemin du fichier audio de sortie
        speed_factor: Facteur d'accélération (ex: 1.5 = 1.5x plus rapide)
    """
    print(f"⚡ Accélération de l'audio par un facteur de {speed_factor}x...")
    
    # Obtenir la durée originale
    original_duration = get_audio_duration(input_audio_path)
    print(f"📊 Durée audio originale : {original_duration:.2f}s ({original_duration/60:.2f} minutes)")
    
    try:
        # Le filtre atempo accepte des valeurs entre 0.5 et 2.0
        # Pour des valeurs en dehors de cette plage, il faudrait chaîner plusieurs filtres
        if 0.5 <= speed_factor <= 2.0:
            audio_filter = f"atempo={speed_factor}"
        else:
            print(f"❌ Le facteur de vitesse {speed_factor} n'est pas supporté (doit être entre 0.5 et 2.0)")
            return None
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_audio_path,
            "-filter:a", audio_filter,
            "-vn",  # Pas de vidéo
            output_audio_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Vérifier la nouvelle durée
        new_duration = get_audio_duration(output_audio_path)
        actual_speed = original_duration / new_duration if new_duration > 0 else 0
        
        print(f"✅ Audio accéléré : {output_audio_path}")
        print(f"📊 Nouvelle durée : {new_duration:.2f}s ({new_duration/60:.2f} minutes)")
        print(f"📊 Facteur de vitesse réel : {actual_speed:.2f}x")
        
        return output_audio_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'accélération audio : {e}")
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

def combine_video_and_audio(video_path, audio_path, output_path):
    """
    Combine la vidéo de fond avec l'audio.
    """
    print(f"🎬 Combinaison de la vidéo et de l'audio...")
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",  # Copier le codec vidéo sans ré-encodage
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",  # S'arrêter quand le flux le plus court se termine
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Vidéo finale générée : {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la combinaison vidéo/audio : {e}")
        return None

##############################
# PIPELINE PRINCIPAL
##############################

def main():
    """
    Pipeline principal pour la génération de vidéos podcast avec audio accéléré.
    """
    print("=" * 60)
    print(f"🎙️⚡ GÉNÉRATEUR DE VIDÉO PODCAST (Accéléré {SPEED_FACTOR}x)")
    print("=" * 60)
    
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
    
    # Étape 4: Accélérer l'audio
    print(f"\n⚡ Étape d'accélération de l'audio...")
    accelerated_audio_path = os.path.join(OUTPUT_DIR, f"accelerated_audio_{timestamp}.mp3")
    accelerated_audio = accelerate_audio(audio_path, accelerated_audio_path, SPEED_FACTOR)
    if not accelerated_audio:
        return
    
    # Étape 5: Obtenir la durée de l'audio accéléré
    audio_duration = get_audio_duration(accelerated_audio)
    if audio_duration == 0:
        print("❌ Impossible de déterminer la durée de l'audio accéléré!")
        return
    
    print(f"\n⏱️  Durée finale de l'audio accéléré : {audio_duration:.2f} secondes ({audio_duration/60:.2f} minutes)")
    
    # Étape 6: Préparer la vidéo de fond bouclée
    looped_video_path = os.path.join(OUTPUT_DIR, f"looped_background_acc_{timestamp}.mp4")
    looped_video = prepare_background_video(background_video_path, audio_duration, looped_video_path)
    if not looped_video:
        return
    
    # Étape 7: Combiner la vidéo et l'audio
    input_basename = Path(input_file_path).stem
    final_output_path = os.path.join(OUTPUT_DIR, f"{input_basename}_Acc.mp4")
    final_video = combine_video_and_audio(looped_video, accelerated_audio, final_output_path)
    
    if not final_video:
        return
    
    # Étape 8: Résumé
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print(f"📹 Vidéo finale : {final_output_path}")
    print(f"⚡ Facteur d'accélération : {SPEED_FACTOR}x")
    print(f"📊 Durée : {audio_duration/60:.2f} minutes")
    print(f"📁 Tous les fichiers se trouvent dans : {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processus interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()

