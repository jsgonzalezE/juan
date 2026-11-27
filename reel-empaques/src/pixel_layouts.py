"""Opciones de organizacion de la escena de la taza: la misma parada (Java) armada de cinco maneras.

Uso: python3 src/pixel_layouts.py -> storyboards/opciones_taza.jpg + storyboards/frames/h_0N.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P = 180, 320, 6
GLOW = (246, 228, 196)
C1, C2 = (40, 84, 40), (132, 170, 60)                 # verde de Java
COFFEE, CREMA, CREMA_HI = (58, 32, 18), (168, 114, 64), (226, 184, 126)
FOAM, FOAM_BR, LOZA, BODY = (238, 220, 190), (168, 112, 66), (250, 242, 226), (34, 26, 21)
yy, xx = np.mgrid[0:LH, 0:LW]
XC = (LW - 1) / 2
BAY = B8[yy % 8, xx % 8]


def arc(y0, R, sign=1): return y0 + sign * (R - np.sqrt(R * R - (xx - XC) ** 2))


def sky(horizon):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, C1, .5), C1, mixc(C1, C2, .5), C2, mixc(C2, GLOW, .6), GLOW]
    return Image.fromarray(dither_ramp(t, ramp, 0.34, horizon / LH + 0.02), 'RGB').convert('RGBA')


def header(img):
    text(img, (13, 40), '01 / 04', F_S, CREAM)
    text(img, (12, 50), 'JAVA', fit_title('JAVA', 156, 30), CREAM)
    text(img, (13, 92), '(the new kid.)', F_M, CREAM)


def floaters(img, items):
    for (mk, mw, mx, my) in items:
        img.alpha_composite(motif(mk, mw), (mx, my))


def layer(rgb, mask):
    out = np.zeros((LH, LW, 4), np.uint8); out[..., :3] = rgb; out[..., 3] = mask * 255
    return Image.fromarray(out, 'RGBA')


def coffee_fill(depth):
    rgb = np.zeros((LH, LW, 3), np.uint8); rgb[:] = COFFEE
    dark = np.clip(depth / 130.0, 0, 1) * 1.1 > BAY
    rgb[dark] = (20, 11, 7)
    rgb[(depth >= 5) & (depth < 22) & (B8[yy % 8, (xx + yy // 3) % 8] < 0.09) & ((yy // 2) % 3 == 0)] = (96, 58, 30)
    rgb[(depth >= 0) & (depth < 3)] = CREMA
    rgb[(depth >= 0) & (depth < 1)] = CREMA_HI
    return rgb


def foam_fill(depth):
    rgb = np.zeros((LH, LW, 3), np.uint8); rgb[:] = FOAM
    band = np.mod((depth * 0.9 + 7 * np.sin(xx / 15.0)) / 10.0, 1.0)
    rgb[(depth > 4) & (band < 0.26)] = FOAM_BR
    rgb[(depth > 4) & (np.abs(band - 0.26) < 0.05) & (BAY > 0.5)] = (206, 166, 122)
    rgb[(depth >= 0) & (depth < 1)] = (255, 250, 238)
    return rgb


def body_fill(d2):
    rgb = np.zeros((LH, LW, 3), np.uint8); rgb[:] = BODY
    rgb[(np.clip(1 - d2 / 40.0, 0, 1) * 0.5 > BAY)] = (58, 44, 34)
    return rgb


def swirl(cx, cy, rx, ry):
    ex, ey = (xx - cx) / rx, (yy - cy) / ry
    rr = np.sqrt(ex ** 2 + ey ** 2)
    sw = np.mod(np.arctan2(ey, ex) / (2 * np.pi) + 1.15 * rr, 1.0)
    rgb = np.zeros((LH, LW, 3), np.uint8); rgb[:] = FOAM
    rgb[sw >= 0.55] = FOAM_BR
    rgb[(np.abs(sw - 0.55) < 0.06) & (BAY > 0.5)] = (206, 166, 122)
    return rgb, rr < 1


FL = [(10, 28, 3, 112), (57, 9, 14, 154), (58, 8, 92, 150), (13, 20, 88, 112), (44, 8, 166, 132), (57, 7, 60, 110)]
OPTS = []


def finish(img, name, es, noah_xy, s=0.33):
    c = up(img, P)
    noah(c, 'host', s, noah_xy[0] * P, noah_xy[1] * P + 8)
    i = len(OPTS) + 1
    c.convert('RGB').save(os.path.join(FR, f'h_{i:02d}.png'))
    OPTS.append((i, name, es, c))


# ---- 1 · loma de cafe (como esta ahora) ----
top = arc(192, 300)
img = sky(192); header(img); floaters(img, FL)
b = bag_obj('cerezas', 46); img.alpha_composite(b, (114, int(top[0, 138]) + 3 - b.height))
img.alpha_composite(layer(coffee_fill(yy - top), yy >= top))
finish(img, 'LOMA DE CAFÉ', 'Como está ahora: una loma oscura de café con su borde de crema.', (58, int(top[0, 58])))

# ---- 2 · borde del capuchino: la curva al reves ----
far, near = arc(152, 420), arc(224, 300, -1)
img = sky(152); header(img)
floaters(img, [(10, 26, 4, 106), (57, 9, 150, 108), (13, 18, 96, 104), (58, 8, 60, 118), (44, 8, 166, 130)])
img.alpha_composite(layer(foam_fill((yy - far) * 0.6), yy >= far + 5))
rim = np.zeros((LH, LW, 3), np.uint8); rim[:] = LOZA
rim[(yy - far < 1) | (yy - far >= 4)] = OUTLINE
img.alpha_composite(layer(rim, (yy >= far) & (yy < far + 5)))
b = bag_obj('cerezas', 46); img.alpha_composite(b, (116, int(near[0, 139]) + 4 - b.height))
lip = np.zeros((LH, LW, 3), np.uint8); lip[:] = LOZA
lip[(yy - near < 1) | (yy - near >= 7)] = OUTLINE
img.alpha_composite(layer(lip, (yy >= near) & (yy < near + 8)))
img.alpha_composite(layer(body_fill(yy - near - 8), yy >= near + 8))
finish(img, 'BORDE DEL CAPUCHINO', 'La taza vista un poco desde arriba. Noah camina por el borde de adelante, que curva hacia abajo; detrás queda la espuma.', (58, int(near[0, 58]) + 1))

# ---- 3 · espuma arriba: los colores al reves ----
top, base = arc(192, 300), arc(218, 520)
img = sky(192); header(img); floaters(img, FL)
b = bag_obj('cerezas', 46); img.alpha_composite(b, (114, int(top[0, 138]) + 3 - b.height))
img.alpha_composite(layer(foam_fill(yy - top), yy >= top))
lip = np.zeros((LH, LW, 3), np.uint8); lip[:] = LOZA
lip[(yy - base < 1) | (yy - base >= 6)] = OUTLINE
img.alpha_composite(layer(lip, (yy >= base) & (yy < base + 7)))
img.alpha_composite(layer(body_fill(yy - base - 7), yy >= base + 7))
finish(img, 'ESPUMA ARRIBA', 'La misma loma, pero es la espuma clara del capuchino. La taza oscura queda debajo.', (58, int(top[0, 58])))

# ---- 4 · taza completa ----
img = sky(206); header(img); floaters(img, [(10, 28, 3, 112), (57, 9, 150, 116), (13, 20, 98, 110), (58, 8, 24, 160), (44, 8, 166, 150)])
d = ImageDraw.Draw(img)
d.rectangle([0, 298, LW, LH], fill=BLACK); d.line([(0, 298), (LW, 298)], fill=(70, 62, 54))
x1, x2, yt, yb = 28, 132, 214, 296
d.ellipse([x2 - 10, yt + 10, x2 + 30, yt + 62], fill=LOZA); d.ellipse([x2 - 2, yt + 20, x2 + 20, yt + 52], fill=tuple(int(v) for v in np.asarray(img)[yt + 34, x2 + 40, :3]))
d.rounded_rectangle([x1 - 1, yt - 1, x2 + 1, yb + 1], radius=13, fill=LOZA)
d.rounded_rectangle([x1, yt, x2, yb], radius=12, fill=BODY)
a = np.asarray(img).copy()
hl = (a[..., :3] == BODY).all(2) & ((1 - (xx - x1) / (x2 - x1)) ** 3 * 0.8 > BAY)
a[hl, :3] = (62, 47, 36); img = Image.fromarray(a, 'RGBA'); d = ImageDraw.Draw(img)
d.ellipse([x1 - 4, yt - 14, x2 + 4, yt + 10], fill=LOZA)
rgb, m = swirl(80, yt - 2, 50, 9); img.alpha_composite(layer(rgb, m))
b = bag_obj('cerezas', 34); img.alpha_composite(b, (92, yt - 2 - b.height))
finish(img, 'TAZA COMPLETA', 'Se ve toda la taza, con su asa. Noah y el empaque van encima, más pequeños, y hay más cielo.', (60, yt - 4), s=0.24)

# ---- 5 · desde arriba ----
img = Image.new('RGBA', (LW, LH), BLACK + (255,)); header(img)
cx, cy, rx, ry = 84, 204, 76, 54
r = np.sqrt(((xx - cx) / 1.25) ** 2 + (yy - cy) ** 2)
a = np.asarray(img).copy()
halo = np.clip(1 - (r - 50) / 62.0, 0, 1)
a[(halo * 0.9 > BAY) & (yy > 104), :3] = C1
a[(halo * 0.55 > BAY) & (yy > 104), :3] = C2
img = Image.fromarray(a, 'RGBA'); d = ImageDraw.Draw(img)
d.ellipse([cx + rx - 8, cy - 14, cx + rx + 22, cy + 22], fill=LOZA); d.ellipse([cx + rx - 2, cy - 7, cx + rx + 14, cy + 15], fill=C1)
d.ellipse([cx - rx, cy - ry + 10, cx + rx, cy + ry + 22], fill=BODY)
d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=LOZA)
d.ellipse([cx - rx + 7, cy - ry + 6, cx + rx - 7, cy + ry - 5], fill=(196, 150, 100))
rgb, m = swirl(cx, cy + 1, rx - 12, ry - 11); img.alpha_composite(layer(rgb, m))
floaters(img, [(10, 26, 2, 114), (57, 9, 160, 122), (13, 18, 150, 268), (58, 8, 10, 262), (44, 8, 92, 110)])
b = bag_obj('cerezas', 38); img.alpha_composite(b, (96, cy + 20 - b.height))
finish(img, 'DESDE ARRIBA', 'El capuchino visto desde arriba, sobre negro. Noah da la vuelta por el borde y el empaque queda en medio de la espuma.', (46, cy + ry - 8), s=0.26)

# ---- lamina con las cinco opciones ----
TW, TH, GAP, PAD = 432, 768, 30, 44
W = PAD * 2 + len(OPTS) * TW + (len(OPTS) - 1) * GAP
sheet = Image.new('RGB', (W, PAD + 110 + TH + 230), (23, 21, 19))
d = ImageDraw.Draw(sheet)
f_h = font('montserrat', 'montserrat-latin-300-normal.woff', 54)
f_k = font('montserrat', 'montserrat-latin-500-normal.woff', 18)
f_n = font('montserrat', 'montserrat-latin-500-normal.woff', 24)
f_b = font('montserrat', 'montserrat-latin-400-normal.woff', 21)
d.text((PAD, PAD - 6), 'ESCOGE UNA  ·  LA MISMA ESCENA ARMADA DE CINCO MANERAS', font=f_k, fill=ORANGE)
d.text((PAD, PAD + 22), '¿Cómo se ve la taza?', font=f_h, fill=CREAM)


def wrap(s, f, maxw):
    out, line = [], ''
    for w_ in s.split():
        t = (line + ' ' + w_).strip()
        if f.getlength(t) <= maxw: line = t
        else: out.append(line); line = w_
    return out + [line]


for i, name, es, c in OPTS:
    x = PAD + (i - 1) * (TW + GAP); y = PAD + 110
    sheet.paste(c.convert('RGB').resize((TW, TH), Image.LANCZOS), (x, y))
    d.rectangle([x, y, x + TW - 1, y + TH - 1], outline=(51, 48, 44))
    d.text((x, y + TH + 18), f'{i}', font=f_h, fill=ORANGE)
    d.text((x + 50, y + TH + 40), name, font=f_n, fill=CREAM)
    for k, ln in enumerate(wrap(es, f_b, TW - 4)):
        d.text((x, y + TH + 92 + k * 30), ln, font=f_b, fill=(207, 198, 184))
sheet.save(os.path.join(SB, 'opciones_taza.jpg'), quality=90)
print('ok', len(OPTS), sheet.size)
