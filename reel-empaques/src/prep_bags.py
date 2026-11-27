"""Convierte las fotos de los empaques a pixel art (a color, sin esconder nada).

Uso: python3 prep_bags.py PAQUETE_DIR OUT_DIR
Genera, por cada empaque, un PNG pequeno (1 pixel de arte = 1 pixel de imagen)
que luego se amplia sin suavizado (nearest) en el storyboard / video.
"""
import sys, os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

PK, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

BAGS = {
    'cerezas':   ('02_empaques/empaque_acuarela_cerezas.png',          (4, 3, 4, 4)),
    'colores':   ('02_empaques/empaque_colores_CASTILLO.png',          (5, 3, 6, 9)),
    'casa_azul': ('02_empaques/empaque_acuarela_casa_azul.png',        (4, 3, 4, 4)),
    'casa_roja': ('02_empaques/empaque_acuarela_casa_roja_perro.png',  (4, 3, 4, 4)),
    'recolector':('02_empaques/empaque_acuarela_recolector_VERDE_gusta_menos.png', (5, 3, 6, 6)),
}


def pixelate(im, w, colors=40, sat=1.22, con=1.08, h=None):
    h = h or round(im.height * w / im.width)
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(con)
    small = im.resize((w * 3, h * 3), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 80, 2))
    small = small.resize((w, h), Image.BOX)
    q = small.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE, kmeans=3)
    return q.convert('RGB')


def bag_mask(w, h, r=4):
    """Silueta de bolsa con esquinas redondeadas en escalera (pixel art)."""
    m = np.ones((h, w), bool)
    for y in range(r):
        for x in range(r):
            if (r - x - 0.5) ** 2 + (r - y - 0.5) ** 2 > r * r + 1:
                m[y, x] = m[y, w - 1 - x] = m[h - 1 - y, x] = m[h - 1 - y, w - 1 - x] = False
    return m


for name, (rel, (l, t, r, b)) in BAGS.items():
    src = Image.open(os.path.join(PK, rel)).convert('RGB')
    W, H = src.size
    src = src.crop((round(W * l / 100), round(H * t / 100), W - round(W * r / 100), H - round(H * b / 100)))
    for w in (72,):
        px = pixelate(src, w, h=122)   # todas las bolsas del mismo tamano: 72 x 122
        a = np.asarray(px).copy()
        h = a.shape[0]
        m = bag_mask(w, h, r=max(3, w // 20))
        rgba = np.dstack([a, (m * 255).astype(np.uint8)])
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'{name}.png'))
    print(name, src.size, '->', (w, h))
