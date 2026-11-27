"""Recorta las ilustraciones pixel art de Noah (fondo blanco -> transparente).

No redibuja nada: solo quita el fondo blanco y las sombras grises del piso,
y separa cada ilustracion en piezas sueltas (Noah + objetos + destellos) para
poder usarlas sobre fondo negro.  Uso:  python3 prep_noah.py SRC_DIR OUT_DIR
"""
import sys, os, json
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def flood_bg(rgb):
    """Mascara del fondo: blanco puro + grises claros sin color (sombras, bordes suavizados)."""
    a = rgb.astype(int)
    mx, mn = a.max(2), a.min(2)
    white = mn >= 246
    grey = (mx - mn <= 26) & (mn >= 120)          # sombras y franja suavizada
    cream = (a[..., 0] - a[..., 2] >= 12)          # pelaje crema: no tocar
    shadow = (mn >= 120) & (mn < 210) & (mx - mn <= 42)   # sombra gris-calida del piso
    shadow[:820] = False                                   # solo abajo: arriba hay humo gris que si es dibujo
    passable = white | (grey & ~cream) | shadow
    h, w = passable.shape
    seen = np.zeros((h, w), bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if passable[y, x] and not seen[y, x]:
                seen[y, x] = True; dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if passable[y, x] and not seen[y, x]:
                seen[y, x] = True; dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and passable[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; dq.append((ny, nx))
    return seen


def components(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    boxes = []
    n = 0
    for y0 in range(h):
        row = np.where(mask[y0] & (lab[y0] == 0))[0]
        for x0 in row:
            if lab[y0, x0]:
                continue
            n += 1
            dq = deque([(y0, x0)]); lab[y0, x0] = n
            x1 = x2 = x0; y1 = y2 = y0; cnt = 0
            while dq:
                y, x = dq.popleft(); cnt += 1
                x1 = min(x1, x); x2 = max(x2, x); y1 = min(y1, y); y2 = max(y2, y)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n; dq.append((ny, nx))
            boxes.append(dict(id=n, box=[int(x1), int(y1), int(x2) + 1, int(y2) + 1], area=int(cnt)))
    return lab, boxes


meta = {}
for f in sorted(os.listdir(SRC)):
    if not f.endswith('.png'):
        continue
    name = f.replace('noah_pixel_', '').replace('.png', '')
    rgb = np.asarray(Image.open(os.path.join(SRC, f)).convert('RGB'))
    bg = flood_bg(rgb)
    fg = ~bg
    # quita motas sueltas
    lab, boxes = components(fg)
    boxes = [b for b in boxes if b['area'] >= 500]
    keep = np.isin(lab, [b['id'] for b in boxes])
    alpha = (keep * 255).astype(np.uint8)
    rgba = np.dstack([rgb, alpha])
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'{name}.png'))
    boxes.sort(key=lambda b: -b['area'])
    meta[name] = boxes
    for i, b in enumerate(boxes):
        x1, y1, x2, y2 = b['box']
        part = rgba.copy()
        part[..., 3] = np.where(lab == b['id'], 255, 0)
        Image.fromarray(part, 'RGBA').save(os.path.join(OUT, f'{name}__part{i}.png'))
    print(name, [(b['area'], b['box']) for b in boxes])
json.dump(meta, open(os.path.join(OUT, 'parts.json'), 'w'), indent=1)
