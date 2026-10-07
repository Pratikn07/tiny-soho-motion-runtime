"""Render one slide's text animation from its plan, over the text-free plate. Fast, CPU only, no sound.

    python3 tools/render.py work/slide-03/plan.json            # full clip
    python3 tools/render.py work/slide-03/plan.json --stills    # frame sheet + key stills only (seconds)
    python3 tools/render.py work/slide-03/plan.json --frames 1.6,1.75,1.9   # exact frames, e.g. mid-motion

Writes into work/<name>/: preview.mp4, frames.jpg (a still every 0.5 s), motion.jpg (five frames across every
animated cue, cropped to its words), first.png (frame 0), last.png and
layout.json (where every word landed, used by tools/check.py) and text-layer.png (the settled text and logo on
transparency, for the app's finishing step).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import shutil

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "brand" / "fonts"
LOGOS = {"wordmark": ROOT / "brand" / "logo" / "tiny-soho-wordmark.png",
         "lockup": ROOT / "brand" / "logo" / "tiny-soho-lockup.png"}
FPS = 30
COCOA, ROSE = (50, 23, 8), (185, 94, 86)

# Brand type roles. Source Serif 4 axes are [wght, opsz]; DM Sans axes are [opsz, wght].
ROLES = {
    "display": ("InstrumentSerif-Regular.ttf", None, 0.0, True),
    "headline": ("SourceSerif4[opsz,wght].ttf", [600, 36], -0.005, False),
    "heading": ("SourceSerif4[opsz,wght].ttf", [700, 48], -0.01, False),
    "body": ("SourceSerif4[opsz,wght].ttf", [450, 16], 0.0, False),
    "eyebrow": ("SourceSerif4[opsz,wght].ttf", [600, 20], 0.3, True),
    "label": ("DMSans[opsz,wght].ttf", [14, 600], 0.14, True),
}
ENTRANCES = {"none", "fade", "rise", "snap", "slow", "spring", "stamp", "pop", "slide-left", "slide-right", "drop"}
ACCENTS = {"droop", "pulse", "nudge", "wiggle", "hop", "tilt"}


def font(role, size):
    file, axes, _, _ = ROLES[role]
    f = ImageFont.truetype(str(FONTS / file), max(1, round(size)))
    if axes:
        f.set_variation_by_axes(axes)
    return f


def clamp01(x):
    return max(0.0, min(1.0, x))


def out_quart(t):
    return 1 - (1 - clamp01(t)) ** 4


def out_cubic(t):
    return 1 - (1 - clamp01(t)) ** 3


def in_cubic(t):
    return clamp01(t) ** 3


def in_out_sine(t):
    return 0.5 - 0.5 * math.cos(math.pi * clamp01(t))


def out_bounce(t):
    """Falls and bounces twice, settling at 1."""
    t = clamp01(t)
    if t < 0.55:
        return (t / 0.55) ** 2
    if t < 0.82:
        u = (t - 0.685) / 0.135
        return 1 - 0.12 * (1 - u * u)
    u = (t - 0.91) / 0.09
    return 1 - 0.035 * (1 - min(1.0, u * u))


def out_back(t, s=2.2):
    t = clamp01(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


# ------------------------------------------------------------------ layout

def ink_box(text, role, size):
    f = font(role, size)
    track = ROLES[role][2] * size
    if not track:
        return f.getbbox(text, anchor="ls")
    x, top, bottom, right = 0.0, 0, 0, 0
    for ch in text:
        b = f.getbbox(ch, anchor="ls")
        top, bottom, right = min(top, b[1]), max(bottom, b[3]), max(right, x + b[2])
        x += f.getlength(ch) + track
    return (0, top, right, bottom)


def advance(text, role, size):
    f = font(role, size)
    track = ROLES[role][2] * size
    return f.getlength(text) + track * max(0, len(text) - 1) if track else f.getlength(text)


def line_words(line):
    role = line.get("role", "body")
    caps = ROLES[role][3]
    words = []
    for run in line["runs"]:
        for w in run["text"].split():
            words.append({"text": w.upper() if caps else w, "rose": bool(run.get("rose"))})
    return words


def layout(plan, canvas):
    """Place every word. Size fits the original lettering height unless the plan sets `size`; the line keeps its
    original left edge (or centre/right with `align`) and vertical centre unless the plan sets `x`/`y`."""
    placed = []
    for li, line in enumerate(plan["lines"]):
        role = line.get("role", "body")
        words = line_words(line)
        text = " ".join(w["text"] for w in words)
        x0, y0, x1, y1 = line["box"]
        if line.get("size"):
            size = float(line["size"])
        else:
            b = ink_box(text, role, 200)
            size = 200 * (y1 - y0) / max(1, b[3] - b[1])
            # Never wider than the original line by more than 6%, so text stays where the designer put it.
            width = advance(text, role, size)
            if width > (x1 - x0) * 1.06:
                size *= (x1 - x0) * 1.06 / width
        f = font(role, size)
        track = ROLES[role][2] * size

        def prefix_width(chunk):
            # Width of the line up to a point, measured the way the whole line would be typeset, so word gaps and
            # kerning match one-piece setting. Tracked roles add their letter spacing to every character, spaces
            # included, so word gaps grow with the tracking.
            if not track:
                return f.getlength(chunk)
            return sum(f.getlength(ch) + track for ch in chunk)

        total = prefix_width(text) - (track if track else 0)
        align = line.get("align", "left")
        if "x" in line:
            x = float(line["x"])
        elif align == "center":
            x = (x0 + x1) / 2 - total / 2
        elif align == "right":
            x = x1 - total
        else:
            x = x0
        b = ink_box(text, role, size)
        baseline = float(line["y"]) if "y" in line else (y0 + y1) / 2 - (b[1] + b[3]) / 2
        pos = 0
        for wi, w in enumerate(words):
            start = text.index(w["text"], pos)
            pos = start + len(w["text"])
            wx = x + prefix_width(text[:start])
            wb = ink_box(w["text"], role, size)
            placed.append({"line": line["id"], "li": li, "wi": wi, "text": w["text"], "rose": w["rose"],
                           "role": role, "size": size, "x": wx, "baseline": baseline,
                           "box": [wx + wb[0], baseline + wb[1], wx + wb[2], baseline + wb[3]]})
    return placed


def sprite(word, pad=26):
    f = font(word["role"], word["size"])
    color = ROSE if word["rose"] else COCOA
    track = ROLES[word["role"]][2] * word["size"]
    b = ink_box(word["text"], word["role"], word["size"])
    w, h = int(b[2] - b[0]) + pad * 2, int(b[3] - b[1]) + pad * 2
    im = Image.new("RGBA", (w, h), color + (0,))
    d = ImageDraw.Draw(im)
    ox, oy = pad - b[0], pad - b[1]
    if track:
        x = ox
        for ch in word["text"]:
            d.text((x, oy), ch, font=f, fill=color + (255,), anchor="ls")
            x += f.getlength(ch) + track
    else:
        d.text((ox, oy), word["text"], font=f, fill=color + (255,), anchor="ls")
    return np.asarray(im).astype(np.float32) / 255.0, (ox, oy)


# ------------------------------------------------------------------ timing

def schedule(plan, placed):
    """Attach entrance and accent cues to words. Unlisted words appear with the line's first cue, or at 0."""
    for w in placed:
        w["enter"] = {"effect": "none", "at": 0.0, "dur": 0.0}
        w["accents"] = []
    by_line = {}
    for w in placed:
        by_line.setdefault(w["line"], []).append(w)
    for cue in plan.get("motion", []):
        ws = by_line.get(cue["line"], [])
        if "words" in cue and cue["words"] != "all":
            a, b = cue["words"]
            ws = ws[a:b]
        eff = cue["effect"]
        for k, w in enumerate(ws):
            at = float(cue.get("at", 0)) + k * float(cue.get("stagger", 0))
            if eff in ENTRANCES:
                w["enter"] = {"effect": eff, "at": at, "dur": float(cue.get("dur", 0.45)),
                              "amount": cue.get("amount")}
            elif eff in ACCENTS:
                w["accents"].append({"effect": eff, "at": at, "dur": float(cue.get("dur", 0.55)),
                                     "amount": cue.get("amount")})
            else:
                raise SystemExit(f"unknown effect {eff!r}; entrances {sorted(ENTRANCES)}, accents {sorted(ACCENTS)}")


