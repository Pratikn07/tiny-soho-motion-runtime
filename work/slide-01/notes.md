# slide-01: "In the car I stare out the window."

Concept: **story** (a sleepy toddler's voice). Hook: l1 + l2, the two-line headline, both static from frame 0.
Duration 7.0 s. All text in by 1.91 s, then a 5.1 s hold. Brand: lockup.

## Final scores

| | Readable | Faithful | Meaningful motion | Polish |
|---|---|---|---|---|
| Mine (round 4) | 9 | 9 | 8 | 9 |
| Reviewer 1 (cold, on round 2) | 8 | 9 | 5 | 6 |
| Reviewer 2 (cold, on round 3) | 8 | 9 | 5 | 7 |

Both reviewers found the wording, curly apostrophes, full stops, line breaks and rose emphasis exact. They found no
ghost lettering and nothing on the child.

## Motion

- Headline: `none`. It is there on frame 0, so viewers read it in the first second.
- "I’m not ignoring you.": `rise`, from 0.30 s.
- "I’m still waking up.": `slow`, 0.9 s per word with a 0.1 s stagger. The line drifts out of blur into focus, the way
  eyes open. It is the only slow line, so the contrast is visible.
- "My brain needs" / "twenty minutes" / "and you gave me": `rise`, cascading from 0.95 s to 1.15 s.
- "four.": `stamp` (amount 1.12) at 1.55 s, after a 0.4 s beat with "and you gave me" already settled. The punchline
  lands at about 1.66 s. This is the only gag, and it is not on the hook line.
- Camera: push-in from 1.0 to 1.03, focus [0.3, 0.15], so the text block stays steady under the fixed logo while the
  photo pushes in on the child.

## Rounds

1. First plan: auto line sizes; all body lines `slow`; stamp 1.35 at 1.6 s; push to 1.04 toward the face
   [0.72, 0.6]. `check.py` passed. Seen in the frames:
   - At 1.65 s the scaled "four." touched "me", which was still blurred.
   - Body sizes were uneven: l7 was width-capped at 47 px against about 51 px for the others, and l3 ran to x=604,
     near the hair.
   - The push lifted the headline to within about 31 px of the logo.
   Scores: 8 / 9 / 7 / 6.
2. Fixes:
   - Uniform sizes: headline 93, body 47.
   - Stamp amount cut to 1.2, then to 1.12, after looking at frames 1.62–1.72. The final minimum gap from "me" is
     6 px, measured.
   - Earlier cascade, so "me" settles before "four." lands.
   - Camera focus moved to [0.62, 0.32].
   Scores: 9 / 9 / 8 / 9. Sent for cold review.
3. Reviewer 1 issues, and what I did about each:
   - Every word got the same fade: **fixed**. Body lines now `rise`, the drowsy line is the only `slow` one, and
     "four." keeps its beat and stamp.
   - Layout drifted toward the logo and left edge: **fixed**. Camera focus moved to [0.45, 0.15], which holds the
     headline steady at about 58 px under the logo.
   - "four." 15–25 px from the stray hairs: **fixed**. Body size went to 46, so "four." now ends at x=572, about 30 px
     from the hair.
   - No margin on the 2.0 s rule: **fixed**. The last text is now in at 1.91 s.
   - Logo size and position: **not changeable**. The renderer places the logo; the plan cannot.
   Scores: 9 / 9 / 8 / 9. Sent for a second cold review.
4. Reviewer 2 issues, and what I did about each:
   - Text drifted after 2.0 s against the fixed logo: **fixed**. Push reduced to 1.03 (the renderer's default) with
     focus [0.3, 0.15]. The left edge now moves only from 102 to about 96 px, and the headline top holds at about
     y=216–220.
   - Rushed reveal, and no beat for "four.": **not changed**. Most of this comes from the 0.5 s contact-sheet
     sampling. The beat (1.15–1.55 s), the stamp (1.55–1.66 s) and the slow focus-in all fall between samples, and I
     checked them on exact frames. The 2.0 s rule limits how slow 14 body words can enter.
   - Pale regular-weight rose words: **not changed**. Their colour and weight are set by the brand kit in the
     renderer, not by the plan. Worth raising for the brand kit: a semibold rose for body emphasis would read better
     at phone size.
   Final scores: 9 / 9 / 8 / 9. `check.py` passes. Full render: 7.0 s, 1122×1402, 30 fps.

## Scene prompt (for the video model)

> The sleepy toddler in the car seat keeps gazing out the window, blinks slowly once and lets her head settle a little
> deeper into the seat. Warm morning sunlight drifts softly across her face and a few loose curls stir.

Avoid: No camera moves. She must not turn toward the camera, talk, or move into the upper-left text area. No new
objects or people.
