"""P1 — TURNTABLE: the packs, in pixel art, printed up from a floor line and turning like products."""
import math

import numpy as np

import common as C
import minimal as M
from audio import CHORDS, ROOT, Track
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, dotmatrix, ease, font

NAME = "p1_turntable"
DURATION = 16.0
FLOOR = 1400
G_COLOR = C.pix("color", 60, ncolors=32)
G_DARK = C.pix("dark", 60, ncolors=32)
NAME_T = [3.0, 4.0, 5.0, 6.0]
LOGO_W, LOGO_CELL = 320, 5
LOGO_G = C.logo_grid(LOGO_W, LOGO_CELL)
LOGO_A = C.logo_alpha(LOGO_W)
LINE = np.ones((2, 900, 3), np.float32) * np.array(INK, np.float32) / 255


def draw_pack(img, grid, cx, cell, ang=0.0, reveal=1.0, scan=True):
    """Pack standing on the floor at centre x; reveal prints rows bottom-up (negative: top-down)."""
    rgb, a, m = C.card3d(grid, ang, 0.0, persp=2.6, margin=0.25)
    rows = grid.shape[0]
    R = rgb.shape[0]
    rr = np.arange(R)[:, None]
    if reveal < 1:
        k = int(round(rows * clamp01(reveal)))
        top = m + rows - k
        a = a * (rr >= top)
        if scan and 0 < k < rows:
            band = (rr == top).astype(np.float32)
            rgb = np.clip(rgb + band[..., None] * 0.45, 0, 1)
    x = int(cx - rgb.shape[1] * cell / 2)
    vis = np.where(C.card3d(grid, ang, 0.0, persp=2.6, margin=0.25)[1].any(1))[0]
    b = int(vis.max()) if vis.size else m + rows - 1
    y = int(FLOOR - (b + 1) * cell)
    col, aa = dotmatrix(rgb, a, cell, dot=cell - 2)
    composite(img, col, aa, (x, y))
    # floor reflection: flipped, darker, fading out
    fr = rgb[::-1] * 0.55
    fa = a[::-1].copy()
    top = R - 1 - b
    fade = np.clip(1 - (np.arange(R) - top) / (rows * 0.32), 0, 1)[:, None]
    fa = fa * fade * 0.38
    col, aa = dotmatrix(np.ascontiguousarray(fr), fa, cell, dot=cell - 2)
    composite(img, col, aa, (x, FLOOR + 8 - top * cell))
    return img


