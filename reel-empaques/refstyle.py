"""Reference-style helpers: error-diffusion dot matrix and packs as lit 3D pouches."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image

import common as C
from fx import H, W, composite, dotmatrix

BGC = (12, 12, 12)
DOT_ORANGE = (240, 128, 52)
DOT_GREY = (196, 196, 192)


def fs_on(lum):
    """Floyd–Steinberg dither of a [0,1] grid -> boolean dots (gives the horizontal 'dash' texture)."""
    im = Image.fromarray((np.clip(lum, 0, 1) * 255).astype(np.uint8), "L")
    return np.asarray(im.convert("1", dither=Image.Dither.FLOYDSTEINBERG)).astype(bool)


def dots(img, lum, mask, x, y, color, cell=6, dot=5, alpha=1.0):
    on = fs_on(lum) & (mask > 0.5)
    rgb = np.empty(lum.shape + (3,), np.float32)
    rgb[:] = np.array(color, np.float32) / 255
    col, a = dotmatrix(rgb, on.astype(np.float32) * alpha, cell, dot=dot)
    return composite(img, col, a, (int(x), int(y)))


@lru_cache(maxsize=None)
def pouch_mesh(name, nu, nv, corner=0.0, enhance=0.0):
    """Surface samples of a stand-up pouch with the pack art as albedo."""
    im = C.IMAGES[name]
    aspect = im.width / im.height
    tex = np.asarray(im.resize((nu, nv), Image.BOX)).astype(np.float32) / 255
    alb = C.luminance(tex)
    if enhance > 0:  # local contrast + warm accents so watercolours read in one colour
        from PIL import ImageFilter
        warm = np.clip(tex[..., 0] - 0.5 * (tex[..., 1] + tex[..., 2]), 0, 1)
        alb = 0.8 * alb + 1.1 * warm
        bl = np.asarray(Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(max(2, nu / 40)))).astype(np.float32) / 255
        alb = alb + enhance * (alb - bl)
    lo, hi = np.percentile(alb, (2, 98))
    alb = np.clip((alb - lo) / (hi - lo), 0, 1)
    if enhance > 0:  # S-curve: separate shapes from the mid-tone wash
        med = float(np.median(alb))
        alb = 1 / (1 + np.exp(-(alb - med) * 7))
    u = np.linspace(-1, 1, nu)[None, :].repeat(nv, 0)
    v = np.linspace(-1, 1, nv)[:, None].repeat(nu, 1)
    prof = np.clip(1 - np.abs(v) ** 6, 0, 1) ** 0.6
    prof = np.where(v < -0.86, 0.15, prof)            # flat crimped top seal
    bul = 0.24
    z = bul * np.sqrt(np.clip(1 - u ** 2, 0, 1)) * prof
    X = u * aspect
    Y = -v
    P = np.stack([X, Y, z], -1)
    # normals from finite differences
    dPu = np.gradient(P, axis=1)
    dPv = np.gradient(P, axis=0)
    N = np.cross(dPv, dPu)
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9
    N[..., 2] = np.abs(N[..., 2])
    keep = np.ones(u.shape, bool)
    if corner > 0:  # rounded pouch corners (corner = radius as a fraction of the width)
        rx = corner
        ry = corner * aspect
        cu = np.clip(np.abs(u) - (1 - rx), 0, None) / rx
        cv = np.clip(np.abs(v) - (1 - ry), 0, None) / ry
        keep = cu ** 2 + cv ** 2 <= 1
    keep = keep.reshape(-1)
    return P.reshape(-1, 3)[keep], N.reshape(-1, 3)[keep], alb.reshape(-1)[keep], aspect


def rot(ay, ax=0.0, az=0.0):
    cy, sy = math.cos(ay), math.sin(ay)
    cx, sx = math.cos(ax), math.sin(ax)
    cz, sz = math.cos(az), math.sin(az)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def pouch(name, ang, rows, cols, scale, tilt=0.12, roll=0.0, nu=300, nv=480, back=0.5,
          contrast=1.0, corner=0.0, enhance=0.0, gamma=1.0):
    """Render a pouch into a (rows, cols) brightness grid + mask.

    scale = grid cells per world unit (pack height is 2 units).
    """
    P, N, alb, aspect = pouch_mesh(name, nu, nv, corner, enhance)
    alb = alb ** gamma
    R = rot(ang, tilt, roll)
    L = np.array([-0.45, 0.35, 0.82])
    L /= np.linalg.norm(L)
    out_l = np.zeros(rows * cols, np.float32)
    out_z = np.full(rows * cols, -1e9, np.float32)
    D = 6.0
    for side in (1, -1):
        Ps = P.copy()
        Ns = N.copy()
        if side < 0:  # back face: mirrored bulge, plain albedo
            Ps[:, 2] *= -1
            Ns[:, 2] *= -1
            a = np.full_like(alb, back)
        else:
            a = np.clip(0.5 + (alb - 0.5) * contrast, 0, 1)
        Pw = Ps @ R.T
        Nw = Ns @ R.T
        vis = Nw[:, 2] > -0.05
        f = D / (D - Pw[:, 2])
        gx = (Pw[:, 0] * f * scale + cols / 2).astype(int)
        gy = (-Pw[:, 1] * f * scale + rows / 2).astype(int)
        ok = vis & (gx >= 0) & (gx < cols) & (gy >= 0) & (gy < rows)
        diff = np.clip(Nw @ L, 0, 1)
        spec = np.clip(Nw @ (L + np.array([0, 0, 1])) / np.linalg.norm(L + np.array([0, 0, 1])),
                       0, 1) ** 24
        val = (0.12 + 0.88 * a) * (0.18 + 0.9 * diff ** 1.15) + 0.25 * spec
        idx = (gy * cols + gx)[ok]
        z = Pw[ok, 2]
        v = val[ok]
        order = np.argsort(z)
        idx, z, v = idx[order], z[order], v[order]
        nearer = z > out_z[idx]
        out_l[idx[nearer]] = v[nearer]
        out_z[idx[nearer]] = z[nearer]
    mask = (out_z > -1e8).reshape(rows, cols).astype(np.float32)
    return np.clip(out_l.reshape(rows, cols), 0, 1), mask


def static(rng, strength=1.0):
    n = rng.random((H // 3, W // 3)).astype(np.float32)
    n = 0.16 + n * 0.38 * strength
    for _ in range(4):
        r = rng.integers(0, H // 3)
        n[r:r + rng.integers(1, 3)] *= 1.6
    n = np.repeat(np.repeat(n, 3, 0), 3, 1)
    return np.repeat(n[..., None], 3, 2)


def tear(img, rng, n=3, amp=40):
    """A few horizontal line tears like a worn video."""
    for _ in range(n):
        y = int(rng.integers(0, H - 6))
        h = int(rng.integers(2, 8))
        img[y:y + h] = np.roll(img[y:y + h], int(rng.integers(-amp, amp)), axis=1)
    return img


DOT_CREAM = (238, 228, 212)


def fs_levels(lum, levels=3):
    """Multi-level Floyd–Steinberg: returns indices 0..levels-1."""
    g = (np.clip(lum, 0, 1) * 255).astype(np.uint8)
    rgb = Image.fromarray(np.stack([g, g, g], -1), "RGB")
    pal = Image.new("P", (1, 1))
    vals = [int(round(255 * k / (levels - 1))) for k in range(levels)]
    flat = []
    for v in vals:
        flat += [v, v, v]
    pal.putpalette(flat + [0, 0, 0] * (256 - levels))
    q = rgb.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG)
    return np.asarray(q).astype(np.int32)


def dots2(img, lum, mask, x, y, c1, c2, cell=6, dot=5, alpha=1.0):
    """Two-tone dots: mid tones in c1, highlights in c2."""
    idx = fs_levels(lum, 3) * (mask > 0.5)
    rgb = np.zeros(lum.shape + (3,), np.float32)
    rgb[idx == 1] = np.array(c1, np.float32) / 255
    rgb[idx == 2] = np.array(c2, np.float32) / 255
    col, a = dotmatrix(rgb, (idx > 0).astype(np.float32) * alpha, cell, dot=dot)
    return composite(img, col, a, (int(x), int(y)))
