# 🎬 Guide - Video Generator Wave avec Sous-titres

## 🆕 Nouveau Script : video_generator_wave_sub.py

Ce script combine **3 fonctionnalités** :
1. 🎥 Vidéo de fond bouclée
2. 🌊 Visualisation audio (en bas)
3. 📝 Sous-titres générés par Whisper (au centre)

## 📂 Structure

```
Clip_Extractor/
├── video_generator_wave_sub.py           # Script avec wave + sous-titres
├── working_dir_wave_sub/                 # Input directory (DÉDIÉ)
│   ├── background_video.mp4             # Vidéo de fond (REQUIRED)
│   └── [your_audio_or_video_file]       # Podcast (REQUIRED)
├── video_generator_wave_sub_output/     # Output directory (DÉDIÉ)
│   └── podcast_wave_sub_*.mp4
└── subs_generator/                       # Module Whisper (REQUIRED)
    └── srt_generator.py
```

## ⚙️ Prérequis

1. ✅ Python 3.x
2. ✅ FFmpeg installé
3. ✅ **Module `subs_generator` avec `srt_generator.py`** (pour Whisper)
4. ✅ Whisper installé (`pip install openai-whisper`)

## 🚀 Utilisation

### Étape 1: Préparer les Fichiers

Placez dans `working_dir_wave_sub/` :
```
working_dir_wave_sub/
├── background_video.mp4     # Vidéo de fond
└── mon_podcast.mp4           # Votre audio/vidéo
```

### Étape 2: Lancer le Script

#### Style par Défaut
```bash
python video_generator_wave_sub.py
```
- Visualisation: Ondes sinusoïdales blanches (bas)
- Sous-titres: Centre

#### Avec Style Personnalisé
```bash
# Barres centrées cyan + sous-titres
python video_generator_wave_sub.py centered bottom cyan 0.4

# Barres gradient feu + sous-titres
python video_generator_wave_sub.py bars_gradient bottom fire 0.6

# Arc-en-ciel + sous-titres
python video_generator_wave_sub.py rainbow center 0.6
```

### Étape 3: Récupérer le Résultat

Fichier généré: `video_generator_wave_sub_output/podcast_wave_sub_{nom}_{style}_{timestamp}.mp4`

## 🎨 Tous les Styles Disponibles

Les **11 styles** de `video_generator_wave.py` sont disponibles :

```bash
sine, bars, point, p2p, spectrum, spectrum_line, 
rainbow, centered, centered_bars, bars_gradient, volume
```

## 📝 Positionnement

| Élément | Position | Description |
|---------|----------|-------------|
| **Visualisation audio** | `bottom` (défaut) | En bas de la vidéo |
| **Sous-titres** | `center` (fixe) | Au centre de la vidéo |

## 💡 Exemples Complets

### Podcast Professionnel
```bash
python video_generator_wave_sub.py centered bottom cyan 0.3
```
- Barres centrées cyan subtiles en bas
- Sous-titres au centre

### Mix Musical
```bash
python video_generator_wave_sub.py bars_gradient bottom fire 0.6
```
- Égaliseur gradient feu en bas
- Sous-titres au centre

### Contenu Gaming
```bash
python video_generator_wave_sub.py rainbow center 0.7
```
- Arc-en-ciel au centre (autour des sous-titres)
- Sous-titres au centre

### Interview Professionnelle
```bash
python video_generator_wave_sub.py sine bottom blue 0.35
```
- Ondes bleues discrètes en bas
- Sous-titres au centre

## 🔄 Pipeline Complet

1. 📂 Détection des fichiers
2. 🎵 Extraction audio (si vidéo)
3. 🔁 Boucle de la vidéo de fond
4. 🌊 Génération de la visualisation audio
5. 📝 **Génération des sous-titres avec Whisper** (NOUVEAU)
6. 🎬 Superposition: Vidéo + Wave + Sous-titres + Audio
7. ✅ Export MP4 compatible

## 📊 Comparaison des Scripts

| Script | Features | Output |
|--------|----------|--------|
| `video_generator_podcast.py` | Vidéo + Audio | Standard |
| `video_generator_podcast_acc.py` | Vidéo + Audio accéléré | Accéléré |
| `video_generator_wave.py` | Vidéo + Audio + Wave | Avec wave |
| **`video_generator_wave_sub.py`** | **Vidéo + Audio + Wave + Sous-titres** | **Complet** |

## ⚠️ Notes Importantes

### Si les Sous-titres ne sont Pas Générés
Le script continue sans sous-titres et produit une vidéo avec juste la visualisation audio (comme `video_generator_wave.py`).

### Temps de Génération
- Vidéo de 30 min : ~5-10 minutes (selon Whisper)
- La génération des sous-titres prend le plus de temps

### Format des Sous-titres
- Style: Montserrat (si disponible, sinon police par défaut)
- Taille: 18
- Couleur: Blanc avec contour noir
- Position: Centrés verticalement (milieu de la vidéo)

## 🎯 Cas d'Usage Idéaux

### ✅ Utilisez ce Script Pour:
- Podcasts avec transcription
- Interviews nécessitant des sous-titres
- Contenu éducatif
- Contenu multilingue
- Accessibilité (malentendants)

### ❌ Utilisez les Autres Scripts Pour:
- Simple visualisation audio → `video_generator_wave.py`
- Vidéo rapide sans sous-titres → `video_generator_podcast.py`
- Contenu accéléré → `video_generator_podcast_acc.py`

## 📖 Syntaxe Complète

```bash
python video_generator_wave_sub.py [style] [position] [couleur] [opacité]
```

**Exemples:**
```bash
python video_generator_wave_sub.py
python video_generator_wave_sub.py centered bottom cyan 0.4
python video_generator_wave_sub.py bars_gradient bottom fire 0.6
python video_generator_wave_sub.py spectrum center ocean 0.5
```

## 🔍 Vérifier que tout Fonctionne

```bash
# 1. Vérifier que subs_generator existe
dir subs_generator

# 2. Vérifier Whisper
pip list | findstr whisper

# 3. Lancer le script
python video_generator_wave_sub.py
```

## ✅ Résultat Final

Vous obtenez une vidéo MP4 avec :
- 🎥 Vidéo de fond bouclée
- 🌊 Visualisation audio dynamique (bas)
- 📝 Sous-titres synchronisés (centre)
- 🎵 Audio synchronisé

**C'est le package complet pour vos podcasts vidéo !** 🎉

