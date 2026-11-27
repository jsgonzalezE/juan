"""Idea F (el horizonte de cafe): Noah camina sobre la curva de una taza de cafe.

El horizonte curvo es la superficie del cafe. El mundo gira bajo Noah; los empaques van saliendo
por el horizonte, el cielo cambia de color con cada variedad y flotan referencias a los sabores.
Al final la imagen se aleja y la curva resulta ser la taza de Noah.
Uso: python3 src/pixel_cup.py -> storyboards/frames/f_XX.png + frames_f.json
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P = 180, 320, 6
H0, R = 192, 300                      # tope de la curva y radio
GLOW = (246, 228, 196)


def yd(x): return H0 + R - np.sqrt(R * R - (np.asarray(x, float) - LW / 2) ** 2)


def sky(c1, c2, glow=GLOW):
    yy, xx = np.mgrid[0:LH, 0:LW]
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, c1, .5), c1, mixc(c1, c2, .5), c2, mixc(c2, glow, .6), glow]
    return Image.fromarray(dither_ramp(t, ramp, 0.34, H0 / LH + 0.02), 'RGB').convert('RGBA')


def coffee(tint=None, lit=True):
    """La superficie del cafe: curva oscura con borde de crema y brillos en puntos."""
    yy, xx = np.mgrid[0:LH, 0:LW]
    depth = yy - yd(xx)
    base = (46, 26, 15) if lit else (26, 20, 17)
    if tint is not None:
        base = mixc(base, tint, 0.14)
    dark = (20, 11, 7) if lit else (14, 12, 11)
    k = np.clip(depth / (LH - H0), 0, 1)
    out = np.zeros((LH, LW, 4), np.uint8)
    out[..., :3] = np.where((k * 1.1 > B8[yy % 8, xx % 8])[..., None], dark, base)
    streak = (depth >= 5) & (depth < 22) & (B8[yy % 8, (xx + yy // 3) % 8] < 0.09) & ((yy // 2) % 3 == 0)
    out[streak, :3] = (96, 58, 30) if lit else (44, 36, 30)
    out[(depth >= 0) & (depth < 3), :3] = (152, 100, 54) if lit else (58, 48, 40)      # crema
    out[(depth >= 0) & (depth < 1), :3] = (218, 174, 116) if lit else (84, 72, 60)     # brillo del borde
    out[..., 3] = (depth >= 0) * 255
    return Image.fromarray(out, 'RGBA')


VAR = [
    dict(name='JAVA', n='01', bag='cerezas', c=[(40, 84, 40), (132, 170, 60)], noah='host', s=0.33, line='(the new kid.)',
         motifs=[(10, 28, 3, 112), (57, 9, 14, 154), (58, 8, 92, 150), (13, 20, 88, 112), (44, 8, 166, 132), (57, 7, 60, 110)]),
    dict(name='CASTILLO', n='02', bag='colores', c=[(150, 30, 86), (234, 124, 30)], noah='listen', s=0.40, line='(the loud one.)',
         motifs=[(15, 18, 6, 110), (28, 14, 90, 114), (42, 12, 12, 152), (12, 14, 92, 148), (25, 10, 166, 130), (42, 9, 58, 110)]),
    dict(name='GEISHA', n='03', bag='casa_azul', c=[(26, 66, 122), (96, 154, 200)], noah='peek', s=0.36, line='(the fancy one.)',
         motifs=[(5, 28, 3, 110), (42, 12, 92, 114), (19, 22, 40, 116), (15, 12, 94, 150), (42, 9, 166, 130), (12, 12, 10, 156)]),
    dict(name='BOURBON', n='04', bag='casa_roja', c=[(124, 28, 24), (216, 90, 52)], noah='sideeye', s=0.36, line="(...who's that dog?)",
         motifs=[(7, 20, 5, 110), (28, 13, 90, 114), (26, 20, 6, 152), (18, 13, 92, 150), (53, 9, 166, 130), (51, 8, 60, 110)]),
]
B = Board('f')


def compose(sky_img, behind, front_fn, tint=None, lit=True):
    """cielo -> cosas detras del horizonte -> cafe -> cosas encima."""
    for im, xy in behind:
        sky_img.alpha_composite(im, xy)
    sky_img.alpha_composite(coffee(tint, lit))
    c = up(sky_img, P)
    front_fn(c)
    return c


# 1 · amanece
img = sky((22, 20, 19), (40, 36, 32), glow=(86, 76, 64))
text(img, (90, 96), 'FOUR NEW VARIETIES', F_M, CREAM, 'ma')
text(img, (90, 118), '(follow Noah.)', F_S, SOFT, 'ma')
b = bag_obj('cerezas', 46)
c = compose(img, [(b, (124, int(yd(148)) - 34))], lambda c: noah(c, 'host', 0.33, 62 * P, int(yd(62)) * P + 8), lit=False)
B.save(c, '0 – 2,5 s', 'Amanece sobre el café', 'Todo oscuro. El horizonte curvo es la superficie de una taza de café. Noah camina por encima; el primer empaque empieza a salir por el horizonte, como un sol.',
       'FOUR NEW VARIETIES · (follow Noah.)', 'Pasitos. Un zumbido grave, como café sirviéndose.')

# 2-5 · un empaque, un cielo, una expresion
times = ['2,5 – 6 s', '6 – 9 s', '9 – 12 s', '12 – 15 s']
desc = ['El mundo gira bajo Noah y el empaque termina de salir. El cielo se pinta de verde y aparecen flotando cerezas y hojas. Noah sonríe.',
        'Noah sigue caminando; el cielo pasa a magenta y naranja y flotan flores y estrellas. Segundo empaque. Noah levanta la oreja.',
        'El cielo pasa a azul, flotan flores de café. Tercer empaque. Noah se asoma por el horizonte, muy serio.',
        'El cielo pasa a rojo. Cuarto empaque: Noah ve al perro pintado y lo mira de reojo.']
for k, v in enumerate(VAR):
    img = sky(*v['c'])
    for (mk, mw, mx, my) in v['motifs']:
        img.alpha_composite(motif(mk, mw), (mx, my))
    text(img, (13, 40), f"{v['n']} / 04", F_S, CREAM)
    text(img, (12, 50), v['name'], fit_title(v['name'], 156, 30), CREAM)
    text(img, (13, 92), v['line'], F_M, CREAM)
    b = bag_obj(v['bag'], 46)
    bx = 114
    img.alpha_composite(b, (bx, int(yd(bx + 24)) + 3 - b.height))   # el empaque, apoyado en la curva
    behind = []
    if v['noah'] == 'peek':                                         # Noah asomado detras del horizonte
        tmp = up(img, P)
        noah(tmp, 'peek', v['s'], 56 * P, int(yd(56)) * P + 20)
        tmp.alpha_composite(up(coffee(v['c'][0]), P))
        c = tmp
    else:
        img.alpha_composite(coffee(v['c'][0]))
        c = up(img, P)
        noah(c, v['noah'], v['s'], 58 * P, int(yd(58)) * P + 8)
    B.save(c, times[k], f"Empaque: {v['name'].capitalize()}", desc[k], f"{v['n']} / 04 · {v['name']} · {v['line']}", 'Nota al llegar. Cambia el ambiente de fondo.')

# 6 · se aleja: era su taza
warm = [(104, 58, 22), (226, 160, 70)]
img = sky(*warm)
text(img, (90, 76), '(Noah in his', F_M, CREAM, 'ma')
text(img, (90, 96), 'happy place.)', F_M, CREAM, 'ma')
yy, xx = np.mgrid[0:LH, 0:LW]
floor = Image.fromarray(np.dstack([np.full((LH, LW, 3), CREAM, np.uint8), ((yy >= 262) * 255).astype(np.uint8)]), 'RGBA')
img.alpha_composite(floor)
ImageDraw.Draw(img).line([(0, 262), (LW, 262)], fill=INK)
c = up(img, P)
noah(c, 'mug', 0.86, 540, 262 * P + 8)
B.save(c, '15 – 17,5 s', 'Se aleja: era su taza', 'La imagen se aleja de golpe y la curva resulta ser el café de la taza de Noah, la de tu ilustración. Noah la abraza.',
       '(Noah in his happy place.)', 'Sorbo. Suspiro.')

# 7 · cierre
img = sky(*warm)
text(img, (90, 146), 'COMING SOON', fit_title('COMING SOON', 150, 22), CREAM, 'ma')
text(img, (90, 176), '(green coffee - Huila, Colombia)', F_S, INK, 'ma')
text(img, (90, 190), '@juanitocoffee', F_S, INK, 'ma')
img.alpha_composite(floor)
ImageDraw.Draw(img).line([(0, 262), (LW, 262)], fill=INK)
c = up(img, P)
logo = Image.open(os.path.join(A, 'logo_blanco.png')).convert('RGBA')
lw = 340; logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
c.alpha_composite(logo, (540 - lw // 2, 330))
noah(c, 'mug', 0.42, 540, 262 * P + 8)
B.save(c, '17,5 – 20 s', 'Cierre', 'Misma escena. Entra el logo y los datos.',
       'COMING SOON · (green coffee - Huila, Colombia) · @juanitocoffee', 'Taza que se apoya en la mesa. Fin.')
B.close()
