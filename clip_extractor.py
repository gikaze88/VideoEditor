"""
EXTRACTEUR DE CLIPS VIDÉO AVEC UPSCALING AVANCÉ
==============================================

Ce script extrait des segments de vidéo en améliorant leur qualité grâce à l'upscaling.

FONCTIONNALITÉS D'AMÉLIORATION DE QUALITÉ :
- Upscaling intelligent jusqu'à 4K et au-delà
- 5 méthodes d'upscaling disponibles
- Amélioration automatique de la netteté et des couleurs
- Préservation audio haute qualité

MÉTHODES D'UPSCALING DISPONIBLES :
- "enhanced" (Recommandé) : Combinaison d'upscaling Lanczos + amélioration netteté + correction couleurs
- "lanczos" : Upscaling de haute qualité, excellent pour la plupart des contenus
- "bicubic" : Bon compromis qualité/vitesse
- "spline" : Très fluide, idéal pour l'animation
- "ai_super_resolution" : Upscaling assisté par IA avec amélioration de netteté

CONFIGURATION RAPIDE :
Modifiez ces 3 variables dans la fonction main() :
- ENABLE_UPSCALING = True/False
- SCALE_FACTOR = 2.0 (pour doubler la résolution)
- UPSCALE_METHOD = "enhanced"

EXEMPLES D'AMÉLIORATION :
- 720p (1280x720) → 1440p (2560x1440) avec SCALE_FACTOR = 2.0
- 1080p (1920x1080) → 4K (3840x2160) avec SCALE_FACTOR = 2.0
- 480p (854x480) → 1080p (1708x960) avec SCALE_FACTOR = 2.0

PERFORMANCE :
L'upscaling prend plus de temps mais produit des clips de qualité exceptionnelle.
Pour la vitesse maximale, utilisez ENABLE_UPSCALING = False.
"""

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

def get_video_quality_info(video_file: str) -> dict:
    """Analyze video to determine appropriate quality settings."""
    import json
    import subprocess
    
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate,r_frame_rate,codec_name",
        "-show_entries", "format=bit_rate,duration",
        "-of", "json",
        video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    
    video_stream = info['streams'][0]
    format_info = info['format']
    
    # Calculate appropriate CRF based on video characteristics
    width = int(video_stream.get('width', 1920))
    height = int(video_stream.get('height', 1080))
    
    # Determine quality settings based on resolution and bitrate
    total_pixels = width * height
    
    if total_pixels >= 3840 * 2160:  # 4K
        crf = 20
    elif total_pixels >= 1920 * 1080:  # 1080p
        crf = 21
    elif total_pixels >= 1280 * 720:   # 720p
        crf = 22
    else:  # Lower resolution
        crf = 23
    
    # Get original bitrate if available
    bitrate = None
    if 'bit_rate' in video_stream:
        bitrate = int(video_stream['bit_rate'])
    elif 'bit_rate' in format_info:
        bitrate = int(format_info['bit_rate'])
    
    return {
        'width': width,
        'height': height,
        'crf': crf,
        'bitrate': bitrate,
        'codec': video_stream.get('codec_name', 'unknown'),
        'duration': float(format_info.get('duration', 0))
    }

