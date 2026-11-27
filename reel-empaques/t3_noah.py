"""T3 — NOAH'S SHIFT, animated. The brand's own pixel-art Noah illustrations (assets/noah_pix),
animated as cut-out puppets (anim.py): he peeks out of the sack of green coffee, his ear snaps at
the first crack, his eyes go from cup to cup, he serves the four real packs, gives the painted
dog a side-eye, and hugs his mug at the end.

    python3 t3_noah.py --stills 1,4,7      # previews
    python3 t3_noah.py --cues              # build/t3_noah_cues.json for the sound design
    python3 t3_noah.py                     # build/t3_noah_silent.mp4
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

import anim as A
import common as C
import stage as S
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, ease, ease_out, font

NAME = "t3_noah"
DURATION = 22.0
BGC = (17, 16, 16)
CREAM = (240, 228, 206)
SOFT = (176, 166, 152)
BEAT = 0.5
PACKS = ["color", "cherries", "mule", "dog"]
BASE = 1330
NX, PX_, PW = 300, 805, 400

T = dict(
    wob=0.55, knot=0.8, peek=1.25, pop=1.7, origin=2.0,
    roast=3.0, crack1=3.5, crack2=4.25, crack_txt=3.6, heard_txt=4.4, wave=4.5,
    cup=5.5, qc_txt=5.8, names=(6.5, 7.0, 7.5, 8.0),
    packs=9.0, pack=(9.0, 10.5, 12.0, 13.5), look_txt=9.4,
    huh=14.5, who_txt=14.9, glance=15.6, incl_txt=16.2,
    family=17.5, row=(17.5, 17.7, 17.9, 18.1), q_txt=18.5, a_txt=18.9,
    end=19.5, logo=19.6, soon=20.0, handle=20.35,
)


def cues():
    c = [("rustle", T["wob"]), ("knot", T["knot"]), ("peek", T["peek"]), ("pop", T["pop"]),
         ("cut", T["roast"]), ("crack", T["crack1"]), ("crack", T["crack2"]), ("wave", T["wave"]),
         ("cut", T["cup"])]
    c += [("name", t) for t in T["names"]]
    c += [("swap", t) for t in T["pack"]] + [("resolve", t + 0.5) for t in T["pack"]]
    c += [("huh", T["huh"]), ("tick", T["huh"] + 0.12), ("who", T["who_txt"]), ("glance", T["glance"]),
          ("incl", T["incl_txt"]), ("family", T["family"])]
    c += [("pack_pop", t) for t in T["row"]]
    c += [("yap", T["a_txt"]), ("end", T["end"]), ("blip", T["soon"]), ("blip", T["handle"])]
    return sorted(c, key=lambda x: x[1])


# ---------------------------------------------------------------- drawing
def put(img, name, cx, bottom, h, squash=(1.0, 1.0), scale=1.0, accents=True, alpha=1.0, dx=0, **state):
    """Draw an animated illustration with the picture's bottom-centre at (cx, bottom)."""
    spr, (ax, ay) = A.sprite(name, h, accents, **state)
    sx, sy = squash[0] * scale, squash[1] * scale
    if abs(sx - 1) > 0.004 or abs(sy - 1) > 0.004:
        sh, sw = spr.shape[:2]
        nw, nh = max(1, round(sw * sx)), max(1, round(sh * sy))
        yi = np.minimum((np.arange(nh) * sh / nh).astype(int), sh - 1)
        xi = np.minimum((np.arange(nw) * sw / nw).astype(int), sw - 1)
        spr = spr[yi][:, xi]
        ax, ay = ax * sx, ay * sy
    return composite(img, np.ascontiguousarray(spr[..., :3]), spr[..., 3] * alpha,
                     (int(round(cx - ax + dx)), int(round(bottom - ay))))


