import os
import re
import datetime
import subprocess
import ctypes.util
import shutil
import sys
import random
from datetime import timedelta, datetime
from dotenv import load_dotenv
import requests

# --- Monkey-patch for Windows (Whisper) ---
_orig_find_library = ctypes.util.find_library
def patched_find_library(name):
    result = _orig_find_library(name)
    if name == "c" and result is None:
        return "msvcrt"
    return result
ctypes.util.find_library = patched_find_library

# Charger l'environnement et clés API
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

# Définir le dossier de travail pour les fichiers d'entrée
WORKING_DIR = os.path.join(os.getcwd(), "working_dir_shorts")

# Créer le dossier de sortie : exemple "Project_DDMMYYYY_HHMMSS"
OUTPUT_DIR = "Project_" + datetime.now().strftime("%d%m%Y_%H%M%S")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

##############################
# PARTIE 1 – Préparation & génération audio
##############################

def extract_title_and_script(file_path, title_file, script_file):
    """Sépare le titre et le script brut depuis le fichier."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        match = re.search(r"Transcript:\s*(.*)", text, re.DOTALL)
        if match:
            script_text = match.group(1).strip()
            title_text = text[:match.start()].strip()
            with open(title_file, "w", encoding="utf-8") as f_title:
                f_title.write(title_text)
            with open(script_file, "w", encoding="utf-8") as f_script:
                f_script.write(script_text)
            print(f"✅ Titre sauvegardé dans {title_file}")
            print(f"✅ Script extrait sauvegardé dans {script_file}")
        else:
            print("❌ 'Transcript:' introuvable dans le texte.")
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")

def clean_script(input_file, output_file):
    """Nettoie le script en supprimant timestamps et espaces superflus."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            script_text = f.read()
        script_text = re.sub(r'\(\d{1,2}:\d{2}\)', '', script_text)
        script_text = re.sub(r'\s+', ' ', script_text).strip()
        script_text = re.sub(r'([a-zA-Z])\.([A-Z])', r'\1. \2', script_text)
        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write(script_text)
        print(f"✅ Script nettoyé sauvegardé dans {output_file}")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")

def split_text_smart(text, max_length=4900):
    """Découpe intelligemment le texte par phrase afin d'éviter de casser une phrase."""
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind(".", 0, max_length)
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index+1].strip())
        text = text[split_index+1:].strip()
    chunks.append(text.strip())
    return chunks

def normalize_audio(input_file, output_file, target_i=-23):
    """
    Normalise the audio volume using FFmpeg's loudnorm filter.
    `target_i` is the integrated loudness target (e.g., -23 LUFS).
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-af", f"loudnorm=I={target_i}:TP=-2:LRA=11",
        output_file
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Audio normalisé sauvegardé dans {output_file}")

def generate_audio(text_chunks):
    """Génère et normalise des fichiers audio avec ElevenLabs pour chaque chunk."""
    audio_files = []
    for i, chunk in enumerate(text_chunks, 1):
        audio_filename = os.path.join(OUTPUT_DIR, f"audio_part_{i}.mp3")
        normalized_filename = os.path.join(OUTPUT_DIR, f"audio_part_{i}_norm.mp3")
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": chunk,
            "model_id": "eleven_multilingual_v1",
            "voice_settings": {
                "speed": 1.0,
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            with open(audio_filename, "wb") as af:
                af.write(response.content)
            print(f"✅ Audio généré : {audio_filename}")
            # Normalize the generated audio to have consistent volume
            normalize_audio(audio_filename, normalized_filename)
            audio_files.append(normalized_filename)
        else:
            print(f"❌ Erreur audio : {response.json()}")
    return audio_files

def process_audio_generation(input_script):
    """
    Exécute l'extraction, le nettoyage et la génération des audios.
    Renvoie la liste des fichiers audio générés.
    """
    title_file = os.path.join(OUTPUT_DIR, "title.txt")
    extrait_file = os.path.join(OUTPUT_DIR, "script_extrait.txt")
    netoye_file = os.path.join(OUTPUT_DIR, "script_nettoye.txt")
    
    extract_title_and_script(input_script, title_file, extrait_file)
    clean_script(extrait_file, netoye_file)
    
    with open(netoye_file, "r", encoding="utf-8") as f:
        script_text = f.read()
    chunks = split_text_smart(script_text, 4900)
    audio_files = generate_audio(chunks)
    print("✅ Génération audio terminée.")
    return audio_files

##############################
# PARTIE 2 – Génération du SRT avec Whisper
##############################

def get_audio_duration(audio_path):
    """Retourne la durée de l'audio en secondes."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout.decode().strip())

