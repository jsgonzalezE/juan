"""Minimal A — STILL LIFE: one dithered object at a time, flower -> cherry -> bean -> pack -> logo."""
import math

import numpy as np

import common as C
import minimal as M
from audio import BEAT, CHORDS, ROOT, Track
from bean import bean_grid
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, dotmatrix, ease, font

NAME = "m1_still_life"
DURATION = 15.0
CX, CY = 540, 900
NAME_T = [6.0, 7.0, 8.0, 9.0]

FLOWER = M.object_grid("flower", 112)
CHERRY = M.object_grid("cherries", 124)
PACK = C.pix("color", 52, ncolors=0)
LOGO_W, LOGO_CELL = 300, 5
LOGO_G = C.logo_grid(LOGO_W, LOGO_CELL)
LOGO_A = C.logo_alpha(LOGO_W)


def pack_lum(t):
    ang = 0.55 * math.sin((t - 11.0) * 0.9) + 0.15
    rgb, a, m = C.card3d(PACK, ang, 0.0, persp=2.4, margin=0.25)
    lum = C.luminance(rgb)
    return np.clip(0.15 + lum * 0.95, 0, 1), a


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(5000 + i)
    img = C.bg(M.BGC)
    L = Layer()
    sm = font(300, 34, True)
    # 1 — flower
    p = M.window(t, 0.25, 3.0, 0.9, 0.35)
    if p > 0:
        lum, mask = FLOWER
        sway = 1.0 + 0.03 * math.sin(t * 1.3)
        img = M.draw_obj(img, lum, mask, CX, CY, 6, p, seed=1, gain=sway, floor=0.45)
        C.fade_text(L, t, 1.2, "(something is blooming)", sm, (W // 2, 1420), anchor="ms",
                    end=3.0)
    # 2 — cherries / origin
    p = M.window(t, 3.0, 5.5, 0.5, 0.35)
    if p > 0:
        lum, mask = CHERRY
        img = M.draw_obj(img, lum, mask, CX + int(6 * math.sin(t * 1.6)), CY, 6, p, seed=2,
                         color=(226, 92, 58), floor=0.35)
        if t > 3.4:
            a = ease((t - 3.4) / 0.4) * clamp01((5.5 - t) / 0.3)
            M.mixed_line(L, [("(origin", font(300, 36, True), 0, INK),
                             ("HUILA", font(300, 58), 16, INK),
                             ("COLOMBIA)", font(500, 22), 10, INK)], W // 2, 1430, a)
    # 3 — the bean and the varieties
    p = M.window(t, 5.5, 11.0, 0.5, 0.35)
    if p > 0:
        n = 100
        shade, hit = bean_grid(n, 0.4 + 0.85 * (t - 5.5), tilt=0.5 + 0.12 * math.sin(t * 0.8),
                               wobble=0.3 * math.sin(t * 0.6))
        img = M.draw_obj(img, shade ** 0.9, hit.astype(np.float32), CX, CY, 6, p, seed=3,
                         floor=0.0)
        for k, (name, t0) in enumerate(zip(C.VARIETY_NAMES, NAME_T)):
            if t0 <= t < t0 + 1.0:
                a = ease((t - t0) / 0.25) * clamp01((t0 + 1.0 - t) / 0.2)
                L.text((W // 2, 1440), name, font(300, 64), anchor="ms", tracking=20, alpha=a)
                L.text((W // 2, 1340), f"0{k + 1} / 04", font(500, 18), anchor="ms", tracking=6,
                       fill=ORANGE, alpha=a)
        if t >= 10.0:
            a = ease((t - 10.0) / 0.3) * clamp01((11.0 - t) / 0.25)
            L.text((W // 2, 1400), "JAVA  ·  CASTILLO  ·  GEISHA  ·  BOURBON", font(400, 22),
                   anchor="ms", tracking=8, alpha=a)
            L.text((W // 2, 1460), "(new varieties)", sm, anchor="ms", alpha=a)
    # 4 — the pack, whispered
    p = M.window(t, 11.0, 13.2, 0.6, 0.35)
    if p > 0:
        lum, a = pack_lum(t)
        img = M.draw_obj(img, lum, a, CX, CY, 8, p, seed=4, floor=0.25)
        C.fade_text(L, t, 11.7, "(and a new look)", sm, (W // 2, 1450), anchor="ms", end=13.2)
    # 5 — logo
    if t >= 13.1:
        lt = t - 13.1
        on = ((LOGO_G > 0.3) & (M.order(LOGO_G.shape, 9) < lt / 0.5)).astype(np.float32)
        k = ease((lt - 0.55) / 0.3)
        c = np.empty(LOGO_G.shape + (3,), np.float32)
        c[:] = np.array(INK, np.float32) / 255
        col, a = dotmatrix(c, on * (1 - k), LOGO_CELL, dot=3)
        lx, ly = (W - LOGO_W) // 2, 640
        composite(img, col, a, (lx, ly))
        if k > 0:
            s = np.empty(LOGO_A.shape + (3,), np.float32)
            s[:] = np.array(INK, np.float32) / 255
            composite(img, s, LOGO_A * k, (lx, ly))
        C.fade_text(L, t, 13.6, "GREEN COFFEE  ·  HUILA, COLOMBIA", font(400, 20), (W // 2, 1110),
                    anchor="ms", tracking=8)
        C.fade_text(L, t, 13.8, "(coming soon)", sm, (W // 2, 1180), anchor="ms")
        C.fade_text(L, t, 14.0, "@JUANITOCOFFEE", font(500, 20), (W // 2, 1250), anchor="ms",
                    tracking=8, color=ORANGE)
    M.hud(L, t, DURATION)
    img = L.apply(img)
    img = M.finish(img, rng, t, DURATION)
    return C.to_u8(img).tobytes()


def soundtrack(path):
    tr = Track(DURATION, seed=11)
    tr.vinyl(0.012)
    prog = ["Am7", "Fmaj7", "Cmaj7", "G6"]
    for k in range(8):
        t0 = 2.0 * k
        if t0 >= DURATION:
            break
        tr.pad(CHORDS[prog[k % 4]], t0, min(t0 + 2.0, DURATION - 0.3), gain=0.07, cutoff=650)
    # slow heartbeat pulse from the origin onwards
    for k in range(int(3.0 / 1.0), int(13.0 / 1.0)):
        tr.kick(k * 1.0, 0.35)
        tr.hat(k * 1.0 + 0.5, 0.025)
    for t0 in range(3, 13, 2):
        tr.bass(ROOT[prog[(t0 // 2) % 4]], float(t0), 1.8, 0.18)
    tr.bell(81, 0.3, 0.1)
    tr.bell(76, 1.2, 0.07, pan=0.3)
    tr.bell(84, 3.0, 0.08, pan=-0.3)
    for k, t0 in enumerate(NAME_T):
        tr.bell([81, 84, 88, 86][k], t0, 0.09, pan=[-0.3, 0.3, -0.3, 0.3][k])
    tr.bell(79, 11.0, 0.08)
    tr.bell(88, 13.1, 0.09)
    tr.bell(81, 13.6, 0.06, pan=0.4)
    for t0 in (3.0, 5.5, 11.0, 13.1):
        tr.whoosh(t0 + 0.05, 0.35, 0.04)
    return tr.write(path, fade=0.8)


if __name__ == "__main__":
    import sys
    C.run(render, DURATION, NAME)
    if "--stills" not in sys.argv:
        C.finalize(NAME, soundtrack)
