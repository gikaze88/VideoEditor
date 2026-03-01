# Video Generator with Audio Visualization (Wave)

Ce script génère des vidéos podcast avec une **visualisation audio dynamique** qui réagit en temps réel au volume et aux fréquences de l'audio.

## 🌊 Styles de Visualisation Disponibles

Le script propose **6 styles différents** sélectionnables via argument :

### 1. **sine** (Ondes Sinusoïdales) - Par défaut ✨
- Ondes classiques qui suivent l'amplitude audio
- Aspect fluide et élégant
- Idéal pour podcasts et voix

### 2. **bars** (Barres Verticales)
- Barres verticales style égaliseur
- Look moderne et dynamique
- Parfait pour contenu musical

### 3. **point** (Points)
- Visualisation en points individuels
- Aspect minimaliste
- Original et discret

### 4. **p2p** (Point à Point)
- Connexions point à point
- Effet de réseau/maillage
- Style technique et moderne

### 5. **spectrum** (Spectre de Fréquences)
- Analyse fréquentielle colorée
- Affiche graves, médiums et aigus
- Très visuel et professionnel

### 6. **volume** (Indicateur de Volume)
- Barre de volume simple
- Affiche le niveau audio instantané
- Minimaliste et clair

## 📍 Positions Disponibles

- **bottom** (bas) - Par défaut
- **center** (centre)
- **top** (haut)

## 🚀 Utilisation

### Syntaxe de Base

```bash
python video_generator_wave.py [style] [position]
```

### Exemples

```bash
# Style par défaut (sine) en bas
python video_generator_wave.py

# Barres verticales en bas
python video_generator_wave.py bars

# Ondes sinusoïdales au centre
python video_generator_wave.py sine center

# Spectre de fréquences en haut
python video_generator_wave.py spectrum top

# Indicateur de volume au centre
python video_generator_wave.py volume center
```

### Afficher l'Aide

```bash
python video_generator_wave.py --help
```

## 📂 Structure des Dossiers

```
Clip_Extractor/
├── video_generator_wave.py             # Script avec visualisation audio
├── working_dir_wave/                   # Input directory (DÉDIÉ)
│   ├── background_video.mp4           # Vidéo de fond (REQUIRED)
│   └── [your_audio_or_video_file]     # Votre podcast (REQUIRED)
└── video_generator_wave_output/       # Output directory (DÉDIÉ)
    └── podcast_wave_[name]_[style]_[timestamp].mp4
```

## 🎬 Fonctionnement

1. **Détection automatique** : Audio ou vidéo
2. **Extraction audio** : Si nécessaire
3. **Boucle vidéo de fond** : Pour correspondre à la durée audio
4. **Génération visualisation** : Crée la waveform avec le style choisi
5. **Superposition** : Combine vidéo + waveform + audio
6. **Export** : Vidéo finale avec visualisation réactive

## 📊 Comparaison avec les Autres Scripts

| Script | Caractéristique | Sortie |
|--------|----------------|--------|
| `video_generator_podcast.py` | Standard | `podcast_video_{name}_{timestamp}.mp4` |
| `video_generator_podcast_acc.py` | Audio accéléré 1.25x | `{name}_Acc.mp4` |
| **`video_generator_wave.py`** | **+ Visualisation audio** | `podcast_wave_{name}_{style}_{timestamp}.mp4` |

## 🎨 Exemples de Combinaisons

### Pour Podcasts Professionnels
```bash
python video_generator_wave.py sine bottom
```
- Ondes élégantes en bas
- Ne distrait pas du contenu

### Pour Contenu Musical
```bash
python video_generator_wave.py spectrum center
```
- Spectre coloré au centre
- Aspect professionnel

### Pour Style Minimaliste
```bash
python video_generator_wave.py volume bottom
```
- Simple barre de volume
- Discret mais informatif

### Pour Look Moderne/Technique
```bash
python video_generator_wave.py p2p center
```
- Effet de réseau au centre
- Original et captivant