def generate_srt_with_srt_generator(audio_file, output_srt):
    """
    Génère le fichier SRT en utilisant le sous-module srt_generator directement.
    Ce module utilise Whisper avec des optimisations anti-hallucination.
    """
    print("🔄 Génération SRT avec le sous-module srt_generator...")
    
    # Importer le module srt_generator
    sys.path.insert(0, os.path.join(os.getcwd(), "subs_generator"))
    try:
        from srt_generator import generate_srt
        
        # Appeler directement la fonction generate_srt
        generated_srt_path = generate_srt(audio_file, output_srt)
        print(f"✅ Fichier SRT généré avec succès: {generated_srt_path}")
        
        return generated_srt_path
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération SRT: {e}")
        raise
    finally:
        # Nettoyer le path ajouté
        if os.path.join(os.getcwd(), "subs_generator") in sys.path:
            sys.path.remove(os.path.join(os.getcwd(), "subs_generator"))

def select_background_music():
    """
    Utilise le fichier background_song.mp3 du dossier working_dir_shorts.
    """
    background_song_path = os.path.join(WORKING_DIR, "background_song.mp3")
    
    if not os.path.exists(background_song_path):
        raise FileNotFoundError(f"Le fichier background_song.mp3 n'existe pas dans : {WORKING_DIR}")
    
    print(f"🎵 Musique de fond utilisée : background_song.mp3")
    return background_song_path

def prepare_background_video(target_duration, output_video):
    """
    Prépare la vidéo de fond en bouclant le fichier background_video.mp4 
    pour correspondre à la durée de l'audio principal + 4 secondes (2s avant + 2s après).
    """
    background_video_path = os.path.join(WORKING_DIR, "background_video.mp4")
    
    if not os.path.exists(background_video_path):
        raise FileNotFoundError(f"Le fichier background_video.mp4 n'existe pas dans : {WORKING_DIR}")
    
    # Ajouter 4 secondes à la durée cible (2s avant + 2s après)
    extended_duration = target_duration + 4
    print(f"🔄 Préparation vidéo de fond pour une durée de {extended_duration:.1f} secondes (audio: {target_duration:.1f}s + 4s de marge)")
    
    # Obtenir la durée de la vidéo de fond originale
    original_duration = get_audio_duration(background_video_path)
    print(f"📊 Durée vidéo originale : {original_duration:.1f}s")
    
    # Calculer le nombre de boucles nécessaires
    loop_count = int(extended_duration / original_duration) + 1
    print(f"🔁 Nombre de boucles nécessaires : {loop_count}")
    
    # Boucler la vidéo et la couper à la durée exacte
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", str(loop_count),
        "-i", background_video_path,
        "-t", str(extended_duration),
        "-c", "copy",
        output_video
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Vidéo de fond préparée avec succès: {output_video}")
        
        # Vérifier la durée de la vidéo générée
        actual_duration = get_audio_duration(output_video)
        print(f"📊 Durée vidéo finale : {actual_duration:.1f}s (cible : {extended_duration:.1f}s)")
        
        return output_video
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la préparation de la vidéo de fond: {e}")
        raise

##############################
# PARTIE 3 – Génération vidéo avec FFmpeg
##############################

