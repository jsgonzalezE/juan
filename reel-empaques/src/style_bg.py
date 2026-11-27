"""Fondos con degradado y grano (negro -> color de la variedad -> crema), uno por variedad.
Uso: python3 style_bg.py   -> assets/style/bg_<variedad>.jpg
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'style'); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
BLACK, CREAM = (11, 10, 9), (241, 231, 214)
# color tomado del dibujo de cada empaque
VAR = {
    'java':     [(52, 96, 48), (132, 168, 62)],      # hojas de cafe
    'castillo': [(150, 30, 86), (232, 122, 30)],     # magenta y naranja del empaque de colores
    'geisha':   [(30, 72, 128), (92, 150, 196)],     # azul de la casa
    'bourbon':  [(128, 30, 26), (214, 88, 52)],      # rojo de la casa
}
rng = np.random.default_rng(7)
for name, (c1, c2) in VAR.items():
    stops = [(0.00, BLACK), (0.40, BLACK), (0.50, c1), (0.57, c2), (0.66, CREAM), (1.00, CREAM)]
    yy, xx = np.mgrid[0:H, 0:W]
    t = yy / H + 0.012 * np.sin(xx / W * 2 * np.pi * 0.9 + 0.6) - 0.02 * (xx / W - 0.5)
    t = t + rng.normal(0, 0.012, (H, W))             # el grano tambien desordena el borde del degradado
    t = np.clip(t, 0, 1)
    img = np.zeros((H, W, 3))
    for (p0, a), (p1, b) in zip(stops[:-1], stops[1:]):
        m = (t >= p0) & (t <= p1)
        k = ((t - p0) / max(p1 - p0, 1e-6))[..., None]
        k = k * k * (3 - 2 * k)
        seg = np.array(a) * (1 - k) + np.array(b) * k
        img[m] = seg[m]
    img += rng.normal(0, 7, (H, W, 1))               # grano
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f'bg_{name}.jpg'), quality=92)
    print(name)
