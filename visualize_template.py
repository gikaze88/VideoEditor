#!/usr/bin/env python3
"""
Template Visualizer
===================
Visualise le template NEWS DU 237 avec dimensions garanties.
"""

# Configuration du template (identique à video_generator_simple.py)
LOGO_ZONE_HEIGHT = 400
SPACING_LOGO_TO_VIDEO = 100
MINI_VIDEO_HEIGHT_PORTRAIT = 1200
MINI_VIDEO_WIDTH_PORTRAIT = 680
MARGIN_BOTTOM = 220
BORDER_WIDTH = 3
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

print("="*70)
print("📐 TEMPLATE NEWS DU 237 - DIMENSIONS GARANTIES")
print("="*70)
print()

# Vérification
total = LOGO_ZONE_HEIGHT + SPACING_LOGO_TO_VIDEO + MINI_VIDEO_HEIGHT_PORTRAIT + MARGIN_BOTTOM
print(f"Canvas total : {CANVAS_WIDTH}x{CANVAS_HEIGHT}")
print(f"Vérification : {total} == {CANVAS_HEIGHT} ✅" if total == CANVAS_HEIGHT else f"❌ ERREUR: {total} != {CANVAS_HEIGHT}")
print()

print("="*70)
print("ZONES DU TEMPLATE (de haut en bas)")
print("="*70)
print()

# Zone logo
print(f"1️⃣  ZONE LOGO (haut)")
print(f"   Hauteur : {LOGO_ZONE_HEIGHT}px")
print(f"   Usage   : Logo 'NEWS DU 237' + cercle")
print(f"   Y       : 0 → {LOGO_ZONE_HEIGHT}")
print()

# Espacement
print(f"2️⃣  ESPACEMENT (garanti)")
print(f"   Hauteur : {SPACING_LOGO_TO_VIDEO}px")
print(f"   Usage   : Séparation visuelle claire")
print(f"   Y       : {LOGO_ZONE_HEIGHT} → {LOGO_ZONE_HEIGHT + SPACING_LOGO_TO_VIDEO}")
print(f"   ✅ TOUJOURS IDENTIQUE")
print()

# Mini-vidéo
mini_video_y_start = LOGO_ZONE_HEIGHT + SPACING_LOGO_TO_VIDEO
mini_video_y_end = mini_video_y_start + MINI_VIDEO_HEIGHT_PORTRAIT
print(f"3️⃣  MINI-VIDÉO (contenu)")
print(f"   Dimensions : {MINI_VIDEO_WIDTH_PORTRAIT}x{MINI_VIDEO_HEIGHT_PORTRAIT}")
print(f"   + Bordure  : {BORDER_WIDTH}px blanche")
print(f"   Dimensions totales : {MINI_VIDEO_WIDTH_PORTRAIT + BORDER_WIDTH*2}x{MINI_VIDEO_HEIGHT_PORTRAIT + BORDER_WIDTH*2}")
print(f"   Position X : Centré horizontalement")
print(f"   Y          : {mini_video_y_start} → {mini_video_y_end}")
print(f"   ✅ TOUJOURS IDENTIQUE")
print()

# Marge bas
print(f"4️⃣  MARGE BAS")
print(f"   Hauteur : {MARGIN_BOTTOM}px")
print(f"   Usage   : Espace respiration")
print(f"   Y       : {mini_video_y_end} → {CANVAS_HEIGHT}")
print()

print("="*70)
print("VISUALISATION ASCII")
print("="*70)
print()

# Calcul échelle
scale = 40 / CANVAS_HEIGHT  # 40 lignes de haut

def draw_zone(height, char, label):
    lines = max(1, int(height * scale))
    for i in range(lines):
        if i == lines // 2:
            print(f"│ {char*36} │ {label}")
        else:
            print(f"│ {char*36} │")

print("┌" + "─"*38 + "┐")
draw_zone(LOGO_ZONE_HEIGHT, "█", f"LOGO ({LOGO_ZONE_HEIGHT}px)")
print("├" + "─"*38 + "┤")
draw_zone(SPACING_LOGO_TO_VIDEO, "░", f"ESPACE GARANTI ({SPACING_LOGO_TO_VIDEO}px) ✅")
print("├" + "─"*38 + "┤")
draw_zone(MINI_VIDEO_HEIGHT_PORTRAIT, "▓", f"MINI-VIDÉO ({MINI_VIDEO_HEIGHT_PORTRAIT}px) ✅")
print("├" + "─"*38 + "┤")
draw_zone(MARGIN_BOTTOM, " ", f"MARGE ({MARGIN_BOTTOM}px)")
print("└" + "─"*38 + "┘")

print()
print("="*70)
print("GARANTIES DU TEMPLATE")
print("="*70)
print()
print("✅ Espacement logo → mini-vidéo : TOUJOURS 100px")
print("✅ Taille mini-vidéo             : TOUJOURS 680x1200px")
print("✅ Position mini-vidéo (Y)       : TOUJOURS à 500px du haut")
print("✅ Cohérence visuelle            : TOTALE sur toutes les vidéos")
print()
print("="*70)
print("COMPARAISON AVANT/APRÈS")
print("="*70)
print()

print("AVANT (dimensions variables):")
print("  Vidéo 1 : Logo → vidéo = 420px, hauteur vidéo = 800px")
print("  Vidéo 2 : Logo → vidéo = 300px, hauteur vidéo = 950px")
print("  Vidéo 3 : Logo → vidéo = 500px, hauteur vidéo = 750px")
print("  ❌ Incohérent, pas d'identité visuelle")
print()

print("APRÈS (template fixe):")
print("  Vidéo 1 : Logo → vidéo = 100px, hauteur vidéo = 1200px ✅")
print("  Vidéo 2 : Logo → vidéo = 100px, hauteur vidéo = 1200px ✅")
print("  Vidéo 3 : Logo → vidéo = 100px, hauteur vidéo = 1200px ✅")
print("  ✅ Cohérent, identité de marque forte")
print()

print("="*70)
print("MODIFIER LE TEMPLATE")
print("="*70)
print()
print("Pour ajuster, édite video_generator_simple.py lignes 13-17:")
print()
print("LOGO_ZONE_HEIGHT = 400        # Zone logo")
print("SPACING_LOGO_TO_VIDEO = 100   # ← Espace garanti")
print("MINI_VIDEO_HEIGHT = 1200       # Hauteur vidéo")
print("MARGIN_BOTTOM = 220            # Calculé auto")
print()
print("Note: Total doit = 1920px")
print()

print("="*70)
print("EXEMPLES DE TEMPLATES ALTERNATIFS")
print("="*70)
print()

alternatives = [
    {"spacing": 150, "video": 1150, "margin": 220, "desc": "Plus d'espace, vidéo légèrement plus petite"},
    {"spacing": 80, "video": 1240, "margin": 200, "desc": "Moins d'espace, vidéo plus grande"},
    {"spacing": 100, "video": 1300, "margin": 120, "desc": "Vidéo maximale, marge minimale"},
]

for i, alt in enumerate(alternatives, 1):
    total_alt = 400 + alt["spacing"] + alt["video"] + alt["margin"]
    status = "✅" if total_alt == 1920 else "❌"
    print(f"{i}. Espace: {alt['spacing']}px | Vidéo: {alt['video']}px | Marge: {alt['margin']}px {status}")
    print(f"   {alt['desc']}")
    print()

print("="*70)