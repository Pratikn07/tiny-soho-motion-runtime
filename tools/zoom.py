"""Zoom into part of an image with a fine coordinate grid, to measure boxes or inspect details.

    python3 tools/zoom.py inputs/slide-01.png 80 180 720 560          # region x0 y0 x1 y1 of the source
    python3 tools/zoom.py work/slide-01/frame-1.80.png 80 600 720 920 --scale 3

Writes work/zoom/<image>-<x0>-<y0>-<x1>-<y1>.png. Grid lines every 10 px (labelled every 50 px), in the source
image's own coordinates.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def main(argv):
    path = Path(argv[0])
    x0, y0, x1, y1 = (int(v) for v in argv[1:5])
    scale = int(argv[argv.index("--scale") + 1]) if "--scale" in argv else 2
    im = Image.open(path).convert("RGB")
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width, x1), min(im.height, y1)
    crop = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    for x in range((x0 // 10 + 1) * 10, x1, 10):
        major = x % 50 == 0
        d.line([((x - x0) * scale, 0), ((x - x0) * scale, crop.height)],
               fill=(0, 110, 255) if major else (185, 215, 255), width=1)
        if major:
            d.text(((x - x0) * scale + 2, 2), str(x), fill=(0, 0, 200))
    for y in range((y0 // 10 + 1) * 10, y1, 10):
        major = y % 50 == 0
        d.line([(0, (y - y0) * scale), (crop.width, (y - y0) * scale)],
               fill=(0, 110, 255) if major else (185, 215, 255), width=1)
        if major:
            d.text((2, (y - y0) * scale + 2), str(y), fill=(0, 0, 200))
    out = Path("work") / "zoom"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{path.stem}-{x0}-{y0}-{x1}-{y1}.png"
    crop.save(dest)
    print(dest)


if __name__ == "__main__":
    main(sys.argv[1:])
