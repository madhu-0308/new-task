# Interactive clip review - one shot class at a time.
#
# For each .mp4 in the source folder, opens it in your default video player
# and asks: Keep, Delete, Skip, Replay, Open-folder, Quit.
#
# Usage:
#   .\scripts\review_clips.ps1 -Class drive
#       Reviews clips in data\incoming\drive\ - Keep moves to data\clips\drive\.
#
#   .\scripts\review_clips.ps1 -Class cut -Source data\clips
#       Reviews clips ALREADY in data\clips\cut\ to weed out old bad ones.
#       Keep does nothing (file stays); Delete removes it.
#
#   .\scripts\review_clips.ps1 -Class drive -DryRun
#       Show what would happen but don't touch files.
#
# Keys during review:
#   K   keep the clip                    (move to data\clips\<class>\ )
#   D   delete the clip                  (sent to Recycle Bin, not nuked)
#   S   skip / next                      (leave it where it is)
#   R   replay (open the video again)
#   O   open the source folder in Explorer
#   Q   quit the review

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("drive", "cut", "pull_hook", "sweep", "defensive", "innovative", "glance")]
    [string]$Class,

    [string]$Source = "data\incoming",   # where the clips currently are
    [string]$Dest   = "data\clips",      # where keepers go
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repo = "F:\cricket-shot-analysis"
Set-Location $repo

$srcDir  = Join-Path $repo (Join-Path $Source $Class)
$destDir = Join-Path $repo (Join-Path $Dest $Class)

# Resolve "review-in-place" mode: when source == destination, Keep is a no-op.
$inPlace = (Resolve-Path $Source -ErrorAction SilentlyContinue).Path -eq
           (Resolve-Path $Dest   -ErrorAction SilentlyContinue).Path

if (-not (Test-Path $srcDir)) {
    Write-Host "No folder at $srcDir - nothing to review." -ForegroundColor Yellow
    exit 0
}

# Need Microsoft.VisualBasic for "send to Recycle Bin" (safer than rm).
Add-Type -AssemblyName Microsoft.VisualBasic

$clips = Get-ChildItem $srcDir -Filter *.mp4 -File | Sort-Object Name
if (-not $clips) {
    Write-Host "No .mp4 files in $srcDir." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $destDir) -and -not $inPlace -and -not $DryRun) {
    New-Item -ItemType Directory -Path $destDir | Out-Null
}

Write-Host ""
Write-Host "Cricket Shot - clip review" -ForegroundColor Cyan
Write-Host ("-" * 60)
Write-Host "Class:    $Class"
Write-Host "Source:   $srcDir   ($($clips.Count) clips)"
if ($inPlace) {
    Write-Host "Mode:     review-in-place (Keep = no-op, Delete = remove)" -ForegroundColor Yellow
} else {
    Write-Host "Keep ->   $destDir"
}
if ($DryRun) { Write-Host "DRY-RUN:  no files will be moved or deleted" -ForegroundColor Yellow }
Write-Host ""
Write-Host "Workflow:" -ForegroundColor Green
Write-Host "   - Clip loops in ffplay until you decide."
Write-Host "   - See the batsman clearly?      press  K   (keep)"
Write-Host "   - Can't see batter / wrong shot? press  D   (delete -> Recycle Bin)"
Write-Host "   - Not sure yet?                  press  S   (skip, leave it)"
Write-Host "   - Other:                         R replay  |  O open folder  |  Q quit"
Write-Host ""

$kept = $deleted = $skipped = 0
$lastProc = $null

