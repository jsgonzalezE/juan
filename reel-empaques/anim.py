"""Cut-out animation of the brand's pixel-art Noah illustrations (assets/noah_pix).

Nothing is redrawn. Each picture is split into parts (head, ear, paw, tail, eyes, tongue...) with
polygons given in source-picture pixels, and poses are made by shifting / rotating those parts,
the way cut-out pixel-art puppets are animated. `sprite(name, height, **state)` returns the frame.

Pictures and their states
    sack      d=0..470        head lowered behind the beans by d px (470 = hidden, paw stays on the rim)
    roaster   ear, paw, tail  rotations in degrees; rat = roaster shift in px; (sparks = accents)
    cupping   eye=-1|0|1      where he looks: left bowl, straight, right bowl;  blink=True
    barista   head=px down, tongue=0|1, cup=deg (raise), bow=deg
    sugar_noah  look=0|1 (1 = pupils to camera), knot=deg
    mug       nuzzle=deg, blink=True (the mug's face blinks)
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import pixref as PR

N = 1254
MARGIN = 70
_yy, _xx = np.mgrid[0:N, 0:N]


def _poly(pts):
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m) > 0


def _rgba(rgb, alpha):
    out = np.zeros((N, N, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = alpha
    out[~alpha.astype(bool)] = 0
    return out


def _rot(layer, deg, pivot):
    if not deg:
        return layer
    im = Image.fromarray((layer * 255).astype(np.uint8), "RGBA").rotate(deg, resample=Image.NEAREST, center=pivot)
    return np.asarray(im).astype(np.float32) / 255


def _shift(layer, dx, dy):
    dx, dy = int(round(dx)), int(round(dy))
    if not dx and not dy:
        return layer
    out = np.zeros_like(layer)
    h, w = layer.shape[:2]
    xs0, xs1 = max(0, dx), min(w, w + dx)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    out[ys0:ys1, xs0:xs1] = layer[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


def _over(dst, src):
    m = src[..., 3] > 0.5
    dst[m] = src[m]
    return dst


def _cut(layer, mask, pivot=None, plug=26):
    """Split `layer` into (rest, part). Near the pivot the hole is plugged so no gap opens."""
    m = mask & (layer[..., 3] > 0.5)
    part = np.zeros_like(layer)
    part[m] = layer[m]
    rest = layer.copy()
    rest[m] = 0
    if pivot is not None:
        near = m & ((_xx - pivot[0]) ** 2 + (_yy - pivot[1]) ** 2 <= plug * plug)
        if near.any():
            rest[near] = layer[near]
    return rest, part


def _move_blob(layer, win, dx, dy, fill, thresh=0.36):
    """Move the dark blob inside window (x0,y0,x1,y1) by (dx,dy), filling its old place."""
    x0, y0, x1, y1 = win
    sub = layer[y0:y1, x0:x1]
    dark = (sub[..., :3].mean(-1) < thresh) & (sub[..., 3] > 0.5)
    blob = np.zeros((N, N), bool)
    blob[y0:y1, x0:x1] = dark
    col = layer[blob].copy()
    out = layer.copy()
    out[blob, :3] = np.array(fill, np.float32) / 255
    ys, xs = np.nonzero(blob)
    out[np.clip(ys + dy, 0, N - 1), np.clip(xs + dx, 0, N - 1)] = col
    return out


@lru_cache(maxsize=None)
def _layers(name):
    rgb, fig, acc = PR.layers(name)
    return _rgba(rgb, fig), _rgba(rgb, acc)


FUR = (254, 245, 233)

# ---------------------------------------------------------------- per-picture poses
SACK_FRONT = None


def _sack(d=0):
    global SACK_FRONT
    fig, acc = _layers("sack")
    if SACK_FRONT is None:
        SACK_FRONT = (_yy >= 612) | _poly([(326, 562), (488, 562), (490, 660), (326, 660)])
    if not d:
        return fig, acc
    front, head = _cut(fig, ~SACK_FRONT)                # front = sack, beans and the paw on the rim
    moved = _shift(head, 0, d)
    moved[SACK_FRONT] = 0
    out = moved
    return _over(out, front), acc


def _roaster(ear=0, paw=0, tail=0, rat=0):
    fig, acc = _layers("roaster")
    roaster_m = ((_xx >= 656) & (_yy >= 604) & (_yy < 700)) | ((_xx >= 632) & (_yy >= 700)) | ((_xx >= 960) & (_yy >= 505))
    noah, roast = _cut(fig, roaster_m)
    ear_m = _poly([(505, 412), (560, 350), (600, 290), (640, 260), (730, 260), (730, 400), (702, 453), (612, 453),
                   (560, 442)])
    paw_m = _poly([(598, 453), (718, 453), (718, 574), (598, 574)])
    tail_m = _poly([(106, 836), (204, 836), (204, 1006), (106, 1006)])
    noah, e = _cut(noah, ear_m, (590, 428), 34)
    noah, p = _cut(noah, paw_m, (655, 576), 34)
    noah, tl = _cut(noah, tail_m, (202, 950), 28)
    out = np.zeros_like(fig)
    _over(out, _shift(roast, rat, 0))
    _over(out, _rot(tl, tail, (202, 950)))
    _over(out, _rot(e, ear, (590, 428)))
    _over(out, noah)
    _over(out, _rot(p, paw, (655, 576)))
    return out, _shift(acc, rat, 0)


def _cupping(eye=0, blink=False):
    fig, acc = _layers("cupping")
    out = fig
    wins = ((524, 614, 568, 658), (694, 614, 734, 658))
    if blink:
        out = out.copy()
        for (x0, y0, x1, y1) in wins:                  # squeeze each eye to a slit
            sub = out[y0:y1, x0:x1]
            dark = (sub[..., :3].mean(-1) < 0.36)
            keep = np.zeros_like(dark)
            keep[:14] = dark[:14]
            sub[dark & ~keep, :3] = np.array(FUR, np.float32) / 255
    elif eye:
        for w in wins:
            out = _move_blob(out, w, 13 * eye, 0, FUR)
    return out, acc


def _barista(head=0, tongue=0, cup=0, bow=0):
    fig, acc = _layers("barista")
    head_m = _poly([(280, 60), (1020, 60), (1020, 612), (850, 612), (812, 655), (792, 672), (482, 672), (455, 652),
                    (448, 552), (280, 552)])
    cup_m = _poly([(160, 548), (446, 548), (446, 668), (500, 700), (505, 800), (400, 846), (330, 852), (240, 802),
                   (160, 742)])
    bow_m = _poly([(836, 812), (958, 812), (958, 998), (862, 998), (836, 905)])
    body, hd = _cut(fig, head_m)
    body, cp = _cut(body, cup_m, (500, 770), 36)
    body, bw = _cut(body, bow_m, (842, 858), 26)
    if tongue:                                           # pant: the tongue pulls in a little
        x0, y0, x1, y1 = 590, 548, 674, 626
        sub = hd[y0:y1, x0:x1].copy()
        h = y1 - y0
        nh = h - 14
        idx = (np.arange(nh) * h / nh).astype(int)
        hd[y0:y0 + nh, x0:x1] = sub[idx]
        hd[y0 + nh:y1, x0:x1, :3] = np.array(FUR, np.float32) / 255
    out = np.zeros_like(fig)
    _over(out, _rot(bw, bow, (842, 858)))
    _over(out, body)
    _over(out, _rot(cp, cup, (500, 770)))
    _over(out, _shift(hd, 0, head))
    return out, _rot(acc, cup, (500, 770))


def _sugar(look=0, knot=0):
    fig, acc = _layers("sugar_noah")
    out = fig
    if look:                                             # pupils slide to the camera
        out = _move_blob(out, (656, 622, 714, 684), -26, 2, FUR)
        out = _move_blob(out, (466, 646, 528, 704), -24, 0, FUR)
    if knot:
        rest, k = _cut(out, _poly([(340, 170), (606, 170), (606, 372), (340, 372)]), (492, 368), 42)
        out = _over(rest, _rot(k, knot, (492, 372)))
    return out, np.zeros_like(acc)


def _mug(nuzzle=0, blink=False):
    fig, acc = _layers("mug")
    out = fig
    if blink:
        out = out.copy()
        mugc = out[735, 450, :3].copy()
        for (x0, y0, x1, y1) in ((376, 700, 420, 742), (479, 700, 523, 742)):
            sub = out[y0:y1, x0:x1]
            dark = sub[..., :3].mean(-1) < 0.42
            sub[dark, :3] = mugc
    if nuzzle:
        head_m = _poly([(572, 222), (1070, 222), (1070, 702), (905, 702), (872, 692), (770, 692), (700, 645),
                        (655, 615), (646, 470), (572, 440)])
        rest, hd = _cut(out, head_m, (800, 690), 44)
        out = _over(rest, _rot(hd, nuzzle, (800, 695)))
    return out, acc


POSES = dict(sack=_sack, roaster=_roaster, cupping=_cupping, barista=_barista, sugar_noah=_sugar, mug=_mug)


# ---------------------------------------------------------------- output
@lru_cache(maxsize=None)
def _box(name):
    x0, y0, x1, y1 = PR._bbox(name)
    return (max(0, x0 - MARGIN), max(0, y0 - MARGIN), min(N, x1 + MARGIN), min(N, y1 + MARGIN)), (x0, y0, x1, y1)


@lru_cache(maxsize=400)
def _frame(name, height, accents, state):
    fig, acc = POSES[name](**dict(state))
    (bx0, by0, bx1, by1), (x0, y0, x1, y1) = _box(name)
    alpha = fig[..., 3] > 0.5
    fat = np.asarray(Image.fromarray(alpha.astype(np.uint8) * 255).filter(
        ImageFilter.MaxFilter(PR.RIM_PX * 2 + 1))) > 0
    out = np.zeros((N, N, 4), np.float32)
    out[fat, :3] = np.array(PR.RIM, np.float32) / 255
    out[fat, 3] = 1
    out[alpha] = fig[alpha]
    if accents:
        am = acc[..., 3] > 0.5
        out[am] = acc[am]
    out = out[by0:by1, bx0:bx1]
    k = height / (y1 - y0)
    size = (max(1, round(out.shape[1] * k)), max(1, round(out.shape[0] * k)))
    pre = out.copy()
    pre[..., :3] *= pre[..., 3:4]
    im = Image.fromarray((pre * 255).astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
    o = np.asarray(im).astype(np.float32) / 255
    al = o[..., 3:4]
    o[..., :3] = np.where(al > 1e-3, o[..., :3] / np.maximum(al, 1e-3), 0)
    o = np.clip(o, 0, 1)
    o.setflags(write=False)
    # where the original picture's bottom-centre sits inside this sprite
    ax = ((x0 + x1) / 2 - bx0) * k
    ay = (y1 - by0) * k
    return o, (ax, ay)


def sprite(name, height, accents=True, **state):
    """(RGBA float sprite, (anchor_x, anchor_y)): the anchor is the picture's bottom-centre."""
    return _frame(name, int(height), bool(accents), tuple(sorted(state.items())))


