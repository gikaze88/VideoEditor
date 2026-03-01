#!/usr/bin/env python3
"""
Flexible Video Cropper
======================
Crop vidéo avec contrôle total des 4 côtés.
Enlève ce que TU veux - logo, visage, watermark, n'importe où !

Usage:
  python flexible_cropper.py TOP BOTTOM LEFT RIGHT
  
  TOP    = Pixels à enlever du HAUT
  BOTTOM = Pixels à enlever du BAS
  LEFT   = Pixels à enlever de la GAUCHE
  RIGHT  = Pixels à enlever de la DROITE
  
Examples:
  # Enlever logo en haut à droite (200px haut, 300px droite)
  python flexible_cropper.py 200 0 0 300
  
  # Enlever bannière en bas (150px)
  python flexible_cropper.py 0 150 0 0
  
  # Enlever logo gauche ET bannière bas
  python flexible_cropper.py 0 100 250 0
  
  # Centrer : enlever 10% de chaque côté
  python flexible_cropper.py 10% 10% 10% 10%
"""

import os
import glob
import subprocess
import json
import time
from datetime import datetime

def get_video_file(working_dir="working_dir_cropper"):
    """Get the first video file from working directory."""
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(working_dir, ext)))
    
    return sorted(video_files)[0] if video_files else None

