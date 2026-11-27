"""T2 — NOAH'S SHIFT. The client's own pixel-art Noah illustrations (assets/noah_pix) take the new
harvest from green coffee to the new packs: sack -> first crack -> cupping the four new
varieties -> presenting the four real packs -> a jealous side-eye -> coming soon.

    python3 t2_noah.py --stills 1,4,7      # previews
    python3 t2_noah.py --cues              # build/t2_noah_cues.json for the sound design
    python3 t2_noah.py                     # build/t2_noah_silent.mp4
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

import common as C
import pixref as PR
import stage as S
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, ease, ease_out, font

NAME = "t2_noah"
DURATION = 22.0
BGC = (17, 16, 16)
CREAM = (240, 228, 206)
SOFT = (176, 166, 152)
BEAT = 0.5
PACKS = ["color", "cherries", "mule", "dog"]
BASE = 1330                      # shared floor line for Noah + pack scenes
NX, PX_, PW = 300, 805, 400      # Noah centre x, pack centre x, pack width

T = dict(
    sack=0.15, origin=1.0,
    roast=3.0, crack1=3.5, crack2=4.25, crack_txt=3.6, heard_txt=4.4,
    cup=5.5, qc_txt=5.8, names=(6.5, 7.0, 7.5, 8.0),
    packs=9.0, pack=(9.0, 10.5, 12.0, 13.5), look_txt=9.4,
    huh=14.5, who_txt=14.9, incl_txt=16.0,
    family=17.5, row=(17.5, 17.7, 17.9, 18.1), q_txt=18.5, a_txt=18.9,
    end=19.5, logo=19.6, soon=20.0, handle=20.35,
)


def cues():
    c = [("pop", T["sack"]), ("rustle", T["sack"] + 0.05), ("cut", T["roast"]), ("crack", T["crack1"]),
         ("crack", T["crack2"]), ("cut", T["cup"])]
    c += [("name", t) for t in T["names"]]
    c += [("swap", t) for t in T["pack"]] + [("resolve", t + 0.5) for t in T["pack"]]
    c += [("huh", T["huh"]), ("tick", T["huh"] + 0.12), ("who", T["who_txt"]), ("incl", T["incl_txt"]),
          ("family", T["family"])]
    c += [("pack_pop", t) for t in T["row"]]
    c += [("yap", T["a_txt"]), ("end", T["end"]), ("blip", T["soon"]), ("blip", T["handle"])]
    return sorted(c, key=lambda x: x[1])


# ---------------------------------------------------------------- drawing
def noah(img, name, cx, bottom, h, t0=None, t=0.0, squash=(1.0, 1.0), accents=True, alpha=1.0, dx=0):
    """Draw an illustration with its bottom-centre at (cx, bottom); optional pop-in from t0."""
    scale = 1.0
    if t0 is not None:
        u = (t - t0) / 0.26
        if u < 0:
            return img
        if u < 1:                                  # pop: overshoot and settle, in 12 fps steps
            u = int(u * 6) / 6
            scale = 0.72 + 0.28 * (1 - (1 - u) ** 3) + 0.07 * math.sin(u * math.pi)
            alpha *= min(1.0, u * 3 + 0.34)
    hh = max(8, int(round(h * scale / 2)) * 2)
    spr = PR.sprite(name, hh, accents)
    sx, sy = squash
    if abs(sx - 1) > 0.004 or abs(sy - 1) > 0.004:
        sh, sw = spr.shape[:2]
        nw, nh = max(1, round(sw * sx)), max(1, round(sh * sy))
        yi = np.minimum((np.arange(nh) * sh / nh).astype(int), sh - 1)
        xi = np.minimum((np.arange(nw) * sw / nw).astype(int), sw - 1)
        spr = spr[yi][:, xi]
    sh, sw = spr.shape[:2]
    return composite(img, np.ascontiguousarray(spr[..., :3]), spr[..., 3] * alpha,
                     (int(round(cx - sw / 2 + dx)), int(round(bottom - sh))))


def bounce(t, start=0.0, amt=1.0):
    """A little squash on every beat: he bobs to the music."""
    if t < start:
        return (1.0, 1.0)
    u = ((t - start) % BEAT) / 0.17
    if u >= 1:
        return (1.0, 1.0)
    k = math.sin(u * math.pi) * amt
    return (1 + 0.022 * k, 1 - 0.032 * k)


def caption(L, t, t0, t1, text, x, y, size=38, color=CREAM, italic=True, weight=300, tracking=0):
    if not (t0 <= t < t1):
        return
    a = ease((t - t0) / 0.2) * clamp01((t1 - t) / 0.2)
    L.text((x, y), text, font(weight, size, italic), fill=color, anchor="ms", alpha=a, tracking=tracking)


def header(L, a=1.0):
    L.text((64, 150), "JUANITO COFFEE", font(600, 20), tracking=6, fill=(196, 186, 172), alpha=a)
    L.text((1016, 150), "NEW HARVEST", font(400, 20), tracking=6, anchor="ra", fill=(132, 124, 114), alpha=a)


def words_line(L, t, words, times, y, f, color, gap="   ·   ", tracking=5):
    """One centred line whose words appear one by one."""
    parts = []
    for i, w in enumerate(words):
        parts.append(w)
        if i < len(words) - 1:
            parts.append(gap)
    widths = [sum(f.getlength(ch) + tracking for ch in p) for p in parts]
    x = W / 2 - sum(widths) / 2
    for i, (p, wd) in enumerate(zip(parts, widths)):
        k = i // 2 if i % 2 == 0 else i // 2 + 1          # separators arrive with the next word
        a = ease((t - times[min(k, len(times) - 1)]) / 0.18)
        if a > 0:
            L.text((x, y - (1 - a) * 10), p, f, fill=color if i % 2 == 0 else SOFT, anchor="ls",
                   tracking=tracking, alpha=a)
        x += wd


def pack_slot(img, t):
    """The hero pack: each one materialises from big pixels in the same slot."""
    ts = T["pack"]
    k = max(i for i in range(4) if t >= ts[i])
    lt = t - ts[k]
    if lt < 0.5:
        if k > 0 and lt < 0.2:                       # the previous one breaks up first
            return S.pack(img, PACKS[k - 1], PW, PX_, BASE, k=1 - ease(lt / 0.2) * 0.85), k
        return S.pack(img, PACKS[k], PW, PX_, BASE, k=0.15 + 0.85 * ease((lt - (0.2 if k else 0)) / (0.3 if k else 0.5))), k
    return S.pack(img, PACKS[k], PW, PX_, BASE), k


# ---------------------------------------------------------------- scenes
def s_sack(img, L, t):
    """Green coffee: Noah pops out of the sack."""
    sq = bounce(t, 1.0, 0.8)
    img = noah(img, "sack", 540, 1250, 800, t0=T["sack"], t=t, squash=sq)
    img = S.dust(img, 540, 1232, T["sack"] + 0.05, t, color=(190, 170, 136), n=8, seed=2)
    a = ease((t - T["origin"]) / 0.35)
    if a > 0:
        L.text((W // 2, 1356), "GREEN COFFEE", font(500, 28), anchor="ms", tracking=12, fill=CREAM, alpha=a)
        f1, f2 = font(300, 36, True), font(500, 22)
        w1 = f1.getlength("(origin ")
        w2 = sum(f2.getlength(ch) + 8 for ch in "HUILA  COLOMBIA")
        x0 = W / 2 - (w1 + w2 + f1.getlength(")")) / 2
        a2 = ease((t - T["origin"] - 0.25) / 0.35)
        L.text((x0, 1418), "(origin ", f1, fill=SOFT, anchor="ls", alpha=a2)
        L.text((x0 + w1, 1416), "HUILA  COLOMBIA", f2, fill=CREAM, anchor="ls", tracking=8, alpha=a2)
        L.text((x0 + w1 + w2 + 2, 1418), ")", f1, fill=SOFT, anchor="ls", alpha=a2)
    return img


def s_roast(img, L, t):
    """First crack: his ear shoots up before anyone hears it."""
    jolt, flash = 0, False
    for tc in (T["crack1"], T["crack2"]):
        u = (t - tc) / 0.22
        if 0 <= u < 1:
            jolt = int(round(7 * math.sin(u * math.pi * 3) * (1 - u)))
            flash = True
    sparks = flash or (t > T["crack1"] and int(t * 6) % 2 == 0)
    img = noah(img, "roaster", 540, 1230, 680, t0=T["roast"], t=t, accents=sparks, dx=jolt,
               squash=bounce(t, 3.0, 0.6))
    caption(L, t, T["crack_txt"], T["cup"], "(first crack?", W // 2, 1340, 40)
    caption(L, t, T["heard_txt"], T["cup"], "I heard it first.)", W // 2, 1398, 40, color=ORANGE)
    return img


def s_cup(img, L, t):
    """Quality control: a slow push-in on the stare, the four varieties arrive on the beat."""
    lt = t - T["cup"]
    h = 620 + int(lt / 3.5 * 44 / 2) * 2
    img = noah(img, "cupping", 540, 1180 + (h - 620) // 3, h, t0=T["cup"], t=t)
    caption(L, t, T["qc_txt"], T["packs"], "(quality control)", W // 2, 470, 38, color=SOFT)
    a = ease((t - T["names"][0] + 0.15) / 0.25)
    if a > 0:
        L.text((W // 2, 1296), "FOUR NEW VARIETIES", font(500, 20), anchor="ms", tracking=10, fill=SOFT, alpha=a)
    words_line(L, t, ["JAVA", "CASTILLO", "GEISHA", "BOURBON"], T["names"], 1362, font(500, 30), CREAM)
    return img


def s_packs(img, L, t):
    """The new look: barista Noah serves the four real packs, one per bar."""
    img, k = pack_slot(img, t)
    lt = t - T["pack"][k]
    for j, (dx, dy) in enumerate(((-232, -640), (236, -520), (-246, -300))):
        img = S.sparkle(img, PX_ + dx, BASE + dy, T["pack"][k] + 0.46 + 0.05 * j, t)
    img = noah(img, "barista", NX, BASE, 690, t0=T["packs"], t=t, squash=bounce(t, 9.0),
               accents=int(t * 4) % 2 == 0)
    caption(L, t, T["look_txt"], T["huh"], "(a new look)", PX_, BASE - 716, 38)
    if lt > 0.45:
        a = ease((lt - 0.45) / 0.2)
        L.text((PX_, BASE + 62), f"0{k + 1} / 04", font(600, 20), anchor="ms", tracking=8, fill=SOFT, alpha=a)
    return img


def s_huh(img, L, t):
    """Pack four has another dog on it."""
    lt = t - T["huh"]
    img = S.pack(img, "dog", PW, PX_, BASE)
    shake = int(round(6 * math.sin(lt * 60) * clamp01(1 - lt / 0.25))) if lt < 0.25 else 0
    h = 640 + int(clamp01(lt / 3.0) * 30 / 2) * 2
    img = noah(img, "sugar_noah", NX + 6, BASE, h, dx=shake, accents=False)
    pw, ph = S.pack_size("dog", PW)
    bx0, by0 = PX_ - pw / 2, BASE - ph
    x0, y0, x1, y1 = [int(v) for v in (bx0 + 0.40 * pw, by0 + 0.805 * ph, bx0 + 0.60 * pw, by0 + 0.985 * ph)]
    if lt > 0.12:
        a = 1.0 if (lt > 0.45 or int((lt - 0.12) * 12) % 2 == 0) else 0.25
        s = 22 + int(4 * math.sin(lt * 9))
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            L.line([(x, y + dy * s), (x, y), (x + dx * s, y)], fill=ORANGE, width=5, alpha=a)
    caption(L, t, T["who_txt"], T["family"], "(...who's HE?)", NX + 6, BASE - h - 26, 40)
    caption(L, t, T["incl_txt"], T["family"], "(dog included.)", PX_, BASE + 66, 38, color=ORANGE)
    return img


ROW_W, ROW_GAP = 222, 32
ROW_X0 = (W - (4 * ROW_W + 3 * ROW_GAP)) // 2 + ROW_W // 2


def s_family(img, L, t):
    for i, key in enumerate(PACKS):
        img = S.pack(img, key, ROW_W, ROW_X0 + i * (ROW_W + ROW_GAP), 720, k=ease((t - T["row"][i]) / 0.4), glow=0.16)
    img = noah(img, "barista", 540, 1330, 540, t0=T["family"] + 0.1, t=t, squash=bounce(t, 17.5),
               accents=int(t * 4) % 2 == 0)
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
    img = noah(img, "mug", 540, 1350, 480, t0=T["end"] + 0.05, t=t, squash=bounce(t, 19.5, 0.7),
               accents=int(t * 4) % 2 == 0)
    C.fade_text(L, t, T["handle"], "@juanitocoffee", font(600, 28), (W // 2, 1432), anchor="ms", tracking=4,
                color=ORANGE)
    return img


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(16000 + i)
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
    if t < 0.3:
        img *= ease(t / 0.3)
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
