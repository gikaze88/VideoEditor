#!/usr/bin/env python3

import subprocess
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

class SingleVideoComposer:
    def __init__(self, working_dir="working_dir", output_dir="output"):
        self.working_dir = Path(working_dir)
        self.output_dir = Path(output_dir)
        
        # Créer le dossier output s'il n'existe pas
        self.output_dir.mkdir(exist_ok=True)
        
        self.background_video = self.working_dir / "background.mp4"
        self.center_video = self.working_dir / "video.mp4"
        
        # Configuration équilibrée qualité/vitesse - vidéo centrale plus grande
        self.config = {
            "output_width": 1920,
            "output_height": 1080,
            # Dimensions en POURCENTAGE de l'écran (plus grande pour une seule vidéo)
            "video_width_percent": 55,    # 55% de la largeur écran
            "video_height_percent": 55,   # 55% de la hauteur écran
            # Position au centre de l'écran
            "center_x_percent": 22.5,     # 22.5% du bord gauche (centré)
            "center_y_percent": 22.5,     # 22.5% du bord haut (centré)
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
        width = int(self.config['output_width'] * self.config['video_width_percent'] / 100)
        height = int(self.config['output_height'] * self.config['video_height_percent'] / 100)
        
        center_x = int(self.config['output_width'] * self.config['center_x_percent'] / 100)
        center_y = int(self.config['output_height'] * self.config['center_y_percent'] / 100)
        
        return {
            'width': width,
            'height': height,
            'center_x': center_x,
            'center_y': center_y
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
        """Génère le nom de fichier: video_single_timestamp.mp4"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"video_single_{timestamp}.mp4"
    
    def check_files(self):
        """Vérification des fichiers nécessaires"""
        files = [self.background_video, self.center_video]
        missing_files = [f for f in files if not f.exists()]
        
        if missing_files:
            print("❌ Fichiers manquants:")
            for f in missing_files:
                print(f"   - {f}")
            return False
        
        print("✓ Tous les fichiers présents")
        return True
    
    def create_single_video(self):
        """
        Crée UNE vidéo composite avec une seule vidéo centrée et agrandie
        """
        
        if not self.check_files():
            return False
        
        # Obtenir la durée
        print("\n📊 Analyse de la vidéo...")
        video_duration = self.get_video_duration(self.center_video)
        
        if video_duration is None:
            print("❌ Impossible d'obtenir la durée")
            return False
        
        output_path = self.generate_output_filename()
        
        # Calculer les dimensions
        dims = self.calculate_dimensions()
        
        print(f"🎬 Création: {output_path.name}")
        print(f"⏱️  Durée: {video_duration:.1f}s")
        print(f"📐 Dimensions: {dims['width']}x{dims['height']} ({self.config['video_width_percent']}% de l'écran)")
        print(f"📐 Position: Centrée sur l'écran")
        print(f"👥 Mode: Vidéo unique centrée et agrandie")
        
        # Construction du filtre simplifié
        filter_complex = self._build_filter_complex(video_duration, dims)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.background_video),
            '-i', str(self.center_video),
            '-filter_complex', filter_complex,
            '-map', '[final_video]',
            '-map', '[final_audio]',
            '-t', str(video_duration),
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
    
    def _build_filter_complex(self, video_duration, dims):
        """Filtre simplifié pour une seule vidéo centrée"""
        
        config = self.config
        
        # Filtre simple pour une vidéo centrée
        filter_complex = f"""
[0:v]loop=loop=-1:size=32767:start=0,scale={config['output_width']}:{config['output_height']},fps={config['fps']}[bg_loop];
[1:v]scale={dims['width']}:{dims['height']},fps={config['fps']}[center_scaled];
[bg_loop][center_scaled]overlay=x={dims['center_x']}:y={dims['center_y']}[final_video];
[1:a]aresample=async=1[final_audio];
"""
        return filter_complex

def main():
    parser = argparse.ArgumentParser(description='🎬 Créateur de vidéos composites avec une seule vidéo centrée')
    parser.add_argument('--size', type=int, default=55,
                       help='Taille de la vidéo en pourcentage (défaut: 55)')
    parser.add_argument('--transition', type=float, default=0.5,
                       help='Durée du fondu en secondes (défaut: 0.5)')
    parser.add_argument('--quality', type=int, default=23,
                       help='Qualité CRF - plus bas = meilleure (18=haute, 23=bonne, 28=correcte)')
    parser.add_argument('--working-dir', default='working_dir',
                       help='Dossier contenant les vidéos')
    
    args = parser.parse_args()
    
    composer = SingleVideoComposer(working_dir=args.working_dir)
    
    # Calculer la position centrée dynamiquement selon la taille
    center_position = (100 - args.size) / 2
    
    # Appliquer les paramètres
    composer.set_config(
        video_width_percent=args.size,
        video_height_percent=args.size,
        center_x_percent=center_position,
        center_y_percent=center_position,
        transition_duration=args.transition,
        crf=args.quality
    )
    
    print("🎬 Créateur de vidéos composites - Mode: Vidéo Unique Centrée")
    print(f"📁 Dossier d'entrée: {composer.working_dir}")
    print(f"📁 Dossier de sortie: {composer.output_dir}")
    print("👥 Arrangement: Vidéo unique centrée et agrandie")
    print("🎥 Fichiers requis: video.mp4, background.mp4")
    
    # Mesurer le temps
    start_time = datetime.now()
    result = composer.create_single_video()
    end_time = datetime.now()
    
    if result:
        processing_time = (end_time - start_time).total_seconds()
        print(f"\n🎉 Terminé en {processing_time:.1f}s")
        print(f"💡 Vidéo unique centrée créée avec succès")
    else:
        print("\n❌ Échec de la création")
        sys.exit(1)

if __name__ == "__main__":
    main() 