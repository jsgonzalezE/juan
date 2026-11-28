"""Arma los sprites que usan los storyboards.

  python3 make_sprites.py PAQUETE_DIR
- assets/sprites/noah_*.png : Noah recortado (ilustraciones del cliente, sin redibujar)
- assets/sprites/det_*.png  : detalles de las acuarelas en pixel art
- assets/sprites/ui_*.png   : piezas de escenografia (lampara, luz en puntos, burbuja)
"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

PK = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '..', 'assets')
OUT = os.path.join(A, 'sprites'); os.makedirs(OUT, exist_ok=True)
parts = json.load(open(os.path.join(A, 'noah', 'parts.json')))
RIM = (86, 74, 64)      # borde tenue para que las orejas oscuras no se pierdan en el negro
RIM_W = 5


def load(name, idx=None):
    if idx is None:
        return Image.open(os.path.join(A, 'noah', f'{name}.png')).convert('RGBA')
    base = None
    for i in idx:
        im = Image.open(os.path.join(A, 'noah', f'{name}__part{i}.png')).convert('RGBA')
        base = im if base is None else Image.alpha_composite(base, im)
    return base


def rim(im, w=RIM_W, col=RIM):
    a = im.split()[3]
    d = a.filter(ImageFilter.MaxFilter(2 * w + 1))
    base = Image.new('RGBA', im.size, col + (0,)); base.putalpha(d)
    base.alpha_composite(im)
    return base


def save_noah(key, name, idx=None):
    im = load(name, idx)
    im = rim(im)
    box = im.getbbox()
    im = im.crop(box)
    im.save(os.path.join(OUT, f'noah_{key}.png'))
    return im.size


sizes = {}
sizes['host'] = save_noah('host', 'barista')
sizes['sideeye'] = save_noah('sideeye', 'sugar', [0])
sizes['sugar'] = save_noah('sugar', 'sugar')
sizes['listen'] = save_noah('listen', 'roaster', [0, 3, 4, 5])
sizes['roaster'] = save_noah('roaster', 'roaster')
sizes['peek'] = save_noah('peek', 'cupping', [0])
sizes['cupping'] = save_noah('cupping', 'cupping')
sizes['sleep'] = save_noah('sleep', 'sleep')
sizes['sleepbody'] = save_noah('sleepbody', 'sleep', [0])
sizes['moka'] = save_noah('moka', 'moka')
sizes['mug'] = save_noah('mug', 'mug')
sizes['sack'] = save_noah('sack', 'sack')
sizes['gift'] = save_noah('gift', 'gift')
sizes['bag'] = save_noah('bag', 'bag')
sizes['cap'] = save_noah('cap', 'cap')


# ---------- detalles de las ilustraciones de los empaques, en pixel art ----------
def pixelate(im, w, colors=36, sat=1.25, con=1.1):
    h = round(im.height * w / im.width)
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(con)
    s = im.resize((w * 3, h * 3), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 90, 2))
    s = s.resize((w, h), Image.BOX)
    return s.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE, kmeans=3).convert('RGB')


DET = {
    'cerezas': ('03_acuarelas/acuarela_cerezas.jpg', (150, 960, 950, 1560)),
    'fiesta': ('02_empaques/empaque_colores_CASTILLO.png', (196, 470, 460, 668)),
    'mula': ('03_acuarelas/acuarela_mula_casa_azul.jpg', (470, 960, 1030, 1380)),
    'perro': ('03_acuarelas/acuarela_mula_perro_casa_roja.jpg', (350, 1020, 690, 1275)),
}
for k, (rel, box) in DET.items():
    im = Image.open(os.path.join(PK, rel)).convert('RGB').crop(box)
    px = pixelate(im, 72)
    px.save(os.path.join(OUT, f'det_{k}.png'))
    sizes['det_' + k] = px.size

# ---------- escenografia ----------
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def dither(field, col):
    h, w = field.shape
    thr = BAYER[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4]
    on = field > thr
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = on * 255
    return Image.fromarray(out, 'RGBA')


# halo de luz (puntos finos) detras de una pieza colgada: 210 x 240 px de arte a 4 px
h, w = 240, 210
yy, xx = np.mgrid[0:h, 0:w]
f = np.clip(1 - ((xx - w / 2) / (w * 0.50)) ** 2 - ((yy - 30) / (h * 0.86)) ** 2, 0, 1) ** 1.6 * 0.5
dither(f, (70, 55, 38)).save(os.path.join(OUT, 'ui_halo.png'))
# charco de luz en el piso
h, w = 14, 110
yy, xx = np.mgrid[0:h, 0:w]
f = np.clip(1 - ((xx - w / 2) / (w * 0.5)) ** 2 - ((yy - h / 2) / (h * 0.5)) ** 2, 0, 1) * 0.6
dither(f, (62, 49, 35)).save(os.path.join(OUT, 'ui_pool.png'))

# lampara de cuadro (pixel): brazo + pantalla
lamp = np.zeros((7, 34, 4), np.uint8)
brass, dark, glow = (201, 162, 90, 255), (120, 92, 44, 255), (255, 226, 160, 255)
lamp[0:3, 16:18] = dark
lamp[3:5, 2:32] = brass
lamp[5, 3:31] = dark
lamp[6, 5:29] = glow
Image.fromarray(lamp, 'RGBA').save(os.path.join(OUT, 'ui_lamp.png'))


# burbuja de sueno: union de circulos, contorno de 1 px
def bubble(w, h, circles, fill=(19, 17, 15, 255), line=(214, 204, 188, 255)):
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.zeros((h, w), bool)
    for cx, cy, r in circles:
        m |= (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    er = m.copy()
    er[1:, :] &= m[:-1, :]; er[:-1, :] &= m[1:, :]; er[:, 1:] &= m[:, :-1]; er[:, :-1] &= m[:, 1:]
    out = np.zeros((h, w, 4), np.uint8)
    out[m] = line
    out[er] = fill
    return Image.fromarray(out, 'RGBA')


W, H = 166, 176
cs = [(83, 88, 64)]
for i in range(13):                      # nube: cuerpo grande + bultos en el borde
    a = 2 * math.pi * i / 13 + 0.2
    cs.append((round(83 + 60 * math.cos(a)), round(88 + 66 * math.sin(a)), 19 + (i % 3)))
bubble(W, H, cs).save(os.path.join(OUT, 'ui_bubble.png'))
bubble(14, 14, [(7, 7, 6)]).save(os.path.join(OUT, 'ui_dot_l.png'))
bubble(9, 9, [(4, 4, 4)]).save(os.path.join(OUT, 'ui_dot_m.png'))
bubble(5, 5, [(2, 2, 2)]).save(os.path.join(OUT, 'ui_dot_s.png'))

for k in ('cerezas', 'colores', 'casa_azul', 'casa_roja'):
    sizes['bag_' + k] = Image.open(os.path.join(A, 'bags', f'{k}.png')).size
json.dump(sizes, open(os.path.join(OUT, 'sizes.json'), 'w'), indent=1)
print(sizes)
