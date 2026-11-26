"""N2 — HORIZONS: each pack becomes a pixel-art planet; a tiny Noah walks over its horizon."""
import math

import numpy as np
from PIL import Image

import common as C
import noah as N
from audio import CHORDS, ROOT, SR, Track, filt
from fx import INK, ORANGE, H, W, Layer, bayer, clamp01, composite, dotmatrix, ease, font

NAME = "n2_horizons"
DURATION = 17.0
CELL = 6
GR, GC = H // CELL, W // CELL          # 320 x 180 grid
CX = GC / 2
R = 640.0                               # planet radius in cells
CREST = 178                             # crest row of the horizon

# scene: (start, end, kind, pack, sky top, sky bottom)
SCENES = [
    (0.0, 2.6, "pack", "color", (226, 196, 170), (244, 206, 160)),
    (2.6, 4.7, "pack", "cherries", (150, 172, 190), (226, 228, 222)),
    (4.7, 6.8, "cup", None, (236, 226, 186), (240, 232, 198)),
    (6.8, 8.8, "pack", "mule", (120, 150, 176), (214, 222, 220)),
    (8.8, 10.8, "pack", "dog", (96, 104, 116), (200, 200, 196)),
    (10.8, 13.6, "night", "color", (6, 8, 16), (30, 26, 48)),
    (13.6, 17.0, "pack", "color", (226, 196, 170), (244, 206, 160)),
]
VAR_T = [11.2, 11.8, 12.4, 13.0]


