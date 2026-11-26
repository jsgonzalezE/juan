"""P2 — LOOKBOOK: light grey editorial presentation of the packs in crisp pixel art."""
import math

import numpy as np

import common as C
import minimal as M
from audio import CHORDS, ROOT, Track
from fx import ORANGE, WINE, H, W, Layer, clamp01, composite, ease, ease_out, font

NAME = "p2_lookbook"
DURATION = 16.0
BGC = (217, 213, 207)
INKD = (40, 35, 32)
SHADOW = (192, 186, 178)
G_COLOR = C.pix("color", 60, ncolors=32)
G_DARK = C.pix("dark", 60, ncolors=32)
VAR_T = [10.2, 10.6, 11.0, 11.4]
LOGO_W, LOGO_CELL = 320, 5
LOGO_G = C.logo_grid(LOGO_W, LOGO_CELL)
LOGO_A = C.logo_alpha(LOGO_W)
_rnd = np.random.default_rng(4).uniform(0, 0.08, 60)


def pixels(grid, cell):
    r, c = grid.shape[:2]
    img = np.repeat(np.repeat(grid, cell, 0), cell, 1).astype(np.float32)
    a = np.ones((r * cell, c * cell), np.float32)
    a[cell - 1::cell, :] = 0
    a[:, cell - 1::cell] = 0
    return img, a


PX = {(k, cell): pixels(g, cell) for k, g in (("color", G_COLOR), ("dark", G_DARK))
      for cell in (10, 6)}
SH = np.array(SHADOW, np.float32) / 255


def pack(img, key, cell, x, y, t_in, t_out, t, float_amp=6):
    """Columns rise into place at t_in and drop away at t_out."""
    pim, pa = PX[(key, cell)]
    cols = pim.shape[1] // cell
    bob = int(float_amp * math.sin((t - t_in) * 1.8)) if t > t_in + 1.2 else 0
    for c in range(cols):
        d = c * 0.012 + _rnd[c % 60]
        pin = ease_out(clamp01((t - t_in - d) / 0.5))
        pout = ease(clamp01((t - t_out - d * 0.6) / 0.4)) if t_out is not None else 0.0
        if pin <= 0 or pout >= 1:
            continue
        dy = int((1 - pin) * 240 + pout * 260) + bob
        al = pin * (1 - pout)
        xs = slice(c * cell, (c + 1) * cell)
        sh = np.broadcast_to(SH, (pim.shape[0], cell, 3))
        composite(img, sh, pa[:, xs] * al * 0.9, (x + c * cell + 16, y + dy + 16))
    for c in range(cols):
        d = c * 0.012 + _rnd[c % 60]
        pin = ease_out(clamp01((t - t_in - d) / 0.5))
        pout = ease(clamp01((t - t_out - d * 0.6) / 0.4)) if t_out is not None else 0.0
        if pin <= 0 or pout >= 1:
            continue
        dy = int((1 - pin) * 240 + pout * 260) + bob
        al = pin * (1 - pout)
        xs = slice(c * cell, (c + 1) * cell)
        composite(img, pim[:, xs], pa[:, xs] * al, (x + c * cell, y + dy))
    return img


def hud(L, t, page):
    L.text((60, 64), "JUANITO COFFEE", font(600, 18), tracking=6, fill=INKD)
    L.text((1020, 64), "NEW HARVEST", font(400, 18), tracking=6, anchor="ra", fill=INKD, alpha=0.6)
    L.text((60, 1856), "HUILA · COLOMBIA", font(400, 18), tracking=6, anchor="ls", fill=INKD,
           alpha=0.6)
    L.text((1020, 1856), page, font(500, 18), tracking=6, anchor="rs", fill=INKD, alpha=0.8)


