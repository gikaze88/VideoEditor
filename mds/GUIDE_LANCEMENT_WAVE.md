# 🚀 Guide de Lancement - Video Generator Wave

## 📋 Structure des Dossiers

Chaque script a maintenant **ses propres dossiers** :

```
Clip_Extractor/
├── video_generator_podcast.py          → working_dir_podcast/
├── video_generator_podcast_acc.py      → working_dir_podcast/
└── video_generator_wave.py             → working_dir_wave/      ⭐ NOUVEAU
```

## 🎯 Comment Lancer video_generator_wave.py

### **Étape 1 : Préparer les Fichiers**

Placez vos fichiers dans le dossier **`working_dir_wave/`** :

```
working_dir_wave/
├── background_video.mp4    ← Vidéo courte à boucler
└── mon_podcast.mp4         ← Votre vidéo/audio source
```

**Important** : Le script détecte automatiquement si c'est un audio ou une vidéo !

### **Étape 2 : Ouvrir le Terminal**

```powershell
cd C:\Projects\Clip_Extractor
```

### **Étape 3 : Lancer le Script**

#### ✅ Méthode Simple (style par défaut)
```bash
python video_generator_wave.py
```
- Style : Ondes sinusoïdales
- Position : En bas de la vidéo
- Parfait pour commencer !

#### 🎨 Choisir un Style Spécifique

**Barres verticales** (recommandé pour contenu musical)
```bash
python video_generator_wave.py bars
```

**Spectre de fréquences** (très visuel)
```bash
python video_generator_wave.py spectrum
```

**Indicateur de volume** (minimaliste)
```bash
python video_generator_wave.py volume
```

#### 📍 Changer la Position

**Au centre**
```bash
python video_generator_wave.py sine center
```

**En haut**
```bash
python video_generator_wave.py bars top
```

**En bas** (défaut, mais vous pouvez le spécifier)
```bash
python video_generator_wave.py spectrum bottom
```

### **Étape 4 : Récupérer le Résultat**

Le fichier généré se trouve dans : **`video_generator_wave_output/`**

Nom du fichier : `podcast_wave_{nom}_{style}_{timestamp}.mp4`

Exemple : `podcast_wave_mon_podcast_sine_20251128_113000.mp4`

## 🎬 Exemple Complet Étape par Étape

```powershell
# 1. Se placer dans le bon dossier
cd C:\Projects\Clip_Extractor

# 2. Vérifier que les fichiers sont présents
dir working_dir_wave

# Vous devriez voir :
# - background_video.mp4
# - votre_fichier_podcast.mp4 (ou .mp3)

# 3. Lancer le script avec barres verticales en bas
python video_generator_wave.py bars bottom

# 4. Attendre... (le script affiche la progression)

# 5. Vérifier le résultat
explorer video_generator_wave_output
```

## 📊 Tous les Styles Disponibles

| Commande | Style | Meilleur Pour |
|----------|-------|---------------|
| `sine` | Ondes sinusoïdales | Podcasts, voix parlée |
| `bars` | Barres verticales | Musique, contenu dynamique |
| `point` | Points | Look minimaliste |
| `p2p` | Point à point | Style technique/moderne |
| `spectrum` | Spectre coloré | Contenu musical, analyse audio |
| `volume` | Barre de volume | Simple et discret |

## 💡 Commandes Utiles

### Voir tous les styles disponibles
```bash
python video_generator_wave.py --help
```

### Lancer avec le style par défaut
```bash
python video_generator_wave.py
```

### Combinaisons Recommandées

**Pour un podcast professionnel** :
```bash
python video_generator_wave.py sine bottom
```

**Pour de la musique** :
```bash
python video_generator_wave.py spectrum center
```

**Pour un look technique** :
```bash
python video_generator_wave.py p2p center
```

**Pour un style minimaliste** :
```bash
python video_generator_wave.py volume bottom
```

## 🔧 Résolution de Problèmes

### ❌ "Fichier background_video.mp4 introuvable"
**Solution** : Vérifiez que le fichier est dans `working_dir_wave/` et qu'il s'appelle exactement `background_video.mp4`

### ❌ "Aucun fichier audio ou vidéo trouvé"
**Solution** : Placez votre fichier podcast (MP3, MP4, WAV, etc.) dans `working_dir_wave/`

### ❌ "Style 'xyz' non reconnu"
**Solution** : Utilisez un des styles valides : `sine`, `bars`, `point`, `p2p`, `spectrum`, `volume`

### ❌ "Position 'xyz' non reconnue"
**Solution** : Utilisez : `top`, `center`, ou `bottom`

## 📂 Organisation des Dossiers

```
C:\Projects\Clip_Extractor\
│
├── working_dir_podcast/              ← Pour video_generator_podcast.py
│   └── working_dir_podcast_acc.py
│
├── working_dir_wave/                 ← Pour video_generator_wave.py ⭐
│   ├── background_video.mp4
│   └── mon_podcast.mp4
│
├── video_generator_podcast_output/   ← Sorties des scripts podcast
│
└── video_generator_wave_output/      ← Sorties du script wave ⭐
    └── podcast_wave_*.mp4
```

## 🎯 Workflow Complet de A à Z

### 1️⃣ Préparation
```powershell
# Créer une copie de votre vidéo de fond dans le dossier wave
copy working_dir_podcast\background_video.mp4 working_dir_wave\

# Copier votre podcast
copy "C:\Mes Documents\podcast.mp4" working_dir_wave\
```

### 2️⃣ Test Rapide
```bash
# Tester avec le style par défaut
python video_generator_wave.py
```

### 3️⃣ Comparer les Styles
```bash
# Générer plusieurs versions
python video_generator_wave.py sine
python video_generator_wave.py bars
python video_generator_wave.py spectrum

# Comparer les résultats dans video_generator_wave_output/
```

### 4️⃣ Production Finale
```bash
# Une fois le style choisi, utiliser toujours la même commande
python video_generator_wave.py bars bottom
```

## ⚡ Raccourcis Pratiques

Créez un fichier batch `generate_wave.bat` :

```batch
@echo off
cd C:\Projects\Clip_Extractor
python video_generator_wave.py bars bottom
pause
```

Puis double-cliquez dessus pour lancer le script !

## 📝 Checklist Avant de Lancer

- [ ] Fichier `background_video.mp4` dans `working_dir_wave/`
- [ ] Fichier podcast (audio ou vidéo) dans `working_dir_wave/`
- [ ] Terminal ouvert dans `C:\Projects\Clip_Extractor`
- [ ] FFmpeg installé et accessible
- [ ] Espace disque suffisant

## 🎉 C'est Prêt !

Lancez simplement :
```bash
python video_generator_wave.py
```

Et profitez de vos vidéos avec visualisation audio dynamique ! 🌊

