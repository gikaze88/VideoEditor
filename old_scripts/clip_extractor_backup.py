import os
import subprocess
import json
import glob

def get_video_info(video_file):
    """
    Utilise ffprobe pour obtenir les informations détaillées de la vidéo.
    Retourne un dictionnaire avec la durée, codec, résolution, etc.
    """
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,codec_name,bit_rate:format=duration",
         "-of", "json", video_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    if result.returncode != 0:
        print(f"Erreur lors de l'analyse de la vidéo : {result.stderr}")
        return None
    
    info = json.loads(result.stdout)
    
    # Extraction des informations vidéo
    video_info = {}
    if 'format' in info and 'duration' in info['format']:
        video_info['duration'] = float(info['format']['duration'])
    
    if 'streams' in info and len(info['streams']) > 0:
        stream = info['streams'][0]
        video_info['width'] = stream.get('width', 'Unknown')
        video_info['height'] = stream.get('height', 'Unknown')
        video_info['codec'] = stream.get('codec_name', 'Unknown')
        video_info['bit_rate'] = stream.get('bit_rate', 'Unknown')
    
    return video_info

def get_video_duration(video_file):
    """
    Utilise ffprobe pour obtenir la durée totale de la vidéo en secondes.
    Version améliorée avec gestion d'erreur.
    """
    video_info = get_video_info(video_file)
    if video_info and 'duration' in video_info:
        return video_info['duration']
    else:
        raise ValueError(f"Impossible d'obtenir la durée de la vidéo : {video_file}")

def seconds_to_hhmmss(seconds):
    """
    Convertit un temps en secondes au format HH:MM:SS.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def extract_segment(video_file, start_time, duration, output_file):
    """
    Extrait un segment de la vidéo à partir d'un temps de début donné (en secondes)
    et pour une durée spécifiée, en utilisant ffmpeg.
    Préserve la qualité maximale avec stream copy quand possible.
    """
    # Première tentative : stream copy pour préserver la qualité parfaitement
    cmd = [
        "ffmpeg",
        "-y",  # écrase le fichier de sortie s'il existe déjà
        "-ss", seconds_to_hhmmss(start_time),  # seek avant l'input pour plus de précision
        "-i", video_file,
        "-t", str(duration),
        "-c", "copy",  # copie directe sans réencodage
        "-avoid_negative_ts", "make_zero",  # évite les problèmes de timestamps négatifs
        output_file
    ]
    print("Exécution de la commande :", " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Clip extrait avec succès : {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Erreur avec stream copy, tentative de ré-encodage minimal...")
        # Fallback : ré-encodage minimal avec haute qualité
        cmd_fallback = [
            "ffmpeg",
            "-y",
            "-ss", seconds_to_hhmmss(start_time),
            "-i", video_file,
            "-t", str(duration),
            "-c:v", "libx264",  # codec vidéo
            "-crf", "18",  # qualité très élevée (0-51, plus bas = meilleure qualité)
            "-preset", "slow",  # preset pour qualité optimale
            "-c:a", "aac",  # codec audio
            "-b:a", "192k",  # bitrate audio élevé
            "-avoid_negative_ts", "make_zero",
            output_file
        ]
        print("Commande de fallback :", " ".join(cmd_fallback))
        subprocess.run(cmd_fallback, check=True)
        print(f"Clip extrait avec ré-encodage : {output_file}")

def main():
    # Recherche d'un fichier .mp4 dans le même dossier
    video_files = glob.glob("*.mp4")
    if not video_files:
        print("Aucune vidéo (.mp4) trouvée dans le dossier.")
        return

    video_file = video_files[0]
    print(f"Utilisation de la vidéo : {video_file}")

    # Obtention des informations détaillées de la vidéo
    video_info = get_video_info(video_file)
    if not video_info:
        print("Erreur : Impossible d'analyser la vidéo.")
        return
    
    print("\n=== Informations de la vidéo source ===")
    print(f"Durée : {video_info.get('duration', 'Unknown')} secondes")
    print(f"Résolution : {video_info.get('width', 'Unknown')}x{video_info.get('height', 'Unknown')}")
    print(f"Codec : {video_info.get('codec', 'Unknown')}")
    if video_info.get('bit_rate') != 'Unknown':
        bitrate_mbps = int(video_info['bit_rate']) / 1000000
        print(f"Bitrate : {bitrate_mbps:.2f} Mbps")
    print("=====================================\n")

    # Paramètres par défaut
    num_clips = 20
    clip_duration = 59

    # Obtention de la durée totale de la vidéo
    total_duration = video_info['duration']
    print("Durée totale de la vidéo :", total_duration, "secondes")

    # Vérification de la longueur de la vidéo
    if total_duration < clip_duration:
        print("La vidéo est plus courte que la durée d'un clip.")
        return

    # Calcul de l'intervalle entre chaque clip pour bien couvrir la vidéo
    if num_clips > 1:
        interval = (total_duration - clip_duration) / (num_clips - 1)
    else:
        interval = 0

    # Création du dossier de sortie
    output_dir = "clips"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== Extraction de {num_clips} clips de {clip_duration}s ===")
    print("Mode de préservation de qualité : Stream copy (lossless) avec fallback haute qualité")
    print("===============================================\n")

    # Extraction des clips
    for i in range(num_clips):
        start_time = i * interval
        output_file = os.path.join(output_dir, f"clip_{i+1:02}.mp4")
        print(f"Extraction du clip {i+1}/{num_clips} à partir de {seconds_to_hhmmss(start_time)}")
        extract_segment(video_file, start_time, clip_duration, output_file)

    print("\n=== Extraction terminée ===")
    print(f"Tous les clips ont été sauvegardés dans le dossier '{output_dir}'")
    print("Qualité préservée : Les clips conservent la qualité originale de la vidéo source.")

if __name__ == "__main__":
    main()
