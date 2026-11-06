#!/usr/bin/env sh
# install-video-use.sh - OPTIONAL: install browser-use/video-use into the video station.
#
# You do NOT need this to edit footage: `video-studio edit` ships its own distilled helpers
# (see video_studio/edit/, NOTICE). Install this only when you want the upstream tree itself -
# to follow upstream changes, or to use its cloud ASR path (speaker diarization, filler words).
#
# What it does: clone (or fast-forward) upstream into <station>/video-use, create a venv, install
# its dependencies. Idempotent; it never deletes your work.
#
# Where the venv goes:
#   - Machine WITHOUT OpcOS: <station>/video-use/.venv, installed editable from the clone (as before).
#   - Machine WITH OpcOS (OPCOS_RUNTIME, OPCOS_ROOT, or ~/OpcOS/paths.json): outside the station, at
#     <runtime>/venvs/agent-video-studio/video-use. The package is installed as a COPY, never
#     editable, so nothing is written into the clone. When the OpcOS tool
#     <runtime>/../system/operations/runtime/opcos-runtime.sh exists it does the install
#     (`ensure --repo-dir <repo>`, driven by opcos-runtime.json); otherwise this script builds the
#     venv itself. The clone is still pulled as before unless --venv-only is given.
#
# --venv-only   do not clone or pull (no git at all); needs an existing <station>/video-use clone.
# --print-plan  install nothing, print key=value lines (station, venv, clone, installer), exit 0.
#
# Requires: python3.10+; git and ffmpeg on PATH (not needed with --print-plan or --venv-only).
# Usage: sh scripts/install-video-use.sh [--station DIR] [--venv-only] [--print-plan]
set -eu

STATION=""
VENV_ONLY=0
PRINT_PLAN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --station) STATION="$2"; shift 2 ;;
    --venv-only) VENV_ONLY=1; shift ;;
    --print-plan) PRINT_PLAN=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done


if [ "$PRINT_PLAN" = 0 ] && [ "$VENV_ONLY" = 0 ]; then
  for tool in git ffmpeg; do
    command -v "$tool" >/dev/null 2>&1 || { echo "Missing '$tool' on PATH - install it first." >&2; exit 3; }
  done
fi

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

# The station is resolved by the package itself (VIDEO_STATION -> VIDEO_ROOT ->
# studio.local.json -> <repo>/workspaces), never guessed as a folder under $HOME: an embedded
# install keeps its station inside the repo. The core is stdlib-only, so any Python 3.10+ can
# import it straight from this clone.
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
CODE='import sys; sys.path.insert(0, sys.argv[1]); from video_studio import _env; st = sys.argv[2] if len(sys.argv) > 2 else _env.resolve_station()[0]; print(st or str()); print(_env.init_command(st) if st else str())'
if [ -n "$STATION" ]; then RESOLVED=$("$PY" -c "$CODE" "$REPO_ROOT" "$STATION")
else RESOLVED=$("$PY" -c "$CODE" "$REPO_ROOT"); fi
STATION=$(echo "$RESOLVED" | sed -n 1p)
INIT_CMD=$(echo "$RESOLVED" | sed -n 2p)
[ -n "$STATION" ] || { echo "No video station chosen yet - run 'video-studio init' first, or pass --station DIR." >&2; exit 3; }
DEST="$STATION/video-use"

