"""Copias livianas de los cuadros para el PDF (540 x 960).

Los cuadros en pixel art estan ampliados x6, asi que reducirlos a la mitad con BOX deja
cada pixel de arte en un bloque exacto de 3 x 3: no se emborronan.
Uso: python3 src/pdf_images.py  -> storyboards/pdf/img/
"""
import os, glob
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, '..', 'storyboards')
OUT = os.path.join(SB, 'pdf', 'img'); os.makedirs(OUT, exist_ok=True)

n = 0
for f in sorted(glob.glob(os.path.join(SB, 'frames', '*.png'))):
    im = Image.open(f).convert('RGB').resize((540, 960), Image.BOX)
    im.save(os.path.join(OUT, os.path.basename(f)), optimize=True); n += 1
for f in sorted(glob.glob(os.path.join(SB, 'estilo', 'ficha_*.png'))):   # fichas con grano: mejor en JPEG
    im = Image.open(f).convert('RGB').resize((540, 960), Image.LANCZOS)
    im.save(os.path.join(OUT, os.path.basename(f).replace('.png', '.jpg')), quality=88, subsampling=0); n += 1
pano = os.path.join(SB, 'idea_e_recorrido_panorama.png')
if os.path.exists(pano):
    Image.open(pano).convert('RGB').save(os.path.join(OUT, 'panorama_e.png'), optimize=True); n += 1
print('ok', n)
