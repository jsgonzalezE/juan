"""R2 — reference style with the five real pouches (four watercolours + colourful) as 3D dot objects."""
import math

import numpy as np
from PIL import Image

import common as C
import minimal as M
import refstyle as R
from audio import CHORDS, ROOT, Track
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, ease, font
from r1_reference import HUD_RGB, HUD_A, blotches, hud, ticker

NAME = "r2_pouches"
DURATION = 17.0
POUCHES = ["cherries", "picker", "color", "mule", "dog"]
for _k in POUCHES:
    C.IMAGES["pouch_" + _k] = Image.open(f"{C.HERE}/assets/pouch_{_k}.png").convert("RGB")

VAR = [("JAVA", 8.6, (80, 520), "la"), ("CASTILLO", 9.3, (1000, 700), "ra"),
       ("GEISHA", 10.0, (80, 1350), "la"), ("BOURBON", 10.7, (1000, 1530), "ra")]
FLASH_T0, FLASH_DT = 11.6, 0.4
FLASH = ["dog", "color", "picker", "cherries", "mule"]
LOGO_W = 230
LOGO_A = C.logo_alpha(LOGO_W)


def pouch_dots(img, key, ang, cx, cy, scale, rows=240, cols=168, cell=5, reveal=1.0, nu=320,
               nv=520, color=R.DOT_ORANGE):
    enh = 0.0 if key == "color" else 2.0
    lum, mask = R.pouch("pouch_" + key, ang, rows, cols, scale, tilt=0.1, corner=0.07,
                        enhance=enh, nu=nu, nv=nv)
    if reveal < 1:
        mask = mask * (np.random.default_rng(int(reveal * 40)).random(mask.shape) < reveal)
    return R.dots(img, lum, mask, cx - cols * cell / 2, cy - rows * cell / 2, color, cell=cell,
                  dot=cell - 1)


# grey foliage from the cherry watercolour (leaves), like the reference's dithered leaves
_wc = np.asarray(C.IMAGES["wc_cherries"]).astype(np.float32) / 255


