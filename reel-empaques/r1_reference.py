"""R1 — reference style: fine error-diffusion dots, the packs as lit 3D pouches, thin type."""
import math

import numpy as np
from PIL import Image

import common as C
import minimal as M
import refstyle as R
from audio import CHORDS, ROOT, Track
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, dotmatrix, ease, font

NAME = "r1_reference"
DURATION = 15.0
VAR = [("JAVA", 8.6, (80, 520), "la"), ("CASTILLO", 9.3, (1000, 700), "ra"),
       ("GEISHA", 10.0, (80, 1330), "la"), ("BOURBON", 10.7, (1000, 1510), "ra")]
TICKER = "JAVA  •  CASTILLO  •  GEISHA  •  BOURBON  •  HUILA  •  GREEN COFFEE  •  "
LOGO_W = 250
LOGO_A = C.logo_alpha(LOGO_W)


# ---------------------------------------------------------------------------
def build_hud():
    L = Layer()
    f6, f4 = font(600, 22), font(500, 20)
    L.text((70, 112), "JUANITO COFFEE", f6, tracking=3)
    L.text((600, 104), "NEW HARVEST", f4, tracking=3)
    L.text((1004, 104), "2026", f4, tracking=3, anchor="ra")
    L.rect((600, 132, 1004, 168), width=2)
    L.text((614, 140), "ORIGIN", f4, tracking=3)
    L.text((990, 140), "HUILA", f6, tracking=3, anchor="ra")
    for k in range(41):
        x = 600 + k * 10
        L.line([(x, 176), (x, 176 + (10 if k % 5 == 0 else 5))], width=1, alpha=0.7)
    L.text((70, 1770), "LAT 2.5359 N", f4, tracking=3)
    L.text((70, 1810), "LON 75.5277 W", f4, tracking=3)
    for k in range(13):
        x = 846 + k * 12
        L.line([(x, 1712), (x + 12, 1688)], width=2)
    L.text((1004, 1770), "GREEN COFFEE", f4, tracking=3, anchor="ra")
    L.text((1004, 1810), "© 2026", f4, tracking=3, anchor="ra")
    side = Layer()
    side.text((W // 2, 20), "2.5359° N  —  75.5277° W  —  HUILA, COLOMBIA", font(500, 18),
              tracking=4, anchor="mt")
    strip = side.im.crop((0, 0, W, 50)).rotate(-90, expand=True)
    L.im.alpha_composite(strip, (W - 46, (H - strip.height) // 2))
    a = np.asarray(L.im).astype(np.float32) / 255
    return a[..., :3].copy(), a[..., 3].copy()


HUD_RGB, HUD_A = build_hud()


def hud(img, alpha=1.0):
    if alpha <= 0:
        return img
    a = HUD_A[..., None] * alpha
    return img * (1 - a) + HUD_RGB * a


# grey illustration field (from the dark pack art), like dithered foliage
_dark = np.asarray(C.PACK_DARK.convert("L")).astype(np.float32) / 255


def field(t, rows=330, cols=185):
    """Grey dithered foliage taken from the lower half of the dark pack art (no logo)."""
    zoom = 2.25 + 0.06 * (t - 5.0)
    ih, iw = _dark.shape
    ch = ih / zoom
    cw = ch * cols / rows
    cx, cy = iw * 0.5, ih * (0.74 - 0.015 * (t - 5.0))
    cy = min(max(cy, ch / 2), ih - ch / 2)
    cx = min(max(cx, cw / 2), iw - cw / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    g = np.asarray(Image.fromarray((_dark * 255).astype(np.uint8)).resize((cols, rows), Image.BOX,
                                                                           box=box))
    g = g.astype(np.float32) / 255
    return np.clip((g - 0.22) / 0.75, 0, 1) * 0.62


def blotches(rng):
    g = rng.random((12, 7)).astype(np.float32)
    g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((180, 320), Image.BICUBIC))
    g = np.clip((g.astype(np.float32) / 255 - 0.45) * 2.2, 0, 1)
    return g


def pack_at(img, name, ang, cx, cy, scale, color, rows=200, cols=150, reveal=1.0, rng=None,
            tilt=0.12):
    lum, mask = R.pouch(name, ang, rows, cols, scale, tilt=tilt)
    if reveal < 1 and rng is not None:
        mask = mask * (np.random.default_rng(int(reveal * 50)).random(mask.shape) < reveal)
    return R.dots(img, lum, mask, cx - cols * 3, cy - rows * 3, color)


def ticker(L, y, offset):
    f = font(500, 18)
    tw = sum(f.getlength(c) + 3 for c in TICKER)
    x = -(offset % tw)
    while x < W:
        L.text((x, y), TICKER, f, tracking=3, anchor="lm")
        x += tw


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(10000 + i)
    img = C.bg(R.BGC)
    L = Layer()
    hud_a = 0.0
    if t < 0.5:
        img = R.static(rng)
        img = R.tear(img, rng, 5, 60)
    elif t < 3.0:  # the colourful pack, turning
        ang = -0.55 + 0.42 * (t - 0.5)
        img = pack_at(img, "color", ang, 540, 900, 85, R.DOT_ORANGE, reveal=min(1, (t - 0.5) / 0.3),
                      rng=rng)
        if t > 1.0:
            a = ease((t - 1.0) / 0.4)
            M.mixed_line(L, [("(origin", font(300, 48, True), 0, INK),
                             ("HUILA", font(500, 24), 6, INK),
                             ("COLOMBIA", font(500, 24), 6, INK),
                             (")", font(300, 48, True), 0, INK)], W // 2, 1590, a)
        hud_a = ease((t - 0.55) / 0.3)
    elif t < 4.6:  # coordinates
        items = ["HUILA,", "02°32′ N", "75°31′ W"]
        k = min(2, int((t - 3.0) / 0.53))
        L.text((W // 2, 960), items[k], font(500, 40), anchor="mm", tracking=4)
    elif t < 5.0:
        L.text((W // 2, 960), "FROM OUR LAND", font(500, 30), anchor="mm", tracking=6)
    elif t < 7.8:  # dithered illustration field + brand line
        g = field(t)
        on_a = ease((t - 5.0) / 0.3)
        img = R.dots(img, g, (g > 0.05).astype(np.float32), 0, 0, R.DOT_GREY, alpha=0.9 * on_a)
        C.fade_text(L, t, 5.2, "(grown with", font(300, 64, True), (100, 880), dur=0.3)
        C.fade_text(L, t, 5.35, "LOVE", font(300, 230), (80, 1110), anchor="ls", tracking=14,
                    dur=0.3)
        C.fade_text(L, t, 5.7, "& respect for the land)", font(300, 52, True), (1000, 1200),
                    anchor="ra", dur=0.3)
        for k, s in enumerate(["EVERY BEAN THAT REACHES", "YOUR CUP", "TELLS OUR STORY"]):
            C.fade_text(L, t, 6.1 + 0.25 * k, s, font(500, 26), (W // 2, 1320 + 72 * k),
                        anchor="ms", tracking=5, dur=0.3)
        hud_a = 1.0
    elif t < 8.1:  # orange blotches
        g = blotches(rng)
        img = R.dots(img, g, (g > 0.02).astype(np.float32), 0, 0, R.DOT_ORANGE)
        hud_a = 1.0
    elif t < 11.6:  # the dark pack, varieties around it
        ang = 0.6 - 0.38 * (t - 8.1)
        img = pack_at(img, "dark", ang, 540, 1010, 74, R.DOT_GREY, reveal=min(1, (t - 8.1) / 0.3),
                      rng=rng)
        C.fade_text(L, t, 8.3, "(new varieties)", font(300, 46, True), (1000, 380), anchor="ra",
                    dur=0.3)
        for k, (name, t0, xy, anc) in enumerate(VAR):
            if t >= t0:
                L.text(xy, name, font(300, 104), anchor=anc[0] + "s", tracking=6)
                tag_x = xy[0] if anc[0] == "l" else xy[0] - 46
                L.rect((tag_x, xy[1] - 150, tag_x + 46, xy[1] - 118), outline=ORANGE, width=2)
                L.text((tag_x + 23, xy[1] - 134), f"0{k + 1}", font(600, 16), fill=ORANGE,
                       anchor="mm")
        hud_a = 1.0
    elif t < 13.2:  # statement over grey noise
        n = rng.random((320, 180)).astype(np.float32) * 0.42
        img = R.dots(img, n, np.ones_like(n), 0, 0, (120, 120, 118), alpha=0.8)
        a = ease((t - 11.8) / 0.3)
        if t > 11.8:
            M.mixed_line(L, [("for a", font(300, 30, True), 0, INK),
                             ("NEW", font(600, 24), 4, INK),
                             ("harvest", font(300, 30, True), 0, INK)], W // 2, 870, a)
        C.fade_text(L, t, 12.0, "A NEW LOOK", font(300, 128), (W // 2, 1030), anchor="ms",
                    tracking=8, dur=0.3)
        C.fade_text(L, t, 12.35, "(coming soon)", font(300, 50, True), (W // 2, 1120), anchor="ms",
                    dur=0.3)
        hud_a = 1.0
    else:  # end card
        lt = t - 13.2
        img = pack_at(img, "color", -0.35 + 0.3 * lt, 330, 640, 42, R.DOT_ORANGE, rows=110,
                      cols=90)
        img = pack_at(img, "dark", 0.35 - 0.3 * lt, 750, 640, 42, R.DOT_GREY, rows=110, cols=90)
        k = ease(lt / 0.4)
        s = np.empty(LOGO_A.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, LOGO_A * k, ((W - LOGO_W) // 2, 1010))
        C.fade_text(L, t, 13.5, "(green coffee from", font(300, 40, True), (W // 2, 1400),
                    anchor="ms", dur=0.3)
        C.fade_text(L, t, 13.5, "HUILA)", font(500, 22), (W // 2, 1450), anchor="ms", tracking=8,
                    dur=0.3)
        C.fade_text(L, t, 13.8, "@JUANITOCOFFEE", font(500, 20), (70, 1700), tracking=4, dur=0.3)
        C.fade_text(L, t, 13.8, "HUILA · COLOMBIA", font(500, 20), (1010, 1700), anchor="ra",
                    tracking=4, dur=0.3)
        for y in (30, 72, 1848, 1890):
            L.line([(0, y), (W, y)], width=1, alpha=0.6)
        ticker(L, 51, lt * 80)
        ticker(L, 1869, -lt * 80 + 300)
    img = hud(img, hud_a)
    img = L.apply(img)
    if 0.5 <= t and rng.random() < 0.25:
        img = R.tear(img, rng, 2, 30)
    img = C.grain(img, rng, 0.05)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=31)
    tr.vinyl(0.014)
    from audio import filt, SR
    n = int(0.5 * SR)
    tr.add(filt(tr.rng.standard_normal(n), "bandpass", [600, 8000]) * np.linspace(1, 0.6, n), 0.0,
           0.10)
    prog = ["Dm9", "Am7", "Fmaj7", "Em7"]
    for k in range(8):
        t0 = 0.5 + 2.0 * k
        if t0 >= DURATION:
            break
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.075, cutoff=700)
    for k in range(1, 15):
        tt = 0.5 + k * 1.0
        if tt > 14.2:
            break
        tr.kick(tt, 0.38)
        tr.hat(tt + 0.5, 0.03)
    for t0 in (0.5, 4.5, 8.5, 12.5):
        tr.bass(ROOT[prog[int((t0 - 0.5) // 2) % 4]], t0, 1.9, 0.18)
    for k, t0 in enumerate((3.0, 3.53, 4.06)):
        for j in range(6):
            tr.tick(t0 + j * 0.03, 0.05)
        tr.chip([81, 84, 88][k], t0 + 0.2, 0.18, 0.04, duty=0.125)
    tr.bell(76, 4.6, 0.07)
    tr.bell(84, 5.35, 0.08)
    n2 = int(0.3 * SR)
    tr.add(filt(tr.rng.standard_normal(n2), "bandpass", [500, 6000]) * 0.8, 7.8, 0.08)
    for k, (_, t0, _, _) in enumerate(VAR):
        tr.bell([81, 84, 88, 86][k], t0, 0.09, pan=[-0.3, 0.3, -0.3, 0.3][k])
    tr.riser(10.9, 11.6, 0.05)
    tr.bell(76, 12.0, 0.1)
    tr.bell(88, 13.2, 0.08, pan=0.3)
    tr.bell(81, 13.5, 0.06, pan=-0.3)
    return tr.write(path, fade=0.6)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
