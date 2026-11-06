# install-video-use.ps1 - OPTIONAL: install browser-use/video-use into the video station.
#
# You do NOT need this to edit footage: `video-studio edit` ships its own distilled helpers
# (see video_studio/edit/, NOTICE). Install this only when you want the upstream tree itself -
# to follow upstream changes, or to use its cloud ASR path (speaker diarization, filler words).
#
# What it does: clone (or fast-forward) upstream into <station>/video-use, create a venv, install
# its dependencies, and tell `video-studio init` to record it in station.json.
# Idempotent: running it again pulls and re-checks the venv; it never deletes your work.
#
# Where the venv goes:
#   - Machine WITHOUT OpcOS: <station>/video-use/.venv, installed editable from the clone (as before).
#   - Machine WITH OpcOS (OPCOS_RUNTIME, OPCOS_ROOT, or ~/OpcOS/paths.json): outside the station, at
#     <runtime>/venvs/agent-video-studio/video-use. The package is installed as a COPY, never
#     editable, so nothing is written into the clone. When the OpcOS tool
#     <runtime>/../system/operations/runtime/opcos-runtime.ps1 exists it does the install
#     (`ensure --repo-dir <repo>`, driven by opcos-runtime.json); otherwise this script builds the
#     venv itself. The clone is still pulled as before unless -VenvOnly is given.
#
# -VenvOnly   do not clone or pull (no git at all); needs an existing <station>/video-use clone.
# -PrintPlan  install nothing, print key=value lines (station, venv, clone, installer) and exit 0.
#
# ASCII-only on purpose: a .ps1 saved as UTF-8 without a BOM is parsed as the system code page
# by Windows PowerShell 5.1 and non-ASCII comments become parse errors.
#
# Requires: python 3.10+; git and ffmpeg on PATH (git/ffmpeg are not needed with -PrintPlan or -VenvOnly).
# Usage: pwsh -File scripts/install-video-use.ps1 [-Station <dir>] [-VenvOnly] [-PrintPlan]
param(
    [string]$Station,
    [switch]$VenvOnly,
    [switch]$PrintPlan
)
$ErrorActionPreference = 'Stop'


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

function Get-VenvPython([string]$Venv) {
    if ($env:OS -eq 'Windows_NT') { return (Join-Path $Venv 'Scripts/python.exe') }
    return (Join-Path $Venv 'bin/python')
}

# Where the venv lives. The rule (R = OPCOS_RUNTIME, else OPCOS_ROOT/runtime, else ~/OpcOS/runtime
# when ~/OpcOS/paths.json exists, else none) is implemented ONCE, in video_studio/_env.py;
# $RuntimeVenv is its answer, computed below from $HOME.
function Resolve-VideoUseVenv([string]$Station) {
    if ($script:RuntimeVenv) { return $script:RuntimeVenv }
    return (Join-Path (Join-Path $Station 'video-use') '.venv')
}

# Copy the clone (minus .git and .venv) to a temp folder and install FROM the copy, so the
# clone is never written to. The copy is removed at the end, also on failure.
function Install-FromCopy([string]$Dest, [string]$Venv) {
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('video-use-src-' + [guid]::NewGuid().ToString('N'))
    try {
        New-Item -ItemType Directory -Force $tmp | Out-Null
        Get-ChildItem -LiteralPath $Dest -Force |
            Where-Object { $_.Name -ne '.git' -and $_.Name -ne '.venv' } |
            ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $tmp -Recurse -Force }
        if ($script:Cli) {
            Write-Host "[opcos-runtime] ensure venvs/video-use"
            $hostExe = (Get-Process -Id $PID).Path
            & $hostExe -NoProfile -File $script:Cli ensure --repo-dir $script:RepoRoot --only venvs/video-use --source-dir "venvs/video-use=$tmp"
            if ($LASTEXITCODE -ne 0) { throw 'opcos-runtime ensure failed.' }
        }
        else {
            $venvPy = Get-VenvPython $Venv
            if (-not (Test-Path $venvPy)) {
                Write-Host '[venv] creating'
                & $script:py -m venv $Venv
                if ($LASTEXITCODE -ne 0) { throw 'venv creation failed.' }
            }
            Write-Host '[pip] installing video-use (copy, not editable) and local ASR dependencies'
            & $venvPy -m pip install --quiet --upgrade pip
            & $venvPy -m pip install --quiet $tmp faster-whisper
            if ($LASTEXITCODE -ne 0) { throw 'pip install failed.' }
        }
    }
    finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

# git and ffmpeg are only needed when this run really clones/pulls and installs.
if (-not $PrintPlan -and -not $VenvOnly) {
    foreach ($tool in 'git', 'ffmpeg') {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "Missing '$tool' on PATH - install it first."
        }
    }
}
$py = Find-Python

