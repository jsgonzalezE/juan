"""Pixel-art sprite toolkit for Noah.

Sprites are plain-text grids: one character per pixel, one line per row, all rows the same
length. Characters map to a fixed palette (see PALETTE). '.' is transparent.

Commands
  python3 px.py render SPRITE.txt OUT.png [--scale 8] [--ref REF.png] [--grid] [--bg dark|light|both]
  python3 px.py check SPRITE.txt                       # dims, bad chars, orphan pixels, palette use
  python3 px.py strip OUT.png F1.txt F2.txt ... [--scale 6] [--labels]   # frames side by side
  python3 px.py onion OUT.png BASE.txt OVER.txt [--scale 8]              # OVER at 50% on BASE
  python3 px.py trace REF.png OUT.txt --w 56 --h 64 [--anchor bottom]    # rough auto-trace start
  python3 px.py new OUT.txt --w 56 --h 64                                # blank canvas
  python3 px.py mirror IN.txt OUT.txt [--keep left|right]                # symmetric front views
  python3 px.py flip IN.txt OUT.txt                                      # horizontal flip
  python3 px.py anim OUT.(gif|mp4) F1.txt F2.txt ... [--fps 8] [--scale 6]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PALETTE = {
    ".": None,                 # transparent
    "K": (30, 23, 20),         # outline / ink lines (very dark warm)
    "E": (10, 8, 8),           # eyes, nose (pure dark)
    "e": (250, 250, 250),      # tiny catch-light in eyes / nose
    "W": (248, 244, 237),      # white fur, lit
    "w": (224, 215, 203),      # white fur, shade 1
    "v": (186, 174, 160),      # white fur, shade 2
    "u": (138, 126, 114),      # fur strands / deepest shade on white fur
    "D": (56, 46, 41),         # dark fur (ears, patches) base
    "d": (86, 72, 64),         # dark fur mid / sheen
    "r": (130, 112, 100),      # dark fur rim light (edges facing the light / against black bg)
    "P": (238, 124, 142),      # tongue
    "p": (190, 78, 100),       # tongue shade / inside mouth
    "O": (228, 122, 46),       # brand orange (topknot band, accents)
    "o": (168, 78, 30),        # orange shade
    "B": (124, 28, 60),        # brand wine (bandana)
    "b": (82, 16, 40),         # wine shade
    "C": (240, 228, 206),      # cream (bandana bean emblem, collar tag)
    "g": (110, 104, 98),       # neutral grey (misc. accessory)
}
BG_DARK = (17, 15, 14)
BG_LIGHT = (236, 232, 226)


def load(path):
    with open(path) as f:
        rows = [ln.rstrip("\n").rstrip("\r") for ln in f]
    rows = [r for r in rows if r.strip() != "" or False]
    # allow trailing comment lines starting with '#'
    rows = [r for r in rows if not r.startswith("#")]
    return rows


def validate(rows):
    errs = []
    if not rows:
        return ["empty sprite"]
    w = len(rows[0])
    for i, r in enumerate(rows):
        if len(r) != w:
            errs.append(f"row {i} has length {len(r)} (expected {w})")
        bad = sorted(set(c for c in r if c not in PALETTE))
        if bad:
            errs.append(f"row {i} has unknown chars {bad}")
    return errs


def to_rgba(rows):
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            col = PALETTE.get(c)
            if col is not None:
                a[y, x] = col + (255,)
    return a


def to_float(rows):
    """RGBA float32 in [0,1] — what the video renderer uses."""
    return to_rgba(rows).astype(np.float32) / 255


def save(rows, path):
    with open(path, "w") as f:
        f.write("\n".join(rows) + "\n")


def upscale(rgba, scale):
    return np.repeat(np.repeat(rgba, scale, 0), scale, 1)


def _font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def compose(rgba, scale, bg, grid=False):
    up = upscale(rgba, scale)
    h, w = up.shape[:2]
    canvas = Image.new("RGB", (w, h), bg)
    canvas.paste(Image.fromarray(up, "RGBA"), (0, 0), Image.fromarray(up, "RGBA"))
    if grid and scale >= 6:
        d = ImageDraw.Draw(canvas)
        gc = tuple(min(255, c + 14) for c in bg)
        for x in range(0, w, scale):
            d.line([(x, 0), (x, h)], fill=gc)
        for y in range(0, h, scale):
            d.line([(0, y), (w, y)], fill=gc)
    return canvas


def cmd_render(a):
    rows = load(a.sprite)
    errs = validate(rows)
    if errs:
        print("\n".join(errs))
    rgba = to_rgba(rows)
    tiles = []
    if a.bg in ("dark", "both"):
        tiles.append(compose(rgba, a.scale, BG_DARK, a.grid))
    if a.bg in ("light", "both"):
        tiles.append(compose(rgba, a.scale, BG_LIGHT, a.grid))
    small = compose(rgba, max(1, a.scale // 4), BG_DARK)   # how it reads small
    tiles.append(small)
    if a.ref:
        ref = Image.open(a.ref).convert("RGB")
        hh = tiles[0].height
        ref = ref.resize((max(1, round(ref.width * hh / ref.height)), hh), Image.LANCZOS)
        tiles.append(ref)
    H = max(t.height for t in tiles)
    W = sum(t.width for t in tiles) + 16 * (len(tiles) - 1)
    out = Image.new("RGB", (W, H), (60, 60, 60))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + 16
    out.save(a.out)
    print(f"{a.out}  sprite {rgba.shape[1]}x{rgba.shape[0]}")


def orphans(rows):
    """Opaque pixels whose 8 neighbours are all a different char (isolated specks)."""
    h, w = len(rows), len(rows[0])
    res = []
    for y in range(h):
        for x in range(w):
            c = rows[y][x]
            if c == ".":
                continue
            same = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dy or dx) and 0 <= y + dy < h and 0 <= x + dx < w:
                        if rows[y + dy][x + dx] == c:
                            same += 1
            if same == 0 and c not in "Ee":
                res.append((x, y, c))
    return res


def cmd_check(a):
    rows = load(a.sprite)
    errs = validate(rows)
    print(f"size: {len(rows[0]) if rows else 0} x {len(rows)}")
    for e in errs:
        print("ERROR", e)
    if errs:
        return
    o = orphans(rows)
    print(f"orphan pixels (no same-colour neighbour, eyes excluded): {len(o)}")
    for x, y, c in o[:40]:
        print(f"  x={x} y={y} '{c}'")
    from collections import Counter
    cnt = Counter(c for r in rows for c in r)
    print("palette use:", ", ".join(f"{k}:{v}" for k, v in sorted(cnt.items())))
    op = [(y, x) for y, r in enumerate(rows) for x, c in enumerate(r) if c != "."]
    if op:
        ys, xs = zip(*op)
        print(f"opaque bbox: x {min(xs)}..{max(xs)}  y {min(ys)}..{max(ys)}")


def cmd_strip(a):
    frames = [to_rgba(load(f)) for f in a.frames]
    H = max(f.shape[0] for f in frames) * a.scale
    tiles = []
    for f in frames:
        c = compose(f, a.scale, BG_DARK)
        t = Image.new("RGB", (c.width, H + (24 if a.labels else 0)), BG_DARK)
        t.paste(c, (0, H - c.height))
        d = ImageDraw.Draw(t)
        d.line([(0, H - 1), (c.width, H - 1)], fill=(70, 64, 60))   # baseline
        tiles.append(t)
    W = sum(t.width for t in tiles) + 8 * (len(tiles) - 1)
    out = Image.new("RGB", (W, tiles[0].height), (60, 60, 60))
    x = 0
    for t, name in zip(tiles, a.frames):
        out.paste(t, (x, 0))
        if a.labels:
            ImageDraw.Draw(out).text((x + 4, H + 4), os.path.basename(name)[:-4], fill=(220, 210, 200),
                                     font=_font(14))
        x += t.width + 8
    out.save(a.out)
    print(a.out)


def cmd_onion(a):
    base = to_rgba(load(a.base)).astype(np.float32)
    over = to_rgba(load(a.over)).astype(np.float32)
    h, w = max(base.shape[0], over.shape[0]), max(base.shape[1], over.shape[1])
    canvas = np.zeros((h, w, 3), np.float32) + np.array(BG_DARK, np.float32)
    for img, k, tint in ((base, 1.0, (1.0, 1.0, 1.0)), (over, 0.5, (1.0, 0.55, 0.55))):
        al = img[..., 3:4] / 255 * k
        sub = canvas[:img.shape[0], :img.shape[1]]
        canvas[:img.shape[0], :img.shape[1]] = sub * (1 - al) + img[..., :3] * np.array(tint) * al
    up = upscale(canvas.astype(np.uint8), a.scale)
    Image.fromarray(up).save(a.out)
    print(a.out)


def _silhouette(ink, close=9):
    h, w = ink.shape
    im = Image.fromarray((ink * 255).astype(np.uint8))
    closed = np.asarray(im.filter(ImageFilter.MaxFilter(close))) > 127
    sm = np.asarray(Image.fromarray(closed.astype(np.uint8) * 255).resize(
        (max(2, w // 4), max(2, h // 4)), Image.BOX)) > 60
    hh, ww = sm.shape
    out = np.zeros_like(sm)
    st = [(y, x) for y in range(hh) for x in (0, ww - 1)] + [(y, x) for x in range(ww) for y in (0, hh - 1)]
    while st:
        y, x = st.pop()
        if out[y, x] or sm[y, x]:
            continue
        out[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= y + dy < hh and 0 <= x + dx < ww:
                st.append((y + dy, x + dx))
    sil = ~(np.asarray(Image.fromarray(out.astype(np.uint8) * 255).resize((w, h), Image.NEAREST)) > 0)
    sil = np.asarray(Image.fromarray(sil.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(close))) > 127
    return sil | ink


def cmd_trace(a):
    """Rough starting grid from a black-ink-on-white drawing: K lines, D thick black, W fur."""
    im = Image.open(a.ref).convert("L")
    ink = np.asarray(im) < 128
    W0, H0 = im.size
    k = max(5, int(W0 * a.thick) | 1)
    thick_full = np.asarray(Image.fromarray(ink.astype(np.uint8) * 255).filter(
        ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))) > 127
    sil_full = _silhouette(ink)
    tw = a.w
    th = max(1, round(tw * H0 / W0))

    def down(m):
        return np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize((tw, th), Image.BOX)) / 255.0

    thick = down(thick_full) > 0.5
    line = (down(ink & ~thick_full) > 0.26) & ~thick
    sil = (down(sil_full) > 0.5) | thick | line
    grid = np.full((th, tw), ".", "<U1")
    grid[sil] = "W"
    grid[line] = "K"
    grid[thick] = "D"
    H = a.h or th
    out = np.full((H, tw), ".", "<U1")
    if th >= H:
        out[:] = grid[th - H:] if a.anchor == "bottom" else grid[:H]
    else:
        if a.anchor == "bottom":
            out[H - th:] = grid
        else:
            out[:th] = grid
    rows = ["".join(r) for r in out]
    save(rows, a.out)
    print(f"{a.out}  {tw}x{H}")


def cmd_new(a):
    save(["." * a.w for _ in range(a.h)], a.out)
    print(a.out)


def cmd_mirror(a):
    rows = load(a.inp)
    w = len(rows[0])
    out = []
    for r in rows:
        if a.keep == "left":
            half = r[: (w + 1) // 2]
            out.append((half + half[: w // 2][::-1])[:w])
        else:
            half = r[w // 2:]
            out.append((half[::-1][: w - len(half)] + half)[:w])
    save(out, a.out)
    print(a.out)


def cmd_flip(a):
    save([r[::-1] for r in load(a.inp)], a.out)
    print(a.out)


def cmd_anim(a):
    frames = [to_rgba(load(f)) for f in a.frames]
    H = max(f.shape[0] for f in frames)
    Wd = max(f.shape[1] for f in frames)
    ims = []
    for f in frames:
        c = Image.new("RGB", (Wd * a.scale, H * a.scale), BG_DARK)
        up = Image.fromarray(upscale(f, a.scale), "RGBA")
        c.paste(up, ((Wd - f.shape[1]) * a.scale // 2, (H - f.shape[0]) * a.scale), up)
        ims.append(c)
    if a.out.endswith(".gif"):
        ims[0].save(a.out, save_all=True, append_images=ims[1:], duration=int(1000 / a.fps), loop=0)
    else:
        import subprocess
        tmp = a.out + "_frames"
        os.makedirs(tmp, exist_ok=True)
        for i, im in enumerate(ims):
            im.save(f"{tmp}/{i:04d}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps), "-i", f"{tmp}/%04d.png",
                        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p", a.out], check=True)
    print(a.out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("render"); p.add_argument("sprite"); p.add_argument("out")
    p.add_argument("--scale", type=int, default=8); p.add_argument("--ref")
    p.add_argument("--grid", action="store_true"); p.add_argument("--bg", default="both")
    p.set_defaults(fn=cmd_render)
    p = sub.add_parser("check"); p.add_argument("sprite"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("strip"); p.add_argument("out"); p.add_argument("frames", nargs="+")
    p.add_argument("--scale", type=int, default=6); p.add_argument("--labels", action="store_true")
    p.set_defaults(fn=cmd_strip)
    p = sub.add_parser("onion"); p.add_argument("out"); p.add_argument("base"); p.add_argument("over")
    p.add_argument("--scale", type=int, default=8); p.set_defaults(fn=cmd_onion)
    p = sub.add_parser("trace"); p.add_argument("ref"); p.add_argument("out")
    p.add_argument("--w", type=int, default=56); p.add_argument("--h", type=int, default=0)
    p.add_argument("--thick", type=float, default=0.028); p.add_argument("--anchor", default="bottom")
    p.set_defaults(fn=cmd_trace)
    p = sub.add_parser("new"); p.add_argument("out"); p.add_argument("--w", type=int, default=56)
    p.add_argument("--h", type=int, default=64); p.set_defaults(fn=cmd_new)
    p = sub.add_parser("mirror"); p.add_argument("inp"); p.add_argument("out")
    p.add_argument("--keep", default="left"); p.set_defaults(fn=cmd_mirror)
    p = sub.add_parser("flip"); p.add_argument("inp"); p.add_argument("out"); p.set_defaults(fn=cmd_flip)
    p = sub.add_parser("anim"); p.add_argument("out"); p.add_argument("frames", nargs="+")
    p.add_argument("--fps", type=float, default=8); p.add_argument("--scale", type=int, default=6)
    p.set_defaults(fn=cmd_anim)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
