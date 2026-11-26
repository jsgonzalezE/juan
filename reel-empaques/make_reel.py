"""Juanito Coffee — new harvest teaser (1080x1920, 24 fps, pixel art).

Story: flower -> origin -> cherry -> varieties -> cup -> (locked) packaging -> logo.
Nothing of the real packaging and no people are shown: this is a teaser.

Usage:
    python3 make_reel.py                 # render build/reel_silent.mp4
    python3 make_reel.py --stills 1,5,8  # preview PNGs at given seconds
"""
import argparse
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageFont

import sprites as SP
from fx import (CREAM, FONTS, FPS, H, INK, MAGENTA, ORANGE, RED, WINE, W, Layer, boost,
                clamp01, composite, decode, dotmatrix, ease, ease_out, font, load, luminance,
                scanlines, to_u8)

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")

GEISHA_C = (196, 120, 214)
GREEN_BEAN = (160, 176, 112)
GREY = (120, 112, 104)
DARK = (20, 17, 16)

# ---------------------------------------------------------------------------
# Timeline (seconds, 120 BPM grid)
# ---------------------------------------------------------------------------
T_BLOOM = (0.0, 2.0)
T_FIELD = (2.0, 4.0)
T_ORIGIN = (4.0, 7.0)
T_CHERRY = (7.0, 9.5)
T_VARIETIES = (9.5, 13.5)
T_CUP = (13.5, 16.0)
T_PACK = (16.0, 19.5)
T_OUTRO = (19.5, 24.0)
DURATION = 24.0
NFRAMES = int(round(DURATION * FPS))
CUTS = [4.0, 7.0, 9.5, 13.5, 16.0, 19.5]

VARIETIES = [("JAVA", 10.0, ORANGE), ("CASTILLO", 10.5, MAGENTA),
             ("GEISHA", 11.0, GEISHA_C), ("BOURBON", 11.5, RED)]

STAGES = [("bloom", "BLOOM"), ("origin", "ORIGIN"), ("cherry", "CHERRY"),
          ("bean", "VARIETIES"), ("cup", "CUP"), ("pack", "PACKAGING")]

_pf = {}


def pfont(weight=600, size=80):
    key = (weight, size)
    if key not in _pf:
        _pf[key] = ImageFont.truetype(
            os.path.join(FONTS, f"pixelify-sans-latin-{weight}-normal.woff"), size)
    return _pf[key]


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


