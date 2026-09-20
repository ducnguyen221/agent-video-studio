# preview.ps1 - thin Windows/PowerShell wrapper around `video-studio preview`.
#
# ASCII-only on purpose: a .ps1 saved as UTF-8 WITHOUT a BOM is parsed as the system code page
# by Windows PowerShell 5.1, which turns non-ASCII comments into parse errors at the worst
# possible moment (a scheduled run at 6pm). Keep this file ASCII and the question never comes up.
#
# All logic lives in the Python CLI - this file only finds an interpreter and forwards argv.
# Usage:
#   pwsh -File scripts/preview.ps1 [-Project <name|dir>] [-Port <n>]
param(
    [string]$Project,
    [int]$Port
)

# Do NOT set ErrorActionPreference=Stop: node/hyperframes write ordinary logs to stderr and
# PowerShell 5.1 would turn them into terminating errors. Check $LASTEXITCODE instead.
#
# Exit codes are part of the contract (docs/CONTRACT.md): 1 means "retry may work", 3 means
# "install something". A bare `throw` makes `pwsh -File` exit 1, so a caller that retries on 1
# would retry "video-studio is not installed" forever.

function Fail($code, $message) {
    Write-Error $message
    exit $code
}

function Find-VideoStudio {
    # 1) console script on PATH (pip install put it there)
    $cmd = Get-Command 'video-studio' -ErrorAction SilentlyContinue
    if ($cmd) { return , @($cmd.Source) }
    # 2) python -m video_studio. VIDEO_STUDIO_PY wins; then whatever PATH offers.
    #    Each candidate is proven by running it - on Windows `python3` is often the Microsoft
    #    Store stub, which exists on PATH and fails on every real call.
    $names = @($env:VIDEO_STUDIO_PY, 'python', 'python3', 'py') | Where-Object { $_ }
    foreach ($name in $names) {
        $c = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $c) { continue }
        & $c.Source -c 'import sys' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return , @($c.Source, '-m', 'video_studio') }
    }
    Fail 3 "video-studio not found. Install it: pip install -e <clone of agent-video-studio>"
}

$argv = @('preview')
if ($Project) { $argv += @('--project', $Project) }
if ($Port) { $argv += @('--port', "$Port") }

$run = Find-VideoStudio
$exe = $run[0]
$rest = @()
if ($run.Count -gt 1) { $rest = $run[1..($run.Count - 1)] }
& $exe @($rest + $argv)
exit $LASTEXITCODE
