"""Helpers for the minimal teasers: single dithered objects on black, small type."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter

import common as C
from fx import INK, ORANGE, H, W, Layer, bayer, clamp01, composite, dotmatrix, ease, font

BGC = (11, 10, 10)
ACCENT = ORANGE


def _norm_lum(rgb, mask):
    lum = C.luminance(rgb)
    sel = lum[mask > 0.5]
    if sel.size < 10:
        return lum
    lo, hi = np.percentile(sel, (4, 98))
    return np.clip((lum - lo) / max(1e-3, hi - lo), 0, 1)


def _clean(mask, radius=2):
    im = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius))
    return (np.asarray(im).astype(np.float32) / 255 > 0.5).astype(np.float32)


@lru_cache(maxsize=None)
def watercolor_cutout(kind):
    im = C.IMAGES["wc_cherries"]
    w, h = im.size
    if kind == "flower":
        box = (0.595, 0.638, 0.795, 0.748)
    else:
        box = (0.0, 0.72, 0.48, 0.995)
    c = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    a = np.asarray(c).astype(np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum, sat = a.mean(2), a.max(2) - a.min(2)
    if kind == "flower":
        m = (lum > 150 / 255) & (sat < 70 / 255)
    else:
        m = ((r - g) > 28 / 255) & ((r - b) > 10 / 255)
    m = _clean(m.astype(np.float32), 3 if kind == "flower" else 2)
    return a, m


@lru_cache(maxsize=None)
def object_grid(kind, cols):
    """(lum, mask) grids with `cols` columns for a cut-out object."""
    a, m = watercolor_cutout(kind)
    h, w = m.shape
    rows = max(1, round(cols * h / w))
    rgb = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((cols, rows), Image.BOX))
    rgb = rgb.astype(np.float32) / 255
    mm = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((cols, rows), Image.BOX))
    mm = (mm.astype(np.float32) / 255 > 0.45).astype(np.float32)
    lum = _norm_lum(rgb, mm)
    return lum, mm


_orders = {}


def order(shape, seed):
    key = (shape, seed)
    if key not in _orders:
        _orders[key] = np.random.default_rng(seed).random(shape).astype(np.float32)
    return _orders[key]


def draw_obj(img, lum, mask, cx, cy, cell=6, p=1.0, color=ACCENT, seed=0, gain=1.0, dot=None,
             floor=0.12):
    """Ordered-dither an object into dots; p in [0,1] reveals dots in random order."""
    if p <= 0:
        return img
    r, c = lum.shape
    v = np.clip(floor + (1 - floor) * lum * gain, 0, 1) * mask
    on = (v > bayer(r, c)) & (order((r, c), seed) < p)
    colr = np.array(color, np.float32) / 255
    rgb = np.clip(colr * (0.55 + 0.6 * v[..., None]), 0, 1).astype(np.float32)
    col, a = dotmatrix(rgb, on.astype(np.float32), cell, dot=dot or cell - 2)
    return composite(img, col, a, (int(cx - c * cell / 2), int(cy - r * cell / 2)))


def window(t, t0, t1, fin=0.5, fout=0.35):
    """Reveal factor: ramps in after t0, out before t1."""
    return clamp01((t - t0) / fin) * clamp01((t1 - t) / fout)


def mixed_line(L, parts, cx, y, alpha=1.0):
    """Draw [(text, font, tracking, color)] on one baseline, centred at cx."""
    widths = [sum(f.getlength(ch) for ch in s) + tr * max(0, len(s) - 1) for s, f, tr, _ in parts]
    gap = 18
    total = sum(widths) + gap * (len(parts) - 1)
    x = cx - total / 2
    for (s, f, tr, col), w in zip(parts, widths):
        L.text((x, y), s, f, fill=col, tracking=tr, anchor="ls", alpha=alpha)
        x += w + gap


def hud(L, t, duration, label="NEW HARVEST", alpha=1.0):
    a = 0.55 * alpha
    L.text((60, 64), "JUANITO COFFEE", font(500, 18), tracking=6, alpha=alpha * 0.85)
    L.text((1020, 64), label, font(400, 18), tracking=6, anchor="ra", alpha=a)
    L.text((60, 1856), "HUILA · COLOMBIA", font(400, 18), tracking=6, anchor="ls", alpha=a)
    L.text((1020, 1856), f"{t:05.2f}", font(400, 18), tracking=4, anchor="rs", alpha=a)


def finish(img, rng, t, duration):
    # gentle vignette + grain
    img = C.grain(img, rng, 0.05)
    if t < 0.4:
        img *= ease(t / 0.4)
    if t > duration - 0.5:
        img *= ease((duration - t) / 0.5) * 0.85 + 0.15
    return img
