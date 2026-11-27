"""Prueba de movimiento del fondo: escena 1 (camina, horizonte curvo) -> llegada a Java (plano, de cerca).

Solo se anima el fondo: horizonte, cielo, empaque, brillo, ambiente y texto. Noah es un marcador
(ilustracion fija) hasta que lleguen sus animaciones.
Uso: python3 src/anim_test.py -> storyboards/prueba_movimiento_fondo.mp4
"""
import os, sys, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P, FPS, DUR = 180, 320, 6, 12, 7.5
GLOW = (246, 228, 196)
DIM = [(22, 20, 19), (40, 36, 32), (86, 76, 64)]
GREEN = [(40, 84, 40), (132, 170, 60), GLOW]
yy, xx = np.mgrid[0:LH, 0:LW]
BAY = B8[yy % 8, xx % 8]
XC = (LW - 1) / 2
TMP = os.path.join(SB, '_anim'); shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)


def lerp(a, b, k): return a + (b - a) * k
def smooth(k): k = min(max(k, 0.0), 1.0); return k * k * (3 - 2 * k)
def ease_out(k): k = min(max(k, 0.0), 1.0); return 1 - (1 - k) ** 3
def mix3(a, b, k): return tuple(int(round(lerp(a[i], b[i], k))) for i in range(3))


def ground(x, h0, curv): return h0 + curv * (np.asarray(x, float) - XC) ** 2 / 2


def sky(c1, c2, glow, h0, mist, drift):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, c1, .5), c1, mixc(c1, c2, .5), c2, mixc(c2, glow, .6), glow]
    rgb = dither_ramp(t, ramp, 0.37, h0 / LH + 0.02)
    if mist > 0:
        for yc, amp, k, sp in [(h0 - 22, 3.0, 0.55, 1.0), (h0 - 46, 4.0, 0.35, -0.6)]:
            edge = yc + amp * np.sin((xx + drift * sp) / 13.0 + yc)
            band = (yy > edge) & (yy < edge + 9)
            dens = np.clip(1 - np.abs(yy - edge - 4.5) / 4.5, 0, 1) * k * mist
            rgb[band & (dens > BAY)] = mixc(c2, glow, .72)
    return Image.fromarray(rgb, 'RGB').convert('RGBA')


