"""Minimal C — GLIMPSE + STILL LIFE.

The slit from m2 is the thread of the piece: it opens on fragments of the packs, closes into a
horizon line, and the dithered objects from m1 (flower, bean) appear sitting on that line.
"""
import math

import numpy as np

import common as C
import minimal as M
from audio import CHORDS, ROOT, Track
from bean import bean_grid
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, dotmatrix, ease, font

NAME = "m3_combo"
DURATION = 16.0
BX0, BX1 = 90, 990
BCY = 960
CELL = 8
COLS = (BX1 - BX0) // CELL
NAME_T = [7.4, 8.3, 9.2, 10.1]


def strip(name, box=(0.0, 0.0, 1.0, 1.0)):
    g = C.pix(name, COLS, box=box, ncolors=32)
    return dotmatrix(np.ascontiguousarray(g), np.ones(g.shape[:2], np.float32), CELL,
                     dot=CELL - 2)


S_COLOR = strip("color")
S_DARK = strip("dark")
S_HILLS = strip("wc_picker", (0.0, 0.08, 1.0, 0.55))
FLOWER = M.object_grid("flower", 112)
LOGO_W, LOGO_CELL = 300, 5
LOGO_G = C.logo_grid(LOGO_W, LOGO_CELL)
LOGO_A = C.logo_alpha(LOGO_W)
LINE = np.ones((2, BX1 - BX0, 3), np.float32) * np.array(INK, np.float32) / 255


def seg(t, t0, t1, a, b):
    """Ease from a to b between t0 and t1."""
    return a + (b - a) * ease((t - t0) / (t1 - t0))


