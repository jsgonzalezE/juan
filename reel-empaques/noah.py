"""Pixel-art Noah, derived from the brand's own line drawings.

Each pose is cropped from a drawing, downsampled to a small grid, inked (thin lines -> outline,
thick black areas -> dark fur) and filled white inside, giving an RGBA float sprite.
"""
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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


# ---------------------------------------------------------------------------
# v2: sprites tuned for a black background
# ---------------------------------------------------------------------------
POSES["sit"] = ("roaster.jpg", (205, 395, 522, 950))
THICK_K = {"sit": 0.06, "cap": 0.04}   # opening size (fraction of crop width) per pose

# recolour connected regions by seed (fractions of the crop): (x, y, kind)
SEEDS = {   # (x, y, kind, ymin, ymax) — the region is limited to rows ymin..ymax
    "sit": [(0.78, 0.45, "bandana", 0.31, 0.74)],
    "cup": [(0.50, 0.75, "cup", 0.0, 1.0)],
}
TONGUE = {"face": (0.478, 0.862, 0.07, 0.065)}   # ellipse: cx, cy, rx, ry (fractions)

PALETTES = {
    # name: fur, line, dark fur, rim, tongue, bandana, cup
    "sticker": dict(fur=(246, 241, 232), line=(30, 25, 22), dark=(58, 50, 45),
                    rim=(246, 241, 232), tongue=(236, 120, 136), bandana=(214, 96, 40),
                    cup=(122, 26, 58)),
    "warm": dict(fur=(246, 241, 232), line=(30, 25, 22), dark=(96, 84, 76),
                 rim=(120, 108, 98), tongue=(236, 120, 136), bandana=(214, 96, 40),
                 cup=(122, 26, 58)),
    "soft": dict(fur=(246, 241, 232), line=(44, 38, 34), dark=(74, 64, 58),
                 rim=None, tongue=(236, 120, 136), bandana=(214, 96, 40),
                 cup=(122, 26, 58)),
}


def _flood(mask, y, x):
    """Connected component of `mask` containing (y, x) (4-neighbour)."""
    h, w = mask.shape
    out = np.zeros_like(mask)
    if not (0 <= y < h and 0 <= x < w) or not mask[y, x]:
        return out
    st = [(y, x)]
    while st:
        cy, cx = st.pop()
        if out[cy, cx] or not mask[cy, cx]:
            continue
        out[cy, cx] = True
        if cy > 0:
            st.append((cy - 1, cx))
        if cy < h - 1:
            st.append((cy + 1, cx))
        if cx > 0:
            st.append((cy, cx - 1))
        if cx < w - 1:
            st.append((cy, cx + 1))
    return out


def _nb(mask):
    p = np.pad(mask, 1)
    h, w = mask.shape
    return sum(p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w].astype(np.int32)
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)


