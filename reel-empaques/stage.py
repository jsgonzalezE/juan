"""Stage helpers for the hand-made pixel Noah teaser.

* Sprites: hand-drawn text grids in assets/noah_px (see px.py / STYLE.md).
* Packs: real pouch photos that materialise from big pixels (noah.pack_photo / pixelate).
* Small particle and text helpers.
"""
import glob
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter

import noah as N
import px
from fx import H, W, clamp01, composite, ease

HERE = os.path.dirname(os.path.abspath(__file__))
PXDIR = os.path.join(HERE, "assets", "noah_px")
SCALE = 6
BGC = (17, 16, 16)


# ---------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def sprite_file(path):
    a = px.to_float(px.load(path))
    a.setflags(write=False)
    return a


def master(view):
    return sprite_file(os.path.join(PXDIR, "final", f"{'front_sit' if view == 'front' else 'side_stand'}.txt"))


@lru_cache(maxsize=None)
def anim(name):
    files = sorted(glob.glob(os.path.join(PXDIR, "anim", name, f"{name}_*.txt")))
    return tuple(sprite_file(f) for f in files)


def frame_at(frames, t, fps, loop=True, pingpong=False, hold_last=True):
    """Pick the frame for local time t (seconds since the clip started)."""
    n = len(frames)
    if n == 0:
        return None
    k = int(max(0.0, t) * fps)
    if pingpong and n > 1:
        period = 2 * n - 2
        k %= period
        k = k if k < n else period - k
    elif loop:
        k %= n
    else:
        k = min(k, n - 1) if hold_last else k
        if k >= n:
            return None
    return frames[k]


def seq(frames, order):
    """Reorder/repeat frames by index list, e.g. seq(f, [0,1,2,1])."""
    return tuple(frames[i] for i in order if 0 <= i < len(frames))


@lru_cache(maxsize=4096)
def _scaled(key, spr_id, scale, flip):
    spr = _REG[spr_id]
    if flip:
        spr = spr[:, ::-1]
    up = np.repeat(np.repeat(spr, scale, 0), scale, 1)
    up.setflags(write=False)
    return up


_REG = {}


def blit(img, spr, cx, bottom, scale=SCALE, flip=False, alpha=1.0, clip_bottom=None,
         squash=(1.0, 1.0), tint=None):
    """Draw a sprite with its bottom-centre at (cx, bottom) in screen pixels."""
    if spr is None or alpha <= 0:
        return img
    sx, sy = squash
    if abs(sx - 1) > 0.01 or abs(sy - 1) > 0.01:
        h, w = spr.shape[:2]
        nw, nh = max(1, round(w * sx)), max(1, round(h * sy))
        yi = np.minimum((np.arange(nh) * h / nh).astype(int), h - 1)
        xi = np.minimum((np.arange(nw) * w / nw).astype(int), w - 1)
        spr = spr[yi][:, xi]
        up = np.repeat(np.repeat(spr[:, ::-1] if flip else spr, scale, 0), scale, 1)
    else:
        key = id(spr)
        _REG[key] = spr
        up = _scaled(key, key, scale, flip)
    h, w = up.shape[:2]
    x0 = int(round(cx - w / 2))
    y0 = int(round(bottom - h))
    a = up[..., 3] * alpha
    if clip_bottom is not None:
        keep = max(0, min(h, int(clip_bottom) - y0))
        a = a.copy()
        a[keep:] = 0
    rgb = up[..., :3]
    if tint is not None:
        rgb = rgb * np.array(tint, np.float32)
    return composite(img, np.ascontiguousarray(rgb), a, (x0, y0))


def hop(u, p0, p1, height):
    u = clamp01(u)
    return (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u - height * 4 * u * (1 - u))


# ---------------------------------------------------------------------------
# Packs (real photos)
# ---------------------------------------------------------------------------
STEPS = [80, 56, 40, 28, 20, 14, 10, 7, 5, 3, 2, 1]
GLOW = np.array((255, 214, 150), np.float32) / 255