def source_point(name, height, pt):
    """Offset (dx, dy) of a source-picture point from the bottom-centre anchor at this height."""
    return PR.anchor(name, height, pt)


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    sets = {
        "sack": [dict(d=470), dict(d=340), dict(d=63), dict(d=0)],
        "roaster": [dict(), dict(ear=9, rat=5), dict(paw=-10, tail=12), dict(paw=10, tail=-10, ear=-5)],
        "cupping": [dict(eye=-1), dict(), dict(eye=1), dict(blink=True)],
        "barista": [dict(), dict(head=10, tongue=1), dict(cup=-6, bow=9), dict(cup=-6, bow=-9, tongue=1)],
        "sugar_noah": [dict(), dict(look=1), dict(knot=7), dict(look=1, knot=-6)],
        "mug": [dict(), dict(nuzzle=4), dict(blink=True), dict(nuzzle=4, blink=True)],
    }
    names = sys.argv[2].split(",") if len(sys.argv) > 2 else list(sets)
    hgt = 330
    rows = []
    for nme in names:
        tiles = []
        for st in sets[nme]:
            s, (ax, ay) = sprite(nme, hgt, **st)
            bg = np.full((s.shape[0], s.shape[1], 3), 17 / 255, np.float32)
            al = s[..., 3:4]
            tiles.append(bg * (1 - al) + s[..., :3] * al)
        rows.append(np.concatenate(tiles, 1))
    w = max(r.shape[1] for r in rows)
    img = np.concatenate([np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0)), constant_values=17 / 255) for r in rows], 0)
    Image.fromarray((img * 255).astype(np.uint8)).save(out)
    print(out, img.shape)
