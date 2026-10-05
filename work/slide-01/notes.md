# slide-01: "In the car I stare out the window."

**Concept:** story, told in the child's voice.

**Hook:** the two headline lines, "In the car I stare / out the window." (`l1` + `l2`). Both are fully set on frame 0 with no entrance.

**Duration:** 7.0 s. All text is in by 1.98 s, followed by a 5.0 s hold.

**Brand:** lockup (heart and rules), as in the original.

## Final scores

| | Self (round 4) | Reviewer 1 (round 2 build) | Reviewer 2 (round 3 build) |
|---|---|---|---|
| Readable | 9 | 8 | 8 |
| Faithful | 9 | 9 | 8 |
| Meaningful motion | 8 | 6 | 7 |
| Polish | 9 | 6 | 7 |

Both reviewers were cold subagents. Each saw only the original, `first.png`, `frames.jpg`, `motion.jpg` and `last.png`, never the plan. Round 4 is the build after reviewer 2's findings. No third review was run, because round 4 was the last allowed round.

## Motion

- **Body lines:** `slow` (blur-to-focus with a soft lift), one after another from 0.2 s.
  - The child is "still waking up", so each line comes into focus the way her eyes do.
  - Cues: `l3` 0.20 s, `l4` 0.50 s, `l5` 0.85 s, `l6` 1.08 s, and "and you gave me" (`l7`, words 0–3) at 1.28 s.
  - The 0.35 s gap between `l4` and `l5` marks the break between the two thoughts.
- **"four.":** `snap` at 1.68 s for 0.30 s. It is the one punchline beat.
  - It comes after "me" has settled, quick and firm against the sleepy cascade, because the joke is being rushed: twenty minutes needed, four given.
- **No accents.** The rose words carry their emphasis in colour. The hook line is never animated.
- **Camera:** push-in from 1.00 to 1.03, with the fixed point at (0.40, 0.30), near the text block.
  - The photo pushes in and the child grows slightly.
  - The text moves only about 10 px left and 6 px up over the clip, against the fixed logo.

## Rounds

1. **First plan.**
   - The original slow cascade ran from 0.35 s to about 1.9 s.
   - `stamp` on "four." at 1.55 s, scale 1.35.
   - Camera 1.00→1.04, focus (0.75, 0.60).
   - **Exact frames at 1.57–1.70 s:** the stamp ran "four." into "me", which was itself still blurred and fading in. It read "mefour.".
   - **Last frame:** the push-in carried the headline up to about 37 px from the logo heart.
   - **Self-scores:** Readable 9, Faithful 10, Motion 7, Polish 6.
2. **Stamp and camera.**
   - Pulled the cascade earlier so "and you gave me" settles before the stamp.
   - Stamp at 1.60 s, scale cut to 1.15.
   - Camera 1.00→1.035, focus (0.72, 0.45).
   - **Measured:** the gap between "me" and "four." stayed open but narrowed from 15 px to 8 px at 1.67 s.
   - **Self-scores:** 9 / 10 / 8 / 8.
   - **Reviewer 1** scored it 8 / 9 / 6 / 6 and found:
     - The stamp still reads "mefour." around 1.65 s, and a slam is loud for a sleepy piece.
     - The cascade overlaps too much, with four lines blurred at once around 1.1 s.
     - The text drifts against the fixed logo during the hold.
     - The brand headline is about 35 px wider than the original, so the period of "window." sits on the pillar shading.
     - Clearance to the hair is tighter than in the original.
3. **Fixes for reviewer 1.**
   - Set every line's `size` so its width matches the original box. The headlines are 90.5 px and the body lines 44.7–49.4 px, keeping the original's proportions.
   - Shortened the cues (0.40–0.45 s) so at most two lines are in motion at once.
   - Replaced the stamp with a `snap`. It has no horizontal growth, and the gap holds at 15 px through the landing.
   - Camera 1.00→1.03, focus (0.60, 0.30).
   - **Self-scores:** 9 / 10 / 8 / 9.
   - **Reviewer 2** scored it 8 / 8 / 7 / 7. It found no wording, rose or collision issues and nothing on the child, and flagged:
     - The text still drifts about 18 px left against the fixed logo.
     - The slow/snap contrast is hard to notice.
     - The cues still overlap.
     - "not" and "still" get no beat of their own, and rose reads lighter than the cocoa text.
4. **Fixes for reviewer 2.**
   - Moved the camera's fixed point onto the text block, focus (0.40, 0.30). The drift is now 10 px left and 6 px up.
   - Lengthened the beat between "me" settling and "four." snapping in (snap at 1.68 s).
   - **Measured:** the gap between "me" and "four." holds at 14 px through the snap.
   - **Self-scores:** 9 / 9 / 8 / 9.

## Review points not changed, and why

- **Overlapping cascade.** The account's rule is that all text is in by 2.0 s with the hook readable first. Five body lines in that window must overlap a little. Each line is readable about 0.2 s after it starts, and the 5 s hold is where people read.
- **No beat for "not" and "still".** Accents on them would be decoration. The skill allows at most one or two gags, and the punchline already has one. The rose colour carries the emphasis, as in the original.
- **Rose reads lighter than in the original.** In the original the rose words were set slightly heavier. The renderer sets every body word at one brand weight, so a plan can't change this.
- **Faint clean-up mottling** (about 6–8 grey levels, along the old text rows). It can't be seen in normal viewing and is covered by the new text by about 2 s.

## Clean-up

- **Magenta covers only lettering.**
- **Areas:** the old "TINY SOHO" lockup, heart and rules at [420, 40, 705, 145], plus the seven line boxes.
- **Child protected** at [585, 490, 1015, 1300]. Nothing touched her hair, face or the seat.
- **No ghost letters** at 2× zoom.

## Scene prompt (for the video model)

> She stays slumped in the car seat, gazing out the window. Her eyelids blink slowly and heavily, a few loose curls lift in the warm morning light, and she lets out a small sleepy breath.

**Avoid:** No camera moves. She must not turn toward the camera or lean into the upper-left text area. Keep the bunny, blanket and harness still. No new objects or people.