def enter_state(e, t):
    """(alpha, dx, dy, scale, rot, blur) for an entrance."""
    if e["effect"] == "none":
        return 1.0, 0, 0, 1, 0, 0
    p = (t - e["at"]) / max(1e-6, e["dur"])
    if p <= 0:
        return None
    k = out_quart(p)
    amt = e.get("amount")
    if e["effect"] == "fade":
        return k, 0, 0, 1, 0, 0
    if e["effect"] == "rise":
        return k, 0, (amt or 22) * (1 - k), 1, 0, 3.0 * max(0, 1 - p / 0.6)
    if e["effect"] == "slow":
        return k, 0, (amt or 16) * (1 - k), 1, 0, 4.0 * max(0, 1 - p / 0.7)
    if e["effect"] == "snap":
        return out_cubic(p * 1.4), 0, (amt or 30) * (1 - k), 1, 0, 0
    if e["effect"] == "spring":
        s = 0.55 + 0.45 * out_back(p)
        return clamp01(p * 2.5), 0, (amt or 34) * (1 - out_back(p)), s, 0, 0
    if e["effect"] == "stamp":
        q = clamp01(p / 0.3)
        s = (amt or 1.35) - ((amt or 1.35) - 1) * in_cubic(q) if q < 1 else 1.0
        return clamp01(p * 5), 0, 0, s, -6 * (1 - in_cubic(q)), 0
    if e["effect"] == "pop":
        return clamp01(p * 3), 0, 0, 0.9 + 0.1 * out_back(p, 1.4), 0, 0
    if e["effect"] == "drop":
        # Falls in from above and bounces as it lands, like a toy dropped on the floor.
        return clamp01(p * 4), 0, -(amt or 60) * (1 - out_bounce(p)), 1, 0, 0
    if e["effect"] in ("slide-left", "slide-right"):
        sign = -1 if e["effect"] == "slide-left" else 1
        return k, sign * (amt or 28) * (1 - k), 0, 1, 0, 3.0 * max(0, 1 - p / 0.6)
    raise ValueError(e["effect"])


