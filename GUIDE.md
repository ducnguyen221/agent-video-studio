# agent-video-studio guide

*[Tiếng Việt](GUIDE.vi.md)*

## 1. Prepare the machine

| Needed | Windows | macOS |
|---|---|---|
| Python ≥ 3.10 | python.org or `winget install Python.Python.3.12` | `brew install python@3.12` |
| Node ≥ 22 | `winget install OpenJS.NodeJS.LTS` | `brew install node` |
| ffmpeg + ffprobe | `winget install Gyan.FFmpeg` | `brew install ffmpeg` |
| Inter font | download from rsms.me/inter and install | `brew install --cask font-inter` |

If a tool is not on PATH, set `NODE_DIR` / `FFMPEG_DIR` to the folder that holds it.

## 2. Install the repo

Clone, create a venv, `pip install -e ".[test]"`, then run `video-studio doctor`. It installs
nothing: it names what is missing and how to install it.

## 3. Choose where the station lives

`video-studio init` asks you to pick one:

- **embedded** (recommended for new users) — the station is `workspace/` inside the repo, ignored
  by git. One folder holds everything. Do not delete the repo folder to reinstall: your projects
  live there.
- **separate** — the station has its own folder (default `~/.video`). Suits several machines or a
  repo that is your own public one. Set `VIDEO_STATION` so every other tool finds it.

On a machine that already has a station, `init` detects it and does not ask.

## 4. Adopt an existing station

An older layout (`news/`, `topstory/` directly at the station root) moves to the new layout with:

1. `video-studio init --station <station> --migrate --dry-run` — read the plan: what moves, what
   gets pinned, what stays untouched.
2. If it looks right, run it again without `--dry-run`. Close any browser/preview holding files
   in the station first.
3. To reverse it: `video-studio init --station <station> --undo`.

## 5. HyperFrames version

Renders always use one exact version (`HYPERFRAMES_VERSION`, or `hyperframes_version` in
`station.json`). `video-studio doctor --check-updates` reports newer releases; upgrading is a
deliberate step — render a test, compare, then switch.

## 6. The three jobs

| What you have | Command |
|---|---|
| Data (a news recap, a deep dive) and you want a video | `video-studio render --project topstory --input spec.json --out <dir>` |
| A silent video and a narration script | `video-studio narrate --video in.mp4 --file script.txt --out final.mp4 --profile <name>` |
| Real recorded footage | `video-studio edit --footage <dir> --out <dir>` |

To inspect before rendering: `video-studio preview --project <name>` (Ctrl+C to stop).

Narration needs the **voice studio installed into the same venv** — see the "which venv" section
of `docs/INSTALL.md`. That is the single most common mistake.

## 7. Keeping your work safe

```
video-studio backup --out backup.zip      # zips the station, minus scratch and cache
video-studio migrate --to separate        # moves an embedded station out of the repo
video-studio update                       # git pull --ff-only, never cleans
```

Which folders are safe to delete: `docs/WORKSPACE.md`.

## 8. Moving to another machine

```
video-studio export --out pack.zip --personal --include music   # only your own material
video-studio import --in pack.zip --dry-run                     # see what it would write
video-studio import --in pack.zip                               # unpack into the station
```

`--personal` takes `projects/*/assets` plus exactly the folders you name with `--include`;
scratch, cache, virtualenvs and a vendored `.git` tree never enter the pack. Drop `--personal`
to pack the whole station.

`import` never overwrites: it skips existing files and prints their names so you decide. Pass
`--overwrite` when you really mean it. On a new machine run `video-studio init --station <dir>`
first, then `import`.