def floor_line(img, t):
    if t < 0.6:
        half = int(450 * ease((t - 0.1) / 0.5))
    elif t > 15.2:
        half = int(450 * clamp01((15.9 - t) / 0.7))
    else:
        half = 450
    if half > 0:
        composite(img, LINE[:, :2 * half], np.full((2, 2 * half), 0.5, np.float32),
                  (540 - half, FLOOR))
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(8000 + i)
    img = C.bg(M.BGC)
    L = Layer()
    img = floor_line(img, t)
    sm = font(300, 34, True)
    # --- act 1: the colourful pack alone
    if 0.6 <= t < 7.9:
        if t < 2.2:
            img = draw_pack(img, G_COLOR, 540, 10, 0.0, (t - 0.6) / 1.6)
        elif t < 7.4:
            ang = 0.42 * math.sin((t - 2.2) * 1.05) * clamp01((7.4 - t) / 0.4)
            img = draw_pack(img, G_COLOR, 540, 10, ang)
        else:
            img = draw_pack(img, G_COLOR, 540, 10, 0.0, 1 - (t - 7.4) / 0.5, scan=False)
        C.fade_text(L, t, 2.0, "(a new look)", sm, (W // 2, 1760), anchor="ms", end=2.95)
        for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, NAME_T)):
            if t0 <= t < t0 + 1.0:
                a = ease((t - t0) / 0.2) * clamp01((t0 + 1.0 - t) / 0.2)
                L.text((W // 2, 1790), name, font(300, 56), anchor="ms", tracking=18, alpha=a)
                L.text((W // 2, 1712), f"0{k + 1} / 04", font(500, 18), anchor="ms",
                       tracking=6, fill=ORANGE, alpha=a)
        C.fade_text(L, t, 7.0, "(new varieties)", sm, (W // 2, 1760), anchor="ms", end=7.7)
    # --- act 2: both packs, facing each other
    if 7.9 <= t < 13.9:
        if t < 9.1:
            r = (t - 7.9) / 1.2
            img = draw_pack(img, G_COLOR, 290, 7, 0.0, r)
            img = draw_pack(img, G_DARK, 790, 7, 0.0, r - 0.1)
        elif t < 13.4:
            sway = 0.06 * math.sin((t - 9.1) * 1.4)
            k = ease((t - 9.1) / 0.6) * clamp01((12.9 - t) / 0.5 + 0.0) if t < 12.9 else 0.0
            if t >= 12.9:
                k = 1 - ease((t - 12.9) / 0.5)
            img = draw_pack(img, G_COLOR, 290, 7, (0.30 + sway) * k)
            img = draw_pack(img, G_DARK, 790, 7, (-0.30 - sway) * k)
        else:
            r = 1 - (t - 13.4) / 0.5
            img = draw_pack(img, G_COLOR, 290, 7, 0.0, r, scan=False)
            img = draw_pack(img, G_DARK, 790, 7, 0.0, r, scan=False)
        if 9.6 <= t < 13.3:
            a = ease((t - 9.6) / 0.4) * clamp01((13.3 - t) / 0.3)
            M.mixed_line(L, [("(origin", font(300, 34, True), 0, INK),
                             ("HUILA", font(300, 52), 16, INK),
                             ("COLOMBIA)", font(500, 20), 10, INK)], W // 2, 1720, a)
        C.fade_text(L, t, 10.4, "JAVA  ·  CASTILLO  ·  GEISHA  ·  BOURBON", font(400, 20),
                    (W // 2, 1790), anchor="ms", tracking=8, end=13.3)
    # --- logo
    if t >= 13.9:
        lt = t - 13.9
        on = ((LOGO_G > 0.3) & (M.order(LOGO_G.shape, 9) < lt / 0.5)).astype(np.float32)
        k = ease((lt - 0.55) / 0.3)
        c = np.empty(LOGO_G.shape + (3,), np.float32)
        c[:] = np.array(INK, np.float32) / 255
        lx, ly = (W - LOGO_W) // 2, FLOOR - 60 - LOGO_A.shape[0]
        col, a = dotmatrix(c, on * (1 - k), LOGO_CELL, dot=3)
        composite(img, col, a, (lx, ly))
        if k > 0:
            s = np.empty(LOGO_A.shape + (3,), np.float32)
            s[:] = np.array(INK, np.float32) / 255
            composite(img, s, LOGO_A * k, (lx, ly))
        C.fade_text(L, t, 14.3, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(400, 20),
                    (W // 2, 1500), anchor="ms", tracking=8)
        C.fade_text(L, t, 14.5, "(coming soon)", sm, (W // 2, 1570), anchor="ms")
        C.fade_text(L, t, 14.7, "@JUANITOCOFFEE", font(500, 20), (W // 2, 1640), anchor="ms",
                    tracking=8, color=ORANGE)
    M.hud(L, t, DURATION)
    img = L.apply(img)
    img = M.finish(img, rng, t, DURATION)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=21)
    tr.vinyl(0.012)
    prog = ["Am7", "Fmaj7", "Cmaj7", "G6"]
    for k in range(8):
        t0 = 2.0 * k
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.07, cutoff=750)
    for k in range(2, 14):
        tr.kick(k * 1.0, 0.36)
        tr.hat(k * 1.0 + 0.5, 0.03)
    for t0 in range(2, 14, 2):
        tr.bass(ROOT[prog[(t0 // 2) % 4]], float(t0), 1.8, 0.18)
    # printing: a soft rising tick sequence
    for k in range(16):
        tr.chip(64 + k, 0.6 + k * 0.1, 0.05, 0.022, duty=0.5)
        tr.chip(60 + k, 7.9 + k * 0.075, 0.05, 0.02, duty=0.5)
    tr.bell(81, 2.2, 0.08)
    for k, t0 in enumerate(NAME_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.08, pan=[-0.3, 0.3, -0.3, 0.3][k])
    tr.bell(76, 9.1, 0.08, pan=-0.3)
    tr.bell(84, 9.15, 0.06, pan=0.3)
    tr.whoosh(7.45, 0.3, 0.04)
    tr.whoosh(13.45, 0.3, 0.04)
    tr.bell(76, 13.9, 0.1)
    tr.bell(88, 14.4, 0.07, pan=0.3)
    return tr.write(path, fade=0.8)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
