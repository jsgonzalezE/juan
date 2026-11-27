"""Version 3 — GRID: a 3x4 grid of pixel tiles that flip on the beat and solve into the packs."""
import math

import numpy as np
from PIL import Image

import common as C
from audio import BEAT, CHORDS, ROOT, Track
from fx import CREAM, INK, MAGENTA, ORANGE, RED, WINE, H, W, Layer, clamp01, composite, ease, ease_out, font

NAME = "v3_grid"
DURATION = 15.0
BGC = (29, 28, 27)
TW, TH = 340, 440
XS = [15, 370, 725]
YS = [32, 504, 976, 1448]
SLOTS = [(XS[i % 3], YS[i // 3]) for i in range(12)]
FLIP = 0.24
CELL = 10


def big_pack(name):
    g = C.pix(name, 105, 186)
    col, a = C.dotmatrix(np.ascontiguousarray(g), np.ones(g.shape[:2], np.float32), CELL,
                         dot=CELL - 2)
    bgc = np.array(BGC, np.float32) / 255
    return col * a[..., None] + bgc * (1 - a[..., None])


BIG = {"color": big_pack("color"), "dark": big_pack("dark")}

_cache = {}


def tile(spec):
    """Render a tile (TH, TW, 3) for a content spec, cached."""
    if spec in _cache:
        return _cache[spec]
    kind = spec[0]
    bgc = np.array(BGC, np.float32) / 255
    if kind == "puzzle":
        _, name, j = spec
        x, y = SLOTS[j]
        img = BIG[name][y - 32:y - 32 + TH, x - 15:x - 15 + TW].copy()
        if img.shape[0] < TH:
            pad = np.empty((TH, TW, 3), np.float32)
            pad[:] = bgc
            pad[:img.shape[0]] = img
            img = pad
    elif kind == "img":
        _, name, box = spec
        g = C.pix(name, TW // CELL, TH // CELL, box)
        col, a = C.dotmatrix(np.ascontiguousarray(g), np.ones(g.shape[:2], np.float32), CELL,
                             dot=CELL - 2)
        img = col * a[..., None] + bgc * (1 - a[..., None])
    elif kind == "solid":
        img = np.empty((TH, TW, 3), np.float32)
        img[:] = np.array(spec[1], np.float32) / 255
    elif kind == "text":
        _, lines, bcol, fcol, weight, italic = spec
        L = Layer()
        L.rect((0, 0, TW - 1, TH - 1), outline=None, fill=bcol)
        n = len(lines)
        for k, s in enumerate(lines):
            f = C.fit(s, TW - 60, weight=weight, start=110 if n == 1 else 84, italic=italic)
            y = TH / 2 + (k - (n - 1) / 2) * f.size * 1.05
            L.text((TW / 2, y), s, f, fill=fcol, anchor="mm")
        img = np.asarray(L.im.crop((0, 0, TW, TH))).astype(np.float32)[..., :3] / 255
    else:
        raise ValueError(kind)
    _cache[spec] = img
    return img


def T(lines, bcol, fcol=CREAM, weight=800, italic=False):
    return ("text", tuple(lines), bcol, fcol, weight, italic)


# ---------------------------------------------------------------------------
# Pages: (start time, specs[12], per-slot delays)
# ---------------------------------------------------------------------------
SHUFFLE = [7, 2, 10, 4, 11, 0, 9, 5, 1, 8, 3, 6]   # piece j starts in slot SHUFFLE[j]
SOLVE_T = 1.6
DIAG = [((i % 3) + (i // 3)) * 0.05 for i in range(12)]
SPIRAL_ORDER = [0, 1, 2, 5, 8, 11, 10, 9, 6, 3, 4, 7]
SPIRAL = [SPIRAL_ORDER.index(i) * 0.06 for i in range(12)]

P_SOLVED = [("puzzle", "color", j) for j in range(12)]
P_LOOK = list(P_SOLVED)
P_LOOK[3] = T(["A NEW"], WINE)
P_LOOK[4] = T(["LOOK"], ORANGE, WINE)
P_LOOK[5] = T(["IS", "COMING"], MAGENTA)

V_IMG = [("img", "dark", (0.0, 0.0, 0.55, 0.45)), T(["NEW", "VARIETIES"], BGC, INK, 300),
         ("img", "wc_cherries", (0.50, 0.60, 0.98, 0.86)), ("img", "color", (0.0, 0.55, 0.5, 1.0)),
         ("img", "color", (0.55, 0.55, 1.0, 1.0)), ("img", "dark", (0.45, 0.0, 1.0, 0.45)),
         ("img", "dark", (0.0, 0.5, 0.55, 1.0)), ("img", "wc_cherries", (0.0, 0.70, 0.45, 0.99)),
         ("img", "wc_cherries", (0.0, 0.10, 0.5, 0.55)), ("img", "color", (0.0, 0.0, 0.6, 0.5)),
         ("img", "dark", (0.45, 0.5, 1.0, 1.0)), T(["(coming", "soon)"], BGC, INK, 300, True)]
VAR_SLOTS = [3, 5, 7, 9]
VAR_T = [5.0, 5.5, 6.0, 6.5]
VAR_TILES = [T(["JAVA"], ORANGE, WINE), T(["CASTILLO"], MAGENTA),
             T(["GEISHA"], C.GEISHA_C, WINE), T(["BOURBON"], RED)]

P_ORIGIN = [("img", "wc_picker", (0.0, 0.10, 0.5, 0.5)), T(["ORIGIN"], BGC, INK, 300),
            ("img", "wc_picker", (0.5, 0.10, 1.0, 0.5)), ("img", "wc_cherries", (0.0, 0.0, 0.5, 0.5)),
            T(["HUILA"], ORANGE, WINE), ("img", "wc_mule_dog", (0.55, 0.35, 1.0, 0.7)),
            ("img", "wc_cherries", (0.5, 0.62, 1.0, 0.9)), T(["COLOMBIA"], BGC, INK, 300),
            ("img", "wc_cherries", (0.0, 0.72, 0.5, 1.0)), ("img", "color", (0.0, 0.1, 0.5, 0.45)),
            ("img", "wc_mule_dog", (0.62, 0.55, 1.0, 0.85)), ("img", "color", (0.5, 0.1, 1.0, 0.45))]

P_DARK = [("puzzle", "dark", j) for j in range(12)]
P_READY = list(P_DARK)
P_READY[7] = T(["ALMOST", "READY"], WINE)

P_WINE = [("solid", WINE)] * 12


def pages():
    out = [(0.0, [None] * 12, [0] * 12)]  # empty start
    out.append((0.15, [("puzzle", "color", j) for j in range(12)], [k * 0.1 for k in range(12)]))
    out.append((3.2, P_LOOK, [0, 0, 0, 0, 0.12, 0.24, 0, 0, 0, 0, 0, 0]))
    vp = list(V_IMG)
    out.append((4.4, vp, DIAG))
    for k, (s, t0) in enumerate(zip(VAR_SLOTS, VAR_T)):
        nxt = list(out[-1][1])
        nxt[s] = VAR_TILES[k]
        d = [99] * 12
        d[s] = 0
        out.append((t0, nxt, d))
    out.append((7.5, P_ORIGIN, DIAG))
    out.append((9.5, P_DARK, SPIRAL))
    out.append((11.0, P_READY, [99] * 7 + [0] + [99] * 4))
    out.append((12.2, P_WINE, DIAG))
    return out


PAGES = pages()
FLIP_TIMES = sorted({p[0] + d for p in PAGES[1:] for d in p[2] if d < 50})


def slot_state(s, t):
    """Return (prev_spec, cur_spec, flip_progress or None)."""
    prev, cur, start = None, None, -1
    for t0, specs, delays in PAGES:
        if delays[s] >= 50:
            continue
        ts = t0 + delays[s]
        if t >= ts:
            prev, cur, start = cur, specs[s], ts
    if t - start < FLIP:
        return prev, cur, (t - start) / FLIP
    return prev, cur, None


def draw_tile(img, spec, x, y, sx=1.0):
    if spec is None:
        return img
    tl = tile(spec)
    if sx < 0.999:
        w = max(1, int(TW * sx))
        tl = np.asarray(Image.fromarray(C.to_u8(tl)).resize((w, TH), Image.NEAREST)).astype(np.float32) / 255
        x = x + (TW - w) // 2
    img[y:y + TH, x:x + tl.shape[1]] = tl
    return img


def render_grid(img, t):
    for s, (x, y) in enumerate(SLOTS):
        prev, cur, p = slot_state(s, t)
        if p is None:
            img = draw_tile(img, cur, x, y)
        elif p < 0.5:
            img = draw_tile(img, prev, x, y, math.cos(p * math.pi))
        else:
            img = draw_tile(img, cur, x, y, -math.cos(p * math.pi))
    return img


def render_puzzle(img, t):
    """Pieces of the colourful pack start shuffled and slide into place."""
    order = sorted(range(12), key=lambda j: SHUFFLE[j])
    for j in order:
        appear = 0.15 + SHUFFLE[j] * 0.1
        if t < appear:
            continue
        p = (t - appear) / FLIP
        sx = ease(min(1.0, p)) if p < 1 else 1.0
        m = ease_out(clamp01((t - SOLVE_T - j * 0.07) / 0.55))
        x0, y0 = SLOTS[SHUFFLE[j]]
        x1, y1 = SLOTS[j]
        x, y = int(x0 + (x1 - x0) * m), int(y0 + (y1 - y0) * m)
        img = draw_tile(img, ("puzzle", "color", j), x, y, sx)
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(4000 + i)
    img = C.bg(BGC)
    if t < 3.2:
        img = render_puzzle(img, t)
    else:
        img = render_grid(img, t)
    L = Layer()
    if t >= 12.6:
        k = ease((t - 12.6) / 0.4)
        L.rect((0, 0, W, H), outline=None, fill=WINE, alpha=k)
        img = L.apply(img)
        L = Layer()
        lg_w = 400
        la = C.logo_alpha(lg_w)
        kk = ease((t - 12.8) / 0.4)
        if kk > 0:
            s = np.ones(la.shape + (3,), np.float32) * np.array(CREAM, np.float32) / 255
            composite(img, s, la * kk, ((W - lg_w) // 2, 460 + int((1 - kk) * 30)))
        C.fade_text(L, t, 13.1, "GREEN COFFEE", font(800, 80), (W // 2, 1140), anchor="ms",
                    color=CREAM)
        C.fade_text(L, t, 13.25, "FROM HUILA, COLOMBIA", font(600, 24), (W // 2, 1200),
                    anchor="ms", color=CREAM, tracking=10)
        C.fade_text(L, t, 13.45, "COMING SOON", font(800, 58), (W // 2, 1330), anchor="ms",
                    color=ORANGE)
        C.fade_text(L, t, 13.6, "@JUANITOCOFFEE", font(700, 32), (W // 2, 1410), anchor="ms",
                    color=CREAM, tracking=8)
        img = L.apply(img)
    img = C.grain(img, rng, 0.04)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=3)
    prog = ["Am7", "Fmaj7", "Cmaj7", "G6"]
    bars = [(2.0 * k, prog[k % 4]) for k in range(8)]
    for t0, ch in bars:
        end = min(t0 + 2.0, DURATION)
        tr.pad(CHORDS[ch], t0, end, gain=0.065, cutoff=1100)
        if 3.0 <= t0 < 12.0:
            tr.arp(ch, t0, end, step=0.25, gain=0.035)
    for k in range(int(1.5 / BEAT), int(12.5 / BEAT)):
        tt = k * BEAT
        tr.kick(tt, 0.8)
        if k % 2 == 1:
            tr.snare(tt, 0.26)
        tr.hat(tt + BEAT / 2 + 0.01, 0.06)
        tr.hat(tt + BEAT / 4, 0.03)
    for t0, ch in bars:
        if 1.5 <= t0 < 12.5 or t0 == 0.0:
            r = ROOT[ch]
            for off, dur in ((0, 0.4), (0.75, 0.2), (1.0, 0.4), (1.5, 0.4)):
                if 1.5 <= t0 + off < 12.5:
                    tr.bass(r, t0 + off, dur, 0.28)
    for ft in FLIP_TIMES:
        tr.tick(ft, 0.06)
    for j in range(12):
        tr.thud(SOLVE_T + j * 0.07 + 0.55, 0.06, f=600 + 40 * j)
    for k, t0 in enumerate(VAR_T):
        tr.chip([81, 84, 88, 86][k], t0, 0.3, 0.07, duty=0.125)
    tr.riser(11.6, 12.55, 0.07)
    tr.impact(12.6, 0.5)
    tr.bass(ROOT["Am7"], 12.6, 2.2, 0.26)
    tr.arp("Am7", 12.7, 14.6, step=0.25, gain=0.03, kind="bell")
    return tr.write(path)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
