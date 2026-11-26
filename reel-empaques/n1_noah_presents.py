"""N1 — NOAH PRESENTS: pixel-art Noah spells the sign, presents each pack, then the varieties."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import common as C
import noah as N
from audio import CHORDS, ROOT, SR, Track, filt
from fx import INK, ORANGE, WINE, MAGENTA, RED, H, W, Layer, clamp01, composite, dotmatrix, ease, ease_out, font

NAME = "n1_noah_presents"
DURATION = 20.5
BGC = (21, 19, 18)
DOT = (112, 103, 94)
CREAM = (246, 236, 214)
PACKS = ["color", "cherries", "mule", "dog"]   # the mostly-green "picker" pack is left out

SIGN = (120, 300, 960, 540)
PANEL = (152, 332, 928, 508)
PED = (200, 1260, 880, 1500)
FLOOR_Y = 1500
SACK_TOP = 990

WORD = "NEW LOOK"
LETTER_T = [1.75 + 0.27 * k for k in range(len(WORD))]
LIGHT_T = 3.95
PACK_T = [4.8 + 2.0 * k for k in range(4)]
VAR_T = [12.8, 13.7, 14.6, 15.5]
END_T = 16.4


# ---------------------------------------------------------------------------
# Dotted props (grey halftone, like line art printed in dots)
# ---------------------------------------------------------------------------
def dotted(mask, step=5, dot=2, color=DOT, solid_bg=None):
    """mask: L image (255 full dots, ~128 checker dots). Returns (rgb, alpha) full-res."""
    m = np.asarray(mask)
    rows, cols = H // step, W // step
    c = m[step // 2::step, step // 2::step][:rows, :cols].astype(np.int32)
    yy, xx = np.mgrid[0:rows, 0:cols]
    on = (c > 200) | ((c > 90) & ((xx + yy) % 2 == 0))
    rgb = np.empty((rows, cols, 3), np.float32)
    rgb[:] = np.array(color, np.float32) / 255
    col, a = dotmatrix(rgb, on.astype(np.float32), step, dot=dot, offset=(step - dot) // 2)
    full = np.zeros((H, W, 3), np.float32)
    fa = np.zeros((H, W), np.float32)
    full[:col.shape[0], :col.shape[1]] = col
    fa[:a.shape[0], :a.shape[1]] = a
    if solid_bg is not None:
        sb = np.asarray(solid_bg).astype(np.float32) / 255
        bgc = np.array(BGC, np.float32) / 255
        full = full * fa[..., None] + bgc * (1 - fa[..., None]) * (sb[..., None] > 0)
        fa = np.maximum(fa, sb)
    return full, fa


def build_sign():
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for x in (300, 780):
        d.line([(x, 0), (x, 250)], fill=255, width=6)
    d.rounded_rectangle(SIGN, radius=44, outline=255, width=18)
    d.rounded_rectangle((SIGN[0] + 34, SIGN[1] + 34, SIGN[2] - 34, SIGN[3] - 34), radius=22,
                        outline=128, width=8)
    d.rounded_rectangle((390, 246, 690, 300), radius=16, outline=255, width=8, fill=0)
    return dotted(m)


def build_sacks():
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for (x0, y0, x1, y1) in ((80, 1255, 300, 1500), (290, 1255, 510, 1500), (185, 1000, 405, 1262)):
        d.rounded_rectangle((x0, y0, x1, y1), radius=50, fill=128, outline=255, width=12)
        cx = (x0 + x1) // 2
        d.line([(cx - 34, y0 + 26), (cx + 34, y0 + 26)], fill=255, width=10)
        d.ellipse((cx - 30, (y0 + y1) // 2 - 40, cx + 30, (y0 + y1) // 2 + 40), fill=0,
                  outline=255, width=8)
        d.line([(cx, (y0 + y1) // 2 - 34), (cx - 8, (y0 + y1) // 2),
                (cx + 8, (y0 + y1) // 2 + 34)], fill=255, width=6)
    return dotted(m)


def build_pedestal():
    m = Image.new("L", (W, H), 0)
    solid = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    ds = ImageDraw.Draw(solid)
    ds.rectangle(PED, fill=255)
    d.rectangle(PED, fill=128)
    d.rectangle((PED[0] - 20, PED[1] - 6, PED[2] + 20, PED[1] + 18), fill=255)
    d.rectangle((PED[0], PED[3] - 14, PED[2], PED[3]), fill=255)
    return dotted(m, solid_bg=solid)


def build_floor():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).line([(40, FLOOR_Y), (W - 40, FLOOR_Y)], fill=255, width=8)
    return dotted(m)


SIGN_L = build_sign()
SACK_L = build_sacks()
PED_L = build_pedestal()
FLOOR_L = build_floor()

_pm = Image.new("L", (W, H), 0)
ImageDraw.Draw(_pm).rounded_rectangle(PANEL, radius=20, fill=255)
PANEL_A = np.asarray(_pm).astype(np.float32) / 255
GLOW_A = np.asarray(_pm.filter(ImageFilter.GaussianBlur(46))).astype(np.float32) / 255
CREAM_F = np.array(CREAM, np.float32) / 255
GLOW_C = np.array((255, 214, 150), np.float32) / 255


def put(img, layer, alpha=1.0):
    rgb, a = layer
    a = a[..., None] * alpha
    return img * (1 - a) + rgb * a


# ---------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------
def draw(img, spr, cx, bottom, cell, sx=1.0, sy=1.0, alpha=1.0, flip=False, clip=None):
    """Blit a pixel sprite with its bottom-centre at (cx, bottom); optional squash/stretch."""
    h, w = spr.shape[:2]
    if flip:
        spr = spr[:, ::-1]
    if abs(sx - 1) > 0.01 or abs(sy - 1) > 0.01:
        nw, nh = max(1, round(w * sx)), max(1, round(h * sy))
        yi = (np.arange(nh) * h / nh).astype(int)
        xi = (np.arange(nw) * w / nw).astype(int)
        spr = spr[yi][:, xi]
        h, w = nh, nw
    col, a = dotmatrix(np.ascontiguousarray(spr[..., :3]), spr[..., 3] * alpha, cell, dot=cell)
    y0 = int(bottom - h * cell)
    if clip is not None:   # hide everything below this y (behind the pedestal)
        keep = max(0, min(a.shape[0], int(clip) - y0))
        a = a.copy()
        a[keep:] = 0
    return composite(img, col, a, (int(cx - w * cell / 2), y0))


def hop(t, t0, t1, p0, p1, height):
    """Position along a hop arc and a squash factor."""
    u = clamp01((t - t0) / (t1 - t0))
    x = p0[0] + (p1[0] - p0[0]) * u
    y = p0[1] + (p1[1] - p0[1]) * u - height * 4 * u * (1 - u)
    return x, y


def squash(t, land_times, dur=0.12):
    for lt in land_times:
        if 0 <= t - lt < dur:
            k = math.sin((t - lt) / dur * math.pi)
            return 1 + 0.18 * k, 1 - 0.2 * k
    return 1.0, 1.0


BOW = N.sprite("bow", 62)
PEEK = N.sprite("peek", 48)
CUP = N.sprite("cup", 56)
FACE = N.sprite("face", 54)
SNIFF = N.sprite("sniff", 54)

# Noah's path in act 1: (t0, t1, from, to, height)
SX = 295
HOPS = [(0.40, 0.70, (1180, FLOOR_Y), (930, FLOOR_Y), 70),
        (0.70, 1.00, (930, FLOOR_Y), (690, FLOOR_Y), 70),
        (1.00, 1.30, (690, FLOOR_Y), (450, 1262), 150),
        (1.30, 1.62, (450, 1262), (SX, SACK_TOP), 170)]
for _k, _t in enumerate(LETTER_T):   # a jump up for every letter placed
    if WORD[_k] != " ":
        HOPS.append((_t - 0.13, _t + 0.13, (SX, SACK_TOP), (SX, SACK_TOP), 230))
HOPS += [(LIGHT_T + 0.05, LIGHT_T + 0.35, (SX, SACK_TOP), (SX, SACK_TOP), 120),
         (4.25, 4.55, (SX, SACK_TOP), (60, FLOOR_Y), 160),
         (4.55, 4.75, (60, FLOOR_Y), (-200, FLOOR_Y), 60)]
LANDS = [h[1] for h in HOPS]

PACK_BIG = {k: N.pack_sprite(k, 42) for k in PACKS}
PACK_SMALL = {k: N.pack_sprite(k, 30) for k in PACKS}


def noah_act1(img, t):
    for (t0, t1, p0, p1, hh) in HOPS:
        if t0 <= t < t1:
            x, y = hop(t, t0, t1, p0, p1, hh)
            sx, sy = 1.0, 1.0
            break
    else:
        if t < HOPS[0][0] or t >= HOPS[-1][1]:
            return img
        prev = [h for h in HOPS if h[1] <= t][-1]
        x, y = prev[3]
        sx, sy = squash(t, LANDS)
    return draw(img, BOW, x, y, 5, sx, sy)


# ---------------------------------------------------------------------------
def sign_text(t):
    """(text, colour, lit) shown on the sign at time t."""
    if t < END_T and t >= VAR_T[0] - 0.15:
        k = max(0, max(i for i, v in enumerate(VAR_T) if t >= v - 0.15))
        name = C.VARIETY_NAMES[k]
        n = int(clamp01((t - VAR_T[k]) / (0.06 * len(name))) * len(name) + 0.999)
        return name[:n], C.VARIETY_COLORS[k], False
    if t >= END_T:
        s = "COMING SOON"
        n = int(clamp01((t - END_T - 0.2) / 0.5) * len(s) + 0.999)
        return s[:n], WINE, t >= END_T + 0.8
    n = sum(1 for lt in LETTER_T if t >= lt)
    return WORD[:n], ORANGE, t >= LIGHT_T


def draw_sign(img, L, t):
    img = put(img, SIGN_L)
    text, colr, lit = sign_text(t)
    if lit:
        on_t = LIGHT_T if t < VAR_T[0] else END_T + 0.8
        k = ease((t - on_t) / 0.15)
        if (t - on_t) < 0.25 and int((t - on_t) * 30) % 3 == 1:
            k *= 0.4   # flicker on
        pulse = 0.85 + 0.15 * math.sin(t * 5)
        g = GLOW_A[..., None] * 0.55 * k * pulse
        img = img * (1 - g) + GLOW_C * g
        a = PANEL_A[..., None] * k
        img = img * (1 - a) + CREAM_F * a
        if colr == ORANGE:
            colr = WINE
    L.text((W // 2, 274), "NOW BREWING", font(600, 18), anchor="mm", tracking=6,
           fill=(150, 140, 128))
    if text:
        f = C.fit(WORD if len(text) <= len(WORD) else text, 720, weight=600, start=128,
                  pixel=True)
        if len(text) > len(WORD):
            f = C.fit(text, 720, weight=600, start=128, pixel=True)
        L.text((W // 2 - C.pfont(600, f.size).getlength(
            sign_full(t)) / 2, 424), text, f, fill=colr, anchor="lm")
    return img


def sign_full(t):
    if t >= END_T:
        return "COMING SOON"
    if t >= VAR_T[0] - 0.15:
        k = max(0, max(i for i, v in enumerate(VAR_T) if t >= v - 0.15))
        return C.VARIETY_NAMES[k]
    return WORD


def header(L, t):
    L.text((60, 70), "JUANITO COFFEE", font(600, 20), tracking=6, fill=(200, 190, 176))
    L.text((1020, 70), "NEW HARVEST", font(400, 20), tracking=6, anchor="ra",
           fill=(140, 130, 120))


def act2(img, L, t):
    k = min(3, int((t - PACK_T[0]) // 2.0))
    lt = t - PACK_T[k]
    spr = PACK_BIG[PACKS[k]]
    cell = 8
    ph = spr.shape[0] * cell
    px = 455
    # drop in / slide out
    # rises from behind the pedestal with a little overshoot
    u = clamp01(lt / 0.42)
    over = math.sin(u * math.pi) * 0.12 if u < 1 else 0.0
    y = PED[1] + (1 - ease(u)) * (ph + 20) - over * 120
    sx = sy = 1.0
    x = px - (ease((lt - 1.72) / 0.28) * 760 if lt > 1.72 else 0)
    # Noah peeks up from behind the pedestal on the right
    up = ease((lt - 0.55) / 0.22) * (1 - ease((lt - 1.62) / 0.18))
    if up > 0:
        nb = PED[1] + 40 + (1 - up) * PEEK.shape[0] * 5
        img = draw(img, PEEK, 745, nb + 4 * math.sin(lt * 9), 5, clip=PED[1] + 10)
    img = draw(img, spr, x, y, cell, sx, sy, clip=PED[1] + 10)
    img = put(img, PED_L)
    if lt > 0.4:
        a = ease((lt - 0.4) / 0.3) * (1 - ease((lt - 1.7) / 0.2))
        L.text((W // 2, 1572), f"LOOK  0{k + 1} / 04", font(600, 22), anchor="ms", tracking=8,
               fill=(214, 204, 190), alpha=a)
    return img


def act3(img, L, t):
    lt = t - VAR_T[0]
    a = ease(lt / 0.3)
    bob = 6 * math.sin(lt * 6)
    img = draw(img, CUP, W // 2, PED[1] + 8 + bob, 6, alpha=a)
    img = put(img, PED_L)
    k = max(0, max(i for i, v in enumerate(VAR_T) if t >= v - 0.15))
    L.text((W // 2, 1580), "(new varieties)", font(300, 40, True), anchor="ms",
           fill=(226, 216, 200), alpha=a)
    L.text((W // 2, 1640), f"0{k + 1} / 04", font(600, 20), anchor="ms", tracking=6,
           fill=C.VARIETY_COLORS[k], alpha=a)
    return img


def act4(img, L, t):
    lt = t - END_T
    # Noah's face pops up behind the row of packs
    up = ease_out((lt - 0.9) / 0.35)
    if up > 0:
        img = draw(img, FACE if int(lt * 1.6) % 3 else SNIFF, W // 2,
                   1040 + (1 - up) * 280 + 6 * math.sin(lt * 7), 5)
    xs = [240 + i * 200 for i in range(4)]
    for i, key in enumerate(PACKS):
        p = clamp01((lt - 0.1 - i * 0.12) / 0.34)
        if p <= 0:
            continue
        hpx = PACK_SMALL[key].shape[0] * 5
        y = PED[1] + (1 - ease(p)) * (hpx + 20) - math.sin(p * math.pi) * 40
        img = draw(img, PACK_SMALL[key], xs[i], y, 5, clip=PED[1] + 10)
    img = put(img, PED_L)
    la = C.logo_alpha(170)
    ka = ease((lt - 1.5) / 0.4)
    if ka > 0:
        s = np.empty(la.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, la * ka, ((W - 170) // 2, 1545))
    C.fade_text(L, t, END_T + 1.8, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(500, 20),
                (W // 2, 1790), anchor="ms", tracking=6, color=(214, 204, 190))
    C.fade_text(L, t, END_T + 2.0, "@JUANITOCOFFEE", font(600, 22), (W // 2, 1840),
                anchor="ms", tracking=8, color=ORANGE)
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(12000 + i)
    img = C.bg(BGC)
    L = Layer()
    fade_in = ease(t / 0.4)
    img = put(img, FLOOR_L, fade_in)
    if t < 4.9:
        img = put(img, SACK_L, fade_in * (1 - ease((t - 4.4) / 0.4)))
        img = noah_act1(img, t)
    elif t < VAR_T[0] - 0.15:
        img = act2(img, L, t)
    elif t < END_T:
        img = act3(img, L, t)
    else:
        img = act4(img, L, t)
    img = draw_sign(img, L, t)   # after the acts, so falling packs pass behind the sign
    header(L, t)
    img = L.apply(img)
    img = C.grain(img, rng, 0.035)
    if t > DURATION - 0.45:
        img *= 0.25 + 0.75 * ease((DURATION - t) / 0.45)
    return C.to_u8(img).tobytes()


# ---------------------------------------------------------------------------
def boing(tr, t0, gain=0.05, f0=300, f1=700, dur=0.12):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * (tt / dur)
    ph = np.cumsum(f) / SR
    sig = np.where(ph % 1.0 < 0.5, 1.0, -1.0) * np.exp(-tt / (dur * 0.6))
    tr.add(filt(sig, "lowpass", 4000), t0, gain, pan=tr.rng.uniform(-0.3, 0.3), rev=0.15)


def soundtrack(path):
    tr = Track(DURATION, seed=51)
    tr.vinyl(0.01)
    prog = ["Fmaj7", "G6", "Am7", "Cmaj7"]
    bars = [(2.0 * k, prog[k % 4]) for k in range(11)]
    for t0, ch in bars:
        tr.pad(CHORDS[ch], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.05, cutoff=1200)
    # chiptune groove from the sign light-up on
    for k in range(int(4.0 / 0.5), int(20.0 / 0.5)):
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
        if t0 >= 4.0:
            r = ROOT[ch]
            for off, dur, dm in ((0, 0.4, 0), (0.5, 0.2, 12), (1.0, 0.4, 7), (1.5, 0.2, 12)):
                if t0 + off < 20.0:
                    tr.bass(r + dm, t0 + off, dur, 0.22)
            if 4.0 <= t0 < 20.0:
                tr.arp(ch, t0, min(t0 + 2.0, 20.0), step=0.25, gain=0.022)
    for (t0, t1, p0, p1, hh) in HOPS:
        boing(tr, t0, 0.04 if hh < 200 else 0.05, 260, 560 + hh)
    for lt in LETTER_T:
        tr.chip(84 + (LETTER_T.index(lt) % 5) * 2, lt, 0.08, 0.05, duty=0.125)
    for k in (0, 4, 7):
        tr.bell(72 + k, LIGHT_T, 0.08, pan=-0.2 + 0.2 * k / 7)
    n = int(0.3 * SR)
    tr.add(filt(tr.rng.standard_normal(n), "bandpass", [80, 400]) * np.exp(-np.arange(n) / SR / 0.1),
           LIGHT_T, 0.15)
    for t0 in PACK_T:
        boing(tr, t0, 0.04, 200, 600, 0.3)
        tr.thud(t0 + 0.42, 0.12, f=220)
        boing(tr, t0 + 0.55, 0.035, 400, 900)
        tr.whoosh(t0 + 2.0, 0.25, 0.03)
    for k, t0 in enumerate(VAR_T):
        for j in range(len(C.VARIETY_NAMES[k])):
            tr.tick(t0 + j * 0.06, 0.04)
        tr.chip([81, 84, 88, 86][k], t0, 0.25, 0.06, duty=0.125)
    for i in range(4):
        boing(tr, END_T + 0.1 + i * 0.12, 0.03, 300 + 80 * i, 800 + 80 * i, 0.2)
    boing(tr, END_T + 0.9, 0.05, 300, 1000, 0.18)
    for k in (0, 4, 7, 12):
        tr.bell(76 + k, END_T + 0.8, 0.07, pan=-0.3 + 0.2 * k / 4)
    return tr.write(path, fade=0.5)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