def make_palette(img, n=28):
    q = img.resize((img.width // 3, img.height // 3)).quantize(
        colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(q.getpalette()[:n * 3], np.float32).reshape(n, 3) / 255.0


def palettize(g, pal):
    d = ((g[..., None, :] - pal[None, None]) ** 2).sum(-1)
    return pal[d.argmin(-1)]


SRC = {}
for key in ("wc_cherries", "wc_picker", "wc_mule_dog"):
    im = load(key + ".jpg")
    arr = np.asarray(im).astype(np.float32)
    lo, hi = np.percentile(luminance(arr), (2, 99))
    im = Image.fromarray(to_u8(np.clip((arr - lo) / (hi - lo), 0, 1)))
    SRC[key] = (im, make_palette(im))

# watercolour crops chosen so that no person appears
BANDS = [  # key, box (fractions of the painting), y0, rows, slide direction
    ("wc_picker", (0.0, 0.10, 1.0, 0.50), 150, 50, 1),
    ("wc_mule_dog", (0.50, 0.36, 1.0, 0.66), 1010, 36, -1),
    ("wc_cherries", (0.0, 0.62, 1.0, 0.98), 1370, 33, 1),
]


def sample_box(img, box, rows, cols, pan=0.0):
    iw, ih = img.size
    x0, y0, x1, y1 = box[0] * iw, box[1] * ih, box[2] * iw, box[3] * ih
    cx, cy = (x0 + x1) / 2 + pan * iw, (y0 + y1) / 2
    target = cols / rows
    bw, bh = x1 - x0, y1 - y0
    if bw / bh > target:
        bw = bh * target
    else:
        bh = bw / target
    bw *= 0.96
    bh *= 0.96
    cx = min(max(cx, bw / 2), iw - bw / 2)
    crop = img.resize((cols, rows), Image.BILINEAR,
                      box=(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2))
    return np.asarray(crop).astype(np.float32) / 255.0


LOGO = Image.open(os.path.join(HERE, "assets", "logo_white.png"))
LOGO_W = 400
LOGO_H = round(LOGO_W * LOGO.height / LOGO.width)
LOGO_A = np.asarray(LOGO.resize((LOGO_W, LOGO_H), Image.LANCZOS))[..., 3].astype(np.float32) / 255
LOGO_CELL = 6
LOGO_GRID = np.asarray(LOGO.resize((LOGO_W // LOGO_CELL, LOGO_H // LOGO_CELL), Image.BOX))[..., 3]
LOGO_GRID = LOGO_GRID.astype(np.float32) / 255
LOGO_T = np.random.default_rng(7).uniform(0.1, 0.8, LOGO_GRID.shape).astype(np.float32)

# field of blossoms
_r = np.random.default_rng(11)
FIELD = []
for i in range(26):
    while True:
        x, y = _r.uniform(40, 1040), _r.uniform(180, 1700)
        if not (60 < x < 1020 and 680 < y < 1260):  # keep the text box clear
            break
    n = int(_r.choice([17, 25, 33]))
    cell = int(_r.choice([6, 8, 10]))
    FIELD.append(dict(x=x, y=y, n=n, cell=cell, t=2.05 + i * 0.05, rot=_r.uniform(0, 1.2),
                      leaf=_r.random() < 0.45, flip=_r.random() < 0.5))
FLOWER_POPS = [f["t"] for f in FIELD]

POUCH_EDGE, POUCH_IN = SP.pouch(40, 56)
_ey, _ex = np.where(POUCH_EDGE[..., 3] > 0)
_ang = np.arctan2(_ey - 28, _ex - 20)
POUCH_ORDER = np.full(POUCH_EDGE.shape[:2], 2.0, np.float32)
POUCH_ORDER[_ey, _ex] = (np.argsort(np.argsort(_ang)) / max(1, len(_ang) - 1)).astype(np.float32)
BRAND = np.array([CREAM, ORANGE, WINE, MAGENTA, (120, 52, 140), RED, (40, 30, 28)],
                 np.float32) / 255
LOCK = SP.lock()
BEAN = SP.bean(18, 24, GREEN_BEAN)
CUP = SP.cup(56, 40)

LOAD_START, LOAD_END, LOAD_MAX = 16.4, 18.6, 0.87
NSEG = 30
LOAD_TICKS = [LOAD_START + (LOAD_END - LOAD_START) * k / int(NSEG * LOAD_MAX)
              for k in range(1, int(NSEG * LOAD_MAX) + 1)]
BEAN_DROPS = [(13.6 + i * 0.13, 452 + i * 38) for i in range(5)]  # start time, x
BEAN_LAND = [s + 0.42 for s, _ in BEAN_DROPS]

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def black():
    img = np.empty((H, W, 3), np.float32)
    img[:] = np.array(DARK, np.float32) / 255
    return img


def blit(img, spr, x, y, cell, gap=1, alpha=1.0, color=None):
    if color is None:
        rgb = np.ascontiguousarray(spr[..., :3])
    else:
        rgb = np.empty(spr.shape[:2] + (3,), np.float32)
        rgb[:] = np.array(color, np.float32) / 255
    col, a = dotmatrix(rgb, spr[..., 3] * alpha, cell, dot=cell - gap)
    return composite(img, col, a, (x, y))


def tx(L, t, start, text, f, xy, anchor="la", dur=0.35, color=INK, tracking=0, seed=0,
       end=None, fade=0.2):
    if t < start:
        return
    a = 1.0
    if end is not None and t > end - fade:
        a = clamp01((end - t) / fade)
    L.text(xy, decode(text, (t - start) / dur, seed), f, fill=color, anchor=anchor,
           tracking=tracking, alpha=a)


def pixel_box(L, box, color=CREAM, alpha=1.0, step=12, size=6, fill=None):
    x0, y0, x1, y1 = [int(v) for v in box]
    if fill is not None:
        L.rect((x0, y0, x1, y1), outline=None, fill=fill, alpha=alpha * 0.92)
    for x in range(x0, x1 - size + 1, step):
        L.rect((x, y0, x + size, y0 + size), outline=None, fill=color, alpha=alpha)
        L.rect((x, y1 - size, x + size, y1), outline=None, fill=color, alpha=alpha)
    for y in range(y0, y1 - size + 1, step):
        L.rect((x0, y, x0 + size, y + size), outline=None, fill=color, alpha=alpha)
        L.rect((x1 - size, y, x1, y + size), outline=None, fill=color, alpha=alpha)


def header(L, alpha=1.0):
    if alpha <= 0:
        return
    L.text((60, 56), "JUANITO COFFEE", pfont(600, 34), alpha=alpha)
    L.text((1020, 70), "NEW HARVEST", font(500, 20), anchor="ra", tracking=6, alpha=0.75 * alpha)


def tracker(img, L, stage, alpha=1.0, done=False):
    """Journey bar at the bottom: flower -> ... -> packaging."""
    if alpha <= 0:
        return img
    xs = [150 + i * 156 for i in range(len(STAGES))]
    y = 1772
    for i in range(len(STAGES) - 1):
        lit = done or i < stage
        c = ORANGE if lit else GREY
        for x in range(xs[i] + 34, xs[i + 1] - 30, 14):
            L.rect((x, y - 3, x + 6, y + 3), outline=None, fill=c,
                   alpha=alpha * (1 if lit else 0.5))
    for i, (kind, label) in enumerate(STAGES):
        if done:
            c, a = ORANGE, 1.0
        elif i < stage:
            c, a = CREAM, 0.9
        elif i == stage:
            c, a = ORANGE, 1.0
        else:
            c, a = GREY, 0.45
        img = blit(img, SP.icon(kind), xs[i] - 22, y - 22, 4, gap=0, alpha=a * alpha, color=c)
        if i == stage and not done:
            L.text((xs[i], 1838), label, font(600, 18), fill=ORANGE, anchor="mm", tracking=4,
                   alpha=alpha)
    return img


SWEEP_PAL = np.array([ORANGE, MAGENTA, WINE], np.float32) / 255


def sweep(img, t):
    """Colourful pixel wipe that hides every scene cut."""
    for b in CUTS:
        if b - 0.22 <= t < b + 0.22:
            cell = 60
            rows, cols = H // cell + 1, W // cell + 1
            yy, xx = np.mgrid[0:rows, 0:cols]
            d = xx / cols * 0.45 + yy / rows * 0.55
            d = d + np.random.default_rng(int(b * 10)).uniform(0, 0.08, d.shape)
            if t < b:
                on = d < (t - (b - 0.22)) / 0.2
            else:
                on = d >= (t - b) / 0.2
            colr = SWEEP_PAL[(xx + yy) % 3]
            col, a = dotmatrix(colr, on.astype(np.float32), cell, dot=cell - 4)
            img = composite(img, col[:H, :W], a[:H, :W], (0, 0))
    return img


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------


def scene_bloom(t, rng):
    img = black()
    b = ease_out((t - 0.15) / 1.2)
    fl = SP.flower(41, b, 0.3 + 0.25 * t)
    img = blit(img, fl, 540 - 41 * 8, 830 - 41 * 8, 16, gap=2, alpha=ease(t / 0.3))
    L = Layer()
    header(L, ease((t - 0.2) / 0.4))
    tx(L, t, 0.9, "SOMETHING", pfont(600, 112), (W // 2, 1330), anchor="ms", seed=1)
    tx(L, t, 1.15, "IS BLOOMING", pfont(600, 112), (W // 2, 1450), anchor="ms", seed=2)
    tx(L, t, 1.5, "(in Huila, Colombia)", font(300, 46, True), (W // 2, 1540), anchor="ms",
       seed=3)
    img = tracker(img, L, 0, ease((t - 0.4) / 0.4))
    return L.apply(img)


def scene_field(t, rng):
    img = black()
    lt = t - T_FIELD[0]
    drift = -50 * lt
    for f in FIELD:
        b = ease_out((t - f["t"]) / 0.35)
        if b <= 0:
            continue
        x, y, c = f["x"], f["y"] + drift, f["cell"]
        if f["leaf"]:
            lf = SP.leaf(18, 9, f["flip"])
            img = blit(img, lf, int(x + (2 if f["flip"] else -20) * c), int(y + 3 * c), c,
                       gap=1, alpha=b)
        fl = SP.flower(f["n"], b, f["rot"] + 0.3 * lt)
        img = blit(img, fl, int(x - f["n"] * c / 2), int(y - f["n"] * c / 2), c, gap=1)
    L = Layer()
    header(L)
    k = ease((t - 2.55) / 0.25)
    if k > 0:
        cy, hh = 975, 220 * k
        pixel_box(L, (100, cy - hh, 980, cy + hh), fill=DARK, color=CREAM)
        if k >= 1:
            tx(L, t, 2.8, "NEW HARVEST", pfont(600, 124), (W // 2, 1000), anchor="ms", seed=4)
            tx(L, t, 3.1, "COMING SOON", font(600, 28), (W // 2, 1100), anchor="ms",
               tracking=14, color=ORANGE, seed=5)
    img = tracker(img, L, 0)
    return L.apply(img)


def scene_origin(t, rng):
    img = black()
    lt = t - T_ORIGIN[0]
    cols, cell = 108, 10
    for k, (key, box, y0, rows, direction) in enumerate(BANDS):
        src, pal = SRC[key]
        g = palettize(sample_box(src, box, rows, cols, pan=0.012 * lt * direction), pal)
        col, a = dotmatrix(boost(g, 1.35, 0.05), np.ones((rows, cols), np.float32), cell,
                           dot=cell - 2)
        start = 0.05 + 0.22 * k
        for r in range(rows):
            p = ease_out((lt - start - r * 0.007) / 0.45)
            if p <= 0:
                continue
            dx = int(-direction * W * (1 - p))
            img = composite(img, col[r * cell:(r + 1) * cell], a[r * cell:(r + 1) * cell],
                            (dx, y0 + r * cell))
    L = Layer()
    header(L)
    tx(L, t, 4.45, "ORIGIN", font(600, 26), (W // 2, 712), anchor="ms", tracking=16, seed=10)
    tx(L, t, 4.6, "HUILA", pfont(700, 230), (W // 2, 915), anchor="ms", dur=0.45, seed=11)
    tx(L, t, 5.0, "COLOMBIA  ·  02°32′N  75°31′W", font(500, 22), (W // 2, 975), anchor="ms",
       tracking=6, seed=12)
    img = tracker(img, L, 1)
    return L.apply(img)


def scene_cherry(t, rng):
    img = black()
    lt = t - T_CHERRY[0]
    ripe = ease((lt - 0.35) / 1.7)
    ch = SP.cherries(48, ripe)
    sway = int(10 * math.sin(lt * 2.2))
    img = blit(img, ch, 540 - 24 * 14 + sway, 680, 14, gap=2, alpha=ease(lt / 0.25))
    L = Layer()
    header(L)
    tx(L, t, 7.15, "FROM FLOWER", pfont(600, 104), (70, 380), seed=20)
    tx(L, t, 7.55, "TO CHERRY", pfont(600, 104), (1010, 500), anchor="ra", seed=21,
       color=ORANGE)
    tx(L, t, 8.1, "(ripening in the mountains of Huila)", font(300, 42, True), (W // 2, 1620),
       anchor="ms", seed=22)
    img = tracker(img, L, 2)
    return L.apply(img)


def card_box(k):
    x0 = 80 + (k % 2) * 480
    y0 = 500 + (k // 2) * 560
    return x0, y0, x0 + 440, y0 + 520


def scene_varieties(t, rng):
    img = black()
    L = Layer()
    header(L)
    tx(L, t, 9.6, "NEW VARIETIES", pfont(600, 96), (W // 2, 340), anchor="ms", seed=30)
    tx(L, t, 9.8, "(coming soon)", font(300, 46, True), (W // 2, 420), anchor="ms", seed=31)
    cards = Layer()
    for k, (name, start, colr) in enumerate(VARIETIES):
        if t < start:
            continue
        x0, y0, x1, y1 = card_box(k)
        pixel_box(cards, (x0, y0, x1, y1), color=colr, fill=tuple(int(c * 0.16) for c in colr),
                  step=16, size=8)
        cards.text((x0 + 30, y0 + 30), f"0{k + 1}", font(600, 22), fill=colr, tracking=4)
        tx(cards, t, start + 0.05, name, pfont(600, 66), ((x0 + x1) // 2, y1 - 62), anchor="ms",
           seed=40 + k)
    # pixel dissolve of each card while it appears
    ca = np.asarray(cards.im).astype(np.float32) / 255
    mask = np.ones((H, W), np.float32)
    for k, (name, start, colr) in enumerate(VARIETIES):
        x0, y0, x1, y1 = card_box(k)
        p = (t - start) / 0.3
        if 0 <= p < 1:
            g = np.random.default_rng(100 + k).random(((y1 - y0) // 20 + 1, (x1 - x0) // 20 + 1))
            m = np.repeat(np.repeat((g < p).astype(np.float32), 20, 0), 20, 1)
            mask[y0:y1 + 1, x0:x1 + 1] = m[:y1 - y0 + 1, :x1 - x0 + 1]
    a = ca[..., 3] * mask
    img = img * (1 - a[..., None]) + ca[..., :3] * a[..., None]
    for k, (name, start, colr) in enumerate(VARIETIES):
        if t < start + 0.15:
            continue
        x0, y0, x1, y1 = card_box(k)
        bob = int(8 * math.sin(t * 3.2 + k * 1.3))
        img = blit(img, BEAN, (x0 + x1) // 2 - 9 * 10, y0 + 90 + bob, 10, gap=1,
                   alpha=ease((t - start - 0.15) / 0.2))
    tx(L, t, 12.4, "ONE ORIGIN  ·  HUILA", font(600, 24), (W // 2, 1660), anchor="ms",
       tracking=10, seed=50)
    img = tracker(img, L, 3)
    return L.apply(img)


STEAM_BLOCK = np.ones((10, 10, 3), np.float32) * np.array(CREAM, np.float32) / 255


def scene_cup(t, rng):
    img = black()
    lt = t - T_CUP[0]
    cx, top, cell = 540, 930, 12
    sa = ease((t - 14.2) / 0.5)
    if sa > 0:
        for w_i, x0 in enumerate((cx - 130, cx - 30, cx + 70)):
            for j in range(26):
                y = top - 40 - j * 14
                x = x0 + 26 * math.sin(j * 0.42 - lt * 4.5 + w_i * 2.1)
                a = sa * (1 - j / 26) ** 1.4 * 0.75
                if a > 0.02:
                    composite(img, STEAM_BLOCK, np.full((10, 10), a, np.float32),
                              (int(x), int(y)))
    img = blit(img, CUP, cx - 31 * cell, top - 30, cell, gap=1, alpha=ease(lt / 0.25))
    # green beans dropping into the cup
    for s, x in BEAN_DROPS:
        u = t - s
        if 0 <= u < 0.42:
            y = -120 + (top - 10 + 120) * (u / 0.42) ** 2
            img = blit(img, BEAN, int(x), int(y), 4, gap=0)
    L = Layer()
    header(L)
    tx(L, t, 13.65, "YOUR NEXT", pfont(600, 104), (W // 2, 330), anchor="ms", seed=60)
    tx(L, t, 13.95, "FAVORITE CUP", pfont(600, 104), (W // 2, 450), anchor="ms", seed=61,
       color=ORANGE)
    tx(L, t, 14.6, "(every bean tells a story)", font(300, 46, True), (W // 2, 1560),
       anchor="ms", seed=62)
    img = tracker(img, L, 4)
    return L.apply(img)


def scene_pack(t, rng):
    img = black()
    lt = t - T_PACK[0]
    cell, px, py = 15, 240, 480
    trace = clamp01((lt - 0.05) / 0.55)
    edge = POUCH_EDGE.copy()
    edge[..., 3] *= (POUCH_ORDER <= trace).astype(np.float32)
    # scrambled interior: brand colours only, never the real design
    fill = clamp01((lt - 0.45) / 0.4)
    if fill > 0:
        r = np.random.default_rng(int(t * FPS) // 2)
        idx = r.integers(0, len(BRAND), POUCH_IN.shape)
        inner = np.zeros(POUCH_IN.shape + (4,), np.float32)
        inner[..., :3] = BRAND[idx] * 0.85
        scan = int((lt * 30) % 56)
        inner[scan:scan + 2, :, :3] = np.minimum(1, inner[scan:scan + 2, :, :3] + 0.35)
        inner[..., 3] = POUCH_IN * fill * (r.random(POUCH_IN.shape) < 0.55 + 0.45 * fill)
        img = blit(img, inner, px, py, cell, gap=2)
    img = blit(img, edge, px, py, cell, gap=2)
    if lt > 0.9:
        k = ease((lt - 0.9) / 0.2)
        lc = 14
        lw, lh = LOCK.shape[1] * lc, LOCK.shape[0] * lc
        lx, ly = px + 20 * cell - lw // 2, py + 30 * cell - lh // 2
        L0 = Layer()
        L0.rect((lx - 36, ly - 36, lx + lw + 36, ly + lh + 36), outline=None, fill=DARK,
                alpha=0.95 * k)
        img = L0.apply(img)
        img = blit(img, LOCK, lx, ly, lc, gap=2, alpha=k)
    L = Layer()
    header(L)
    tx(L, t, 16.1, "NEW PACKAGING", pfont(600, 100), (W // 2, 330), anchor="ms", seed=70)
    tx(L, t, 16.45, "(we can't show it yet...)", font(300, 44, True), (W // 2, 410),
       anchor="ms", seed=71)
    if t >= LOAD_START - 0.2:
        p = LOAD_MAX * clamp01((t - LOAD_START) / (LOAD_END - LOAD_START))
        L.text((120, 1398), "LOADING", font(600, 22), tracking=8, anchor="ls")
        L.text((960, 1396), f"{int(round(p * 100))}%", pfont(600, 44), anchor="rs", fill=ORANGE)
        pixel_box(L, (120, 1412, 960, 1472), color=CREAM, step=10, size=5)
        segs = int(NSEG * p + 1e-6)
        sw = (960 - 120 - 24) / NSEG
        for s in range(segs):
            x = 132 + s * sw
            L.rect((x, 1424, x + sw - 6, 1460), outline=None, fill=ORANGE)
        if t > 18.7 and int((t - 18.7) * 4) % 2 == 0:
            L.text((W // 2, 1580), "ALMOST READY...", pfont(600, 56), anchor="ms", fill=ORANGE)
    img = tracker(img, L, 5)
    return L.apply(img)


OUTRO_FLOWERS = [(150, 560, 25, 10, 20.1), (930, 700, 25, 10, 20.3),
                 (200, 1000, 17, 8, 20.5), (890, 420, 17, 8, 20.7)]


def scene_outro(t, rng):
    img = black()
    lt = t - T_OUTRO[0]
    lx, ly = (W - LOGO_W) // 2, 470
    on = ((LOGO_GRID > 0.3) & (LOGO_T <= lt)).astype(np.float32)
    k = ease((lt - 0.85) / 0.3)
    c = np.ones(LOGO_GRID.shape + (3,), np.float32) * (np.array(INK, np.float32) / 255)
    col, a = dotmatrix(c, on * (1 - k), LOGO_CELL, dot=4)
    composite(img, col, a, (lx, ly))
    if k > 0:
        solid = np.ones(LOGO_A.shape + (3,), np.float32) * (np.array(INK, np.float32) / 255)
        composite(img, solid, LOGO_A * k, (lx, ly))
    for i, (x, y, n, cell, s) in enumerate(OUTRO_FLOWERS):
        b = ease_out((t - s) / 0.4)
        if b > 0:
            img = blit(img, SP.flower(n, b, 0.4 * t + i), x - n * cell // 2, y - n * cell // 2,
                       cell, gap=1)
    L = Layer()
    tx(L, t, 20.5, "GREEN COFFEE", pfont(600, 96), (W // 2, 1150), anchor="ms", seed=90)
    tx(L, t, 20.75, "FROM HUILA, COLOMBIA", font(600, 24), (W // 2, 1215), anchor="ms",
       tracking=10, seed=91)
    if t >= 21.1:
        cursor = "_" if int(t * 3) % 2 == 0 else " "
        tx(L, t, 21.1, "COMING SOON", pfont(600, 64), (W // 2, 1350), anchor="ms",
           color=ORANGE, seed=92)
        if t > 21.5:
            L.text((W // 2 + 205, 1350), cursor, pfont(600, 64), fill=ORANGE, anchor="ls")
    tx(L, t, 21.5, "@JUANITOCOFFEE", font(600, 34), (W // 2, 1450), anchor="ms", tracking=8,
       seed=93)
    img = tracker(img, L, len(STAGES), alpha=ease((lt - 0.3) / 0.4), done=True)
    return L.apply(img)


SCENES = [(T_BLOOM, scene_bloom), (T_FIELD, scene_field), (T_ORIGIN, scene_origin),
          (T_CHERRY, scene_cherry), (T_VARIETIES, scene_varieties), (T_CUP, scene_cup),
          (T_PACK, scene_pack), (T_OUTRO, scene_outro)]


def render(i):
    t = i / FPS
    rng = np.random.default_rng(1000 + i)
    fn = SCENES[-1][1]
    for (a, b), f in SCENES:
        if a <= t < b:
            fn = f
            break
    img = fn(t, rng)
    img = sweep(img, t)
    n = rng.random((H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[..., None]
    img = img + (n - 0.5) * 0.05
    img = scanlines(img, 0.06)
    return to_u8(img).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="comma-separated seconds to preview")
    ap.add_argument("--out", default=os.path.join(BUILD, "reel_silent.mp4"))
    args = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    if args.stills:
        for s in args.stills.split(","):
            im = Image.frombytes("RGB", (W, H), render(int(float(s) * FPS)))
            p = os.path.join(BUILD, f"still_{float(s):05.2f}.png")
            im.save(p)
            print(p)
        return
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render, range(NFRAMES), chunksize=2)):
            proc.stdin.write(buf)
            if k % 96 == 0:
                print(f"frame {k}/{NFRAMES}", file=sys.stderr, flush=True)
    proc.stdin.close()
    proc.wait()
    print(args.out)


if __name__ == "__main__":
    main()
