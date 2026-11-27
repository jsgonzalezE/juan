"""Puppet rig for pixel-art Noah (front, sitting).

The hand-drawn master (assets/noah_px/final/front_sit.txt, 56x64) is split into a head layer
(with ears and topknot) and a body layer; poses are built with whole-pixel moves and small
hand-drawn patches (eyes, mouth, paw, tail), the classic way pixel-art characters are animated.

    grid = rig.pose(eyes="happy", mouth="closed", nose=1, ...)   # list[str], 68x70
    rgba = rig.sprite(...)                                        # float RGBA, cached
"""
import os
from functools import lru_cache

import numpy as np

import px

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "assets", "noah_px", "final", "front_sit.txt")
PADX, PADT = 6, 6            # padding so tilts and perks never clip
W0, H0 = 56, 64
CW, CH = W0 + 2 * PADX, H0 + PADT

EYES = ("open", "half", "closed", "happy", "left", "right", "wide", "squint")
MOUTHS = ("tongue", "closed", "flat", "pant_a", "pant_b")


def _load():
    return [list(r) for r in px.load(MASTER)]


def _put(g, x, y, s):
    for i, ch in enumerate(s):
        if 0 <= y < len(g) and 0 <= x + i < len(g[0]) and ch != " ":
            g[y][x + i] = ch


def _blank(h=H0, w=W0):
    return [["."] * w for _ in range(h)]


def _split(m):
    """Master -> (head layer, body layer)."""
    head, body = _blank(), _blank()
    for y in range(H0):
        for x in range(W0):
            c = m[y][x]
            if c == ".":
                continue
            is_head = y <= 34
            if 35 <= y <= 37:
                if c in "Ddr" and (x < 12 or x > 43):          # ear tips
                    is_head = True
                elif c in "Wwv" and 18 <= x <= 37:              # beard strands over the bandana
                    is_head = True
            (head if is_head else body)[y][x] = c
    # complete the body under the head so the head can move
    for y in (35, 36, 37):
        for x in range(18, 38):
            if body[y][x] == ".":
                body[y][x] = "b" if (x > 27 or y > 35) else "B"
    for y in (32, 33, 34):                                      # neck in the head's shadow
        for x in range(17, 39):
            body[y][x] = "v" if y < 34 else "b"
    _put(body, 15, 34, "BB")
    _put(body, 39, 34, "bb")
    return head, body


# ---------------------------------------------------------------- face patches
def _eyes(h, kind):
    L, R = 19, 34                      # left x of each 3x3 eye block (rows 17-19)
    def clear():
        for y in (16, 17, 18, 19):
            _put(h, L - 1, y, "WWWWW")
            _put(h, R - 1, y, "WWWWW")
    if kind == "open":
        return
    clear()
    if kind == "half":
        for x0 in (L, R):
            _put(h, x0, 17, "KKK"); _put(h, x0, 18, "EEE"); _put(h, x0, 19, "EEE")
    elif kind == "closed":
        for x0 in (L, R):
            _put(h, x0 - 1, 18, "K"); _put(h, x0, 19, "KKK"); _put(h, x0 + 3, 18, "K")
    elif kind == "happy":
        for x0 in (L, R):
            _put(h, x0, 17, "KKK"); _put(h, x0 - 1, 18, "K"); _put(h, x0 + 3, 18, "K")
    elif kind in ("left", "right"):
        d = -1 if kind == "left" else 1
        for x0 in (L, R):
            x1 = x0 + d
            _put(h, x1, 17, "EEE"); _put(h, x1, 18, "EEE"); _put(h, x1, 19, "EEE")
            _put(h, x1 if d < 0 else x1 + 2, 17, "e")
    elif kind == "wide":
        for x0 in (L, R):
            for y in (16, 17, 18, 19):
                _put(h, x0, y, "EEE")
            _put(h, x0, 16, "e"); _put(h, x0 + 1, 16, "e")
        _put(h, 18, 15, "WWWW"); _put(h, 34, 15, "WWWW")       # brows jump up
        _put(h, 18, 13, "KKKK"); _put(h, 34, 13, "KKKK")
    elif kind == "squint":
        for x0 in (L, R):
            _put(h, x0 - 1, 17, "KKKKK"); _put(h, x0, 18, "EEE")
        _put(h, 18, 15, "WWWW"); _put(h, 34, 15, "WWWW")       # brows pressed flat and low
        _put(h, 17, 16, "KKKKK"); _put(h, 34, 16, "KKKKK")


