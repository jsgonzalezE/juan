"""Recorta los dibujos sueltos del diseno oscuro de la marca (flores, cerezas, granos...) para
usarlos como referencias de sabor flotando en el cielo.  Uso: python3 prep_motifs.py PAQUETE_DIR
"""
import sys, os, json
from collections import deque
import numpy as np
from PIL import Image

PK = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'motifs'); os.makedirs(OUT, exist_ok=True)
im = Image.open(os.path.join(PK, '02_empaques/mockups_originales/pack_dark_front.jpg')).convert('RGB')
a = np.asarray(im).astype(int)
bg = np.median(a[:40, :40].reshape(-1, 3), axis=0)
fg = np.abs(a - bg).sum(2) > 70
h, w = fg.shape
lab = np.zeros((h, w), np.int32); comps = []; n = 0
for y0 in range(0, h, 2):
    for x0 in np.where(fg[y0] & (lab[y0] == 0))[0]:
        if lab[y0, x0]:
            continue
        n += 1; dq = deque([(y0, x0)]); lab[y0, x0] = n
        x1 = x2 = x0; y1 = y2 = y0; cnt = 0
        while dq:
            y, x = dq.popleft(); cnt += 1
            x1 = min(x1, x); x2 = max(x2, x); y1 = min(y1, y); y2 = max(y2, y)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and fg[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n; dq.append((ny, nx))
        if cnt > 900:
            comps.append((cnt, n, (x1, y1, x2 + 1, y2 + 1)))
comps.sort(reverse=True)
meta = []
for k, (cnt, cid, box) in enumerate(comps[:60]):
    x1, y1, x2, y2 = box
    rgba = np.dstack([a[y1:y2, x1:x2], (lab[y1:y2, x1:x2] == cid) * 255]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'm{k:02d}.png'))
    col = a[y1:y2, x1:x2][lab[y1:y2, x1:x2] == cid].mean(0).round().astype(int).tolist()
    meta.append(dict(k=k, area=int(cnt), box=[int(v) for v in box], color=col))
json.dump(meta, open(os.path.join(OUT, 'motifs.json'), 'w'))
print(len(comps), 'piezas;', im.size, 'fondo', bg)
