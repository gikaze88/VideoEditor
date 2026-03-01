# 📁 Fichiers Générés - Video Generator Wave

## 🎯 Fichier Final (À Utiliser)

Quand le script termine, cherchez le fichier avec ce format :

```
podcast_wave_{nom}_{style}_{timestamp}.mp4
```

**Exemple** : `podcast_wave_Video_1_sine_20251128_113000.mp4`

✅ **C'est ce fichier que vous devez utiliser**
- Format : MP4
- Compatible avec tous les lecteurs
- Contient la vidéo finale avec la visualisation audio

## 📦 Fichiers Temporaires (Automatiquement Nettoyés)

Ces fichiers sont créés pendant le processus mais **supprimés automatiquement** :

### ~~waveform_{style}_{timestamp}.mov~~ ❌ SUPPRIMÉ
- Fichier temporaire de la visualisation audio
- Format MOV pour supporter la transparence
- **Automatiquement supprimé** après génération du fichier final

## 🗂️ Fichiers Intermédiaires (Conservés)

Ces fichiers restent dans le dossier pour le débogage :

### extracted_audio_{timestamp}.mp3
- Audio extrait de la vidéo source
- Conservé au cas où vous en auriez besoin
- Peut être supprimé manuellement si désiré

### looped_background_wave_{timestamp}.mp4
- Vidéo de fond bouclée
- Conservé pour le débogage
- Peut être supprimé manuellement si désiré

## 📊 Structure du Dossier de Sortie

```
video_generator_wave_output/
│
├── podcast_wave_Video_1_sine_20251128_113000.mp4    ← 🎯 FICHIER FINAL (À UTILISER)
│
├── extracted_audio_20251128_113000.mp3              ← Fichier intermédiaire
└── looped_background_wave_20251128_113000.mp4       ← Fichier intermédiaire
```

## ✅ Comment Identifier le Fichier Final

Le fichier final est **toujours** :

1. ✅ En format **MP4**
2. ✅ Commence par `podcast_wave_`
3. ✅ Contient le nom de votre fichier source
4. ✅ Le plus récent dans le dossier
5. ✅ Le plus gros en taille (contient tout)

## 🎬 Ouverture du Fichier Final

### Windows
```powershell
# Ouvrir le dossier de sortie
explorer video_generator_wave_output

# Chercher le fichier MP4 commençant par "podcast_wave_"
# Double-cliquez pour lire avec VLC, Windows Media Player, etc.
```

### Ligne de Commande
```powershell
# Lister les fichiers MP4 finaux
dir video_generator_wave_output\podcast_wave_*.mp4 /O:D

# Le dernier listé est le plus récent
```

## 🧹 Nettoyage Manuel (Optionnel)

Si vous voulez libérer de l'espace, vous pouvez supprimer :

```powershell
# Supprimer les fichiers audio extraits
del video_generator_wave_output\extracted_audio_*.mp3

# Supprimer les vidéos de fond bouclées
del video_generator_wave_output\looped_background_*.mp4

# Garder uniquement les fichiers finaux
del video_generator_wave_output\*.mp3
del video_generator_wave_output\looped_*.mp4
```

**Attention** : Ne supprimez PAS les fichiers `podcast_wave_*.mp4` !

## 📱 Compatibilité

Le fichier final MP4 est compatible avec :

✅ VLC Media Player
✅ Windows Media Player  
✅ QuickTime Player (Mac)
✅ Smartphones (iOS, Android)
✅ Navigateurs web
✅ Plateformes de streaming (YouTube, etc.)
✅ Éditeurs vidéo (Premiere, DaVinci, etc.)

## ❌ Problème : Je vois un fichier .mov

Si vous voyez un fichier `.mov` dans le dossier de sortie :

### Cause Possible 1 : La génération a échoué
- Le script s'est arrêté avant de créer le fichier final
- Vérifiez les messages d'erreur dans le terminal

### Cause Possible 2 : Ancienne version du script
- Le fichier .mov n'est plus créé dans la nouvelle version
- Relancez le script avec la version mise à jour

### Solution
```powershell
# Supprimer les anciens fichiers .mov
del video_generator_wave_output\*.mov

# Relancer le script
python video_generator_wave.py
```

## 💡 Astuces

### Vérifier le Fichier Généré
```powershell
# Afficher la taille et la date du fichier final
dir video_generator_wave_output\podcast_wave_*.mp4
```

### Renommer le Fichier
```powershell
# Renommer pour un nom plus simple
ren "podcast_wave_Video_1_sine_20251128_113000.mp4" "Mon_Podcast_Final.mp4"
```

### Copier vers un Autre Dossier
```powershell
# Copier le fichier final vers un autre emplacement
copy video_generator_wave_output\podcast_wave_*.mp4 "C:\Mes Vidéos\"
```

## 🎯 Résumé

| Fichier | Format | Statut | Action |
|---------|--------|--------|--------|
| `podcast_wave_*.mp4` | MP4 | **À utiliser** | ✅ C'est votre vidéo finale |
| `waveform_*.mov` | MOV | Supprimé auto | ❌ N'existe plus |
| `extracted_audio_*.mp3` | MP3 | Conservé | ⚠️ Peut être supprimé |
| `looped_background_*.mp4` | MP4 | Conservé | ⚠️ Peut être supprimé |

## ✅ Le Plus Important

**Cherchez le fichier qui commence par `podcast_wave_` et se termine par `.mp4`**

C'est votre vidéo finale, prête à être partagée ! 🎉