def _mouth(h, kind):
    if kind == "tongue":
        return
    for y in (27, 28, 29, 30, 31, 32):                         # wipe mouth + tongue
        for x in range(23, 33):
            if h[y][x] in "KPp":
                h[y][x] = "W"
    if kind == "closed":
        _put(h, 23, 27, "K"); _put(h, 32, 27, "K")
        _put(h, 24, 28, "KK"); _put(h, 30, 28, "KK")
        _put(h, 26, 27, "KKKK")
    elif kind == "flat":
        _put(h, 24, 27, "KKKKKKKK")
    elif kind in ("pant_a", "pant_b"):
        _put(h, 23, 27, "K"); _put(h, 32, 27, "K")
        _put(h, 24, 28, "K"); _put(h, 31, 28, "K")
        _put(h, 25, 27, "KppppppK"[0:1]); _put(h, 26, 27, "pppp"); _put(h, 30, 27, "K")
        _put(h, 25, 28, "pPPpPp"); _put(h, 25, 29, "KPPpPK")
        _put(h, 26, 30, "PPpP")
        if kind == "pant_a":
            _put(h, 26, 31, "PPpP"); _put(h, 27, 32, "Pp")
        else:
            _put(h, 27, 31, "Pp")


def _nose(h, up):
    if not up:
        return
    for y in range(20, 25):
        for x in range(23, 33):
            h[y][x] = h[y + 1][x]
    _put(h, 23, 25, "WWWWWWWWWW")
    _put(h, 27, 25, "KK")


def _ears(h, perk):
    """Lift and flare the floppy ears (column shear on the outer part of each ear)."""
    if not perk:
        return h
    out = [row[:] for row in h]
    def col(x, dy):
        ys = [y for y in range(len(h)) if h[y][x] in "Ddr" and 7 <= y <= 37]
        for y in ys:
            out[y][x] = "."
        for y in ys:
            if 0 <= y - dy < len(out):
                out[y - dy][x] = h[y][x]
    for x in range(0, 11):
        col(x, round(perk * (11 - x) / 3.4))
    for x in range(45, W0):
        col(x, round(perk * (x - 44) / 3.4))
    return out


def _topknot(h, spring):
    """spring > 0: fronds jump up (stem stretches); < 0: fronds squash down."""
    if not spring:
        return h
    out = [row[:] for row in h]
    if spring > 0:
        for y in range(0, 6):
            for x in range(17, 39):
                out[y][x] = "."
        for y in range(0, 6):
            if y - spring >= -PADT:
                for x in range(17, 39):
                    if h[y][x] != "." and y - spring >= 0:
                        out[y - spring][x] = h[y][x]
        for k in range(spring):                                 # stretch the stem
            _put(out, 25, 5 - k, "dDDDDd")
    else:
        for y in range(0, 4):
            for x in range(17, 39):
                out[y][x] = "."
        for y in range(0, 3):
            for x in range(17, 39):
                if h[y][x] != ".":
                    out[y + 1][x] = h[y][x]
    return out


# ---------------------------------------------------------------- body patches
PAW_UP1 = [            # paw lifted and bent, seen from the front (x0=29, y0=50)
    " vWWWWWWv ",
    "vWWWWWWWWv",
    "vWWWWWWWWv",
    "vWWvWWvWWv",
    "vWWvWWvWwv",
    " vwwwwwwv ",
    "  vvvvvv  ",
]
PAW_UP2 = [            # raised high and out to the side, below the ear (x0=37, y0=36)
    "         wWWWw ",
    "        wWWWWWw",
    "        WWvWvWW",
    "        WWvWvWw",
    "       wWWWWWwv",
    "      wWWWWWwv ",
    "     wWWWWwvv  ",
    "   wWWWWWwv    ",
    "  WWWWWWwv     ",
    " vWWWWwvv      ",
    "  vvvvv        ",
]


def _paw(b, state):
    if not state:
        return
    # the standing right foreleg (screen right, x29-39, rows 47-63) is lifted off the floor
    for y in range(47, 64):
        for x in range(29, 40):
            if b[y][x] != ".":
                b[y][x] = "."
    for y in range(47, 59):                                     # chest / belly seen behind it
        _put(b, 29, y, "WWWWWWWWWw")
    _put(b, 29, 59, "WWWWWWWWww")
    _put(b, 29, 60, "wWWWWWWwwv")
    _put(b, 30, 61, "wwwwwwvv")
    _put(b, 31, 62, "vvvvvv")
    for i, r in enumerate(PAW_UP2):                             # 1 = half raised, 2 = raised
        _put(b, 37, (40 if state == 1 else 36) + i, r)


