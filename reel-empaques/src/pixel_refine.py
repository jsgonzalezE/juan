"""Afinar la idea F: cada ajuste por separado sobre la misma escena (Java), para escoger cuales si.

Uso: python3 src/pixel_refine.py -> storyboards/afinar_idea_f.jpg + storyboards/frames/r_0N.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P, R = 180, 320, 6, 300
GLOW = (246, 228, 196)
C1, C2 = (40, 84, 40), (132, 170, 60)                      # verde de Java
yy, xx = np.mgrid[0:LH, 0:LW]
BAY = B8[yy % 8, xx % 8]
XC = (LW - 1) / 2
FL = [(10, 30, 16, 118), (57, 9, 150, 112), (58, 9, 132, 132), (13, 22, 96, 108), (44, 8, 14, 158)]   # como esta ahora


def ydome(h0, x): return h0 + R - np.sqrt(R * R - (np.asarray(x, float) - XC) ** 2)


def sky(h0, mist=False):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, C1, .5), C1, mixc(C1, C2, .5), C2, mixc(C2, GLOW, .6), GLOW]
    rgb = dither_ramp(t, ramp, 0.34 + (h0 - 192) / LH * 0.5, h0 / LH + 0.02)
    if mist:                                                # dos capas de neblina: dan profundidad
        for yc, amp, k in [(h0 - 22, 3.0, 0.55), (h0 - 46, 4.0, 0.35)]:
            edge = yc + amp * np.sin(xx / 13.0 + yc)
            band = (yy > edge) & (yy < edge + 9)
            dens = np.clip(1 - np.abs(yy - edge - 4.5) / 4.5, 0, 1) * k
            rgb[band & (dens > BAY)] = mixc(C2, GLOW, .72)
    return Image.fromarray(rgb, 'RGB').convert('RGBA')


def coffee(h0, reflect=False):
    depth = yy - ydome(h0, xx)
    base, dark = mixc((46, 26, 15), C1, 0.14), (20, 11, 7)
    out = np.zeros((LH, LW, 4), np.uint8)
    k = np.clip(depth / (LH - h0), 0, 1)
    out[..., :3] = np.where((k * 1.1 > BAY)[..., None], dark, base)
    streak = (depth >= 5) & (depth < 22) & (B8[yy % 8, (xx + yy // 3) % 8] < 0.09) & ((yy // 2) % 3 == 0)
    out[streak, :3] = (96, 58, 30)
    if reflect:                                             # el cielo se refleja en el cafe, en lineas
        sheen = (depth >= 3) & (depth < 18) & (yy % 2 == 0) & ((1 - (depth - 3) / 15.0) * 0.5 > BAY)
        out[sheen, :3] = mixc(C2, base, 0.62)
    out[(depth >= 0) & (depth < 3), :3] = (152, 100, 54)
    out[(depth >= 0) & (depth < 1), :3] = (218, 174, 116)
    out[..., 3] = (depth >= 0) * 255
    return Image.fromarray(out, 'RGBA')


def header(img):
    text(img, (13, 40), '01 / 04', F_S, CREAM)
    text(img, (12, 50), 'JAVA', fit_title('JAVA', 156, 30), CREAM)
    text(img, (13, 92), '(the new kid.)', F_M, CREAM)


def halo(img, cx, cy, r):
    a = np.asarray(img).copy()
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2)
    f = np.clip(1 - d / r, 0, 1) * (yy >= 108)        # el brillo no se mete debajo del texto
    a[(f * 0.9 > BAY) & (d < r), :3] = mixc(C1, GLOW, .45)
    a[(f * 0.9 > BAY + 0.3) & (d < r), :3] = mixc(C2, GLOW, .8)
    a[(f > 0.72) & (d < r), :3] = GLOW
    img.paste(Image.fromarray(a, 'RGBA'))


def ambient(img):
    """Pocos dibujos, mas grandes, entrando por los bordes (no regados como confeti)."""
    img.alpha_composite(motif(10, 64), (-14, 102))          # rama con cerezas, desde la izquierda
    img.alpha_composite(motif(13, 34), (154, 98))           # ramita, desde la derecha
    for (mk, mw, mx, my) in [(57, 8, 70, 124), (58, 7, 142, 150)]:
        img.alpha_composite(motif(mk, mw), (mx, my))


def scene(h0=192, noah_s=0.33, noah_x=58, sun=False, sun_x=90, reflect=False, amb=False):
    img = sky(h0, mist=amb)
    if amb:
        ambient(img)
    else:
        for (mk, mw, mx, my) in FL:
            img.alpha_composite(motif(mk, mw), (mx, my))
    if sun:                                                 # el empaque sube por detras del horizonte
        b = bag_obj('cerezas', 62)
        top = int(ydome(h0, sun_x)) + 26 - b.height
        halo(img, sun_x, top + 18, 74)
        img.alpha_composite(b, (sun_x - b.width // 2, top))
    else:
        b = bag_obj('cerezas', 46)
        img.alpha_composite(b, (114, int(ydome(h0, 138)) + 3 - b.height))
    header(img)
    img.alpha_composite(coffee(h0, reflect))
    c = up(img, P)
    noah(c, 'host', noah_s, noah_x * P, int(ydome(h0, noah_x)) * P + 8)
    return c


OPTS = [
    ('ACTUAL', 'Como está ahora, para comparar.', Image.open(os.path.join(FR, 'f_02.png')).convert('RGBA')),
    ('NOAH MÁS GRANDE', 'Noah casi el doble de grande y al frente: es el presentador.', scene(noah_s=0.48, noah_x=50)),
    ('EL EMPAQUE SALE COMO SOL', 'El empaque, más grande, sube por detrás del horizonte con un brillo. En el video sale despacio.', scene(sun=True, noah_x=34)),
    ('MÁS CIELO, CAFÉ QUE BRILLA', 'El horizonte baja: más cielo y menos loma oscura. El café refleja el color de cada variedad.', scene(h0=220, reflect=True)),
    ('AMBIENTE, NO CONFETI', 'Menos dibujos sueltos y más grandes, entrando por los bordes, con capas de neblina.', scene(amb=True)),
    ('TODO JUNTO', 'Los cuatro ajustes al mismo tiempo.', scene(h0=212, noah_s=0.46, noah_x=36, sun=True, sun_x=110, reflect=True, amb=True)),
]
for i, (_, _, c) in enumerate(OPTS):
    c.convert('RGB').save(os.path.join(FR, f'r_{i:02d}.png'))

# ---- lamina ----
TW, TH, GAP, PAD = 400, 711, 26, 44
W = PAD * 2 + len(OPTS) * TW + (len(OPTS) - 1) * GAP
sheet = Image.new('RGB', (W, PAD + 120 + TH + 200), (23, 21, 19))
d = ImageDraw.Draw(sheet)
f_h = font('montserrat', 'montserrat-latin-300-normal.woff', 54)
f_k = font('montserrat', 'montserrat-latin-500-normal.woff', 18)
f_n = font('montserrat', 'montserrat-latin-500-normal.woff', 21)
f_b = font('montserrat', 'montserrat-latin-400-normal.woff', 20)
d.text((PAD, PAD - 6), 'AFINAR LA IDEA F  ·  CADA AJUSTE POR SEPARADO, SOBRE LA MISMA ESCENA', font=f_k, fill=ORANGE)
d.text((PAD, PAD + 22), 'Dime cuáles sí y cuáles no', font=f_h, fill=CREAM)


def wrap(s, f, maxw):
    out, line = [], ''
    for w_ in s.split():
        t = (line + ' ' + w_).strip()
        if f.getlength(t) <= maxw: line = t
        else: out.append(line); line = w_
    return out + [line]


for i, (name, es, c) in enumerate(OPTS):
    x = PAD + i * (TW + GAP); y = PAD + 120
    sheet.paste(c.convert('RGB').resize((TW, TH), Image.LANCZOS), (x, y))
    d.rectangle([x, y, x + TW - 1, y + TH - 1], outline=ORANGE if i == 0 else (51, 48, 44))
    d.text((x, y + TH + 16), f'{i}', font=f_h, fill=SOFT if i == 0 else ORANGE)
    d.text((x + 46, y + TH + 38), name, font=f_n, fill=CREAM)
    for k, ln in enumerate(wrap(es, f_b, TW - 4)):
        d.text((x, y + TH + 90 + k * 28), ln, font=f_b, fill=(207, 198, 184))
sheet.save(os.path.join(SB, 'afinar_idea_f.jpg'), quality=90)
print('ok', len(OPTS), sheet.size)
