"""Version 2 — POP: light grey background, chunky pixel-art packaging built from falling tiles."""
import math

import numpy as np
from PIL import Image

import common as C
from audio import BEAT, CHORDS, ROOT, Track
from fx import MAGENTA, ORANGE, WINE, H, W, Layer, clamp01, composite, ease, ease_out, font

NAME = "v2_pop"
DURATION = 16.0
BGC = (214, 209, 202)
SHADOW = (186, 180, 172)
NAMES_T = [4.75, 5.25, 5.75, 6.25]

# pack 1: colourful, built by falling tiles
P1 = C.pix("color", 36)
R1, C1 = P1.shape[:2]
CELL = 18
X1, Y1 = (W - C1 * CELL) // 2, 540
_r = np.random.default_rng(3)
_yy, _xx = np.mgrid[0:R1, 0:C1]
LAND = 0.3 + (R1 - 1 - _yy) * 0.036 + _r.uniform(0, 0.14, (R1, C1))
FALL = 0.34

# pack 2: dark, tiles pop in along a diagonal wave
P2 = C.pix("dark", 34)
R2, C2 = P2.shape[:2]
X2, Y2 = (W - C2 * CELL) // 2, 560
POP = 9.15 + (_r.uniform(0, 1, (R2, C2)) * 0.25) + (np.mgrid[0:R2, 0:C2].sum(0)) * 0.018

LOGO_W = 360
LOGO_A = C.logo_alpha(LOGO_W)


def pack_image(grid, cell, gap=1):
    r, c = grid.shape[:2]
    img = np.repeat(np.repeat(grid, cell, 0), cell, 1)
    a = np.ones((r * cell, c * cell), np.float32)
    if gap:
        a[cell - gap::cell, :] = 0
        a[:, cell - gap::cell] = 0
    return img, a


PACK1_IMG, PACK1_A = pack_image(P1, CELL)
PACK2_IMG, PACK2_A = pack_image(P2, CELL)
SH1 = np.ones(PACK1_IMG.shape, np.float32) * np.array(SHADOW, np.float32) / 255
SH2 = np.ones(PACK2_IMG.shape, np.float32) * np.array(SHADOW, np.float32) / 255


def scaled(img, a, width):
    h = round(img.shape[0] * width / img.shape[1])
    im = Image.fromarray(C.to_u8(img)).resize((width, h), Image.NEAREST)
    am = Image.fromarray(C.to_u8(a)).resize((width, h), Image.NEAREST)
    return np.asarray(im).astype(np.float32) / 255, np.asarray(am).astype(np.float32) / 255


def ui(L, t):
    L.text((60, 62), "JUANITO COFFEE", font(800, 24), fill=WINE, tracking=4)
    L.text((1020, 66), "NEW HARVEST", font(600, 20), fill=WINE, tracking=6, anchor="ra",
           alpha=0.6)
    for k, c in enumerate(C.VARIETY_COLORS):
        L.rect((60 + k * 30, 1836, 80 + k * 30, 1856), outline=None, fill=c)
    L.text((1020, 1856), "HUILA · COLOMBIA", font(700, 20), fill=WINE, tracking=6, anchor="rs")


def falling_tiles(img, t, bob=0):
    """Draw pack 1 tiles that have started falling (vectorised splat)."""
    start = LAND - FALL
    vis = t >= start
    if not vis.any():
        return img
    u = np.clip((t - start) / FALL, 0, 1)
    y_off = np.where(u < 1, -(1 - u ** 2) * 1000, 0.0)
    # tiny bounce after landing
    after = t - LAND
    y_off = y_off - np.where((after > 0) & (after < 0.12), np.sin(after / 0.12 * math.pi) * 10, 0)
    ys = (Y1 + _yy * CELL + y_off + bob)[vis].astype(int)
    xs = (X1 + _xx * CELL)[vis].astype(int)
    cols = P1[vis]
    d = CELL - 1
    oy, ox = np.mgrid[0:d, 0:d]
    # shadow for landed tiles
    landed = (t >= LAND)[vis]
    if landed.any():
        Xs = (xs[landed][:, None, None] + ox[None] + 12).ravel()
        Ys = (ys[landed][:, None, None] + oy[None] + 12).ravel()
        ok = (Xs >= 0) & (Xs < W) & (Ys >= 0) & (Ys < H)
        img[Ys[ok], Xs[ok]] = np.array(SHADOW, np.float32) / 255
    X = (xs[:, None, None] + ox[None]).ravel()
    Y = (ys[:, None, None] + oy[None]).ravel()
    Cc = np.repeat(cols, d * d, 0)
    ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
    img[Y[ok], X[ok]] = Cc[ok]
    return img


