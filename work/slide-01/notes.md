# slide-01 — "In the car I stare out the window."

**Concept:** story. **Hook:** l1 + l2 ("In the car I stare / out the window."), both on frame 0, no entrance.
**Clip:** 7.0 s, all text in by 1.98 s, 5.0 s hold. Lockup logo. Gentle push-in 1.00 → 1.03.

## Final scores

| Criterion | Mine (round 4) | Reviewer (cold read of round 3) |
|---|---|---|
| Readable | 9 | 9 |
| Faithful | 9 | 9 |
| Meaningful motion | 8 | 7 |
| Polish | 8 | 8 |

`check.py`: pass, no problems (last text in at 1.98 s, no accents, stamp is an entrance).

## Motion

| Time | Line | Effect | Why |
|---|---|---|---|
| 0.00 | l1–l2 "In the car I stare / out the window." | none | The hook must be readable on frame 0 |
| 0.30 | l3 "I’m" | rise | Supporting line |
| 0.42 | l3 "not" | snap | A firm, slightly defensive denial |
| 0.50 | l3 "ignoring you." | rise | |
| 0.70 | l4 "I’m still waking up." | slow | Sleepy and tender |
| 0.95 | l5 "My brain needs" | rise | |
| 1.18 | l6 "twenty minutes" | rise, tight stagger | Lands as one phrase, after "needs" has settled |
| 1.30 | l7 "and you gave me" | rise | |
| 1.72 | l7 "four." | stamp (amount 1.15, 0.26 s) | The punchline, after a short beat |

## Rounds

1. **Round 1.** Box-fitted sizes and camera focus [0.66, 0.58] → 1.035. `check.py` passed. Self scores: R8 F8 M8 P7.
   - The push-in pulled the headline up to about 37 px under the heart (about 56 px on frame 0).
   - l7 was fitted at 46 px while the other body lines were about 52 px, so it looked smaller.
2. **Round 2.** Fixed sizes: headline 95, body 47.
   - 47 keeps the wider brand serif inside the original line widths. At 52, "four." would run into the hair.
   - Camera focus moved up to [0.62, 0.36] → 1.03, so the logo gap stays at 50 px or more.
   - Frame grabs at 1.62–1.95 s showed the 1.35× stamp on "four." overlapping "me" while "me" was still rising: it read as "mefour.".
3. **Round 3.** Fixed the stamp in two steps:
   - Retimed so "and you gave me" settles before "four." lands after a beat.
   - Reduced the stamp to 1.22. Frames at 1.72–1.76 s still showed the word gap closing (measured minimum 0.3 px), so I reduced it to 1.15 (minimum 4.3 px, settled 10.8 px) and checked the landing frames by eye.
   - Self scores: R9 F9 M8 P8. Sent to the independent review.
4. **Round 4: after the review.**
   - The reviewer found no wording, punctuation or rose errors and nothing on the child.
   - It flagged that the motion was uniform and the rose words had no beat of their own. I gave "not" a snap entrance and set "twenty minutes" to land as one phrase after "needs". I also kept the beat before "four.".
   - It flagged the hook-to-logo gap tightening during the push-in. I moved the camera focus to [0.62, 0.20], level with the headline, so the gap stays at about 54–56 px for the whole clip.
   - Frames at 0.36–0.60, 0.9, 1.2–1.85 s confirmed: no collisions, and the stamp keeps a visible gap from "me".

## Known limits, not changed

- **Rose words are lighter than in the original.** The original sets "not", "still" and "twenty minutes" a little heavier than the body text. The renderer marks emphasis with colour only, so they are regular-weight rose.
- **"four." is close to the hair.** It ends about 20–30 px from the loose hair strands (the original had about 40 px), because the brand serif is wider than the original face. It sits on the wall, not on the child. Shrinking every body line further would cost legibility.
- **The logo sits a little closer to the hook than in the original.** The renderer's lockup is taller and placed lower (fixed at y = 60) than the original logo.

## Scene prompt

> A sleepy toddler in a car seat keeps gazing out the side window in warm morning light. She blinks slowly, her eyelids heavy, and her chest rises with a slow breath; a few loose strands of her messy bun stir faintly. The landscape outside the window drifts by softly out of focus.

**Avoid:** No camera moves, no zoom. She stays seated facing the window; her head, hair and hands must not move left or up into the text area on the upper left. No new people or objects, no talking, no sudden movements.
