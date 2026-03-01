# 🌍 Configuration de l'environnement - Clip Extractor

Ce guide explique comment configurer correctement l'environnement Python pour tous les scripts du projet, notamment pour `srt_generator.py` qui utilise Whisper.

---

## ✅ Prérequis système

1. **Python 3.8+** (recommandé: 3.10 ou 3.11)
2. **FFmpeg** installé et dans le PATH
3. **GPU NVIDIA avec CUDA** (optionnel mais recommandé pour Whisper)

---

## 🚀 Installation rapide (Environnement virtuel)

### Étape 1 : Créer l'environnement virtuel

```powershell
# Dans le dossier C:\Projects\Clip_Extractor
python -m venv venv
```

### Étape 2 : Activer l'environnement

**PowerShell (Windows):**
```powershell
.\venv\Scripts\Activate.ps1
```

**CMD (Windows):**
```cmd
venv\Scripts\activate.bat
```

**Bash/Linux/Mac:**
```bash
source venv/bin/activate
```

### Étape 3 : Installer les dépendances

#### Option A - CPU uniquement (plus simple)
```powershell
pip install -r requirements.txt
```

#### Option B - GPU avec CUDA (recommandé pour RTX 4000)
```powershell
# CUDA 11.8 (compatible RTX 4000)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install openai-whisper
```

---

## 🐍 Alternative avec Conda

Si tu préfères Conda/Miniconda:

```bash
# 1. Créer l'environnement
conda create -n clip_extractor python=3.10

# 2. Activer
conda activate clip_extractor

# 3. Installer PyTorch avec CUDA
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# 4. Installer Whisper
pip install openai-whisper
```

---

## ✅ Vérification de l'installation

### Test 1 : Vérifier Python et les imports
```powershell
python -c "import whisper; import torch; print('✅ Whisper OK')"
```

### Test 2 : Vérifier le GPU CUDA
```powershell
python -c "import torch; print(f'GPU CUDA disponible: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

**Résultat attendu avec GPU:**
```
GPU CUDA disponible: True
GPU: Quadro RTX 4000
```

### Test 3 : Tester srt_generator
```powershell
cd subs_generator
python srt_generator.py --help
```

---

## 📦 Dépendances principales

| Package | Version | Utilisation |
|---------|---------|-------------|
| `openai-whisper` | ≥20231117 | Transcription audio → texte (SRT) |
| `torch` | ≥2.0.0 | Framework PyTorch pour Whisper |
| `torchvision` | ≥0.15.0 | Utilitaires PyTorch |
| `torchaudio` | ≥2.0.0 | Traitement audio PyTorch |

---

## 🎮 Optimisations GPU (Quadro RTX 4000)

Le script `srt_generator.py` est optimisé pour ton GPU RTX 4000 avec:

- ✅ **Modèle Whisper "medium"** (balance vitesse/qualité)
- ✅ **Détection automatique CUDA** 
- ✅ **Fallback CPU** si GPU indisponible
- ✅ **Gestion mémoire optimisée** (~1.5 GB VRAM)

### Vérifier les performances GPU

```python
import torch
print(f"CUDA: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
print(f"VRAM totale: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
```

---

## 🔧 Désactiver l'environnement

Quand tu as terminé:

```powershell
deactivate
```

---

## 🆘 Résolution de problèmes

### Erreur: "CUDA not available"

1. Vérifier les drivers NVIDIA à jour
2. Réinstaller PyTorch avec CUDA:
   ```powershell
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### Erreur: "No module named 'whisper'"

```powershell
pip install openai-whisper
```

### Erreur: FFmpeg not found

Vérifier que FFmpeg est dans le PATH:
```powershell
ffmpeg -version
```

Si absent, télécharger depuis: https://ffmpeg.org/download.html

---

## 📁 Structure du projet avec environnement

```
C:\Projects\Clip_Extractor\
├── venv/                          # 🌍 Environnement virtuel
├── subs_generator/
│   └── srt_generator.py           # Script Whisper
├── video_generator_wave.py
├── video_generator_wave_acc.py
├── video_generator_wave_sub.py
├── requirements.txt               # 📦 Dépendances
└── SETUP_ENVIRONMENT.md           # 📖 Ce guide
```

---

## 💡 Conseils

1. **Toujours activer l'environnement** avant d'exécuter les scripts
2. **Vérifier CUDA** si tu as un GPU pour des performances optimales
3. **Mettre à jour régulièrement**: `pip install --upgrade openai-whisper torch`

---

✅ Une fois l'environnement configuré, tu peux exécuter:
- `python video_generator_wave.py`
- `python video_generator_wave_acc.py`
- `python video_generator_wave_sub.py` (avec Whisper)

