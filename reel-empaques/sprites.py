"""Small procedural pixel-art sprites (RGBA float arrays) for the teaser."""
import math

import numpy as np
from PIL import Image, ImageDraw

CREAM = (251, 240, 220)
PETAL_SHADE = (226, 208, 182)
POLLEN = (242, 193, 78)
STAMEN = (240, 150, 50)
LEAF = (86, 150, 72)
LEAF_DARK = (52, 104, 50)
BRANCH = (120, 82, 56)
COFFEE = (59, 36, 24)
CREMA = (176, 104, 58)


def _canvas(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _arr(im):
    return np.asarray(im).astype(np.float32) / 255.0


def _petal(d, cx, cy, ang, length, width, fill):
    pts_l, pts_r = [], []
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        r = math.sin(math.pi * min(1.0, t * 1.05)) * width * (0.55 + 0.45 * t)
        px, py = cx + dx * length * t, cy + dy * length * t
        pts_l.append((px + nx * r, py + ny * r))
        pts_r.append((px - nx * r, py - ny * r))
    d.polygon(pts_l + pts_r[::-1], fill=fill)


def flower(n=41, bloom=1.0, rot=0.0, petals=5):
    """White star-shaped coffee blossom. bloom in [0,1]."""
    im, d = _canvas(n, n)
    c = (n - 1) / 2
    if bloom <= 0:
        return _arr(im)
    L = (n / 2 - 1.5) * (0.25 + 0.75 * bloom)
    wd = L * 0.30
    for k in range(petals):
        a = rot + k * 2 * math.pi / petals - math.pi / 2
        _petal(d, c, c, a, L, wd, CREAM + (255,))
        # soft shading strip along one side of each petal
        _petal(d, c + math.cos(a + 0.5) * 0.8, c + math.sin(a + 0.5) * 0.8, a, L * 0.8, wd * 0.35,
               PETAL_SHADE + (255,))
    # stamens between petals
    if bloom > 0.5:
        for k in range(petals):
            a = rot + (k + 0.5) * 2 * math.pi / petals - math.pi / 2
            r = L * 0.55 * (bloom - 0.5) * 2
            x, y = c + math.cos(a) * r, c + math.sin(a) * r
            d.line([(c, c), (x, y)], fill=STAMEN + (255,), width=1)
            d.point((x, y), fill=POLLEN + (255,))
    rc = max(1.0, L * 0.16)
    d.ellipse((c - rc, c - rc, c + rc, c + rc), fill=POLLEN + (255,))
    return _arr(im)


def leaf(w=24, h=12, flip=False):
    im, d = _canvas(w, h)
    pts_t, pts_b = [], []
    for i in range(w):
        t = i / (w - 1)
        r = math.sin(math.pi * t) ** 0.8 * (h / 2 - 0.5)
        pts_t.append((i, h / 2 - r))
        pts_b.append((i, h / 2 + r))
    d.polygon(pts_t + pts_b[::-1], fill=LEAF + (255,))
    d.line([(1, h / 2), (w - 2, h / 2)], fill=LEAF_DARK + (255,))
    for i in range(3, w - 3, 4):
        d.line([(i, h / 2), (i + 2, h / 2 - h * 0.22)], fill=LEAF_DARK + (255,))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return _arr(im)


RIPE = [(108, 168, 72), (176, 190, 64), (236, 168, 52), (214, 74, 44), (160, 24, 44)]


def ripe_color(r):
    r = min(max(r, 0.0), 1.0) * (len(RIPE) - 1)
    i = min(int(r), len(RIPE) - 2)
    f = r - i
    a, b = np.array(RIPE[i]), np.array(RIPE[i + 1])
    return tuple(int(v) for v in a + (b - a) * f)


NODES = [(15, 15), (26, 26), (37, 37)]
CLUSTER = [(-4, -1), (0, -5), (4, 0), (0, 4), (-3, 5)]


def cherries(n=48, ripeness=0.0):
    """A coffee branch with clusters of cherries at the nodes, ripening green -> red."""
    im, d = _canvas(n, n)
    d.line([(2, 2), (46, 46)], fill=BRANCH + (255,), width=2)
    for i, (nx, ny) in enumerate(NODES):
        if i % 2 == 0:
            lf = Image.fromarray((leaf(18, 9) * 255).astype(np.uint8)).rotate(30, expand=True)
            im.alpha_composite(lf, (max(0, nx - 22), min(n - 16, ny + 1)))
        else:
            lf = Image.fromarray((leaf(18, 9, True) * 255).astype(np.uint8)).rotate(30, expand=True)
            im.alpha_composite(lf, (min(n - 22, nx + 3), max(0, ny - 17)))
    d = ImageDraw.Draw(im)
    k = 0
    for nx, ny in NODES:
        for ox, oy in CLUSTER:
            x, y = nx + ox, ny + oy
            r = ripeness * 1.3 - ((k * 7) % 5) * 0.06
            col = ripe_color(r)
            shade = tuple(int(v * 0.55) for v in col)
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=col + (255,), outline=shade + (255,))
            d.point((x - 1, y - 1), fill=(255, 245, 225, 230))
            k += 1
    return _arr(im)


