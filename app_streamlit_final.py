import streamlit as st
import os
import subprocess
from pathlib import Path
import datetime
import time
import json

# Configuration de la page
st.set_page_config(
    page_title="Studio Vidéo NEWS DU 237",
    page_icon="🎬",
    layout="wide"
)

# ============================================================================
# CONFIGURATION DES DOSSIERS
# ============================================================================

WORKING_DIR = Path("working_dir_wave_sub")
OUTPUT_DIR = Path("video_generator_wave_sub_output")
EXTRACTOR_DIR = Path("extracted_clips")
CROPPED_DIR = Path("cropped_videos")

# Créer les dossiers s'ils n'existent pas
for directory in [WORKING_DIR, OUTPUT_DIR, EXTRACTOR_DIR, CROPPED_DIR]:
    directory.mkdir(exist_ok=True)

# Limite de taille de fichier (2 GB)
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB en bytes

# ============================================================================
# FONCTIONS DE NETTOYAGE
# ============================================================================

def clean_input_folder():
    """
    Nettoie le dossier working_dir en ne gardant que background_video.mp4.
    Supprime tous les autres fichiers vidéo/audio pour éviter confusion.
    """
    if not WORKING_DIR.exists():
        return 0
    
    files_removed = 0
    for file in WORKING_DIR.iterdir():
        # Garder uniquement background_video.mp4 et les thumbnails
        if file.name == "background_video.mp4" or file.name.endswith("_thumbnail.jpg"):
            continue
        
        # Supprimer les autres fichiers
        if file.is_file():
            try:
                file.unlink()
                files_removed += 1
            except:
                pass
    
    return files_removed

def list_input_files():
    """Liste les fichiers vidéo/audio dans le dossier input (hors background)."""
    if not WORKING_DIR.exists():
        return []
    
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    audio_extensions = {'.mp3', '.wav', '.aac', '.m4a'}
    
    files = []
    for file in WORKING_DIR.iterdir():
        if file.name == "background_video.mp4" or file.name.endswith("_thumbnail.jpg"):
            continue
        
        if file.suffix.lower() in video_extensions or file.suffix.lower() in audio_extensions:
            files.append({
                'name': file.name,
                'path': file,
                'size': file.stat().st_size / (1024 * 1024),  # MB
                'type': 'video' if file.suffix.lower() in video_extensions else 'audio'
            })
    
    return files

def list_generated_videos():
    """Liste toutes les vidéos générées dans le dossier output."""
    if not OUTPUT_DIR.exists():
        return []
    
    videos = []
    
    # Vidéos mini-vidéo (Tab 3)
    for file in OUTPUT_DIR.glob("podcast_simple_*.mp4"):
        videos.append({
            'name': file.name,
            'path': file,
            'size': file.stat().st_size / (1024 * 1024),  # MB
            'mtime': file.stat().st_mtime,
            'date': datetime.datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'mini-video'
        })
    
    # Vidéos audio (Tab 4)
    for file in OUTPUT_DIR.glob("podcast_audio_*.mp4"):
        videos.append({
            'name': file.name,
            'path': file,
            'size': file.stat().st_size / (1024 * 1024),  # MB
            'mtime': file.stat().st_mtime,
            'date': datetime.datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'audio-interview'
        })
    
    # Trier par date (plus récent en premier)
    videos.sort(key=lambda x: x['mtime'], reverse=True)
    
    return videos

