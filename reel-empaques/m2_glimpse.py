"""Minimal B — GLIMPSE: the packs are only seen through a thin slit that scans across them."""
import math

import numpy as np

import common as C
import minimal as M
from audio import CHORDS, ROOT, Track
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, dotmatrix, ease, font

NAME = "m2_glimpse"
DURATION = 15.0
BX0, BX1 = 90, 990
BCY = 940
CELL = 8
COLS = (BX1 - BX0) // CELL
NAME_T = [6.0, 7.0, 8.0, 9.0]


def strip(name, box=(0.0, 0.0, 1.0, 1.0)):
    g = C.pix(name, COLS, box=box, ncolors=32)
    col, a = dotmatrix(np.ascontiguousarray(g), np.ones(g.shape[:2], np.float32), CELL,
                       dot=CELL - 2)
    return col, a


S_COLOR = strip("color")
S_DARK = strip("dark")
S_HILLS = strip("wc_picker", (0.0, 0.08, 1.0, 0.55))
LOGO_W, LOGO_CELL = 300, 5
LOGO_G = C.logo_grid(LOGO_W, LOGO_CELL)
LOGO_A = C.logo_alpha(LOGO_W)


def band_height(t):
    if t < 0.6:
        return 2
    if t < 10.2:
        return int(2 + 118 * ease((t - 0.6) / 0.4))
    if t < 12.0:
        return int(120 + 640 * ease((t - 10.2) / 1.3))
    if t < 12.5:
        return int(2 + 758 * (1 - ease((t - 12.0) / 0.5)))
    return 2


def band_source(t):
    """(strip, scroll offset in px) for the slit at time t."""
    if t < 4.0:
        col, a = S_COLOR
        return col, a, 120 + (t - 0.6) * 160
    if t < 5.75:
        col, a = S_HILLS
        return col, a, 40 + (t - 4.0) * 60
    if t < 10.0:
        col, a = S_DARK
        k = int((t - 5.75) // 1.0)
        base = [180, 620, 380, 900, 260][min(k, 4)]
        return col, a, base + ((t - 5.75) % 1.0) * 70
    col, a = S_COLOR
    return col, a, 380 - (t - 10.0) * 120


def draw_band(img, L, t):
    h = band_height(t)
    # guide lines and ticks
    la = ease(t / 0.4) if t < 12.6 else clamp01((12.9 - t) / 0.3)
    if la > 0:
        if t < 0.6:
            half = int(480 * ease((t - 0.15) / 0.45))
            L.line([(540 - half, BCY), (540 + half, BCY)], width=2, alpha=la)
            return img
        if t >= 12.5:
            half = int(480 * (1 - ease((t - 12.5) / 0.4)))
            if half > 1:
                L.line([(540 - half, BCY), (540 + half, BCY)], width=2, alpha=la)
            return img
        y0, y1 = BCY - h // 2, BCY + h // 2
        for y in (y0 - 10, y1 + 10):
            L.line([(60, y), (1020, y)], width=1, alpha=0.35 * la)
        for x in (BX0, BX1):
            L.line([(x, y0 - 22), (x, y0 - 10)], width=2, alpha=0.8 * la)
            L.line([(x, y1 + 10), (x, y1 + 22)], width=2, alpha=0.8 * la)
    if h > 4:
        col, a, off = band_source(t)
        off = int(off) % max(1, col.shape[0] - h)
        composite(img, col[off:off + h], a[off:off + h], (BX0, BCY - h // 2))
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(6000 + i)
    img = C.bg(M.BGC)
    L = Layer()
    img = draw_band(img, L, t)
    sm = font(300, 34, True)
    C.fade_text(L, t, 1.4, "(a glimpse of what's coming)", sm, (W // 2, 840), anchor="ms",
                end=4.0)
    if 4.1 <= t < 5.75:
        a = ease((t - 4.1) / 0.35) * clamp01((5.75 - t) / 0.25)
        M.mixed_line(L, [("(origin", font(300, 36, True), 0, INK),
                         ("HUILA", font(300, 58), 16, INK),
                         ("COLOMBIA)", font(500, 22), 10, INK)], W // 2, 1080, a)
    for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, NAME_T)):
        if t0 <= t < t0 + 1.0:
            a = ease((t - t0) / 0.2) * clamp01((t0 + 1.0 - t) / 0.2)
            L.text((W // 2, 840), name, font(300, 64), anchor="ms", tracking=20, alpha=a)
            L.text((W // 2, 1060), f"0{k + 1} / 04  —  NEW VARIETY", font(500, 18), anchor="ms",
                   tracking=6, fill=ORANGE, alpha=a)
    C.fade_text(L, t, 10.9, "(almost)", sm, (W // 2, 1420), anchor="ms", end=12.3)
    if t >= 12.8:
        lt = t - 12.8
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
        C.fade_text(L, t, 13.3, "JAVA  ·  CASTILLO  ·  GEISHA  ·  BOURBON", font(400, 20),
                    (W // 2, 1110), anchor="ms", tracking=8)
        C.fade_text(L, t, 13.5, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(400, 20), (W // 2, 1150),
                    anchor="ms", tracking=8)
        C.fade_text(L, t, 13.7, "(coming soon)", sm, (W // 2, 1220), anchor="ms")
        C.fade_text(L, t, 13.9, "@JUANITOCOFFEE", font(500, 20), (W // 2, 1290), anchor="ms",
                    tracking=8, color=ORANGE)
    M.hud(L, t, DURATION)
    img = L.apply(img)
    img = M.finish(img, rng, t, DURATION)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=12)
    tr.vinyl(0.012)
    prog = ["Dm9", "Am7", "Fmaj7", "Em7"]
    for k in range(8):
        t0 = 2.0 * k
        if t0 >= DURATION:
            break
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.07, cutoff=700)
    for k in range(2, 13):
        tr.kick(k * 1.0, 0.32)
        tr.hat(k * 1.0 + 0.5, 0.025)
    for t0 in range(2, 12, 2):
        tr.bass(ROOT[prog[(t0 // 2) % 4]], float(t0), 1.8, 0.18)
    tr.chip(93, 0.15, 0.06, 0.03, duty=0.5)
    tr.bell(81, 0.6, 0.08)
    for t0 in (4.0, 5.75, 6.75, 7.75, 8.75, 10.0):
        tr.tick(t0, 0.08)
        tr.whoosh(t0 + 0.02, 0.18, 0.03)
    for k, t0 in enumerate(NAME_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.09, pan=[-0.3, 0.3, -0.3, 0.3][k])
    tr.riser(10.2, 11.9, 0.05)
    tr.whoosh(12.5, 0.4, 0.05)
    tr.bell(76, 12.8, 0.1)
    tr.bell(88, 13.3, 0.07, pan=0.3)
    return tr.write(path, fade=0.8)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
