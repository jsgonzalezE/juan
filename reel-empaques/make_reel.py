"""Juanito Coffee — new packaging / green coffee reel (1080x1920, 24 fps).

Usage:
    python3 make_reel.py                 # render build/reel_silent.mp4
    python3 make_reel.py --stills 2,7,11 # render preview PNGs at given seconds
"""
import argparse
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

from bean import bean_grid
from fx import (BG, CREAM, FPS, H, INK, MAGENTA, ORANGE, PURPLE, RED, W, Layer,
                bayer, boost, clamp01, composite, decode, dotmatrix, ease,
                ease_out, font, glitch, load, luminance, sample_grid,
                scanlines, static_tv, to_u8)

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")

# ---------------------------------------------------------------------------
# Timeline (seconds) — cuts sit on a 120 BPM grid so the soundtrack can lock to it
# ---------------------------------------------------------------------------
T_INTRO = (0.0, 1.0)
T_ORIGIN = (1.0, 4.0)
T_COORDS = (4.0, 5.5)
T_STORY = (5.5, 9.0)
T_VARIETIES = (9.0, 13.5)
T_PACK = (13.5, 17.5)
T_JOURNEY = (17.5, 19.5)
T_OUTRO = (19.5, 23.5)
DURATION = 23.5
NFRAMES = int(round(DURATION * FPS))

VARIETIES = [  # name, appear time (absolute s), bean colour
    ("JAVA", 9.5, ORANGE),
    ("CASTILLO", 10.5, MAGENTA),
    ("GEISHA", 11.5, (196, 120, 214)),
    ("BOURBON", 12.5, RED),
]

# ---------------------------------------------------------------------------
# Assets (loaded once, shared by forked workers)
# ---------------------------------------------------------------------------


def make_palette(img, n=28):
    q = img.resize((img.width // 3, img.height // 3)).quantize(
        colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:n * 3], np.float32).reshape(n, 3) / 255.0
    return pal


def palettize(g, pal):
    d = ((g[..., None, :] - pal[None, None]) ** 2).sum(-1)
    return pal[d.argmin(-1)]


SRC = {}
for key in ("wc_cherries", "wc_picker", "wc_mule_dog", "wc_mule_blue"):
    im = load(key + ".jpg")
    # stretch levels so the washed watercolours stay punchy as dots on black
    arr = np.asarray(im).astype(np.float32)
    lo, hi = np.percentile(luminance(arr), (2, 99))
    arr = np.clip((arr - lo) / (hi - lo), 0, 1)
    im = Image.fromarray(to_u8(arr))
    SRC[key] = (im, make_palette(im))

PACK1 = Image.open(os.path.join(HERE, "assets", "pack_color_front.png")).convert("RGB")
PACK2 = load("pack_dark_front.jpg")
P1_W = 600
P1_H = round(P1_W * PACK1.height / PACK1.width)
P2_W = 640
P2_H = round(P2_W * PACK2.height / PACK2.width)
PACK1_D = np.asarray(PACK1.resize((P1_W, P1_H), Image.LANCZOS)).astype(np.float32) / 255
PACK2_D = np.asarray(PACK2.resize((P2_W, P2_H), Image.LANCZOS)).astype(np.float32) / 255

LOGO = Image.open(os.path.join(HERE, "assets", "logo_white.png"))
LOGO_W = 420
LOGO_H = round(LOGO_W * LOGO.height / LOGO.width)
LOGO_A = np.asarray(LOGO.resize((LOGO_W, LOGO_H), Image.LANCZOS))[..., 3].astype(np.float32) / 255
LOGO_CELL = 6
_lr, _lc = LOGO_H // LOGO_CELL, LOGO_W // LOGO_CELL
LOGO_GRID = np.asarray(LOGO.resize((_lc, _lr), Image.BOX))[..., 3].astype(np.float32) / 255
LOGO_T = np.random.default_rng(7).uniform(0.15, 0.85, LOGO_GRID.shape).astype(np.float32)

# ---------------------------------------------------------------------------
# HUD (static parts pre-rendered)
# ---------------------------------------------------------------------------