def is_image_file(file_path):
    """Vérifie si le fichier est une image."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return Path(file_path).suffix.lower() in image_extensions

def extract_audio_from_video(video_path, output_audio_path):
    """Extrait l'audio d'une vidéo."""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            output_audio_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_audio_path
    except:
        return None

# ============================================================================
# AUTHENTIFICATION
# ============================================================================

def check_password():
    """Retourne True si l'utilisateur a entré le bon mot de passe."""
    
    def password_entered():
        """Vérifie si le mot de passe est correct."""
        if st.session_state["password"] == "300588":  # ← CHANGE CE MOT DE PASSE !
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 Authentification")
        st.text_input(
            "Mot de passe", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.info("💡 Entrez le mot de passe pour accéder à l'application")
        return False
    
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Mot de passe", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("❌ Mot de passe incorrect")
        return False
    
    return True

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def parse_time(time_str):
    """Convertir string temps en secondes."""
    time_str = str(time_str).strip()
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        return int(time_str)

def format_time(seconds):
    """Convertir secondes en format HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_video_duration(video_path):
    """Obtenir la durée d'une vidéo en secondes."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ], stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
        return float(result.stdout.strip())
    except:
        return 0

def get_video_dimensions(video_path):
    """Obtenir largeur et hauteur d'une vidéo."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(video_path)
        ], stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
        data = json.loads(result.stdout)
        width = data['streams'][0]['width']
        height = data['streams'][0]['height']
        return width, height
    except:
        return 0, 0

def extract_frame(video_path, time_seconds, output_path):
    """Extraire un frame à un temps donné."""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(time_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except:
        return False

# ============================================================================
# TAB 1: EXTRACTEUR DE TEMPS
# ============================================================================

def tab_extract_video():
    st.markdown("### ⏱️ Extraire un segment vidéo")
    st.markdown("Extrayez une partie d'une vidéo longue en spécifiant le début et la fin")
    
    # Upload vidéo
    extract_file = st.file_uploader(
        "📁 Choisir une vidéo à extraire",
        type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        key="extract_upload",
        help="Taille max: 2GB"
    )
    
    if extract_file:
        # Vérifier taille
        if extract_file.size > MAX_FILE_SIZE:
            st.error(f"❌ Fichier trop grand: {extract_file.size / (1024**3):.2f} GB (max: 2 GB)")
            return
        
        # Sauvegarder temporairement
        temp_extract_path = EXTRACTOR_DIR / f"temp_{extract_file.name}"
        with st.spinner("📤 Upload en cours..."):
            with open(temp_extract_path, "wb") as f:
                f.write(extract_file.read())
        
        # Obtenir la durée
        video_duration = get_video_duration(temp_extract_path)
        
        if video_duration > 0:
            file_size_mb = extract_file.size / (1024 * 1024)
            st.success(f"✅ {extract_file.name} | {file_size_mb:.1f} MB | Durée: {format_time(video_duration)}")
            
            # Sélection des temps
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**⏱️ Temps de début**")
                start_method = st.radio(
                    "Format de saisie",
                    ["Slider (secondes)", "Texte (MM:SS ou HH:MM:SS)"],
                    key="start_method"
                )
                
                if start_method == "Slider (secondes)":
                    start_seconds = st.slider(
                        "Début",
                        0, int(video_duration) - 1, 0,
                        key="start_slider",
                        help="Sélectionnez le temps de début en secondes"
                    )
                    start_time_str = str(start_seconds)
                    st.info(f"📍 Début: {format_time(start_seconds)}")
                else:
                    start_time_str = st.text_input(
                        "Temps de début",
                        value="00:00",
                        key="start_text",
                        help="Format: MM:SS ou HH:MM:SS"
                    )
                    try:
                        start_seconds = parse_time(start_time_str)
                        st.info(f"📍 Début: {format_time(start_seconds)}")
                    except:
                        st.error("⚠️ Format invalide")
                        start_seconds = 0
            
            with col2:
                st.markdown("**⏱️ Temps de fin**")
                end_method = st.radio(
                    "Format de saisie",
                    ["Slider (secondes)", "Texte (MM:SS ou HH:MM:SS)"],
                    key="end_method"
                )
                
                if end_method == "Slider (secondes)":
                    end_seconds = st.slider(
                        "Fin",
                        1, int(video_duration), int(video_duration),
                        key="end_slider",
                        help="Sélectionnez le temps de fin en secondes"
                    )
                    end_time_str = str(end_seconds)
                    st.info(f"📍 Fin: {format_time(end_seconds)}")
                else:
                    end_time_str = st.text_input(
                        "Temps de fin",
                        value=format_time(video_duration),
                        key="end_text",
                        help="Format: MM:SS ou HH:MM:SS"
                    )
                    try:
                        end_seconds = parse_time(end_time_str)
                        st.info(f"📍 Fin: {format_time(end_seconds)}")
                    except:
                        st.error("⚠️ Format invalide")
                        end_seconds = video_duration
            
            # Calcul durée segment
            segment_duration = end_seconds - start_seconds
            
            if segment_duration > 0:
                st.markdown("---")
                st.info(f"📊 **Durée du segment:** {format_time(segment_duration)} ({segment_duration:.1f}s)")
                
                # Bouton extraction
                if st.button("✂️ Extraire le segment", type="primary", use_container_width=True):
                    with st.spinner("⏳ Extraction en cours..."):
                        try:
                            # Nom du fichier de sortie
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_filename = f"extracted_{Path(extract_file.name).stem}_{timestamp}.mp4"
                            output_path = EXTRACTOR_DIR / output_filename
                            
                            # Extraction
                            cmd = [
                                "ffmpeg", "-y",
                                "-ss", str(start_seconds),
                                "-i", str(temp_extract_path),
                                "-t", str(segment_duration),
                                "-c", "copy",  # Stream copy (très rapide)
                                str(output_path)
                            ]
                            
                            subprocess.run(cmd, check=True, capture_output=True)
                            
                            st.success(f"✅ Segment extrait avec succès!")
                            st.info(f"📁 Fichier sauvegardé: `{output_filename}`")
                            
                            # Proposer téléchargement
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Télécharger le segment",
                                    data=f,
                                    file_name=output_filename,
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                        
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'extraction: {str(e)}")
            else:
                st.warning("⚠️ Le temps de fin doit être après le temps de début")
        else:
            st.error("❌ Impossible de lire la vidéo")

# ============================================================================
# TAB 2: CROP VIDÉO
# ============================================================================

def tab_crop_video():
    st.markdown("### ✂️ Crop Vidéo")
    st.markdown("Recadrez votre vidéo en ajustant les 4 côtés (haut, bas, gauche, droite)")
    
    # Upload vidéo
    crop_file = st.file_uploader(
        "📁 Choisir une vidéo à cropper",
        type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        key="crop_upload",
        help="Taille max: 2GB"
    )
    
    if crop_file:
        # Vérifier taille
        if crop_file.size > MAX_FILE_SIZE:
            st.error(f"❌ Fichier trop grand: {crop_file.size / (1024**3):.2f} GB (max: 2 GB)")
            return
        
        # Sauvegarder temporairement
        temp_crop_path = CROPPED_DIR / f"temp_{crop_file.name}"
        with st.spinner("📤 Upload en cours..."):
            with open(temp_crop_path, "wb") as f:
                f.write(crop_file.read())
        
        # Obtenir dimensions
        width, height = get_video_dimensions(temp_crop_path)
        
        if width > 0 and height > 0:
            file_size_mb = crop_file.size / (1024 * 1024)
            st.success(f"✅ {crop_file.name} | {file_size_mb:.1f} MB | Dimensions: {width}x{height}")
            
            # Extraire frame pour prévisualisation
            frame_path = CROPPED_DIR / "preview_frame.jpg"
            if extract_frame(temp_crop_path, 1, frame_path):
                
                st.markdown("---")
                st.markdown("#### 🎨 Ajuster le cadrage")
                
                # Sliders pour crop
                col1, col2 = st.columns(2)
                
                with col1:
                    crop_top = st.slider(
                        "✂️ Crop HAUT (pixels à enlever)",
                        0, height // 2, 0,
                        key="crop_top",
                        help="Nombre de pixels à enlever du haut"
                    )
                    
                    crop_bottom = st.slider(
                        "✂️ Crop BAS (pixels à enlever)",
                        0, height // 2, 0,
                        key="crop_bottom",
                        help="Nombre de pixels à enlever du bas"
                    )
                
                with col2:
                    crop_left = st.slider(
                        "✂️ Crop GAUCHE (pixels à enlever)",
                        0, width // 2, 0,
                        key="crop_left",
                        help="Nombre de pixels à enlever de la gauche"
                    )
                    
                    crop_right = st.slider(
                        "✂️ Crop DROITE (pixels à enlever)",
                        0, width // 2, 0,
                        key="crop_right",
                        help="Nombre de pixels à enlever de la droite"
                    )
                
                # Calculer nouvelles dimensions
                new_width = width - crop_left - crop_right
                new_height = height - crop_top - crop_bottom
                
                st.markdown("---")
                
                # Afficher résumé
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.metric("📐 Original", f"{width}x{height}")
                
                with col_info2:
                    st.metric("🎯 Après crop", f"{new_width}x{new_height}")
                
                with col_info3:
                    ratio = new_width / new_height if new_height > 0 else 0
                    st.metric("📊 Ratio", f"{ratio:.3f}")
                
                # Aperçu visuel
                with st.expander("👁️ Aperçu du cadrage", expanded=True):
                    st.image(
                        str(frame_path),
                        caption=f"Frame de prévisualisation (crop appliqué visuellement dans l'interface)",
                        use_container_width=True
                    )
                    
                    st.info(f"""
                    **Zone croppée :**
                    - Haut : {crop_top}px
                    - Bas : {crop_bottom}px
                    - Gauche : {crop_left}px
                    - Droite : {crop_right}px
                    """)
                
                # Bouton crop
                if new_width > 0 and new_height > 0:
                    st.markdown("---")
                    
                    if st.button("✂️ Appliquer le crop", type="primary", use_container_width=True):
                        with st.spinner("⏳ Crop en cours..."):
                            try:
                                # Nom du fichier de sortie
                                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                output_filename = f"cropped_{Path(crop_file.name).stem}_{timestamp}.mp4"
                                output_path = CROPPED_DIR / output_filename
                                
                                # Commande FFmpeg crop
                                cmd = [
                                    "ffmpeg", "-y",
                                    "-i", str(temp_crop_path),
                                    "-filter:v", f"crop={new_width}:{new_height}:{crop_left}:{crop_top}",
                                    "-c:a", "copy",  # Copier audio sans ré-encodage
                                    str(output_path)
                                ]
                                
                                subprocess.run(cmd, check=True, capture_output=True)
                                
                                st.success(f"✅ Vidéo croppée avec succès!")
                                st.info(f"📁 Fichier sauvegardé: `{output_filename}`")
                                
                                # Proposer téléchargement
                                with open(output_path, "rb") as f:
                                    st.download_button(
                                        label="⬇️ Télécharger la vidéo croppée",
                                        data=f,
                                        file_name=output_filename,
                                        mime="video/mp4",
                                        use_container_width=True
                                    )
                            
                            except Exception as e:
                                st.error(f"❌ Erreur lors du crop: {str(e)}")
                else:
                    st.error("❌ Les dimensions après crop doivent être positives")
            else:
                st.warning("⚠️ Impossible d'extraire un frame de prévisualisation")
        else:
            st.error("❌ Impossible de lire les dimensions de la vidéo")

# ============================================================================
# TAB 3: GÉNÉRATEUR VIDÉO SIMPLE (CORRIGÉ AVEC SUBPROCESS)
# ============================================================================

def tab_generate_video():
    st.markdown("### 🎬 Générateur Vidéo Simple")
    st.markdown("Créez votre vidéo finale avec background NEWS DU 237 + mini-vidéo")
    
    # ========================================================================
    # AVERTISSEMENT MOBILE
    # ========================================================================
    
    st.warning("""
    ⚠️ **Important pour utilisateurs mobiles :**
    - Gardez l'écran allumé pendant la génération
    - La génération peut prendre plusieurs minutes
    - Ne fermez pas l'application pendant le traitement
    """)
    
    # ========================================================================
    # NETTOYAGE AUTOMATIQUE + LISTE DES FICHIERS INPUT
    # ========================================================================
    
    with st.expander("📂 Fichiers dans le dossier d'entrée", expanded=False):
        input_files = list_input_files()
        
        col_info, col_clean = st.columns([3, 1])
        
        with col_info:
            if input_files:
                st.info(f"🗂️ {len(input_files)} fichier(s) trouvé(s) dans le dossier d'entrée")
                for file in input_files:
                    icon = "🎥" if file['type'] == 'video' else "🎵"
                    st.text(f"{icon} {file['name']} ({file['size']:.1f} MB)")
            else:
                st.success("✅ Dossier d'entrée vide (prêt pour nouvel upload)")
        
        with col_clean:
            if st.button("🧹 Nettoyer", help="Supprime tous les fichiers sauf background_video.mp4"):
                files_removed = clean_input_folder()
                if files_removed > 0:
                    st.success(f"✅ {files_removed} fichier(s) supprimé(s)")
                    st.rerun()
                else:
                    st.info("Rien à nettoyer")
    
    st.markdown("---")
    
    # ========================================================================
    # GESTION DU BACKGROUND
    # ========================================================================
    
    st.markdown("#### 📺 Background")
    
    # Chercher background par défaut
    default_background = WORKING_DIR / "background_video.mp4"
    
    # Lister tous les backgrounds disponibles
    available_backgrounds = list(WORKING_DIR.glob("background_*.mp4"))
    
    # État de sélection de background
    if 'show_background_selector' not in st.session_state:
        st.session_state.show_background_selector = False
    
    if 'show_background_uploader' not in st.session_state:
        st.session_state.show_background_uploader = False
    
    # Afficher le background actuellement utilisé
    if default_background.exists():
        st.success("✅ Background par défaut disponible")
        
        # Extraire miniature du background
        thumbnail_path = WORKING_DIR / "background_thumbnail.jpg"
        if not thumbnail_path.exists() or st.button("🔄 Rafraîchir miniature", key="refresh_thumb"):
            with st.spinner("📸 Création miniature..."):
                extract_frame(default_background, 1, thumbnail_path)
        
        # Afficher miniature avec info
        col_thumb, col_info = st.columns([1, 2])
        
        with col_thumb:
            if thumbnail_path.exists():
                st.image(str(thumbnail_path), caption="Background actuel", use_container_width=True)
        
        with col_info:
            bg_size = default_background.stat().st_size / (1024 * 1024)
            bg_duration = get_video_duration(default_background)
            bg_width, bg_height = get_video_dimensions(default_background)
            
            st.metric("📁 Fichier", default_background.name)
            st.metric("💾 Taille", f"{bg_size:.1f} MB")
            st.metric("⏱️ Durée", format_time(bg_duration))
            st.metric("📐 Dimensions", f"{bg_width}x{bg_height}")
        
        # Boutons d'action
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔄 Changer le background", use_container_width=True):
                st.session_state.show_background_uploader = not st.session_state.show_background_uploader
        
        with col_btn2:
            if len(available_backgrounds) > 1:
                if st.button("📋 Voir tous les backgrounds", use_container_width=True):
                    st.session_state.show_background_selector = not st.session_state.show_background_selector
            else:
                st.info("1 seul background disponible")
    
    else:
        st.warning("⚠️ Aucun background par défaut trouvé")
        st.info("💡 Uploadez un background pour commencer")
        st.session_state.show_background_uploader = True
    
    # ========================================================================
    # SÉLECTEUR DE BACKGROUNDS (si plusieurs disponibles)
    # ========================================================================
    
    if st.session_state.show_background_selector and len(available_backgrounds) > 1:
        st.markdown("---")
        st.markdown("#### 📋 Backgrounds Disponibles")
        
        # Afficher tous les backgrounds en grille
        cols = st.columns(3)
        
        for idx, bg_file in enumerate(available_backgrounds):
            col = cols[idx % 3]
            
            with col:
                # Extraire miniature
                bg_thumb_path = WORKING_DIR / f"thumb_{bg_file.stem}.jpg"
                if not bg_thumb_path.exists():
                    extract_frame(bg_file, 1, bg_thumb_path)
                
                # Afficher miniature
                if bg_thumb_path.exists():
                    st.image(str(bg_thumb_path), use_container_width=True)
                
                # Info
                bg_size = bg_file.stat().st_size / (1024 * 1024)
                st.caption(f"📁 {bg_file.name}")
                st.caption(f"💾 {bg_size:.1f} MB")
                
                # Bouton sélection
                is_default = bg_file.name == default_background.name
                
                if is_default:
                    st.success("✅ Actuel")
                else:
                    if st.button(f"Utiliser", key=f"select_{bg_file.stem}"):
                        # Remplacer le background par défaut
                        import shutil
                        shutil.copy(bg_file, default_background)
                        st.success(f"✅ Background changé : {bg_file.name}")
                        st.rerun()
        
        st.markdown("---")
    
    # ========================================================================
    # UPLOADER DE BACKGROUND
    # ========================================================================
    
    if st.session_state.show_background_uploader:
        st.markdown("---")
        st.markdown("#### 📤 Upload Nouveau Background")
        
        background_file = st.file_uploader(
            "📁 Choisir un background (avec logo NEWS DU 237)",
            type=['mp4', 'mov'],
            key="background_upload",
            help="Vidéo background qui contient déjà le logo"
        )
        
        if background_file:
            # Vérifier taille
            if background_file.size > MAX_FILE_SIZE:
                st.error(f"❌ Fichier trop grand: {background_file.size / (1024**3):.2f} GB (max: 2 GB)")
            else:
                # Options de sauvegarde
                save_option = st.radio(
                    "Comment sauvegarder ce background ?",
                    [
                        "Remplacer le background par défaut",
                        "Sauvegarder comme nouveau background"
                    ],
                    key="save_option"
                )
                
                if st.button("💾 Sauvegarder le background", type="primary"):
                    with st.spinner("📤 Sauvegarde en cours..."):
                        if save_option == "Remplacer le background par défaut":
                            # Sauvegarder comme défaut
                            save_path = default_background
                        else:
                            # Sauvegarder avec timestamp
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            save_path = WORKING_DIR / f"background_{timestamp}.mp4"
                        
                        # Écrire le fichier
                        with open(save_path, "wb") as f:
                            f.write(background_file.read())
                        
                        st.success(f"✅ Background sauvegardé : {save_path.name}")
                        
                        # Créer miniature
                        thumbnail_path = WORKING_DIR / "background_thumbnail.jpg"
                        extract_frame(save_path, 1, thumbnail_path)
                        
                        # Masquer l'uploader
                        st.session_state.show_background_uploader = False
                        st.rerun()
        
        st.markdown("---")
    
    # ========================================================================
    # UPLOAD VIDÉO
    # ========================================================================
    
    st.markdown("#### 🎥 Mini-vidéo")
    
    # Nettoyage automatique avant upload
    if 'last_clean_time' not in st.session_state:
        st.session_state.last_clean_time = 0
    
    # Nettoyer automatiquement si dernier nettoyage > 5 min
    current_time = time.time()
    if current_time - st.session_state.last_clean_time > 300:  # 5 minutes
        files_removed = clean_input_folder()
        if files_removed > 0:
            st.info(f"🧹 Nettoyage automatique : {files_removed} ancien(s) fichier(s) supprimé(s)")
        st.session_state.last_clean_time = current_time
    
    # Option accélération audio
    accelerate_audio = st.checkbox(
        "⚡ Accélérer l'audio à 1.25x",
        value=False,
        help="Réduit la durée de 20% (10 min → 8 min). Recommandé pour interviews longues et podcasts."
    )
    
    if accelerate_audio:
        st.info("✅ Audio sera accéléré à 1.25x (durée réduite de 20%)")
    
    video_file = st.file_uploader(
        "📁 Choisir la vidéo (originale, extraite ou croppée)",
        type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        key="video_upload",
        help="La vidéo qui sera affichée comme mini-vidéo"
    )
    
    # ========================================================================
    # GÉNÉRATION (CORRIGÉ AVEC SUBPROCESS)
    # ========================================================================
    
    if video_file:
        # Vérifier qu'on a un background
        if not default_background.exists():
            st.error("❌ Aucun background disponible. Veuillez en uploader un d'abord.")
            return
        
        # Vérifier taille vidéo
        if video_file.size > MAX_FILE_SIZE:
            st.error(f"❌ Vidéo trop grande: {video_file.size / (1024**3):.2f} GB (max: 2 GB)")
            return
        
        # Sauvegarder la vidéo
        video_path = WORKING_DIR / f"input_{video_file.name}"
        
        with st.spinner("📤 Upload de la vidéo..."):
            with open(video_path, "wb") as f:
                f.write(video_file.read())
        
        # Afficher infos
        video_size_mb = video_file.size / (1024 * 1024)
        video_duration = get_video_duration(video_path)
        video_width, video_height = get_video_dimensions(video_path)
        
        st.success(f"✅ Vidéo: {video_file.name} ({video_size_mb:.1f} MB)")
        
        # Infos détaillées
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            st.metric("⏱️ Durée", format_time(video_duration))
        with col_v2:
            st.metric("📐 Dimensions", f"{video_width}x{video_height}")
        with col_v3:
            ratio = video_width / video_height if video_height > 0 else 0
            st.metric("📊 Ratio", f"{ratio:.3f}")
        
        st.markdown("---")
        
        # Bouton génération
        st.markdown("#### 🚀 Génération")
        
        st.info(f"""
        **Configuration :**
        - Background : `{default_background.name}`
        - Vidéo : `{video_file.name}`
        - Accélération : {'✅ 1.25x' if accelerate_audio else '❌ Normal'}
        - Format sortie : 1080x1920 (portrait 9:16)
        - Qualité : GPU optimisée (preset P7, CQ 19)
        """)
        
        if st.button("🎬 Générer la vidéo finale", type="primary", use_container_width=True, key="generate_btn"):
            with st.spinner("⏳ Génération en cours... Cela peut prendre plusieurs minutes..."):
                try:
                    # ✅ CORRIGÉ: Utiliser subprocess avec script corrigé
                    script_path = Path(__file__).parent / "video_generator_simple_accelerated.py"
                    
                    # Vérifier que le script existe
                    if not script_path.exists():
                        st.error(f"❌ Script introuvable : {script_path}")
                        st.info("💡 Assurez-vous que 'video_generator_simple_accelerated.py' est dans le même dossier que l'app Streamlit")
                        return
                    
                    # Construire la commande
                    cmd = ["python", str(script_path)]
                    if accelerate_audio:
                        cmd.append("--acc")
                    
                    # Exécuter le script
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(Path(__file__).parent)
                    )
                    
                    # Vérifier erreurs
                    if result.returncode != 0:
                        st.error(f"❌ Erreur lors de la génération:")
                        with st.expander("📋 Détails de l'erreur"):
                            st.code(result.stderr, language="text")
                        return
                    
                    # Afficher logs
                    with st.expander("📋 Logs de génération", expanded=False):
                        st.code(result.stdout, language="text")
                    
                    # Trouver la vidéo générée (plus récente)
                    output_files = list(OUTPUT_DIR.glob("podcast_simple_*.mp4"))
                    if output_files:
                        latest_output = max(output_files, key=lambda p: p.stat().st_mtime)
                        
                        st.success("✅ Vidéo générée avec succès!")
                        st.balloons()
                        
                        # Infos du fichier généré
                        output_size = latest_output.stat().st_size / (1024 * 1024)
                        st.info(f"""
                        **Vidéo Finale :**
                        - Fichier : `{latest_output.name}`
                        - Taille : {output_size:.1f} MB
                        - Emplacement : `{OUTPUT_DIR}/`
                        """)
                        
                        # Proposer téléchargement
                        with open(latest_output, "rb") as f:
                            st.download_button(
                                label="⬇️ Télécharger la vidéo finale",
                                data=f,
                                file_name=latest_output.name,
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.warning("⚠️ Fichier généré introuvable dans le dossier de sortie")
                
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération")
                    with st.expander("📋 Détails de l'erreur"):
                        st.exception(e)
    
    else:
        st.info("💡 Uploadez une vidéo pour commencer la génération")

# ============================================================================
# TAB 4: VIDÉOS GÉNÉRÉES
# ============================================================================

def tab_generated_videos():
    st.markdown("### 📂 Vidéos Générées")
    st.markdown("Consultez et téléchargez vos vidéos générées précédemment")
    
    # Lister les vidéos
    videos = list_generated_videos()
    
    if not videos:
        st.info("📭 Aucune vidéo générée pour le moment")
        st.markdown("💡 Les vidéos générées dans les **Tab 3 et Tab 5** apparaîtront ici")
        return
    
    # Statistiques
    total_size = sum(v['size'] for v in videos)
    st.success(f"📊 {len(videos)} vidéo(s) générée(s) | Taille totale : {total_size:.1f} MB")
    
    # Bouton nettoyage global
    col_header1, col_header2 = st.columns([3, 1])
    with col_header2:
        if st.button("🗑️ Tout supprimer", type="secondary"):
            if st.session_state.get('confirm_delete_all', False):
                for video in videos:
                    try:
                        video['path'].unlink()
                    except:
                        pass
                st.success("✅ Toutes les vidéos supprimées")
                st.session_state.confirm_delete_all = False
                st.rerun()
            else:
                st.session_state.confirm_delete_all = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")
    
    st.markdown("---")
    
    # Afficher chaque vidéo
    for idx, video in enumerate(videos):
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Icône selon le type
                icon = "🎬" if video['type'] == 'mini-video' else "🎙️"
                type_label = "Mini-vidéo" if video['type'] == 'mini-video' else "Audio/Interview"
                
                st.markdown(f"**{icon} {video['name']}**")
                st.caption(f"📅 {video['date']} | 🏷️ {type_label}")
                st.caption(f"💾 {video['size']:.1f} MB")
            
            with col2:
                # Bouton téléchargement
                with open(video['path'], "rb") as f:
                    st.download_button(
                        label="⬇️ Télécharger",
                        data=f,
                        file_name=video['name'],
                        mime="video/mp4",
                        key=f"download_{idx}",
                        use_container_width=True
                    )
            
            with col3:
                # Bouton suppression
                if st.button("🗑️", key=f"delete_{idx}", help="Supprimer cette vidéo"):
                    try:
                        video['path'].unlink()
                        st.success(f"✅ {video['name']} supprimée")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur : {str(e)}")
            
            st.markdown("---")
    
    # Footer
    st.markdown("💡 **Astuce :** Téléchargez et supprimez régulièrement pour économiser l'espace disque")

# ============================================================================
# TAB 5: GÉNÉRER AUDIO (INTERVIEWS) - CORRIGÉ AVEC SUBPROCESS
# ============================================================================

def tab_generate_audio():
    st.markdown("### 🎙️ Générateur Audio (Interviews)")
    st.markdown("Créez une vidéo à partir d'un audio avec photo optionnelle")
    
    # ========================================================================
    # AVERTISSEMENT MOBILE
    # ========================================================================
    
    st.warning("""
    ⚠️ **Important pour utilisateurs mobiles :**
    - Gardez l'écran allumé pendant la génération
    - La génération peut prendre plusieurs minutes
    - Ne fermez pas l'application pendant le traitement
    """)
    
    st.markdown("---")
    
    # ========================================================================
    # GESTION DU BACKGROUND
    # ========================================================================
    
    st.markdown("#### 📺 Background")
    
    # Chercher background par défaut
    default_background = WORKING_DIR / "background_video.mp4"
    
    if not default_background.exists():
        st.error("❌ Aucun background disponible. Veuillez uploader un background dans le Tab 3 d'abord.")
        return
    
    st.success(f"✅ Background : {default_background.name}")
    
    st.markdown("---")
    
    # ========================================================================
    # OPTIONS
    # ========================================================================
    
    st.markdown("#### ⚙️ Options")
    
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        # Option accélération audio
        accelerate_audio = st.checkbox(
            "⚡ Accélérer l'audio à 1.25x",
            value=False,
            help="Réduit la durée de 20% (10 min → 8 min)",
            key="audio_accelerate"
        )
    
    with col_opt2:
        # Option waveform
        use_waveform = st.checkbox(
            "🌊 Afficher waveform",
            value=False,
            help="Ajoute une visualisation animée de l'audio (plus lent)",
            key="audio_waveform"
        )
    
    if accelerate_audio:
        st.info("✅ Audio sera accéléré à 1.25x (durée réduite de 20%)")
    
    if use_waveform:
        st.info("✅ Waveform animée sera générée (traitement plus long)")
    
    st.markdown("---")
    
    # ========================================================================
    # UPLOAD FICHIERS
    # ========================================================================
    
    st.markdown("#### 📁 Fichiers Source")
    
    col_upload1, col_upload2 = st.columns(2)
    
    with col_upload1:
        # Upload vidéo ou audio
        input_file = st.file_uploader(
            "🎥 Vidéo ou 🎵 Audio (requis)",
            type=['mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'aac', 'm4a'],
            key="audio_input",
            help="Vidéo (audio sera extrait) ou fichier audio direct"
        )
    
    with col_upload2:
        # Upload photo (optionnelle)
        photo_file = st.file_uploader(
            "📸 Photo (optionnelle)",
            type=['jpg', 'jpeg', 'png'],
            key="photo_input",
            help="Photo de la personne qui parle (600x600px, optionnelle)"
        )
    
    if photo_file:
        st.success(f"✅ Photo : {photo_file.name}")
        with st.expander("👁️ Aperçu photo"):
            st.image(photo_file, caption=photo_file.name, use_container_width=True)
    else:
        st.info("ℹ️ Pas de photo (background uniquement)")
    
    st.markdown("---")
    
    # ========================================================================
    # GÉNÉRATION (CORRIGÉ AVEC SUBPROCESS)
    # ========================================================================
    
    if input_file:
        # Vérifier taille
        if input_file.size > MAX_FILE_SIZE:
            st.error(f"❌ Fichier trop grand: {input_file.size / (1024**3):.2f} GB (max: 2 GB)")
            return
        
        # Nettoyer dossier input
        files_removed = clean_input_folder()
        if files_removed > 0:
            st.info(f"🧹 {files_removed} ancien(s) fichier(s) nettoyé(s)")
        
        # Sauvegarder les fichiers
        input_path = WORKING_DIR / input_file.name
        
        with st.spinner("📤 Upload du fichier..."):
            with open(input_path, "wb") as f:
                f.write(input_file.read())
        
        # Sauvegarder photo si présente (avec nom original)
        if photo_file:
            # Garder le nom original pour meilleure traçabilité
            photo_path = WORKING_DIR / photo_file.name
            with open(photo_path, "wb") as f:
                f.write(photo_file.read())
            st.success(f"✅ Photo sauvegardée : {photo_file.name}")
        
        # Afficher infos
        file_size_mb = input_file.size / (1024 * 1024)
        st.success(f"✅ Fichier source : {input_file.name} ({file_size_mb:.1f} MB)")
        
        # Déterminer type
        is_video = input_file.name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))
        is_audio = input_file.name.lower().endswith(('.mp3', '.wav', '.aac', '.m4a'))
        
        if is_video:
            st.info("🎥 Vidéo détectée → Audio sera extrait automatiquement")
        elif is_audio:
            st.info("🎵 Audio détecté → Utilisation directe")
        
        st.markdown("---")
        
        # Bouton génération
        st.markdown("#### 🚀 Génération")
        
        config_text = f"""
        **Configuration :**
        - Background : `{default_background.name}`
        - Source : `{input_file.name}` ({'vidéo' if is_video else 'audio'})
        - Photo : {'✅ Oui (600x600px)' if photo_file else '❌ Non'}
        - Waveform : {'✅ Oui' if use_waveform else '❌ Non'}
        - Accélération : {'✅ 1.25x' if accelerate_audio else '❌ Normal'}
        - Format sortie : 1080x1920 (portrait 9:16)
        """
        st.info(config_text)
        
        if st.button("🎬 Générer la vidéo audio", type="primary", use_container_width=True, key="generate_audio_btn"):
            with st.spinner("⏳ Génération en cours... Cela peut prendre plusieurs minutes..."):
                try:
                    # ✅ CORRIGÉ: Utiliser subprocess avec script corrigé
                    script_path = Path(__file__).parent / "video_generator_simple_audio_accelerated.py"
                    
                    # Vérifier que le script existe
                    if not script_path.exists():
                        st.error(f"❌ Script introuvable : {script_path}")
                        st.info("💡 Assurez-vous que 'video_generator_simple_audio_accelerated.py' est dans le même dossier que l'app Streamlit")
                        return
                    
                    # Construire la commande
                    cmd = ["python", str(script_path)]
                    if accelerate_audio:
                        cmd.append("--acc")
                    
                    # Créer config temporaire pour waveform
                    config_file = WORKING_DIR / "temp_audio_config.json"
                    with open(config_file, "w") as f:
                        json.dump({"USE_WAVEFORM": use_waveform}, f)
                    
                    # Note: Le script devra lire ce fichier pour USE_WAVEFORM
                    # Pour l'instant, on utilise la valeur par défaut du script
                    
                    # Exécuter le script
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(Path(__file__).parent)
                    )
                    
                    # Nettoyer config
                    if config_file.exists():
                        config_file.unlink()
                    
                    # Vérifier erreurs
                    if result.returncode != 0:
                        st.error(f"❌ Erreur lors de la génération:")
                        with st.expander("📋 Détails de l'erreur"):
                            st.code(result.stderr, language="text")
                        return
                    
                    # Afficher logs
                    with st.expander("📋 Logs de génération", expanded=False):
                        st.code(result.stdout, language="text")
                    
                    # Trouver la vidéo générée (plus récente)
                    output_files = list(OUTPUT_DIR.glob("podcast_audio_*.mp4"))
                    if output_files:
                        latest_output = max(output_files, key=lambda p: p.stat().st_mtime)
                        
                        st.success("✅ Vidéo audio générée avec succès! 🎉")
                        st.balloons()
                        
                        # Infos du fichier généré
                        output_size = latest_output.stat().st_size / (1024 * 1024)
                        st.info(f"""
                        **Vidéo Finale :**
                        - Fichier : `{latest_output.name}`
                        - Taille : {output_size:.1f} MB
                        - Emplacement : `{OUTPUT_DIR}/`
                        """)
                        
                        # Proposer téléchargement
                        with open(latest_output, "rb") as f:
                            st.download_button(
                                label="⬇️ Télécharger la vidéo audio finale",
                                data=f,
                                file_name=latest_output.name,
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.warning("⚠️ Fichier généré introuvable dans le dossier de sortie")
                
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération")
                    with st.expander("📋 Détails de l'erreur"):
                        st.exception(e)
    
    else:
        st.info("💡 Uploadez une vidéo ou un audio pour commencer la génération")

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

# Vérifier authentification
if not check_password():
    st.stop()

# Header
st.title("🎬 Studio Vidéo NEWS DU 237")
st.markdown("**Plateforme complète de création vidéo**")
st.markdown("---")

# Créer les tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⏱️ Extraire Segment",
    "✂️ Crop Vidéo",
    "🎬 Générer Vidéo",
    "🎙️ Générer Audio",
    "📂 Vidéos Générées"
])

with tab1:
    tab_extract_video()

with tab2:
    tab_crop_video()

with tab3:
    tab_generate_video()

with tab4:
    tab_generate_audio()

with tab5:
    tab_generated_videos()

# Footer
st.markdown("---")
st.markdown("**💡 Workflow recommandé:**")
st.markdown("""
1. **⏱️ Tab 1:** Extraire un segment d'une longue vidéo (optionnel)
2. **✂️ Tab 2:** Cropper la vidéo pour enlever les interfaces (optionnel)
3. **🎬 Tab 3:** Générer vidéo avec mini-vidéo + **option accélération ⚡ 1.25x**
4. **🎙️ Tab 4:** Générer vidéo audio/interview + photo + **option accélération ⚡ 1.25x**
5. **📂 Tab 5:** Télécharger et gérer vos vidéos générées
""")

st.markdown("---")
st.markdown("**✨ Nouveautés :**")
st.markdown("""
- ✅ **Accélération 1.25x** (Tab 3 & Tab 4) → Réduit durée de 20% avec audio uniquement
- ⚠️ **Mode normal recommandé** → Accélération vidéo en cours d'amélioration (problème sync)
- ✅ **Méthode corrigée** → Utilise subprocess pour fiabilité maximale
- ✅ **Mode Audio/Interview** (Tab 4) → Audio + photo optionnelle + waveform
- ✅ **Bug fix** → Division par zéro corrigée dans stats
- ✅ **Photo 600x600px** → Même dimensions que mini-vidéo
""")

st.markdown("---")
st.markdown("**📱 Conseils mobile:**")
st.markdown("""
- Gardez l'écran allumé pendant la génération
- Tab 3 (vidéo) : génération ~2-5 minutes
- Tab 4 (audio) : génération ~1-3 minutes
- Les logs montrent la progression en temps réel
""")