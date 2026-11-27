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


def yd(x): return H0 + R - np.sqrt(R * R - (np.asarray(x, float) - (LW - 1) / 2) ** 2)   # centro entre dos pixeles: curva simetrica


def sky(c1, c2, glow=GLOW):
    yy, xx = np.mgrid[0:LH, 0:LW]
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, c1, .5), c1, mixc(c1, c2, .5), c2, mixc(c2, glow, .6), glow]
    return Image.fromarray(dither_ramp(t, ramp, 0.34, H0 / LH + 0.02), 'RGB').convert('RGBA')


MUG, MUG_SH, MUG_HI = (252, 236, 212), (224, 200, 174), (255, 248, 234)   # colores de la taza de Noah


def ylip(x): return H0 + 13 + 520 - np.sqrt(520.0 ** 2 - (np.asarray(x, float) - (LW - 1) / 2) ** 2)


def coffee(tint=None, lit=True):
    """La taza vista de cerca: cafe con crema arriba, el borde de la taza y su cuerpo color crema."""
    yy, xx = np.mgrid[0:LH, 0:LW]
    top, lip = yd(xx), ylip(xx)
    depth = yy - top
    out = np.zeros((LH, LW, 4), np.uint8)
    # cafe
    base = (58, 32, 18) if tint is None else mixc((58, 32, 18), tint, 0.12)
    out[..., :3] = base
    streak = (depth >= 4) & (B8[yy % 8, (xx + yy // 2) % 8] < 0.12) & (yy % 3 == 0)
    out[streak, :3] = (104, 62, 32)
    out[(depth >= 0) & (depth < 3), :3] = (168, 114, 64)       # crema
    out[(depth >= 0) & (depth < 1), :3] = (226, 184, 126)      # brillo de la crema
    # borde de la taza
    d2 = yy - lip
    rim = (d2 >= 0) & (d2 < 7)
    out[rim, :3] = MUG_HI
    out[(d2 >= 0) & (d2 < 1), :3] = OUTLINE
    out[(d2 >= 6) & (d2 < 7), :3] = OUTLINE
    # cuerpo de la taza, con sombra en puntos a los lados y bajo el borde
    body = d2 >= 7
    side = (np.abs(xx - LW / 2) / (LW / 2)) ** 2 * 0.75
    under = np.clip(1 - (d2 - 7) / 9.0, 0, 1) * 0.8
    shade = np.maximum(side, under) > B8[yy % 8, xx % 8]
    out[body, :3] = MUG
    out[body & shade, :3] = MUG_SH
    out[..., 3] = (depth >= 0) * 255
    return Image.fromarray(out, 'RGBA')


def mug_wide(img):
    """La taza completa (toma inicial): cuerpo crema, asa, carita y cafe arriba, como la taza de Noah."""
    d = ImageDraw.Draw(img)
    x1, x2, yt, yb = 34, 132, 198, 292
    d.ellipse([x2 - 12, yt + 14, x2 + 30, yt + 70], fill=OUTLINE)                 # asa
    d.ellipse([x2 - 6, yt + 20, x2 + 24, yt + 64], fill=MUG)
    d.ellipse([x2 - 2, yt + 30, x2 + 14, yt + 54], fill=OUTLINE)
    d.ellipse([x2, yt + 32, x2 + 12, yt + 52], fill=tuple(int(v) for v in np.asarray(img)[yt + 40, x2 + 40, :3]))
    d.rounded_rectangle([x1 - 2, yt - 2, x2 + 2, yb + 2], radius=14, fill=OUTLINE)  # cuerpo
    d.rounded_rectangle([x1, yt, x2, yb], radius=12, fill=MUG)
    a = np.asarray(img).copy()
    yy, xx = np.mgrid[0:LH, 0:LW]
    inside = (a[..., :3] == MUG).all(2)
    sh = inside & (((xx - x1) / (x2 - x1)) ** 3 * 0.9 > B8[yy % 8, xx % 8])
    a[sh, :3] = MUG_SH
    img.paste(Image.fromarray(a, 'RGBA'))
    d = ImageDraw.Draw(img)
    d.ellipse([x1 - 4, yt - 12, x2 + 4, yt + 8], fill=OUTLINE)                    # boca de la taza
    d.ellipse([x1 - 2, yt - 10, x2 + 2, yt + 6], fill=MUG_HI)
    d.ellipse([x1 + 4, yt - 9, x2 - 4, yt + 3], fill=OUTLINE)
    d.ellipse([x1 + 5, yt - 8, x2 - 5, yt + 2], fill=(58, 32, 18))                # cafe
    d.arc([x1 + 8, yt - 7, x2 - 8, yt + 1], 200, 340, fill=(226, 184, 126))       # brillo de crema
    for ex in (66, 98):                                                           # carita
        d.rounded_rectangle([ex - 3, yt + 34, ex + 3, yt + 46], radius=3, fill=OUTLINE)
    d.arc([60, yt + 40, 104, yt + 72], 20, 160, fill=OUTLINE, width=3)


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


# 1 · la taza completa
img = sky((26, 21, 18), (62, 46, 32), glow=(44, 34, 26))
text(img, (90, 96), 'FOUR NEW VARIETIES', F_M, CREAM, 'ma')
text(img, (90, 118), '(follow Noah.)', F_S, SOFT, 'ma')
ImageDraw.Draw(img).rectangle([0, 294, LW, LH], fill=BLACK)
ImageDraw.Draw(img).line([(0, 294), (LW, 294)], fill=(70, 62, 54))
mug_wide(img)
c = up(img, P)
noah(c, 'host', 0.15, 70 * P, 190 * P + 4)
B.save(c, '0 – 2 s', 'La taza completa', 'Abre con la taza de Noah entera, humeando, y él chiquito caminando por encima del café. Así queda claro desde el primer segundo que el mundo es una taza.',
       'FOUR NEW VARIETIES · (follow Noah.)', 'Café sirviéndose. Pasitos.')

# 2-5 · un empaque, un cielo, una expresion
times = ['2 – 6 s', '6 – 9 s', '9 – 12 s', '12 – 15 s']
desc = ['La cámara baja hasta el borde de la taza: abajo se ve la loza crema, encima el café con su crema. Noah camina sobre el café, sale el primer empaque, el cielo se pinta de verde y flotan cerezas y hojas.',
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

# ---------- final: Noah tostando -> los granos arman el logo -> el logo pasa de pixel art a normal ----------
warm = [(104, 58, 22), (226, 160, 70)]
LOGO = Image.open(os.path.join(A, 'logo_blanco.png')).convert('RGBA')
rng = np.random.default_rng(4)


def pixel_logo(w, drop=0.0):
    """El logo oficial llevado a pixel art (solo se reduce: no se redibuja)."""
    h = round(LOGO.height * w / LOGO.width)
    on = np.asarray(LOGO.split()[3].resize((w, h), Image.BOX)) >= 92
    if drop:
        on &= rng.random(on.shape) > drop
    out = np.zeros((h, w, 4), np.uint8); out[on] = CREAM + (255,)
    return Image.fromarray(out, 'RGBA')


def puff(img, cx, cy, r, col=(226, 214, 196)):
    """Bocanada de humo en puntos."""
    d = ImageDraw.Draw(img)
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            q = ((x - cx) ** 2 + (y - cy) ** 2) / (r * r + 0.1)
            if q <= 1 and B8[y % 8, x % 8] > q * 0.8:
                d.point((x, y), fill=col)


def spaced(canvas, s, f, cx, y, track, fill):
    """Texto fino con espacio entre letras (letra normal, no pixel)."""
    d = ImageDraw.Draw(canvas)
    ws = [f.getlength(ch) for ch in s]
    total = sum(ws) + track * (len(s) - 1)
    x = cx - total / 2
    for ch, wch in zip(s, ws):
        d.text((x, y), ch, font=f, fill=fill); x += wch + track


# 6 · llega a la tostadora
img = sky(*warm)
text(img, (90, 64), '(first crack?', F_M, CREAM, 'ma')
text(img, (90, 84), 'I heard it first.)', F_M, CREAM, 'ma')
for (cx_, cy_, r_) in [(112, 124, 6), (120, 108, 4), (106, 112, 3)]:
    puff(img, cx_, cy_, r_)
for (mk, mw, mx, my) in [(53, 9, 126, 138), (56, 8, 96, 132), (25, 9, 134, 118)]:
    img.alpha_composite(motif(mk, mw), (mx, my))
img.alpha_composite(coffee(warm[0]))
c = up(img, P)
noah(c, 'roaster', 0.42, 86 * P, int(yd(86)) * P + 8)
B.save(c, '15 – 16,5 s', 'Final: Noah tostando', 'Ya no hay empaques. Por el horizonte aparece la tostadora y Noah se sienta al lado, con la oreja levantada. El tambor gira, sale humo y saltan los primeros granos.',
       '(first crack? I heard it first.)', 'Tambor girando. Un "crack".')

# 7 · los granos suben y arman el logo
img = sky((40, 24, 12), (150, 92, 36), glow=(214, 150, 80))
lg = pixel_logo(30, drop=0.42)
big = lg.resize((lg.width * 2, lg.height * 2), Image.NEAREST)      # pixeles gordos: el logo apenas se esta armando
img.alpha_composite(big, (90 - big.width // 2, 34))
for i in range(46):                                               # chorro de pixeles y granos que sube desde la tostadora
    tt = rng.random()
    x = int(104 + (90 - 104) * tt + rng.normal(0, 10 * (0.3 + tt)))
    y = int(150 - 96 * tt + rng.normal(0, 4))
    ImageDraw.Draw(img).rectangle([x, y, x + 1, y + 1], fill=CREAM if rng.random() > 0.3 else (226, 160, 70))
for (mk, mw, mx, my) in [(53, 9, 112, 132), (56, 8, 84, 118), (25, 8, 100, 104), (53, 7, 70, 98)]:
    img.alpha_composite(motif(mk, mw), (mx, my))
img.alpha_composite(coffee(warm[0]))
c = up(img, P)
noah(c, 'roaster', 0.42, 86 * P, int(yd(86)) * P + 8)
B.save(c, '16,5 – 17,5 s', 'Los granos arman el logo', 'Con el "crack" los granos salen disparados hacia arriba, se vuelven pixeles y empiezan a formar el logo de Juanito en el cielo. Noah lo mira.',
       '(sin texto)', 'Palomitas de "crack" cada vez más rápidas, subiendo de tono.')

# 8 · solo el logo, en pixel art
img = Image.new('RGBA', (LW, LH), BLACK + (255,))
lg = pixel_logo(62)
img.alpha_composite(lg, (90 - lg.width // 2, 96))
for (x, y) in [(52, 90), (130, 104), (60, 172), (126, 166), (90, 84)]:
    ImageDraw.Draw(img).point((x, y), fill=(226, 160, 70))
c = up(img, P)
B.save(c, '17,5 – 18,5 s', 'Solo el logo, en pixel art', 'Todo se va a negro. Queda únicamente el logo de Juanito, armado en pixel art. Sin empaques y sin Noah.',
       '(logo en pixel art)', 'Último pixel que encaja: un "clic".')

# 9 · el logo pasa a normal + coming soon
c = Image.new('RGBA', (LW * P, LH * P), BLACK + (255,))
lw = 62 * P
logo = LOGO.resize((lw, round(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
c.alpha_composite(logo, (540 - lw // 2, 96 * P))
spaced(c, 'COMING SOON', font('montserrat', 'montserrat-latin-300-normal.woff', 40), 540, 96 * P + logo.height + 70, 20, CREAM)
B.save(c, '18,5 – 20 s', 'El logo pasa a normal', 'Los pixeles se afinan en tres saltos hasta volverse el logo normal, nítido. Debajo aparece "coming soon" en letra fina. Fin.',
       'COMING SOON', 'Una nota limpia que se sostiene y se apaga.')
B.close()