def pop(t, t0, dur=0.26):
    """(scale, alpha) of a pop-in that overshoots and settles, in 12 fps steps."""
    u = (t - t0) / dur
    if u < 0:
        return 0.0, 0.0
    if u >= 1:
        return 1.0, 1.0
    u = int(u * 6) / 6
    return 0.72 + 0.28 * (1 - (1 - u) ** 3) + 0.07 * math.sin(u * math.pi), min(1.0, u * 3 + 0.34)


def hit(t, t0, dur=0.18, amt=1.0):
    """A squash that fires once at t0."""
    u = (t - t0) / dur
    if not 0 <= u < 1:
        return (1.0, 1.0)
    k = math.sin(u * math.pi) * amt
    return (1 + 0.035 * k, 1 - 0.05 * k)


def on_beat(t, start, width=0.13):
    return t >= start and ((t - start) % BEAT) < width


def step(t, hz, *values):
    """Cycle through values at hz frames per second (stop-motion timing)."""
    return values[int(t * hz) % len(values)]


def caption(L, t, t0, t1, text, x, y, size=38, color=CREAM, italic=True, weight=300, tracking=0):
    if not (t0 <= t < t1):
        return
    a = ease((t - t0) / 0.2) * clamp01((t1 - t) / 0.2)
    L.text((x, y), text, font(weight, size, italic), fill=color, anchor="ms", alpha=a, tracking=tracking)


def header(L, a=1.0):
    L.text((64, 150), "JUANITO COFFEE", font(600, 20), tracking=6, fill=(196, 186, 172), alpha=a)
    L.text((1016, 150), "NEW HARVEST", font(400, 20), tracking=6, anchor="ra", fill=(132, 124, 114), alpha=a)


def words_line(L, t, words, times, y, f, color, gap="   ·   ", tracking=5):
    parts = []
    for i, w in enumerate(words):
        parts.append(w)
        if i < len(words) - 1:
            parts.append(gap)
    widths = [sum(f.getlength(ch) + tracking for ch in p) for p in parts]
    x = W / 2 - sum(widths) / 2
    for i, (p, wd) in enumerate(zip(parts, widths)):
        k = i // 2 if i % 2 == 0 else i // 2 + 1
        a = ease((t - times[min(k, len(times) - 1)]) / 0.18)
        if a > 0:
            L.text((x, y - (1 - a) * 10), p, f, fill=color if i % 2 == 0 else SOFT, anchor="ls",
                   tracking=tracking, alpha=a)
        x += wd


def pack_slot(img, t):
    ts = T["pack"]
    k = max(i for i in range(4) if t >= ts[i])
    lt = t - ts[k]
    if lt < 0.5:
        if k > 0 and lt < 0.2:
            return S.pack(img, PACKS[k - 1], PW, PX_, BASE, k=1 - ease(lt / 0.2) * 0.85), k
        return S.pack(img, PACKS[k], PW, PX_, BASE,
                      k=0.15 + 0.85 * ease((lt - (0.2 if k else 0)) / (0.3 if k else 0.5))), k
    return S.pack(img, PACKS[k], PW, PX_, BASE), k


def glide(t, keys):
    """Piecewise value: keys = [(time, value), ...]; steps between keys in 3 sub-frames."""
    v = keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t >= t1:
            v = v1
        elif t >= t0:
            u = (t - t0) / (t1 - t0)
            v = v0 + (v1 - v0) * (int(u * 3) / 3)
            break
    return int(round(v))


