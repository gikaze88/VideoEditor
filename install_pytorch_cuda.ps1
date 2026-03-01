# Script PowerShell pour installer PyTorch avec CUDA
# Compatible avec Quadro RTX 4000 (CUDA 12.1)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installation PyTorch avec support CUDA 12.1" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si PyTorch est déjà installé
Write-Host "[1/4] Verification de PyTorch existant..." -ForegroundColor Yellow
$torchInstalled = python -c "import torch; print('OK')" 2>$null

if ($torchInstalled -eq "OK") {
    Write-Host "   PyTorch detecte. Desinstallation de la version actuelle..." -ForegroundColor Yellow
    pip uninstall torch torchvision torchaudio -y
    Write-Host "   [OK] Desinstallation terminee" -ForegroundColor Green
} else {
    Write-Host "   Aucune version PyTorch detectee" -ForegroundColor Green
}

# Installer PyTorch avec CUDA 12.1
Write-Host ""
Write-Host "[2/4] Installation de PyTorch avec CUDA 12.1..." -ForegroundColor Yellow
Write-Host "   Cela peut prendre quelques minutes..." -ForegroundColor Gray

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Installation terminee" -ForegroundColor Green
} else {
    Write-Host "   [ERREUR] Echec de l'installation" -ForegroundColor Red
    exit 1
}

# Vérifier l'installation
Write-Host ""
Write-Host "[3/4] Verification de l'installation..." -ForegroundColor Yellow

$cudaCheck = python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Version:', torch.__version__); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

Write-Host $cudaCheck

# Test final
Write-Host ""
Write-Host "[4/4] Test GPU..." -ForegroundColor Yellow
$gpuTest = python -c "import torch; x = torch.randn(100, 100).cuda(); y = torch.matmul(x, x); torch.cuda.synchronize(); print('OK')" 2>$null

if ($gpuTest -eq "OK") {
    Write-Host "   [OK] Test GPU reussi !" -ForegroundColor Green
} else {
    Write-Host "   [ATTENTION] Test GPU echoue - verifiez les drivers NVIDIA" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installation terminee !" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaine etape: Relancer video_generator_wave_sub.py" -ForegroundColor Yellow
Write-Host "Whisper devrait maintenant utiliser le GPU !" -ForegroundColor Green

