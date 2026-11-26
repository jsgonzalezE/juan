"""Shared assets and helpers for the three teaser versions."""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageFont

from fx import (CREAM, FONTS, FPS, H, INK, MAGENTA, ORANGE, RED, WINE, W, Layer, bayer,
                clamp01, composite, decode, dotmatrix, ease, ease_out, font, load, luminance,
                to_u8)

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
GEISHA_C = (196, 120, 214)
PURPLE = (120, 52, 140)

VARIETY_NAMES = ["JAVA", "CASTILLO", "GEISHA", "BOURBON"]
VARIETY_COLORS = [ORANGE, MAGENTA, GEISHA_C, RED]

_pf = {}


def pfont(weight=600, size=80):
    key = (weight, size)
    if key not in _pf:
        _pf[key] = ImageFont.truetype(
            os.path.join(FONTS, f"pixelify-sans-latin-{weight}-normal.woff"), size)
    return _pf[key]


def fit(text, maxw, weight=800, start=200, italic=False, pixel=False, tracking=0):
    s = start
    while s > 10:
        f = pfont(weight, s) if pixel else font(weight, s, italic)
        w = sum(f.getlength(c) for c in text) + tracking * (len(text) - 1)
        if w <= maxw:
            return f
        s -= 4
    return f


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
PACK_COLOR = Image.open(os.path.join(HERE, "assets", "pack_color_front.png")).convert("RGB")
PACK_DARK = load("pack_dark_front.jpg")
WATER = {k: load(k + ".jpg") for k in ("wc_cherries", "wc_picker", "wc_mule_dog")}
IMAGES = {"color": PACK_COLOR, "dark": PACK_DARK, **WATER}

LOGO = Image.open(os.path.join(HERE, "assets", "logo_white.png")).convert("RGBA")  # load now, before workers fork


@lru_cache(maxsize=None)
def logo_alpha(width):
    h = round(width * LOGO.height / LOGO.width)
    return np.asarray(LOGO.resize((width, h), Image.LANCZOS))[..., 3].astype(np.float32) / 255


