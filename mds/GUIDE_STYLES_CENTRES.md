# 🎯 Guide des Styles Centrés Symétriques

## 🆕 Nouveaux Styles Ajoutés

Deux nouveaux styles **centrés symétriques** ont été ajoutés, inspirés par les waveforms modernes comme dans votre image :

### 1. `centered` - Waveform Centrée Symétrique 🌊
- **Description** : Ondes symétriques depuis une ligne centrale
- **Effet** : Effet miroir (haut et bas identiques)
- **Supporte gradients** : ✅ Oui
- **Meilleur pour** : Podcasts stylés, contenu moderne

### 2. `centered_bars` - Barres Centrées Symétriques 📊
- **Description** : Barres symétriques depuis le centre
- **Effet** : Égaliseur symétrique (haut et bas)
- **Supporte gradients** : ✅ Oui
- **Meilleur pour** : Musique, contenu énergique

## 🎨 Comment Ça Marche ?

Les styles centrés créent un **effet miroir** :

```
        ↑ Haut (copie inversée)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ← Ligne centrale
        ↓ Bas (original)
```

## 🚀 Exemples d'Utilisation

### Waveform Centrée Basique
```bash
# Blanc simple
python video_generator_wave.py centered bottom white 0.4

# Bleu subtil
python video_generator_wave.py centered center blue 0.3

# Cyan moderne
python video_generator_wave.py centered bottom 0x00CED1 0.4
```

### Barres Centrées Basique
```bash
# Orange énergique
python video_generator_wave.py centered_bars bottom orange 0.5

# Violet créatif
python video_generator_wave.py centered_bars center purple 0.4

# Vert personnalisé
python video_generator_wave.py centered_bars bottom 0,255,0 0.5
```

### Avec Gradients Multicolores 🌈

#### Waveform Centrée avec Gradient Feu
```bash
python video_generator_wave.py centered bottom fire 0.5
```
**Effet** : Rouge → Orange → Jaune en symétrie

#### Barres Centrées avec Gradient Océan
```bash
python video_generator_wave.py centered_bars center ocean 0.6
```
**Effet** : Bleu foncé → Bleu → Cyan en symétrie

#### Waveform Centrée avec Gradient Arc-en-ciel
```bash
python video_generator_wave.py centered bottom rainbow 0.4
```
**Effet** : Toutes les couleurs de l'arc-en-ciel

#### Barres Centrées avec Gradient Coucher de Soleil
```bash
python video_generator_wave.py centered_bars bottom sunset 0.5
```
**Effet** : Rose → Orange → Jaune

### Reproduire Votre Image 🎯

Pour obtenir un effet similaire à votre capture d'écran (bleu, rouge, blanc) :

```bash
# Option 1: Gradient personnalisé
python video_generator_wave.py centered center "0x0000FF|0xFF0000|0xFFFFFF" 0.5

# Option 2: Gradient prédéfini proche
python video_generator_wave.py centered center ice 0.5

# Option 3: Barres centrées colorées
python video_generator_wave.py centered_bars center "0x4A90E2|0xFF4444|0xFFFFFF" 0.6
```

## 📊 Comparaison des Styles

| Style | Symétrique | Gradient | Position | Meilleur Pour |
|-------|-----------|----------|----------|---------------|
| `sine` | ❌ | ❌ | Ligne | Podcasts simples |
| `bars` | ❌ | ❌ | Depuis bas | Égaliseur classique |
| `spectrum` | ❌ | ✅ | Depuis bas | Analyse fréquentielle |
| **`centered`** | **✅** | **✅** | **Centre** | **Waveform moderne** |
| **`centered_bars`** | **✅** | **✅** | **Centre** | **Égaliseur moderne** |

## 🎨 Tous les Gradients Disponibles

Ces gradients fonctionnent avec `centered` et `centered_bars` :

