"""Version 1 — NOIR: dark, elegant dot-matrix. Packaging shown only as dots."""
import math
import os

import numpy as np

import common as C
from audio import BEAT, CHORDS, ROOT, Track
from fx import INK, ORANGE, H, W, Layer, bayer, clamp01, composite, dotmatrix, ease, ease_out, font

NAME = "v1_noir"
DURATION = 18.0
BGC = (14, 13, 12)
CUTS = [3.5, 6.0, 7.25, 8.5, 9.75, 11.0, 14.5]
VAR_T = [6.0, 7.25, 8.5, 9.75]
VAR_SRC = [("color", (0.0, 0.32, 1.0, 0.78)), ("dark", (0.0, 0.42, 0.62, 0.98)),
           ("wc_cherries", (0.50, 0.60, 0.98, 0.86)), ("wc_cherries", (0.0, 0.74, 0.46, 0.99))]

# --- assembled pack (scene 1)
G1 = C.pix("color", 48)
R1, C1 = G1.shape[:2]
CELL1 = 10
X1, Y1 = 540 - C1 * CELL1 // 2, 880 - R1 * CELL1 // 2
_r = np.random.default_rng(5)
START = np.stack([_r.uniform(-200, W + 200, (R1, C1)), _r.uniform(-300, H + 300, (R1, C1))], -1)
DELAY = _r.uniform(0, 0.9, (R1, C1))
_yy, _xx = np.mgrid[0:R1, 0:C1]
TARGET = np.stack([X1 + _xx * CELL1, Y1 + _yy * CELL1], -1).astype(np.float32)

MACRO = C.pix("color", 120)
CARD_A = C.pix("color", 40, 65)
CARD_B = C.pix("dark", 46, 65)
LOGO_W, LOGO_CELL = 420, 6
LOGO_G = C.logo_grid(LOGO_W, LOGO_CELL)
LOGO_A = C.logo_alpha(LOGO_W)
LOGO_T = np.random.default_rng(7).uniform(0.1, 0.8, LOGO_G.shape)


def var_grid(k):
    name, box = VAR_SRC[k]
    g = C.pix(name, 140, 250, box, ncolors=0)
    lum = C.luminance(g)
    lo, hi = np.percentile(lum, (3, 97))
    return np.clip((lum - lo) / (hi - lo), 0, 1)


VAR_LUM = [var_grid(k) for k in range(4)]


def chapter(t):
    return 1 + sum(t >= b for b in (3.5, 6.0, 11.0, 14.5))


def ui(L, t):
    L.text((60, 64), "JUANITO COFFEE", font(600, 20), tracking=6)
    L.text((1020, 64), "NEW HARVEST", font(400, 20), tracking=6, anchor="ra", alpha=0.6)
    L.text((60, 1846), "HUILA · COLOMBIA", font(500, 18), tracking=6, alpha=0.6)
    L.text((1020, 1846), f"0{chapter(t)} / 05", font(600, 18), tracking=4, anchor="ra")
    L.line([(60, 1812), (1020, 1812)], width=2, alpha=0.15)
    L.line([(60, 1812), (60 + 960 * t / DURATION, 1812)], width=2, alpha=0.8)


def draw_card(img, grid, ang, x, y, cell, alpha=1.0, reveal=1.0, tilt=0.0):
    rgb, a, m = C.card3d(grid, ang, tilt)
    if reveal < 1:
        v = reveal * 1.2 - 0.2 + 0.2 * C.luminance(rgb)
        a = a * (v > bayer(*a.shape))
    col, aa = dotmatrix(rgb, a * alpha, cell, dot=cell - 2)
    return composite(img, col, aa, (x - m * cell, y - m * cell))