# ---------------------------------------------------------------------
# Win32 focus helpers so the PowerShell console keeps keyboard input
# after we spawn the video window. Without this, ffplay/WMP steal focus
# and K/D/S go to the video player (which ignores them) instead of our
# Console.ReadKey loop.
# ---------------------------------------------------------------------
if (-not ("Native.FocusHelper" -as [type])) {
    Add-Type -Name FocusHelper -Namespace Native -MemberDefinition @'
        [System.Runtime.InteropServices.DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(System.IntPtr hWnd);
        [System.Runtime.InteropServices.DllImport("user32.dll")]
        public static extern bool ShowWindowAsync(System.IntPtr hWnd, int nCmdShow);
        [System.Runtime.InteropServices.DllImport("kernel32.dll")]
        public static extern System.IntPtr GetConsoleWindow();
        [System.Runtime.InteropServices.DllImport("user32.dll")]
        public static extern bool AllowSetForegroundWindow(int dwProcessId);
'@
}

$script:PsHwnd = [Native.FocusHelper]::GetConsoleWindow()
if ($script:PsHwnd -eq [System.IntPtr]::Zero) {
    # Fallback if running inside Terminal/ISE that hides the console
    $script:PsHwnd = (Get-Process -Id $PID).MainWindowHandle
}

function Focus-Ps {
    if ($script:PsHwnd -ne [System.IntPtr]::Zero) {
        # SW_RESTORE = 9 (unminimise + show)
        [Native.FocusHelper]::ShowWindowAsync($script:PsHwnd, 9) | Out-Null
        [Native.FocusHelper]::SetForegroundWindow($script:PsHwnd) | Out-Null
    }
}

# Decide ONCE up front how we'll open videos. Order of preference:
#   1. ffplay.exe (ships with ffmpeg, loops the clip so we have time)
#   2. wmplayer.exe (Windows Media Player, always installed)
#   3. shell association via "cmd /c start"  (uses default app)
$script:OpenMode = $null
$script:FfplayExe = $null

if (Get-Command ffplay.exe -ErrorAction SilentlyContinue) {
    $script:OpenMode = "ffplay"
    $script:FfplayExe = (Get-Command ffplay.exe).Source
} elseif (Test-Path "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ffplay.exe") {
    $script:OpenMode = "ffplay"
    $script:FfplayExe = "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ffplay.exe"
} elseif (Test-Path "$env:ProgramFiles\ffmpeg\bin\ffplay.exe") {
    $script:OpenMode = "ffplay"
    $script:FfplayExe = "$env:ProgramFiles\ffmpeg\bin\ffplay.exe"
} elseif (Test-Path "$env:SystemRoot\System32\wmplayer.exe") {
    $script:OpenMode = "wmplayer"
} else {
    $script:OpenMode = "shellopen"
}
Write-Host "Player:   $($script:OpenMode)$(if ($script:FfplayExe) { ' (' + $script:FfplayExe + ')' })" -ForegroundColor DarkGray

function Open-Clip($path) {
    # Returns the Process object so Close-Clip can stop it later.
    try {
        switch ($script:OpenMode) {
            "ffplay" {
                # -loop 0           = loop forever until we kill the window
                # -loglevel quiet   = no banner spam
                # -window_title     = show filename in the title bar
                # -x / -y           = a comfortable preview size; small clips
                #                     would otherwise pop up at native size.
                # We intentionally do NOT use -autoexit so a 2 s clip keeps
                # replaying until the reviewer hits K/D/S in the PS window.
                $title = [System.IO.Path]::GetFileName($path)
                return Start-Process -FilePath $script:FfplayExe `
                    -ArgumentList @(
                        '-loop', '0',
                        '-loglevel', 'quiet',
                        '-x', '640', '-y', '480',
                        '-window_title', "`"$title`"",
                        "`"$path`""
                    ) `
                    -PassThru -ErrorAction Stop
            }
            "wmplayer" {
                return Start-Process -FilePath "$env:SystemRoot\System32\wmplayer.exe" `
                    -ArgumentList "`"$path`"" -PassThru -ErrorAction Stop
            }
            default {
                # Shell open via cmd's start - uses whatever default
                # association the user has. Returns the cmd process,
                # not the player itself, so Close-Clip is a no-op here.
                return Start-Process -FilePath "cmd.exe" `
                    -ArgumentList @('/c', 'start', '""', "`"$path`"") `
                    -WindowStyle Hidden -PassThru -ErrorAction Stop
            }
        }
    } catch {
        Write-Host "  (could not launch player: $($_.Exception.Message))" -ForegroundColor Red
        return $null
    }
}
function Close-Clip($proc) {
    if ($null -ne $proc -and -not $proc.HasExited) {
        try { $proc.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 200 } catch {}
        try { if (-not $proc.HasExited) { $proc | Stop-Process -Force } } catch {}
    }
    # For shellopen mode we can't track the real player. Best-effort: kill
    # any stray ffplay/wmplayer windows so they don't pile up.
    if ($script:OpenMode -eq "ffplay") {
        Get-Process ffplay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

for ($i = 0; $i -lt $clips.Count; $i++) {
    $clip = $clips[$i]
    $sizeKB = [math]::Round($clip.Length / 1KB, 1)
    Write-Host ("[{0,3}/{1,3}] {2}   ({3} KB)" -f ($i + 1), $clips.Count, $clip.Name, $sizeKB) -ForegroundColor White

    Close-Clip $lastProc
    $lastProc = Open-Clip $clip.FullName
    # Give the video window ~250 ms to draw, then yank focus back to
    # the PS console so the next keypress lands in ReadKey() below.
    Start-Sleep -Milliseconds 250
    Focus-Ps

    $decided = $false
    while (-not $decided) {
        $key = [Console]::ReadKey($true).Key
        switch ($key) {
            'K' {
                if ($inPlace) {
                    Write-Host "  kept (already in $destDir)" -ForegroundColor Green
                } elseif ($DryRun) {
                    Write-Host "  [dry-run] would move -> $destDir\$($clip.Name)" -ForegroundColor Green
                } else {
                    $target = Join-Path $destDir $clip.Name
                    if (Test-Path $target) {
                        Write-Host "  duplicate already in dest - leaving source, NOT moving" -ForegroundColor Yellow
                    } else {
                        Move-Item $clip.FullName -Destination $target -Force
                        Write-Host "  kept -> $target" -ForegroundColor Green
                    }
                }
                $kept++
                $decided = $true
            }
            'D' {
                if ($DryRun) {
                    Write-Host "  [dry-run] would delete $($clip.FullName)" -ForegroundColor Red
                } else {
                    Close-Clip $lastProc; $lastProc = $null
                    [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                        $clip.FullName,
                        [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                        [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
                    )
                    Write-Host "  deleted (Recycle Bin)" -ForegroundColor Red
                }
                $deleted++
                $decided = $true
            }
            'S' {
                Write-Host "  skipped" -ForegroundColor DarkGray
                $skipped++
                $decided = $true
            }
            'R' {
                Close-Clip $lastProc
                $lastProc = Open-Clip $clip.FullName
                Start-Sleep -Milliseconds 250
                Focus-Ps
                Write-Host "  replaying..." -ForegroundColor DarkGray
            }
            'O' {
                Start-Process explorer.exe $srcDir
                Write-Host "  opened folder - back to clip..." -ForegroundColor DarkGray
            }
            'Q' {
                Write-Host ""
                Write-Host "  Quitting review." -ForegroundColor Yellow
                Close-Clip $lastProc
                Write-Host ""
                Write-Host ("Summary:  kept {0}   deleted {1}   skipped {2}" -f $kept, $deleted, $skipped) -ForegroundColor Cyan
                exit 0
            }
            default {
                Write-Host "  Use K / D / S / R / O / Q" -ForegroundColor DarkGray
            }
        }
    }
}

Close-Clip $lastProc

Write-Host ""
Write-Host "Done with class '$Class'." -ForegroundColor Cyan
Write-Host ("Summary:  kept {0}   deleted {1}   skipped {2}" -f $kept, $deleted, $skipped)
if (-not $inPlace -and -not $DryRun -and $kept -gt 0) {
    Write-Host ""
    Write-Host "Next:" -ForegroundColor Yellow
    Write-Host "  Repeat for the next class:   .\scripts\review_clips.ps1 -Class cut"
    Write-Host "  Or retrain + redeploy now:   .\redeploy.ps1"
}