def accent_offset(w, t):
    """Extra (dx, dy, scale, rot) from accents such as the droop."""
    dx = dy = rot = 0.0
    scale = 1.0
    for a in w["accents"]:
        p = (t - a["at"]) / max(1e-6, a["dur"])
        if p <= 0:
            continue
        amt = a.get("amount") or 1.0
        if a["effect"] == "droop":
            # Sag with a small settle bounce; later words in the phrase lean more.
            q = min(p, 1.0)
            k = 1 - math.cos(q * math.pi * 1.5) * math.exp(-q * 4) if q < 1 else 1.0
            lean = (7 + 4 * (w["wi"] % 2)) * amt
            dx += 3 * k
            dy += (9 + 6 * (w["wi"] % 2)) * amt * k
            rot -= lean * k
        elif a["effect"] == "pulse" and p < 1:
            scale *= 1 + 0.14 * amt * math.sin(math.pi * p)
        elif a["effect"] == "nudge" and p < 1:
            dx += 10 * amt * math.sin(math.pi * p) * math.exp(-p * 2)
        elif a["effect"] == "wiggle" and p < 1:
            # A quick no-no shake that dies away: protest, refusal, a tiny tantrum.
            shake = math.sin(p * 4 * math.pi) * (1 - p)
            rot += 11 * amt * shake
            dx += 4 * amt * shake
        elif a["effect"] == "hop" and p < 1:
            # One happy bounce straight up and back down.
            dy -= 16 * amt * math.sin(math.pi * p)
        elif a["effect"] == "tilt":
            # Leans over and stays leaning: confusion, a question, "wait, what?".
            rot += 6 * amt * out_back(min(p, 1.0), 1.6)
    return dx, dy, scale, rot


# ------------------------------------------------------------------ compositing

def blit(canvas, spr, x, y, alpha):
    h, w = spr.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.shape[1], x + w), min(canvas.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[:, :, 3:4] * alpha
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - a) + s[:, :, :3] * 255.0 * a


def draw(canvas, w, t):
    st = enter_state(w["enter"], t)
    if st is None:
        return
    alpha, dx, dy, scale, rot, blur = st
    adx, ady, ascale, arot = accent_offset(w, t)
    dx, dy, scale, rot = dx + adx, dy + ady, scale * ascale, rot + arot
    spr, (ox, oy) = w["_sprite"]
    if scale != 1 or rot != 0 or blur > 0.05:
        h, ww = spr.shape[:2]
        m = cv2.getRotationMatrix2D((ww / 2, h / 2), rot, scale)
        spr = cv2.warpAffine(spr, m, (ww, h), flags=cv2.INTER_CUBIC)
        if blur > 0.05:
            spr = cv2.GaussianBlur(spr, (0, 0), blur)
        spr = np.clip(spr, 0, 1)
    fx, fy = w["x"] - ox + dx, w["baseline"] - oy + dy
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    sx, sy = fx - ix, fy - iy
    if sx > 1e-3 or sy > 1e-3:
        h, ww = spr.shape[:2]
        spr = cv2.warpAffine(spr, np.float32([[1, 0, sx], [0, 1, sy]]), (ww, h), flags=cv2.INTER_LINEAR)
    blit(canvas, spr, ix, iy, alpha)


