# 🚀 Guide de Lancement - video_generator_wave_sub.py

## 📋 Récapitulatif

Ce script génère une vidéo podcast avec :
- 🎥 Vidéo de fond bouclée
- 🌊 Visualisation audio (en bas par défaut)
- 📝 **Sous-titres générés automatiquement par Whisper** (au centre)

## ⚙️ Prérequis

### 1. Module Whisper
```bash
pip install openai-whisper
```

### 2. Dossier subs_generator
Assurez-vous que le dossier `subs_generator` existe avec le fichier `srt_generator.py`

### 3. Fichiers d'entrée
```
working_dir_wave_sub/
├── background_video.mp4
└── votre_podcast.mp4
```

## 🚀 Lancement

### Commande Simple (Défaut)
```bash
python video_generator_wave_sub.py
```
**Résultat:**
- Wave: Ondes blanches en bas (opacité 40%)
- Sous-titres: Centrés

### Avec Style Personnalisé

#### Barres centrées + sous-titres
```bash
python video_generator_wave_sub.py centered bottom cyan 0.4
```

#### Égaliseur gradient feu + sous-titres
```bash
python video_generator_wave_sub.py bars_gradient bottom fire 0.6
```

#### Arc-en-ciel + sous-titres
```bash
python video_generator_wave_sub.py rainbow center 0.6
```

## 📍 Positionnement

```
┌─────────────────────────┐
│                         │
│                         │
│    📝 SOUS-TITRES       │ ← Centre (fixe)
│       (centre)          │
│                         │
│                         │
│   🌊 WAVE VISUALIZATION │ ← Bottom (défaut)
└─────────────────────────┘
```

## 📊 Temps de Traitement

| Durée Audio | Temps Estimé |
|-------------|--------------|
| 5 minutes | ~2-3 minutes |
| 15 minutes | ~5-7 minutes |
| 30 minutes | ~10-15 minutes |
| 60 minutes | ~20-30 minutes |

La génération des sous-titres avec Whisper prend le plus de temps.

## ✅ Sortie

Fichier: `podcast_wave_sub_{nom}_{style}_{timestamp}.mp4`

Exemple: `podcast_wave_sub_mon_podcast_centered_20251129_214500.mp4`

## 💡 Exemples par Type de Contenu

### Podcast Interview
```bash
python video_generator_wave_sub.py sine bottom blue 0.3
```

### Mix Musical
```bash
python video_generator_wave_sub.py bars_gradient bottom fire 0.6
```

### Contenu Éducatif
```bash
python video_generator_wave_sub.py centered bottom green 0.4
```

### Contenu Gaming
```bash
python video_generator_wave_sub.py rainbow center 0.7
```

## 📖 Aide Complète

```bash
python video_generator_wave_sub.py --help
```

## 🎯 Prêt à Utiliser !

```bash
cd C:\Projects\Clip_Extractor
python video_generator_wave_sub.py
```

🎉 Profitez de vos vidéos avec wave + sous-titres !

