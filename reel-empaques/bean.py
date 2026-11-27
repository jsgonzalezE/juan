"""Procedural rotating coffee bean, rendered as a brightness grid for dithering."""
import math

import numpy as np


def rot(ax, ay, az):
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


_tex_cache = {}


def bean_grid(n, angle, tilt=0.35, wobble=0.0, seed=3):
    """Return (n, n) brightness in [0,1] and coverage mask for a bean.

    Bean long axis = y. Flat face (with crease) points to +z in object space.
    """
    a, b = 1.0, 0.74          # half length, half width
    c_back, c_front = 0.56, 0.30
    R = rot(tilt, angle, wobble)
    Rt = R.T
    span = 1.25
    u = np.linspace(-span, span, n)
    X, Y = np.meshgrid(u, -u)
    # ray origin in world: (X, Y, 5), direction (0,0,-1)
    O = np.stack([X, Y, np.full_like(X, 5.0)], -1) @ Rt.T
    D = np.array([0, 0, -1.0]) @ Rt.T
    best_t = np.full(X.shape, np.inf)
    best_p = np.zeros(X.shape + (3,))
    best_front = np.zeros(X.shape, bool)
    for cz, front in ((c_back, False), (c_front, True)):
        s = np.array([b, a, cz])
        o = O / s
        d = D / s
        A = (d * d).sum()
        B = 2 * (o * d).sum(-1)
        C = (o * o).sum(-1) - 1
        disc = B * B - 4 * A * C
        ok = disc >= 0
        sq = np.sqrt(np.where(ok, disc, 0))
        for t in ((-B - sq) / (2 * A), (-B + sq) / (2 * A)):
            p = O + t[..., None] * D
            good = ok & (t > 0) & ((p[..., 2] >= 0) if front else (p[..., 2] <= 0)) & (t < best_t)
            best_t = np.where(good, t, best_t)
            best_p = np.where(good[..., None], p, best_p)
            best_front = np.where(good, front, best_front)
    hit = np.isfinite(best_t)
    p = best_p
    cz = np.where(best_front, c_front, c_back)
    nrm = np.stack([p[..., 0] / b ** 2, p[..., 1] / a ** 2, p[..., 2] / cz ** 2], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9
    nw = nrm @ R.T
    L = np.array([-0.45, 0.55, 0.7])
    L /= np.linalg.norm(L)
    lam = np.clip((nw * L).sum(-1), 0, 1)
    rim = np.clip(1 - nw[..., 2], 0, 1) ** 3
    shade = 0.12 + 0.88 * lam + 0.25 * rim
    # crease on the flat face: S-shaped groove along the long axis
    cx = 0.06 * np.sin(2.4 * p[..., 1] / a)
    dist = np.abs(p[..., 0] - cx)
    along = np.clip(1 - (np.abs(p[..., 1]) / (0.92 * a)) ** 6, 0, 1)
    groove = np.exp(-(dist / 0.045) ** 2) * along * best_front
    shade *= 1 - 0.9 * groove
    # lip highlight next to the groove
    shade += 0.25 * np.exp(-((dist - 0.09) / 0.03) ** 2) * along * best_front * lam
    # organic mottling, fixed to the object surface
    key = (n, seed)
    if key not in _tex_cache:
        r = np.random.default_rng(seed)
        _tex_cache[key] = r.random((64, 64, 64)).astype(np.float32)
    tex = _tex_cache[key]
    idx = np.clip(((p + 1.1) / 2.2 * 63).astype(int), 0, 63)
    mott = tex[idx[..., 0], idx[..., 1], idx[..., 2]]
    shade *= 0.85 + 0.3 * mott
    shade = np.where(hit, np.clip(shade, 0, 1), 0)
    return shade.astype(np.float32), hit
