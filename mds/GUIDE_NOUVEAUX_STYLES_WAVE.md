# 🎨 Guide des Nouveaux Styles et Couleurs - Video Generator Wave

## 🆕 Nouvelles Fonctionnalités

### 1. ✅ Nouveaux Styles de Visualisation
- **spectrum_line** - Analyse fréquentielle en lignes
- **rainbow** - Arc-en-ciel automatique multicolore

### 2. ✅ Support de Multiples Formats de Couleur
- Noms prédéfinis (blue, red, etc.)
- Hex avec `0x` : `0xFF8000`
- Hex avec `#` : `#FF8000` 
- RGB : `255,128,0`

### 3. ✅ Gradients Prédéfinis
- fire, ocean, rainbow, sunset, forest, purple, ice

### 4. ✅ Support des Gradients sur Certains Styles
- spectrum, spectrum_line, rainbow supportent les gradients multicolores

## 🎨 Tous les Styles Disponibles

| Style | Description | Gradient | Meilleur Pour |
|-------|-------------|----------|---------------|
| `sine` | Ondes sinusoïdales | ❌ | Podcasts, voix |
| `bars` | Barres verticales | ❌ | Égaliseur classique |
| `point` | Points individuels | ❌ | Minimaliste |
| `p2p` | Point à point | ❌ | Look technique |
| `spectrum` | Barres fréquencielles | ✅ | Musique, gradients |
| `spectrum_line` | Lignes fréquencielles | ✅ | Waveform colorée |
| `rainbow` | Arc-en-ciel auto | ✅ | Effet multicolore |
| `volume` | Barre de volume | ❌ | Simple et clair |

## 🌈 Gradients Prédéfinis

| Gradient | Couleurs | Visuel | Usage |
|----------|----------|--------|-------|
| `fire` | Rouge → Orange → Jaune | 🔥 | Contenu énergique |
| `ocean` | Bleu foncé → Bleu → Cyan | 🌊 | Contenu calme |
| `sunset` | Rose → Orange → Jaune | 🌅 | Romantique |
| `forest` | Vert foncé → Vert → Vert clair | 🌲 | Nature |
| `rainbow` | Arc-en-ciel complet | 🌈 | Festif |
| `purple` | Indigo → Violet → Violet clair | 💜 | Créatif |
| `ice` | Blanc → Bleu ciel → Bleu | ❄️ | Froid, tech |

## 📐 Formats de Couleur

### 1. Nom Prédéfini
```bash
python video_generator_wave.py bars bottom blue
```
Couleurs: white, blue, green, purple, orange, pink, yellow, cyan, red

### 2. Hexadécimal avec 0x
```bash
python video_generator_wave.py bars bottom 0xFF8000
```
Format: `0xRRGGBB` où RR=Rouge, GG=Vert, BB=Bleu en hexadécimal

**Exemples:**
- `0xFF0000` = Rouge pur
- `0x00FF00` = Vert pur
- `0x0000FF` = Bleu pur
- `0xFF8000` = Orange
- `0xFF00FF` = Magenta

### 3. Hexadécimal avec #
```bash
python video_generator_wave.py bars bottom "#FF8000"
```
Format: `#RRGGBB` (comme en CSS/HTML)

**Exemples:**
- `#FF0000` = Rouge
- `#00CED1` = Cyan foncé
- `#9B59B6` = Violet

### 4. RGB (Rouge, Vert, Bleu)
```bash
python video_generator_wave.py bars bottom "255,128,0"
```
Format: `R,G,B` où chaque valeur est entre 0-255

**Exemples:**
- `255,0,0` = Rouge
- `0,255,0` = Vert
- `0,0,255` = Bleu
- `255,128,0` = Orange
- `128,0,128` = Violet

### 5. Gradient Prédéfini
```bash
python video_generator_wave.py spectrum bottom fire
```
Utilise un des gradients prédéfinis

## 🚀 Exemples d'Utilisation

### Style Classique avec Couleur Personnalisée

#### Orange vif (comme dans votre image)
```bash
python video_generator_wave.py bars bottom 0xFF8000 0.4
python video_generator_wave.py bars bottom 255,128,0 0.4
python video_generator_wave.py bars bottom "#FF8000" 0.4
```

#### Rose néon
```bash
python video_generator_wave.py sine bottom 0xFF1493 0.5
python video_generator_wave.py sine bottom 255,20,147 0.5
```

#### Cyan électrique
```bash
python video_generator_wave.py bars bottom 0x00FFFF 0.4
python video_generator_wave.py bars bottom 0,255,255 0.4
```

### Styles avec Gradients

#### Spectre avec gradient feu (Rouge → Orange → Jaune)
```bash
python video_generator_wave.py spectrum bottom fire 0.5
```

#### Spectre avec gradient océan (Bleu foncé → Cyan)
```bash
python video_generator_wave.py spectrum center ocean 0.6
```

#### Arc-en-ciel automatique
```bash
python video_generator_wave.py rainbow center
```

#### Spectre en lignes avec coucher de soleil
```bash
python video_generator_wave.py spectrum_line bottom sunset 0.5
```

#### Spectre violet dégradé
```bash
python video_generator_wave.py spectrum bottom purple 0.6
```

### Reproduire les Designs de vos Images

#### Image 1 - Ondes orange/rouge
```bash
python video_generator_wave.py sine bottom 0xFF4500 0.6
# ou
python video_generator_wave.py sine bottom fire 0.5
```

