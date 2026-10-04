# tiny-soho-motion-runtime

The workspace a Claude Code session uses to turn finished Tiny Soho slides (text baked in) into short branded reel
clips. The session reads each slide, removes the text, re-sets it in brand type with tested motion, looks at its
own frames, fixes what it sees, gets an independent review, and writes a scene prompt for the video model (LTX)
that animates the child afterwards.

It runs two ways:

- **Cloud (Claude Code routine).** The app fires the routine's API trigger, a cloud session clones this repo and
  follows `routine/PROMPT.md`. It uses the owner's Claude subscription, not an API key.
- **Local.** `./run_local.sh <job-dir> <slides…>` runs headless `claude -p` in a sealed copy of this workspace,
  using a subscription token from `claude setup-token`, saved in `~/.config/tiny-soho/claude-oauth-token`.

## Layout

| Path | What |
|---|---|
| `.claude/skills/tiny-soho-direct/SKILL.md` | The brief, the plan format, the effect menu and the critique procedure |
| `tools/inspect_slide.py` | Coordinate grid and OCR hints for a slide |
| `tools/zoom.py` | Enlarged crop with a 10 px grid |
| `tools/clean.py` | Removes baked-in text inside the plan's line boxes, never inside protected boxes |
| `tools/render.py` | Brand type plus word-level motion (rise, snap, slow, spring, stamp, pop, slides, droop, pulse, nudge) over the text-free image. Outputs stills, exact frames or an MP4 |
| `tools/check.py` | Automatic checks: edges, overlaps, protected areas, hook on frame 0, timing |
| `brand/` | Brand fonts (SIL Open Font License) and the wordmark |
| `fixtures/` | Test slides. Each folder is one job |
| `routine/PROMPT.md` | The prompt the cloud routine runs |
| `setup.sh`, `requirements.txt` | Python dependencies. ffmpeg comes from PyPI (`imageio-ffmpeg`) |

## Rules

- This repository is private and must stay private. Fixtures and run outputs contain children's photos.
- Runs push only to `claude/run-*` branches. `main` changes only by hand.
- In production, job outputs go to storage through one-time upload URLs, never into git. Committing outputs to a
  branch is for proof runs only.