def make_tex(key, wt=300, ht=150, ncolors=26):
    im = Image.open(f"{C.HERE}/assets/pouch_{key}.png").convert("RGB")
    w, h = im.size
    im = im.crop((int(w * 0.07), int(h * 0.14), int(w * 0.93), int(h * 0.95)))
    from PIL import ImageEnhance
    im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.15)).enhance(1.3)
    sm = im.resize((wt // 2, ht), Image.BOX)
    sm = sm.quantize(colors=ncolors, method=Image.Quantize.MEDIANCUT,
                     dither=Image.Dither.NONE).convert("RGB")
    a = np.asarray(sm).astype(np.float32) / 255
    return a


TEX = {k: make_tex(k) for k in ("color", "cherries", "mule", "dog")}

_yy, _xx = np.mgrid[0:GR, 0:GC].astype(np.float32)


def planet_geom(cy):
    dx = _xx + 0.5 - CX
    dy = cy - (_yy + 0.5)
    r = np.sqrt(dx * dx + dy * dy)
    theta = np.arctan2(dx, dy)
    depth = R - r
    return theta, depth


def surface_row(x, cy):
    return cy - math.sqrt(max(0.0, R * R - (x - CX) ** 2))


def sky(top, bot, glow=None):
    tcol = np.array(top, np.float32) / 255
    bcol = np.array(bot, np.float32) / 255
    g = np.clip(_yy / CREST, 0, 1) ** 1.6
    levels = 7
    q = np.floor(g * levels + bayer(GR, GC) - 0.5).clip(0, levels) / levels
    return tcol + (bcol - tcol) * q[..., None]


def render_planet(t, sc, drift):
    start, end, kind, key, top, bot = sc
    cy = CREST + R - drift
    theta, depth = planet_geom(cy)
    img = sky(top, bot)
    below = depth >= 0
    if kind == "cup":
        coffee = np.array((40, 24, 16), np.float32) / 255
        crema = np.array((176, 108, 58), np.float32) / 255
        img[below] = coffee * (0.7 + 0.3 * np.clip(1 - depth[below] / 50, 0, 1))[:, None]
        rim = below & (depth < 2.2)
        img[rim] = crema
        return img
    tex = TEX[key]
    ht, wt = tex.shape[:2]
    s = theta * R
    u = np.clip(s * 0.72 + wt / 2 + (t - start) * 3 - 4, 0, wt - 1).astype(int)
    v = (np.clip(depth / 150, 0, 1) ** 0.82 * (ht - 1)).astype(int)
    col = tex[v, u]
    shade = 0.82 + 0.18 * np.clip(depth / 12, 0, 1)        # darker right at the rim
    col = col * shade[..., None]
    if kind == "night":
        col = col * 0.45 + np.array((0.02, 0.02, 0.06)) * 0.55
    img[below] = col[below]
    # bright atmosphere line just above the surface
    atm = (~below) & (depth > -1.6)
    bc = np.array(bot, np.float32) / 255
    img[atm] = np.clip(bc * 1.08 + 0.06, 0, 1) if kind != "night" else np.array((0.75, 0.62, 0.9))
    return img


STARS = np.random.default_rng(4).random((GR, GC)) > 0.996
NOAH_SIL = N.sprite("bow", 36)
NOAH_PEEK = N.sprite("peek", 44)
LOGO = C.LOGO.convert("RGBA")
_la = np.asarray(LOGO)[..., 3]
_cup_rows = int(_la.shape[0] * 0.56)
ICON = Image.fromarray(_la[:_cup_rows]).resize((86, round(86 * _cup_rows / _la.shape[1])),
                                               Image.LANCZOS)
ICON_A = np.asarray(ICON).astype(np.float32) / 255


def silhouette(spr, color):
    out = np.zeros_like(spr)
    out[..., :3] = np.array(color, np.float32) / 255
    out[..., 3] = spr[..., 3]
    return out


SIL_DARK = silhouette(NOAH_SIL, (26, 22, 20))
SIL_LIGHT = silhouette(NOAH_SIL, (236, 228, 214))


def grid_blit(img, spr, gx, gy_bottom, flip=False):
    """Blit a sprite into the cell grid (one sprite pixel = one cell)."""
    s = spr[:, ::-1] if flip else spr
    h, w = s.shape[:2]
    x0, y0 = int(round(gx - w / 2)), int(round(gy_bottom - h))
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(GC, x0 + w), min(GR, y0 + h)
    if xb <= xa or yb <= ya:
        return img
    a = s[ya - y0:yb - y0, xa - x0:xb - x0, 3:4]
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + s[ya - y0:yb - y0, xa - x0:xb - x0, :3] * a
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(13000 + i)
    sc = [s for s in SCENES if s[0] <= t < s[1]]
    sc = sc[0] if sc else SCENES[-1]
    start, end, kind, key, top, bot = sc
    lt = t - start
    drift = 3.0 * lt
    if kind == "night":
        drift = -2 + 2.2 * lt
    g = render_planet(t, sc, drift)
    cy = CREST + R - drift
    if kind == "night":
        tw = STARS & (rng.random((GR, GC)) > 0.15) & (_yy < CREST - 4)
        g[tw] = np.array((0.9, 0.88, 0.95))
    # tiny Noah walking over the horizon
    if kind in ("pack", "night"):
        speed = 9.0
        gx = GC * 0.78 - speed * lt
        bounce = abs(math.sin(lt * 7.5)) * 1.6
        gy = surface_row(gx, cy) - bounce + 0.6
        spr = SIL_LIGHT if kind == "night" else SIL_DARK
        if start >= 13.6:   # walks in from the right and stops beside the title
            gx = max(CX + 66, GC + 20 - speed * 1.6 * lt)
            if gx <= CX + 66:
                bounce = abs(math.sin(lt * 3.0)) * 0.8
            gy = surface_row(gx, cy) - bounce + 0.6
        g = grid_blit(g, spr, gx, gy)
    if kind == "cup":   # Noah peeks over the rim of the cup
        rise = ease((lt - 0.3) / 0.8) * 0.62
        h = NOAH_PEEK.shape[0]
        tmp = grid_blit(g.copy(), NOAH_PEEK, CX + 6, CREST + h * (1 - rise) + 2)
        theta, depth = planet_geom(cy)
        below = depth >= 0
        tmp[below] = g[below]
        g = tmp
    img = np.repeat(np.repeat(g, CELL, 0), CELL, 1)[:H, :W].astype(np.float32)
    L = Layer()
    hy = (CREST - drift) * CELL   # horizon y in pixels at the centre
    white = (250, 246, 238)
    if kind == "pack" and start == 0.0:
        C.fade_text(L, t, 0.8, "(new harvest)", font(300, 40, True), (W // 2, hy - 300),
                    anchor="ms", color=(90, 60, 50), end=2.55)
    if kind == "pack" and key == "cherries":
        C.fade_text(L, t, 3.0, "HUILA, COLOMBIA", font(500, 30), (W // 2, hy - 300),
                    anchor="ms", tracking=12, color=(40, 50, 60), end=4.65)
    if kind == "cup":
        C.fade_text(L, t, 5.4, "(a new look)", font(300, 40, True), (W // 2, hy - 300),
                    anchor="ms", color=(70, 45, 30), end=6.75)
    if kind == "night":
        for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, VAR_T)):
            if t >= t0:
                a = ease((t - t0) / 0.3) * clamp01((13.55 - t) / 0.25)
                L.text((W // 2, hy - 520 + k * 80), name, font(300, 52), anchor="ms",
                       tracking=18, fill=white, alpha=a)
        C.fade_text(L, t, 11.0, "(new varieties)", font(300, 34, True), (W // 2, hy - 640),
                    anchor="ms", color=(200, 190, 220), end=13.55)
    if kind == "pack" and start >= 13.6:
        ka = ease((lt - 0.2) / 0.5) * (1 - ease((lt - 1.4) / 0.3))
        if ka > 0:
            L.text((W // 2, hy - 28), "New Harvest", font(400, 64), anchor="ms",
                   fill=(255, 250, 244), alpha=ka)
        kb = ease((lt - 1.75) / 0.5)
        if kb > 0:
            f = font(500, 64)
            tw = f.getlength("Juanito Coffee")
            iw = ICON_A.shape[1]
            x0 = W / 2 - (tw + iw + 22) / 2
            s = np.empty(ICON_A.shape + (3,), np.float32)
            s[:] = 1.0
            composite(img, s, ICON_A * kb, (int(x0), int(hy - 28 - ICON_A.shape[0] + 8)))
            L.text((x0 + iw + 22, hy - 28), "Juanito Coffee", f, anchor="ls",
                   fill=(255, 250, 244), alpha=kb)
        C.fade_text(L, t, 15.4, "GREEN COFFEE  ·  COMING SOON", font(600, 24),
                    (W // 2, hy - 330), anchor="ms", tracking=8, color=(96, 52, 44))
        C.fade_text(L, t, 15.6, "@JUANITOCOFFEE", font(600, 24), (W // 2, hy - 280),
                    anchor="ms", tracking=8, color=(96, 52, 44))
    img = L.apply(img)
    img = C.grain(img, rng, 0.03)
    # quick dip to black at each cut, like straight cuts in a film
    for s_ in SCENES[1:]:
        d = t - s_[0]
        if -0.04 <= d < 0.06:
            img *= 0.15
    if t < 0.5:
        img *= ease(t / 0.5)
    if t > DURATION - 0.6:
        img *= ease((DURATION - t) / 0.6)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=61)
    tr.vinyl(0.008)
    prog = ["Fmaj7", "Am7", "Cmaj7", "G6", "Fmaj7", "Am7", "Dm9", "Cmaj7", "Fmaj7"]
    for k, ch in enumerate(prog):
        t0 = 2.0 * k
        if t0 >= DURATION:
            break
        tr.pad(CHORDS[ch], t0, min(t0 + 2.0, DURATION - 0.2), gain=0.085, cutoff=900)
        tr.bass(ROOT[ch], t0, 1.9, 0.14)
    # gentle pulse, a bell on every cut
    for k in range(1, 33):
        tt = k * 0.5
        if tt < 13.6:
            tr.tick(tt, 0.02)
    notes = [81, 84, 79, 88, 76, 83, 86]
    for k, sc in enumerate(SCENES):
        tr.bell(notes[k % len(notes)], sc[0] + 0.02, 0.08, pan=[-0.3, 0.3][k % 2])
    for k, t0 in enumerate(VAR_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.07, pan=[-0.3, 0.3, -0.3, 0.3][k])
    # tiny footsteps for Noah
    for sc in SCENES:
        if sc[2] in ("pack", "night"):
            n_steps = int((sc[1] - sc[0]) / (math.pi / 7.5))
            for j in range(n_steps):
                tt = sc[0] + j * math.pi / 7.5
                if sc[0] >= 13.6 and tt - sc[0] > 1.15:
                    break
                tr.chip(96, tt, 0.025, 0.012, duty=0.5)
    tr.riser(12.6, 13.6, 0.05)
    tr.impact(13.6, 0.3)
    tr.bell(76, 15.35, 0.1)
    tr.bell(88, 15.4, 0.07, pan=0.3)
    return tr.write(path, fade=0.9)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