#### Image 2 - Barres multicolores (égaliseur)
```bash
python video_generator_wave.py rainbow bottom
# ou
python video_generator_wave.py spectrum bottom rainbow 0.6
```

#### Image 3 - Waveform rouge dense
```bash
python video_generator_wave.py bars bottom 0xFF0000 0.7
```

#### Image 4 - Waveform multicolore (bleu/rose/jaune)
```bash
python video_generator_wave.py spectrum_line bottom "0x0000FF|0xFF00FF|0xFFFF00" 0.5
```

#### Image 5 - Barres arc-en-ciel
```bash
python video_generator_wave.py spectrum bottom rainbow 0.6
```

## 🎯 Commandes Complètes Recommandées

### Pour un Podcast Professionnel
```bash
# Bleu subtil
python video_generator_wave.py sine bottom 0x4A90E2 0.3

# Cyan doux
python video_generator_wave.py bars bottom 0,206,209 0.35
```

### Pour de la Musique Énergique
```bash
# Gradient feu
python video_generator_wave.py spectrum center fire 0.6

# Orange vif
python video_generator_wave.py bars bottom 255,128,0 0.5
```

### Pour un Look Moderne/Tech
```bash
# Cyan électrique
python video_generator_wave.py spectrum_line bottom 0x00FFFF 0.4

# Gradient océan
python video_generator_wave.py spectrum bottom ocean 0.5
```

### Pour un Effet Festif/Créatif
```bash
# Arc-en-ciel automatique
python video_generator_wave.py rainbow center 0.6

# Gradient coucher de soleil
python video_generator_wave.py spectrum bottom sunset 0.5
```

## 🎨 Créer Vos Propres Couleurs

### Trouver les Valeurs RGB

1. **Online Color Picker:**
   - https://htmlcolorcodes.com/color-picker/
   - Choisissez une couleur visuellement
   - Copiez les valeurs RGB ou Hex

2. **À partir d'une image:**
   - Ouvrez l'image dans un éditeur
   - Utilisez la pipette pour sélectionner la couleur
   - Notez les valeurs RGB

### Convertir entre Formats

**RGB vers Hex:**
- RGB `255,128,0` = Hex `0xFF8000` = `#FF8000`
- Formule: Convertir chaque valeur en hex

**Hex vers RGB:**
- Hex `0xFF8000` = RGB `255,128,0`
- FF = 255, 80 = 128, 00 = 0

### Outils en Ligne
- https://www.rapidtables.com/convert/color/rgb-to-hex.html
- https://www.color-hex.com/

## 🌈 Créer des Gradients Personnalisés

Format: `couleur1|couleur2|couleur3|...`

```bash
# Gradient personnalisé bleu → vert → jaune
python video_generator_wave.py spectrum bottom "0x0000FF|0x00FF00|0xFFFF00" 0.5

# Gradient rose → violet
python video_generator_wave.py spectrum center "255,20,147|138,43,226" 0.6

# Gradient à 4 couleurs
python video_generator_wave.py spectrum bottom "0xFF0000|0xFF8000|0xFFFF00|0xFFFFFF" 0.5
```

## 💡 Astuces Pro

### 1. Choisir l'Opacité selon la Couleur
- Couleurs vives (orange, jaune, cyan) → Opacité 0.3-0.4
- Couleurs moyennes (bleu, vert, violet) → Opacité 0.4-0.5
- Couleurs sombres → Opacité 0.5-0.6
- Gradients → Opacité 0.5-0.7 (ils sont déjà variés)

### 2. Tester Plusieurs Options
```bash
# Créer test_styles.bat
@echo off
python video_generator_wave.py bars bottom 0xFF8000 0.4
python video_generator_wave.py spectrum bottom fire 0.5
python video_generator_wave.py rainbow center 0.6
echo Tests terminés!
pause
```

### 3. Matcher avec Votre Branding
Si votre logo est orange (#FF8000), utilisez:
```bash
python video_generator_wave.py bars bottom 0xFF8000 0.4
```

## 📖 Voir Toutes les Options

```bash
python video_generator_wave.py --help
```

## 🎬 Exemples Pratiques par Cas d'Usage

### Podcast Tech
```bash
python video_generator_wave.py spectrum_line bottom 0x00CED1 0.4
```

### Mix Musical
```bash
python video_generator_wave.py spectrum center fire 0.6
```

### ASMR / Méditation
```bash
python video_generator_wave.py sine bottom 0x87CEEB 0.25
```

### Contenu Gaming
```bash
python video_generator_wave.py rainbow center 0.7
```

### Interview Professionnelle
```bash
python video_generator_wave.py bars bottom 0x4A90E2 0.3
```

## 🎯 Résumé

| Feature | Avant | Maintenant |
|---------|-------|------------|
| Styles | 6 styles | **8 styles** (+ spectrum_line, rainbow) |
| Couleurs | Noms uniquement | **4 formats** (nom, 0x, #, RGB) |
| Gradients | ❌ Non | **✅ Oui** (7 prédéfinis + custom) |
| Multicolore | ❌ Non | **✅ Oui** (rainbow, gradients) |

## 🚀 Commande Rapide pour Démarrer

```bash
# Style moderne avec gradient océan
python video_generator_wave.py spectrum bottom ocean 0.5
```

Profitez de toutes ces nouvelles possibilités créatives ! 🎨✨

