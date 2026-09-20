# install-video-use.ps1 - OPTIONAL: install browser-use/video-use into the video station.
#
# You do NOT need this to edit footage: `video-studio edit` ships its own distilled helpers
# (see video_studio/edit/, NOTICE). Install this only when you want the upstream tree itself -
# to follow upstream changes, or to use its cloud ASR path (speaker diarization, filler words).
#
# What it does: clone (or fast-forward) upstream into <station>/video-use, create a venv next
# to it, install its dependencies, and tell `video-studio init` to record it in station.json.
# Idempotent: running it again pulls and re-checks the venv; it never deletes your work.
#
# ASCII-only on purpose: a .ps1 saved as UTF-8 without a BOM is parsed as the system code page
# by Windows PowerShell 5.1 and non-ASCII comments become parse errors.
#
# Requires: git, python 3.10+, ffmpeg on PATH.
# Usage: pwsh -File scripts/install-video-use.ps1 [-Station <dir>]
param(
    [string]$Station
)
$ErrorActionPreference = 'Stop'

if (-not $Station) { $Station = $env:VIDEO_STATION }
if (-not $Station) { $Station = $env:VIDEO_ROOT }
if (-not $Station) { $Station = Join-Path $HOME '.video' }
$Dest = Join-Path $Station 'video-use'

function Find-Python {
    # Prove each candidate by running it: on Windows `python3` is often the Microsoft Store
    # stub, which sits on PATH and fails on every real call.
    $names = @($env:VIDEO_STUDIO_PY, 'python', 'python3', 'py') | Where-Object { $_ }
    foreach ($name in $names) {
        $c = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $c) { continue }
        & $c.Source -c 'import sys; assert sys.version_info[:2] >= (3, 10)' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return $c.Source }
    }
    throw 'No usable Python 3.10+ found. Install one, or set VIDEO_STUDIO_PY.'
}

foreach ($tool in 'git', 'ffmpeg') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Missing '$tool' on PATH - install it first."
    }
}
$py = Find-Python

if (Test-Path (Join-Path $Dest '.git')) {
    Write-Host "[git] fast-forward $Dest"
    git -C $Dest pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw 'git pull --ff-only failed - resolve it by hand (nothing was deleted).' }
}
else {
    New-Item -ItemType Directory -Force (Split-Path -Parent $Dest) | Out-Null
    git clone --depth 1 https://github.com/browser-use/video-use.git $Dest
    if ($LASTEXITCODE -ne 0) { throw 'git clone failed.' }
}

$venv = Join-Path $Dest '.venv'
if ($env:OS -eq 'Windows_NT') { $venvPy = Join-Path $venv 'Scripts/python.exe' }
else { $venvPy = Join-Path $venv 'bin/python' }
if (-not (Test-Path $venvPy)) {
    Write-Host '[venv] creating'
    & $py -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'venv creation failed.' }
}

Write-Host '[pip] installing video-use and local ASR dependencies'
& $venvPy -m pip install --quiet --upgrade pip
& $venvPy -m pip install --quiet -e $Dest faster-whisper
if ($LASTEXITCODE -ne 0) { throw 'pip install failed.' }

Write-Host ''
Write-Host "video-use installed at $Dest"
Write-Host "Next: video-studio init --station `"$Station`"   # records it in station.json"
Write-Host '      video-studio edit --footage <dir> --out <dir> --backend vendored'