# ---------------------------------------------------------------------------
def s_look(t, L):
    img = C.bg(BGC)
    if t < 1.9:
        prog = np.clip((t - 0.1 - DELAY) / 0.9, 0, 1)
        prog = 1 - (1 - prog) ** 3
        pos = START + (TARGET - START) * prog[..., None]
        vis = prog > 0
        xs = pos[..., 0][vis].astype(int)
        ys = pos[..., 1][vis].astype(int)
        cols = G1[vis]
        dot = CELL1 - 2
        ox, oy = np.mgrid[0:dot, 0:dot]
        X = (xs[:, None, None] + ox[None]).ravel()
        Y = (ys[:, None, None] + oy[None]).ravel()
        Cc = np.repeat(cols, dot * dot, 0)
        ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
        img[Y[ok], X[ok]] = Cc[ok]
    else:
        ang = 0.34 * math.sin((t - 1.9) * 1.2)
        img = draw_card(img, G1, ang, X1, Y1, CELL1)
    C.fade_text(L, t, 1.6, "A NEW LOOK", font(200, 104), (W // 2, 1460), anchor="ms",
                tracking=22)
    C.fade_text(L, t, 1.95, "(is on its way)", font(300, 46, True), (W // 2, 1540), anchor="ms")
    return img


def s_origin(t, L):
    lt = t - 3.5
    img = C.bg(BGC)
    cell = 20
    vr, vc = H // cell + 1, W // cell + 1
    fx = 8 + 40 * ease(lt / 2.5)
    fy = 4 + 70 * ease(lt / 2.5)
    ix, iy = int(fx), int(fy)
    g = MACRO[iy:iy + vr + 1, ix:ix + vc + 1]
    col, a = dotmatrix(np.ascontiguousarray(g), np.ones(g.shape[:2], np.float32), cell, dot=cell - 4)
    img = composite(img, col, a * ease(lt / 0.3), (-int((fx - ix) * cell), -int((fy - iy) * cell)))
    band = np.ones((H, 1, 1), np.float32)
    ys = np.arange(H)
    band[:, 0, 0] = 1 - 0.78 * np.clip(1 - np.abs(ys - 990) / 300, 0, 1) ** 0.6
    img *= band
    C.fade_text(L, t, 3.75, "ORIGIN", font(500, 24), (W // 2, 860), anchor="ms", tracking=18)
    C.fade_text(L, t, 3.9, "HUILA", font(200, 240), (W // 2, 1080), anchor="ms", tracking=36)
    C.fade_text(L, t, 4.15, "COLOMBIA", font(500, 24), (W // 2, 1150), anchor="ms", tracking=18)
    return img


def s_variety(t, L, k):
    lt = t - VAR_T[k]
    img = C.bg(BGC)
    lum = VAR_LUM[k]
    p = clamp01(lt / 0.25)
    zoom_px = int(lt * 30)
    th = bayer(*lum.shape)
    on = ((lum - (1 - p) * 1.1) > th).astype(np.float32)
    colr = np.array(C.VARIETY_COLORS[k], np.float32) / 255
    rgb = np.clip(colr * (0.5 + 0.7 * lum[..., None]), 0, 1).astype(np.float32)
    col, a = dotmatrix(rgb, on, 8, dot=6)
    img = composite(img, col, a, (-zoom_px // 2, -zoom_px))
    L.rect((0, 820, W, 1200), outline=None, fill=BGC, alpha=0.86)
    name = C.VARIETY_NAMES[k]
    f = C.fit(name, 900, weight=200, start=200, tracking=24)
    L.text((W // 2, 868), f"NEW VARIETY — 0{k + 1} / 04", font(600, 20), tracking=8, anchor="ms",
           fill=C.VARIETY_COLORS[k])
    C.fade_text(L, t, VAR_T[k] + 0.05, name, f, (W // 2, 1070), anchor="ms", tracking=24,
                dur=0.3, rise=8)
    C.fade_text(L, t, VAR_T[k] + 0.2, "(coming soon)", font(300, 40, True), (W // 2, 1150),
                anchor="ms", dur=0.3, rise=6)
    return img


def s_packs(t, L):
    lt = t - 11.0
    img = C.bg(BGC)
    wa, wb = CARD_A.shape[1] * 10, CARD_B.shape[1] * 10
    xa = (W - wa - wb - 50) // 2
    xb = xa + wa + 50
    y = 960 - CARD_A.shape[0] * 10 // 2
    sw = 0.05 * math.sin(lt * 1.6)
    img = draw_card(img, CARD_A, 0.26 + sw, xa, y, 10, reveal=ease((lt - 0.1) / 0.45))
    img = draw_card(img, CARD_B, -0.26 - sw, xb, y, 10, reveal=ease((lt - 0.4) / 0.45))
    C.fade_text(L, t, 11.15, "NEW PACKAGING", font(300, 74), (W // 2, 480), anchor="ms",
                tracking=16)
    C.fade_text(L, t, 11.45, "(almost ready)", font(300, 44, True), (W // 2, 552), anchor="ms")
    C.fade_text(L, t, 12.2, "COMING SOON", font(600, 24), (W // 2, 1420), anchor="ms",
                tracking=16, color=ORANGE)
    return img


def s_outro(t, L):
    lt = t - 14.5
    img = C.bg(BGC)
    lx, ly = (W - LOGO_W) // 2, 470
    on = ((LOGO_G > 0.3) & (LOGO_T <= lt)).astype(np.float32)
    k = ease((lt - 0.95) / 0.35)
    c = np.empty(LOGO_G.shape + (3,), np.float32)
    c[:] = np.array(INK, np.float32) / 255
    col, a = dotmatrix(c, on * (1 - k), LOGO_CELL, dot=4)
    composite(img, col, a, (lx, ly))
    if k > 0:
        s = np.empty(LOGO_A.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, LOGO_A * k, (lx, ly))
    C.fade_text(L, t, 15.4, "GREEN COFFEE", font(300, 72), (W // 2, 1180), anchor="ms",
                tracking=16)
    C.fade_text(L, t, 15.6, "FROM HUILA, COLOMBIA", font(500, 22), (W // 2, 1240), anchor="ms",
                tracking=10)
    C.fade_text(L, t, 15.9, "COMING SOON", font(600, 30), (W // 2, 1370), anchor="ms",
                tracking=16, color=ORANGE)
    C.fade_text(L, t, 16.1, "@JUANITOCOFFEE", font(600, 30), (W // 2, 1450), anchor="ms",
                tracking=8)
    return img


def dither_dip(img, t):
    """Bayer-dither dip to black around each cut."""
    for b in CUTS:
        d = abs(t - b)
        if d < 0.12:
            k = 1 - d / 0.12
            cell = 8
            th = bayer(H // cell + 1, W // cell + 1)
            m = (th < k).astype(np.float32)
            m = np.repeat(np.repeat(m, cell, 0), cell, 1)[:H, :W]
            img = img * (1 - m[..., None]) + np.array(BGC, np.float32) / 255 * m[..., None]
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(2000 + i)
    L = Layer()
    if t < 3.5:
        img = s_look(t, L)
    elif t < 6.0:
        img = s_origin(t, L)
    elif t < 11.0:
        img = s_variety(t, L, min(3, int((t - 6.0) / 1.25)))
    elif t < 14.5:
        img = s_packs(t, L)
    else:
        img = s_outro(t, L)
    ui(L, t)
    img = L.apply(img)
    img = dither_dip(img, t)
    img = C.grain(img, rng)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=1)
    tr.vinyl()
    prog = ["Am7", "Fmaj7", "Cmaj7", "G6"]
    bars = [(2.0 * k, prog[k % 4]) for k in range(8)]  # 0 .. 14.5
    for t0, ch in bars:
        tr.pad(CHORDS[ch], t0, min(t0 + 2.0, 14.5), gain=0.085, cutoff=800)
    tr.pad(CHORDS["Am7"] + [71], 14.5, DURATION - 0.1, gain=0.09, cutoff=700)
    tr.arp("Am7", 0.0, 2.0, step=0.5, gain=0.06, kind="bell")
    tr.arp("Fmaj7", 2.0, 3.5, step=0.5, gain=0.05, kind="bell")
    for k in range(int(3.5 / BEAT), int(14.5 / BEAT)):
        tt = k * BEAT
        if k % 2 == 0:
            tr.kick(tt, 0.55)
        tr.hat(tt + BEAT / 2 + 0.01, 0.05)
        if k % 4 == 2:
            tr.tick(tt, 0.08)
    for t0, ch in bars:
        if 3.5 <= t0 + 1.5 and t0 < 14.5:
            r = ROOT[ch]
            for off, dur in ((0, 0.9), (1.0, 0.45), (1.5, 0.45)):
                if 3.5 <= t0 + off < 14.5:
                    tr.bass(r, t0 + off, dur, 0.26)
    tr.bass(ROOT["Am7"], 14.5, 2.5, 0.28)
    for k, t0 in enumerate(VAR_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.12, pan=[-0.3, 0.3, -0.3, 0.3][k])
    tr.arp("Am7", 14.6, 17.0, step=0.25, gain=0.03, kind="bell")
    for b in CUTS:
        tr.whoosh(b + 0.03, 0.25, 0.06)
    tr.impact(14.5, 0.45)
    tr.riser(13.0, 14.45, 0.06)
    return tr.write(path)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