def get_video_dimensions(video_path):
    """Get video dimensions using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            video_path
        ], stdout=subprocess.PIPE, text=True)
        
        data = json.loads(result.stdout)
        width = data['streams'][0]['width']
        height = data['streams'][0]['height']
        
        return width, height
    except Exception as e:
        print(f"❌ Erreur lecture dimensions : {e}")
        return None, None

def parse_value(value_str, dimension):
    """
    Parse une valeur qui peut être:
    - Un nombre de pixels: "200"
    - Un pourcentage: "10%"
    """
    if isinstance(value_str, int):
        return value_str
    
    value_str = str(value_str).strip()
    
    if value_str.endswith('%'):
        # Pourcentage
        percent = float(value_str[:-1])
        return int(dimension * (percent / 100))
    else:
        # Pixels
        return int(value_str)

def draw_crop_preview(src_width, src_height, top, bottom, left, right):
    """Display ASCII art preview of the crop."""
    
    # Calculate final dimensions
    final_width = src_width - left - right
    final_height = src_height - top - bottom
    
    print("\n" + "="*70)
    print("📐 APERÇU DU CROP")
    print("="*70)
    print(f"Vidéo source    : {src_width}x{src_height}")
    print(f"Vidéo finale    : {final_width}x{final_height}")
    print()
    print(f"✂️  Enlever du HAUT   : {top}px")
    print(f"✂️  Enlever du BAS    : {bottom}px")
    print(f"✂️  Enlever de GAUCHE : {left}px")
    print(f"✂️  Enlever de DROITE : {right}px")
    print("="*70)
    
    # ASCII representation
    scale = 50 / src_width  # Scale to fit 50 chars
    
    print()
    print("┌" + "─" * int(src_width * scale) + "┐")
    
    # Top area (removed)
    top_lines = max(1, int(top * scale * (src_height / src_width)))
    if top > 0:
        for _ in range(top_lines):
            print("│" + "░" * int(src_width * scale) + "│  ← SUPPRIMÉ (haut)")
    
    # Middle area (kept)
    kept_height_lines = max(1, int(final_height * scale * (src_height / src_width)))
    for _ in range(kept_height_lines):
        left_removed = "░" * int(left * scale)
        kept = "█" * int(final_width * scale)
        right_removed = "░" * int(right * scale)
        
        line = "│" + left_removed + kept + right_removed + "│"
        
        # Add labels
        if _ == 0:
            line += "  ← CONSERVÉ"
        elif left > 0 and _ == kept_height_lines // 2:
            line += f"  ↑ SUPPRIMÉ (gauche: {left}px)"
        elif right > 0 and _ == kept_height_lines // 2:
            line += f"  ↑ SUPPRIMÉ (droite: {right}px)"
        
        print(line)
    
    # Bottom area (removed)
    bottom_lines = max(1, int(bottom * scale * (src_height / src_width)))
    if bottom > 0:
        for _ in range(bottom_lines):
            print("│" + "░" * int(src_width * scale) + "│  ← SUPPRIMÉ (bas)")
    
    print("└" + "─" * int(src_width * scale) + "┘")
    print()
    print("█ = Zone CONSERVÉE")
    print("░ = Zone SUPPRIMÉE (logos, visages, watermarks, etc.)")
    print("="*70 + "\n")

def crop_video(video_file, top, bottom, left, right, output_file, use_gpu=True):
    """
    Crop video by removing specified amounts from each side.
    
    FFmpeg crop syntax: crop=out_w:out_h:x:y
    - out_w = width - left - right
    - out_h = height - top - bottom
    - x = left (offset from left edge)
    - y = top (offset from top edge)
    """
    
    # Get source dimensions
    src_width, src_height = get_video_dimensions(video_file)
    
    # Calculate final dimensions
    final_width = src_width - left - right
    final_height = src_height - top - bottom
    
    # Crop filter
    crop_filter = f"crop={final_width}:{final_height}:{left}:{top}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", crop_filter,
    ]
    
    # GPU encoding if available - QUALITÉ MAXIMALE
    if use_gpu:
        print("🚀 Encodage GPU avec qualité maximale (preset p7, cq 19)...")
        cmd.extend([
            "-c:v", "h264_nvenc",
            "-preset", "p7",           # P7 = Preset le plus lent/meilleur qualité
            "-tune", "hq",             # High Quality tune
            "-rc", "vbr",              # Variable bitrate
            "-cq", "19",               # Constant Quality (19 = très haute qualité, 0-51)
            "-b:v", "0",               # Pas de limite avec CQ
            "-maxrate", "20M",         # Bitrate max sécurité
            "-bufsize", "40M",         # Buffer
            "-profile:v", "high",      # Profil H.264 high
            "-spatial-aq", "1",        # Adaptive quantization spatiale
            "-temporal-aq", "1",       # Adaptive quantization temporelle
        ])
    else:
        print("💻 Encodage CPU avec qualité maximale (preset veryslow, crf 18)...")
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryslow",     # Le plus lent = meilleure qualité
            "-crf", "18",              # CRF 18 = quasi transparent
            "-profile:v", "high",
        ])
    
    cmd.extend([
        "-c:a", "aac",               # Audio haute qualité
        "-b:a", "256k",              # 256kbps audio
        "-ar", "48000",              # 48kHz
        "-pix_fmt", "yuv420p",
        output_file
    ])
    
    print("🎬 Commande FFmpeg:")
    print(" ".join(cmd))
    print()
    
    start = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"❌ Erreur: {result.stderr}")
        return False
    
    print(f"✅ Terminé en {elapsed:.1f} secondes!")
    return True

def main():
    import sys
    
    if len(sys.argv) < 5:
        print("="*70)
        print("🎬 FLEXIBLE VIDEO CROPPER")
        print("="*70)
        print()
        print("Usage: python flexible_cropper.py TOP BOTTOM LEFT RIGHT")
        print()
        print("Les valeurs peuvent être:")
        print("  - En pixels: 200")
        print("  - En pourcentage: 10%")
        print()
        print("="*70)
        print("📚 EXEMPLES")
        print("="*70)
        print()
        print("1️⃣  Enlever logo en HAUT à DROITE (200px haut, 300px droite):")
        print("   python flexible_cropper.py 200 0 0 300")
        print()
        print("2️⃣  Enlever bannière en BAS (150px):")
        print("   python flexible_cropper.py 0 150 0 0")
        print()
        print("3️⃣  Enlever watermark en BAS à GAUCHE (100px bas, 250px gauche):")
        print("   python flexible_cropper.py 0 100 250 0")
        print()
        print("4️⃣  Enlever logo GAUCHE ET bannière BAS:")
        print("   python flexible_cropper.py 0 120 280 0")
        print()
        print("5️⃣  Centrer la vidéo (enlever 10% de chaque côté):")
        print("   python flexible_cropper.py 10% 10% 10% 10%")
        print()
        print("6️⃣  Cacher visage en HAUT à GAUCHE:")
        print("   python flexible_cropper.py 300 0 400 0")
        print()
        print("7️⃣  Format portrait (enlever côtés pour 9:16):")
        print("   python flexible_cropper.py 0 0 20% 20%")
        print()
        print("="*70)
        print()
        print("💡 ASTUCE: Utilise crop_helper.py d'abord pour voir ta vidéo")
        print("           et trouver les bonnes valeurs !")
        print()
        return
    
    top_str = sys.argv[1]
    bottom_str = sys.argv[2]
    left_str = sys.argv[3]
    right_str = sys.argv[4]
    
    # Get video file
    video_file = get_video_file()
    if not video_file:
        print("❌ Aucune vidéo trouvée dans working_dir_cropper/")
        return
    
    # Get video dimensions
    src_width, src_height = get_video_dimensions(video_file)
    if not src_width or not src_height:
        print("❌ Impossible de lire les dimensions de la vidéo")
        return
    
    # Show video info
    file_size = os.path.getsize(video_file) / (1024*1024)
    print(f"\n📁 Vidéo: {os.path.basename(video_file)} ({file_size:.1f} MB)")
    print(f"📐 Dimensions: {src_width}x{src_height}")
    
    # Parse crop values
    top = parse_value(top_str, src_height)
    bottom = parse_value(bottom_str, src_height)
    left = parse_value(left_str, src_width)
    right = parse_value(right_str, src_width)
    
    # Validate
    final_width = src_width - left - right
    final_height = src_height - top - bottom
    
    if final_width <= 0:
        print(f"❌ Erreur: left ({left}) + right ({right}) >= largeur ({src_width})")
        return
    
    if final_height <= 0:
        print(f"❌ Erreur: top ({top}) + bottom ({bottom}) >= hauteur ({src_height})")
        return
    
    if final_width < 100 or final_height < 100:
        print(f"⚠️  Attention: Vidéo finale très petite ({final_width}x{final_height})")
    
    # Show preview
    draw_crop_preview(src_width, src_height, top, bottom, left, right)
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("simple_cropper_output", exist_ok=True)
    output_file = f"simple_cropper_output/cropped_{final_width}x{final_height}_{timestamp}.mp4"
    
    print(f"🚀 Crop de la vidéo vers: {output_file}\n")
    
    # Do the crop
    if crop_video(video_file, top, bottom, left, right, output_file):
        output_size = os.path.getsize(output_file) / (1024*1024)
        reduction = ((file_size - output_size) / file_size * 100) if output_size < file_size else 0
        
        print(f"\n📁 Output: {output_file}")
        print(f"📊 Taille: {output_size:.1f} MB")
        if reduction > 0:
            print(f"💾 Réduction: {reduction:.1f}%")
    else:
        print("\n❌ Échec du crop")

if __name__ == "__main__":
    main()