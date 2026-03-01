#!/usr/bin/env python3
"""
Extracteur Multi-Critères Intelligent
====================================
Combine analyse temporelle, textuelle et structurelle pour détecter
les vraies transitions entre locuteurs avec validation croisée.
"""

import os
import glob
import subprocess
import time
import json
import whisper
import cv2
import numpy as np
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter

class MultiCriteriaSpeechExtractor:
    def __init__(self, working_dir="working_dir_extractor", output_dir="multicriteria_extracts"):
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.video_file = None
        self.audio_file = "temp_audio/extracted_audio.wav"
        
        # Modèle Whisper
        self.whisper_model = None
        
        # Données d'analyse
        self.transcription_segments = []
        self.points_transition_candidats = []
        self.interventions_validees = []
        
        # Créer les dossiers
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)
        
        # ===== PATTERNS DE TRANSITION ENTRE LOCUTEURS =====
        self.patterns_debut_intervention = [
            # Interpellations directes
            r"^(alors |bon |donc |écoutez |regardez |monsieur |madame |moi je)",
            r"^(non mais |oui mais |justement |exactement |absolument)",
            r"^(permettez|pardonnez|excusez)",
            
            # Questions directes
            r"^(est-ce que|qu'est-ce que|comment|pourquoi|quand|où)",
            r"(n'est-ce pas|vous ne pensez pas|vous ne croyez pas)",
            
            # Changements de sujet
            r"^(maintenant|passons|abordons|parlons|concernant|à propos)",
            r"^(sur ce point|sur cette question|dans ce contexte)",
            
            # Réactions/oppositions
            r"^(je ne suis pas d'accord|je pense le contraire|c'est faux)",
            r"^(vous avez tort|vous vous trompez|ce n'est pas vrai)"
        ]
        
        self.patterns_fin_intervention = [
            # Conclusions
            r"(donc voilà|en conclusion|pour conclure|finalement|au final)",
            r"(c'est tout|point final|j'ai terminé|je m'arrête là)",
            
            # Transferts de parole
            r"(qu'est-ce que vous en pensez|votre avis|qu'en dites-vous)",
            r"(je vous laisse|je vous passe|à vous)",
            
            # Questions ouvertes
            r"(n'est-ce pas|vous voyez|vous comprenez|non)",
            r"(\?$)"  # Phrases se terminant par une question
        ]
        
        # ===== INDICATEURS DE QUALITÉ =====
        self.duree_min_realiste = 8      # En dessous = probablement fragmenté
        self.duree_max_realiste = 600    # Au-dessus = probablement fusionné (10 min)
        
    def initialiser_whisper(self):
        """Initialise Whisper."""
        
        print("🤖 Chargement de Whisper...")
        
        try:
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper prêt")
            return True
        except Exception as e:
            print(f"❌ Erreur Whisper : {e}")
            return False
    
    def get_video_file(self):
        """Récupère le fichier vidéo."""
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(glob.glob(os.path.join(self.working_dir, ext)))
        
        if video_files:
            self.video_file = sorted(video_files)[0]
            return self.video_file
        return None
    
    def extraire_audio(self):
        """Extrait l'audio."""
        
        if not self.video_file:
            return False
        
        cmd = [
            "ffmpeg", "-y",
            "-i", self.video_file,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            self.audio_file
        ]
        
        print("🔊 Extraction audio...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Audio extrait")
            return True
        else:
            print(f"❌ Erreur extraction audio: {result.stderr}")
            return False
    
    def transcrire_avec_analyse(self):
        """Transcription avec analyse multi-critères."""
        
        if not self.whisper_model:
            return False
        
        if not os.path.exists(self.audio_file):
            if not self.extraire_audio():
                return False
        
        print("📝 Transcription avec analyse multi-critères...")
        
        # Transcription
        result = self.whisper_model.transcribe(
            self.audio_file,
            word_timestamps=False,
            language="fr",
            task="transcribe"
        )
        
        # Traitement avec filtrage minimal
        segments_valides = []
        
        for segment in result["segments"]:
            texte = segment["text"].strip()
            
            # Filtrage ultra-minimal
            if len(texte) < 3 or self._est_bruit_audio(texte):
                continue
            
            segments_valides.append({
                "debut": segment["start"],
                "fin": segment["end"],
                "duree": segment["end"] - segment["start"],
                "texte": texte
            })
        
        self.transcription_segments = segments_valides
        
        print(f"✅ {len(segments_valides)} segments analysés")
        
        # Analyse multi-critères
        self._analyser_points_transition()
        
        return True
    
    def _est_bruit_audio(self, texte):
        """Détecte le vrai bruit audio vs vraie parole."""
        
        texte_lower = texte.lower()
        
        # Seulement les vrais bruits/artefacts
        bruits = ["[musique]", "[applaudissements]", "[rires]", "♪", "♫"]
        
        for bruit in bruits:
            if bruit in texte_lower:
                return True
        
        # Texte trop répétitif (générique)
        mots = texte_lower.split()
        if len(mots) >= 2 and len(set(mots)) == 1:
            return True
        
        return False
    
    def _analyser_points_transition(self):
        """Analyse multi-critères pour identifier les points de transition."""
        
        print("🔍 Analyse multi-critères des transitions...")
        
        candidats_transition = []
        
        for i in range(1, len(self.transcription_segments)):
            segment_precedent = self.transcription_segments[i-1]
            segment_actuel = self.transcription_segments[i]
            
            # Calculer le score de probabilité de transition
            score_transition = self._calculer_score_transition(
                segment_precedent, segment_actuel, i
            )
            
            if score_transition > 0:
                candidats_transition.append({
                    "position": i,
                    "timestamp": segment_actuel["debut"],
                    "score": score_transition,
                    "raisons": self._get_raisons_transition(segment_precedent, segment_actuel, i),
                    "segment_precedent": segment_precedent,
                    "segment_actuel": segment_actuel
                })
        
        # Tri par score de confiance
        candidats_transition.sort(key=lambda x: x["score"], reverse=True)
        
        self.points_transition_candidats = candidats_transition
        
        print(f"✅ {len(candidats_transition)} points de transition candidats identifiés")
        
        return candidats_transition
    
    def _calculer_score_transition(self, segment_prec, segment_act, position):
        """Calcule un score de probabilité qu'il y ait un changement de locuteur."""
        
        score = 0
        pause = segment_act["debut"] - segment_prec["fin"]
        texte_prec = segment_prec["texte"].lower()
        texte_act = segment_act["texte"].lower()
        
        # 1. Analyse temporelle (pause)
        if pause > 2:
            score += min(pause * 0.5, 3)  # Max 3 points pour les pauses
        
        # 2. Analyse textuelle - début d'intervention
        for pattern in self.patterns_debut_intervention:
            if re.search(pattern, texte_act):
                score += 2
                break
        
        # 3. Analyse textuelle - fin d'intervention précédente
        for pattern in self.patterns_fin_intervention:
            if re.search(pattern, texte_prec):
                score += 1.5
                break
        
        # 4. Changement de style/rythme
        if len(self.transcription_segments) > position + 2:
            # Analyser le contexte autour
            segments_avant = self.transcription_segments[max(0, position-3):position]
            segments_apres = self.transcription_segments[position:position+3]
            
            if segments_avant and segments_apres:
                duree_moy_avant = sum(s["duree"] for s in segments_avant) / len(segments_avant)
                duree_moy_apres = sum(s["duree"] for s in segments_apres) / len(segments_apres)
                
                ratio_changement = duree_moy_apres / max(duree_moy_avant, 0.5)
                if ratio_changement > 2 or ratio_changement < 0.5:
                    score += 1
        
        # 5. Détection de questions/réponses
        if "?" in texte_prec and not "?" in texte_act:
            score += 1.5  # Question suivie d'affirmation = probable changement
        
        # 6. Changement de personne grammaticale
        if self._detecter_changement_personne(texte_prec, texte_act):
            score += 1
        
        # 7. Longueur du segment précédent (intervention potentiellement complète)
        if segment_prec["duree"] > 10:  # Segment assez long pour être une intervention
            score += 0.5
        
        return score
    
    def _detecter_changement_personne(self, texte_prec, texte_act):
        """Détecte un changement de personne grammaticale."""
        
        # Indicateurs de première personne
        premiere_personne = ["je ", "j'", "mon ", "ma ", "mes ", "moi "]
        # Indicateurs de deuxième personne  
        deuxieme_personne = ["vous ", "votre ", "vos "]
        
        prec_1ere = any(p in texte_prec for p in premiere_personne)
        prec_2eme = any(p in texte_prec for p in deuxieme_personne)
        
        act_1ere = any(p in texte_act for p in premiere_personne)
        act_2eme = any(p in texte_act for p in deuxieme_personne)
        
        # Changement significatif de personne
        if (prec_1ere and act_2eme) or (prec_2eme and act_1ere):
            return True
        
        return False
    
    def _get_raisons_transition(self, segment_prec, segment_act, position):
        """Retourne les raisons détectées pour cette transition."""
        
        raisons = []
        pause = segment_act["debut"] - segment_prec["fin"]
        texte_prec = segment_prec["texte"].lower()
        texte_act = segment_act["texte"].lower()
        
        if pause > 2:
            raisons.append(f"Pause {pause:.1f}s")
        
        for pattern in self.patterns_debut_intervention:
            if re.search(pattern, texte_act):
                raisons.append("Début d'intervention détecté")
                break
        
        for pattern in self.patterns_fin_intervention:
            if re.search(pattern, texte_prec):
                raisons.append("Fin d'intervention détectée")
                break
        
        if "?" in texte_prec:
            raisons.append("Question précédente")
        
        if self._detecter_changement_personne(texte_prec, texte_act):
            raisons.append("Changement de personne")
        
        return raisons
    
    def segmenter_interventions_intelligentes(self):
        """Segmente en utilisant les points de transition validés."""
        
        print("🧠 Segmentation intelligente des interventions...")
        
        # Sélectionner les meilleurs points de transition
        transitions_retenues = self._selectionner_transitions_optimales()
        
        print(f"   📍 {len(transitions_retenues)} transitions retenues")
        
        # Créer les interventions basées sur ces transitions
        interventions = []
        debut_intervention = 0  # Index du premier segment
        speaker_id = 1
        
        for transition in transitions_retenues:
            # Créer l'intervention depuis le début jusqu'à cette transition
            fin_intervention = transition["position"] - 1
            
            if fin_intervention >= debut_intervention:
                intervention = self._creer_intervention(
                    debut_intervention, fin_intervention, speaker_id
                )
                
                if intervention:
                    interventions.append(intervention)
                    print(f"   ✅ Intervention {len(interventions)} : {intervention['duree_totale']:.1f}s")
            
            debut_intervention = transition["position"]
            speaker_id += 1
        
        # Ajouter la dernière intervention
        if debut_intervention < len(self.transcription_segments):
            intervention = self._creer_intervention(
                debut_intervention, len(self.transcription_segments) - 1, speaker_id
            )
            if intervention:
                interventions.append(intervention)
                print(f"   ✅ Intervention finale : {intervention['duree_totale']:.1f}s")
        
        # Post-traitement : fusion/division si nécessaire
        interventions_optimisees = self._post_traiter_interventions(interventions)
        
        self.interventions_validees = interventions_optimisees
        
        print(f"✅ {len(interventions_optimisees)} interventions intelligentes créées")
        
        return interventions_optimisees
    
    def _selectionner_transitions_optimales(self):
        """Sélectionne les transitions les plus probables en évitant la sur-segmentation."""
        
        if not self.points_transition_candidats:
            return []
        
        # Filtrer par score minimum
        candidats_qualite = [t for t in self.points_transition_candidats if t["score"] >= 2.5]
        
        # Éviter les transitions trop rapprochées (sur-segmentation)
        transitions_espacees = []
        derniere_position = -1
        
        for candidat in candidats_qualite:
            # Au moins 10 segments d'écart (environ 30-60s selon le débit)
            if candidat["position"] - derniere_position > 10:
                transitions_espacees.append(candidat)
                derniere_position = candidat["position"]
                print(f"   📍 Transition retenue à {candidat['timestamp']:.1f}s (score: {candidat['score']:.1f}) - {candidat['raisons']}")
        
        return transitions_espacees
    
    def _creer_intervention(self, debut_idx, fin_idx, speaker_id):
        """Crée une intervention à partir des indices de segments."""
        
        if debut_idx > fin_idx or debut_idx < 0 or fin_idx >= len(self.transcription_segments):
            return None
        
        segments = self.transcription_segments[debut_idx:fin_idx + 1]
        
        if not segments:
            return None
        
        texte_complet = " ".join(seg["texte"] for seg in segments)
        debut = segments[0]["debut"]
        fin = segments[-1]["fin"]
        duree_totale = fin - debut
        
        intervention = {
            "speaker_id": speaker_id,
            "speaker": f"SPEAKER_{speaker_id}",
            "debut": debut,
            "fin": fin,
            "duree_totale": duree_totale,
            "segments": segments,
            "texte_complet": texte_complet,
            "nb_mots": len(texte_complet.split()),
            "nb_segments": len(segments),
            "duree_formattee": str(timedelta(seconds=int(duree_totale)))
        }
        
        return intervention
    
    def _post_traiter_interventions(self, interventions):
        """Post-traitement pour optimiser les interventions."""
        
        print("🔧 Post-traitement des interventions...")
        
        interventions_optimisees = []
        
        for intervention in interventions:
            duree = intervention["duree_totale"]
            
            # Cas 1: Intervention trop courte -> fusionner avec la suivante si possible
            if duree < self.duree_min_realiste:
                print(f"   ⚠️  Intervention trop courte détectée : {duree:.1f}s")
                # Pour l'instant, on la garde mais on la marque
                intervention["attention"] = "Potentiellement fragmentée"
            
            # Cas 2: Intervention trop longue -> potentiellement diviser
            elif duree > self.duree_max_realiste:
                print(f"   ⚠️  Intervention très longue détectée : {duree:.1f}s")
                # Chercher des points de division internes
                sous_interventions = self._diviser_intervention_longue(intervention)
                interventions_optimisees.extend(sous_interventions)
                continue
            
            interventions_optimisees.append(intervention)
        
        # Fusion des interventions très courtes adjacentes
        interventions_finales = self._fusionner_interventions_courtes(interventions_optimisees)
        
        return interventions_finales
    
    def _diviser_intervention_longue(self, intervention):
        """Divise une intervention très longue en cherchant des points de division naturels."""
        
        segments = intervention["segments"]
        
        # Chercher des pauses internes longues
        points_division = []
        
        for i in range(1, len(segments)):
            pause_interne = segments[i]["debut"] - segments[i-1]["fin"]
            
            # Pause significative à l'intérieur
            if pause_interne > 4:
                # Vérifier que ce n'est pas trop près du début/fin
                temps_depuis_debut = segments[i]["debut"] - segments[0]["debut"]
                temps_jusqu_fin = segments[-1]["fin"] - segments[i]["debut"]
                
                if temps_depuis_debut > 60 and temps_jusqu_fin > 60:  # Au moins 1 min de chaque côté
                    points_division.append(i)
        
        if not points_division:
            # Pas de point de division naturel, garder tel quel
            print(f"     ℹ️  Aucun point de division trouvé")
            return [intervention]
        
        # Créer les sous-interventions
        sous_interventions = []
        debut_idx = 0
        speaker_base = intervention["speaker_id"]
        
        for i, point_div in enumerate(points_division):
            sous_intervention = self._creer_intervention(debut_idx, point_div - 1, f"{speaker_base}.{i+1}")
            if sous_intervention:
                sous_interventions.append(sous_intervention)
                print(f"     ✂️  Sous-intervention créée : {sous_intervention['duree_totale']:.1f}s")
            debut_idx = point_div
        
        # Dernière sous-intervention
        derniere = self._creer_intervention(debut_idx, len(segments) - 1, f"{speaker_base}.{len(points_division)+1}")
        if derniere:
            sous_interventions.append(derniere)
            print(f"     ✂️  Dernière sous-intervention : {derniere['duree_totale']:.1f}s")
        
        return sous_interventions
    
    def _fusionner_interventions_courtes(self, interventions):
        """Fusionne les interventions très courtes avec leurs voisines."""
        
        if len(interventions) <= 1:
            return interventions
        
        interventions_fusionnees = []
        i = 0
        
        while i < len(interventions):
            intervention_courante = interventions[i]
            
            # Si l'intervention courante est très courte
            if intervention_courante["duree_totale"] < self.duree_min_realiste:
                
                # Essayer de fusionner avec la suivante
                if i + 1 < len(interventions):
                    intervention_suivante = interventions[i + 1]
                    
                    # Fusionner si la suivante n'est pas trop longue
                    if intervention_suivante["duree_totale"] < 300:  # Moins de 5 min
                        intervention_fusionnee = self._fusionner_deux_interventions(
                            intervention_courante, intervention_suivante
                        )
                        interventions_fusionnees.append(intervention_fusionnee)
                        print(f"   🔗 Fusion : {intervention_courante['duree_totale']:.1f}s + {intervention_suivante['duree_totale']:.1f}s = {intervention_fusionnee['duree_totale']:.1f}s")
                        i += 2  # Passer les deux interventions fusionnées
                        continue
                
                # Sinon fusionner avec la précédente si possible
                elif interventions_fusionnees and interventions_fusionnees[-1]["duree_totale"] < 300:
                    derniere = interventions_fusionnees.pop()
                    intervention_fusionnee = self._fusionner_deux_interventions(
                        derniere, intervention_courante
                    )
                    interventions_fusionnees.append(intervention_fusionnee)
                    print(f"   🔗 Fusion arrière : {derniere['duree_totale']:.1f}s + {intervention_courante['duree_totale']:.1f}s = {intervention_fusionnee['duree_totale']:.1f}s")
                    i += 1
                    continue
            
            # Intervention OK, la garder
            interventions_fusionnees.append(intervention_courante)
            i += 1
        
        return interventions_fusionnees
    
    def _fusionner_deux_interventions(self, interv1, interv2):
        """Fusionne deux interventions adjacentes."""
        
        segments_fusionnes = interv1["segments"] + interv2["segments"]
        texte_complet = interv1["texte_complet"] + " " + interv2["texte_complet"]
        
        intervention_fusionnee = {
            "speaker_id": interv1["speaker_id"],
            "speaker": interv1["speaker"],
            "debut": interv1["debut"],
            "fin": interv2["fin"],
            "duree_totale": interv2["fin"] - interv1["debut"],
            "segments": segments_fusionnes,
            "texte_complet": texte_complet,
            "nb_mots": len(texte_complet.split()),
            "nb_segments": len(segments_fusionnes),
            "duree_formattee": str(timedelta(seconds=int(interv2["fin"] - interv1["debut"])))
        }
        
        return intervention_fusionnee
    
    def extraire_intervention_validee(self, intervention, marge_contexte=2):
        """Extrait une intervention validée."""
        
        if not self.video_file:
            return False
        
        start_time = max(0, intervention["debut"] - marge_contexte)
        end_time = intervention["fin"] + marge_contexte
        duree_totale = end_time - start_time
        
        # Nom de fichier descriptif
        debut_format = str(timedelta(seconds=int(intervention["debut"]))).replace(':', 'h', 1).replace(':', 'm') + 's'
        duree_format = str(timedelta(seconds=int(intervention["duree_totale"]))).replace(':', 'h', 1).replace(':', 'm') + 's'
        
        timestamp_creation = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = os.path.join(
            self.output_dir,
            f"{intervention['speaker']}_{debut_format}_dur{duree_format}_validated_{timestamp_creation}.mp4"
        )
        
        # Extraction
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", self.video_file,
            "-t", str(duree_totale),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            output_file
        ]
        
        print(f"🎬 {intervention['speaker']} : {debut_format} ({duree_format})")
        print(f"   📝 {intervention['nb_mots']} mots en {intervention['nb_segments']} segments")
        print(f"   💬 \"{intervention['texte_complet'][:80]}...\"")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_file) / (1024*1024)
            print(f"   ✅ {file_size:.1f} MB créé")
            return output_file
        else:
            print(f"   ❌ Erreur : {result.stderr}")
            return False
    
    def processus_multi_criteres_complet(self):
        """Pipeline multi-critères complet."""
        
        print("🧠 EXTRACTEUR MULTI-CRITÈRES INTELLIGENT")
        print("=" * 50)
        print("🎯 Analyse temporelle + textuelle + structurelle")
        print("=" * 50)
        
        # 1. Initialisation
        if not self.initialiser_whisper():
            return []
        
        if not self.get_video_file():
            print("❌ Aucune vidéo trouvée dans working_dir_extractor/")
            return []
        
        file_size = os.path.getsize(self.video_file) / (1024*1024)
        print(f"📁 Vidéo : {os.path.basename(self.video_file)} ({file_size:.1f} MB)")
        
        # 2. Transcription et analyse
        print(f"\n📝 PHASE 1 : TRANSCRIPTION + ANALYSE MULTI-CRITÈRES")
        print("-" * 55)
        
        debut = time.time()
        if not self.transcrire_avec_analyse():
            print("❌ Échec transcription")
            return []
        temps_transcription = time.time() - debut
        
        print(f"⏱️  Transcription + analyse : {temps_transcription/60:.1f} minutes")
        
        # 3. Segmentation intelligente
        print(f"\n🧠 PHASE 2 : SEGMENTATION INTELLIGENTE")
        print("-" * 40)
        
        debut = time.time()
        interventions = self.segmenter_interventions_intelligentes()
        temps_segmentation = time.time() - debut
        
        if not interventions:
            print("❌ Aucune intervention segmentée")
            return []
        
        print(f"⏱️  Segmentation : {temps_segmentation:.1f}s")
        
        # Affichage des résultats
        print(f"\n📋 INTERVENTIONS MULTI-CRITÈRES VALIDÉES :")
        for intervention in interventions:
            print(f"   {intervention['speaker']} | "
                  f"⏰ {str(timedelta(seconds=int(intervention['debut'])))} | "
                  f"Durée: {intervention['duree_formattee']} | "
                  f"Mots: {intervention['nb_mots']}")
        
        # 4. Extraction
        print(f"\n✂️  PHASE 3 : EXTRACTION VALIDÉE")
        print("-" * 30)
        
        extraits_crees = []
        for i, intervention in enumerate(interventions, 1):
            print(f"\n📽️  Extrait {i}/{len(interventions)}")
            
            fichier = self.extraire_intervention_validee(intervention)
            if fichier:
                extraits_crees.append({
                    'fichier': fichier,
                    'intervention': intervention
                })
        
        # 5. Rapport
        self._generer_rapport_multicriteres(extraits_crees)
        
        return extraits_crees
    
    def _generer_rapport_multicriteres(self, extraits_crees):
        """Rapport multi-critères."""
        
        if not extraits_crees:
            return
        
        print(f"\n🎉 EXTRACTION MULTI-CRITÈRES TERMINÉE !")
        print("=" * 40)
        
        duree_totale = sum(e['intervention']['duree_totale'] for e in extraits_crees)
        taille_totale = sum(os.path.getsize(e['fichier']) for e in extraits_crees) / (1024*1024)
        
        print(f"🎬 Extraits validés : {len(extraits_crees)}")
        print(f"⏱️  Durée totale : {timedelta(seconds=int(duree_totale))}")
        print(f"💾 Espace : {taille_totale:.1f} MB")
        print(f"📂 Dossier : {self.output_dir}/")
        
        # Analyse de la qualité des extraits
        durees = [e['intervention']['duree_totale'] for e in extraits_crees]
        mots = [e['intervention']['nb_mots'] for e in extraits_crees]
        
        nb_courts = len([d for d in durees if d < 30])
        nb_moyens = len([d for d in durees if 30 <= d <= 180])
        nb_longs = len([d for d in durees if d > 180])
        
        print(f"\n📊 QUALITÉ DES EXTRAITS :")
        print(f"   Courts (< 30s) : {nb_courts}")
        print(f"   Moyens (30s-3min) : {nb_moyens}")
        print(f"   Longs (> 3min) : {nb_longs}")
        print(f"   Durée moyenne : {sum(durees)/len(durees):.1f}s")
        print(f"   Mots moyens : {sum(mots)/len(mots):.0f}")
        
        print(f"\n🧠 MÉTHODE MULTI-CRITÈRES :")
        print("• Analyse temporelle (pauses)")
        print("• Analyse textuelle (patterns début/fin)")
        print("• Analyse structurelle (questions/réponses)")
        print("• Post-traitement (fusion/division)")
        print("• Validation croisée des critères")
        
        # Sauvegarde
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rapport_file = os.path.join(self.output_dir, f"rapport_multicriteres_{timestamp}.json")
        
        rapport = {
            'video_source': os.path.basename(self.video_file),
            'methode': 'Multi-critères (temporel + textuel + structurel)',
            'nb_extraits': len(extraits_crees),
            'qualite_extraits': {
                'courts_moins_30s': nb_courts,
                'moyens_30s_3min': nb_moyens,
                'longs_plus_3min': nb_longs
            },
            'nb_transitions_detectees': len(self.points_transition_candidats),
            'extraits': []
        }
        
        for extrait in extraits_crees:
            intervention = extrait['intervention']
            rapport['extraits'].append({
                'fichier': os.path.basename(extrait['fichier']),
                'speaker': intervention['speaker'],
                'debut': intervention['debut'],
                'duree': intervention['duree_totale'],
                'nb_mots': intervention['nb_mots'],
                'transcription': intervention['texte_complet']
            })
        
        with open(rapport_file, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Rapport multi-critères : {rapport_file}")

def main():
    """Fonction principale multi-critères."""
    
    try:
        import whisper
        print("✅ Whisper disponible")
    except ImportError:
        print("❌ Installez Whisper : pip install openai-whisper")
        return
    
    try:
        extractor = MultiCriteriaSpeechExtractor()
        extraits = extractor.processus_multi_criteres_complet()
        
        if extraits:
            durees = [e['intervention']['duree_totale'] for e in extraits]
            print(f"\n🎯 SUCCÈS ! {len(extraits)} interventions multi-critères extraites.")
            print(f"📊 Plage réaliste : {min(durees):.1f}s - {max(durees):.1f}s")
        else:
            print("\n❌ Échec de l'extraction multi-critères.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Arrêt utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")

if __name__ == "__main__":
    main()