def bean(w=18, h=24, color=(150, 90, 50)):
    im, d = _canvas(w, h)
    c = np.array(color)
    dark = tuple(int(v) for v in c * 0.55)
    mid = tuple(int(v) for v in c)
    light = tuple(int(min(255, v * 1.25 + 20)) for v in c)
    d.ellipse((1, 1, w - 2, h - 2), fill=dark + (255,))
    d.ellipse((2, 2, w - 3, h - 3), fill=mid + (255,))
    d.ellipse((4, 3, w // 2, h // 2), fill=light + (255,))
    # S-shaped crease
    pts = []
    for i in range(3, h - 3):
        t = (i - 3) / (h - 7)
        pts.append((w / 2 - 0.5 + 1.6 * math.sin(t * math.pi * 2), i))
    d.line(pts, fill=dark + (255,), width=1)
    return _arr(im)


def cup(w=56, h=40, band=(242, 147, 43)):
    im, d = _canvas(w, h)
    shade = PETAL_SHADE
    # saucer
    d.ellipse((2, h - 10, w - 6, h - 1), fill=shade + (255,))
    d.ellipse((5, h - 9, w - 9, h - 3), fill=CREAM + (255,))
    # handle
    d.ellipse((w - 19, 10, w - 3, 26), outline=CREAM + (255,), width=3)
    # body
    body = [(7, 6), (w - 13, 6), (w - 14, 18), (w - 18, 28), (w - 24, h - 7), (20, h - 7),
            (14, 28), (10, 18)]
    d.polygon(body, fill=CREAM + (255,))
    d.polygon([(w - 15, 9), (w - 13, 6), (w - 14, 18), (w - 18, 28), (w - 21, 30)],
              fill=shade + (255,))
    d.rectangle((9, 15, w - 14, 19), fill=band + (255,))
    # coffee surface
    d.ellipse((7, 3, w - 13, 10), fill=CREMA + (255,))
    d.ellipse((9, 4, w - 15, 9), fill=COFFEE + (255,))
    return _arr(im)


def pouch(w=40, h=56):
    """Stand-up pouch silhouette: returns (outline_rgba, interior_mask)."""
    mk = Image.new("L", (w, h), 0)
    dm = ImageDraw.Draw(mk)
    shape = [(4, 1), (w - 5, 1), (w - 5, h - 9), (w - 6, h - 5), (w - 9, h - 2),
             (8, h - 2), (5, h - 5), (4, h - 9)]
    dm.polygon(shape, fill=255)
    mask = np.asarray(mk).astype(np.float32) / 255
    er = mask.copy()
    er[1:-1, 1:-1] = np.minimum.reduce([mask[1:-1, 1:-1], mask[:-2, 1:-1], mask[2:, 1:-1],
                                         mask[1:-1, :-2], mask[1:-1, 2:]])
    edge = (mask > 0.5) & (er < 0.5)
    rgba = np.zeros((h, w, 4), np.float32)
    cream = np.array(CREAM + (255,)) / 255
    rgba[edge] = cream
    # crimped top seal
    rgba[7, 5:w - 5] = cream
    for x in range(6, w - 6, 2):
        rgba[3:6, x] = np.array(PETAL_SHADE + (200,)) / 255
    # tear notches
    rgba[4, 4:6] = 0
    rgba[4, w - 6:w - 4] = 0
    # bottom gusset curve
    for x in range(8, w - 8):
        yy = int(round(h - 9 + 2.5 * math.cos((x - w / 2) / (w / 2 - 8) * math.pi / 2)))
        rgba[yy, x] = np.array(PETAL_SHADE + (220,)) / 255
    inner = (er > 0.5).astype(np.float32)
    inner[:8] = 0
    return rgba, inner


def _ascii(rows, color):
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.float32)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#":
                a[y, x] = np.array(color + (255,)) / 255
    return a


LOCK = [
    "...######...",
    "..########..",
    ".###....###.",
    ".##......##.",
    ".##......##.",
    ".##......##.",
    "############",
    "############",
    "#####..#####",
    "#####..#####",
    "######.#####",
    "######.#####",
    "############",
    "############",
]


def lock(color=CREAM):
    return _ascii(LOCK, color)


ICONS = {
    "bloom": ["....###....", "...#####...", "...#####...", ".###.#.###.", "#####.#####",
              "#####.#####", ".###.#.###.", "...#####...", "...#####...", "....###....",
              "..........."],
    "origin": ["...........", "...........", "....#......", "...###.....", "..#####.#..",
               "..######.#.", ".#########.", ".##########", "###########", "###########",
               "..........."],
    "cherry": [".......##..", "......#.##.", ".....#.....", "....#.#....", "...#...#...",
               "..#.....#..", ".###...###.", "#####.#####", "#####.#####", "#####.#####",
               ".###...###."],
    "bean": ["...#####...", "..###.###..", ".####.####.", ".###.#####.", ".###.#####.",
             ".####.####.", ".#####.###.", ".#####.###.", ".####.####.", "..###.###..",
             "...#####..."],
    "cup": ["...........", "..#..#..#..", "...#..#..#.", "...........", "########...",
            "########.##", "########..#", "########.##", ".######....", "..####.....",
            "###########"],
    "pack": ["..#######..", "..#######..", "...........", "..#######..", "..#######..",
             ".#########.", ".#########.", ".#########.", ".#########.", ".#########.",
             "..#######.."],
}


def icon(kind, color=CREAM):
    return _ascii(ICONS[kind], color)
