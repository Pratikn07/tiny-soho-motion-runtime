"""Make a slide easy to read precisely: a copy with a labelled 50 px coordinate grid, plus OCR word boxes as hints.

    python3 tools/inspect_slide.py inputs/slide-03.png

Writes work/<name>/grid.png and work/<name>/ocr.json. OCR is a hint only: it misses pale rose text and invents
words from hair, fabric and screens. Always confirm against the image.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def main(path):
    src = Path(path)
    out = Path("work") / src.stem
    out.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    w, h = im.size
    g = im.copy()
    d = ImageDraw.Draw(g)
    for x in range(0, w, 50):
        d.line([(x, 0), (x, h)], fill=(0, 140, 255) if x % 100 == 0 else (150, 200, 255), width=1)
        if x % 100 == 0:
            d.text((x + 2, 2), str(x), fill=(0, 60, 200))
    for y in range(0, h, 50):
        d.line([(0, y), (w, y)], fill=(0, 140, 255) if y % 100 == 0 else (150, 200, 255), width=1)
        if y % 100 == 0:
            d.text((2, y + 2), str(y), fill=(0, 60, 200))
    g.save(out / "grid.png")
    words = []
    try:
        import pytesseract
        data = pytesseract.image_to_data(im, output_type=pytesseract.Output.DICT)
        for i, t in enumerate(data["text"]):
            if t.strip() and float(data["conf"][i]) > 30:
                words.append({"text": t, "box": [data["left"][i], data["top"][i],
                                                  data["left"][i] + data["width"][i],
                                                  data["top"][i] + data["height"][i]],
                              "conf": round(float(data["conf"][i]))})
    except Exception as exc:  # OCR is optional
        words = [{"error": f"ocr unavailable: {type(exc).__name__}"}]
    (out / "ocr.json").write_text(json.dumps({"size": [w, h], "words": words}, indent=1))
    print(json.dumps({"size": [w, h], "grid": str(out / "grid.png"), "ocr": str(out / "ocr.json"),
                      "ocr_words": len(words)}))


if __name__ == "__main__":
    main(sys.argv[1])
