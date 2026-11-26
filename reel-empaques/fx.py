"""Pixel / dot-matrix helpers for the Juanito Coffee reel."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONTS = os.path.join(HERE, "fonts")

W, H = 1080, 1920
FPS = 24

# Juanito palette (taken from the new packaging)
CREAM = (251, 240, 220)
ORANGE = (242, 147, 43)
WINE = (122, 26, 58)
MAGENTA = (196, 58, 108)
PURPLE = (120, 52, 140)
RED = (214, 74, 44)
INK = (236, 230, 218)  # off-white text
BG = (11, 10, 10)

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
], dtype=np.float32) / 64.0 + 1 / 128.0


_font_cache = {}


def font(weight=300, size=40, italic=False):
    key = (weight, size, italic)
    if key not in _font_cache:
        style = "italic" if italic else "normal"
        path = os.path.join(FONTS, f"montserrat-latin-{weight}-{style}.woff")
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGB")


def bayer(rows, cols):
    reps = (math.ceil(rows / 8), math.ceil(cols / 8))
    return np.tile(BAYER8, reps)[:rows, :cols]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def clamp01(x):
    return min(max(x, 0.0), 1.0)


def sample_grid(img, rows, cols, zoom=1.0, cx=0.5, cy=0.5, aspect=None):
    """Resize a crop of `img` to a (rows, cols) float grid in [0,1].

    The crop keeps the grid aspect ratio, zoomed by `zoom` around (cx, cy).
    """
    iw, ih = img.size
    target = cols / rows if aspect is None else aspect
    # largest crop with target aspect
    if iw / ih > target:
        ch = ih
        cw = ih * target
    else:
        cw = iw
        ch = iw / target
    cw /= zoom
    ch /= zoom
    x0 = cx * iw - cw / 2
    y0 = cy * ih - ch / 2
    x0 = min(max(x0, 0), iw - cw)
    y0 = min(max(y0, 0), ih - ch)
    crop = img.resize((cols, rows), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    return np.asarray(crop).astype(np.float32) / 255.0


def luminance(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def boost(rgb, sat=1.25, lift=0.18):
    """Brighten/saturate colours so dots read on a black background."""
    lum = luminance(rgb)[..., None]
    out = lum + (rgb - lum) * sat
    out = lift + out * (1 - lift)
    return np.clip(out, 0, 1)


def dotmatrix(colors, on, cell, dot=None, offset=None):
    """Render a cell grid as square dots.

    colors: (R, C, 3) float in [0,1]; on: (R, C) float alpha in [0,1].
    Returns (R*cell, C*cell, 3) float image and matching alpha.
    """
    R, C = on.shape
    if dot is None:
        dot = max(1, cell - max(1, round(cell * 0.3)))
    if offset is None:
        offset = (cell - dot) // 2
    block = np.zeros((cell, cell), np.float32)
    block[offset:offset + dot, offset:offset + dot] = 1.0
    a = np.repeat(np.repeat(on, cell, 0), cell, 1) * np.tile(block, (R, C))
    col = np.repeat(np.repeat(colors, cell, 0), cell, 1)
    return col, a


def composite(base, layer, alpha, pos=(0, 0)):
    """Alpha-composite float layer (h,w,3) with alpha (h,w) onto base at pos (clipped)."""
    x, y = int(pos[0]), int(pos[1])
    h, w = alpha.shape
    bh, bw = base.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, bw), min(y + h, bh)
    if x1 <= x0 or y1 <= y0:
        return base
    lx0, ly0 = x0 - x, y0 - y
    a = alpha[ly0:ly0 + (y1 - y0), lx0:lx0 + (x1 - x0)][..., None]
    l = layer[ly0:ly0 + (y1 - y0), lx0:lx0 + (x1 - x0)]
    region = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = region * (1 - a) + l * a
    return base


def noise_bg(rng, strength=0.05, cell=4, base=BG):
    rows, cols = H // cell, W // cell
    n = rng.random((rows, cols)).astype(np.float32)
    n = np.repeat(np.repeat(n, cell, 0), cell, 1)
    b = np.array(base, np.float32) / 255.0
    img = np.empty((H, W, 3), np.float32)
    img[:] = b
    img += (n[..., None] - 0.5) * strength
    return img


def static_tv(rng, t, cell=3):
    """Grey analogue static with rolling bands."""
    rows, cols = H // cell, W // cell
    n = rng.random((rows, cols)).astype(np.float32)
    band = 0.5 + 0.5 * np.sin(np.linspace(0, 9, rows) + t * 40)[:, None]
    n = 0.18 + n * 0.42 * (0.7 + 0.3 * band)
    # occasional horizontal tear lines
    for _ in range(3):
        r = rng.integers(0, rows)
        n[r:r + rng.integers(1, 4)] *= 1.5
    n = np.repeat(np.repeat(n, cell, 0), cell, 1)
    return np.repeat(n[..., None], 3, 2).clip(0, 1)


def glitch(img, rng, amount=1.0):
    """Horizontal slice displacement + RGB split."""
    out = img.copy()
    n = int(6 + 10 * amount)
    for _ in range(n):
        y = rng.integers(0, H - 10)
        h = rng.integers(6, int(20 + 120 * amount))
        dx = int(rng.integers(-60, 60) * amount)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    s = int(8 * amount)
    if s:
        out[..., 0] = np.roll(out[..., 0], s, axis=1)
        out[..., 2] = np.roll(out[..., 2], -s, axis=1)
    return out


def scanlines(img, strength=0.12):
    img[::3] *= 1 - strength
    return img


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------------------
# Text helpers (drawn on an RGBA PIL layer, then composited)
# ---------------------------------------------------------------------------

GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/#%&*+=<>"


def decode(text, p, rng_seed=0):
    """Return `text` partially scrambled; p=0 nothing, p=1 final text."""
    if p >= 1:
        return text
    if p <= 0:
        return ""
    r = np.random.default_rng(rng_seed + int(p * 40))
    n = len(text)
    shown = int(math.ceil(n * min(1.0, p * 1.6)))
    settled = int(n * max(0.0, (p - 0.25) / 0.75))
    out = []
    for i, ch in enumerate(text[:shown]):
        if i < settled or ch in " ,.()°′":
            out.append(ch)
        else:
            out.append(GLYPHS[r.integers(0, len(GLYPHS))] if ch.isupper() or ch.isdigit()
                       else GLYPHS[r.integers(0, 26)].lower())
    return "".join(out)


class Layer:
    """RGBA text/HUD layer."""

    def __init__(self):
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, f, fill=INK, alpha=1.0, anchor="la", tracking=0):
        if not s or alpha <= 0:
            return
        fill = tuple(fill) + (int(255 * clamp01(alpha)),)
        if tracking == 0:
            self.d.text(xy, s, font=f, fill=fill, anchor=anchor)
            return
        # manual letter spacing
        total = sum(f.getlength(c) for c in s) + tracking * (len(s) - 1)
        x, y = xy
        if anchor[0] == "m":
            x -= total / 2
        elif anchor[0] == "r":
            x -= total
        a = "l" + anchor[1]
        for c in s:
            self.d.text((x, y), c, font=f, fill=fill, anchor=a)
            x += f.getlength(c) + tracking

    def rect(self, box, outline=INK, width=2, alpha=1.0, fill=None):
        o = tuple(outline) + (int(255 * clamp01(alpha)),) if outline else None
        fl = tuple(fill) + (int(255 * clamp01(alpha)),) if fill else None
        self.d.rectangle(box, outline=o, width=width, fill=fl)

    def line(self, pts, fill=INK, width=2, alpha=1.0):
        self.d.line(pts, fill=tuple(fill) + (int(255 * clamp01(alpha)),), width=width)

    def apply(self, base):
        a = np.asarray(self.im).astype(np.float32) / 255.0
        alpha = a[..., 3:4]
        return base * (1 - alpha) + a[..., :3] * alpha
