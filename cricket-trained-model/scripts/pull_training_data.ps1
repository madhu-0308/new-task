# Pull user-contributed training clips from the cricket-shot backend.
#
# Usage:
#   $env:ADMIN_TOKEN = "the-secret-you-set-on-azure"
#   .\scripts\pull_training_data.ps1
#
# What it does:
#   1. Calls /api/training-stats (public) to show what's available.
#   2. Calls /api/training-archive with X-Admin-Token to download a zip
#      of every clip + contributions.jsonl into data\incoming\.
#   3. Extracts the zip into data\incoming\uploads\<class>\ for review.
#
# After pulling:
#   * Watch each clip. Delete bad ones (wrong shot, no batsman, multiple
#     people, jitter, etc.).
#   * Move the keepers into data\clips\<class>\.
#   * Run .\redeploy.ps1 to re-extract poses, retrain, redeploy.

param(
    [string]$App        = "cricket-shot-gaara",
    [string]$LocalRoot  = "F:\cricket-shot-analysis\data\incoming",
    [string]$Token      = $env:ADMIN_TOKEN,
    [switch]$ListOnly
)

$ErrorActionPreference = "Stop"
$apiBase = "https://$App.azurewebsites.net"

Write-Host ""
Write-Host "Cricket Shot — training-data review pull" -ForegroundColor Cyan
Write-Host ("-" * 60)

# --- Stats ---
try {
    $stats = Invoke-RestMethod -Uri "$apiBase/api/training-stats" -TimeoutSec 15
    Write-Host "Server reports $($stats.total) contributed clip(s):" -ForegroundColor Yellow
    if ($stats.by_class.PSObject.Properties.Count -eq 0) {
        Write-Host "  (no clips collected yet)"
    } else {
        $stats.by_class.PSObject.Properties | Sort-Object Name | ForEach-Object {
            "  {0,-12} {1,5}" -f $_.Name, $_.Value | Write-Host
        }
    }
    Write-Host "Remote storage:  $($stats.storage)"
} catch {
    Write-Host "Could not fetch /api/training-stats: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

if ($ListOnly -or $stats.total -eq 0) {
    if ($ListOnly) { Write-Host ""; Write-Host "List-only mode — not downloading." -ForegroundColor Yellow }
    exit 0
}

if (-not $Token) {
    Write-Host ""
    Write-Host "ERROR: no admin token provided." -ForegroundColor Red
    Write-Host "Set it once with:  `$env:ADMIN_TOKEN = `"your-secret-here`""
    Write-Host "Or pass:           .\scripts\pull_training_data.ps1 -Token your-secret-here"
    Write-Host ""
    Write-Host "If you haven't picked one yet, generate + apply with:" -ForegroundColor Yellow
    Write-Host "  `$token = [Guid]::NewGuid().ToString('N')"
    Write-Host "  az webapp config appsettings set --name $App --resource-group rg-cricket-shot ``"
    Write-Host "      --settings ADMIN_TOKEN=`$token --output none"
    Write-Host "  `$env:ADMIN_TOKEN = `$token"
    exit 1
}

# --- Download zip ---
New-Item -ItemType Directory -Force -Path $LocalRoot | Out-Null
$zipPath = Join-Path $LocalRoot ("archive_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".zip")
Write-Host ""
Write-Host "Downloading archive..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri "$apiBase/api/training-archive" `
        -Headers @{ "X-Admin-Token" = $Token } `
        -OutFile $zipPath -TimeoutSec 300
} catch {
    Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
$sizeKB = [math]::Round((Get-Item $zipPath).Length / 1KB, 1)
Write-Host "  Saved $zipPath ($sizeKB KB)"

# --- Extract ---
$extractDir = Join-Path $LocalRoot ("extract_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
Write-Host "  Extracted to $extractDir"

# Move clips into per-class folders directly under LocalRoot for review
$uploadsDir = Join-Path $extractDir "uploads"
if (Test-Path $uploadsDir) {
    $moved = 0
    Get-ChildItem $uploadsDir -Directory | ForEach-Object {
        $cls = $_.Name
        $target = Join-Path $LocalRoot $cls
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Get-ChildItem $_.FullName -File | ForEach-Object {
            $dest = Join-Path $target $_.Name
            if (Test-Path $dest) { return }  # already pulled in a previous run
            Move-Item $_.FullName -Destination $dest -Force
            $moved++
        }
    }
    Write-Host "  Moved $moved new clip(s) into $LocalRoot\<class>\" -ForegroundColor Green
    # Remove the extract folder (it's been drained except for empty dirs / log)
    $logSrc = Join-Path $extractDir "contributions.jsonl"
    if (Test-Path $logSrc) {
        Move-Item $logSrc (Join-Path $LocalRoot "contributions_$(Get-Date -Format yyyyMMdd_HHmmss).jsonl") -Force
    }
    Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review each clip in $LocalRoot\<class>\ ."
Write-Host "  2. Move keepers into  F:\cricket-shot-analysis\data\clips\<class>\ ."
Write-Host "  3. Run                .\redeploy.ps1   to retrain + redeploy."