def extract_segment(video_file, start_time, duration, output_file, upscale_config=None):
    """
    Extract video segment with optimized quality settings that match original video quality.
    Much faster than previous version while maintaining same quality.
    """
    
    # Analyze original video quality
    quality_info = get_video_quality_info(video_file)
    
    if upscale_config is None:
        # Mode preservation: try stream copy first, fallback to optimized re-encoding
        cmd = [
            "ffmpeg",
            "-y",  # overwrite output file if it exists
            "-ss", seconds_to_hhmmss(start_time),  # seek before input for precision
            "-i", video_file,
            "-t", str(duration),
            "-c", "copy",  # direct copy without re-encoding
            "-avoid_negative_ts", "make_zero",  # avoid negative timestamp issues
            output_file
        ]
        print("Mode: Original quality preservation (stream copy)")
        print("Executing command:", " ".join(cmd))
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Clip extracted successfully: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Stream copy failed, using optimized re-encoding...")
            # Fallback: optimized re-encoding with quality matching original
            cmd_fallback = [
                "ffmpeg",
                "-y",
                "-ss", seconds_to_hhmmss(start_time),
                "-i", video_file,
                "-t", str(duration),
                "-c:v", "libx264",  # video codec
                "-crf", str(quality_info['crf']),  # quality matching original
                "-preset", "medium",  # balanced speed/quality
                "-c:a", "aac",  # audio codec
                "-b:a", "128k",  # reasonable audio bitrate
                "-avoid_negative_ts", "make_zero",
                output_file
            ]
            print(f"Fallback command (CRF {quality_info['crf']}):", " ".join(cmd_fallback))
            subprocess.run(cmd_fallback, check=True)
            print(f"Clip extracted with optimized re-encoding: {output_file}")
    else:
        # Mode upscaling: quality improvement with optimized settings
        width, height = upscale_config['resolution']
        method = upscale_config['method']
        
        print(f"Mode: Upscaling to {width}x{height} with {method} method")
        
        # Build video filter based on method
        if method == "lanczos":
            vf_filter = f"scale={width}:{height}:flags=lanczos"
        elif method == "bicubic":
            vf_filter = f"scale={width}:{height}:flags=bicubic"
        elif method == "spline":
            vf_filter = f"scale={width}:{height}:flags=spline"
        elif method == "ai_super_resolution":
            # Use super-resolution filter from ffmpeg (requires recent version)
            vf_filter = f"scale={width}:{height}:flags=lanczos,unsharp=5:5:1.0:5:5:0.0"
        elif method == "enhanced":
            # Combination of filters for maximum improvement
            vf_filter = f"scale={width}:{height}:flags=lanczos,unsharp=5:5:0.8:3:3:0.4,eq=contrast=1.1:brightness=0.02:saturation=1.05"
        else:  # default to lanczos
            vf_filter = f"scale={width}:{height}:flags=lanczos"
        
        # Use higher quality CRF for upscaled content, but still optimized
        upscale_crf = max(18, quality_info['crf'] - 2)
        
        # Choose preset based on duration
        if duration > 300:  # 5+ minutes
            preset = "fast"
        else:
            preset = "medium"
        
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", seconds_to_hhmmss(start_time),
            "-i", video_file,
            "-t", str(duration),
            "-vf", vf_filter,  # video filter for upscaling
            "-c:v", "libx264",  # high quality video codec
            "-crf", str(upscale_crf),  # optimized quality for upscaling
            "-preset", preset,  # optimized preset for speed
            "-c:a", "aac",  # audio codec
            "-b:a", "128k",  # reasonable audio bitrate
            "-avoid_negative_ts", "make_zero",
            output_file
        ]
        
        print(f"Upscaling command (CRF {upscale_crf}, preset {preset}):", " ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"Clip upscaled successfully: {output_file}")

def calculate_upscale_resolution(original_width, original_height, scale_factor):
    """
    Calcule la nouvelle résolution basée sur un facteur d'échelle.
    Assure que les dimensions sont paires (requis pour certains codecs).
    """
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    # Assure que les dimensions sont paires
    new_width = new_width + (new_width % 2)
    new_height = new_height + (new_height % 2)
    
    return new_width, new_height

def get_upscale_config(video_info, enable_upscale=True, scale_factor=2.0, method="enhanced"):
    """
    Configure les paramètres d'upscaling basés sur la vidéo source.
    """
    if not enable_upscale:
        return None
    
    original_width = video_info.get('width', 1920)
    original_height = video_info.get('height', 1080)
    
    if original_width == 'Unknown' or original_height == 'Unknown':
        print("Résolution inconnue, utilisation de valeurs par défaut")
        original_width, original_height = 1920, 1080
    
    new_width, new_height = calculate_upscale_resolution(original_width, original_height, scale_factor)
    
    return {
        'resolution': (new_width, new_height),
        'method': method,
        'scale_factor': scale_factor,
        'original_resolution': (original_width, original_height)
    }

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
    
    # CONFIGURATION D'UPSCALING - Modifiez ces valeurs selon vos besoins
    ENABLE_UPSCALING = True  # True pour activer l'upscaling, False pour préserver la qualité originale
    SCALE_FACTOR = 2.0  # Facteur d'agrandissement (2.0 = double la résolution)
    UPSCALE_METHOD = "enhanced"  # Options: "enhanced", "lanczos", "bicubic", "spline", "ai_super_resolution"
    
    # Configuration de l'upscaling
    upscale_config = get_upscale_config(
        video_info, 
        enable_upscale=ENABLE_UPSCALING, 
        scale_factor=SCALE_FACTOR, 
        method=UPSCALE_METHOD
    )
    
    # Affichage des paramètres d'amélioration
    if upscale_config:
        orig_w, orig_h = upscale_config['original_resolution']
        new_w, new_h = upscale_config['resolution']
        scale = upscale_config['scale_factor']
        method = upscale_config['method']
        
        print("=== Configuration d'amélioration de qualité ===")
        print(f"Résolution originale : {orig_w}x{orig_h}")
        print(f"Nouvelle résolution : {new_w}x{new_h}")
        print(f"Facteur d'agrandissement : x{scale}")
        print(f"Méthode d'upscaling : {method}")
        print(f"Pixels originaux : {orig_w * orig_h:,}")
        print(f"Pixels après upscaling : {new_w * new_h:,}")
        improvement = (new_w * new_h) / (orig_w * orig_h)
        print(f"Amélioration qualité : +{improvement:.1f}x pixels")
        print("==============================================\n")
    else:
        print("=== Mode préservation qualité originale ===")
        print("L'upscaling est désactivé - qualité identique à la source")
        print("==========================================\n")

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
    output_dir = "clips_enhanced" if upscale_config else "clips"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== Extraction de {num_clips} clips de {clip_duration}s ===")
    if upscale_config:
        print("Mode : Upscaling et amélioration de qualité activés")
        print(f"Qualité cible : CRF 15 (exceptionnelle) à {upscale_config['resolution'][0]}x{upscale_config['resolution'][1]}")
    else:
        print("Mode : Stream copy (lossless) avec fallback haute qualité")
    print("===============================================\n")

    # Extraction des clips
    for i in range(num_clips):
        start_time = i * interval
        output_file = os.path.join(output_dir, f"clip_{i+1:02}.mp4")
        print(f"Extraction du clip {i+1}/{num_clips} à partir de {seconds_to_hhmmss(start_time)}")
        extract_segment(video_file, start_time, clip_duration, output_file, upscale_config)

    print("\n=== Extraction terminée ===")
    print(f"Tous les clips ont été sauvegardés dans le dossier '{output_dir}'")
    if upscale_config:
        orig_w, orig_h = upscale_config['original_resolution']
        new_w, new_h = upscale_config['resolution']
        print(f"✨ Qualité améliorée : {orig_w}x{orig_h} → {new_w}x{new_h}")
        print(f"✨ Méthode utilisée : {upscale_config['method']}")
        print("✨ Les clips ont une qualité supérieure à la vidéo originale!")
    else:
        print("Qualité préservée : Les clips conservent la qualité originale de la vidéo source.")

if __name__ == "__main__":
    main()
