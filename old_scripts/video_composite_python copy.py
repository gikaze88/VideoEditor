#!/usr/bin/env python3

import subprocess
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

class VideoComposer:
    def __init__(self, working_dir="working_dir", output_dir="output"):
        self.working_dir = Path(working_dir)
        self.output_dir = Path(output_dir)
        
        # Créer le dossier output s'il n'existe pas
        self.output_dir.mkdir(exist_ok=True)
        
        self.background_video = self.working_dir / "background.mp4"
        self.left_video = self.working_dir / "video_left.mp4"
        self.right_video = self.working_dir / "video_right.mp4"
        
        # Configuration équilibrée qualité/vitesse
        self.config = {
            "output_width": 1920,
            "output_height": 1080,
            # Dimensions en POURCENTAGE de l'écran
            "small_width_percent": 25,    # 25% de la largeur écran
            "small_height_percent": 25,   # 25% de la hauteur écran
            # Positions en POURCENTAGE
            "left_x_percent": 2.6,        # 2.6% du bord gauche
            "left_y_percent": 4.6,        # 4.6% du bord haut
            "right_x_percent": 72.4,      # 72.4% du bord gauche
            "right_y_percent": 70.4,      # 70.4% du bord haut
            "fps": 30,
            "crf": 23,                    # Bonne qualité par défaut
            "preset": "medium",           # Bon équilibre qualité/temps
            "transition_duration": 0.5,   # Durée du fondu en secondes
        }
    
    def set_config(self, **kwargs):
        """Permet de modifier la configuration facilement"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                print(f"✓ Configuration: {key} = {value}")
            else:
                print(f"⚠️  Paramètre ignoré: {key}")
    
    def calculate_dimensions(self):
        """Calcule les dimensions réelles en pixels à partir des pourcentages"""
        width = int(self.config['output_width'] * self.config['small_width_percent'] / 100)
        height = int(self.config['output_height'] * self.config['small_height_percent'] / 100)
        
        left_x = int(self.config['output_width'] * self.config['left_x_percent'] / 100)
        left_y = int(self.config['output_height'] * self.config['left_y_percent'] / 100)
        right_x = int(self.config['output_width'] * self.config['right_x_percent'] / 100)
        right_y = int(self.config['output_height'] * self.config['right_y_percent'] / 100)
        
        return {
            'width': width,
            'height': height,
            'left_x': left_x,
            'left_y': left_y,
            'right_x': right_x,
            'right_y': right_y
        }
    
    def get_video_duration(self, video_path):
        """Obtient la durée d'une vidéo en secondes"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            print(f"❌ Erreur durée {video_path}: {e}")
            return None
    
    def generate_output_filename(self):
        """Génère le nom de fichier: video_composite_timestamp.mp4"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"video_composite_{timestamp}.mp4"
    
    def check_files(self):
        """Vérification des fichiers nécessaires"""
        files = [self.background_video, self.left_video, self.right_video]
        missing_files = [f for f in files if not f.exists()]
        
        if missing_files:
            print("❌ Fichiers manquants:")
            for f in missing_files:
                print(f"   - {f}")
            return False
        
        print("✓ Tous les fichiers présents")
        return True
    
    def create_composite_video(self):
        """
        Crée UNE SEULE vidéo composite avec transitions de qualité
        """
        
        if not self.check_files():
            return False
        
        # Obtenir les durées
        print("\n📊 Analyse des vidéos...")
        left_duration = self.get_video_duration(self.left_video)
        right_duration = self.get_video_duration(self.right_video)
        
        if left_duration is None or right_duration is None:
            print("❌ Impossible d'obtenir les durées")
            return False
        
        total_duration = left_duration + right_duration
        output_path = self.generate_output_filename()
        
        # Calculer les dimensions
        dims = self.calculate_dimensions()
        
        print(f"🎬 Création: {output_path.name}")
        print(f"⏱️  Durée: vidéo gauche {left_duration:.1f}s + vidéo droite {right_duration:.1f}s = {total_duration:.1f}s total")
        print(f"📐 Dimensions: {dims['width']}x{dims['height']} ({self.config['small_width_percent']}% de l'écran)")
        print(f"🎭 Transition: fondu de {self.config['transition_duration']}s entre les vidéos")
        
        # Construction du filtre avec transitions
        filter_complex = self._build_filter_complex(left_duration, right_duration, dims)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.background_video),
            '-i', str(self.left_video),
            '-i', str(self.right_video),
            '-filter_complex', filter_complex,
            '-map', '[final_video]',
            '-map', '[final_audio]',
            '-t', str(total_duration),
            '-c:v', 'libx264',
            '-preset', self.config['preset'],
            '-crf', str(self.config['crf']),
            '-r', str(self.config['fps']),
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ]
        
        print("⚙️  Encodage en cours...")
        
        try:
            # Afficher la progression si possible, sinon silencieux
            subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
            
            # Vérification du résultat
            if output_path.exists():
                file_size = output_path.stat().st_size / (1024*1024)  # MB
                print(f"✅ Vidéo créée: {output_path.name}")
                print(f"📁 Taille: {file_size:.1f} MB")
                print(f"📂 Emplacement: {output_path}")
                return output_path
            else:
                print("❌ Fichier non créé")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'encodage: {e}")
            return False
    
    def _build_filter_complex(self, left_duration, right_duration, dims):
        """Filtre optimisé pour transitions de qualité"""
        
        config = self.config
        transition_duration = config['transition_duration']
        transition_start = left_duration - transition_duration
        
        # Filtre complet avec transitions professionnelles
        filter_complex = f"""
