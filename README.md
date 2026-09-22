# agent-video-studio

*[Tiếng Việt](README.vi.md)* · [Website](https://ducnguyen.vn/agent-video-studio/)

A video-production engine an AI agent can drive: HTML/CSS/GSAP compositions rendered to MP4 by
[HyperFrames](https://github.com/heygen-com/hyperframes), wrapped in an installable Python package
with one CLI, `video-studio`.

> **Status: first release, v0.1.0.** This build ships the station layout, the machine check,
> the migration tool, the news template family, narration, preview, footage editing, and
> `export` / `import` for moving station data between machines. Every command in the table
> below is backed by real code.

**This is an added capability, not one piece of a suite you must install whole.** The
repository stands alone: install it when you need to build video, and only then. A content
pipeline (for example `agent-marketing-studio`) *can* call it through the shared contract —
exit code plus a final JSON line on stdout — when it is present, but that pipeline runs fine
without it and says plainly that the video capability is missing rather than failing mid-run.
The **voice** station (`agent-voice-studio`) is the same: without it, silent renders still
work, you just cannot add narration. There is no required install order and no bundle.

## What is in this build

| Command | Does |
|---|---|
| `video-studio doctor` | Checks Node ≥ 22, npx, the pinned HyperFrames build, its headless Chromium, ffmpeg/ffprobe, the Inter font, the station and `station.json`. `--check-updates` only *reports* a newer HyperFrames. |
| `video-studio init` | Lays out a station (`embedded` inside the repo, or `separate` outside it), writes `station.json`, copies the agent skills. `--migrate` adopts an older station layout, `--dry-run` prints the plan without writing, `--undo` reverses the last run from its journal. |
| `video-studio render` | A JSON spec (`schema_version: 1`) → MP4s from a template: `news`, `news-weekly`, `topstory`, `repo-today`. Needs the `[voice]` extra. |
| `video-studio narrate` | A silent MP4 (or a whole project, rendered first) + narration text → one finished MP4 with voice and optional background music, through the voice studio. |
| `video-studio preview` | Opens the HyperFrames preview studio for a project — with the *pinned* build, so what you inspect is what will render. |
| `video-studio edit` | Cuts real footage: transcribe locally, pack the transcript into phrase-level markdown, then render an EDL with grade, overlays, subtitles and loudness normalisation. Helpers distilled from `video-use` (MIT); can also drive a vendored upstream copy. |
| `video-studio export` / `import` | Zip a station and unpack it on another machine. `--personal` takes only project assets (`projects/*/assets`) plus the top-level folders you name with `--include`; scratch, cache, virtualenvs and git trees never enter the pack. `import` never overwrites unless you ask, and has `--dry-run`. |
| `video-studio backup` / `migrate` / `update` | Zip the station; move an `embedded` station out of the repo; fast-forward the clone (never cleans). |

Every command follows one contract: exit `0` ok · `1` render/engine error (retryable) ·
`2` bad call or config · `3` station or tool missing; with `--json` the last stdout line is a
single JSON object and human logs go to stderr. Full calling contract:
[docs/CONTRACT.md](docs/CONTRACT.md).

**The engine ships no default brand.** A spec must declare `brand.a`, `brand.b` and
`brand.site`; leaving them out is exit code 2, never a silent fallback — a silent fallback here
means your video carries somebody else's name.

## Install

```bash
git clone https://github.com/ducnguyen221/agent-video-studio
cd agent-video-studio
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[test]"
video-studio init            # presents the two-option table and waits; --station DIR = separate
video-studio doctor          # after init: before there is a station, doctor exits 3 by design
```

`init` **presents a table before doing anything**, rather than asking an open question.
`embedded` — station at `<repo>/workspace/`, configuration in `<repo>/.env` — is the
**recommendation**: press Enter and you are done, with no environment variables to set, and
`init` copies `.env.example` to `.env` for you to fill in. Choose `separate` when you work
across machines, are comfortable with the technical side, or this repository is your own public
fork. With nobody to answer (CI, a scheduled task) `init` prints that table and **exits with
code 2 without writing a byte** — an installing agent must show it to the user instead of
choosing silently.

HyperFrames is not a Python dependency: it runs through `npx hyperframes@$HYPERFRAMES_VERSION`,
always an exact version (never `latest`).

## Documentation

- [Website](https://ducnguyen.vn/agent-video-studio/) — what it does, how to install, the rules.
- [docs/INSTALL.md](docs/INSTALL.md) — Node, ffmpeg, fonts, and *which venv to install into*.
- [docs/WORKSPACE.md](docs/WORKSPACE.md) — the station, the two install modes, what is safe to delete.
- [docs/AGENT_VIDEO_GUIDE.md](docs/AGENT_VIDEO_GUIDE.md) — how an agent drives the whole thing.
- [docs/CONTRACT.md](docs/CONTRACT.md) — the spec schema and the calling contract.
- [docs/THEME-LIBRARY.md](docs/THEME-LIBRARY.md) — layout patterns and the hard rendering rules.

## Agent skills

`skills/` holds **24 skills**: three written for this repo (`video-routing`, `video-edit`,
`video-theme-library`) and **21 distilled from the current HyperFrames skill set**
(`skills/hyperframes/`). Those 21 are translated into Vietnamese, condensed and edited from the
upstream `skills/<name>/SKILL.md` at one pinned tag; the frontmatter stays in English because
that is what a harness reads to route. No upstream binary (font, audio, image) and no upstream
`references/` tree was copied. The pinned source of each skill lives in
[`upstream.json`](upstream.json), and `video-studio doctor` checks that ledger against the tree.

`video-studio init` copies all 24 into `<station>/.claude/skills` and `<station>/.agents/skills`
and writes `skills-lock.json`. If the station still carries an older skill set installed by
another tool, `init --migrate` removes it — the old copy is kept in the run journal, so
`init --undo` puts it back.

## Rules

Not advice — these are why the repository is built the way it is, and the conditions for using
it without causing anybody trouble.

1. **Credit the right source under the right licence.** The distilled HyperFrames skills are
   **Apache-2.0** and carry the "state your changes" obligation (§4(b)); the `edit` helpers are
   distilled from `video-use` under **MIT**; one upstream skill drags in an **MIT** credit for
   `vtake-skills`. All three are spelled out in `NOTICE` with the pinned source tag. **Removing
   the attribution breaks the licence**, it is not an editorial choice.
2. **Never redistribute somebody else's assets.** No upstream font, audio, image or video is
   copied into this repository — the per-file licences have not been checked. Whatever is needed
   is **called at runtime** and installed by the user.
3. **The brand must be declared; there is no default.** A spec missing `brand.a` / `brand.b` /
   `brand.site` is **exit code 2**. A silent fallback here means your video carries somebody
   else's name, and you only find out after publishing.
4. **Pin the version; report, never auto-upgrade.** The engine always runs through
   `npx hyperframes@$HYPERFRAMES_VERSION`, never `latest`. `doctor --check-updates` only
   *reports* a newer build — upgrading is your call, because upgrading the engine changes what
   comes out of it.

A test gate blocks customer names, private brand names, voice profile names, machine paths and
home-directory environment variables — across the docs and the website page too, **allowed by
count** rather than by exempting whole files.

## License

MIT for this repository's code (see `LICENSE`). Third-party components called at runtime keep
their own licenses — see `NOTICE`.

## Acknowledgments

- [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) — the render engine.
- [video-use](https://github.com/browser-use/video-use) (MIT) — the footage-editing method the
  `edit` helpers are distilled from.