## 💡 Conseils d'Utilisation

✅ **Position "bottom"** : Recommandé pour la plupart des cas
- N'interfère pas avec le contenu visuel principal
- Visible sans être intrusif

✅ **Style "sine"** : Meilleur choix pour débuter
- Fonctionne bien avec tous types d'audio
- Aspect professionnel et fluide

✅ **Style "spectrum"** : Pour contenu dynamique
- Idéal si votre audio a beaucoup de variations
- Très visuel et captivant

✅ **Style "volume"** : Pour aspect minimaliste
- Si vous voulez quelque chose de discret
- Focus sur le contenu, pas sur la visualisation

## 🔧 Configuration Avancée

Si vous voulez personnaliser davantage (couleurs, taille, etc.), vous pouvez modifier directement dans le script la section `WAVE_STYLES` :

```python
WAVE_STYLES = {
    "sine": {
        "filter": "showwaves=s=1080x200:mode=line:colors=white@0.8",
        # Modifiez: colors=red@0.8, s=1080x300, etc.
    },
}
```

### Paramètres Modifiables

- **s=WIDTHxHEIGHT** : Taille de la visualisation (ex: `1080x300`)
- **colors=COLOR@OPACITY** : Couleur et opacité (ex: `red@0.5`, `blue@0.9`)
- **mode** : Mode d'affichage (line, p2p, cline, point)

## 🎯 Workflow Complet

### Étape 1: Préparer les fichiers
```
working_dir_wave/
├── background_video.mp4     # Votre vidéo de fond
└── my_podcast.mp3           # Votre audio
```

### Étape 2: Tester différents styles
```bash
# Essayez plusieurs styles pour trouver votre préféré
python video_generator_wave.py sine
python video_generator_wave.py bars
python video_generator_wave.py spectrum
```

### Étape 3: Choisir le meilleur
Regardez les vidéos générées et choisissez celle qui correspond le mieux à votre contenu.

### Étape 4: Produire en série
Une fois le style choisi, utilisez toujours la même commande pour une cohérence visuelle.

## ❓ FAQ

**Q: La visualisation ne bouge pas beaucoup**
- R: Certains audios ont peu de dynamique. Essayez le style "spectrum" qui est plus sensible.

**Q: Puis-je changer la couleur ?**
- R: Oui, modifiez le paramètre `colors=` dans `WAVE_STYLES` du script.

**Q: La visualisation couvre trop/pas assez d'espace**
- R: Modifiez le paramètre `s=1080x200` (changez le 200 pour ajuster la hauteur).

**Q: Puis-je mettre plusieurs visualisations ?**
- R: Pas directement, mais vous pourriez modifier le script pour combiner plusieurs filtres.

## 🆚 Quand Utiliser Quel Script ?

| Besoin | Script à Utiliser |
|--------|-------------------|
| Vidéo podcast simple | `video_generator_podcast.py` |
| Gagner du temps (audio accéléré) | `video_generator_podcast_acc.py` |
| Ajouter visualisation audio | **`video_generator_wave.py`** |
| Combiner accélération + visualisation | Modifier `video_generator_wave.py` avec logique d'accélération |

## 🔥 Prochaines Améliorations Possibles

- [ ] Combiner accélération audio + visualisation
- [ ] Couleurs personnalisables via arguments
- [ ] Visualisations multiples simultanées
- [ ] Presets pré-configurés (podcast, music, voiceover, etc.)
- [ ] Mode "réactif intelligent" qui adapte le style au contenu

## ⚠️ Notes Importantes

- Ce script a son **propre dossier de travail** : `working_dir_wave/`
- Ce script a son **propre dossier de sortie** : `video_generator_wave_output/`
- Les scripts `video_generator_podcast.py` et `video_generator_podcast_acc.py` utilisent leurs propres dossiers (`working_dir_podcast/`) et ne sont **PAS modifiés**
- Tous les scripts fonctionnent **indépendamment** les uns des autres