[0:v]loop=loop=-1:size=32767:start=0,scale={config['output_width']}:{config['output_height']},fps={config['fps']}[bg_loop];
[1:v]scale={dims['width']}:{dims['height']},fps={config['fps']}[left_scaled];
[2:v]scale={dims['width']}:{dims['height']},fps={config['fps']}[right_scaled];
[left_scaled]tpad=stop_mode=clone:stop_duration={right_duration}[left_extended];
[right_scaled]tpad=start_duration={left_duration}:start_mode=clone[right_extended];
[left_extended]fade=t=out:st={transition_start}:d={transition_duration}:alpha=1[left_faded];
[right_extended]fade=t=in:st={left_duration}:d={transition_duration}:alpha=1[right_faded];
[bg_loop][left_faded]overlay=x={dims['left_x']}:y={dims['left_y']}[bg_with_left];
[bg_with_left][right_faded]overlay=x={dims['right_x']}:y={dims['right_y']}[final_video];
[1:a]apad=pad_dur={right_duration}[left_audio_extended];
[2:a]adelay={left_duration * 1000}|{left_duration * 1000}[right_audio_delayed];
[left_audio_extended][right_audio_delayed]amix=inputs=2:duration=longest[final_audio];
"""
        return filter_complex

def main():
    parser = argparse.ArgumentParser(description='🎬 Créateur de vidéos composites avec transitions')
    parser.add_argument('--size', type=int, default=25,
                       help='Taille des vidéos en pourcentage (défaut: 25)')
    parser.add_argument('--transition', type=float, default=0.5,
                       help='Durée du fondu en secondes (défaut: 0.5)')
    parser.add_argument('--quality', type=int, default=23,
                       help='Qualité CRF - plus bas = meilleure (18=haute, 23=bonne, 28=correcte)')
    parser.add_argument('--working-dir', default='working_dir',
                       help='Dossier contenant les vidéos')
    
    args = parser.parse_args()
    
    composer = VideoComposer(working_dir=args.working_dir)
    
    # Appliquer les paramètres
    composer.set_config(
        small_width_percent=args.size,
        small_height_percent=args.size,
        transition_duration=args.transition,
        crf=args.quality
    )
    
    print("🎬 Créateur de vidéos composites avec transitions")
    print(f"📁 Dossier d'entrée: {composer.working_dir}")
    print(f"📁 Dossier de sortie: {composer.output_dir}")
    print("⚡ Avantage: Une seule vidéo créée (transitions) = 2x plus rapide qu'avant !")
    
    # Mesurer le temps
    start_time = datetime.now()
    result = composer.create_composite_video()
    end_time = datetime.now()
    
    if result:
        processing_time = (end_time - start_time).total_seconds()
        print(f"\n🎉 Terminé en {processing_time:.1f}s")
        print(f"💡 Temps divisé par 2 (pas de version basic)")
    else:
        print("\n❌ Échec de la création")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
    def set_config(self, **kwargs):
        """Permet de modifier la configuration facilement"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                print(f"✓ Configuration: {key} = {value}")
            else:
                print(f"⚠️  Paramètre ignoré: {key}")
    
    def calculate_dimensions(self):
        """Calcule les dimensions réelles en pixels à partir des pourcentages"""
        width = int(self.config['output_width'] * self.config['small_width_percent'] / 100)
        height = int(self.config['output_height'] * self.config['small_height_percent'] / 100)
        
        left_x = int(self.config['output_width'] * self.config['left_x_percent'] / 100)
        left_y = int(self.config['output_height'] * self.config['left_y_percent'] / 100)
        right_x = int(self.config['output_width'] * self.config['right_x_percent'] / 100)
        right_y = int(self.config['output_height'] * self.config['right_y_percent'] / 100)
        
        return {
            'width': width,
            'height': height,
            'left_x': left_x,
            'left_y': left_y,
            'right_x': right_x,
            'right_y': right_y
        }
    
    def get_video_duration(self, video_path):
        """Obtient la durée d'une vidéo en secondes"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            print(f"❌ Erreur durée {video_path}: {e}")
            return None
    
    def generate_output_filename(self):
        """Génère le nom de fichier demandé: video_composite_timestamp.mp4"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"video_composite_{timestamp}.mp4"
    
    def check_files(self):
        """Vérification rapide des fichiers"""
        files = [self.background_video, self.left_video, self.right_video]
        missing_files = [f for f in files if not f.exists()]
        
        if missing_files:
            print("❌ Fichiers manquants:")
            for f in missing_files:
                print(f"   - {f}")
            return False
        return True
    
    def create_composite_video(self):
        """
        Crée UNE SEULE vidéo composite avec transitions (optimisé pour la vitesse)
        """
        
        if not self.check_files():
            return False
        
        # Obtenir les durées rapidement
        left_duration = self.get_video_duration(self.left_video)
        right_duration = self.get_video_duration(self.right_video)
        
        if left_duration is None or right_duration is None:
            print("❌ Impossible d'obtenir les durées")
            return False
        
        total_duration = left_duration + right_duration
        output_path = self.generate_output_filename()
        
        # Calculer les dimensions
        dims = self.calculate_dimensions()
        
        print(f"🎬 Création: {output_path.name}")
        print(f"⏱️  Durée totale: {total_duration:.1f}s")
        print(f"📐 Dimensions: {dims['width']}x{dims['height']} ({self.config['small_width_percent']}%)")
        
        # Construction du filtre optimisé (seulement transitions)
        filter_complex = self._build_filter_complex(left_duration, right_duration, dims)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.background_video),
            '-i', str(self.left_video),
            '-i', str(self.right_video),
            '-filter_complex', filter_complex,
            '-map', '[final_video]',
            '-map', '[final_audio]',
            '-t', str(total_duration),
            '-c:v', 'libx264',
            '-preset', self.config['preset'],  # 'fast' pour plus de vitesse
            '-crf', str(self.config['crf']),
            '-r', str(self.config['fps']),
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ]
        
        try:
            # Exécution silencieuse pour plus de vitesse
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Vérification rapide du résultat
            if output_path.exists():
                file_size = output_path.stat().st_size / (1024*1024)  # MB
                print(f"✅ Créé: {output_path.name} ({file_size:.1f} MB)")
                return output_path
            else:
                print("❌ Fichier non créé")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur FFmpeg: {e}")
            return False
    
    def _build_filter_complex(self, left_duration, right_duration, dims):
        """Filtre optimisé pour transitions uniquement"""
        
        config = self.config
        transition_duration = config['transition_duration']
        transition_start = left_duration - transition_duration
        
        # Filtre complet optimisé en une seule chaîne
        filter_complex = f"""
[0:v]loop=loop=-1:size=32767:start=0,scale={config['output_width']}:{config['output_height']},fps={config['fps']}[bg_loop];
[1:v]scale={dims['width']}:{dims['height']},fps={config['fps']}[left_scaled];
[2:v]scale={dims['width']}:{dims['height']},fps={config['fps']}[right_scaled];
[left_scaled]tpad=stop_mode=clone:stop_duration={right_duration}[left_extended];
[right_scaled]tpad=start_duration={left_duration}:start_mode=clone[right_extended];
[left_extended]fade=t=out:st={transition_start}:d={transition_duration}:alpha=1[left_faded];
[right_extended]fade=t=in:st={left_duration}:d={transition_duration}:alpha=1[right_faded];
[bg_loop][left_faded]overlay=x={dims['left_x']}:y={dims['left_y']}[bg_with_left];
[bg_with_left][right_faded]overlay=x={dims['right_x']}:y={dims['right_y']}[final_video];
[1:a]apad=pad_dur={right_duration}[left_audio_extended];
[2:a]adelay={left_duration * 1000}|{left_duration * 1000}[right_audio_delayed];
[left_audio_extended][right_audio_delayed]amix=inputs=2:duration=longest[final_audio];
"""
        return filter_complex