| Gradient | Couleurs | Effet | Commande |
|----------|----------|-------|----------|
| `fire` | 🔥 Rouge → Orange → Jaune | Énergique | `centered bottom fire 0.5` |
| `ocean` | 🌊 Bleu foncé → Cyan | Calme | `centered center ocean 0.4` |
| `sunset` | 🌅 Rose → Orange → Jaune | Romantique | `centered_bars bottom sunset 0.5` |
| `rainbow` | 🌈 Arc-en-ciel complet | Festif | `centered bottom rainbow 0.6` |
| `forest` | 🌲 Vert dégradé | Nature | `centered_bars center forest 0.4` |
| `purple` | 💜 Indigo → Violet | Créatif | `centered bottom purple 0.5` |
| `ice` | ❄️ Blanc → Bleu | Tech/Froid | `centered center ice 0.4` |

## 💡 Astuces d'Utilisation

### 1. Position Recommandée
```bash
# Centre (recommandé pour les styles centrés)
python video_generator_wave.py centered center blue 0.4

# Bas (aussi possible)
python video_generator_wave.py centered bottom cyan 0.3
```

### 2. Opacité Selon l'Effet
- **Subtil (0.3-0.4)** : Pour effet discret
- **Normal (0.4-0.5)** : Équilibré
- **Marqué (0.5-0.7)** : Pour attirer l'attention

### 3. Combiner avec Couleurs Personnalisées

#### RGB Format
```bash
python video_generator_wave.py centered center "255,128,0" 0.4
```

#### Hex Format
```bash
python video_generator_wave.py centered_bars bottom 0xFF8000 0.5
python video_generator_wave.py centered center "#00CED1" 0.4
```

#### Gradient Personnalisé
```bash
# Dégradé bleu → rose → jaune
python video_generator_wave.py centered center "0x0000FF|0xFF1493|0xFFFF00" 0.5
```

## 🎬 Exemples par Cas d'Usage

### Podcast Moderne
```bash
python video_generator_wave.py centered center ocean 0.3
```
**Effet** : Waveform centrée bleue/cyan très subtile

### Mix Musical Énergique
```bash
python video_generator_wave.py centered_bars center fire 0.6
```
**Effet** : Barres centrées rouge/orange/jaune dynamiques

### Contenu Tech/Gaming
```bash
python video_generator_wave.py centered center ice 0.5
```
**Effet** : Waveform centrée blanche/bleue style tech

### Interview Professionnelle
```bash
python video_generator_wave.py centered bottom blue 0.3
```
**Effet** : Waveform centrée bleue discrète

### Contenu Créatif/Artistique
```bash
python video_generator_wave.py centered_bars center rainbow 0.5
```
**Effet** : Barres centrées arc-en-ciel

## 🆚 Centered vs Non-Centered

### Style Normal (bars)
```
                 ███
             ███████
         ███████████
     ███████████████
━━━━━━━━━━━━━━━━━━━━━━━ ← Bas
```

### Style Centré (centered_bars)
```
     ███████████████  ← Haut (miroir)
         ███████████
             ███████
                 ███
━━━━━━━━━━━━━━━━━━━━━━━ ← Centre
                 ███
             ███████
         ███████████
     ███████████████  ← Bas (original)
```

## 🎯 Commandes Rapides à Essayer

```bash
# 1. Waveform centrée cyan subtile
python video_generator_wave.py centered center cyan 0.3

# 2. Barres centrées gradient feu
python video_generator_wave.py centered_bars center fire 0.5

# 3. Waveform centrée gradient océan
python video_generator_wave.py centered bottom ocean 0.4

# 4. Barres centrées arc-en-ciel
python video_generator_wave.py centered_bars center rainbow 0.6

# 5. Waveform centrée personnalisée bleu/rose
python video_generator_wave.py centered center "0x0000FF|0xFF1493" 0.5
```

## 📖 Voir Toutes les Options

```bash
python video_generator_wave.py --help
```

## ✅ Résumé

| Feature | Description | Exemple |
|---------|-------------|---------|
| **Symétrique** | Effet miroir haut/bas | Comme votre image |
| **Gradients** | Supportés | `fire`, `ocean`, `rainbow`, etc. |
| **Couleurs** | 4 formats | nom, 0x, #, RGB |
| **Position** | Tous | top, center, bottom |
| **Opacité** | Réglable | 0.0 à 1.0 |

## 🚀 Commencez Maintenant !

```bash
# La commande la plus proche de votre image
python video_generator_wave.py centered center "0x0000FF|0xFF0000|0xFFFFFF" 0.5
```

Profitez de ces nouveaux styles symétriques ! 🎨✨

