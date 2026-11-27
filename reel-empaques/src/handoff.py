"""Arma el paquete para quien anima a Noah: encargo, storyboard, fondos sin Noah y guias.

Uso: PLATES=1 python3 src/pixel_cup.py && python3 src/pixel_cup.py && python3 src/handoff.py
  -> storyboards/paquete_para_chatgpt.zip
"""
import os, json, shutil, zipfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SB = os.path.join(ROOT, 'storyboards'); FR = os.path.join(SB, 'frames')
OUT = os.path.join(SB, 'paquete_para_chatgpt')
shutil.rmtree(OUT, ignore_errors=True)
for d in ('1_storyboard', '2_fondos_sin_noah', '3_guias_donde_va_noah', '4_poses_de_referencia'):
    os.makedirs(os.path.join(OUT, d))

shutil.copy(os.path.join(ROOT, 'ENCARGO_ANIMACIONES_NOAH.md'), os.path.join(OUT, 'LEEME_ENCARGO.md'))
pdf = os.path.join(SB, 'Juanito_Coffee_idea_F_afinada.pdf')
if os.path.exists(pdf):
    shutil.copy(pdf, os.path.join(OUT, '1_storyboard'))
slots = json.load(open(os.path.join(FR, 'slots.json')))
by = {s['frame']: s for s in slots}
for i in range(1, 11):
    f = os.path.join(FR, f'f_{i:02d}.png')
    Image.open(f).convert('RGB').resize((540, 960), Image.BOX).save(os.path.join(OUT, '1_storyboard', f'cuadro_{i:02d}.png'), optimize=True)
    plate = Image.open(os.path.join(FR, f'p_{i:02d}.png')).convert('RGB')
    plate.resize((540, 960), Image.BOX).save(os.path.join(OUT, '2_fondos_sin_noah', f'fondo_{i:02d}.png'), optimize=True)
    if i in by:                                              # guia: recuadro donde va Noah y linea de las patas
        s = by[i]; g = plate.copy(); d = ImageDraw.Draw(g)
        x, y, w, h = s['x'], s['y'], s['w'], s['h']
        for k in range(0, w, 24):
            d.line([(x + k, y), (x + min(k + 12, w), y)], fill=(255, 220, 0), width=4)
        for k in range(0, h, 24):
            d.line([(x, y + k), (x, y + min(k + 12, h))], fill=(255, 220, 0), width=4)
            d.line([(x + w, y + k), (x + w, y + min(k + 12, h))], fill=(255, 220, 0), width=4)
        d.line([(max(x - 40, 0), s['feet_y']), (x + w + 40, s['feet_y'])], fill=(255, 60, 60), width=4)
        g.resize((540, 960), Image.LANCZOS).save(os.path.join(OUT, '3_guias_donde_va_noah', f'guia_{i:02d}.png'), optimize=True)
for k in sorted({s['pose'] for s in slots}):
    shutil.copy(os.path.join(ROOT, 'assets', 'sprites', f'noah_{k}.png'), os.path.join(OUT, '4_poses_de_referencia', f'marcador_{k}.png'))
json.dump(slots, open(os.path.join(OUT, '3_guias_donde_va_noah', 'posiciones.json'), 'w'), indent=1)
z = os.path.join(SB, 'paquete_para_chatgpt.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            p = os.path.join(root, f); zf.write(p, os.path.relpath(p, SB))
print('ok', round(os.path.getsize(z) / 1e6, 1), 'MB')