def label(L, t, t0, t1, left, right, y, x0=240, x1=840):
    a = ease((t - t0) / 0.4) * clamp01((t1 - t) / 0.3)
    if a <= 0:
        return
    L.text((x0, y), left, font(500, 18), tracking=8, fill=INKD, alpha=a)
    L.text((x1, y), right, font(500, 18), tracking=8, fill=INKD, anchor="ra", alpha=a)


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(9000 + i)
    img = C.bg(BGC)
    L = Layer()
    sm = font(300, 32, True)
    # look 01 — colourful
    if 0.4 <= t < 5.4:
        img = pack(img, "color", 10, 240, 380, 0.5, 4.3, t)
        label(L, t, 0.9, 4.4, "LOOK 01", "01 / 02", 345)
        C.fade_text(L, t, 1.4, "(new look)", sm, (W // 2, 1460), anchor="ms", color=INKD, end=4.4)
    # look 02 — dark
    if 4.6 <= t < 9.4:
        img = pack(img, "dark", 10, 240, 510, 4.7, 8.3, t)
        label(L, t, 5.1, 8.4, "LOOK 02", "02 / 02", 475)
        C.fade_text(L, t, 5.6, "(new look)", sm, (W // 2, 1460), anchor="ms", color=INKD, end=8.4)
    # both + varieties
    if 8.7 <= t < 13.9:
        img = pack(img, "color", 6, 150, 512, 8.8, 12.8, t, 4)
        img = pack(img, "dark", 6, 570, 590, 9.0, 12.9, t, 4)
        C.fade_text(L, t, 9.9, "(new varieties)", sm, (W // 2, 1215), anchor="ms", color=INKD,
                    end=12.9)
        for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, VAR_T)):
            C.fade_text(L, t, t0, name, font(300, 46), (W // 2, 1290 + k * 66), anchor="ms",
                        tracking=16, color=INKD, end=12.9)
        C.fade_text(L, t, 12.0, "ORIGIN  —  HUILA, COLOMBIA", font(500, 18), (W // 2, 1600),
                    anchor="ms", tracking=8, color=WINE, end=12.95)
    # logo
    if t >= 13.4:
        lt = t - 13.4
        on = ((LOGO_G > 0.3) & (M.order(LOGO_G.shape, 9) < lt / 0.5)).astype(np.float32)
        k = ease((lt - 0.55) / 0.3)
        c = np.empty(LOGO_G.shape + (3,), np.float32)
        c[:] = np.array(INKD, np.float32) / 255
        lx, ly = (W - LOGO_W) // 2, 620
        col, a = C.dotmatrix(c, on * (1 - k), LOGO_CELL, dot=3)
        composite(img, col, a, (lx, ly))
        if k > 0:
            s = np.empty(LOGO_A.shape + (3,), np.float32)
            s[:] = np.array(INKD, np.float32) / 255
            composite(img, s, LOGO_A * k, (lx, ly))
        C.fade_text(L, t, 13.9, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(500, 20), (W // 2, 1120),
                    anchor="ms", tracking=8, color=INKD)
        C.fade_text(L, t, 14.1, "(coming soon)", sm, (W // 2, 1190), anchor="ms", color=INKD)
        C.fade_text(L, t, 14.3, "@JUANITOCOFFEE", font(600, 20), (W // 2, 1260), anchor="ms",
                    tracking=8, color=WINE)
    page = "01 / 03" if t < 8.6 else ("02 / 03" if t < 13.3 else "03 / 03")
    hud(L, t, page)
    img = L.apply(img)
    img = C.grain(img, rng, 0.03)
    if t < 0.35:
        img = img * ease(t / 0.35) + (1 - ease(t / 0.35)) * np.array(BGC, np.float32) / 255
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=22)
    tr.vinyl(0.01)
    prog = ["Fmaj7", "Cmaj7", "Am7", "G6"]
    for k in range(8):
        t0 = 2.0 * k
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.065, cutoff=1000)
    for k in range(1, 27):
        tt = k * 0.5
        if k % 2 == 0:
            tr.kick(tt, 0.4)
        else:
            tr.clap(tt, 0.08)
        tr.hat(tt + 0.25, 0.03)
    for t0 in range(0, 14, 2):
        r = ROOT[prog[(t0 // 2) % 4]]
        tr.bass(r, float(t0), 0.9, 0.2)
        tr.bass(r + 7, t0 + 1.0, 0.9, 0.16)
    for t0 in (0.5, 4.7, 8.8, 9.0):
        tr.whoosh(t0 + 0.35, 0.35, 0.035)
    for t0 in (4.3, 8.3, 12.8):
        tr.whoosh(t0 + 0.3, 0.3, 0.03)
    tr.bell(84, 1.0, 0.07)
    tr.bell(88, 5.2, 0.07, pan=0.3)
    for k, t0 in enumerate(VAR_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.07, pan=[-0.3, 0.3, -0.3, 0.3][k])
    tr.bell(76, 13.4, 0.09)
    tr.bell(84, 13.9, 0.07, pan=0.3)
    return tr.write(path, fade=0.8)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
