#!/usr/bin/env python3
"""Build the prototype video from one still image per shot.

The camera moves over each image (push-in, pan, tilt, pull-out) following storyboard.json, a title and a
line of caption fade in and out over a soft shade band, and the shots are joined with short dips to black.
Needs ffmpeg on the PATH (ChatGPT's Python tool has it; on a PC install it from ffmpeg.org).

    python animatic.py [--images fotos] [--frame 1920x1080] [--out prototipo.mp4] [--long] [--only shot-01,shot-02]

    --images  folder with shot-01.png ... (jpg/webp also fine); for a vertical frame shot-01-v.png is used when it exists
    --frame   1920x1080 (horizontal) or 1080x1920 (vertical)
    --long    include the optional shots (the spray-drying route)
    --only    build just these shots, e.g. to check one new image
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--images", default="fotos")
ap.add_argument("--frame", default="1920x1080")
ap.add_argument("--out", default=None)
ap.add_argument("--long", action="store_true")
ap.add_argument("--only", default="")
ap.add_argument("--fps", type=int, default=None)
args = ap.parse_args()

FW, FH = (int(v) for v in args.frame.lower().split("x"))
VERTICAL = FH > FW
OUT = os.path.abspath(args.out or ("prototipo-vertical.mp4" if VERTICAL else "prototipo.mp4"))
with open(os.path.join(HERE, "storyboard.json"), encoding="utf-8") as f:
    board = json.load(f)
FPS = args.fps or board.get("fps", 30)
FADE = board.get("fade", 0.4)
IMAGES = os.path.abspath(args.images)
ONLY = [s for s in args.only.split(",") if s]

if shutil.which("ffmpeg") is None:
    sys.exit("ffmpeg not found: install it (ffmpeg.org) or run this inside ChatGPT's Python tool")


def find_font(bold):
    candidates = [
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf" if bold else "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


FONT_BOLD = find_font(True)
FONT_BOOK = find_font(False)


def font_opt(bold):
    path = FONT_BOLD if bold else FONT_BOOK
    if path:
        return "fontfile=" + path.replace("\\", "/").replace(":", "\\:")
    return "font=Sans"


def run(argv):
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit(f"{argv[0]} failed")
    return r.stdout


def image_for(shot_id):
    files = os.listdir(IMAGES)

    def pick(base):
        for name in files:
            low = name.lower()
            if low.startswith(base.lower() + ".") and low.rsplit(".", 1)[-1] in ("png", "jpg", "jpeg", "webp"):
                return os.path.join(IMAGES, name)
        return None

    return (pick(shot_id + "-v") if VERTICAL else None) or pick(shot_id)


shots = [s for s in board["shots"] if (args.long or not s.get("optional")) and (not ONLY or s["id"] in ONLY)]
missing = [s["id"] for s in shots if not image_for(s["id"])]
if missing:
    sys.exit(f"missing images in {IMAGES}: {', '.join(missing)}")

work = tempfile.mkdtemp(prefix="animatic-")
SW, SH = FW * 2, FH * 2
EASE = "(pow(on/(duration-1),2)*(3-2*on/(duration-1)))"  # zoompan calls its frame count `duration`


def lerp(a, b):
    return f"{a}" if a == b else f"({a}+({b}-{a})*{EASE})"


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:")


def wrap(text, limit):
    lines, line = [], ""
    for w in text.split(" "):
        if len((line + " " + w).strip()) > limit and line:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    return lines


# the shade band: a gradient from clear to near-black, so photographs keep their lower edge
BAND_H = round(FH * 0.36)
band = os.path.join(work, "band.png")
run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
     f"color=c=black:s={FW}x{BAND_H},format=rgba,geq=r=0:g=0:b=0:a='255*0.88*pow(Y/H,1.3)'", "-frames:v", "1", band])

segments = []
for i, shot in enumerate(shots):
    img = image_for(shot["id"])
    d = round(shot["dur"] * FPS)
    a, b = shot["cam"]["from"], shot["cam"]["to"]
    z = f"1/{lerp(a['w'], b['w'])}"
    cx, cy = lerp(a["cx"], b["cx"]), lerp(a["cy"], b["cy"])
    x = f"min(max({cx}*iw-iw/zoom/2,0),iw-iw/zoom)"
    y = f"min(max({cy}*ih-ih/zoom/2,0),ih-ih/zoom)"
    left, bottom = round(FW * 0.045), round(FH * 0.075)
    title_size, sub_size = round(min(FW, FH) * 0.044), round(min(FW, FH) * 0.027)
    sub_lines = wrap(shot["sub"], 38 if VERTICAL else 70)
    line_h = round(sub_size * 1.35)
    sub_block = len(sub_lines) * line_h
    dur = shot["dur"]

    def fade_text(start):
        return (f"if(lt(t,{start}),0,if(lt(t,{start + 0.5}),(t-{start})/0.5,"
                f"if(gt(t,{dur - 0.6}),max(0,({dur}-t)/0.6),1)))")

    texts = [f"drawtext=expansion=none:{font_opt(True)}:text='{esc(shot['title'])}':fontsize={title_size}:fontcolor=white"
             f":x={left}:y=h-{bottom + sub_block + round(title_size * 1.25)}:alpha='{fade_text(0.5)}'"]
    for n, line in enumerate(sub_lines):
        texts.append(f"drawtext=expansion=none:{font_opt(False)}:text='{esc(line)}':fontsize={sub_size}:fontcolor=0xd0d0d0"
                     f":x={left}:y=h-{bottom + sub_block - n * line_h}:alpha='{fade_text(0.9)}'")
    camera = ",".join([
        f"scale={SW}:{SH}:force_original_aspect_ratio=increase",
        f"crop={SW}:{SH}",
        f"zoompan=z='{z}':x='{x}':y='{y}':d={d}:s={FW}x{FH}:fps={FPS}",
    ])
    words = ",".join([f"overlay=0:{FH - BAND_H}:format=auto", *texts,
                      f"fade=t=in:st=0:d={FADE}", f"fade=t=out:st={dur - FADE:.2f}:d={FADE}", "format=yuv420p"])
    graph = f"[0:v]{camera}[cam];[cam][1:v]{words}[out]"
    seg = os.path.join(work, f"{i:02d}-{shot['id']}.mp4")
    print(f"{shot['id']} · {dur} s · {shot['title']}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", img, "-i", band, "-filter_complex", graph, "-map", "[out]",
         "-frames:v", str(d), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", seg])
    segments.append(seg)

lst = os.path.join(work, "list.txt")
with open(lst, "w", encoding="utf-8") as f:
    f.write("\n".join(f"file '{s}'" for s in segments))
run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT])
shutil.rmtree(work, ignore_errors=True)
total = sum(s["dur"] for s in shots)
print(f"wrote {OUT} · {len(shots)} shots · {total} s · {FW}x{FH}")
