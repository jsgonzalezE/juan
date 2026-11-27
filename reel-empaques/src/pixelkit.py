"""Piezas comunes para los borradores en pixel art (reticula real, ampliada sin suavizado)."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
A = os.path.join(ROOT, 'assets')
SB = os.path.join(ROOT, 'storyboards')
FR = os.path.join(SB, 'frames'); os.makedirs(FR, exist_ok=True)
FONTS = os.path.join(ROOT, 'node_modules', '@fontsource')

BLACK, CREAM, INK, ORANGE = (11, 10, 9), (243, 234, 217), (27, 22, 19), (224, 144, 63)
SOFT = (176, 166, 150)
OUTLINE = (36, 20, 20)
B8 = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
               [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
               [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64.0


def font(pkg, file, size): return ImageFont.truetype(os.path.join(FONTS, pkg, 'files', file), size)
def F_title(size): return font('montserrat', 'montserrat-latin-900-normal.woff', size)
F_S = font('tiny5', 'tiny5-latin-400-normal.woff', 8)
F_M = font('tiny5', 'tiny5-latin-400-normal.woff', 16)


def mixc(a, b, k): return tuple(int(round(a[i] * (1 - k) + b[i] * k)) for i in range(3))


def text(img, xy, s, f, fill, anchor='la'):
    d = ImageDraw.Draw(img); d.fontmode = '1'; d.text(xy, s, font=f, fill=fill, anchor=anchor)


def fit_title(name, maxw, top):
    for size in range(top, 10, -1):
        if F_title(size).getlength(name) <= maxw:
            return F_title(size)
    return F_title(10)


def outline(body):
    """Contorno oscuro de 1 px, como los objetos de las ilustraciones de Noah."""
    big = Image.new('RGBA', (body.width + 2, body.height + 2), (0, 0, 0, 0)); big.alpha_composite(body, (1, 1))
    edge = big.split()[3].filter(ImageFilter.MaxFilter(3))
    out = Image.new('RGBA', big.size, OUTLINE + (0,)); out.putalpha(edge); out.alpha_composite(big)
    return out


def bag_obj(name, w=56):
    """Empaque como objeto de pixel art: menos pixeles, menos colores y contorno oscuro."""
    src = Image.open(os.path.join(A, 'bags', f'{name}.png')).convert('RGBA')
    h = round(src.height * w / src.width)
    rgb = src.convert('RGB').resize((w, h), Image.BOX).quantize(colors=20, method=Image.MEDIANCUT, dither=Image.NONE, kmeans=2).convert('RGB')
    body = Image.new('RGBA', (w, h), (0, 0, 0, 0)); body.paste(rgb, (0, 0), src.split()[3].resize((w, h), Image.NEAREST))
    return outline(body)


def motif(k, w):
    """Dibujo suelto del diseno de la marca (flor, cereza, grano...), llevado a pixel art."""
    src = Image.open(os.path.join(A, 'motifs', f'm{k:02d}.png')).convert('RGBA')
    h = max(3, round(src.height * w / src.width))
    small = src.resize((w, h), Image.BOX)
    al = small.split()[3].point(lambda v: 255 if v >= 120 else 0)
    rgb = small.convert('RGB').quantize(colors=5, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')
    body = Image.new('RGBA', (w, h), (0, 0, 0, 0)); body.paste(rgb, (0, 0), al)
    return outline(body)


def up(img, p): return img.resize((img.width * p, img.height * p), Image.NEAREST)


def noah(canvas, key, s, cx, bottom, flip=False):
    im = Image.open(os.path.join(A, 'sprites', f'noah_{key}.png')).convert('RGBA')
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.alpha_composite(im, (round(cx - im.width / 2), bottom - im.height))
    return im.size


def dither_ramp(t, ramp, t0, t1):
    """Degradado vertical en bandas con tramado. t: campo 0..1; ramp: lista de colores."""
    h, w = t.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.array(ramp, float)
    u = np.clip((t - t0) / (t1 - t0), 0, 1) * (len(ramp) - 1)
    i = np.minimum(np.floor(u).astype(int), len(ramp) - 2)
    return r[i + ((u - i) > B8[yy % 8, xx % 8])].round().astype(np.uint8)


class Board:
    """Junta los cuadros de una idea y escribe su indice para la lamina."""
    def __init__(self, idea): self.idea, self.frames = idea, []
    def save(self, canvas, t, title, es, txt, snd):
        i = len(self.frames) + 1
        fid = f'{self.idea}_{i:02d}'
        canvas.convert('RGB').save(os.path.join(FR, f'{fid}.png'))
        self.frames.append(dict(id=fid, idea=self.idea, n=i, t=t, title=title, es=es, text=txt, snd=snd))
    def close(self):
        json.dump(self.frames, open(os.path.join(FR, f'frames_{self.idea}.json'), 'w'), indent=1)
        print('ok', self.idea, len(self.frames))