# Runtime placement (OpcOS machines). The rule (R = OPCOS_RUNTIME, else OPCOS_ROOT/runtime, else
# ~/OpcOS/runtime when ~/OpcOS/paths.json exists, else none) is implemented ONCE, in
# video_studio/_env.py. Two lines: the runtime root R, then the venv dir; empty = no OpcOS here.
RCODE='import sys; sys.path.insert(0, sys.argv[1]); from video_studio import _env; fix = lambda p: (p or str()).replace(chr(92), chr(47)); print(fix(_env.runtime_root(home=sys.argv[2]))); print(fix(_env.runtime_resource("venvs", "video-use", home=sys.argv[2])))'
RT=$("$PY" -c "$RCODE" "$REPO_ROOT" "$HOME")
RUNTIME_ROOT=$(printf '%s\n' "$RT" | sed -n 1p)
RUNTIME_VENV=$(printf '%s\n' "$RT" | sed -n 2p)
# The opcos-runtime tool: $OPCOS_ROOT/system/... first (R may live outside the OpcOS tree), then
# <parent of R>/system/...; none found means this script builds the venv itself.
CLI=""
OPCOS_ROOT_T=$(printf '%s' "${OPCOS_ROOT:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if [ -n "$OPCOS_ROOT_T" ] && [ -f "$OPCOS_ROOT_T/system/operations/runtime/opcos-runtime.sh" ]; then
  CLI="$OPCOS_ROOT_T/system/operations/runtime/opcos-runtime.sh"
elif [ -n "$RUNTIME_ROOT" ]; then
  cand="$(dirname "$RUNTIME_ROOT")/system/operations/runtime/opcos-runtime.sh"
  [ -f "$cand" ] && CLI="$cand"
fi

resolve_video_use_venv() {
  # $1 = station. With OpcOS: the runtime venv; without: <station>/video-use/.venv.
  if [ -n "$RUNTIME_VENV" ]; then printf '%s\n' "$RUNTIME_VENV"; else printf '%s\n' "$1/video-use/.venv"; fi
}
VENV=$(resolve_video_use_venv "$STATION")

if [ "$PRINT_PLAN" = 1 ]; then
  if [ "$VENV_ONLY" = 1 ]; then CLONE_MODE=skip
  elif [ -d "$DEST/.git" ]; then CLONE_MODE=pull
  else CLONE_MODE=clone; fi
  if [ -n "$RUNTIME_VENV" ] && [ -n "$CLI" ]; then INSTALLER=opcos-runtime; else INSTALLER=venv; fi
  if [ -n "$RUNTIME_VENV" ]; then EDITABLE=no; else EDITABLE=yes; fi
  echo "station=$STATION"
  echo "venv=$VENV"
  echo "clone=$CLONE_MODE"
  echo "installer=$INSTALLER"
  echo "editable=$EDITABLE"
  echo "runtime=$RUNTIME_ROOT"
  echo "cli=$CLI"
  exit 0
fi

# Copy the clone to a temp folder and install FROM the copy, so the clone
# is never written to. The copy is removed at the end, also on failure or interrupt.
install_from_copy() {
  TMP_COPY=$(mktemp -d)
  trap 'rm -rf "$TMP_COPY"' EXIT
  trap 'rm -rf "$TMP_COPY"; exit 130' INT TERM
  for item in "$DEST"/* "$DEST"/.[!.]*; do
    [ -e "$item" ] || continue
    case "$(basename "$item")" in .venv|.git) continue ;; esac
    cp -R "$item" "$TMP_COPY/"
  done
  # .git is NOT copied: the need's package is "@source", which the opcos-runtime tool hashes by file
  # tree (skipping .git) and never checks with git. *.egg-info and __pycache__ are pruned so stale
  # build metadata cannot confuse pip; build/ is kept (it may be source).
  find "$TMP_COPY" \( -name __pycache__ -o -name '*.egg-info' \) -type d -prune -exec rm -rf {} + 2>/dev/null || true
  if [ -n "$CLI" ]; then
    echo "[opcos-runtime] ensure venvs/video-use"
    # Success is judged only by the exit code (set -e): uv/pip log to stderr even when they succeed.
    # The need's package is "." and comes ONLY from --source-dir (the copy made above).
    # --upgrade: an unchanged spec hash stays RT_UP_TO_DATE, a changed one (new clone commit) reinstalls.
    sh "$CLI" ensure --repo-dir "$REPO_ROOT" --only venvs/video-use --source-dir "venvs/video-use=$TMP_COPY" --upgrade
  else
    VENV_PY="$VENV/bin/python"
    [ -x "$VENV_PY" ] || { echo "[venv] creating"; "$PY" -m venv "$VENV"; }
    echo "[pip] installing video-use (copy, not editable) and local ASR dependencies"
    "$VENV_PY" -m pip install --quiet --upgrade pip
    PIP_C=""
    case "$(uname -s 2>/dev/null)" in MINGW*|MSYS*|CYGWIN*) PIP_C="$REPO_ROOT/locks/video-use-windows.txt" ;; esac
    "$VENV_PY" -m pip install --quiet "$TMP_COPY" -r "$REPO_ROOT/scripts/requirements-video-use.txt" ${PIP_C:+-c "$PIP_C"}
  fi
  rm -rf "$TMP_COPY"
  trap - EXIT INT TERM
}

if [ "$VENV_ONLY" = 1 ]; then
  [ -d "$DEST" ] || { echo "--venv-only needs an existing clone at $DEST - none found (nothing was changed). Run without --venv-only to clone it." >&2; exit 3; }
elif [ -d "$DEST/.git" ]; then
  echo "[git] fast-forward $DEST"
  git -C "$DEST" pull --ff-only
else
  mkdir -p "$STATION"
  git clone --depth 1 https://github.com/browser-use/video-use.git "$DEST"
fi

if [ -n "$RUNTIME_VENV" ]; then
  # With OpcOS, with or without --venv-only: the venv is the runtime one and the package is a copy.
  install_from_copy
else
  VENV_PY="$VENV/bin/python"
  [ -x "$VENV_PY" ] || { echo "[venv] creating"; "$PY" -m venv "$VENV"; }

  echo "[pip] installing video-use and local ASR dependencies"
  "$VENV_PY" -m pip install --quiet --upgrade pip
  "$VENV_PY" -m pip install --quiet -e "$DEST" faster-whisper
fi

echo
echo "video-use installed at $DEST (venv: $VENV)"
if [ -n "$RUNTIME_VENV" ]; then
  echo "python=$VENV/bin/python"
  echo "Note: a station that already records video_use.python keeps it (init never overwrites it) - edit station.json by hand to use this venv."
fi
echo "Next: ${INIT_CMD:-video-studio init}   # records it in station.json"
echo "      video-studio edit --footage <dir> --out <dir> --backend vendored"