def camera(frame, plan, t, dur):
    """The photo stays still: the video model animates the scene later. A camera move only when a plan asks for one
    with `"camera": {"allow": true, ...}`, which the skill does not do."""
    cam = plan.get("camera") or {}
    if not cam.get("allow"):
        return frame
    s0, s1 = float(cam.get("from", 1.0)), float(cam.get("to", 1.03))
    fx, fy = cam.get("focus", [0.5, 0.5])
    h, w = frame.shape[:2]
    s = s0 + (s1 - s0) * in_out_sine(t / dur)
    cx, cy = fx * w, fy * h
    tx = min(0.0, max(w - s * w, cx - s * cx))
    ty = min(0.0, max(h - s * h, cy - s * cy))
    return cv2.warpAffine(frame, np.float32([[s, 0, tx], [0, s, ty]]), (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REFLECT)


def ffmpeg_bin():
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg  # pip install imageio-ffmpeg ships a static ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def motion_events(plan, placed):
    """Every cue that moves something, with the words it touches and when it starts and settles."""
    by_line = {}
    for w in placed:
        by_line.setdefault(w["line"], []).append(w)
    events = []
    for cue in plan.get("motion", []):
        if cue["effect"] == "none":
            continue
        words = by_line.get(cue["line"], [])
        if "words" in cue and cue["words"] != "all":
            a, b = cue["words"]
            words = words[a:b]
        if not words:
            continue
        start = float(cue.get("at", 0))
        default = 0.55 if cue["effect"] in ACCENTS else 0.45
        end = start + float(cue.get("dur", default)) + float(cue.get("stagger", 0)) * (len(words) - 1)
        box = [min(w["box"][0] for w in words), min(w["box"][1] for w in words),
               max(w["box"][2] for w in words), max(w["box"][3] for w in words)]
        label = " ".join(w["text"] for w in words)
        events.append({"label": f'{cue["line"]} "{label[:40]}" {cue["effect"]} {start:.2f}-{end:.2f}s',
                       "start": start, "end": end, "box": box})
    return events


def main():
    args = sys.argv[1:]
    plan_file = Path(args[0])
    stills_only = "--stills" in args
    frame_times = [float(v) for v in args[args.index("--frames") + 1].split(",")] if "--frames" in args else None
    plan = json.loads(plan_file.read_text())
    out = plan_file.parent
    plate = cv2.cvtColor(cv2.imread(str(out / "plate.png")), cv2.COLOR_BGR2RGB).astype(np.float32)
    h, w = plate.shape[:2]
    source_size = (w, h)  # text-layer.png must match plate.png, which keeps the slide's own size.
    if w % 2 or h % 2:
        plate = cv2.resize(plate, (w // 2 * 2, h // 2 * 2))
        h, w = plate.shape[:2]
    dur = float(plan.get("duration", 6.0))
    placed = layout(plan, (w, h))
    schedule(plan, placed)
    for word in placed:
        word["_sprite"] = sprite(word)
    logo = None
    brand = plan.get("brand", True)
    if brand:
        # true or "wordmark": the name only. "lockup": the name with the heart and rules underneath.
        im = Image.open(LOGOS["lockup" if brand == "lockup" else "wordmark"]).convert("RGBA")
        im = im.crop(im.getchannel("A").getbbox())
        im = im.resize((270, round(im.height * 270 / im.width)), Image.LANCZOS)
        logo = np.asarray(im).astype(np.float32) / 255.0

    def frame_at(t):
        f = plate.copy()
        for word in placed:
            draw(f, word, t)
        f = camera(f, plan, t, dur)
        if logo is not None:
            blit(f, logo, (w - logo.shape[1]) // 2, 60, 1.0)
        return np.clip(f, 0, 255).astype(np.uint8)

    if frame_times is not None:
        written = []
        for t in frame_times:
            dest = out / f"frame-{t:.2f}.png"
            Image.fromarray(frame_at(t)).save(dest)
            written.append(str(dest))
        print(json.dumps({"frames": written}))
        return

    (out / "layout.json").write_text(json.dumps({
        "size": [w, h], "duration": dur,
        "words": [{k: v for k, v in word.items() if not k.startswith("_")} for word in placed]}, indent=1))
    # text-layer.png: the settled text and logo on transparency, full canvas, for the app's finishing step.
    # Rendered over black and over white; alpha comes from the difference, colour from the black render.
    def settled_on(value):
        f = np.full_like(plate, value)
        for word in placed:
            draw(f, word, dur)
        if logo is not None:
            blit(f, logo, (w - logo.shape[1]) // 2, 60, 1.0)
        return f
    on_black, on_white = settled_on(0.0), settled_on(255.0)
    alpha = np.clip(1 - (on_white - on_black).mean(axis=2, keepdims=True) / 255.0, 0, 1)
    rgb = np.where(alpha > 1e-3, on_black / np.maximum(alpha, 1e-3), 0)
    layer = np.concatenate([np.clip(rgb, 0, 255), alpha * 255], axis=2).astype(np.uint8)
    text_layer = Image.fromarray(layer, "RGBA")
    if text_layer.size != source_size:  # Odd-sized slide: the video frames were trimmed to even, the layer is not.
        text_layer = text_layer.resize(source_size, Image.LANCZOS)
    text_layer.save(out / "text-layer.png")

    Image.fromarray(frame_at(0.0)).save(out / "first.png")
    Image.fromarray(frame_at(dur - 1 / FPS)).save(out / "last.png")
    times = [i * 0.5 for i in range(int(dur / 0.5) + 1) if i * 0.5 < dur]
    tw, th = w // 4, h // 4
    cols = 6
    rows = (len(times) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 18)), "white")
    dd = ImageDraw.Draw(sheet)
    for k, t in enumerate(times):
        im = Image.fromarray(frame_at(t)).resize((tw, th), Image.LANCZOS)
        x, y = (k % cols) * tw, (k // cols) * (th + 18)
        sheet.paste(im, (x, y + 18))
        dd.text((x + 4, y + 3), f"{t:.1f}s", fill="black")
    sheet.save(out / "frames.jpg", quality=88)

    # motion.jpg: one row per cue, five frames from just before it starts to just after it settles, cropped to the
    # words it moves (with room around them for collisions). This shows what the 0.5 s sheet skips over.
    events = motion_events(plan, placed)[:14]
    if events:
        cell_h, pad, label_h = 150, 70, 20
        rows = []
        for ev in events:
            x0, y0, x1, y1 = ev["box"]
            # At least 360 px wide, so a single short word still shows its neighbours.
            grow = max(0, 360 - (x1 - x0 + 2 * pad)) / 2
            box = (max(0, int(x0 - pad - grow)), max(0, int(y0 - pad)), min(w, int(x1 + pad + grow)), min(h, int(y1 + pad)))
            span = max(0.05, ev["end"] - ev["start"])
            # Every effect eases out, so the action is early in the cue: sample densely at the start.
            ts = ([max(0.0, ev["start"] - 0.04)] + [ev["start"] + span * f for f in (0.08, 0.2, 0.45)]
                  + [min(dur - 1 / FPS, ev["end"] + 0.06)])
            crops = []
            for t in ts:
                crop = Image.fromarray(frame_at(t)).crop(box)
                scale = cell_h / crop.height
                crops.append((t, crop.resize((max(1, int(crop.width * scale)), cell_h), Image.LANCZOS)))
            rows.append((ev["label"], crops))
        width = max(sum(c.width for _, c in crops) + 6 * len(crops) for _, crops in rows)
        msheet = Image.new("RGB", (min(width, 2400), len(rows) * (cell_h + label_h + 8)), "white")
        dm = ImageDraw.Draw(msheet)
        for r, (label, crops) in enumerate(rows):
            y = r * (cell_h + label_h + 8)
            dm.text((4, y + 3), label, fill="black")
            x = 0
            for t, crop in crops:
                msheet.paste(crop, (x, y + label_h))
                dm.text((x + 3, y + label_h + 3), f"{t:.2f}s", fill=(200, 0, 0))
                x += crop.width + 6
        msheet.save(out / "motion.jpg", quality=88)

    result = {"layout": str(out / "layout.json"), "frames": str(out / "frames.jpg"),
              "first": str(out / "first.png"), "last": str(out / "last.png")}
    if events:
        result["motion"] = str(out / "motion.jpg")
    if not stills_only:
        mp4 = out / "preview.mp4"
        cmd = [ffmpeg_bin(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(mp4)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(int(round(dur * FPS))):
            proc.stdin.write(frame_at(i / FPS).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise SystemExit("ffmpeg failed")
        result["video"] = str(mp4)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
