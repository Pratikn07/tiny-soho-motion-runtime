"""Automatic checks on a rendered slide. Run after tools/render.py.

    python3 tools/check.py work/slide-03/plan.json

Prints JSON with `pass` and a list of `problems`. Passing these checks is necessary, not sufficient: you still have
to look at frames.jpg, first.png and last.png.
"""
import json
import sys
from pathlib import Path


def overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def area(a):
    return max(0, a[2] - a[0]) * max(0, a[3] - a[1])


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
    accents = [a for wd in words for a in wd["accents"]]
    if len({(wd['line']) for wd in words if wd['accents']}) > 2:
        problems.append("accents on more than 2 lines; keep gags to one or two phrases")
    print(json.dumps({"pass": not problems, "problems": problems, "last_text_in_s": round(last_in, 2),
                      "accent_count": len(accents)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
