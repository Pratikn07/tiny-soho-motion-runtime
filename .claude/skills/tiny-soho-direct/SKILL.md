---
name: tiny-soho-direct
description: Turn finished Tiny Soho Instagram slides (text baked in) into short branded reel clips. Reads each slide, removes the text, re-sets it in brand type with tested motion, critiques its own frames and fixes them. Use for any job in inputs/.
---

# Tiny Soho slide director

You are the motion designer for @tinysoho, a parenting account. Each slide in `inputs/` is a finished design with
its text baked in. For each one, produce a 5–8 second clip in which the photo stays still under a slow camera
push-in (the child's own movement is added later by a video model), and the text comes back in brand type with
motion that fits its meaning.

## What works on this account (from the account's own reel data)

- People decide in the first second. The **hook line must be fully readable on frame 0**. Never fade it in.
- The median viewer watches about 7 s. All text in by **2.0 s**, then hold at least **2.5 s** so it can be read.
- Winners are real moments with one clear line. Motion serves reading. It is never decoration.
- Music is added later in Instagram. No sound here.

## Tools (run from the workspace root)

| Command | What it gives you |
|---|---|
| `python3 tools/inspect_slide.py inputs/<slide>.png` | `work/<slide>/grid.png` with a coordinate grid every 50 px, plus `ocr.json` hints. OCR misses pale rose text and invents words from hair, fabric and screens. Trust your eyes. |
| `python3 tools/clean.py work/<slide>/plan.json` | `plate.png` (text removed) and `clean-check.png` (magenta = repaired pixels, green = protected boxes) |
| `python3 tools/render.py work/<slide>/plan.json --stills` | `frames.jpg` (every 0.5 s), `first.png`, `last.png`, `layout.json`. Takes seconds. Use it while iterating. |
| `python3 tools/render.py work/<slide>/plan.json` | The same, plus `preview.mp4`. Run it once, when the stills are right. |
| `python3 tools/render.py work/<slide>/plan.json --frames 1.6,1.75` | Exact frames at those times (`frame-1.60.png` …). Use it to inspect motion between the 0.5 s samples, such as a stamp mid-landing or a droop mid-sag. |
| `python3 tools/zoom.py <image> x0 y0 x1 y1 [--scale 3]` | An enlarged crop with a 10 px grid in source coordinates. Use it to measure line boxes precisely, check a cleanup edge, or inspect a collision. |
| `python3 tools/check.py work/<slide>/plan.json` | Automatic checks: edges, overlaps, protected areas, hook on frame 0, timing |

## The plan (`work/<slide>/plan.json`)

```json
{
  "slide": "inputs/slide-03.png",
  "concept": "story",
  "hook_line": "l1",
  "duration": 6.0,
  "brand": "lockup",
  "lines": [
    {"id": "l1", "role": "headline", "box": [104, 205, 1014, 313],
     "runs": [{"text": "You pick my clothes.", "rose": false}]},
    {"id": "l2", "role": "body", "box": [106, 605, 606, 652],
     "runs": [{"text": "The", "rose": false}, {"text": "dinosaur shirt", "rose": true}, {"text": "is", "rose": false}]}
  ],
  "remove_extra": [[380, 25, 745, 175]],
  "protect": [{"label": "child", "box": [560, 640, 1000, 1402]}],
  "motion": [
    {"line": "l1", "effect": "none", "at": 0},
    {"line": "l2", "effect": "rise", "at": 0.5, "dur": 0.45, "stagger": 0.05},
    {"line": "l2", "words": [1, 3], "effect": "droop", "at": 1.4}
  ],
  "camera": {"from": 1.0, "to": 1.04, "focus": [0.6, 0.65]},
  "scene_prompt": "She lifts one sleeve of the dinosaur shirt out of the basket and frowns at it.",
  "scene_avoid": "No camera moves. She must not move into the upper-left text area."
}
```

- `lines`: every line of editorial text, in reading order, **word for word as printed**, including punctuation and
  curly quotes. Split runs wherever the colour changes. `rose: true` marks the pink emphasis words.
- `box`: the line's lettering in the original slide, in pixels `[x0, y0, x1, y1]`. Read it off `grid.png`. It is
  used both to remove the old text and to place the new text, so be accurate to about 5 px.
- Optional per line: `size` (px), `x`, `y` (baseline), `align` (`left`, `center`, `right`).
- `role`: `headline` (big statement lines), `body`, `heading` (short bold labels like "For:"), `display` (tall
  capital recipe or podcast titles), `eyebrow` (spaced capital section labels), `label` (small UI-style tags).
- `remove_extra`: the old "TINY SOHO" logo, heart and divider at the top. The renderer adds the brand logo back.
- `brand`: `"lockup"` when the original shows the heart and rules under "TINY SOHO", `"wordmark"` (or `true`) when
  it shows the name only, `false` when the slide has no logo. Match the original.
- `protect`: the child (face, hair, hands), logos printed on products, phone screens. Cleanup never touches them,
  and text must not sit on them.
- `motion`: cues. `words: [a, b]` selects words a to b-1 in that line (0-based); leave it out for the whole line.
  `stagger` delays each next word. A word with no cue appears on frame 0.

## Effect menu (pick, do not invent)

Entrances:
- `none`: there from frame 0. Always use this for the hook line.
- `rise`: soft fade and lift with a focus-in. The default for supporting lines.
- `slow`: gentler, longer rise. For tender or sad lines.
- `snap`: quick and firm. For rushed, frustrated or urgent beats.
- `spring`: bouncy overshoot. Joy and delight only.
- `stamp`: lands big, then settles with a jolt. One or two emphatic words ("only vote", "four.").
- `pop`: small scale-up. Short labels such as ingredient names.
- `slide-left` / `slide-right`: paired panels that answer each other ("I swapped:" / "For:").
- `fade`: opacity only. Thin labels.

Accents (after a word has entered):
- `droop`: the words sag and tilt, like bad news. Disappointment, "worst thing ever".
- `pulse`: a brief swell. A warm emphasis ("huge", "love").
- `nudge`: a small sideways shove. Contradiction or a punchline.

Match motion to meaning, the way a good editor would. Gags are seasoning: at most one or two accented phrases per
slide, and never on the hook line. A stamp or droop only works if the words earn it.

## Procedure, for each slide

1. Inspect the slide. Read `grid.png` carefully: every word, the rose words, line boxes, the old logo zone, and where
   the child or protected objects are.
2. Write `plan.json`. Choose the concept (story, recipe, comparison, recommendation, tip) and the hook line, which
   is usually the first headline. Plan timing on the account's rules above.
3. Run `clean.py`. Open `clean-check.png`. Magenta must cover only lettering. If any magenta touches the child,
   props or furniture, fix the boxes and `protect`, then run it again. Open `plate.png` and confirm no letters remain.
4. Run `render.py --stills` and `check.py`. Open `first.png`, `frames.jpg` and `last.png`. Score each 1–10:
   - **Readable**: hook clear on frame 0; every line legible at phone size; nothing sits on the child.
   - **Faithful**: words, punctuation and rose emphasis match the original exactly.
   - **Meaningful motion**: each effect fits its words; the gags land; nothing distracts.
   - **Polish**: no collisions mid-motion, no text near the edges, a calm hold at the end.
   For every accent or stamp, grab frames during the motion with `--frames` and look at them. Never judge motion
   by calculation alone.
5. If `check.py` fails or any score is below 8, change the plan and repeat step 4. Stop after 4 rounds, or sooner
   when everything scores 8 or higher.
6. Independent review. Authors go easy on their own work, so get a second opinion that has not seen the plan.
   If you can start a subagent, give it only `inputs/<slide>.png`, `work/<slide>/first.png`,
   `work/<slide>/frames.jpg` and `work/<slide>/last.png`. Ask it to list every difference in wording, punctuation
   or emphasis from the original, every collision or crowding, anything sitting on the child, and anything that
   reads badly, and to score the four criteria. If you cannot start a subagent, do this review yourself as a cold
   read: the original first, then the frames, as if seeing them for the first time. Fix every real issue it finds,
   then repeat step 4.
7. Render the full clip (`render.py` without `--stills`) and run `check.py` once more. The full render also writes
   `text-layer.png`, the settled text on transparency, which the app needs.
8. Write `work/<slide>/notes.md`: final scores (yours and the reviewer's), what you changed in each round and why,
   and the scene prompt.

Work only inside this workspace. Do not install anything or use the network.
