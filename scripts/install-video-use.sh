#!/usr/bin/env sh
# install-video-use.sh - OPTIONAL: install browser-use/video-use into the video station.
#
# You do NOT need this to edit footage: `video-studio edit` ships its own distilled helpers
# (see video_studio/edit/, NOTICE). Install this only when you want the upstream tree itself -
# to follow upstream changes, or to use its cloud ASR path (speaker diarization, filler words).
#
# What it does: clone (or fast-forward) upstream into <station>/video-use, create a venv next
# to it, install its dependencies. Idempotent; it never deletes your work.
#
# Requires: git, python3.10+, ffmpeg on PATH.
# Usage: sh scripts/install-video-use.sh [--station DIR]
set -eu

STATION=""
while [ $# -gt 0 ]; do
  case "$1" in
    --station) STATION="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -n "$STATION" ] || STATION="${VIDEO_STATION:-${VIDEO_ROOT:-$HOME/.video}}"
DEST="$STATION/video-use"

for tool in git ffmpeg; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing '$tool' on PATH - install it first." >&2; exit 3; }
done

# Prove the interpreter by running it: a `python3` that exists but cannot run is worse than none.
PY=""
for cand in "${VIDEO_STUDIO_PY:-}" python3 python; do
  [ -n "$cand" ] || continue
  command -v "$cand" >/dev/null 2>&1 || continue
  if "$cand" -c 'import sys; assert sys.version_info[:2] >= (3, 10)' >/dev/null 2>&1; then
    PY="$cand"; break
  fi
done
[ -n "$PY" ] || { echo "No usable Python 3.10+ found (set VIDEO_STUDIO_PY)." >&2; exit 3; }

if [ -d "$DEST/.git" ]; then
  echo "[git] fast-forward $DEST"
  git -C "$DEST" pull --ff-only
else
  mkdir -p "$STATION"
  git clone --depth 1 https://github.com/browser-use/video-use.git "$DEST"
fi

VENV="$DEST/.venv"
VENV_PY="$VENV/bin/python"
[ -x "$VENV_PY" ] || { echo "[venv] creating"; "$PY" -m venv "$VENV"; }

echo "[pip] installing video-use and local ASR dependencies"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -e "$DEST" faster-whisper

echo
echo "video-use installed at $DEST"
echo "Next: video-studio init --station \"$STATION\"   # records it in station.json"
echo "      video-studio edit --footage <dir> --out <dir> --backend vendored"
