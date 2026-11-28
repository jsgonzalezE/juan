"""Lee las animaciones de Noah que entrega quien lo anima y las deja listas para montar.

Acepta cualquier tamano: si los cuadros traen fondo liso en vez de transparente, lo quita; mide a
Noah en toda la animacion y lo ancla por las patas.  Uso como revision:
    python3 src/noah_anim.py [CARPETA]   -> informe + storyboards/noah_anim_revision.png
"""
import os, sys, glob
from collections import deque
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
DEFAULT = os.environ.get('NOAH_ANIM') or os.path.join(ROOT, 'noah_anim')


def _clear_flat_bg(im):
    """Si el cuadro no trae transparencia, quita el color liso que toca las esquinas."""
    a = np.asarray(im.convert('RGBA')).copy()
    if (a[..., 3] < 250).any():
        return Image.fromarray(a, 'RGBA'), False
    h, w = a.shape[:2]
    bg = a[0, 0, :3].astype(int)
    close = np.abs(a[..., :3].astype(int) - bg).sum(2) <= 24
    seen = np.zeros((h, w), bool)
    dq = deque((y, x) for y in (0, h - 1) for x in range(w) if close[y, x])
    dq.extend((y, x) for x in (0, w - 1) for y in range(h) if close[y, x])
    for y, x in dq:
        seen[y, x] = True
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and close[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; dq.append((ny, nx))
    a[seen, 3] = 0
    return Image.fromarray(a, 'RGBA'), True


def load(name, base=None):
    """Devuelve dict(frames, box, cleared) o None si esa animacion no existe todavia."""
    d = os.path.join(base or DEFAULT, name)
    files = sorted(glob.glob(os.path.join(d, '*.png')))
    if not files:
        return None
    frames, cleared = [], False
    for f in files:
        im, c = _clear_flat_bg(Image.open(f)); frames.append(im); cleared |= c
    size = frames[0].size
    frames = [f if f.size == size else f.resize(size, Image.NEAREST) for f in frames]
    al = np.max([np.asarray(f)[..., 3] for f in frames], axis=0) > 0
    ys, xs = np.where(al)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)   # Noah en toda la animacion
    return dict(name=name, frames=frames, box=box, size=size, cleared=cleared, files=files)


def place(canvas, anim, i, cx, feet_y, height):
    """Pega el cuadro i con Noah de `height` pixeles de alto, centrado en cx y con las patas en feet_y."""
    x1, y1, x2, y2 = anim['box']
    s = height / (y2 - y1)
    f = anim['frames'][i % len(anim['frames'])].crop(anim['box'])
    f = f.resize((max(1, round(f.width * s)), max(1, round(f.height * s))), Image.NEAREST)
    canvas.alpha_composite(f, (int(round(cx - f.width / 2)), int(round(feet_y - f.height))))


def place_exact(canvas, anim, i, cx, feet_y, scale, ax=64, ay=120):
    """Para cuadros en el formato acordado (128 x 128, centro en x=64, apoyo en y=120): amplia el cuadro
    entero por `scale` sin suavizar y hace coincidir ese punto con (cx, feet_y)."""
    f = anim['frames'][i % len(anim['frames'])]
    f = f.resize((max(1, round(f.width * scale)), max(1, round(f.height * scale))), Image.NEAREST)
    canvas.alpha_composite(f, (int(round(cx - ax * scale)), int(round(feet_y - ay * scale))))


def report(base=None):
    base = base or DEFAULT
    names = sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n))) if os.path.isdir(base) else []
    rows, anims = [], []
    for n in names:
        a = load(n, base)
        if not a:
            continue
        anims.append(a)
        cols = set()
        for f in a['frames']:
            px = np.asarray(f); cols |= set(map(tuple, px[px[..., 3] > 0][:, :3]))
        x1, y1, x2, y2 = a['box']
        rows.append(f"{n}: {len(a['frames'])} cuadros, {a['size'][0]}x{a['size'][1]}, Noah {x2 - x1}x{y2 - y1}, "
                    f"patas en fila {y2}, {len(cols)} colores, fondo {'liso (lo quite)' if a['cleared'] else 'transparente'}")
    return rows, anims


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    rows, anims = report(base)
    print('\n'.join(rows) if rows else 'Todavia no hay animaciones en ' + base)
    if anims:
        cell = 200
        sheet = Image.new('RGBA', (cell * max(len(a['frames']) for a in anims), cell * len(anims)), (40, 36, 32, 255))
        for r, a in enumerate(anims):
            for i in range(len(a['frames'])):
                place(sheet, a, i, i * cell + cell // 2, r * cell + cell - 14, 150)
        out = os.path.join(ROOT, 'storyboards', 'noah_anim_revision.png')
        sheet.convert('RGB').save(out); print(out)
