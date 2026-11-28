"""Prueba de movimiento de una actuacion de Noah hecha sobre la ilustracion original (1254 px).

Monta los cuadros nativos transparentes, sin reescalar (1 pixel del dibujo = 1 pixel del video),
sobre el piso plano de las llegadas. Usa los tiempos del manifest.json del animador.

Uso: python3 src/anim_nap_test.py [carpeta] [salida.mp4] [vueltas] [hundido]
     carpeta por defecto: storyboards/noah_anim_privado/ronda6/siesta
     hundido: pixeles que la figura queda por debajo de la linea del piso, asomada detras del
              horizonte (para los bustos, que no tienen patas). Por defecto 0: apoyada en el piso.
"""
import os, sys, json, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SB, 'noah_anim_privado', 'ronda6', 'siesta')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SB, 'prueba_siesta.mp4')
LOOPS = int(sys.argv[3]) if len(sys.argv) > 3 else 2
SINK = int(sys.argv[4]) if len(sys.argv) > 4 else 0
LW, LH, P, FPS, H0 = 180, 320, 6, 60, 234
C1, C2, GLOW = (34, 40, 78), (120, 98, 142), (244, 212, 170)      # cielo de siesta: azul noche a rosa calido
yy, xx = np.mgrid[0:LH, 0:LW]
BAY = B8[yy % 8, xx % 8]
F_NOTE = font('montserrat', 'montserrat-latin-500-normal.woff', 22)

man = json.load(open(os.path.join(SRC, 'manifest.json')))['frames']
SEQ = [(Image.open(os.path.join(SRC, m['file'])).convert('RGBA'), m['ms'] / 1000.0) for m in man]
TOTAL = sum(d for _, d in SEQ)
alpha = np.zeros(np.asarray(SEQ[0][0]).shape[:2], bool)
for f, _ in SEQ:
    alpha |= np.asarray(f)[..., 3] > 0
ys, xs = np.where(alpha)
APOYO = int(np.where(np.asarray(SEQ[0][0])[..., 3] > 0)[0].max()) + 1   # fila siguiente a la de apoyo, en el cuadro 01
CX = (xs.min() + xs.max()) / 2
FEET = H0 * P + 3                                                 # misma linea de apoyo que en las llegadas


def sky(drift):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, C1, .5), C1, mixc(C1, C2, .5), C2, mixc(C2, GLOW, .6), GLOW]
    rgb = dither_ramp(t, ramp, 0.37, H0 / LH + 0.02)
    for yc, amp, k, sp in [(H0 - 22, 3.0, 0.55, 1.0), (H0 - 46, 4.0, 0.35, -0.6)]:
        edge = yc + amp * np.sin((xx + drift * sp) / 13.0 + yc)
        band = (yy > edge) & (yy < edge + 9)
        dens = np.clip(1 - np.abs(yy - edge - 4.5) / 4.5, 0, 1) * k
        rgb[band & (dens > BAY)] = mixc(C2, GLOW, .72)
    return rgb


def coffee(rgb):
    depth = yy - H0
    base, dark = mixc((46, 26, 15), C1, 0.14), (20, 11, 7)
    k = np.clip(depth / (LH - H0), 0, 1)
    g = np.where((k * 1.1 > BAY)[..., None], dark, base).astype(np.uint8)
    streak = (depth >= 5) & (depth < 22) & (B8[yy % 8, (xx % 24 // 3 + yy // 3) % 8] < 0.09) & ((yy // 2) % 3 == 0)
    g[streak] = (96, 58, 30)
    sheen = (depth >= 3) & (depth < 18) & (yy % 2 == 0) & ((1 - (depth - 3) / 15.0) * 0.5 > BAY)
    g[sheen] = mixc(C2, base, 0.62)
    g[(depth >= 0) & (depth < 3)] = (152, 100, 54)
    g[(depth >= 0) & (depth < 1)] = (218, 174, 116)
    rgb[depth >= 0] = g[depth >= 0]
    return rgb


def pick(t):
    t %= TOTAL
    acc = 0.0
    for i, (f, d) in enumerate(SEQ):
        acc += d
        if t < acc - 1e-9:
            return i, f
    return len(SEQ) - 1, SEQ[-1][0]


def scene(step, f):
    """Cielo, Noah y piso. Si va hundido, el piso se pinta encima y tapa el corte del busto."""
    rgb = sky(step * 0.4)
    pos = (int(round(540 - CX)), FEET - APOYO + SINK)             # sin reescalar: pixel por pixel
    if SINK:
        c = up(Image.fromarray(rgb, 'RGB'), P).convert('RGBA')
        c.alpha_composite(f, pos)
        ground = np.asarray(up(Image.fromarray(coffee(rgb.copy()), 'RGB'), P).convert('RGBA')).copy()
        ground[:H0 * P, :, 3] = 0
        c.alpha_composite(Image.fromarray(ground, 'RGBA'))
    else:
        c = up(Image.fromarray(coffee(rgb), 'RGB'), P).convert('RGBA')
        c.alpha_composite(f, pos)
    ImageDraw.Draw(c).text((540, 1836), 'PRUEBA PRIVADA DE MOVIMIENTO', font=F_NOTE, fill=(120, 112, 102), anchor='ma')
    return c


def render():
    n = int(round(TOTAL * LOOPS * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '14', '-movflags', '+faststart', OUT],
                          stdin=subprocess.PIPE)
    cache = {}
    for k in range(n):
        t = k / FPS
        step = int(t * 12)                                        # la bruma se mueve a 12 pasos por segundo
        i, f = pick(t)
        key = (step, i)
        if key not in cache:
            cache.clear()
            cache[key] = scene(step, f).convert('RGB').tobytes()
        ff.stdin.write(cache[key])
    ff.stdin.close(); ff.wait()
    print(f'{OUT}: {len(SEQ)} dibujos, {TOTAL:.2f} s por vuelta x {LOOPS}, {n} cuadros a {FPS} fps, '
          f'figura {xs.max() - xs.min() + 1} x {ys.max() - ys.min() + 1} px, apoyo en y={FEET}')


if __name__ == '__main__':
    render()
