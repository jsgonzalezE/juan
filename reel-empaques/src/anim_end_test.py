"""Prueba del final: Noah escucha junto a la tostadora, suena el primer crack y da el sobresalto.

Usa los cuadros PNG con transparencia y la tabla de tiempos de quien anima a Noah (lienzo de
1254 x 1254, apoyo en la fila 1052, la maquina en su propia capa). Se pegan a tamano real, sin
reescalar.  Empalme: la escucha se sostiene en el dibujo 16 y de ahi corta al primer dibujo de crack.
Uso: python3 src/anim_end_test.py -> storyboards/prueba_final_tostadora.mp4
"""
import os, sys, csv, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P, FPS, DUR, H0 = 180, 320, 6, 24, 7.5, 234
GLOW = (246, 228, 196)
C1, C2 = (104, 58, 22), (226, 160, 70)
yy, xx = np.mgrid[0:LH, 0:LW]
BAY = B8[yy % 8, xx % 8]
PRIV = os.path.join(SB, 'noah_anim_privado')
TMP = os.path.join(SB, '_anim_end'); shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)

rows = list(csv.DictReader(open(os.path.join(PRIV, 'tiempos.csv'), encoding='utf-8-sig')))
SEQ = {a: [(Image.open(os.path.join(PRIV, r['archivo'])).convert('RGBA'), int(r['duracion_ms']) / 1000.0)
           for r in rows if r['accion'] == a] for a in ('tostando', 'crack')}
SUPPORT = int(rows[0]['apoyo_y'])
MACHINE = Image.open(os.path.join(PRIV, 'tostadora', 'maquina_alineada.png')).convert('RGBA')
LISTEN = SEQ['tostando'][:16]                                 # hasta el dibujo 16: oreja erguida, se sostiene
T_CRACK = sum(d for _, d in LISTEN)                           # ahi suena el crack y corta al sobresalto
al = np.max([np.asarray(f)[..., 3] for f, _ in SEQ['tostando'] + SEQ['crack']] + [np.asarray(MACHINE)[..., 3]], axis=0) > 0
xs = np.where(al.any(0))[0]; ys = np.where(al.any(1))[0]
OX = 540 - (xs.min() + xs.max() + 1) // 2                      # centra a Noah con su maquina
OY = H0 * P + 10 - SUPPORT                                     # el apoyo cae sobre el piso
print('escucha', len(LISTEN), 'dibujos; crack en', round(T_CRACK, 2), 's; caja x', xs.min(), xs.max(), 'y', ys.min(), ys.max())


def pick(seq, t, hold=True):
    acc = 0.0
    for f, d in seq:
        acc += d
        if t < acc:
            return f
    return seq[-1][0]


def sky(drift, flash):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    c2 = mixc(C2, GLOW, 0.5 * flash)
    ramp = [BLACK, mixc(BLACK, C1, .5), C1, mixc(C1, c2, .5), c2, mixc(c2, GLOW, .6), GLOW]
    rgb = dither_ramp(t, ramp, 0.37 - 0.03 * flash, H0 / LH + 0.02)
    for yc, amp, k, sp in [(H0 - 22, 3.0, 0.55, 1.0), (H0 - 46, 4.0, 0.35, -0.6)]:
        edge = yc + amp * np.sin((xx + drift * sp) / 13.0 + yc)
        band = (yy > edge) & (yy < edge + 9)
        dens = np.clip(1 - np.abs(yy - edge - 4.5) / 4.5, 0, 1) * k
        rgb[band & (dens > BAY)] = mixc(c2, GLOW, .72)
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
BEANS = [(motif(53, 10), 142, -70, -210), (motif(56, 9), 150, 40, -250), (motif(25, 10), 136, -20, -290), (motif(53, 8), 146, 90, -190)]


def frame(t):
    since = t - T_CRACK
    flash = max(0.0, 1 - since / 0.5) if since >= 0 else 0.0
    img = sky(t * 5, flash)
    if since >= 0:
        text(img, (90, 62), '(first crack!)', F_M, CREAM, 'ma')
    if since >= 1.0:
        s = 'this one is almost ready.'
        text(img, (90, 86), s[:int((since - 1.0) * 30)], F_S, CREAM, 'ma')
    if 0 <= since < 1.3:                                      # granos que saltan de la tostadora
        for m, bx, vx, vy in BEANS:
            x = bx + vx * since / 6.0
            y = H0 - 62 + (vy * since + 420 * since * since) / 6.0
            if y < H0 - 4:
                img.alpha_composite(m, (int(round(x)), int(round(y))))
    c = up(img, P)
    c.alpha_composite(COF)
    jx = int(6 * np.sin(since * 60)) if 0 <= since < 0.25 else 0   # la maquina se sacude con el crack
    c.alpha_composite(MACHINE, (OX + jx, OY))
    f = pick(LISTEN, t) if since < 0 else pick(SEQ['crack'], since)
    c.alpha_composite(f, (OX, OY))
    ImageDraw.Draw(c).text((540, 1836), 'PRUEBA DE MOVIMIENTO', font=F_NOTE, fill=(120, 112, 102), anchor='ma')
    return c


n = int(DUR * FPS)
for i in range(n):
    frame(i / FPS).convert('RGB').save(os.path.join(TMP, f'{i:04d}.png'))
out = os.path.join(SB, 'prueba_final_tostadora.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(TMP, '%04d.png'),
                '-vf', 'fps=30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '14', '-preset', 'slow', '-movflags', '+faststart', out], check=True)
picks = [0.2, 1.2, T_CRACK - 0.05, T_CRACK + 0.02, T_CRACK + 0.3, T_CRACK + 0.55, T_CRACK + 0.8, T_CRACK + 1.6, T_CRACK + 2.4]
sheet = Image.new('RGB', (len(picks) * 306 - 6, 533), (60, 60, 60))
for k, t in enumerate(picks):
    sheet.paste(Image.open(os.path.join(TMP, f'{min(int(t * FPS), n - 1):04d}.png')).resize((300, 533), Image.LANCZOS), (k * 306, 0))
sheet.save(os.path.join(SB, '_anim_check.png'))
# empalme: dibujo 16 de la escucha contra el primero de crack
a16, c1 = np.asarray(SEQ['tostando'][15][0]).astype(int), np.asarray(SEQ['crack'][0][0]).astype(int)
diff = (np.abs(a16 - c1).sum(2) > 40)
print('empalme 16 -> crack_01: pixeles distintos', int(diff.sum()), 'de', int((a16[..., 3] > 0).sum()), 'visibles')
shutil.rmtree(TMP)
print('ok', n, 'cuadros', round(os.path.getsize(out) / 1e6, 2), 'MB')
