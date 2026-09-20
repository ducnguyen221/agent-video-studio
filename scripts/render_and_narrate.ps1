# render_and_narrate.ps1 - thin Windows/PowerShell wrapper around `video-studio narrate`.
#
# One command: render a HyperFrames project to a silent MP4, then add a voiceover from the
# voice station -> one finished MP4. The old version of this script hardcoded one machine's
# Python, one machine's Node directory and a floating engine version; all three now come from
# the CLI's own resolution (VIDEO_STATION, NODE_DIR, HYPERFRAMES_VERSION).
#
# ASCII-only on purpose: a .ps1 saved as UTF-8 WITHOUT a BOM is parsed as the system code page
# by Windows PowerShell 5.1 and non-ASCII comments become parse errors.
#
# Usage:
#   pwsh -File scripts/render_and_narrate.ps1 -Project demo -Text "..."  -Out final.mp4
#   pwsh -File scripts/render_and_narrate.ps1 -Video silent.mp4 -TextFile script.txt -Out final.mp4 `
#        -Profile my-profile -Mode fit -Bgm none
param(
    [string]$Project,
    [string]$Video,
    [string]$Text,
    [string]$TextFile,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Profile,
    [ValidateSet('fit', 'shortest')][string]$Mode = 'fit',
    [double]$Speed,
    [string]$Bgm,
    [switch]$KeepSilent,
    [switch]$Json
)

# Do NOT set ErrorActionPreference=Stop: the engines log to stderr on a healthy run.

function Find-VideoStudio {
    $cmd = Get-Command 'video-studio' -ErrorAction SilentlyContinue
    if ($cmd) { return , @($cmd.Source) }
    $names = @($env:VIDEO_STUDIO_PY, 'python', 'python3', 'py') | Where-Object { $_ }
    foreach ($name in $names) {
        $c = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $c) { continue }
        & $c.Source -c 'import sys' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return , @($c.Source, '-m', 'video_studio') }
    }
    throw "video-studio not found. Install it: pip install -e <clone of agent-video-studio>"
}

if (-not $Project -and -not $Video) { throw "Give -Project <name|dir> or -Video <silent.mp4>." }
if (-not $Text -and -not $TextFile) { throw "Give -Text or -TextFile (the narration)." }

$argv = @('narrate', '--out', $Out, '--mode', $Mode)
if ($Project) { $argv += @('--project', $Project) }
if ($Video) { $argv += @('--video', $Video) }
if ($TextFile) { $argv += @('--file', $TextFile) } else { $argv += @('--text', $Text) }
if ($Profile) { $argv += @('--profile', $Profile) }
if ($PSBoundParameters.ContainsKey('Speed')) { $argv += @('--speed', "$Speed") }
if ($Bgm) { $argv += @('--bgm', $Bgm) }
if ($KeepSilent) { $argv += '--keep-silent' }
if ($Json) { $argv += '--json' }

$run = Find-VideoStudio
$exe = $run[0]
$rest = @()
if ($run.Count -gt 1) { $rest = $run[1..($run.Count - 1)] }
& $exe @($rest + $argv)
exit $LASTEXITCODE
