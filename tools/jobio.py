"""Fetch a production job's slides and deliver its outputs, using only the one-time links in the job payload.

    python3 tools/jobio.py fetch work/payload.txt     # downloads each slide into inputs/slide-NN.png
    python3 tools/jobio.py deliver work/payload.txt   # uploads outputs, then result.json last

Payload format (the routine-fire-payload text, saved verbatim to work/payload.txt):

    tiny-soho-job v1
    job: <run id>
    slide 1 <slide id>
      get <signed download url>
      put plate.png <signed upload url>
      put text-layer.png <signed upload url>
      put plan.json <signed upload url>
      put preview.mp4 <signed upload url>
      put frames.jpg <signed upload url>
    slide 2 <slide id>
      ...
    result <signed upload url>

Every URL must be https on a host listed in runtime.json, under /storage/v1/object/. Anything else is refused
before any network call, so a payload cannot send outputs anywhere except this project's storage.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HOSTS = set(json.loads((ROOT / "runtime.json").read_text())["allowed_storage_hosts"])
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
OUTPUTS = {"plate.png": "image/png", "text-layer.png": "image/png", "plan.json": "application/json",
           "preview.mp4": "video/mp4", "frames.jpg": "image/jpeg"}


class PayloadError(ValueError):
    pass


def check_url(url, kind):
    m = re.fullmatch(r"https://([a-z0-9.-]+)(/storage/v1/object/(sign|upload/sign)/[^\s]+)", url)
    if not m or m.group(1) not in ALLOWED_HOSTS:
        raise PayloadError(f"refused {kind} URL: host or path not allowed")
    if kind == "get" and m.group(3) != "sign":
        raise PayloadError("refused download URL: not a signed download link")
    if kind == "put" and m.group(3) != "upload/sign":
        raise PayloadError("refused upload URL: not a signed upload link")
    return url


def parse(text):
    lines = [l.rstrip() for l in text.strip().splitlines() if l.strip()]
    if not lines or lines[0].strip() != "tiny-soho-job v1":
        raise PayloadError("first line must be 'tiny-soho-job v1'")
    job = re.fullmatch(rf"job: ({UUID})", lines[1].strip()) if len(lines) > 1 else None
    if not job:
        raise PayloadError("second line must be 'job: <uuid>'")
    slides, result, current = [], None, None
    for raw in lines[2:]:
        line = raw.strip()
        if m := re.fullmatch(rf"slide (\d+) ({UUID})", line):
            current = {"n": int(m.group(1)), "slide_id": m.group(2), "get": None, "put": {}}
            slides.append(current)
        elif m := re.fullmatch(r"get (\S+)", line):
            if current is None:
                raise PayloadError("'get' before any slide")
            current["get"] = check_url(m.group(1), "get")
        elif m := re.fullmatch(r"put (\S+) (\S+)", line):
            if current is None or m.group(1) not in OUTPUTS:
                raise PayloadError(f"unexpected upload line for {m.group(1)!r}")
            current["put"][m.group(1)] = check_url(m.group(2), "put")
        elif m := re.fullmatch(r"result (\S+)", line):
            result = check_url(m.group(1), "put")
        else:
            raise PayloadError("unrecognised payload line")
    if not slides or len(slides) > 20:
        raise PayloadError("payload must list 1-20 slides")
    if [s["n"] for s in slides] != list(range(1, len(slides) + 1)):
        raise PayloadError("slides must be numbered 1, 2, 3, …")
    for s in slides:
        if not s["get"] or set(s["put"]) != set(OUTPUTS):
            raise PayloadError(f"slide {s['n']} needs one get and puts for {sorted(OUTPUTS)}")
    if not result:
        raise PayloadError("missing 'result' upload line")
    return {"job": job.group(1), "slides": slides, "result": result}


def http(method, url, data=None, ctype=None):
    req = urllib.request.Request(url, data=data, method=method)
    if ctype:
        req.add_header("Content-Type", ctype)
        req.add_header("x-upsert", "false")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def fetch(job):
    Path("inputs").mkdir(exist_ok=True)
    out = []
    for s in job["slides"]:
        data = http("GET", s["get"])
        dest = Path("inputs") / f"slide-{s['n']:02d}.png"
        from PIL import Image
        import io
        Image.open(io.BytesIO(data)).convert("RGB").save(dest)
        out.append(str(dest))
    print(json.dumps({"job": job["job"], "inputs": out}))


def deliver(job):
    slides_report = []
    for s in job["slides"]:
        work = Path("work") / f"slide-{s['n']:02d}"
        missing = [name for name in OUTPUTS if not (work / name).exists()]
        notes = (work / "notes.md").read_text()[:20000] if (work / "notes.md").exists() else ""
        plan = json.loads((work / "plan.json").read_text()) if (work / "plan.json").exists() else {}
        if missing:
            slides_report.append({"n": s["n"], "slide_id": s["slide_id"], "status": "failed",
                                  "error": f"missing outputs: {', '.join(missing)}", "notes": notes})
            continue
        for name, ctype in OUTPUTS.items():
            http("PUT", s["put"][name], (work / name).read_bytes(), ctype)
        slides_report.append({"n": s["n"], "slide_id": s["slide_id"], "status": "completed",
                              "concept": plan.get("concept"), "scene_prompt": plan.get("scene_prompt"),
                              "scene_avoid": plan.get("scene_avoid"), "notes": notes})
    result = {"version": 1, "job": job["job"], "slides": slides_report}
    http("PUT", job["result"], json.dumps(result).encode(), "application/json")
    print(json.dumps({"job": job["job"], "delivered": [r["n"] for r in slides_report if r["status"] == "completed"],
                      "failed": [r["n"] for r in slides_report if r["status"] != "completed"]}))


def main(argv):
    if len(argv) != 2 or argv[0] not in ("fetch", "deliver", "validate"):
        raise SystemExit(__doc__)
    try:
        job = parse(Path(argv[1]).read_text())
    except PayloadError as exc:
        raise SystemExit(f"payload rejected: {exc}")
    if argv[0] == "validate":
        print(json.dumps({"job": job["job"], "slides": len(job["slides"])}))
    elif argv[0] == "fetch":
        fetch(job)
    else:
        deliver(job)


if __name__ == "__main__":
    main(sys.argv[1:])