# ---------------------------------------------------------------- scenes
def s_sack(img, L, t):
    """A paw on the rim... a topknot... two eyes... Noah."""
    d = glide(t, [(0.0, 470), (T["knot"], 470), (T["knot"] + 0.12, 340), (T["peek"], 340), (T["peek"] + 0.12, 63),
                  (T["pop"], 63), (T["pop"] + 0.1, 0)])
    if T["knot"] + 0.12 <= t < T["peek"]:
        d += step(t, 8, 0, -14, 0, 10)                   # the topknot wiggles
    if T["peek"] + 0.12 <= t < T["pop"]:
        d += step(t, 3, 0, 0, 12)                         # he ducks a little, then looks again
    sq = hit(t, T["wob"], 0.3, 1.0)
    if t >= T["pop"]:
        sq = hit(t, T["pop"] + 0.08, 0.22, 1.6) if t < T["pop"] + 0.32 else (
            (1 + 0.022, 1 - 0.032) if on_beat(t, 2.0, 0.1) else (1.0, 1.0))
    a = ease(t / 0.3)
    img = put(img, "sack", 540, 1250, 800, squash=sq, alpha=a, d=d)
    for t0 in (T["wob"], T["pop"]):
        img = S.dust(img, 540, 1232, t0, t, color=(190, 170, 136), n=8, seed=int(t0 * 10))
    for k, (dx, dy) in enumerate(((-250, -640), (268, -560), (-290, -420))):
        img = S.sparkle(img, 540 + dx, 1250 + dy, T["pop"] + 0.08 + 0.05 * k, t)
    a = ease((t - T["origin"]) / 0.3)
    if a > 0:
        L.text((W // 2, 1356), "GREEN COFFEE", font(500, 28), anchor="ms", tracking=12, fill=CREAM, alpha=a)
        f1, f2 = font(300, 36, True), font(500, 22)
        w1 = f1.getlength("(origin ")
        w2 = sum(f2.getlength(ch) + 8 for ch in "HUILA  COLOMBIA")
        x0 = W / 2 - (w1 + w2 + f1.getlength(")")) / 2
        a2 = ease((t - T["origin"] - 0.2) / 0.3)
        L.text((x0, 1418), "(origin ", f1, fill=SOFT, anchor="ls", alpha=a2)
        L.text((x0 + w1, 1416), "HUILA  COLOMBIA", f2, fill=CREAM, anchor="ls", tracking=8, alpha=a2)
        L.text((x0 + w1 + w2 + 2, 1418), ")", f1, fill=SOFT, anchor="ls", alpha=a2)
    return img


def s_roast(img, L, t):
    """First crack: the ear snaps up, the roaster rattles, then he waves: 'me, I heard it'."""
    ear = rat = paw = 0
    sparks = False
    for tc in (T["crack1"], T["crack2"]):
        u = t - tc
        if 0 <= u < 0.36:
            ear = (10, 10, -5, -5, 3, 0)[min(5, int(u / 0.06))]
            rat = (6, -6, 5, -4, 3, 0)[min(5, int(u / 0.06))]
            sparks = True
        elif 0.36 <= u < 0.7:
            sparks = int(u * 10) % 2 == 0
    if t >= T["wave"]:
        paw = step(t, 7, -10, 0, 10, 0)
        sparks = int(t * 5) % 2 == 0
    tail = step(t, 6, 0, 10, 0, -8)
    sc, al = pop(t, T["roast"])
    img = put(img, "roaster", 540, 1230, 680, scale=sc, alpha=al, accents=sparks,
              ear=ear, paw=paw, tail=tail, rat=rat)
    caption(L, t, T["crack_txt"], T["cup"], "(first crack?", W // 2, 1340, 40)
    caption(L, t, T["heard_txt"], T["cup"], "I heard it first.)", W // 2, 1398, 40, color=ORANGE)
    return img


def s_cup(img, L, t):
    """Quality control: his eyes go from cup to cup as the four varieties arrive."""
    n = T["names"]
    eye = 0
    if n[0] <= t < n[1]:
        eye = -1
    elif n[2] <= t < n[3]:
        eye = 1
    blink = (T["cup"] + 0.75 <= t < T["cup"] + 0.87) or (n[3] + 0.5 <= t < n[3] + 0.62)
    sc, al = pop(t, T["cup"])
    push = 1.0 + 0.06 * clamp01((t - T["cup"] - 0.3) / 3.2)
    state = dict(blink=True) if blink else dict(eye=eye)
    img = put(img, "cupping", 540, 1190, 620, scale=sc * push, alpha=al, **state)
    caption(L, t, T["qc_txt"], T["packs"], "(quality control)", W // 2, 470, 38, color=SOFT)
    a = ease((t - n[0] + 0.15) / 0.25)
    if a > 0:
        L.text((W // 2, 1296), "FOUR NEW VARIETIES", font(500, 20), anchor="ms", tracking=10, fill=SOFT, alpha=a)
    words_line(L, t, ["JAVA", "CASTILLO", "GEISHA", "BOURBON"], n, 1362, font(500, 30), CREAM)
    return img


def barista_state(t, serve_times):
    """Head bobs on the beat, he pants, and lifts the cup when a pack lands."""
    st = dict(head=10 if on_beat(t, 9.0) else 0, tongue=step(t, 5, 0, 1))
    for ts in serve_times:
        u = t - ts
        if 0 <= u < 0.62:
            st["cup"] = (-4, -8, -8, -8, -8, -8, -8, -5, -2, 0)[min(9, int(u / 0.062))]
            st["bow"] = step(t, 8, 9, -9)
    return st


def s_packs(img, L, t):
    img, k = pack_slot(img, t)
    lt = t - T["pack"][k]
    for j, (dx, dy) in enumerate(((-232, -640), (236, -520), (-246, -300))):
        img = S.sparkle(img, PX_ + dx, BASE + dy, T["pack"][k] + 0.46 + 0.05 * j, t)
    sc, al = pop(t, T["packs"])
    img = put(img, "barista", NX, BASE, 690, scale=sc, alpha=al, accents=int(t * 4) % 2 == 0,
              **barista_state(t, [p + 0.45 for p in T["pack"]]))
    caption(L, t, T["look_txt"], T["huh"], "(a new look)", PX_, BASE - 716, 38)
    if lt > 0.45:
        a = ease((lt - 0.45) / 0.2)
        L.text((PX_, BASE + 62), f"0{k + 1} / 04", font(600, 20), anchor="ms", tracking=8, fill=SOFT, alpha=a)
    return img


def s_huh(img, L, t):
    """Pack four has another dog on it: topknot twitch, a look at the pack, a look at us."""
    lt = t - T["huh"]
    img = S.pack(img, "dog", PW, PX_, BASE)
    knot = (9, 9, -7, -7, 4, 0)[min(5, int(lt / 0.06))] if lt < 0.36 else 0
    look = 1 if (T["glance"] <= t < T["glance"] + 0.75) else 0
    if T["incl_txt"] + 0.5 <= t < T["incl_txt"] + 0.62:
        knot = 6
    shake = int(round(6 * math.sin(lt * 60) * clamp01(1 - lt / 0.25))) if lt < 0.25 else 0
    push = 1.0 + 0.05 * clamp01(lt / 3.0)
    img = put(img, "sugar_noah", NX + 6, BASE, 640, scale=push, dx=shake, accents=False, look=look, knot=knot)
    pw, ph = S.pack_size("dog", PW)
    bx0, by0 = PX_ - pw / 2, BASE - ph
    x0, y0, x1, y1 = [int(v) for v in (bx0 + 0.40 * pw, by0 + 0.805 * ph, bx0 + 0.60 * pw, by0 + 0.985 * ph)]
    if lt > 0.12:
        a = 1.0 if (lt > 0.45 or int((lt - 0.12) * 12) % 2 == 0) else 0.25
        s = 22 + int(4 * math.sin(lt * 9))
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            L.line([(x, y + dy * s), (x, y), (x + dx * s, y)], fill=ORANGE, width=5, alpha=a)
    caption(L, t, T["who_txt"], T["family"], "(...who's HE?)", NX + 6, BASE - 640 * push - 26, 40)
    caption(L, t, T["incl_txt"], T["family"], "(dog included.)", PX_, BASE + 66, 38, color=ORANGE)
    return img


ROW_W, ROW_GAP = 222, 32
ROW_X0 = (W - (4 * ROW_W + 3 * ROW_GAP)) // 2 + ROW_W // 2


def s_family(img, L, t):
    for i, key in enumerate(PACKS):
        img = S.pack(img, key, ROW_W, ROW_X0 + i * (ROW_W + ROW_GAP), 720, k=ease((t - T["row"][i]) / 0.4), glow=0.16)
    sc, al = pop(t, T["family"] + 0.1)
    img = put(img, "barista", 540, 1330, 540, scale=sc, alpha=al, accents=int(t * 4) % 2 == 0,
              **barista_state(t, [T["a_txt"] - 0.05]))
    caption(L, t, T["q_txt"], T["end"], "New look?", W // 2, 1412, 42, italic=False, weight=400)
    caption(L, t, T["a_txt"], T["end"], "Noah approved.", W // 2, 1470, 42, color=ORANGE)
    return img


LOGO_W = 250
LOGO_A = C.logo_alpha(LOGO_W)


def s_end(img, L, t):
    k = ease((t - T["logo"]) / 0.45)
    if k > 0:
        cell = [40, 24, 12, 6, 3, 1][min(5, int(k * 5.99))]
        la = LOGO_A
        if cell > 1:
            hh, ww = la.shape
            sm = np.asarray(Image.fromarray((la * 255).astype(np.uint8)).resize(
                (max(1, ww // cell), max(1, hh // cell)), Image.BOX))
            la = np.asarray(Image.fromarray(sm).resize((ww, hh), Image.NEAREST)).astype(np.float32) / 255
        s = np.empty(la.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, la * min(1.0, k * 1.5), ((W - LOGO_W) // 2, 330))
    C.fade_text(L, t, T["soon"], "COMING SOON", font(500, 30), (W // 2, 720), anchor="ms", tracking=14, color=CREAM)
    C.fade_text(L, t, T["soon"] + 0.12, "green coffee  ·  Huila, Colombia", font(300, 32, True), (W // 2, 778),
                anchor="ms", color=SOFT)
    lt = t - T["end"]
    nuzzle = 4 if (lt > 0.5 and (lt - 0.5) % 1.0 < 0.3) else 0
    blink = 1.4 <= lt < 1.55
    sc, al = pop(t, T["end"] + 0.05)
    hgt = 480
    img = put(img, "mug", 540, 1350, hgt, scale=sc, alpha=al, accents=int(t * 4) % 2 == 0, nuzzle=nuzzle, blink=blink)
    if lt > 0.4:                                          # steam from the coffee
        dx, dy = A.source_point("mug", hgt, (440, 500))
        img = S.wisps(img, t, 540 + dx, 1350 + dy, color=CREAM, n=2, height=150, size=8, alpha=0.5 * ease((lt - 0.4) / 0.5),
                      spread=60, seed=4)
    C.fade_text(L, t, T["handle"], "@juanitocoffee", font(600, 28), (W // 2, 1432), anchor="ms", tracking=4,
                color=ORANGE)
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(17000 + i)
    img = C.bg(BGC)
    L = Layer()
    if t < T["roast"]:
        img = s_sack(img, L, t)
    elif t < T["cup"]:
        img = s_roast(img, L, t)
    elif t < T["packs"]:
        img = s_cup(img, L, t)
    elif t < T["huh"]:
        img = s_packs(img, L, t)
    elif t < T["family"]:
        img = s_huh(img, L, t)
    elif t < T["end"]:
        img = s_family(img, L, t)
    else:
        img = s_end(img, L, t)
    header(L, ease(t / 0.5))
    img = L.apply(img)
    img = C.grain(img, rng, 0.026)
    if t > DURATION - 0.3:
        img *= 0.3 + 0.7 * ease((DURATION - t) / 0.3)
    return C.to_u8(img).tobytes()


if __name__ == "__main__":
    if "--cues" in sys.argv:
        os.makedirs(C.BUILD, exist_ok=True)
        p = os.path.join(C.BUILD, NAME + "_cues.json")
        json.dump({"duration": DURATION, "fps": C.FPS, "cues": [{"name": n, "t": round(tt, 3)} for n, tt in cues()]},
                  open(p, "w"), indent=1)
        print(p)
    else:
        C.run(render, DURATION, NAME, sys.argv[1:])
