#!/usr/bin/env python3
import os
import time
import whisper
import re
from datetime import datetime
from difflib import SequenceMatcher
import sys

def generate_srt(input_audio_path, output_srt_path=None):
    """
    Fonction principale qui génère le fichier SRT professionnel.
    
    Args:
        input_audio_path: Chemin vers le fichier audio d'entrée
        output_srt_path: Chemin où sauvegarder le fichier SRT (optionnel)
    
    Returns:
        str: Chemin du fichier SRT généré
    """
    # Créer le dossier output s'il n'existe pas
    os.makedirs("output", exist_ok=True)
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_audio_path):
        raise FileNotFoundError(f"Erreur: Le fichier {input_audio_path} n'existe pas.")
    
    print("=" * 60)
    print("GÉNÉRATEUR SRT PROFESSIONNEL")
    print("=" * 60)
    print(f"Début de la transcription avec le modèle Whisper large sur GPU...")
    start_time = time.time()
    
    # Charger le modèle large sur GPU
    try:
        model = whisper.load_model("large", device="cuda")
    except Exception as e:
        print(f"Erreur lors du chargement du modèle sur GPU: {e}")
        print("Tentative de chargement sur CPU...")
        model = whisper.load_model("large", device="cpu")
    
    # Transcription avec paramètres anti-répétition
    result = model.transcribe(
        input_audio_path,
        language="fr",
        verbose=True,
        word_timestamps=True,
        temperature=0.01,  # Température à 0 pour éviter les hallucinations
        no_speech_threshold=0.6,  # Seuil pour détecter le silence
        logprob_threshold=-1.0,  # Probabilité logarithmique pour filtrer
        compression_ratio_threshold=2.4,  # Ratio de compression pour détecter les répétitions
        condition_on_previous_text=False,  # Ne pas se baser sur le texte précédent (clé !)
        initial_prompt=None,  # Pas d'invite initiale
        suppress_tokens=[-1],  # Supprimer certains tokens problématiques
    )
    
    end_time = time.time()
    print(f"Transcription terminée en {end_time - start_time:.2f} secondes.")
    
    print("\n" + "=" * 60)
    print("ÉTAPE 1: DÉDUPLICATION INTELLIGENTE")
    print("=" * 60)
    
    # Déduplication intelligente (fusionner au lieu de supprimer)
    cleaned_segments = advanced_deduplication(result["segments"])
    print(f"Après déduplication intelligente: {len(cleaned_segments)} segments")
    
    print("\n" + "=" * 60)
    print("ÉTAPE 2: OPTIMISATION DES SEGMENTS")
    print("=" * 60)
    
    # Optimiser les segments pour une meilleure lisibilité
    optimized_segments = smart_segmentation(cleaned_segments)
    print(f"Segments optimisés: {len(optimized_segments)} segments")
    
    print("\n" + "=" * 60)
    print("ÉTAPE 3: COMBLEMENT DES TROUS")
    print("=" * 60)
    
    # Combler les trous potentiels
    filled_segments = fill_gaps(optimized_segments)
    print(f"Après comblement des trous: {len(filled_segments)} segments")
    
    # Vérification finale des chevauchements
    final_segments = resolve_overlaps(filled_segments)
    print(f"Après résolution des chevauchements: {len(final_segments)} segments")
    
    # Déterminer le nom du fichier de sortie
    if output_srt_path:
        srt_filename = output_srt_path
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(os.path.dirname(srt_filename), exist_ok=True)
    else:
        # Générer un timestamp pour le nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        srt_filename = f"output/reference_audio_{timestamp}.srt"
    
    # Générer le fichier SRT
    with open(srt_filename, "w", encoding="utf-8") as srt_file:
        write_srt(final_segments, srt_file)
    
    print(f"\n" + "=" * 60)
    print("GÉNÉRATION SRT TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print(f"Fichier SRT professionnel généré: {srt_filename}")
    print(f"Nombre total de segments: {len(final_segments)}")
    
    # Statistiques finales
    total_duration = final_segments[-1]["end"] if final_segments else 0
    print(f"Durée totale traitée: {total_duration:.1f} secondes")
    print("Qualité: Timings précis + Aucun mot perdu + Segmentation intelligente")
    
    return srt_filename

def main():
    """Fonction principale qui génère le fichier SRT professionnel (mode ligne de commande)."""
    # Générer un timestamp pour le nom du fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Fichier audio d'entrée
    input_audio = "reference_audio.mp3"
    
    # Appeler la fonction générique
    generate_srt(input_audio)

def normalize_text(text):
    """Normalise le texte pour la comparaison."""
    # Enlever la ponctuation et les espaces multiples
    text = re.sub(r'[^\w\s]', '', text.lower())
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def advanced_deduplication(segments):
    """Déduplication agressive contre les hallucinations de Whisper."""
    if not segments:
        return []
    
    print("Déduplication anti-hallucination en cours...")
    clean_segments = []
    
    i = 0
    while i < len(segments):
        current = segments[i]
        current_text = current["text"].strip()
        
        # Ignorer les segments très courts ou vides
        if len(current_text) < 3:
            i += 1
            continue
        
        # Chercher des répétitions consécutives (minimum 3 répétitions)
        consecutive_count = 1
        j = i + 1
        
        while j < len(segments):
            next_text = segments[j]["text"].strip()
            similarity = SequenceMatcher(None, 
                                       normalize_text(current_text), 
                                       normalize_text(next_text)).ratio()
            
            if similarity > 0.8:  # Très similaire
                consecutive_count += 1
                j += 1
            else:
                break
        
        # Si on a trouvé 3+ répétitions consécutives, c'est probablement une hallucination
        if consecutive_count >= 3:
            print(f"  Hallucination détectée ({consecutive_count} répétitions): '{current_text[:40]}...'")
            # Garder seulement la première occurrence avec durée étendue
            extended_segment = {
                "start": current["start"],
                "end": segments[j-1]["end"] if j-1 < len(segments) else current["end"],
                "text": current_text,
                "words": current.get("words", [])
            }
            clean_segments.append(extended_segment)
            i = j  # Passer après toutes les répétitions
        else:
            # Segment normal, le garder
            clean_segments.append(current)
            i += 1
    
    return clean_segments

def smart_segmentation(segments):
    """Segmentation séquentielle - Version 27 améliorée avec zéro perte de mots."""
    print("Segmentation séquentielle intelligente en cours...")
    optimized = []
    
    # Paramètres éprouvés de la version 27
    MAX_WORDS_PER_SEGMENT = 5  # 5 mots maximum
    MAX_CHARS_PER_SEGMENT = 35  # 35 caractères maximum  
    MAX_DURATION = 2.8  # 2.8 secondes maximum
    MIN_GAP = 0.1
    
    for segment in segments:
        text = segment["text"].strip()
        start_time = segment["start"]
        end_time = segment["end"]
        duration = end_time - start_time
        
        words = text.split()
        
        # Si le segment respecte déjà les critères, le garder tel quel (logique version 27)
        if (len(words) <= MAX_WORDS_PER_SEGMENT and 
            len(text) <= MAX_CHARS_PER_SEGMENT and 
            duration <= MAX_DURATION):
            optimized.append({
                "start": start_time,
                "end": end_time,
                "text": text
            })
            continue
        
        # Segment dépasse les limites : traitement séquentiel avec timings précis
        print(f"  Traitement séquentiel: '{text[:30]}...' ({len(words)} mots)")
        
        if "words" in segment and segment["words"] and len(segment["words"]) > 0:
            # Utiliser les horodatages précis des mots (version 27 style)
            word_data = segment["words"]
            processed_segments = process_words_sequentially(word_data, MAX_WORDS_PER_SEGMENT, MAX_CHARS_PER_SEGMENT, MIN_GAP)
            optimized.extend(processed_segments)
        else:
            # Fallback : traitement séquentiel sans horodatages précis
            fallback_segments = process_text_sequentially(text, start_time, end_time, MAX_WORDS_PER_SEGMENT, MAX_CHARS_PER_SEGMENT, MIN_GAP)
            optimized.extend(fallback_segments)
    
    return optimized

def process_words_sequentially(word_data, max_words, max_chars, min_gap):
    """Traite les mots séquentiellement avec timings précis - AUCUN mot perdu."""
    if not word_data:
        return []
    
    segments = []
    current_words = []
    
    for i, word_info in enumerate(word_data):
        current_words.append(word_info)
        
        # Construire le texte actuel avec les espaces de Whisper
        current_text = "".join([w["word"] for w in current_words]).strip()
        
        # Vérifier si on doit créer un segment
        should_create_segment = (
            len(current_words) >= max_words or  # Limite de mots atteinte
            len(current_text) >= max_chars or   # Limite de caractères atteinte
            i == len(word_data) - 1 or          # Dernier mot
            word_info["word"].rstrip().endswith(('.', '!', '?', ';', ':'))  # Fin de phrase naturelle
        )
        
        if should_create_segment and current_text:
            # Créer le segment avec timings précis
            segment_start = current_words[0]["start"]
            segment_end = current_words[-1]["end"]
            
            segments.append({
                "start": segment_start,
                "end": segment_end,
                "text": current_text
            })
            
            print(f"    Segment créé: '{current_text}' ({len(current_words)} mots, {len(current_text)} chars)")
            
            # Réinitialiser pour le prochain segment
            current_words = []
    
    return segments

def process_text_sequentially(text, start_time, end_time, max_words, max_chars, min_gap):
    """Traite le texte séquentiellement sans horodatages précis - AUCUN mot perdu."""
    words = text.split()
    if not words:
        return []
    
    segments = []
    duration = end_time - start_time
    total_words = len(words)
    
    word_index = 0
    
    while word_index < total_words:
        current_words = []
        
        # Prendre des mots jusqu'aux limites
        while (word_index < total_words and 
               len(current_words) < max_words and 
               len(" ".join(current_words + [words[word_index]])) <= max_chars):
            current_words.append(words[word_index])
            word_index += 1
        
        # Si aucun mot n'a pu être ajouté (mot très long), le prendre quand même
        if not current_words and word_index < total_words:
            current_words.append(words[word_index])
            word_index += 1
        
        if current_words:
            # Calculer les timings proportionnels
            words_start_ratio = (word_index - len(current_words)) / total_words
            words_end_ratio = word_index / total_words
            
            segment_start = start_time + (duration * words_start_ratio)
            segment_end = start_time + (duration * words_end_ratio)
            
            current_text = " ".join(current_words)
            
            segments.append({
                "start": segment_start,
                "end": segment_end,
                "text": current_text
            })
            
            print(f"    Segment créé: '{current_text}' ({len(current_words)} mots, {len(current_text)} chars)")
    
    return segments

def fill_gaps(segments):
    """Comble les trous entre segments pour éviter les silences dans les sous-titres."""
    if len(segments) < 2:
        return segments
    
    print("Vérification et comblement des trous...")
    filled_segments = []
    
    for i, segment in enumerate(segments):
        filled_segments.append(segment)
        
        # Vérifier s'il y a un trou avec le segment suivant
        if i < len(segments) - 1:
            next_segment = segments[i + 1]
            gap = next_segment["start"] - segment["end"]
            
            # Si le trou est significatif (> 1 seconde) mais pas trop grand (< 5 secondes)
            if 1.0 < gap < 5.0:
                print(f"  Trou détecté de {gap:.1f}s entre segments {i+1} et {i+2}")
                # Étendre légèrement le segment actuel pour réduire le trou
                segment["end"] = min(segment["end"] + gap/2, next_segment["start"] - 0.1)
    
    return filled_segments

def resolve_overlaps(segments):
    """Résout les chevauchements temporels entre segments."""
    print("Résolution des chevauchements temporels...")
    if not segments:
        return []
    
    # Trier les segments par heure de début
    segments.sort(key=lambda x: x["start"])
    
    resolved = []
    for i, current in enumerate(segments):
        if i == 0:
            resolved.append(current)
            continue
        
        previous = resolved[-1]
        
        # Vérifier s'il y a chevauchement
        if current["start"] < previous["end"]:
            # Ajuster les horaires pour éviter le chevauchement
            gap = 0.1  # 100ms de gap minimum
            previous["end"] = current["start"] - gap
            
            # S'assurer que le segment précédent n'est pas trop court
            if previous["end"] - previous["start"] < 0.5:
                previous["end"] = previous["start"] + 0.5
                current["start"] = previous["end"] + gap
            
            print(f"  Chevauchement résolu entre segments {i} et {i+1}")
        
        resolved.append(current)
    
    return resolved

def write_srt(segments, file):
    """Écrire les segments au format SRT - TOUS les mots sont préservés."""
    segment_count = 0
    for segment in segments:
        text = segment["text"].strip()
        
        # Garder tous les segments avec du texte
        if text:
            segment_count += 1
            
            # Numéro de séquence
            file.write(f"{segment_count}\n")
            
            # Temps début --> fin
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            file.write(f"{start} --> {end}\n")
            
            # Texte complet - aucune troncature
            file.write(f"{text}\n\n")

def format_timestamp(seconds):
    """Convertir secondes en format HH:MM:SS,mmm pour SRT."""
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

if __name__ == "__main__":
    main()