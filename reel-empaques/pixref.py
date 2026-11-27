"""Noah sprites cut straight out of the client's own pixel-art illustrations (assets/noah_pix).

Nothing is redrawn: each picture is cut from its white background, given a thin cream rim so it
reads on black, and split into the figure and its loose accents (motion ticks, sparkles, steam)
so the accents can blink.
"""
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "noah_pix")
RIM = (236, 224, 204)
CREAM = (246, 236, 218)
RIM_PX = 13                      # rim width in source pixels (about one art "pixel")

# variants that keep only part of a picture (polygon in source px): Noah without the prop
VARIANTS = {
    "sugar_noah": ("sugar", [(0, 0), (848, 0), (848, 800), (728, 800), (728, 1254), (0, 1254)]),
}


def _outside(candidates):
    """Background = near-white pixels connected to the image border."""
    im = Image.fromarray(np.pad(~candidates, 1).astype(np.uint8) * 255, "L").copy()
    ImageDraw.floodfill(im, (0, 0), 128)
    return np.asarray(im)[1:-1, 1:-1] == 128


@lru_cache(maxsize=None)
def layers(name):
    """(rgb float, figure alpha, accent alpha) at source resolution."""
    key, poly = VARIANTS.get(name, (name, None))
    im = Image.open(os.path.join(SRC, key + ".png")).convert("RGB")
    a = np.asarray(im).astype(np.float32).copy()
    if poly:
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        a[np.asarray(m) == 0] = 255
    white = a.min(2) >= 246
    alpha = ~_outside(white)
    alpha = ndimage.binary_opening(alpha, iterations=1)
    lab, n = ndimage.label(alpha)
    sizes = ndimage.sum(alpha, lab, range(1, n + 1)) if n else np.array([])
    big = [i + 1 for i in range(n) if sizes[i] >= 0.012 * alpha.size]
    if not big and n:
        big = [1 + int(np.argmax(sizes))]
    fig = np.isin(lab, big)
    small = [i + 1 for i in range(n) if sizes[i] >= 60 and (i + 1) not in big]
    acc = np.isin(lab, small)
    rgb = a / 255.0
    lum = rgb.mean(2)
    dark_acc = acc & (lum < 0.4)               # black ticks would vanish on black: make them cream
    rgb = rgb.copy()
    rgb[dark_acc] = np.array(CREAM, np.float32) / 255
    return rgb, fig, acc


@lru_cache(maxsize=None)
def sprite(name, height, accents=True, rim=True):
    """RGBA float sprite scaled so the picture is `height` px tall (figure bbox, padded)."""
    rgb, fig, acc = layers(name)
    ys, xs = np.nonzero(fig | acc)
    pad = RIM_PX + 4
    y0, y1 = max(0, ys.min() - pad), min(fig.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(fig.shape[1], xs.max() + pad + 1)
    rgb, fig, acc = rgb[y0:y1, x0:x1], fig[y0:y1, x0:x1], acc[y0:y1, x0:x1]
    out = np.zeros(fig.shape + (4,), np.float32)
    if rim:
        fat = np.asarray(Image.fromarray(fig.astype(np.uint8) * 255).filter(
            ImageFilter.MaxFilter(RIM_PX * 2 + 1))) > 0
        out[fat, :3] = np.array(RIM, np.float32) / 255
        out[fat, 3] = 1
    out[fig, :3] = rgb[fig]
    out[fig, 3] = 1
    if accents:
        out[acc, :3] = rgb[acc]
        out[acc, 3] = 1
    k = height / out.shape[0]
    size = (max(1, round(out.shape[1] * k)), height)
    pre = out.copy()
    pre[..., :3] *= pre[..., 3:4]
    im = Image.fromarray((pre * 255).astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
    o = np.asarray(im).astype(np.float32) / 255
    al = o[..., 3:4]
    o[..., :3] = np.where(al > 1e-3, o[..., :3] / np.maximum(al, 1e-3), 0)
    o = np.clip(o, 0, 1)
    o.setflags(write=False)
    return o


def _bbox(name):
    rgb, fig, acc = layers(name)
    ys, xs = np.nonzero(fig | acc)
    pad = RIM_PX + 4
    return (max(0, xs.min() - pad), max(0, ys.min() - pad),
            min(fig.shape[1], xs.max() + pad + 1), min(fig.shape[0], ys.max() + pad + 1))


def anchor(name, height, point):
    """Offset of a source-picture point from the sprite's bottom-centre, at the given height."""
    x0, y0, x1, y1 = _bbox(name)
    k = height / (y1 - y0)
    return (point[0] - (x0 + x1) / 2) * k, (point[1] - y1) * k


def info(name):
    rgb, fig, acc = layers(name)
    ys, xs = np.nonzero(fig)
    return dict(size=fig.shape[::-1], fig_bbox=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
                accents=int(ndimage.label(acc)[1]))


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    names = sys.argv[2].split(",")
    hgt = int(sys.argv[3]) if len(sys.argv) > 3 else 420
    tiles = [sprite(n, hgt) for n in names]
    hh = max(t.shape[0] for t in tiles)
    row = []
    for t in tiles:
        bg = np.full((hh + 20, t.shape[1] + 20, 3), 17 / 255, np.float32)
        y0 = hh - t.shape[0] + 10
        al = t[..., 3:4]
        bg[y0:y0 + t.shape[0], 10:10 + t.shape[1]] = bg[y0:y0 + t.shape[0], 10:10 + t.shape[1]] * (1 - al) + t[..., :3] * al
        row.append(bg)
    img = np.concatenate(row, 1)
    Image.fromarray((img * 255).astype(np.uint8)).save(out)
    print(out, img.shape, [info(n) for n in names])
