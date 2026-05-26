# Cricket Shot Classifier - full retrain + redeploy pipeline.
#
# Runs every step from "I cleaned some data" to "Azure is serving the new model":
#   1. Sync orphan poses (where you deleted clips but .npy files remain)
#   2. Regenerate train/val/test splits
#   3. Train a new model
#   4. Copy best.pt to the HF Space deploy folder
#   5. Build & push a new Docker image to Azure Container Registry
#   6. Point the Azure Web App at the new image
#   7. Restart the Web App
#   8. Wait until /healthz says the model is loaded
#
# Usage:
#   .\redeploy.ps1                          # auto-detects next exp/tag, runs everything
#   .\redeploy.ps1 -Epochs 200              # longer training
#   .\redeploy.ps1 -SkipTraining            # skip retraining, just redeploy current model
#   .\redeploy.ps1 -SkipDeploy              # train only, don't push to Azure
#   .\redeploy.ps1 -Exp exp7 -Tag v7        # override auto-detection

param(
    [string]$Exp = "",
    [string]$Tag = "",
    [int]$Epochs = 150,
    [switch]$SkipTraining,
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"
$REPO = "F:\cricket-shot-analysis"
$HF_DIR = "F:\hf-space-cricket"
$RG = "rg-cricket-shot"
$ACR = "cricketshotgaaraai"
$APP = "cricket-shot-gaara"
$URL = "https://cricket-shot-gaara.azurewebsites.net"

Set-Location $REPO

function Step($n, $title) {
    Write-Host ""
    Write-Host "[$n] $title" -ForegroundColor Cyan
    Write-Host ("-" * 60)
}

# --- Auto-detect Exp name (next available exp{N}) --------------------------
if (-not $Exp) {
    $existing = Get-ChildItem "runs" -Directory -ErrorAction SilentlyContinue `
        | Where-Object { $_.Name -match '^exp(\d+)$' } `
        | ForEach-Object { [int]$matches[1] }
    $next = if ($existing) { ($existing | Measure-Object -Maximum).Maximum + 1 } else { 1 }
    $Exp = "exp$next"
}
if (-not $Tag) { $Tag = "v$($Exp -replace '^exp','')" }
Write-Host ""
Write-Host "Run config: Exp=$Exp  Tag=$Tag  Epochs=$Epochs" -ForegroundColor Yellow

# --- 1. Sync orphan poses ---------------------------------------------------
Step 1 "Syncing pose files to current clips (archive orphans)"
$archive = "data\poses\_orphan_archive\$Exp"
New-Item -ItemType Directory -Force -Path $archive | Out-Null
$totalMoved = 0
Get-ChildItem "data\poses" -Directory | Where-Object { $_.Name -notmatch "^_" } | ForEach-Object {
    $cls = $_.Name
    $clipsDir = "data\clips\$cls"
    if (-not (Test-Path $clipsDir)) { return }
    $clipStems = @{}
    Get-ChildItem $clipsDir -Filter *.mp4 -ErrorAction SilentlyContinue `
        | ForEach-Object { $clipStems[$_.BaseName] = $true }
    $orphans = Get-ChildItem $_.FullName -Filter *.npy `
        | Where-Object { -not $clipStems.ContainsKey($_.BaseName) }
    if ($orphans.Count -gt 0) {
        $dst = "$archive\$cls"
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        $orphans | ForEach-Object { Move-Item $_.FullName -Destination $dst -Force }
        Write-Host ("  {0,-12}: archived {1} orphan poses" -f $cls, $orphans.Count)
        $script:totalMoved += $orphans.Count
    }
}
if ($totalMoved -eq 0) { Write-Host "  All in sync." }
else { Write-Host "  Total archived: $totalMoved (recoverable from $archive)" }

# --- 2. Regenerate splits ---------------------------------------------------
Step 2 "Regenerating train/val/test splits"
& .\.venv\Scripts\Activate.ps1
python scripts\make_splits.py
if ($LASTEXITCODE -ne 0) { throw "make_splits.py failed" }

# --- 3. Train ---------------------------------------------------------------
if ($SkipTraining) {
    Write-Host ""
    Write-Host "[3] SKIPPED training (--SkipTraining)" -ForegroundColor Yellow
} else {
    Step 3 "Training $Exp ($Epochs epochs)"
    python src\train.py --exp $Exp --epochs $Epochs
    if ($LASTEXITCODE -ne 0) { throw "train.py failed" }
}

# --- 4. Copy best.pt to HF Space deploy folder ------------------------------
Step 4 "Copying $Exp\best.pt to HF Space dir"
$src = "runs\$Exp\best.pt"
$dst = "$HF_DIR\shot_classifier\weights\best.pt"
if (-not (Test-Path $src)) { throw "best.pt not found at $src - training may have failed" }
Copy-Item $src $dst -Force
$size = [math]::Round((Get-Item $dst).Length / 1KB, 1)
Write-Host "  Copied ($size KB) -> $dst"

if ($SkipDeploy) {
    Write-Host ""
    Write-Host "[5-8] SKIPPED deploy (--SkipDeploy). Model is at $dst" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Done. To deploy later, re-run without --SkipDeploy." -ForegroundColor Green
    exit 0
}

# --- 5. Build & push Docker image -------------------------------------------
Step 5 "Building image $Tag in Azure Container Registry (5-7 min)"
az acr build --registry $ACR --image "cricket-shot:$Tag" $HF_DIR
if ($LASTEXITCODE -ne 0) { throw "az acr build failed" }

# --- 6. Point Web App at new image ------------------------------------------
Step 6 "Pointing Web App at cricket-shot:$Tag"
az webapp config container set `
    --name $APP `
    --resource-group $RG `
    --container-image-name "$ACR.azurecr.io/cricket-shot:$Tag" `
    --output none
if ($LASTEXITCODE -ne 0) { throw "az webapp config container set failed" }

# --- 7. Restart -------------------------------------------------------------
Step 7 "Restarting Web App"
az webapp restart --name $APP --resource-group $RG --output none
if ($LASTEXITCODE -ne 0) { throw "az webapp restart failed" }

# --- 8. Wait for healthy ----------------------------------------------------
Step 8 "Waiting for model load (~30-90s)"
$start = Get-Date
$timeoutMin = 5
while ($true) {
    try {
        $r = Invoke-RestMethod -Uri "$URL/healthz" -TimeoutSec 5
        if ($r.model_ready) {
            $elapsed = [int]((Get-Date) - $start).TotalSeconds
            Write-Host ""
            Write-Host "  DEPLOYED" -ForegroundColor Green
            Write-Host "  Model load:    $($r.model_load_seconds)s"
            Write-Host "  Deploy total:  ${elapsed}s"
            Write-Host "  Backend URL:   $URL"
            Write-Host "  Test on:       https://cric2-fawn.vercel.app/shot-analysis"
            Write-Host ""
            break
        }
        Write-Host "  warming up..."
    } catch {
        Write-Host "  waiting for container..."
    }
    if (((Get-Date) - $start).TotalMinutes -gt $timeoutMin) {
        throw "Timed out after $timeoutMin min waiting for /healthz to report model_ready"
    }
    Start-Sleep -Seconds 10
}
