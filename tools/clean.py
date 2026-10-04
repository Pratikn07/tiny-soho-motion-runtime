"""Remove the slide's baked-in text using the plan's line boxes. Protected boxes are never touched.

    python3 tools/clean.py work/slide-03/plan.json

Writes work/<name>/plate.png (text-free) and work/<name>/clean-check.png (left: original with repaired pixels in
magenta, right: plate). Look at clean-check.png: magenta must sit only on lettering, never on the child or props.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

PAD = 10


def main(plan_path):
    plan_file = Path(plan_path)
    plan = json.loads(plan_file.read_text())
    out = plan_file.parent
    img = cv2.imread(plan["slide"])
    h, w = img.shape[:2]
    zone = np.zeros((h, w), np.uint8)
    boxes = [l["box"] for l in plan["lines"]] + plan.get("remove_extra", [])
    for x0, y0, x1, y1 in boxes:
        zone[max(0, y0 - PAD):min(h, y1 + PAD), max(0, x0 - PAD):min(w, x1 + PAD)] = 1
    for p in plan.get("protect", []):
        x0, y0, x1, y1 = p["box"]
        zone[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] = 0
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.int16)
    bg = cv2.cvtColor(cv2.medianBlur(img, 61), cv2.COLOR_BGR2LAB).astype(np.int16)
    darker = bg[:, :, 0] - lab[:, :, 0]
    redder = lab[:, :, 1] - bg[:, :, 1]
    ink = ((darker > 14) | ((redder > 10) & (darker > 4))) & (zone == 1)
    mask = cv2.dilate(ink.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    mask &= zone * 255
    plate = cv2.inpaint(img, mask, 9, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(plate, (0, 0), 4)
    m = cv2.GaussianBlur(mask, (0, 0), 3)[:, :, None] / 255.0 * 0.7
    plate = (plate * (1 - m) + soft * m).astype(np.uint8)
    cv2.imwrite(str(out / "plate.png"), plate)
    vis = img.copy()
    vis[mask > 0] = (vis[mask > 0] * 0.3 + np.array([255, 0, 255]) * 0.7).astype(np.uint8)
    for p in plan.get("protect", []):
        x0, y0, x1, y1 = p["box"]
        cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 200, 0), 3)
    both = np.concatenate([vis, plate], axis=1)
    cv2.imwrite(str(out / "clean-check.png"), cv2.resize(both, (both.shape[1] // 2, both.shape[0] // 2)))
    print(json.dumps({"plate": str(out / "plate.png"), "check": str(out / "clean-check.png"),
                      "repaired_percent": round(float((mask > 0).mean() * 100), 1)}))


if __name__ == "__main__":
    main(sys.argv[1])