def foliage(t, rows=330, cols=185):
    ih, iw = _wc.shape[:2]
    zoom = 1.05 + 0.05 * (t - 5.0)
    ch = ih * 0.5 / zoom
    cw = ch * cols / rows
    cx, cy = iw * 0.5, ih * 0.74 - 20 * (t - 5.0)
    cy = min(max(cy, ch / 2), ih - ch / 2)
    cx = min(max(cx, cw / 2), iw - cw / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    g = np.asarray(C.IMAGES["wc_cherries"].resize((cols, rows), Image.BOX, box=box))
    g = g.astype(np.float32) / 255
    lum = C.luminance(g)
    lo, hi = np.percentile(lum, (5, 98))
    lum = np.clip((lum - lo) / (hi - lo), 0, 1)
    lum = 1 / (1 + np.exp(-(lum - 0.66) * 10))
    return lum * 0.38


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(11000 + i)
    img = C.bg(R.BGC)
    L = Layer()
    hud_a = 0.0
    if t < 0.5:
        img = R.tear(R.static(rng), rng, 5, 60)
    elif t < 3.0:  # cherry watercolour pouch, turning
        img = pouch_dots(img, "cherries", -0.5 + 0.38 * (t - 0.5), 540, 900, 100,
                         reveal=min(1, (t - 0.5) / 0.3))
        if t > 1.0:
            M.mixed_line(L, [("(origin", font(300, 48, True), 0, INK),
                             ("HUILA", font(500, 24), 6, INK),
                             ("COLOMBIA", font(500, 24), 6, INK),
                             (")", font(300, 48, True), 0, INK)], W // 2, 1600,
                         ease((t - 1.0) / 0.4))
        hud_a = ease((t - 0.55) / 0.3)
    elif t < 4.6:
        items = ["HUILA,", "02°32′ N", "75°31′ W"]
        k = min(2, int((t - 3.0) / 0.53))
        L.text((W // 2, 960), items[k], font(500, 40), anchor="mm", tracking=4)
    elif t < 5.0:
        L.text((W // 2, 960), "FROM OUR LAND", font(500, 30), anchor="mm", tracking=6)
    elif t < 7.8:
        g = foliage(t)
        img = R.dots(img, g, (g > 0.04).astype(np.float32), 0, 0, R.DOT_GREY,
                     alpha=0.9 * ease((t - 5.0) / 0.3))
        C.fade_text(L, t, 5.2, "(grown with", font(300, 64, True), (100, 880), dur=0.3)
        C.fade_text(L, t, 5.35, "LOVE", font(300, 230), (80, 1110), anchor="ls", tracking=14,
                    dur=0.3)
        C.fade_text(L, t, 5.7, "& respect for the land)", font(300, 52, True), (1000, 1200),
                    anchor="ra", dur=0.3)
        for k, s in enumerate(["EVERY BEAN THAT REACHES", "YOUR CUP", "TELLS OUR STORY"]):
            C.fade_text(L, t, 6.1 + 0.25 * k, s, font(500, 26), (W // 2, 1320 + 72 * k),
                        anchor="ms", tracking=5, dur=0.3)
        hud_a = 1.0
    elif t < 8.1:
        g = blotches(rng)
        img = R.dots(img, g, (g > 0.02).astype(np.float32), 0, 0, R.DOT_ORANGE)
        hud_a = 1.0
    elif t < FLASH_T0:  # mule pouch with the varieties around it
        img = pouch_dots(img, "mule", 0.55 - 0.34 * (t - 8.1), 540, 1020, 86,
                         reveal=min(1, (t - 8.1) / 0.3))
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
    elif t < FLASH_T0 + FLASH_DT * len(FLASH):  # quick cuts through the five pouches
        k = int((t - FLASH_T0) / FLASH_DT)
        lt = t - FLASH_T0 - k * FLASH_DT
        img = pouch_dots(img, FLASH[k], (-0.35 + 0.7 * lt / FLASH_DT) * (1 if k % 2 else -1),
                         540, 860, 82)
        L.text((W // 2, 1580), f"0{k + 1} / 05", font(500, 20), anchor="ms", tracking=6,
               fill=ORANGE)
        C.fade_text(L, t, FLASH_T0 + 0.4, "A NEW LOOK", font(300, 104), (W // 2, 1700),
                    anchor="ms", tracking=8, dur=0.3)
        hud_a = 1.0
    else:  # end card: the five pouches in a row
        lt = t - (FLASH_T0 + FLASH_DT * len(FLASH))
        for k, key in enumerate(["cherries", "picker", "color", "mule", "dog"]):
            cx = 140 + k * 200
            p = ease((lt - k * 0.08) / 0.35)
            if p > 0:
                img = pouch_dots(img, key, 0.35 * math.sin(lt * 1.2 + k * 0.6), cx, 580, 29,
                                 rows=76, cols=46, cell=5, reveal=p, nu=160, nv=260)
        k = ease((lt - 0.3) / 0.4)
        s = np.empty(LOGO_A.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, LOGO_A * k, ((W - LOGO_W) // 2, 920))
        st = FLASH_T0 + FLASH_DT * len(FLASH)
        C.fade_text(L, t, st + 0.5, "(green coffee from", font(300, 40, True), (W // 2, 1300),
                    anchor="ms", dur=0.3)
        C.fade_text(L, t, st + 0.5, "HUILA)", font(500, 22), (W // 2, 1350), anchor="ms",
                    tracking=8, dur=0.3)
        C.fade_text(L, t, st + 0.7, "(coming soon)", font(300, 34, True), (W // 2, 1430),
                    anchor="ms", dur=0.3)
        C.fade_text(L, t, st + 0.8, "@JUANITOCOFFEE", font(500, 20), (70, 1700), tracking=4,
                    dur=0.3)
        C.fade_text(L, t, st + 0.8, "HUILA · COLOMBIA", font(500, 20), (1010, 1700), anchor="ra",
                    tracking=4, dur=0.3)
        for y in (30, 72, 1848, 1890):
            L.line([(0, y), (W, y)], width=1, alpha=0.6)
        ticker(L, 51, lt * 80)
        ticker(L, 1869, -lt * 80 + 300)
    img = hud(img, hud_a)
    img = L.apply(img)
    if t >= 0.5 and rng.random() < 0.25:
        img = R.tear(img, rng, 2, 30)
    img = C.grain(img, rng, 0.05)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    from audio import SR, filt
    tr = Track(DURATION, seed=41)
    tr.vinyl(0.014)
    n = int(0.5 * SR)
    tr.add(filt(tr.rng.standard_normal(n), "bandpass", [600, 8000]) * np.linspace(1, 0.6, n), 0.0,
           0.10)
    prog = ["Dm9", "Am7", "Fmaj7", "Em7"]
    for k in range(9):
        t0 = 0.5 + 2.0 * k
        if t0 >= DURATION:
            break
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.075, cutoff=700)
    for k in range(1, 17):
        tt = 0.5 + k * 1.0
        if tt > 16.0:
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
    for k in range(len(FLASH)):
        tr.tick(FLASH_T0 + k * FLASH_DT, 0.09)
        tr.chip([76, 79, 81, 84, 88][k], FLASH_T0 + k * FLASH_DT, 0.12, 0.04, duty=0.125)
    end = FLASH_T0 + FLASH_DT * len(FLASH)
    tr.bell(76, end, 0.1)
    tr.bell(88, end + 0.5, 0.07, pan=0.3)
    return tr.write(path, fade=0.6)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
