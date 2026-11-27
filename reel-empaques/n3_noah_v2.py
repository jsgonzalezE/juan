"""N3 — NOAH PRESENTS v2: sharper pixel Noah tuned for black, real pack photos that
materialise from pixels, more character animation (head tilt, blinks, steam)."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import common as C
import noah as N
import n1_noah_presents as B
from audio import CHORDS, ROOT, SR, Track, filt
from fx import INK, ORANGE, WINE, H, W, Layer, clamp01, composite, dotmatrix, ease, ease_out, font

NAME = "n3_noah_v2"
DURATION = 21.0
BGC = B.BGC
PACKS = B.PACKS
FLOOR_Y = B.FLOOR_Y
PED = (120, 1260, 960, 1500)
LETTER_T, LIGHT_T = B.LETTER_T, B.LIGHT_T
PACK_T = [4.8 + 2.0 * k for k in range(4)]
VAR_T = B.VAR_T
END_T = B.END_T


def build_pedestal():
    m = Image.new("L", (W, H), 0)
    solid = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    ImageDraw.Draw(solid).rectangle(PED, fill=255)
    d.rectangle(PED, fill=128)
    d.rectangle((PED[0] - 20, PED[1] - 6, PED[2] + 20, PED[1] + 18), fill=255)
    d.rectangle((PED[0], PED[3] - 14, PED[2], PED[3]), fill=255)
    return B.dotted(m, solid_bg=solid)


PED_L = build_pedestal()

# --- Noah sprites (sticker palette: cream rim so the silhouette reads on black)
BOW = N.sprite2("bow", 64)
PEEK = N.sprite2("peek", 62)
CUP = N.sprite2("cup", 60)
FACE = N.sprite2("face", 66)
SNIFF = N.sprite2("sniff", 66)
SACK = N.sprite2("sack", 60)


@lru_cache(maxsize=None)
def tilted(name, deg):
    spr = {"peek": PEEK, "face": FACE, "sniff": SNIFF, "cup": CUP}[name]
    if deg == 0:
        return spr
    im = Image.fromarray((spr * 255).astype(np.uint8), "RGBA")
    r = im.rotate(deg, resample=Image.NEAREST, expand=True)
    a = np.asarray(r).astype(np.float32) / 255
    a.setflags(write=False)
    return a


def draw(img, spr, cx, bottom, cell, sx=1.0, sy=1.0, alpha=1.0, clip=None):
    return B.draw(img, spr, cx, bottom, cell, sx, sy, alpha, clip=clip)


# --- real packs
BIG_W, SMALL_W = 390, 176
BIG = {k: N.pack_photo(k, BIG_W) for k in PACKS}
SMALL = {k: N.pack_photo(k, SMALL_W) for k in PACKS}
STEPS = [72, 48, 36, 24, 16, 12, 8, 6, 4, 2, 1]


@lru_cache(maxsize=None)
def halo(key, width):
    p = N.pack_photo(key, width)
    pad = 90
    a = np.pad(p[..., 3], pad)
    g = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(48))).astype(np.float32) / 255
    g.setflags(write=False)
    return g, pad


GLOW = np.array((255, 214, 150), np.float32) / 255


def show_pack(img, key, width, cx, bottom, p_in, p_out=0.0, clip=None):
    """Draw a real pack that materialises from big pixels (p_in 0->1) and back (p_out 0->1)."""
    if p_in <= 0 or p_out >= 1:
        return img
    p = N.pack_photo(key, width)
    k = min(p_in, 1 - p_out)
    cell = STEPS[min(len(STEPS) - 1, int(clamp01(k) * (len(STEPS) - 1) + 1e-6))]
    q = N.pixelate(p, cell)
    h = q.shape[0]
    x0, y0 = int(cx - width / 2), int(bottom - h)
    g, pad = halo(key, width)
    ga = g * 0.22 * clamp01(k * 1.3)
    img = composite(img, np.broadcast_to(GLOW, g.shape + (3,)).copy(), ga, (x0 - pad, y0 - pad))
    a = q[..., 3].copy()
    if clip is not None:
        a[max(0, int(clip) - y0):] = 0
    return composite(img, np.ascontiguousarray(q[..., :3]), a, (x0, y0))


# ---------------------------------------------------------------------------
def noah_act1(img, t):
    for (t0, t1, p0, p1, hh) in B.HOPS:
        if t0 <= t < t1:
            x, y = B.hop(t, t0, t1, p0, p1, hh)
            sx = sy = 1.0
            break
    else:
        if t < B.HOPS[0][0] or t >= B.HOPS[-1][1]:
            return img
        x, y = [h for h in B.HOPS if h[1] <= t][-1][3]
        sx, sy = B.squash(t, B.LANDS)
    return draw(img, BOW, x, y, 5, sx, sy)


def act2(img, L, t):
    k = min(3, int((t - PACK_T[0]) // 2.0))
    lt = t - PACK_T[k]
    key = PACKS[k]
    img = show_pack(img, key, BIG_W, 425, PED[1], ease(lt / 0.55), ease((lt - 1.68) / 0.3))
    # Noah pops up on the right, tilts his head at the pack, ducks before the next one
    up = ease((lt - 0.45) / 0.22) * (1 - ease((lt - 1.62) / 0.18))
    if up > 0:
        deg = int(round(7 * ease((lt - 0.8) / 0.25) * (1 - ease((lt - 1.4) / 0.2))))
        spr = tilted("peek", deg)
        nb = PED[1] + 40 + (1 - up) * spr.shape[0] * 5
        img = draw(img, spr, 790, nb + 3 * math.sin(lt * 9), 5, clip=PED[1] + 10)
    img = B.put(img, PED_L)
    if lt > 0.4:
        a = ease((lt - 0.4) / 0.3) * (1 - ease((lt - 1.7) / 0.2))
        L.text((W // 2, 1572), f"LOOK  0{k + 1} / 04", font(600, 22), anchor="ms", tracking=8,
               fill=(214, 204, 190), alpha=a)
    return img


STEAM = np.array((236, 228, 214), np.float32) / 255


def act3(img, L, t):
    lt = t - VAR_T[0]
    a = ease(lt / 0.3)
    bob = 5 * math.sin(lt * 5)
    deg = int(round(5 * math.sin(lt * 2.2)))
    spr = tilted("cup", 0)
    top = PED[1] + 8 + bob - spr.shape[0] * 6
    # pixel steam rising out of the cup
    for j, x0 in enumerate((W // 2 - 95, W // 2 + 85)):
        for s in range(9):
            yy = top + 30 - s * 34 - (lt * 50) % 34
            xx = x0 + 18 * math.sin(s * 0.7 - lt * 3.5 + j * 2)
            al = a * (1 - s / 9) ** 1.5 * 0.55
            sz = 10 if s < 4 else 8
            sq = np.full((sz, sz), al, np.float32)
            composite(img, np.broadcast_to(STEAM, (sz, sz, 3)).copy(), sq,
                      (int(xx - sz / 2), int(yy)))
    img = draw(img, spr, W // 2, PED[1] + 8 + bob, 6, alpha=a)
    img = B.put(img, PED_L)
    kk = max(0, max(i for i, v in enumerate(VAR_T) if t >= v - 0.15))
    L.text((W // 2, 1580), "(new varieties)", font(300, 40, True), anchor="ms",
           fill=(226, 216, 200), alpha=a)
    L.text((W // 2, 1640), f"0{kk + 1} / 04", font(600, 20), anchor="ms", tracking=6,
           fill=C.VARIETY_COLORS[kk], alpha=a)
    return img


def act4(img, L, t):
    lt = t - END_T
    up = ease_out((lt - 0.95) / 0.35)
    if up > 0:
        blink = (lt % 1.6) > 1.42
        deg = int(round(6 * math.sin(lt * 1.7)))
        spr = tilted("sniff" if blink else "face", deg)
        img = draw(img, spr, W // 2, 1010 + (1 - up) * 330 + 5 * math.sin(lt * 6), 5)
    xs = [PED[0] + 18 + SMALL_W / 2 + i * (SMALL_W + 27) for i in range(4)]
    for i, key in enumerate(PACKS):
        img = show_pack(img, key, SMALL_W, xs[i], PED[1], ease((lt - 0.1 - i * 0.14) / 0.45))
    img = B.put(img, PED_L)
    la = C.logo_alpha(170)
    ka = ease((lt - 1.6) / 0.4)
    if ka > 0:
        s = np.empty(la.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, la * ka, ((W - 170) // 2, 1545))
    C.fade_text(L, t, END_T + 1.9, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(500, 20),
                (W // 2, 1790), anchor="ms", tracking=6, color=(214, 204, 190))
    C.fade_text(L, t, END_T + 2.1, "@JUANITOCOFFEE", font(600, 22), (W // 2, 1840),
                anchor="ms", tracking=8, color=ORANGE)
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(14000 + i)
    img = C.bg(BGC)
    L = Layer()
    fade_in = ease(t / 0.4)
    img = B.put(img, B.FLOOR_L, fade_in)
    if t < 4.9:
        img = B.put(img, B.SACK_L, fade_in * (1 - ease((t - 4.4) / 0.4)))
        img = noah_act1(img, t)
    elif t < VAR_T[0] - 0.15:
        img = act2(img, L, t)
    elif t < END_T:
        img = act3(img, L, t)
    else:
        img = act4(img, L, t)
    img = B.draw_sign(img, L, t)
    B.header(L, t)
    img = L.apply(img)
    img = C.grain(img, rng, 0.03)
    if t > DURATION - 0.45:
        img *= 0.25 + 0.75 * ease((DURATION - t) / 0.45)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=71)
    tr.vinyl(0.01)
    prog = ["Fmaj7", "G6", "Am7", "Cmaj7"]
    bars = [(2.0 * k, prog[k % 4]) for k in range(11)]
    for t0, ch in bars:
        tr.pad(CHORDS[ch], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.05, cutoff=1200)
    for k in range(int(4.0 / 0.5), int(20.4 / 0.5)):
        tt = k * 0.5
        if VAR_T[0] <= tt < END_T:
            if k % 2 == 0:
                tr.kick(tt, 0.45)
            tr.hat(tt + 0.25, 0.04)
            continue
        if k % 2 == 0:
            tr.kick(tt, 0.65)
        else:
            tr.snare(tt, 0.18)
        tr.hat(tt + 0.25, 0.05)
    for t0, ch in bars:
        if 4.0 <= t0 < 20.4:
            r = ROOT[ch]
            for off, dur, dm in ((0, 0.4, 0), (0.5, 0.2, 12), (1.0, 0.4, 7), (1.5, 0.2, 12)):
                if t0 + off < 20.4:
                    tr.bass(r + dm, t0 + off, dur, 0.22)
            tr.arp(ch, t0, min(t0 + 2.0, 20.4), step=0.25, gain=0.022)
    for (t0, t1, p0, p1, hh) in B.HOPS:
        B.boing(tr, t0, 0.04 if hh < 200 else 0.05, 260, 560 + hh)
    for j, lt_ in enumerate(LETTER_T):
        tr.chip(84 + (j % 5) * 2, lt_, 0.08, 0.05, duty=0.125)
    for kk in (0, 4, 7):
        tr.bell(72 + kk, LIGHT_T, 0.08, pan=-0.2 + 0.2 * kk / 7)
    for t0 in PACK_T:   # materialise: a quick rising run of blips, then a soft chime
        for j in range(8):
            tr.chip(72 + j * 2, t0 + j * 0.06, 0.05, 0.025, duty=0.5)
        tr.bell(88, t0 + 0.55, 0.06)
        B.boing(tr, t0 + 0.47, 0.035, 400, 900)
        for j in range(5):
            tr.chip(86 - j * 2, t0 + 1.7 + j * 0.05, 0.04, 0.02, duty=0.5)
    for kk, t0 in enumerate(VAR_T):
        for j in range(len(C.VARIETY_NAMES[kk])):
            tr.tick(t0 + j * 0.06, 0.04)
        tr.chip([81, 84, 88, 86][kk], t0, 0.25, 0.06, duty=0.125)
    for i in range(4):
        for j in range(4):
            tr.chip(76 + i * 3 + j * 2, END_T + 0.1 + i * 0.14 + j * 0.06, 0.04, 0.02, duty=0.5)
    B.boing(tr, END_T + 0.95, 0.05, 300, 1000, 0.18)
    for kk in (0, 4, 7, 12):
        tr.bell(76 + kk, END_T + 0.8, 0.07, pan=-0.3 + 0.2 * kk / 4)
    return tr.write(path, fade=0.5)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