def _tail(bp, wag):
    """Padded body grid. wag -1 = swung out, 0 = master, 1 = swung in toward the body."""
    if not wag:
        return
    ys = range(42 + PADT, 52 + PADT)
    saved = {y: bp[y][PADX:PADX + 7] for y in ys}
    for y in ys:
        for x in range(PADX, PADX + 6):
            if bp[y][x] in "Wwv":
                bp[y][x] = "."
    for y in ys:
        yy = y - PADT
        mag = 3 if yy < 45 else (2 if yy < 48 else 1)
        dx = mag * (1 if wag > 0 else -1)
        for i in range(6):
            c = saved[y][i]
            x = PADX + i + dx
            if c in "Wwv" and 0 <= x < len(bp[0]) and bp[y][x] == ".":
                bp[y][x] = c


# ---------------------------------------------------------------- pose
def _shear_tilt(h, k):
    """Approximate a head rotation with two integer shears (k = -2..2, positive leans right)."""
    if not k:
        return h, 0
    H, Wd = len(h), len(h[0])
    a = [["."] * Wd for _ in range(H)]
    piv = 36 + PADT
    for y in range(H):
        dx = int(round(k * (piv - y) / 9.0)) if y < piv else 0
        for x in range(Wd):
            c = h[y][x]
            if c != "." and 0 <= x + dx < Wd:
                a[y][x + dx] = c
    out = [["."] * Wd for _ in range(H)]
    cx = Wd / 2 - 0.5 + k * 1.5
    for x in range(Wd):
        dy = int(round(k * (x - cx) / 13.0))
        for y in range(H):
            c = a[y][x]
            if c != "." and 0 <= y + dy < H:
                out[y + dy][x] = c
    return out, 0


def pose(eyes="open", mouth="tongue", nose=0, perk=0, topknot=0, tilt=0, paw=0, tail=0,
         head_dy=0, head_only=False):
    m = _load()
    head, body = _split(m)
    _eyes(head, eyes)
    _mouth(head, mouth)
    _nose(head, nose)
    head = _ears(head, perk)
    head = _topknot(head, topknot)
    _paw(body, paw)
    # padded canvases
    def pad(g):
        out = [["."] * CW for _ in range(CH)]
        for y in range(H0):
            for x in range(W0):
                out[y + PADT][x + PADX] = g[y][x]
        return out
    hp, bp = pad(head), pad(body)
    _tail(bp, tail)
    hp, _ = _shear_tilt(hp, tilt)
    out = [["."] * CW for _ in range(CH)] if head_only else [r[:] for r in bp]
    for y in range(CH):
        yy = y + head_dy
        if not 0 <= yy < CH:
            continue
        for x in range(CW):
            c = hp[y][x]
            if c != ".":
                out[yy][x] = c
    return ["".join(r) for r in out]


@lru_cache(maxsize=512)
def sprite(eyes="open", mouth="tongue", nose=0, perk=0, topknot=0, tilt=0, paw=0, tail=0,
           head_dy=0, head_only=False):
    a = px.to_float(pose(eyes, mouth, nose, perk, topknot, tilt, paw, tail, head_dy, head_only))
    a.setflags(write=False)
    return a


if __name__ == "__main__":
    import sys
    from PIL import Image
    out = sys.argv[1] if len(sys.argv) > 1 else "rig_sheet.png"
    tests = [dict(), dict(eyes="half"), dict(eyes="closed"), dict(eyes="happy", mouth="closed", nose=1),
             dict(eyes="left", mouth="closed"), dict(eyes="right", mouth="closed"),
             dict(eyes="wide", mouth="closed", perk=1, topknot=1), dict(eyes="wide", mouth="closed", perk=2, topknot=2),
             dict(eyes="squint", mouth="flat"), dict(mouth="pant_a", eyes="happy"), dict(mouth="pant_b", eyes="happy"),
             dict(tilt=1, mouth="closed"), dict(tilt=-1, mouth="closed"), dict(tilt=2, mouth="closed"),
             dict(paw=1), dict(paw=2, eyes="happy"), dict(tail=-1), dict(tail=1), dict(head_dy=1), dict(head_dy=-2, perk=1),
             dict(head_only=True, eyes="left", mouth="closed")]
    if len(sys.argv) > 2:
        tests = [dict(), dict(paw=1), dict(paw=2, eyes="happy", mouth="closed"), dict(tail=-1), dict(tail=1)]
    sc = 8 if len(sys.argv) > 2 else 5
    tiles = []
    for t in tests:
        a = (px.to_rgba(pose(**t)))
        im = px.compose(a, sc, px.BG_DARK)
        tiles.append(im)
    cols = 7
    rows = (len(tiles) + cols - 1) // cols
    w, h = tiles[0].size
    sheet = Image.new("RGB", (cols * (w + 6), rows * (h + 6)), (70, 20, 20))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * (w + 6), (i // cols) * (h + 6)))
    sheet.save(out)
    print(out, sheet.size)
