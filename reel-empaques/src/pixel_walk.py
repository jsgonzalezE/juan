"""Idea E (el recorrido): Noah camina de empaque en empaque y termina en la tostadora.

Los empaques ya no son la foto de la bolsa: son objetos de pixel art dentro del mundo de Noah.
El color del fondo cambia con cada variedad mientras avanza.
Uso: python3 src/pixel_walk.py  -> storyboards/idea_e_recorrido_panorama.png
                                    storyboards/frames/e_XX.png + frames_e.json
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
A = os.path.join(ROOT, 'assets')
SB = os.path.join(ROOT, 'storyboards')
OUT = os.path.join(SB, 'frames'); os.makedirs(OUT, exist_ok=True)
FONTS = os.path.join(ROOT, 'node_modules', '@fontsource')

BLACK, CREAM, INK, ORANGE = (11, 10, 9), (243, 234, 217), (27, 22, 19), (224, 144, 63)
OUTLINE = (36, 20, 20)
ST = [  # estaciones del recorrido
    dict(id='start', c=[(22, 20, 19), (30, 28, 26)], end=(36, 33, 31)),
    dict(id='java', name='JAVA', n='01', bag='cerezas', c=[(40, 84, 40), (132, 170, 60)], noah='host', s=0.38, line='(the new kid.)'),
    dict(id='castillo', name='CASTILLO', n='02', bag='colores', c=[(150, 30, 86), (234, 124, 30)], noah='listen', s=0.46, line='(the loud one.)'),
    dict(id='geisha', name='GEISHA', n='03', bag='casa_azul', c=[(26, 66, 122), (96, 154, 200)], noah='mug', s=0.40, line='(the fancy one.)'),
    dict(id='bourbon', name='BOURBON', n='04', bag='casa_roja', c=[(124, 28, 24), (216, 90, 52)], noah='sideeye', s=0.40, line="(...who's that dog?)"),
    dict(id='roaster', c=[(104, 58, 22), (226, 160, 70)], noah='roaster', s=0.46),
]
B8 = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
               [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
               [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64.0


def font(pkg, file, size): return ImageFont.truetype(os.path.join(FONTS, pkg, 'files', file), size)
def F_title(size): return font('montserrat', 'montserrat-latin-900-normal.woff', size)
F_S = font('tiny5', 'tiny5-latin-400-normal.woff', 8)
F_M = font('tiny5', 'tiny5-latin-400-normal.woff', 16)


def mixc(a, b, k): return np.asarray(a, float) * (1 - k) + np.asarray(b, float) * k


def ramp_cols(c1, c2, end):
    """Rampa de 7 tonos por columna. c1, c2, end: arreglos (w, 3)."""
    blk = np.broadcast_to(np.array(BLACK, float), c1.shape)
    return np.stack([blk, mixc(blk, c1, .5), c1, mixc(c1, c2, .5), c2, mixc(c2, end, .55), end])  # (7, w, 3)


def backdrop(w, h, c1, c2, end, t0, t1):
    yy, xx = np.mgrid[0:h, 0:w]
    t = yy / h + 0.012 * np.sin(xx / 180 * 2 * np.pi * 0.9 + 0.6)
    r = ramp_cols(c1, c2, end)
    u = np.clip((t - t0) / (t1 - t0), 0, 1) * 6
    i = np.minimum(np.floor(u).astype(int), 5)
    idx = i + ((u - i) > B8[yy % 8, xx % 8])
    return Image.fromarray(r[idx, xx].round().astype(np.uint8), 'RGB').convert('RGBA')


def flat(w, st, key): return np.broadcast_to(np.array(st.get(key, CREAM) if key == 'end' else st['c'][key], float), (w, 3)).copy()


def text(img, xy, s, f, fill, anchor='la'):
    d = ImageDraw.Draw(img); d.fontmode = '1'; d.text(xy, s, font=f, fill=fill, anchor=anchor)


def fit_title(name, maxw, top):
    for size in range(top, 10, -1):
        if F_title(size).getlength(name) <= maxw:
            return F_title(size)
    return F_title(10)


def bag_obj(name, w=56):
    """Empaque como objeto de pixel art: menos pixeles, menos colores y contorno oscuro como los objetos de Noah."""
    src = Image.open(os.path.join(A, 'bags', f'{name}.png')).convert('RGBA')
    h = round(src.height * w / src.width)
    rgb = src.convert('RGB').resize((w, h), Image.BOX).quantize(colors=20, method=Image.MEDIANCUT, dither=Image.NONE, kmeans=2).convert('RGB')
    al = src.split()[3].resize((w, h), Image.NEAREST)
    body = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    body.paste(rgb, (1, 1), al)
    edge = body.split()[3].filter(ImageFilter.MaxFilter(3))
    out = Image.new('RGBA', body.size, OUTLINE + (0,)); out.putalpha(edge)
    out.alpha_composite(body)
    return out


def shadow(img, cx, y, w):
    """Sombra en puntos bajo un objeto."""
    d = ImageDraw.Draw(img)
    for dy in range(3):
        for x in range(cx - w // 2 + dy * 3, cx + w // 2 - dy * 3):
            if (x + y + dy) % 2 == 0:
                d.point((x, y + dy), fill=(196, 184, 164))


def up(img, p): return img.resize((img.width * p, img.height * p), Image.NEAREST)


def noah(canvas, key, s, cx, bottom, flip=False):
    im = Image.open(os.path.join(A, 'sprites', f'noah_{key}.png')).convert('RGBA')
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.alpha_composite(im, (round(cx - im.width / 2), bottom - im.height))


def paws(img, x1, x2, y):
    """Huellitas: marcan por donde camina Noah (en el video va la animacion de caminar)."""
    d = ImageDraw.Draw(img)
    for k, x in enumerate(range(x1, x2, 7)):
        yy = y + (2 if k % 2 else 0)
        d.rectangle([x, yy, x + 1, yy + 1], fill=(150, 138, 120))


# ================= 1) PANORAMA: todo el recorrido de una vez =================
SW, PH, P = 150, 236, 3
PW = SW * len(ST)
cent = np.array([(i + 0.5) * SW for i in range(len(ST))])
xs = np.arange(PW)
def lerp_key(fn):
    vals = np.array([fn(s) for s in ST], float)
    return np.stack([np.interp(xs, cent, vals[:, k]) for k in range(3)], axis=1)
GROUND = 200
pano = backdrop(PW, PH, lerp_key(lambda s: s['c'][0]), lerp_key(lambda s: s['c'][1]), lerp_key(lambda s: s.get('end', CREAM)), 0.30, 0.66)
ImageDraw.Draw(pano).line([(0, GROUND), (PW, GROUND)], fill=INK)
text(pano, (int(cent[0]), 50), 'FOUR NEW', F_M, CREAM, 'ma')
text(pano, (int(cent[0]), 66), 'VARIETIES', F_M, CREAM, 'ma')
text(pano, (int(cent[0]), 88), '(follow Noah.)', F_S, (176, 166, 150), 'ma')
for i, s in enumerate(ST):
    cx = int(cent[i])
    if 'bag' in s:
        b = bag_obj(s['bag'])
        bx = cx - 66
        shadow(pano, bx + b.width // 2, GROUND + 1, b.width + 6)
        pano.alpha_composite(b, (bx, GROUND - b.height))
        text(pano, (cx, 34), f"{s['n']} / 04", F_S, CREAM, 'ma')
        text(pano, (cx, 44), s['name'], fit_title(s['name'], 120, 22), CREAM, 'ma')
        text(pano, (cx, 72), s['line'], F_S, CREAM, 'ma')
    if s['id'] == 'roaster':
        text(pano, (cx, 34), '(first crack? I heard it first.)', F_S, CREAM, 'ma')
        text(pano, (cx, 46), 'COMING SOON', fit_title('COMING SOON', 130, 18), CREAM, 'ma')
paws(pano, 34, PW - 70, GROUND + 9)      # una sola fila de huellitas: el camino completo
pano = up(pano, P)
for i, s in enumerate(ST):
    cx = int(cent[i]) * P
    if s['id'] == 'start':
        noah(pano, 'host', 0.19, cx - 60, GROUND * P + 4)
    elif s['id'] == 'roaster':
        noah(pano, 'roaster', 0.26, cx, GROUND * P + 4)
    else:
        noah(pano, s['noah'], s['s'] * 0.5, cx + 118, GROUND * P + 4)
pano.convert('RGB').save(os.path.join(SB, 'idea_e_recorrido_panorama.png'))

# ================= 2) CUADROS VERTICALES: lo que ve el celular en cada parada =================
frames = []
LW, LH, G = 180, 320, 262


def scene(st, nxt=None):
    """Fondo de una parada. nxt: si viene otra estacion, su empaque se asoma por la derecha."""
    img = backdrop(LW, LH, flat(LW, st, 0), flat(LW, st, 1), flat(LW, st, 'end'), 0.42, 0.66)
    ImageDraw.Draw(img).line([(0, G), (LW, G)], fill=INK)
    return img


def save(i, canvas, t, title_, es, txt, snd):
    fid = f'e_{i:02d}'
    canvas.convert('RGB').save(os.path.join(OUT, f'{fid}.png'))
    frames.append(dict(id=fid, idea='e', n=i, t=t, title=title_, es=es, text=txt, snd=snd))


# 1 · arranca
img = scene(ST[0])
text(img, (90, 96), 'FOUR NEW VARIETIES', F_M, CREAM, 'ma')
text(img, (90, 118), '(follow Noah.)', F_S, (176, 166, 150), 'ma')
b = bag_obj('cerezas', 66)
img.alpha_composite(b, (156, G - b.height))          # el primer empaque ya se asoma por la derecha
paws(img, 96, 150, G + 10)
c = up(img, 6)
noah(c, 'host', 0.38, 300, G * 6 + 6)
save(1, c, '0 – 2,5 s', 'Noah arranca', 'Todo oscuro. Noah entra caminando hacia la derecha; el primer empaque ya se asoma en el borde.',
     'FOUR NEW VARIETIES · (follow Noah.)', 'Pasitos. Empieza una base suave.')

# 2-5 · una parada por variedad
times = ['2,5 – 6 s', '6 – 9 s', '9 – 12 s', '12 – 15 s']
desc = ['Noah llega al primer empaque y se detiene. El fondo se pinta del verde de las hojas. Aparece la variedad y Noah la presenta.',
        'Sigue caminando; el color cambia al magenta y naranja. Segundo empaque, segunda variedad. Noah levanta la oreja.',
        'El color pasa al azul de la casa. Tercer empaque. Noah abraza su taza.',
        'El color pasa al rojo. Cuarto empaque: Noah ve al perro pintado y lo mira de reojo.']
for k, s in enumerate(ST[1:5]):
    img = scene(s)
    b = bag_obj(s['bag'], 66)
    bx = 16
    shadow(img, bx + b.width // 2, G + 1, b.width + 8)
    img.alpha_composite(b, (bx, G - b.height))
    text(img, (13, 40), f"{s['n']} / 04", F_S, CREAM)
    text(img, (12, 50), s['name'], fit_title(s['name'], 156, 30), CREAM)
    text(img, (13, 92), s['line'], F_M, CREAM)
    paws(img, 0, 16, G + 10)
    paws(img, 150, 180, G + 10)
    c = up(img, 6)
    noah(c, s['noah'], s['s'], 770, G * 6 + 6)
    save(2 + k, c, times[k], f"Parada: {s['name'].capitalize()}", desc[k], f"{s['n']} / 04 · {s['name']} · {s['line']}", 'Nota al llegar. Los pasitos se detienen.')

# 6 · la tostadora
s = ST[5]
img = scene(s)
text(img, (90, 66), '(first crack?', F_M, CREAM, 'ma')
text(img, (90, 86), 'I heard it first.)', F_M, CREAM, 'ma')
shadow(img, 90, G + 1, 110)
paws(img, 0, 30, G + 10)
c = up(img, 6)
noah(c, 'roaster', 0.62, 540, G * 6 + 6)
save(6, c, '15 – 17,5 s', 'Final: Noah tostador', 'Al final del camino está la tostadora. Noah se sienta al lado y levanta la oreja: ya casi.',
     '(first crack? I heard it first.)', 'Tambor de tostadora girando. Un "crack".')

# 7 · cierre
img = scene(s)
text(img, (90, 150), 'COMING SOON', fit_title('COMING SOON', 150, 22), CREAM, 'ma')
text(img, (90, 180), '(green coffee - Huila, Colombia)', F_S, INK, 'ma')
text(img, (90, 194), '@juanitocoffee', F_S, INK, 'ma')
c = up(img, 6)
logo = Image.open(os.path.join(A, 'logo_blanco.png')).convert('RGBA')
lw = 360; logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
c.alpha_composite(logo, (540 - lw // 2, 330))
noah(c, 'roaster', 0.34, 540, G * 6 + 6)
save(7, c, '17,5 – 20 s', 'Cierre', 'Mismo lugar, la cámara se queda. Entra el logo y los datos.',
     'COMING SOON · (green coffee - Huila, Colombia) · @juanitocoffee', 'Segundo "crack". Fin.')

json.dump(frames, open(os.path.join(OUT, 'frames_e.json'), 'w'), indent=1)
print('ok', len(frames), pano.size)