def merge_audio_files(audio_files, output):
    """Fusionne des fichiers audio avec insertion d'une pause entre chaque segment."""
    silence = os.path.join(OUTPUT_DIR, "silence.mp3")
    if not os.path.exists(silence):
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "1", silence
        ]
        subprocess.run(cmd, check=True)
    merge_list = []
    for part in audio_files:
        abs_path = os.path.abspath(part).replace('\\', '/')
        merge_list.append(abs_path)
    list_file = os.path.join(OUTPUT_DIR, "file_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for item in merge_list:
            f.write(f"file '{item}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-ar", "44100",  # force sample rate
        "-c:a", "libmp3lame", "-q:a", "2",
        output
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Audios fusionnés dans {output}")

def boost_audio(input_file, output_file, boost_db=10):
    """
    Booste le volume de l'audio du fichier d'entrée par le nombre de décibels spécifié.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-af", f"volume={boost_db}dB",
        output_file
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Audio boosté de +{boost_db} dB sauvegardé dans {output_file}")

def shift_srt_timing(input_srt, output_srt, delay_seconds=2):
    """
    Décale tous les timecodes du fichier SRT de delay_seconds secondes.
    """
    with open(input_srt, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour matcher les timecodes SRT (HH:MM:SS,mmm --> HH:MM:SS,mmm)
    import re
    timecode_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})'
    
    def shift_timecode(match):
        # Extraire les composants du timecode de début
        start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
        # Extraire les composants du timecode de fin
        end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])
        
        # Convertir en millisecondes totales
        start_total_ms = (start_h * 3600 + start_m * 60 + start_s) * 1000 + start_ms
        end_total_ms = (end_h * 3600 + end_m * 60 + end_s) * 1000 + end_ms
        
        # Ajouter le délai
        delay_ms = delay_seconds * 1000
        start_total_ms += delay_ms
        end_total_ms += delay_ms
        
        # Reconvertir en format HH:MM:SS,mmm
        def ms_to_timecode(total_ms):
            hours = total_ms // (3600 * 1000)
            minutes = (total_ms % (3600 * 1000)) // (60 * 1000)
            seconds = (total_ms % (60 * 1000)) // 1000
            milliseconds = total_ms % 1000
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        
        start_tc = ms_to_timecode(start_total_ms)
        end_tc = ms_to_timecode(end_total_ms)
        
        return f"{start_tc} --> {end_tc}"
    
    # Remplacer tous les timecodes
    shifted_content = re.sub(timecode_pattern, shift_timecode, content)
    
    with open(output_srt, 'w', encoding='utf-8') as f:
        f.write(shifted_content)
    
    print(f"✅ Fichier SRT décalé de +{delay_seconds}s sauvegardé dans {output_srt}")

def smart_word_split(text):
    """
    Divise intelligemment le texte en mots en gardant la ponctuation attachée aux mots appropriés.
    Conserve les espaces originaux entre les signes de ponctuation.
    
    Args:
        text: Le texte à diviser
        
    Returns:
        List[str]: Liste des mots avec ponctuation correctement attachée
    """
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
    Optimise le fichier SRT pour le format vertical (shorts) en divisant les lignes longues.
    Divise les sous-titres en segments plus courts pour une meilleure lisibilité sur mobile.
    """
    import re
    
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
    
    print(f"✅ Fichier SRT optimisé pour shorts sauvegardé dans {output_srt} (max {max_words_per_line} mots par ligne)")

def mix_audio_with_background_delayed(voice_audio, bg_music, output, voice_delay_seconds=2):
    """
    Mixe l'audio principal boosté avec la musique d'ambiance.
    L'audio principal est retardé de voice_delay_seconds secondes.
    La musique d'ambiance démarre immédiatement et couvre toute la durée.
    """
    # Calculer la durée totale nécessaire (durée de l'audio vocal + délai + 2s à la fin)
    voice_duration = get_audio_duration(voice_audio)
    total_duration = voice_duration + (voice_delay_seconds * 2)  # 2s avant + 2s après
    
    cmd = [
        "ffmpeg", "-y",
        "-i", voice_audio,
        "-stream_loop", "-1", "-i", bg_music,
        "-filter_complex", f"[0:a]adelay={voice_delay_seconds * 1000}|{voice_delay_seconds * 1000}[a0];[1:a]volume=0.2[a1];[a0][a1]amix=inputs=2:duration=longest:dropout_transition=3",
        "-t", str(total_duration),
        "-c:a", "aac",
        "-b:a", "192k",
        output
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Audio mixé avec délai de {voice_delay_seconds}s généré : {output} (durée: {total_duration:.1f}s)")

def generate_final_video(video_input, audio_input, subtitle_file, output, format="shorts"):
    """
    Génère la vidéo finale en incrustant des sous-titres décalés.
    La vidéo est ré-encodée en gardant une haute qualité (preset veryslow, CRF 15)
    et le son est mappé correctement.
    
    Args:
        format: "shorts" pour format 9:16, "landscape" pour format 16:9
    """
    # Créer un fichier SRT décalé de 2 secondes
    shifted_srt = subtitle_file.replace('.srt', '_shifted.srt')
    shift_srt_timing(subtitle_file, shifted_srt, delay_seconds=2)
    
    # Si format shorts, optimiser les sous-titres
    if format == "shorts":
        optimized_srt = shifted_srt.replace('.srt', '_optimized.srt')
        optimize_srt_for_shorts(shifted_srt, optimized_srt, max_words_per_line=3)
        final_srt = optimized_srt
    else:
        final_srt = shifted_srt
    
    abs_sub = os.path.abspath(final_srt)
    # Handle Windows path for FFmpeg subtitle filter
    if len(abs_sub) > 1 and abs_sub[1] == ':':
        # For Windows: C:\path -> C\:/path (escape colon, then replace remaining backslashes)
        drive_letter = abs_sub[0]
        path_remainder = abs_sub[2:].replace('\\', '/')  # Convert backslashes to forward slashes
        abs_sub = drive_letter + '\\:' + path_remainder
    else:
        # For non-Windows paths, just convert backslashes
        abs_sub = abs_sub.replace('\\', '/')
    
    # Ajuster le style selon le format
    if format == "shorts":
        # Style optimisé pour mobile (9:16)
        font_size = 12  # Légèrement plus grand pour la lisibilité mobile
        title_font_size = 28
        margin_v = 10  # Marge verticale plus petite
        vf_filter = ("drawtext=text='La Sagesse Du Christ':fontfile='C\\:/Windows/Fonts/montserrat-regular.ttf':fontsize={}:fontcolor=white:x=50:y=50:shadowcolor=black:shadowx=2:shadowy=2,"
                     "subtitles=filename='{}':force_style='FontName=Montserrat ExtraLight,FontSize={},"
                     "OutlineColour=&H000000&,BorderStyle=1,Outline=1,Alignment=10,MarginV={},MarginL=20,MarginR=20'").format(title_font_size, abs_sub, font_size, margin_v)
    else:
        # Style pour format paysage (16:9)
        font_size = 18
        title_font_size = 24
        margin_v = 0
        vf_filter = ("drawtext=text='La Sagesse Du Christ':fontfile='C\\:/Windows/Fonts/montserrat-regular.ttf':fontsize={}:fontcolor=white:x=50:y=50:shadowcolor=black:shadowx=2:shadowy=2,"
                     "subtitles=filename='{}':force_style='FontName=Montserrat ExtraLight,FontSize={},"
                     "OutlineColour=&H000000&,BorderStyle=1,Outline=1,Alignment=10,MarginV={},MarginL=0,MarginR=0'").format(title_font_size, abs_sub, font_size, margin_v)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_input,
        "-i", audio_input,
        "-vf", vf_filter,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "veryslow",
        "-crf", "15",
        "-c:a", "aac",
        "-b:a", "192k",
        output
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Vidéo finale générée en format {format} : {output}")

##############################
# PIPELINE INTÉGRÉ
##############################

def main(format="shorts"):
    """
    Pipeline principal pour la génération de vidéos.
    
    Args:
        format: "shorts" pour format vertical 9:16, "landscape" pour format horizontal 16:9
    """
    print(f"🎬 Démarrage du pipeline en format {format}")
    
    # PARTIE 1 – Génération audio
    input_script = os.path.join(WORKING_DIR, "script_video.txt")
    audio_parts = process_audio_generation(input_script)
    if not audio_parts:
        print("❌ Aucun fichier audio généré.")
        return
    
    # Merge audio parts
    merged_audio = os.path.join(OUTPUT_DIR, "full_audio.mp3")
    merge_audio_files(audio_parts, merged_audio)
    
    # Boost audio volume
    boosted_audio = os.path.join(OUTPUT_DIR, "full_audio_boosted.mp3")
    boost_audio(merged_audio, boosted_audio, boost_db=10)
    
    # PARTIE 2 – Génération du SRT avec le sous-module srt_generator
    final_srt = os.path.join(OUTPUT_DIR, "final_subtitles.srt")
    generate_srt_with_srt_generator(boosted_audio, final_srt)
    
    # PARTIE 3 – Génération vidéo avec FFmpeg
    audio_duration = get_audio_duration(boosted_audio)
    background_video = os.path.join(OUTPUT_DIR, "background_video.mp4")
    prepare_background_video(audio_duration, background_video)
    
    background_music = select_background_music()
    mixed_audio = os.path.join(OUTPUT_DIR, "mixed_audio.m4a")
    mix_audio_with_background_delayed(boosted_audio, background_music, mixed_audio, voice_delay_seconds=2)
    
    final_video = os.path.join(OUTPUT_DIR, "final_video.mp4")
    generate_final_video(background_video, mixed_audio, final_srt, final_video, format=format)
    
    print("✅ Pipeline complet terminé.")
    print("Vidéo finale :", final_video)
    print("Tous les fichiers générés se trouvent dans le dossier :", OUTPUT_DIR)
    
    # Afficher un résumé du format utilisé
    if format == "shorts":
        print("📱 Format optimisé pour les réseaux sociaux (9:16) avec sous-titres courts (max 3 mots par ligne)")
    else:
        print("🖥️ Format paysage (16:9) avec sous-titres standards")

if __name__ == "__main__":
    # Possibilité de passer le format en argument de ligne de commande
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ["shorts", "landscape"]:
        selected_format = sys.argv[1]
        print(f"🎯 Format spécifié via argument : {selected_format}")
    else:
        selected_format = "shorts"  # Format par défaut pour ce script
        print(f"🎯 Format par défaut : {selected_format}")
    
    main(format=selected_format)