def band(t):
    """(height px, strip or None, scroll offset)."""
    if t < 0.6:
        return 0, None, 0
    if t < 3.3:
        h = seg(t, 0.6, 1.0, 2, 120) if t < 3.0 else seg(t, 3.0, 3.3, 120, 2)
        return int(h), S_COLOR, 120 + (t - 0.6) * 160
    if t < 5.5:
        return 2, None, 0
    if t < 7.05:
        h = seg(t, 5.5, 5.8, 2, 120) if t < 6.75 else seg(t, 6.75, 7.05, 120, 2)
        return int(h), S_HILLS, 40 + (t - 5.5) * 60
    if t < 11.4:
        h = seg(t, 7.1, 7.4, 2, 56) if t < 11.1 else seg(t, 11.1, 11.4, 56, 2)
        k = int(max(0, t - 7.4) // 0.9)
        base = [180, 620, 380, 900, 260][min(k, 4)]
        return int(h), S_DARK, base + (t - 7.4) % 0.9 * 60
    if t < 13.1:
        h = seg(t, 11.4, 12.5, 2, 760) if t < 12.6 else seg(t, 12.6, 13.1, 760, 2)
        return int(h), S_COLOR, 380 - (t - 11.4) * 110
    return 2, None, 0


def draw_band(img, L, t):
    h, src, off = band(t)
    if t < 0.6:  # the line draws itself from the centre
        half = int((BX1 - BX0) / 2 * ease((t - 0.15) / 0.45))
        if half > 0:
            composite(img, LINE[:, :2 * half], np.ones((2, 2 * half), np.float32) * 0.9,
                      (540 - half, BCY - 1))
        return img
    if t >= 13.1:  # and collapses before the logo
        half = int((BX1 - BX0) / 2 * (1 - ease((t - 13.1) / 0.4)))
        if half > 0:
            composite(img, LINE[:, :2 * half], np.ones((2, 2 * half), np.float32) * 0.9,
                      (540 - half, BCY - 1))
        return img
    if src is None or h <= 2:
        composite(img, LINE, np.ones(LINE.shape[:2], np.float32) * 0.9, (BX0, BCY - 1))
        return img
    col, a = src
    off = int(off) % max(1, col.shape[0] - h)
    composite(img, col[off:off + h], a[off:off + h], (BX0, BCY - h // 2))
    y0, y1 = BCY - h // 2, BCY + h // 2
    for x in (BX0, BX1):
        L.line([(x, y0 - 22), (x, y0 - 10)], width=2, alpha=0.8)
        L.line([(x, y1 + 10), (x, y1 + 22)], width=2, alpha=0.8)
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(7000 + i)
    img = C.bg(M.BGC)
    L = Layer()
    img = draw_band(img, L, t)
    sm = font(300, 34, True)
    # glimpse 1
    C.fade_text(L, t, 1.3, "(a glimpse of what's coming)", sm, (W // 2, 840), anchor="ms",
                end=3.1)
    # flower blooming on the line
    p = M.window(t, 3.35, 5.5, 0.8, 0.35)
    if p > 0:
        lum, mask = FLOWER
        img = M.draw_obj(img, lum, mask, 540, BCY, 6, p, seed=1,
                         gain=1.0 + 0.03 * math.sin(t * 1.3), floor=0.45)
        C.fade_text(L, t, 4.0, "(something is blooming)", sm, (W // 2, 1340), anchor="ms",
                    end=5.45)
    # origin
    if 5.65 <= t < 7.0:
        a = ease((t - 5.65) / 0.35) * clamp01((7.0 - t) / 0.25)
        M.mixed_line(L, [("(origin", font(300, 36, True), 0, INK),
                         ("HUILA", font(300, 58), 16, INK),
                         ("COLOMBIA)", font(500, 22), 10, INK)], W // 2, 1100, a)
    # bean in front of a thin slit of the dark pack, varieties one by one
    p = M.window(t, 7.05, 11.4, 0.45, 0.35)
    if p > 0:
        n = 96
        shade, hit = bean_grid(n, 0.4 + 0.85 * (t - 7.05), tilt=0.5 + 0.12 * math.sin(t * 0.8),
                               wobble=0.3 * math.sin(t * 0.6))
        # dark plate so the bean reads cleanly over the slit
        m = hit.astype(np.float32)
        plate = np.repeat(np.repeat(m, 6, 0), 6, 1)
        composite(img, np.ones(plate.shape + (3,), np.float32) * np.array(M.BGC) / 255,
                  plate * p, (540 - n * 3, BCY - n * 3))
        img = M.draw_obj(img, shade ** 0.9, m, 540, BCY, 6, p, seed=3, floor=0.0)
        for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, NAME_T)):
            if t0 <= t < t0 + 0.9:
                a = ease((t - t0) / 0.2) * clamp01((t0 + 0.9 - t) / 0.18)
                L.text((W // 2, 1420), name, font(300, 64), anchor="ms", tracking=20, alpha=a)
                L.text((W // 2, 1335), f"0{k + 1} / 04", font(500, 18), anchor="ms",
                       tracking=6, fill=ORANGE, alpha=a)
    # almost
    C.fade_text(L, t, 12.0, "(almost)", sm, (W // 2, 1420), anchor="ms", end=12.9)
    # logo
    if t >= 13.4:
        lt = t - 13.4
        on = ((LOGO_G > 0.3) & (M.order(LOGO_G.shape, 9) < lt / 0.5)).astype(np.float32)
        k = ease((lt - 0.55) / 0.3)
        c = np.empty(LOGO_G.shape + (3,), np.float32)
        c[:] = np.array(INK, np.float32) / 255
        col, a = dotmatrix(c, on * (1 - k), LOGO_CELL, dot=3)
        lx, ly = (W - LOGO_W) // 2, 640
        composite(img, col, a, (lx, ly))
        if k > 0:
            s = np.empty(LOGO_A.shape + (3,), np.float32)
            s[:] = np.array(INK, np.float32) / 255
            composite(img, s, LOGO_A * k, (lx, ly))
        C.fade_text(L, t, 13.9, "JAVA  ·  CASTILLO  ·  GEISHA  ·  BOURBON", font(400, 20),
                    (W // 2, 1110), anchor="ms", tracking=8)
        C.fade_text(L, t, 14.1, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(400, 20), (W // 2, 1150),
                    anchor="ms", tracking=8)
        C.fade_text(L, t, 14.3, "(coming soon)", sm, (W // 2, 1220), anchor="ms")
        C.fade_text(L, t, 14.5, "@JUANITOCOFFEE", font(500, 20), (W // 2, 1290), anchor="ms",
                    tracking=8, color=ORANGE)
    M.hud(L, t, DURATION)
    img = L.apply(img)
    img = M.finish(img, rng, t, DURATION)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=13)
    tr.vinyl(0.012)
    prog = ["Dm9", "Am7", "Fmaj7", "Em7"]
    for k in range(8):
        t0 = 2.0 * k
        if t0 >= DURATION:
            break
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.07, cutoff=700)
    for k in range(2, 14):
        tr.kick(k * 1.0, 0.32)
        tr.hat(k * 1.0 + 0.5, 0.025)
    for t0 in range(2, 13, 2):
        tr.bass(ROOT[prog[(t0 // 2) % 4]], float(t0), 1.8, 0.18)
    tr.chip(93, 0.15, 0.06, 0.03, duty=0.5)
    tr.bell(81, 0.6, 0.08)
    tr.bell(84, 3.4, 0.09, pan=-0.3)
    tr.bell(76, 4.2, 0.06, pan=0.3)
    for t0 in (3.0, 5.5, 6.75, 7.1, 11.4):
        tr.tick(t0, 0.08)
        tr.whoosh(t0 + 0.02, 0.18, 0.03)
    for k, t0 in enumerate(NAME_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.09, pan=[-0.3, 0.3, -0.3, 0.3][k])
        tr.tick(t0, 0.05)
    tr.riser(11.4, 12.55, 0.05)
    tr.whoosh(13.1, 0.4, 0.05)
    tr.bell(76, 13.4, 0.1)
    tr.bell(88, 13.9, 0.07, pan=0.3)
    return tr.write(path, fade=0.8)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