# The station is resolved by the package itself (VIDEO_STATION -> VIDEO_ROOT ->
# studio.local.json -> <repo>/workspaces), never guessed as a folder under $HOME: an embedded
# install keeps its station inside the repo. The core is stdlib-only, so any Python 3.10+ can
# import it straight from this clone.
$RepoRoot = Split-Path -Parent $PSScriptRoot
$code = 'import sys; sys.path.insert(0, sys.argv[1]); from video_studio import _env; ' +
        'st = sys.argv[2] if len(sys.argv) > 2 else _env.resolve_station()[0]; ' +
        'print(st or str()); print(_env.init_command(st) if st else str())'
if ($Station) { $resolved = @(& $py -c $code $RepoRoot $Station) }
else { $resolved = @(& $py -c $code $RepoRoot) }
if ($LASTEXITCODE -ne 0 -or $resolved.Count -lt 1 -or -not $resolved[0]) {
    throw 'No video station chosen yet - run `video-studio init` first, or pass -Station <dir>.'
}
$Station = $resolved[0]
$InitCmd = if ($resolved.Count -gt 1) { $resolved[1] } else { 'video-studio init' }
$Dest = Join-Path $Station 'video-use'

# Runtime placement (OpcOS machines). Two lines: the runtime root R, then the venv dir; empty
# lines mean "no OpcOS here" and the old in-station layout applies.
$rcode = 'import sys; sys.path.insert(0, sys.argv[1]); from video_studio import _env; ' +
         'print(_env.runtime_root(home=sys.argv[2]) or str()); ' +
         'print(_env.runtime_resource(''venvs'', ''video-use'', home=sys.argv[2]) or str())'
$rt = @(& $py -c $rcode $RepoRoot $HOME)
if ($LASTEXITCODE -ne 0) { throw 'could not resolve the OpcOS runtime location.' }
$RuntimeRoot = if ($rt.Count -gt 0) { [string]$rt[0] } else { '' }
$RuntimeVenv = if ($rt.Count -gt 1) { [string]$rt[1] } else { '' }
$Cli = ''
if ($RuntimeRoot) {
    $cand = Join-Path (Split-Path -Parent $RuntimeRoot) 'system/operations/runtime/opcos-runtime.ps1'
    if (Test-Path -LiteralPath $cand -PathType Leaf) { $Cli = $cand }
}
$venv = Resolve-VideoUseVenv $Station

if ($PrintPlan) {
    $cloneMode = if ($VenvOnly) { 'skip' } elseif (Test-Path -LiteralPath (Join-Path $Dest '.git')) { 'pull' } else { 'clone' }
    $installer = if ($RuntimeVenv -and $Cli) { 'opcos-runtime' } else { 'venv' }
    Write-Output "station=$Station"
    Write-Output "venv=$venv"
    Write-Output "clone=$cloneMode"
    Write-Output "installer=$installer"
    Write-Output ('editable=' + $(if ($RuntimeVenv) { 'no' } else { 'yes' }))
    Write-Output "runtime=$RuntimeRoot"
    exit 0
}

if ($VenvOnly) {
    if (-not (Test-Path -LiteralPath $Dest -PathType Container)) {
        throw "-VenvOnly needs an existing clone at $Dest - none found (nothing was changed). Run without -VenvOnly to clone it."
    }
}
elseif (Test-Path (Join-Path $Dest '.git')) {
    Write-Host "[git] fast-forward $Dest"
    git -C $Dest pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw 'git pull --ff-only failed - resolve it by hand (nothing was deleted).' }
}
else {
    New-Item -ItemType Directory -Force (Split-Path -Parent $Dest) | Out-Null
    git clone --depth 1 https://github.com/browser-use/video-use.git $Dest
    if ($LASTEXITCODE -ne 0) { throw 'git clone failed.' }
}

if ($RuntimeVenv) {
    # With OpcOS, with or without -VenvOnly: the venv is the runtime one and the package is a copy.
    Install-FromCopy $Dest $venv
}
else {
    $venvPy = Get-VenvPython $venv
    if (-not (Test-Path $venvPy)) {
        Write-Host '[venv] creating'
        & $py -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'venv creation failed.' }
    }

    Write-Host '[pip] installing video-use and local ASR dependencies'
    & $venvPy -m pip install --quiet --upgrade pip
    & $venvPy -m pip install --quiet -e $Dest faster-whisper
    if ($LASTEXITCODE -ne 0) { throw 'pip install failed.' }
}

Write-Host ''
Write-Host "video-use installed at $Dest (venv: $venv)"
if ($RuntimeVenv) {
    Write-Host ('python=' + (Get-VenvPython $venv))
    Write-Host 'Note: a station that already records video_use.python keeps it (init never overwrites it) - edit station.json by hand to use this venv.'
}
Write-Host "Next: $InitCmd   # records it in station.json"
Write-Host '      video-studio edit --footage <dir> --out <dir> --backend vendored'