@lru_cache(maxsize=None)
def halo(key, width, blur=48):
    p = N.pack_photo(key, width)
    pad = 2 * blur
    a = np.pad(p[..., 3], pad)
    g = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
    g.setflags(write=False)
    return g, pad


@lru_cache(maxsize=256)
def _pix(key, width, cell):
    q = N.pixelate(N.pack_photo(key, width), cell)
    q.setflags(write=False)
    return q


def pack(img, key, width, cx, bottom, k=1.0, glow=0.22, clip_bottom=None, alpha=1.0, dy=0):
    """Real pack photo; k in [0,1] = materialisation (0 nothing, 1 crisp)."""
    if k <= 0 or alpha <= 0:
        return img
    cell = STEPS[min(len(STEPS) - 1, int(clamp01(k) * (len(STEPS) - 1) + 1e-6))]
    q = _pix(key, width, cell) if cell > 1 else N.pack_photo(key, width)
    h = q.shape[0]
    x0, y0 = int(round(cx - width / 2)), int(round(bottom - h + dy))
    if glow > 0:
        g, pad = halo(key, width)
        ga = g * glow * clamp01(k * 1.3) * alpha
        img = composite(img, np.broadcast_to(GLOW, g.shape + (3,)).copy(), ga, (x0 - pad, y0 - pad))
    a = q[..., 3] * alpha
    if clip_bottom is not None:
        a = a.copy()
        a[max(0, int(clip_bottom) - y0):] = 0
    return composite(img, np.ascontiguousarray(q[..., :3]), a, (x0, y0))


def pack_size(key, width):
    p = N.pack_photo(key, width)
    return p.shape[1], p.shape[0]


# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------
def square(img, x, y, size, color, alpha):
    if alpha <= 0:
        return img
    c = np.empty((size, size, 3), np.float32)
    c[:] = np.array(color, np.float32) / 255
    return composite(img, c, np.full((size, size), alpha, np.float32), (int(x - size / 2), int(y - size / 2)))


def wisps(img, t, x0, y0, color=(228, 122, 46), n=3, height=260, size=8, alpha=0.8, spread=40, seed=0):
    """Rising aroma wisps made of pixel squares."""
    for j in range(n):
        ph = (seed * 0.37 + j * 0.61) % 1.0
        for s in range(10):
            u = ((t * 0.55 + ph + s / 10) % 1.0)
            y = y0 - u * height
            x = x0 + (j - (n - 1) / 2) * spread + 16 * math.sin(u * 7 + j * 2 + t * 1.5)
            a = alpha * math.sin(u * math.pi) ** 1.2
            img = square(img, x, y, size if u < 0.6 else size - 2, color, a)
    return img


def sparkle(img, x, y, t0, t, color=(255, 236, 200), size=6):
    """Four-point pixel sparkle that pops and fades (0.5 s)."""
    u = (t - t0) / 0.5
    if not 0 <= u < 1:
        return img
    r = int(2 + 3 * math.sin(u * math.pi))
    a = 1 - u
    img = square(img, x, y, size, color, a)
    for d in range(1, r + 1):
        aa = a * (1 - d / (r + 1))
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            img = square(img, x + dx * size, y + dy * size, size, color, aa)
    return img


def dust(img, x, y, t0, t, color=(150, 140, 130), n=6, seed=0):
    u = (t - t0) / 0.45
    if not 0 <= u < 1:
        return img
    r = np.random.default_rng(seed)
    for k in range(n):
        ang = math.pi * (0.1 + 0.8 * k / max(1, n - 1))
        dist = 20 + 70 * u * (0.7 + 0.6 * r.random())
        px_ = x + math.cos(ang) * dist * (1 if k % 2 else -1)
        py_ = y - math.sin(ang) * dist * 0.35
        img = square(img, px_, py_, 8 if u < 0.5 else 6, color, (1 - u) * 0.8)
    return img