def coffee(c1, c2, h0, curv, lit, scroll):
    depth = yy - ground(xx, h0, curv)
    base = mix3((26, 20, 17), mixc((46, 26, 15), c1, 0.14), lit)
    dark = mix3((14, 12, 11), (20, 11, 7), lit)
    out = np.zeros((LH, LW, 4), np.uint8)
    k = np.clip(depth / (LH - h0), 0, 1)
    out[..., :3] = np.where((k * 1.1 > BAY)[..., None], dark, base)
    sx = (xx + int(scroll)) % 8                               # las vetas se corren: el mundo gira
    streak = (depth >= 5) & (depth < 22) & (B8[yy % 8, (sx + yy // 3) % 8] < 0.09) & ((yy // 2) % 3 == 0)
    out[streak, :3] = mix3((44, 36, 30), (96, 58, 30), lit)
    sheen = (depth >= 3) & (depth < 18) & (yy % 2 == 0) & ((1 - (depth - 3) / 15.0) * 0.5 * lit > BAY)
    out[sheen, :3] = mixc(c2, base, 0.62)
    out[(depth >= 0) & (depth < 3), :3] = mix3((58, 48, 40), (152, 100, 54), lit)
    out[(depth >= 0) & (depth < 1), :3] = mix3((84, 72, 60), (218, 174, 116), lit)
    out[..., 3] = (depth >= 0) * 255
    return Image.fromarray(out, 'RGBA')


def halo(img, c1, c2, glow, cx, cy, r, power):
    a = np.asarray(img).copy()
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2)
    f = np.clip(1 - d / r, 0, 1) * (yy >= 108) * power
    a[(f * 0.9 > BAY) & (d < r), :3] = mixc(c1, glow, .45)
    a[(f * 0.9 > BAY + 0.3) & (d < r), :3] = mixc(c2, glow, .8)
    a[(f > 0.72) & (d < r), :3] = glow
    img.paste(Image.fromarray(a, 'RGBA'))


BAGS = {w: bag_obj('cerezas', w) for w in range(62, 73)}
MOT = [(motif(10, 76), -20, 106, -1), (motif(13, 26), 84, 98, 0), (motif(57, 9), 160, 96, 0), (motif(58, 8), 92, 150, 0)]
NOAH = Image.open(os.path.join(A, 'sprites', 'noah_host.png')).convert('RGBA')
F_TITLE = fit_title('JAVA', 156, 30)
F_NOTE = font('montserrat', 'montserrat-latin-500-normal.woff', 22)


def frame(t):
    walk = smooth(t / 2.4)                                    # 0..1 durante la caminata
    q = smooth((t - 2.4) / 1.0)                               # 0..1: se aplana y la camara se acerca
    arr = t - 3.4                                             # segundos desde la llegada
    lit = lerp(0.0, 0.6, walk ** 1.5) if t < 2.4 else lerp(0.6, 1.0, q)
    c1, c2, glow = (mix3(DIM[i], GREEN[i], lit) for i in range(3))
    h0, curv = lerp(212, 234, q), lerp(1 / 300.0, 0.0, q)
    scroll = t * 16 if t < 2.4 else 2.4 * 16 + (t - 2.4) * 16 * (1 - q) * 0.5

    img = sky(c1, c2, glow, h0, mist=q, drift=t * 5)
    if arr > 0:                                               # el ambiente entra por los bordes y luego flota
        for i, (m, mx, my, side) in enumerate(MOT):
            k = ease_out((arr - i * 0.15) / 0.9)
            if k <= 0:
                continue
            dx = (1 - k) * (-70 if side < 0 else 0)
            dy = (1 - k) * (0 if side < 0 else -26) + 1.6 * np.sin(t * 1.3 + i * 1.7)
            img.alpha_composite(m, (int(round(mx + dx)), int(round(my + dy))))
    # el empaque sube por detras del horizonte y al llegar queda completo
    bw = int(round(lerp(62, 72, q)))
    b = BAGS[bw]
    bx = lerp(lerp(170, 150, walk), 136, q)
    sunk = lerp(lerp(120, 62, walk), 2, q)
    top = ground(bx, h0, curv) + sunk - b.height
    halo(img, c1, c2, glow, bx, top + lerp(18, 34, q), lerp(74, 88, q), lerp(0.35 + 0.35 * walk, 1.0, q))
    img.alpha_composite(b, (int(round(bx - b.width / 2)), int(round(top))))
    # textos
    if 0.4 < t < 2.5:
        text(img, (90, 78), 'FOUR NEW VARIETIES'[:int((t - 0.4) * 30)], F_M, CREAM, 'ma')
        if t > 1.2:
            text(img, (90, 100), '(follow Noah.)', F_S, SOFT, 'ma')
    if arr > 0.1:
        text(img, (13, 30), '01 / 04', F_S, CREAM)
        text(img, (12, 40), 'JAVA'[:int((arr - 0.1) * 10) + 1], F_TITLE, CREAM)
    if arr > 0.9:
        text(img, (13, 80), '(the new kid.)'[:int((arr - 0.9) * 26)], F_M, CREAM)
    img.alpha_composite(coffee(c1, c2, h0, curv, lit, scroll))
    c = up(img, P)
    # Noah: marcador fijo. Sube y baja un poco al caminar y da un saltito al llegar.
    s = lerp(0.46, 0.58, q)
    nx = lerp(44, 45, q)
    n = NOAH.resize((round(NOAH.width * s), round(NOAH.height * s)), Image.LANCZOS)
    bob = (6 if int(t * 4) % 2 else 0) if t < 2.9 else 0
    hop = int(40 * max(0.0, np.sin(np.pi * arr / 0.35))) if 0 < arr < 0.35 else 0
    c.alpha_composite(n, (int(round(nx * P - n.width / 2)), int(round(ground(nx, h0, curv) * P + 8 - n.height - bob - hop))))
    ImageDraw.Draw(c).text((540, 1836), 'PRUEBA DE FONDO  ·  NOAH ES UN MARCADOR', font=F_NOTE, fill=(120, 112, 102), anchor='ma')
    return c


n = int(DUR * FPS)
for i in range(n):
    frame(i / FPS).convert('RGB').save(os.path.join(TMP, f'{i:04d}.png'))
out = os.path.join(SB, 'prueba_movimiento_fondo.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(TMP, '%04d.png'),
                '-vf', 'fps=30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '14', '-preset', 'slow', '-movflags', '+faststart', out], check=True)
# hoja de control: 8 momentos
picks = [0.2, 1.4, 2.3, 2.8, 3.2, 3.6, 4.6, 7.0]
sheet = Image.new('RGB', (len(picks) * 276 - 6, 480), (60, 60, 60))
for k, t in enumerate(picks):
    sheet.paste(Image.open(os.path.join(TMP, f'{int(t * FPS):04d}.png')).resize((270, 480), Image.BOX), (k * 276, 0))
sheet.save(os.path.join(SB, '_anim_check.png'))
shutil.rmtree(TMP)
print('ok', n, 'cuadros', round(os.path.getsize(out) / 1e6, 2), 'MB')
