"""Prueba del final: el estudio animado de Noah junto a la tostadora, montado sobre el fondo.

Usa el GIF que entrego quien anima a Noah (fondo negro): le quita el negro del fondo y lo pega tal
cual, sin cambiarle el tamano mas que lo necesario.
Uso: python3 src/anim_end_test.py -> storyboards/prueba_final_tostadora.mp4
"""
import os, sys, subprocess, shutil
from collections import deque
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P, FPS, DUR, H0 = 180, 320, 6, 24, 6.0, 234
GLOW = (246, 228, 196)
C1, C2 = (104, 58, 22), (226, 160, 70)
yy, xx = np.mgrid[0:LH, 0:LW]
BAY = B8[yy % 8, xx % 8]
GIF = os.path.join(SB, 'noah_anim_privado', 'estudios', 'estudio_escucha.gif')
TMP = os.path.join(SB, '_anim_end'); shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)


def key_black(im):
    """Quita el negro del fondo (solo el que toca los bordes), sin tocar el contorno oscuro de Noah."""
    a = np.asarray(im.convert('RGBA')).copy()
    h, w = a.shape[:2]
    dark = a[..., :3].max(2) <= 10
    seen = np.zeros((h, w), bool)
    dq = deque([(y, x) for y in (0, h - 1) for x in range(w) if dark[y, x]] + [(y, x) for x in (0, w - 1) for y in range(h) if dark[y, x]])
    for y, x in dq:
        seen[y, x] = True
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and dark[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; dq.append((ny, nx))
    a[seen, 3] = 0
    return Image.fromarray(a, 'RGBA')


g = Image.open(GIF)
FR_, T_ = [], []
for i in range(g.n_frames):
    g.seek(i); FR_.append(key_black(g.convert('RGBA'))); T_.append(g.info.get('duration', 100) / 1000.0)
al = np.max([np.asarray(f)[..., 3] for f in FR_], axis=0) > 0
ys, xs = np.where(al); BOX = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
ENDS = np.cumsum(T_); LOOP = ENDS[-1]
# el momento en que la oreja se levanta: el primer cuadro con mas amarillo (las rayitas de alerta)
yel = [int(((np.asarray(f)[..., 0] > 200) & (np.asarray(f)[..., 2] < 90) & (np.asarray(f)[..., 3] > 0)).sum()) for f in FR_]
CRACK = float(([0] + list(ENDS))[int(np.argmax(np.array(yel) > min(yel) + 0.5 * (max(yel) - min(yel))))])
print('gif', len(FR_), 'cuadros,', round(LOOP, 2), 's; oreja arriba en', round(CRACK, 2), 's; caja', BOX)


def sky(drift):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, C1, .5), C1, mixc(C1, C2, .5), C2, mixc(C2, GLOW, .6), GLOW]
    rgb = dither_ramp(t, ramp, 0.37, H0 / LH + 0.02)
    for yc, amp, k, sp in [(H0 - 22, 3.0, 0.55, 1.0), (H0 - 46, 4.0, 0.35, -0.6)]:
        edge = yc + amp * np.sin((xx + drift * sp) / 13.0 + yc)
        band = (yy > edge) & (yy < edge + 9)
        dens = np.clip(1 - np.abs(yy - edge - 4.5) / 4.5, 0, 1) * k
        rgb[band & (dens > BAY)] = mixc(C2, GLOW, .72)
    return Image.fromarray(rgb, 'RGB').convert('RGBA')


def coffee():
    depth = yy - H0
    base, dark = mixc((46, 26, 15), C1, 0.14), (20, 11, 7)
    out = np.zeros((LH, LW, 4), np.uint8)
    out[..., :3] = np.where((np.clip(depth / (LH - H0), 0, 1) * 1.1 > BAY)[..., None], dark, base)
    out[(depth >= 3) & (depth < 18) & (yy % 2 == 0) & ((1 - (depth - 3) / 15.0) * 0.5 > BAY), :3] = mixc(C2, base, 0.62)
    out[(depth >= 0) & (depth < 3), :3] = (152, 100, 54)
    out[(depth >= 0) & (depth < 1), :3] = (218, 174, 116)
    out[..., 3] = (depth >= 0) * 255
    return Image.fromarray(out, 'RGBA')


COF = up(coffee(), P)
F_NOTE = font('montserrat', 'montserrat-latin-500-normal.woff', 22)
x1, y1, x2, y2 = BOX
S = 640 / (y2 - y1)                                           # Noah y la tostadora, unos 640 px de alto


def frame(t):
    img = sky(t * 5)
    tl = t % LOOP
    since = tl - CRACK
    if since >= 0:
        text(img, (90, 62), '(first crack!)', F_M, CREAM, 'ma')
    if since >= 0.7:
        s = 'this one is almost ready.'
        text(img, (90, 86), s[:int((since - 0.7) * 30)], F_S, CREAM, 'ma')
    c = up(img, P)
    c.alpha_composite(COF)
    f = FR_[int(np.searchsorted(ENDS, tl, side='right')) % len(FR_)].crop(BOX)
    f = f.resize((round(f.width * S), round(f.height * S)), Image.LANCZOS if abs(S - round(S)) > 0.02 else Image.NEAREST)
    c.alpha_composite(f, (540 - f.width // 2, H0 * P + 10 - f.height))
    ImageDraw.Draw(c).text((540, 1836), 'PRUEBA DE MOVIMIENTO', font=F_NOTE, fill=(120, 112, 102), anchor='ma')
    return c


n = int(DUR * FPS)
for i in range(n):
    frame(i / FPS).convert('RGB').save(os.path.join(TMP, f'{i:04d}.png'))
out = os.path.join(SB, 'prueba_final_tostadora.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(TMP, '%04d.png'),
                '-vf', 'fps=30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '14', '-preset', 'slow', '-movflags', '+faststart', out], check=True)
picks = [0.1, CRACK + 0.1, CRACK + 0.5, CRACK + 1.6]
sheet = Image.new('RGB', (len(picks) * 366 - 6, 640), (60, 60, 60))
for k, t in enumerate(picks):
    sheet.paste(Image.open(os.path.join(TMP, f'{min(int(t * FPS), n - 1):04d}.png')).resize((360, 640), Image.LANCZOS), (k * 366, 0))
sheet.save(os.path.join(SB, '_anim_check.png'))
shutil.rmtree(TMP)
print('ok', n, 'cuadros', round(os.path.getsize(out) / 1e6, 2), 'MB')