# Interface simplifiée pour production rapide
def main():
    parser = argparse.ArgumentParser(description='🎬 Créateur de vidéos composites RAPIDE (transitions seulement)')
    parser.add_argument('--size', type=int, default=25,
                       help='Taille des vidéos en pourcentage (défaut: 25)')
    parser.add_argument('--transition', type=float, default=0.5,
                       help='Durée du fondu en secondes (défaut: 0.5)')
    parser.add_argument('--quality', type=int, default=23,
                       help='Qualité CRF - plus bas = meilleure (défaut: 23)')
    parser.add_argument('--preset', choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium'], 
                       default='fast', help='Vitesse d\'encodage (défaut: fast)')
    parser.add_argument('--working-dir', default='working_dir',
                       help='Dossier contenant les vidéos')
    
    args = parser.parse_args()
    
    composer = VideoComposer(working_dir=args.working_dir)
    
    # Appliquer les paramètres
    composer.set_config(
        small_width_percent=args.size,
        small_height_percent=args.size,
        transition_duration=args.transition,
        crf=args.quality,
        preset=args.preset
    )
    
    print("🚀 Créateur de vidéos composites RAPIDE")
    print(f"📁 Entrée: {composer.working_dir}")
    print(f"📁 Sortie: {composer.output_dir}")
    print(f"⚡ Mode: TRANSITIONS uniquement (plus rapide)")
    
    # Création rapide
    start_time = datetime.now()
    result = composer.create_composite_video()
    end_time = datetime.now()
    
    if result:
        processing_time = (end_time - start_time).total_seconds()
        print(f"⏱️  Temps de traitement: {processing_time:.1f}s")
        print(f"📂 Fichier: {result}")
    else:
        print("❌ Échec de la création")
        sys.exit(1)

# Utilisation programmatique simplifiée
class QuickComposer:
    """Interface ultra-simple pour production en masse"""
    
    def __init__(self, working_dir="working_dir"):
        self.composer = VideoComposer(working_dir)
        # Configuration optimisée pour la vitesse
        self.composer.set_config(preset="fast", crf=25)  # Légèrement moins de qualité pour plus de vitesse
    
    def create(self, size=25, transition=0.5):
        """Création ultra-rapide avec paramètres minimaux"""
        self.composer.set_config(
            small_width_percent=size,
            small_height_percent=size,
            transition_duration=transition
        )
        return self.composer.create_composite_video()
    
    def batch_create(self, folders_list):
        """Création en lot pour plusieurs dossiers"""
        results = []
        for folder in folders_list:
            print(f"\n🎬 Traitement: {folder}")
            self.composer.working_dir = Path(folder)
            result = self.create()
            results.append((folder, result))
        return results

if __name__ == "__main__":
    main()