@lru_cache(maxsize=None)
def sprite2(pose, width, palette="sticker", line_t=0.26):
    fn, box = POSES[pose]
    im = Image.open(os.path.join(SRC, fn)).convert("L").crop(box)
    ink_full = (np.asarray(im) < 128)
    W0, H0 = im.size
    k = max(5, int(W0 * THICK_K.get(pose, 0.028)) | 1)
    ink_im = Image.fromarray(ink_full.astype(np.uint8) * 255)
    thick_full = np.asarray(ink_im.filter(ImageFilter.MinFilter(k)).filter(
        ImageFilter.MaxFilter(k))) > 127
    sil_full = _silhouette(ink_full.astype(np.float32), open_bottom=pose in OPEN_BOTTOM)
    h = max(1, round(width * H0 / W0))

    def down(a):
        return np.asarray(Image.fromarray((a.astype(np.float32) * 255).astype(np.uint8)).resize(
            (width, h), Image.BOX)).astype(np.float32) / 255

    thick = down(thick_full) > 0.5
    line = (down(ink_full & ~thick_full) > line_t) & ~thick
    sil = (down(sil_full) > 0.5) | thick | line
    if pose in OPEN_BOTTOM:
        inkr = line | thick
        for y in range(int(h * 0.5), h):
            xs = np.nonzero(inkr[y])[0]
            if xs.size >= 2:
                sil[y, xs[0]:xs[-1] + 1] = True
    # clean single-pixel specks
    line &= (_nb(line | thick) >= 1)
    fur = sil & ~line & ~thick
    lone = fur & (_nb(fur) <= 1)
    line |= lone
    fur &= ~lone
    P = PALETTES[palette]
    rgba = np.zeros((h, width, 4), np.float32)
    rgba[fur] = np.array(P["fur"] + (255,)) / 255
    rgba[line] = np.array(P["line"] + (255,)) / 255
    rgba[thick] = np.array(P["dark"] + (255,)) / 255
    for (sx, sy, kind, y0, y1) in SEEDS.get(pose, []):
        reg = _flood(thick, int(sy * h), int(sx * width))
        rows = np.arange(h)[:, None]
        reg &= (rows >= y0 * h) & (rows <= y1 * h)
        rgba[reg] = np.array(P[kind] + (255,)) / 255
    if pose in TONGUE:
        cx, cy, rx, ry = TONGUE[pose]
        yy, xx = np.mgrid[0:h, 0:width]
        ell = (((xx + 0.5) / width - cx) / rx) ** 2 + (((yy + 0.5) / h - cy) / ry) ** 2 <= 1
        rgba[ell & fur] = np.array(P["tongue"] + (255,)) / 255
    if P["rim"] is not None:
        rgba = np.pad(rgba, ((1, 1), (1, 1), (0, 0)))
        s = rgba[..., 3] > 0
        rim = ~s & (_nb(s) > 0)
        rgba[rim] = np.array(P["rim"] + (255,)) / 255
    rgba.setflags(write=False)
    return rgba


@lru_cache(maxsize=None)
def pack_photo(key, width):
    """Real pouch photo (cut out with rounded corners), RGBA float at `width` px."""
    im = Image.open(os.path.join(HERE, "assets", f"pouch_{key}.png")).convert("RGB")
    w0, h0 = im.size
    im = im.crop((2, 2, w0 - 2, h0 - 2))
    h = round(width * im.height / im.width)
    big = im.resize((width, h), Image.LANCZOS)
    from PIL import ImageEnhance
    if width > im.width:          # the watercolour mockups are small: restore a little crispness
        big = big.filter(ImageFilter.UnsharpMask(radius=1.6, percent=int(60 * min(1.6, width / im.width)), threshold=2))
    big = ImageEnhance.Contrast(ImageEnhance.Color(big).enhance(1.08)).enhance(1.05)
    rgb = np.asarray(big).astype(np.float32) / 255
    ss = 3   # supersampled rounded-rect mask for a clean edge
    m = Image.new("L", (width * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, width * ss - 1, h * ss - 1),
                                        radius=int(width * ss * 0.075), fill=255)
    a = np.asarray(m.resize((width, h), Image.LANCZOS)).astype(np.float32) / 255
    out = np.concatenate([rgb, a[..., None]], -1)
    out.setflags(write=False)
    return out


def pixelate(rgba, cell):
    """Blocky version of an RGBA float image (cell >= 1)."""
    if cell <= 1:
        return rgba
    h, w = rgba.shape[:2]
    sw, sh = max(1, w // cell), max(1, h // cell)
    pre = rgba[..., :3] * rgba[..., 3:4]
    im = Image.fromarray((np.concatenate([pre, rgba[..., 3:4]], -1) * 255).astype(np.uint8), "RGBA")
    sm = np.asarray(im.resize((sw, sh), Image.BOX)).astype(np.float32) / 255
    a = sm[..., 3:4]
    rgb = np.where(a > 1e-3, sm[..., :3] / np.maximum(a, 1e-3), 0)
    sm = np.concatenate([rgb, (a > 0.5).astype(np.float32)], -1)
    yi = np.minimum((np.arange(h) * sh / h).astype(int), sh - 1)
    xi = np.minimum((np.arange(w) * sw / w).astype(int), sw - 1)
    return sm[yi][:, xi]