@lru_cache(maxsize=None)
def logo_grid(width, cell):
    h = round(width * LOGO.height / LOGO.width)
    g = np.asarray(LOGO.resize((width // cell, h // cell), Image.BOX))[..., 3]
    return g.astype(np.float32) / 255


@lru_cache(maxsize=None)
def _palette(name, n):
    im = IMAGES[name]
    q = im.resize((max(1, im.width // 3), max(1, im.height // 3))).quantize(
        colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(q.getpalette()[:n * 3], np.float32).reshape(n, 3) / 255.0


def palettize(g, pal):
    d = ((g[..., None, :] - pal[None, None]) ** 2).sum(-1)
    return pal[d.argmin(-1)]


@lru_cache(maxsize=None)
def pix(name, cols, rows=None, box=(0.0, 0.0, 1.0, 1.0), ncolors=24):
    """Pixel-art version of an image (or a crop of it): (rows, cols, 3) float."""
    im = IMAGES[name]
    iw, ih = im.size
    x0, y0, x1, y1 = box[0] * iw, box[1] * ih, box[2] * iw, box[3] * ih
    if rows is None:
        rows = max(1, round(cols * (y1 - y0) / (x1 - x0)))
    else:  # crop to the requested aspect, centred on the box
        target = cols / rows
        bw, bh = x1 - x0, y1 - y0
        if bw / bh > target:
            nb = bh * target
            x0, x1 = (x0 + x1 - nb) / 2, (x0 + x1 + nb) / 2
        else:
            nb = bw / target
            y0, y1 = (y0 + y1 - nb) / 2, (y0 + y1 + nb) / 2
    g = np.asarray(im.resize((cols, rows), Image.BOX, box=(x0, y0, x1, y1))).astype(np.float32) / 255
    if ncolors:
        g = palettize(g, _palette(name, ncolors))
    g.setflags(write=False)
    return g


def card3d(grid, ang, tilt=0.0, persp=2.2, margin=0.3):
    """Rotate a flat pixel grid about its vertical axis (perspective).

    Returns (rgb, alpha, m) on a grid enlarged by m cells on every side.
    """
    rows, cols = grid.shape[:2]
    m = int(math.ceil(max(rows, cols) * margin))
    hw, hh = cols / 2, rows / 2
    D = persp * max(hw, hh)
    yy, xx = np.mgrid[0:rows + 2 * m, 0:cols + 2 * m].astype(np.float32)
    x = xx + 0.5 - m - hw
    y = yy + 0.5 - m - hh
    c, s = math.cos(ang), math.sin(ang)
    den = D * c - x * s
    u = x * D / np.where(np.abs(den) < 1e-3, 1e-3, den)
    z = u * s
    v = y * (D + z) / D + tilt * u
    ui = np.floor(u + hw).astype(int)
    vi = np.floor(v + hh).astype(int)
    ok = (ui >= 0) & (ui < cols) & (vi >= 0) & (vi < rows) & (den > 0)
    rgb = np.zeros((rows + 2 * m, cols + 2 * m, 3), np.float32)
    rgb[ok] = grid[vi[ok], ui[ok]]
    shade = 0.78 + 0.22 * c - 0.15 * np.clip(z / max(hw, 1), -1, 1)
    rgb = np.clip(rgb * shade[..., None], 0, 1)
    return rgb, ok.astype(np.float32), m


def duotone(g, color, lo=0.1, hi=0.95):
    lum = luminance(g)
    return np.clip((lum - lo) / (hi - lo), 0, 1)


def bg(color):
    img = np.empty((H, W, 3), np.float32)
    img[:] = np.array(color, np.float32) / 255
    return img


def grain(img, rng, amount=0.045):
    n = rng.random((H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[..., None]
    return img + (n - 0.5) * amount


def tx(L, t, start, text, f, xy, anchor="la", dur=0.35, color=INK, tracking=0, seed=0,
       end=None, fade=0.2, alpha=1.0):
    if t < start:
        return
    a = alpha
    if end is not None and t > end - fade:
        a *= clamp01((end - t) / fade)
    L.text(xy, decode(text, (t - start) / dur, seed), f, fill=color, anchor=anchor,
           tracking=tracking, alpha=a)


def fade_text(L, t, start, text, f, xy, anchor="la", dur=0.4, color=INK, tracking=0,
              end=None, fade=0.25, rise=14):
    """Soft fade + small rise (elegant alternative to the decode effect)."""
    if t < start:
        return
    k = ease((t - start) / dur)
    a = k
    if end is not None and t > end - fade:
        a *= clamp01((end - t) / fade)
    x, y = xy
    L.text((x, y + (1 - k) * rise), text, f, fill=color, anchor=anchor, tracking=tracking,
           alpha=a)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
_RENDER = None


def _work(i):
    return _RENDER(i)


def run(render, duration, name, argv=None):
    """CLI: --stills 1,2,3 or full render to build/<name>_silent.mp4."""
    import argparse
    global _RENDER
    _RENDER = render
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills")
    args = ap.parse_args(argv)
    os.makedirs(BUILD, exist_ok=True)
    if args.stills:
        for s in args.stills.split(","):
            im = Image.frombytes("RGB", (W, H), render(int(round(float(s) * FPS))))
            p = os.path.join(BUILD, f"{name}_still_{float(s):05.2f}.png")
            im.save(p)
            print(p)
        return
    out = os.path.join(BUILD, f"{name}_silent.mp4")
    n = int(round(duration * FPS))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
           "-crf", "16", "-pix_fmt", "yuv420p", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(_work, range(n), chunksize=2)):
            proc.stdin.write(buf)
            if k % 96 == 0:
                print(f"{name}: frame {k}/{n}", file=sys.stderr, flush=True)
    proc.stdin.close()
    proc.wait()
    print(out)


def finalize(name, soundtrack):
    """Render the soundtrack and mux it with the silent video into build/<name>.mp4."""
    wav = soundtrack(os.path.join(BUILD, f"{name}.wav"))
    out = os.path.join(BUILD, f"{name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(BUILD, f"{name}_silent.mp4"),
                    "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out],
                   check=True)
    print(out)
    return out
