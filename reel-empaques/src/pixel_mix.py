"""Idea D (mezcla): la ficha de color por variedad, toda en pixel art, que se "enciende" cuando Noah actua.

Todo el escenario se dibuja en una reticula real de pixeles (180 x 320, ampliada x6 sin suavizado).
Noah se pega encima con las ilustraciones aprobadas (solo recortadas).
Uso: python3 src/pixel_mix.py   -> storyboards/frames/d_XX.png + frames_d.json
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
A = os.path.join(ROOT, 'assets')
OUT = os.path.join(ROOT, 'storyboards', 'frames'); os.makedirs(OUT, exist_ok=True)
FONTS = os.path.join(ROOT, 'node_modules', '@fontsource')
SIZES = json.load(open(os.path.join(A, 'sprites', 'sizes.json')))

BLACK, CREAM, INK, ORANGE = (11, 10, 9), (243, 234, 217), (27, 22, 19), (224, 144, 63)
DIMTXT = (120, 112, 102)
VAR = {
    'java':     dict(name='JAVA', n='01', bag='cerezas', c=[(40, 84, 40), (132, 170, 60)]),
    'castillo': dict(name='CASTILLO', n='02', bag='colores', c=[(150, 30, 86), (234, 124, 30)]),
    'geisha':   dict(name='GEISHA', n='03', bag='casa_azul', c=[(26, 66, 122), (96, 154, 200)]),
    'bourbon':  dict(name='BOURBON', n='04', bag='casa_roja', c=[(124, 28, 24), (216, 90, 52)]),
}
B8 = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
               [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
               [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64.0


def font(pkg, file, size):
    return ImageFont.truetype(os.path.join(FONTS, pkg, 'files', file), size)


def F_title(size): return font('montserrat', 'montserrat-latin-900-normal.woff', size)
F_S = font('tiny5', 'tiny5-latin-400-normal.woff', 8)      # texto chico (5 px de alto)
F_M = font('tiny5', 'tiny5-latin-400-normal.woff', 16)     # texto mediano


def mix(a, b, k): return tuple(int(round(a[i] * (1 - k) + b[i] * k)) for i in range(3))


def lit_ramp(c1, c2):
    return [BLACK, mix(BLACK, c1, 0.5), c1, mix(c1, c2, 0.5), c2, mix(c2, CREAM, 0.55), CREAM]


OFF_RAMP = [BLACK, (17, 16, 15), (24, 22, 20), (30, 28, 26), (34, 31, 29)]


def backdrop(w, h, ramps, t0=0.42, t1=0.66):
    """Degradado en bandas con tramado (dither). ramps: una rampa por columna (misma anchura)."""
    yy, xx = np.mgrid[0:h, 0:w]
    t = yy / h + 0.012 * np.sin(xx / w * 2 * np.pi * 0.9 + 0.6) - 0.02 * (xx / w - 0.5)
    thr = B8[yy % 8, xx % 8]
    out = np.zeros((h, w, 3), np.uint8)
    cw = w // len(ramps)
    for ci, ramp in enumerate(ramps):
        r = np.array(ramp)
        u = np.clip((t - t0) / (t1 - t0), 0, 1) * (len(ramp) - 1)
        i = np.minimum(np.floor(u).astype(int), len(ramp) - 2)
        idx = i + ((u - i) > thr)
        sl = slice(ci * cw, (ci + 1) * cw if ci < len(ramps) - 1 else w)
        out[:, sl] = r[idx][:, sl]
    return Image.fromarray(out, 'RGB')


def bag_sprite(name, lit=True):
    im = Image.open(os.path.join(A, 'bags', f'{name}.png')).convert('RGBA')
    if lit:
        return im
    a = np.asarray(im).astype(float)
    lum = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11) / 255.0
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    tones = np.array([(20, 19, 18), (36, 33, 31), (54, 50, 46), (72, 67, 62)])
    u = np.clip(lum * 1.15, 0, 0.999) * (len(tones) - 1)
    i = np.minimum(np.floor(u).astype(int), len(tones) - 2)
    rgb = tones[i + ((u - i) > B8[yy % 8, xx % 8])]
    return Image.fromarray(np.dstack([rgb, a[..., 3]]).astype(np.uint8), 'RGBA')


def text(img, xy, s, f, fill, anchor='la'):
    d = ImageDraw.Draw(img); d.fontmode = '1'
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def title_font(name, maxw=150, top=30):
    for size in range(top, 12, -1):
        f = F_title(size)
        if f.getlength(name) <= maxw:
            return f
    return F_title(12)


def title(img, x, y, name, typed=None, lit=True, maxw=150, top=30):
    """Nombre de la variedad. typed = cuantas letras lleva puestas (None = todas)."""
    f = title_font(name, maxw, top)
    typed = len(name) if typed is None else typed
    asc = f.getbbox('H')
    cap_top, cap_bot = asc[1], asc[3]
    cx = x
    for i, ch in enumerate(name):
        wch = f.getlength(ch)
        if i < typed:
            text(img, (cx, y), ch, f, CREAM if lit else (176, 166, 150))
        else:                                   # letra que falta: una rayita apagada
            ImageDraw.Draw(img).rectangle([cx + 1, y + cap_bot - 2, cx + wch - 3, y + cap_bot - 1], fill=(52, 48, 44))
        cx += wch
    return cap_bot


def up(img, p): return img.resize((img.width * p, img.height * p), Image.NEAREST)


def noah(canvas, key, s, right=None, cx=None, bottom=1640):
    im = Image.open(os.path.join(A, 'sprites', f'noah_{key}.png')).convert('RGBA')
    w, h = round(im.width * s), round(im.height * s)
    im = im.resize((w, h), Image.LANCZOS)
    x = right - w if right is not None else round(cx - w / 2)
    canvas.alpha_composite(im, (x, bottom - h))


# ---------------- una ficha (180 x 320) ----------------
def card(v, lit=True, typed=None, line=None):
    d = VAR[v]
    img = backdrop(180, 320, [lit_ramp(*d['c']) if lit else OFF_RAMP]).convert('RGBA')
    img.alpha_composite(bag_sprite(d['bag'], lit), (54, 26))
    cap = title(img, 12, 158, d['name'], typed=typed, lit=lit)
    if lit:
        text(img, (13, 201), f"{d['n']} / 04", F_S, INK)
        text(img, (168, 201), '(new variety)', F_S, INK, 'ra')
        ImageDraw.Draw(img).point([(150, 150), (171, 205)], fill=INK)
        text(img, (12, 284), 'ORIGIN', F_S, INK)
        text(img, (168, 284), 'HUILA, COLOMBIA', F_S, INK, 'ra')
        if line:
            text(img, (12, 228), line, F_S, INK)
    return img


frames = []


def save(i, canvas, t, title_, es, txt, snd):
    fid = f'd_{i:02d}'
    canvas.convert('RGB').save(os.path.join(OUT, f'{fid}.png'))
    frames.append(dict(id=fid, idea='d', n=i, t=t, title=title_, es=es, text=txt, snd=snd))


# 1 · apagado: Noah se asoma
c = up(card('java', lit=False, typed=0), 6)
noah(c, 'peek', 0.42, right=1010, bottom=1690)
save(1, c, '0 – 2 s', 'Todo apagado', 'La ficha está apagada: el empaque y el nombre apenas se adivinan en gris. Noah se asoma por abajo. Es lo único a color.',
     '(nada todavía)', 'Silencio. Pasitos.')

# 2 · Noah ladra y pone las letras
c0 = card('java', lit=False, typed=2)
text(c0, (22, 232), 'woof!', F_M, CREAM)
text(c0, (62, 222), 'woof!', F_S, DIMTXT)
c = up(c0, 6)
noah(c, 'listen', 0.5, right=1010, bottom=1690)
save(2, c, '2 – 3,5 s', 'Un ladrido, una letra', 'Noah ladra y con cada ladrido aparece una letra del nombre: J, A, V, A. Igual que el letrero de tu referencia, pero lo arma él.',
     'J A _ _  ·  woof!', 'Un ladrido corto por letra, con un "clic" de letrero.')

# 3 · se enciende: Java
c = up(card('java', line='(my favorite.)'), 6)
noah(c, 'host', 0.38, right=1010, bottom=1690)
save(3, c, '3,5 – 6 s', 'Se enciende: Java', 'Con la última letra todo se enciende: el color sube como una luz, el empaque queda a todo color y aparece la variedad.',
     'JAVA · 01 / 04 · (new variety) · origin Huila, Colombia — Noah: (my favorite.)', 'Golpe de luz + nota.')

# 4-6 · las otras tres
rest = [('castillo', 'listen', 0.46, '(also my favorite.)', '6 – 9 s', 'Castillo', 'Cambia el color al magenta y naranja del empaque de colores. Noah ladra las letras de CASTILLO y se enciende.'),
        ('geisha', 'peek', 0.4, '(okay. this one.)', '9 – 12 s', 'Geisha', 'El azul de la casa. Mismo juego: ladridos, letras, luz.'),
        ('bourbon', 'sideeye', 0.4, "(...who's that dog?)", '12 – 15 s', 'Bourbon', 'El rojo de la casa. Noah descubre al perro pintado en el empaque y lo mira de reojo.')]
for k, (v, pose, s, line, t, nm, es) in enumerate(rest):
    c = up(card(v, line=line), 6)
    noah(c, pose, s, right=1010, bottom=1690)
    d = VAR[v]
    save(4 + k, c, t, f'Se enciende: {nm}', es, f"{d['name']} · {d['n']} / 04 — Noah: {line}", 'Ladridos + golpe de luz + nota.')

# 7 · se aleja: las cuatro fichas juntas (360 x 640, x3)
W, H = 360, 640
img = backdrop(W, H, [lit_ramp(*VAR[v]['c']) for v in VAR]).convert('RGBA')
for i, v in enumerate(VAR):
    d = VAR[v]
    img.alpha_composite(bag_sprite(d['bag']), (i * 90 + 9, 150))
    f = title_font(d['name'], 80, 16)
    text(img, (i * 90 + 45, 296), d['name'], f, CREAM, 'ma')
    text(img, (i * 90 + 45, 318), f"{d['n']} / 04", F_S, CREAM, 'ma')
text(img, (180, 96), 'FOUR NEW VARIETIES', F_M, CREAM, 'ma')
text(img, (180, 118), '(four new bags)', F_S, DIMTXT, 'ma')
text(img, (180, 436), 'New look. Noah approved.', F_M, INK, 'ma')
c = up(img, 3)
noah(c, 'mug', 0.42, cx=540, bottom=1740)
save(7, c, '15 – 17,5 s', 'Las cuatro juntas', 'La imagen se aleja y quedan las cuatro fichas lado a lado, cada una con su color. Noah abraza su taza.',
     'FOUR NEW VARIETIES · New look. Noah approved.', 'Las cuatro notas en acorde.')

# 8 · cierre: se apaga
img = backdrop(180, 320, [OFF_RAMP]).convert('RGBA')
text(img, (90, 160), 'COMING SOON', F_M, CREAM, 'ma')
text(img, (90, 182), '(green coffee - Huila, Colombia)', F_S, (176, 166, 150), 'ma')
text(img, (90, 196), '@juanitocoffee', F_S, ORANGE, 'ma')
c = up(img, 6)
logo = Image.open(os.path.join(A, 'logo_blanco.png')).convert('RGBA')
lw = 400; logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
c.alpha_composite(logo, (540 - lw // 2, 360))
noah(c, 'sleep', 0.44, cx=540, bottom=1660)
save(8, c, '17,5 – 20 s', 'Cierre', 'Se apaga la luz. Queda el logo y Noah ya dormido.',
     'COMING SOON · (green coffee - Huila, Colombia) · @juanitocoffee', 'La nota se apaga. Ronquido.')

json.dump(frames, open(os.path.join(OUT, 'frames_d.json'), 'w'), indent=1)
print('ok', len(frames))
