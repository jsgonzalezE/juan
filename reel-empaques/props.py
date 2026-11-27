"""Pixel-art props for the Noah teaser: jute sack of green coffee, paws on the rim, paw stamp."""
import math
from functools import lru_cache

import numpy as np

import px

SW, SH = 62, 54                 # sack canvas (pixels)
OCX, OCY, ORX, ORY = 31, 10, 21, 6     # opening ellipse


def _grid(w, h):
    return [["."] * w for _ in range(h)]


def _sack_edges(y):
    """Left/right x of the sack body at row y (below the opening centre)."""
    t = (y - OCY) / (SH - 1 - OCY)                  # 0 at rim .. 1 at floor
    bulge = 7.5 * math.sin(min(1.0, t * 1.15) * math.pi * 0.62)
    half = ORX + bulge
    if t > 0.86:                                     # rounded bottom corners
        k = (t - 0.86) / 0.14
        half -= 7.0 * (1 - math.sqrt(max(0.0, 1 - k * k)))
    slump = 1.2 * math.sin(t * 2.4)                  # slight lean, it is a soft sack
    return OCX - half + slump, OCX + half + slump


def _build():
    back, front = _grid(SW, SH), _grid(SW, SH)
    rng = np.random.default_rng(8)
    # --- back: inside of the mouth, far rim, green beans
    for y in range(SH):
        for x in range(SW):
            dx, dy = (x + 0.5 - OCX) / ORX, (y + 0.5 - OCY) / ORY
            r = dx * dx + dy * dy
            if r <= 1.0:
                back[y][x] = "I"
                if r > 0.74 and dy < 0.15:
                    back[y][x] = "i" if dx < 0.2 else "I"           # far rim, inner face
            dxo, dyo = (x + 0.5 - OCX) / (ORX + 1.6), (y + 0.5 - OCY) / (ORY + 1.6)
            if r > 1.0 and dxo * dxo + dyo * dyo <= 1.0 and y + 0.5 < OCY:
                back[y][x] = "J" if dx < -0.1 else "j"              # far rim, rolled edge
    for _ in range(46):                                              # beans piled inside
        bx = int(rng.integers(OCX - ORX + 4, OCX + ORX - 4))
        by = int(rng.integers(OCY - 1, OCY + ORY - 1))
        dx, dy = (bx + 0.5 - OCX) / ORX, (by + 0.5 - OCY) / ORY
        if dx * dx + dy * dy < 0.8:
            back[by][bx] = "G"
            if bx + 1 < SW and back[by][bx + 1] in "Ii":
                back[by][bx + 1] = "q"
    # --- front: body
    for y in range(OCY, SH):
        xl, xr = _sack_edges(y)
        for x in range(SW):
            if not (xl <= x + 0.5 <= xr):
                continue
            dx, dy = (x + 0.5 - OCX) / ORX, (y + 0.5 - OCY) / ORY
            if dx * dx + dy * dy < 1.0 and y + 0.5 >= OCY:
                continue                                             # mouth opening (front half)
            u = (x + 0.5 - xl) / max(1e-6, xr - xl)                 # 0 left .. 1 right
            v = (y - OCY) / (SH - 1 - OCY)
            wob = 0.035 * math.sin(y * 0.55) + 0.02 * math.sin(y * 1.3 + 1)
            c = "J" if u < 0.34 + wob else ("j" if u < 0.72 + wob else "i")
            if v > 0.9 and c != "i":
                c = "j" if c == "J" else "i"                         # floor shadow
            if u > 0.93 or (v > 0.97 and u > 0.5):
                c = "I"
            front[y][x] = c
    # rolled front rim: a lit band hugging the lower half of the mouth, shadow under it
    for y in range(OCY, OCY + ORY + 5):
        for x in range(SW):
            dx, dy = (x + 0.5 - OCX) / ORX, (y + 0.5 - OCY) / ORY
            r = dx * dx + dy * dy
            dxo, dyo = (x + 0.5 - OCX) / (ORX + 2.6), (y + 0.5 - OCY) / (ORY + 2.8)
            ro = dxo * dxo + dyo * dyo
            dxs, dys = (x + 0.5 - OCX) / (ORX + 3.4), (y + 0.5 - OCY - 0.6) / (ORY + 4.2)
            if r >= 1.0 and ro <= 1.0 and y + 0.5 >= OCY:
                front[y][x] = "J" if dx < 0.35 else "j"
            elif ro > 1.0 and dxs * dxs + dys * dys <= 1.0 and front[y][x] != ".":
                front[y][x] = "i" if dx < 0.5 else "I"
    # weave ticks (sparse, in clusters of 2 so they are not orphans)
    for _ in range(26):
        x = int(rng.integers(8, SW - 9)); y = int(rng.integers(OCY + ORY + 7, SH - 6))
        if front[y][x] == "J" and front[y][x + 1] == "J":
            front[y][x] = front[y][x + 1] = "j"
        elif front[y][x] == "j" and front[y][x + 1] == "j":
            front[y][x] = front[y][x + 1] = "i"
    # coffee-bean emblem
    ecx, ecy = OCX + 0.5, 35.0
    for y in range(SH):
        for x in range(SW):
            dx, dy = x + 0.5 - ecx, y + 0.5 - ecy
            a = math.radians(-24)
            rx_, ry_ = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
            if (rx_ / 5.6) ** 2 + (ry_ / 8.2) ** 2 <= 1.0:
                crease = abs(rx_ - 1.5 * math.sin(ry_ * 0.55)) < 0.75 and abs(ry_) < 6.6
                front[y][x] = "j" if crease else "N"
    return ["".join(r) for r in back], ["".join(r) for r in front]


@lru_cache(maxsize=None)
def sack():
    """(back, front) float RGBA layers; draw back, then Noah, then front."""
    b, f = _build()
    fb, ff = px.to_float(b), px.to_float(f)
    fb.setflags(write=False)
    ff.setflags(write=False)
    return fb, ff


RIM_Y = OCY + ORY + 1           # row of the front rim's top edge at the centre (for clipping Noah)

PAW = [                         # a paw resting over the rim (7x6)
    ".wWWWw.",
    "wWWWWWw",
    "WWWWWWW",
    "WvWvWvW",
    "wvWvWvw",
    ".vwwwv.",
]
STAMP = [                       # paw-print mark (9x9), brand orange
    "..O...O..",
    ".OOO.OOO.",
    ".OOO.OOO.",
    "O.....O.O",
    "OO.OOO.OO",
    "..OOOOO..",
    ".OOOOOOO.",
    ".OOOOOOO.",
    "..OO.OO..",
]


@lru_cache(maxsize=None)
def paw():
    a = px.to_float(PAW)
    a.setflags(write=False)
    return a


@lru_cache(maxsize=None)
def stamp():
    a = px.to_float(STAMP)
    a.setflags(write=False)
    return a


if __name__ == "__main__":
    import sys
    from PIL import Image
    b, f = _build()
    comp = [list(r) for r in b]
    for y, r in enumerate(f):
        for x, c in enumerate(r):
            if c != ".":
                comp[y][x] = c
    rows = ["".join(r) for r in comp]
    im = px.compose(px.to_rgba(rows), 9, px.BG_DARK)
    im.save(sys.argv[1] if len(sys.argv) > 1 else "sack.png")
    print(len(px.orphans(rows)), "orphans")
