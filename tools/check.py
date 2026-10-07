"""Automatic checks on a rendered slide. Run after tools/render.py.

    python3 tools/check.py work/slide-03/plan.json

Prints JSON with `pass` and a list of `problems`. Passing these checks is necessary, not sufficient: you still have
to look at frames.jpg, first.png and last.png.
"""
import json
import math
import sys
from pathlib import Path


def overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def area(a):
    return max(0, a[2] - a[0]) * max(0, a[3] - a[1])


PREMIUM = {"none", "fade", "rise", "slow", "slide-left", "slide-right"}
LIFT_LIMIT = {"rise": 30, "slow": 30, "slide-left": 32, "slide-right": 32}


def peak_boxes(words):
    """For each word that grows or turns mid-motion, its box at the biggest moment (matching render.py's effects):
    (word, time, box, what it does). Used to catch a stamp or wiggle running into its neighbour."""
    out = []
    for wd in words:
        x0, y0, x1, y1 = wd["box"]
        cx, cy, hw, hh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        moves = []
        e = wd["enter"]
        if e["effect"] == "stamp":
            moves.append((e["at"], e.get("amount") or 1.35, 6, "grows as it stamps"))
        if e["effect"] == "drop":
            # Fully visible from a quarter of the way in, still about 80% of its fall height up.
            lift = 0.8 * (e.get("amount") or 60)
            out.append((wd, e["at"] + e["dur"] * 0.25, [x0, y0 - lift, x1, y1 - lift], "falls through"))
        for a in wd["accents"]:
            amt = a.get("amount") or 1.0
            if a["effect"] == "pulse":
                moves.append((a["at"] + a["dur"] / 2, 1 + 0.14 * amt, 0, "swells"))
            elif a["effect"] == "wiggle":
                moves.append((a["at"] + a["dur"] / 8, 1.0, 11 * amt * 0.85, "tilts as it wiggles"))
            elif a["effect"] == "tilt":
                moves.append((a["at"] + a["dur"], 1.0, 6 * amt * 1.1, "leans"))
            elif a["effect"] == "droop":
                moves.append((a["at"] + a["dur"], 1.0, (7 + 4 * (wd["wi"] % 2)) * amt, "sags"))
        for t, scale, degrees, why in moves:
            r = math.radians(degrees)
            w2 = scale * (hw * abs(math.cos(r)) + hh * abs(math.sin(r)))
            h2 = scale * (hw * abs(math.sin(r)) + hh * abs(math.cos(r)))
            if w2 > hw * 1.02 or h2 > hh * 1.02:
                out.append((wd, t, [cx - w2, cy - h2, cx + w2, cy + h2], why))
    return out


def main(plan_path):
    plan_file = Path(plan_path)
    plan = json.loads(plan_file.read_text())
    lay = json.loads((plan_file.parent / "layout.json").read_text())
    w, h = lay["size"]
    words = lay["words"]
    problems = []
    dur = lay["duration"]
    if not 5.0 <= dur <= 8.0:
        problems.append(f"duration {dur}s is outside 5-8 s")
    margin = 24
    for wd in words:
        x0, y0, x1, y1 = wd["box"]
        if x0 < margin or y0 < margin or x1 > w - margin or y1 > h - margin:
            problems.append(f"'{wd['text']}' ({wd['line']}) is within {margin}px of the frame edge")
    lines = {}
    for wd in words:
        b = lines.setdefault(wd["line"], list(wd["box"]))
        b[0], b[1], b[2], b[3] = min(b[0], wd["box"][0]), min(b[1], wd["box"][1]), max(b[2], wd["box"][2]), max(b[3], wd["box"][3])
    ids = list(lines)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if overlap(lines[ids[i]], lines[ids[j]]) > 0.04 * min(area(lines[ids[i]]), area(lines[ids[j]])):
                problems.append(f"lines {ids[i]} and {ids[j]} overlap")
    for p in plan.get("protect", []):
        for lid, b in lines.items():
            if overlap(b, p["box"]) > 0.02 * area(b):
                problems.append(f"line {lid} covers protected area '{p['label']}'")
    hook = plan.get("hook_line")
    hook_words = [wd for wd in words if wd["line"] == hook]
    if not hook_words:
        problems.append("hook_line does not name a line id")
    elif any(wd["enter"]["effect"] != "none" and wd["enter"]["at"] > 0.0 for wd in hook_words):
        problems.append(f"hook line {hook} is not fully visible on frame 0")
    last_in = max((wd["enter"]["at"] + wd["enter"]["dur"]) for wd in words) if words else 0
    if last_in > 2.0:
        problems.append(f"last text lands at {last_in:.2f}s; keep all text in by 2.0 s")
    if dur - last_in < 2.5:
        problems.append(f"only {dur - last_in:.2f}s of hold after the last text; keep at least 2.5 s")
    for cue in plan.get("motion", []):
        if cue["effect"] not in PREMIUM:
            problems.append(f"{cue['line']}: '{cue['effect']}' is not in the premium menu (none, fade, rise, slow, "
                            f"slide-left, slide-right); no accents, bounces or jolts")
        elif cue.get("amount") is not None and abs(cue["amount"]) > LIFT_LIMIT.get(cue["effect"], 0) and cue["effect"] != "fade":
            problems.append(f"{cue['line']}: {cue['effect']} amount {cue['amount']} is too big; keep it within "
                            f"{LIFT_LIMIT[cue['effect']]} px")
    accents = [a for wd in words for a in wd["accents"]]
    if len({(wd['line']) for wd in words if wd['accents']}) > 3:
        problems.append("accents on more than 3 lines; keep it to the signature moment, rose words and the hook")
    for wd in words:
        for a in wd["accents"]:
            if a["at"] < wd["enter"]["at"] + wd["enter"]["dur"] - 1e-6:
                problems.append(f"'{wd['text']}' ({wd['line']}) starts its {a['effect']} before it has entered")
            if a["at"] + a["dur"] > 3.2 + 1e-6:
                problems.append(f"'{wd['text']}' ({wd['line']}) {a['effect']} settles at {a['at'] + a['dur']:.2f}s; "
                                f"settle accents by 3.2 s")
    for wd, peak, grown, why in peak_boxes(words):
        for other in words:
            if other is wd or other["enter"]["at"] > peak:
                continue
            if overlap(grown, other["box"]) > 0.03 * area(other["box"]):
                problems.append(f"'{wd['text']}' ({wd['line']}) {why} into '{other['text']}' ({other['line']}) "
                                f"at about {peak:.2f}s")
    last_accent = max((a["at"] + a["dur"] for a in accents), default=0)
    if accents and dur - last_accent < 2.0:
        problems.append(f"only {dur - last_accent:.2f}s of calm hold after the last accent; keep at least 2 s")
    print(json.dumps({"pass": not problems, "problems": problems, "last_text_in_s": round(last_in, 2),
                      "accent_count": len(accents)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