def bullet(L, x, y, color, s=18):
    for dx, dy in ((0, 0), (s, 0), (0, s), (s, s)):
        L.rect((x + dx, y + dy, x + dx + s - 2, y + dy + s - 2), outline=None, fill=color)


def s_build(t, L):
    img = C.bg(BGC)
    if t < 4.0:
        bob = int(6 * math.sin((t - 2.8) * 2.4)) if t > 2.8 else 0
        img = falling_tiles(img, t, bob)
    C.fade_text(L, t, 2.55, "NEW", font(800, 170), (W // 2, 330), anchor="ms", color=WINE,
                rise=30)
    C.fade_text(L, t, 2.75, "PACKAGING", C.fit("PACKAGING", 940, 800, 150), (W // 2, 470),
                anchor="ms", color=WINE, rise=30)
    C.fade_text(L, t, 3.05, "COMING SOON", font(700, 28), (W // 2, 1700), anchor="ms",
                color=ORANGE, tracking=14)
    return img


def s_varieties(t, L):
    lt = t - 4.0
    img = C.bg(BGC)
    e = ease(lt / 0.55)
    wdt = int(C1 * CELL + (300 - C1 * CELL) * e)
    pk, pa = scaled(PACK1_IMG, PACK1_A, wdt)
    cy = int((Y1 + R1 * CELL / 2) + (400 - (Y1 + R1 * CELL / 2)) * e)
    x, y = (W - wdt) // 2, cy - pk.shape[0] // 2
    sh = np.ones(pk.shape, np.float32) * np.array(SHADOW, np.float32) / 255
    sx = max(4, int(12 * wdt / (C1 * CELL)))
    composite(img, sh, pa, (x + sx, y + sx))
    composite(img, pk, pa, (x, y))
    C.fade_text(L, t, 4.4, "NEW VARIETIES", font(700, 24), (W // 2, 780), anchor="ms",
                color=MAGENTA, tracking=14)
    f = font(800, 120)
    for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, NAMES_T)):
        if t < t0:
            continue
        p = ease_out((t - t0) / 0.3)
        y0 = 920 + k * 140
        tw = f.getlength(name)
        xx = W // 2 + (1 - p) * 300
        L.text((xx, y0), name, f, fill=WINE, anchor="ms", alpha=p)
        bullet(L, int(xx - tw / 2 - 70), y0 - 72, C.VARIETY_COLORS[k])
    C.fade_text(L, t, 7.0, "ONE ORIGIN", font(700, 24), (W // 2, 1500), anchor="ms",
                color=MAGENTA, tracking=14)
    C.fade_text(L, t, 7.2, "HUILA, COLOMBIA", font(800, 76), (W // 2, 1600), anchor="ms",
                color=ORANGE)
    return img


def s_second(t, L):
    img = C.bg(BGC)
    s = np.clip((t - POP) / 0.18, 0, 1)
    s = 1 - (1 - s) ** 3
    d = CELL - 1
    for r in range(R2):
        row_s = s[r]
        if not (row_s > 0).any():
            continue
        for c in np.nonzero(row_s > 0)[0]:
            k = row_s[c]
            sz = max(1, int(d * k))
            off = (d - sz) // 2
            x = X2 + c * CELL + off
            y = Y2 + r * CELL + off
            if k >= 1:
                img[y + 12:y + 12 + sz, x + 12:x + 12 + sz] = np.array(SHADOW, np.float32) / 255
            img[y:y + sz, x:x + sz] = P2[r, c]
    C.fade_text(L, t, 9.6, "ALMOST", font(800, 150), (W // 2, 300), anchor="ms", color=WINE,
                rise=30)
    C.fade_text(L, t, 9.8, "READY", font(800, 150), (W // 2, 450), anchor="ms", color=WINE,
                rise=30)
    C.fade_text(L, t, 10.6, "(stay tuned)", font(400, 46, True), (W // 2, 1520), anchor="ms",
                color=WINE)
    return img


def s_outro(t, L):
    lt = t - 12.5
    img = C.bg(BGC)
    for k, (im, a, x) in enumerate(((PACK1_IMG, PACK1_A, 300), (PACK2_IMG, PACK2_A, 590))):
        p = ease_out((lt - 0.1 - k * 0.15) / 0.35)
        if p <= 0:
            continue
        pk, pa = scaled(im, a, 190)
        y = 190 + int((1 - p) * 60)
        sh = np.ones(pk.shape, np.float32) * np.array(SHADOW, np.float32) / 255
        composite(img, sh, pa * p, (x + 6, y + 6))
        composite(img, pk, pa * p, (x, y))
    k = ease((lt - 0.4) / 0.4)
    if k > 0:
        lg = np.ones(LOGO_A.shape + (3,), np.float32) * np.array(WINE, np.float32) / 255
        composite(img, lg, LOGO_A * k, ((W - LOGO_W) // 2, 600 + int((1 - k) * 30)))
    C.fade_text(L, t, 13.3, "GREEN COFFEE", font(800, 76), (W // 2, 1180), anchor="ms",
                color=WINE)
    C.fade_text(L, t, 13.45, "FROM HUILA, COLOMBIA", font(700, 24), (W // 2, 1240), anchor="ms",
                color=WINE, tracking=10)
    C.fade_text(L, t, 13.7, "COMING SOON", font(800, 60), (W // 2, 1370), anchor="ms",
                color=ORANGE)
    C.fade_text(L, t, 13.9, "@JUANITOCOFFEE", font(700, 32), (W // 2, 1450), anchor="ms",
                color=WINE, tracking=8)
    return img


def tile_wipe(img, t, b, dur=0.4):
    """Grey tiles rise column by column to hide a cut at time b."""
    if not (b - dur <= t < b + dur):
        return img
    cell = 60
    cols = W // cell
    out = img
    pal = [np.array(c_, np.float32) / 255 for c_ in (WINE, ORANGE, MAGENTA)]
    for c in range(cols):
        colr = pal[c % 3]
        delay = (c % 2) * 0.05 + c * 0.012
        if t < b:
            p = ease(clamp01((t - (b - dur) - delay) / (dur - 0.2)))
            top = int(H - p * H)
            out[top:, c * cell:(c + 1) * cell - 4] = colr
        else:
            p = ease(clamp01((t - b - delay) / (dur - 0.2)))
            bot = int(H - p * H)
            out[:bot, c * cell:(c + 1) * cell - 4] = colr
    return out


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(3000 + i)
    L = Layer()
    if t < 4.0:
        img = s_build(t, L)
    elif t < 9.0:
        img = s_varieties(t, L)
    elif t < 12.5:
        img = s_second(t, L)
    else:
        img = s_outro(t, L)
    ui(L, t)
    img = L.apply(img)
    for b in (9.0, 12.5):
        img = tile_wipe(img, t, b)
    img = C.grain(img, rng, 0.03)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=2)
    prog = ["Fmaj7", "G6", "Am7", "Cmaj7"]
    bars = [(2.0 * k, prog[k % 4]) for k in range(8)]
    for t0, ch in bars:
        tr.pad(CHORDS[ch], t0, t0 + 2.0, gain=0.06, cutoff=1400)
        if t0 >= 2.0:
            tr.arp(ch, t0, t0 + 2.0, step=0.25, gain=0.035)
    # tile landings: soft ticks while the pack builds
    land = np.sort(LAND.ravel())
    for tt in land[::18]:
        tr.thud(tt, 0.05, f=900 + 400 * tr.rng.random())
    for k in range(int(2.5 / BEAT), int(15.0 / BEAT)):
        tt = k * BEAT
        tr.kick(tt, 0.75)
        if k % 2 == 1:
            tr.clap(tt, 0.22)
        tr.hat(tt + BEAT / 2 + 0.01, 0.06, open_=(k % 4 == 3))
    for t0, ch in bars:
        if t0 >= 2.0:
            r = ROOT[ch]
            for off, dur, dm in ((0, 0.4, 0), (0.5, 0.2, 12), (0.75, 0.2, 0), (1.25, 0.4, 7),
                                 (1.75, 0.2, 12)):
                tr.bass(r + dm, t0 + off, dur, 0.28)
    tr.riser(1.3, 2.5, 0.07)
    tr.impact(2.5, 0.45)
    for k, t0 in enumerate(NAMES_T):
        tr.chip([81, 84, 88, 86][k], t0, 0.3, 0.07, duty=0.125)
    pops = np.sort(POP.ravel())
    for tt in pops[::25]:
        tr.blip(tt, 0.025)
    for b in (9.0, 12.5):
        tr.whoosh(b, 0.35, 0.07)
    tr.impact(12.5, 0.4)
    tr.bass(ROOT["Fmaj7"], 15.0, 1.0, 0.22)
    return tr.write(path)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