def build_hud():
    L = Layer()
    f = font(600, 20)
    fl = font(400, 20)
    L.text((60, 66), "JUANITO COFFEE", f, tracking=3)
    L.text((60, 94), "NEW HARVEST", fl, tracking=3, alpha=0.7)
    # top-right origin box
    L.rect((800, 60, 1020, 118), width=2, alpha=0.8)
    L.line([(800, 89), (1020, 89)], width=2, alpha=0.8)
    L.text((812, 67), "ORIGIN", fl, tracking=3)
    L.text((1008, 67), "HUILA", f, tracking=3, anchor="ra")
    # bottom-left coordinates
    L.text((60, 1812), "LAT 2.5359 N", f, tracking=3)
    L.text((60, 1840), "LON 75.5277 W", f, tracking=3)
    # bottom-right hatch + label
    for i in range(12):
        x = 900 + i * 10
        L.line([(x, 1792), (x + 10, 1772)], width=2, alpha=0.85)
    L.text((1020, 1812), "GREEN COFFEE", f, tracking=3, anchor="ra")
    L.text((1020, 1840), "COLOMBIA", fl, tracking=3, anchor="ra", alpha=0.7)
    # vertical side label
    side = Layer()
    s = "HUILA  —  COLOMBIA  —  02°32′N  75°31′W"
    side.text((W // 2, 20), s, font(500, 18), tracking=4, anchor="mt", alpha=0.65)
    strip = side.im.crop((0, 0, W, 60)).rotate(-90, expand=True)
    L.im.alpha_composite(strip, (W - 50, (H - strip.height) // 2))
    a = np.asarray(L.im).astype(np.float32) / 255
    return a[..., :3].copy(), a[..., 3].copy()


HUD_RGB, HUD_A = build_hud()


def hud(frame, t, alpha=1.0):
    if alpha <= 0:
        return frame
    a = HUD_A * alpha
    frame = frame * (1 - a[..., None]) + HUD_RGB * a[..., None]
    # running timecode
    L = Layer()
    s = int(t)
    ff = int((t - s) * FPS)
    L.text((1020, 140), f"00:00:{s:02d}:{ff:02d}", font(500, 18), tracking=3, anchor="ra",
           alpha=0.6 * alpha)
    return L.apply(frame)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def black():
    img = np.empty((H, W, 3), np.float32)
    img[:] = np.array(BG, np.float32) / 255
    return img


def mosaic(key, rows, cols, cell, zoom, cx, cy, p_dev, q_color, gap=2):
    src, pal = SRC[key]
    g = palettize(sample_grid(src, rows, cols, zoom, cx, cy), pal)
    lum = luminance(g)
    th = bayer(rows, cols)
    v = lum * 1.2 - 1.2 + 2.2 * p_dev
    on = (v > th).astype(np.float32)
    mono = (np.array(ORANGE, np.float32) / 255) * (0.3 + 0.9 * lum[..., None])
    col = mono * (1 - q_color) + boost(g, 1.4, 0.06) * q_color
    return dotmatrix(col, on, cell, dot=cell - gap)


def vgrad(y0, y1, a0, a1):
    """Per-row multiplier ramp (H,1,1)."""
    m = np.ones(H, np.float32)
    ys = np.arange(H)
    r = np.clip((ys - y0) / max(1, (y1 - y0)), 0, 1)
    sel = (ys >= y0)
    m[sel] = (a0 + (a1 - a0) * r[sel])
    return m[:, None, None]


SHADE_BOTTOM = vgrad(1100, 1920, 1.0, 0.12)
SHADE_TOP = np.minimum(1.0, 0.22 + np.arange(H, dtype=np.float32) / 460)[:, None, None]


def tx(L, t, start, text, f, xy, anchor="la", dur=0.4, color=INK, tracking=0, seed=0,
       end=None, fade=0.25):
    if t < start:
        return
    p = (t - start) / dur
    a = 1.0
    if end is not None and t > end - fade:
        a = clamp01((end - t) / fade)
    L.text(xy, decode(text, p, seed), f, fill=color, anchor=anchor, tracking=tracking, alpha=a)


def depixelate(img, cell, gap_from=6):
    h, w = img.shape[:2]
    if cell <= 1:
        return img, np.ones((h, w), np.float32)
    rows, cols = max(1, h // cell), max(1, w // cell)
    small = np.asarray(Image.fromarray(to_u8(img)).resize((cols, rows), Image.BOX)).astype(np.float32) / 255
    if cell >= gap_from:
        col, a = dotmatrix(small, np.ones((rows, cols), np.float32), cell, dot=cell - 2)
    else:
        col = np.repeat(np.repeat(small, cell, 0), cell, 1)
        a = np.ones(col.shape[:2], np.float32)
    out = np.zeros_like(img)
    oa = np.zeros((h, w), np.float32)
    out[:col.shape[0], :col.shape[1]] = col[:h, :w]
    oa[:col.shape[0], :col.shape[1]] = a[:h, :w]
    return out, oa


DEPIX_STEPS = [90, 64, 48, 36, 24, 16, 12, 8, 4, 2, 1]


def depix_cell(p):
    i = int(clamp01(p) * (len(DEPIX_STEPS) - 1) + 1e-6)
    return DEPIX_STEPS[i]


def brackets(L, box, size=40, alpha=1.0, width=3):
    x0, y0, x1, y1 = box
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        L.line([(x, y + dy * size), (x, y), (x + dx * size, y)], width=width, alpha=alpha)


# ---------------------------------------------------------------------------
# Scenes — each returns the frame (float HxWx3) for absolute time t
# ---------------------------------------------------------------------------


def scene_intro(t, rng):
    img = static_tv(rng, t)
    # logo flickers through the static
    if 0.3 < t < 0.85 and rng.random() < 0.6:
        x = (W - LOGO_W) // 2
        y = 700
        a = LOGO_A * 0.85
        lay = np.ones(LOGO_A.shape + (3,), np.float32)
        composite(img, lay, a, (x + int(rng.integers(-12, 12)), y))
    if t > 0.75:
        img = glitch(img, rng, 1.2)
    return img


def scene_origin(t, rng):
    lt = t - T_ORIGIN[0]
    p = ease(lt / 1.1)
    q = ease((lt - 0.55) / 0.9)
    zoom = 1.0 + 0.16 * ease(lt / 3.0)
    col, a = mosaic("wc_cherries", 192, 108, 10, zoom, 0.42, 0.72, p, q)
    img = black()
    img = img * (1 - a[..., None]) + col * a[..., None]
    img *= SHADE_BOTTOM * SHADE_TOP
    if lt < 0.35:  # static bleeding out
        k = 1 - lt / 0.35
        img = img * (1 - k * 0.8) + static_tv(rng, t) * k * 0.8
    L = Layer()
    tx(L, t, 2.0, "(origin", font(300, 58, True), (78, 1440), seed=11)
    tx(L, t, 2.2, "HUILA", font(300, 210), (62, 1660), anchor="ls", tracking=8, dur=0.5, seed=12)
    tx(L, t, 2.6, "COLOMBIA)", font(500, 34), (1012, 1728), anchor="rs", tracking=10, seed=13)
    img = L.apply(img)
    img = hud(img, t, ease((lt - 0.3) / 0.5))
    return img


def scene_coords(t, rng):
    lt = t - T_COORDS[0]
    img = black()
    L = Layer()
    items = ["HUILA,", "02°32′ N", "75°31′ W"]
    i = min(2, int(lt / 0.5))
    tx(L, lt, i * 0.5, items[i], font(400, 66), (W // 2, H // 2), anchor="mm",
       tracking=6, dur=0.22, seed=20 + i)
    return L.apply(img)


def scene_story(t, rng):
    lt = t - T_STORY[0]
    img = black()
    wx, wy, cols, rows, cell = 70, 300, 94, 100, 10
    p = ease(lt / 0.8)
    q = ease((lt - 0.2) / 0.6)
    zoom = 1.12 + 0.12 * ease(lt / 3.5)
    col, a = mosaic("wc_picker", rows, cols, cell, zoom, 0.62, 0.66, p, q)
    composite(img, col, a, (wx, wy))
    L = Layer()
    box = (wx - 14, wy - 14, wx + cols * cell + 14, wy + rows * cell + 14)
    brackets(L, box, size=46, alpha=ease(lt / 0.4))
    tx(L, t, T_STORY[0] + 0.2, "PLATE 01 — ORIGINAL WATERCOLOR", font(500, 20), (wx, wy - 46),
       tracking=4, seed=30)
    tx(L, t, T_STORY[0] + 0.6, "GROWN", font(300, 190), (56, 1480), anchor="ls", tracking=10,
       dur=0.45, seed=31)
    tx(L, t, T_STORY[0] + 1.1, "(with love", font(300, 74, True), (1010, 1570), anchor="rs", seed=32)
    tx(L, t, T_STORY[0] + 1.4, "& respect for the land)", font(300, 46, True), (1010, 1636),
       anchor="rs", seed=33)
    tx(L, t, T_STORY[0] + 1.9, "EVERY BEAN THAT REACHES YOUR CUP", font(500, 22), (W // 2, 1712),
       anchor="ms", tracking=6, dur=0.5, seed=34)
    tx(L, t, T_STORY[0] + 2.1, "TELLS OUR STORY", font(500, 22), (W // 2, 1748), anchor="ms",
       tracking=6, dur=0.5, seed=35)
    img = L.apply(img)
    img = hud(img, t)
    if lt > 3.35:
        img = glitch(img, rng, 1.0)
    return img


def bean_color(t):
    c = np.array(VARIETIES[0][2], np.float32)
    for name, start, colr in VARIETIES[1:]:
        k = ease((t - start) / 0.3)
        c = c * (1 - k) + np.array(colr, np.float32) * k
    return c / 255


def scene_varieties(t, rng):
    lt = t - T_VARIETIES[0]
    img = black()
    out_p = ease((lt - 4.15) / 0.35)  # exit dissolve
    # orange blotch transition
    if lt < 0.3:
        g = rng.random((16, 9)).astype(np.float32)
        g = np.asarray(Image.fromarray(to_u8(g)).resize((108, 192), Image.BICUBIC)).astype(np.float32) / 255
        on = (g > 0.62).astype(np.float32)
        c = np.zeros((192, 108, 3), np.float32)
        c[:] = np.array(ORANGE, np.float32) / 255
        col, a = dotmatrix(c, on, 10, dot=8)
        return img * (1 - a[..., None]) + col * a[..., None]
    # faint grey leaves in the background
    rows, cols, cell = 320, 180, 6
    src, pal = SRC["wc_cherries"]
    g = sample_grid(src, rows, cols, 1.7, 0.30, 0.80 - 0.02 * lt)
    lum = luminance(g)
    th = bayer(rows, cols)
    on = ((lum * 1.1 - 0.1) > th).astype(np.float32) * ease((lt - 0.3) / 0.6) * (1 - out_p)
    c = np.full((rows, cols, 3), 0.55, np.float32)
    col, a = dotmatrix(c, on, cell, dot=4)
    img = img * (1 - 0.22 * a[..., None]) + col * 0.22 * a[..., None]
    # rotating bean
    n, cell = 112, 7
    shade, hit = bean_grid(n, 0.3 + 0.95 * lt, tilt=0.5 + 0.15 * math.sin(lt * 0.8),
                           wobble=0.35 * math.sin(lt * 0.6))
    dev = ease((lt - 0.3) / 0.6) * (1 - out_p)
    on = ((shade ** 0.85) * dev > bayer(n, n)) & hit
    colr = bean_color(t)
    bc = np.clip(colr * (0.85 + 0.45 * shade[..., None]), 0, 1)
    col, a = dotmatrix(bc.astype(np.float32), on.astype(np.float32), cell, dot=5)
    composite(img, col, a, (W // 2 - n * cell // 2, 990 - n * cell // 2))
    # text
    L = Layer()
    end = T_VARIETIES[1] - 0.05
    tx(L, t, T_VARIETIES[0] + 0.3, "(coming soon)", font(300, 58, True), (70, 300), seed=40, end=end)
    tx(L, t, T_VARIETIES[0] + 0.45, "NEW VARIETIES", font(500, 22), (1010, 292), anchor="ra",
       tracking=6, seed=41, end=end)
    places = [((70, 560), "ls"), ((1010, 760), "rs"), ((70, 1430), "ls"), ((1010, 1630), "rs")]
    for i, ((name, start, colr), (xy, anc)) in enumerate(zip(VARIETIES, places)):
        tx(L, t, start, name, font(300, 132), xy, anchor=anc, tracking=6, dur=0.35, seed=50 + i,
           end=end)
        tag = f"0{i + 1}"
        ty = xy[1] - 150
        if t >= start:
            a = 1.0 if t < end - 0.25 else clamp01((end - t) / 0.25)
            x = xy[0] if anc[0] == "l" else xy[0] - 54
            L.rect((x, ty, x + 54, ty + 32), outline=colr, width=2, alpha=a)
            L.text((x + 27, ty + 16), tag, font(600, 18), fill=colr, anchor="mm", alpha=a)
    tx(L, t, 13.0, "FOUR VARIETIES  ·  ONE ORIGIN", font(500, 24), (W // 2, 1720), anchor="ms",
       tracking=6, dur=0.3, seed=60, end=end)
    img = L.apply(img)
    img = hud(img, t)
    return img


def scene_pack(t, rng):
    lt = t - T_PACK[0]
    img = black()
    swap = 2.0  # local time of the swap to pack 2
    L = Layer()
    if lt < swap:
        pk, pw, ph = PACK1_D, P1_W, P1_H
        p = (lt - 0.1) / 0.9
        idx = "01 / 02"
    else:
        pk, pw, ph = PACK2_D, P2_W, P2_H
        p = (lt - swap - 0.05) / 0.7
        idx = "02 / 02"
    if p > 0:
        x = (W - pw) // 2
        y = 1060 - ph // 2 + int(6 * math.sin(lt * 2.2))
        col, a = depixelate(pk, depix_cell(p))
        composite(img, col, a, (x, y))
        k = ease(p * 1.5)
        L.rect((x - 2, y - 2, x + pw + 1, y + ph + 1), width=2, alpha=0.5 * k)
        brackets(L, (x - 22, y - 22, x + pw + 22, y + ph + 22), size=44, alpha=k)
        L.text((x + pw + 22, y + ph + 40), idx, font(600, 20), anchor="ra", tracking=4, alpha=k)
    tx(L, t, T_PACK[0] + 0.05, "NEW", font(300, 170), (62, 400), anchor="ls", tracking=10,
       dur=0.35, seed=70)
    tx(L, t, T_PACK[0] + 0.3, "PACKAGING", font(300, 104), (1016, 520), anchor="rs", tracking=4,
       dur=0.45, seed=71)
    tx(L, t, T_PACK[0] + 1.0, "(a new look for a new harvest)", font(300, 48, True),
       (W // 2, 1660), anchor="ms", dur=0.5, seed=72)
    img = L.apply(img)
    img = hud(img, t)
    if swap - 0.12 < lt < swap + 0.08 or lt > 3.88:
        img = glitch(img, rng, 1.0)
    return img


def scene_journey(t, rng):
    lt = t - T_JOURNEY[0]
    cut = 1.0
    if lt < cut:
        key, l2, cx, cy = "wc_mule_dog", lt, 0.40, 0.62
        small, big, s1, s2 = "FROM OUR", "MOUNTAINS", 80, 81
    else:
        key, l2, cx, cy = "wc_mule_blue", lt - cut, 0.45, 0.66
        small, big, s1, s2 = "TO YOUR", "ROASTERY", 82, 83
    p = ease(l2 / 0.35)
    q = ease((l2 - 0.1) / 0.3)
    col, a = mosaic(key, 192, 108, 10, 1.12 + 0.08 * l2, cx, cy, p, q)
    img = black()
    img = img * (1 - a[..., None]) + col * a[..., None]
    img *= SHADE_BOTTOM * SHADE_TOP
    L = Layer()
    t0 = T_JOURNEY[0] + (0 if lt < cut else cut)
    tx(L, t, t0 + 0.15, small, font(500, 40), (W // 2, 1480), anchor="ms", tracking=14,
       dur=0.25, seed=s1)
    tx(L, t, t0 + 0.25, big, font(300, 150), (W // 2, 1650), anchor="ms", tracking=6,
       dur=0.35, seed=s2)
    img = L.apply(img)
    img = hud(img, t)
    if abs(lt - cut) < 0.09 or lt > 1.93:
        img = glitch(img, rng, 1.1)
    return img


TICKER = "HUILA  •  JAVA  •  CASTILLO  •  GEISHA  •  BOURBON  •  NEW PACKAGING  •  "


def ticker(L, y, offset, alpha=1.0):
    f = font(600, 20)
    tw = sum(f.getlength(c) + 4 for c in TICKER)
    x = -(offset % tw)
    while x < W:
        L.text((x, y), TICKER, f, tracking=4, anchor="lm", alpha=alpha)
        x += tw


def scene_outro(t, rng):
    lt = t - T_OUTRO[0]
    if lt < 0.12:
        return glitch(static_tv(rng, t), rng, 1.0)
    img = black()
    lx, ly = (W - LOGO_W) // 2, 560
    # logo assembling from dots, then resolving
    on = ((LOGO_GRID > 0.3) & (LOGO_T <= lt)).astype(np.float32)
    k = ease((lt - 0.95) / 0.3)
    c = np.ones(LOGO_GRID.shape + (3,), np.float32) * (np.array(INK, np.float32) / 255)
    col, a = dotmatrix(c, on * (1 - k), LOGO_CELL, dot=4)
    composite(img, col, a, (lx, ly))
    if k > 0:
        solid = np.ones(LOGO_A.shape + (3,), np.float32) * (np.array(INK, np.float32) / 255)
        composite(img, solid, LOGO_A * k, (lx, ly))
    L = Layer()
    tx(L, t, T_OUTRO[0] + 0.3, "NEW LOOK  ·  NEW HARVEST", font(500, 24), (W // 2, 470),
       anchor="ms", tracking=8, dur=0.4, seed=90)
    tx(L, t, T_OUTRO[0] + 1.1, "GREEN COFFEE", font(400, 76), (W // 2, 1230), anchor="ms",
       tracking=12, dur=0.4, seed=91)
    tx(L, t, T_OUTRO[0] + 1.4, "(samples & pricing via DM)", font(300, 46, True), (W // 2, 1310),
       anchor="ms", dur=0.4, seed=92)
    tx(L, t, T_OUTRO[0] + 1.8, "@JUANITOCOFFEE", font(600, 36), (W // 2, 1470), anchor="ms",
       tracking=8, dur=0.4, color=ORANGE, seed=93)
    tx(L, t, T_OUTRO[0] + 2.0, "HUILA, COLOMBIA", font(500, 22), (W // 2, 1525), anchor="ms",
       tracking=8, dur=0.4, seed=94)
    # tickers
    ka = ease((lt - 0.2) / 0.4)
    for y in (40, 92, 1828, 1880):
        L.line([(0, y), (W, y)], width=2, alpha=0.6 * ka)
    ticker(L, 66, lt * 90, ka)
    ticker(L, 1854, -lt * 90 + 400, ka)
    return L.apply(img)


SCENES = [
    (T_INTRO, scene_intro),
    (T_ORIGIN, scene_origin),
    (T_COORDS, scene_coords),
    (T_STORY, scene_story),
    (T_VARIETIES, scene_varieties),
    (T_PACK, scene_pack),
    (T_JOURNEY, scene_journey),
    (T_OUTRO, scene_outro),
]


def render(i):
    t = i / FPS
    rng = np.random.default_rng(1000 + i)
    fn = SCENES[-1][1]
    for (a, b), f in SCENES:
        if a <= t < b:
            fn = f
            break
    img = fn(t, rng)
    # global film grain + scanlines
    n = rng.random((H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[..., None]
    img = img + (n - 0.5) * 0.06
    img = scanlines(img, 0.07)
    return to_u8(img).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="comma-separated seconds to preview")
    ap.add_argument("--out", default=os.path.join(BUILD, "reel_silent.mp4"))
    args = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    if args.stills:
        for s in args.stills.split(","):
            i = int(float(s) * FPS)
            buf = render(i)
            im = Image.frombytes("RGB", (W, H), buf)
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
            if k % 48 == 0:
                print(f"frame {k}/{NFRAMES}", file=sys.stderr, flush=True)
    proc.stdin.close()
    proc.wait()
    print(args.out)


if __name__ == "__main__":
    main()
