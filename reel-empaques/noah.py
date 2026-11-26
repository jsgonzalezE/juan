"""Pixel-art Noah, derived from the brand's own line drawings.

Each pose is cropped from a drawing, downsampled to a small grid, inked (thin lines -> outline,
thick black areas -> dark fur) and filled white inside, giving an RGBA float sprite.
"""
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "noah")

OUTLINE = (24, 20, 18)
FUR_DARK = (58, 50, 46)
WHITE = (244, 239, 230)
SHADE = (214, 206, 194)
TONGUE = (232, 118, 132)

# pose -> (file, crop box in source pixels)
POSES = {
    "face": ("vibes.png", (496, 1318, 815, 1630)),       # big smile, tongue out
    "sniff": ("vibes.png", (146, 982, 436, 1250)),       # eyes closed, topknot
    "peek": ("vibes.png", (910, 980, 1150, 1258)),       # paws over an edge
    "cup": ("vibes.png", (58, 1334, 356, 1622)),         # inside a cup
    "bow": ("vibes.png", (74, 1742, 470, 1960)),         # side, play bow
    "sack": ("vibes.png", (490, 912, 812, 1186)),        # peeking out of a sack
    "sit": ("roaster.jpg", (205, 395, 560, 950)),        # sitting, bandana
    "mug": ("mug.jpg", (440, 320, 870, 800)),            # hugging a mug
    "cap": ("cap.jpg", (215, 340, 790, 1030)),           # wearing a cap
}


OPEN_BOTTOM = {"peek"}


def _flood_outside(blocked, open_bottom=False):
    """Boolean mask of cells reachable from the border without crossing `blocked`."""
    h, w = blocked.shape
    out = np.zeros((h, w), bool)
    stack = [(y, x) for y in range(h) for x in (0, w - 1)] + \
            [(y, x) for x in range(w) for y in ((0,) if open_bottom else (0, h - 1))]
    while stack:
        y, x = stack.pop()
        if out[y, x] or blocked[y, x]:
            continue
        out[y, x] = True
        if y > 0:
            stack.append((y - 1, x))
        if y < h - 1:
            stack.append((y + 1, x))
        if x > 0:
            stack.append((y, x - 1))
        if x < w - 1:
            stack.append((y, x + 1))
    return out


def _silhouette(ink_full, close=9, open_bottom=False):
    """High-res silhouette: close gaps in the ink, flood from the border, reopen."""
    h, w = ink_full.shape
    im = Image.fromarray(((ink_full > 0.45) * 255).astype(np.uint8))
    closed = np.asarray(im.filter(ImageFilter.MaxFilter(close))) > 127
    # flood on a 1/4 grid for speed
    sm = np.asarray(Image.fromarray(closed.astype(np.uint8) * 255).resize(
        (max(2, w // 4), max(2, h // 4)), Image.BOX)) > 60
    if open_bottom:
        sm[-1, :] = True
    out = _flood_outside(sm, open_bottom)
    if open_bottom:
        out[-1, :] = out[-2, :]
    sil = ~np.asarray(Image.fromarray(out.astype(np.uint8) * 255).resize((w, h), Image.NEAREST)) > 0
    sil = np.asarray(Image.fromarray(sil.astype(np.uint8) * 255).filter(
        ImageFilter.MinFilter(close // 2 * 2 + 1))) > 127
    return sil | (ink_full > 0.45)


@lru_cache(maxsize=None)
def sprite(pose, width, thresh=0.30, flip=False):
    """RGBA float sprite (h, width, 4) for a pose."""
    fn, box = POSES[pose]
    im = Image.open(os.path.join(SRC, fn)).convert("L").crop(box)
    ink_full = 1 - np.asarray(im).astype(np.float32) / 255
    sil_full = _silhouette(ink_full, open_bottom=pose in OPEN_BOTTOM)
    h = max(1, round(width * im.height / im.width))

    def down(a):
        return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize(
            (width, h), Image.BOX)).astype(np.float32) / 255

    ink = down(ink_full) > thresh
    sil = down(sil_full.astype(np.float32)) > 0.5
    if pose in OPEN_BOTTOM:  # fill each lower row between its outermost ink pixels
        inkr = down(ink_full) > thresh
        for y in range(int(h * 0.5), h):
            xs = np.nonzero(inkr[y])[0]
            if xs.size >= 2:
                sil[y, xs[0]:xs[-1] + 1] = True
    eroded = np.asarray(Image.fromarray(((ink_full > 0.45) * 255).astype(np.uint8)).filter(
        ImageFilter.MinFilter(11))).astype(np.float32) / 255
    thick = ink & (down(eroded) > 0.4)
    # remove isolated specks (single white pixels inside ink and vice versa)
    pad = np.pad(ink, 1)
    nb = sum(pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + width] for dy in (-1, 0, 1)
             for dx in (-1, 0, 1) if dy or dx)
    ink = (ink & (nb >= 2)) | (~ink & sil & (nb >= 7))
    rgba = np.zeros((h, width, 4), np.float32)
    rgba[sil] = np.array(WHITE + (255,)) / 255
    rgba[ink] = np.array(OUTLINE + (255,)) / 255
    rgba[thick] = np.array(FUR_DARK + (255,)) / 255
    if flip:
        rgba = rgba[:, ::-1].copy()
    rgba.setflags(write=False)
    return rgba


def blink(spr):
    """Close the eyes: dark 1-2px dots in the upper face become a short line."""
    s = spr.copy()
    return s


@lru_cache(maxsize=None)
def pack_sprite(key, width, ncolors=20):
    """Colour pixel-art version of a pouch mockup crop with rounded corners."""
    im = Image.open(os.path.join(HERE, "assets", f"pouch_{key}.png")).convert("RGB")
    h = round(width * im.height / im.width)
    from PIL import ImageEnhance
    small = im.resize((width, h), Image.BOX)
    small = ImageEnhance.Color(ImageEnhance.Contrast(small).enhance(1.18)).enhance(1.3)
    q = small.quantize(colors=ncolors, method=Image.Quantize.MEDIANCUT,
                       dither=Image.Dither.NONE).convert("RGB")
    rgb = np.asarray(q).astype(np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:width].astype(np.float32)
    r = width * 0.09
    cx = np.clip(xx + 0.5, r, width - r)
    cy = np.clip(yy + 0.5, r, h - r)
    a = (((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) <= r * r).astype(np.float32)
    out = np.concatenate([rgb, a[..., None]], -1)
    out.setflags(write=False)
    return out
