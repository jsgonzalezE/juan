"""T1 — THE SNIFF TEST. Hand-made pixel-art Noah, Juanito's self-appointed Head of Quality,
pops out of a sack of Huila green coffee and sniff-tests the four new packs.

Timeline lives in CUES (also exported for the sound design): python3 t1_sniff_test.py --cues
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

import common as C
import noah as N
import props as P
import rig
import stage as S
from fx import INK, ORANGE, H, W, Layer, clamp01, composite, ease, ease_out, font

NAME = "t1_sniff_test"
DURATION = 23.0
BGC = (17, 16, 16)
CREAM = (240, 228, 206)
SOFT = (176, 166, 152)
SC = 7
FLOOR = 1420
NX, PX_ = 250, 800                 # Noah's mark, hero pack slot (centre x)
PW = 430                           # hero pack width
PACKS = ["color", "cherries", "mule", "dog"]
ROW_W, ROW_GAP = 222, 32
ROW_X0 = (W - (4 * ROW_W + 3 * ROW_GAP)) // 2 + ROW_W // 2
ROW_BOTTOM = 690

# ---------------------------------------------------------------- timeline (seconds)
T = dict(
    wob1=0.55, wob2=0.95, knot=1.35, head=1.6, look_l=2.0, look_r=2.3, look_c=2.6,
    text_origin=2.6, sniff0=2.9, duck=3.7, leap=3.85, land=4.3,
    # from here on the cuts sit on a 120 BPM grid (0.5 s beats) so the music can lock to them
    morph=4.5, pack1=5.5, sniff1=5.7, stamp1=6.5,
    swap2=7.0, pack2=7.5, sniff2=7.7, stamp2=8.5,
    swap3=9.0, pack3=9.5, sniff3=9.7, stamp3=10.5, hop_a=10.85, hop_b=11.15,
    swap4=11.5, pack4=12.0, sniff4=12.15, pawup=12.6, freeze=13.0, bracket=13.2,
    plate=13.45, tilt_a=14.05, tilt_b=14.45, close=14.9, back=15.9, stamp4=17.0,
    family=18.0, row=(18.0, 18.25, 18.5, 18.75), varieties=19.0, line1=19.5, line2=20.0,
    end=21.0, logo=21.1, soon=21.5, handle=21.75,
)
STAMPS = [T["stamp1"], T["stamp2"], T["stamp3"], T["stamp4"]]
LEAP_T = (T["leap"], T["land"])


def cues():
    """Named sound cues (time in seconds) for the sound design."""
    c = [("sack_rustle", T["wob1"]), ("sack_rustle", T["wob2"]), ("pop_soft", T["knot"]),
         ("pop_soft", T["head"]), ("sniff", T["sniff0"]), ("sniff", T["sniff0"] + 0.3),
         ("jump", T["leap"]), ("land", T["land"]), ("morph", T["morph"]), ("resolve", T["pack1"]),
         ("sniff", T["sniff1"]), ("sniff", T["sniff1"] + 0.28), ("stamp", T["stamp1"]),
         ("swap", T["swap2"]), ("resolve", T["pack2"]), ("sniff", T["sniff2"]), ("stamp", T["stamp2"]),
         ("swap", T["swap3"]), ("resolve", T["pack3"]), ("sniff", T["sniff3"]), ("stamp", T["stamp3"]),
         ("hop", T["hop_a"]), ("hop", T["hop_b"]),
         ("swap", T["swap4"]), ("resolve", T["pack4"]), ("sniff", T["sniff4"]),
         ("freeze", T["freeze"]), ("tick", T["bracket"]), ("plate", T["plate"]),
         ("huh", T["tilt_a"]), ("huh", T["tilt_b"]), ("zoom", T["close"]), ("zoom_out", T["back"]),
         ("stamp", T["stamp4"]), ("sparkle", T["stamp4"] + 0.05), ("family", T["family"])]
    c += [("pack_pop", t) for t in T["row"]]
    c += [("chime", T["varieties"]), ("end", T["end"]), ("logo", T["logo"]), ("blip", T["soon"]),
          ("blip", T["handle"])]
    return sorted(c, key=lambda x: x[1])


# ---------------------------------------------------------------- assets
SACK_B, SACK_F = P.sack()
SACK_SC = 8
SACK_W, SACK_H = P.SW * SACK_SC, P.SH * SACK_SC
PAW, STAMP = P.paw(), P.stamp()
LOGO_W = 250
LOGO_A = C.logo_alpha(LOGO_W)

_wc = Image.open(os.path.join(C.HERE, "assets", "wc_mule_dog.jpg")).convert("RGB")
PLATE = np.asarray(_wc.crop((416, 1076, 676, 1336)).resize((372, 372), Image.LANCZOS)).astype(np.float32) / 255


def sack_rgba():
    """Whole sack (back+front) as one RGBA image at screen scale, for the pixel morph."""
    comp = SACK_B.copy()
    a = SACK_F[..., 3:4]
    comp[..., :3] = comp[..., :3] * (1 - a) + SACK_F[..., :3] * a
    comp[..., 3] = np.maximum(comp[..., 3], SACK_F[..., 3])
    return np.repeat(np.repeat(comp, SACK_SC, 0), SACK_SC, 1)


SACK_IMG = sack_rgba()


def noah(img, cx, bottom, scale=SC, squash=(1, 1), clip=None, **pose):
    return S.blit(img, rig.sprite(**pose), cx, bottom, scale=scale, squash=squash, clip_bottom=clip)


def floor(img, a=1.0):
    y = FLOOR + 4
    xs = np.arange(60, W - 60, 12)
    for x in xs:
        img[y:y + 3, x:x + 4] = img[y:y + 3, x:x + 4] * (1 - 0.5 * a) + np.array(SOFT, np.float32) / 255 * 0.5 * a * 0.6
    return img


def shadow(img, cx, w, a=0.5):
    """Soft contact shadow on the floor."""
    h = 14
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.clip(1 - ((xx - w / 2) / (w / 2)) ** 2 - ((yy - h / 2) / (h / 2)) ** 2, 0, 1) * a
    return composite(img, np.zeros((h, w, 3), np.float32), m.astype(np.float32), (int(cx - w / 2), FLOOR - 2))


def say(L, t, t0, t1, text, x=NX + 14, y=900, size=38, color=CREAM, stamp_img=None, img=None):
    """Noah's 'voice': a small italic caption above his head (with an optional paw stamp)."""
    if not (t0 <= t < t1):
        return img
    a = ease((t - t0) / 0.18) * clamp01((t1 - t) / 0.22)
    f = font(300, size, True)
    L.text((x, y), text, f, fill=color, anchor="ms", alpha=a)
    return img


def stamp_mark(img, t, t0, t1, x, y):
    if not (t0 <= t < t1):
        return img
    u = (t - t0) / 0.14
    sc = 8 if u < 0.5 else 6            # thup: lands big, settles
    a = clamp01((t1 - t) / 0.22)
    return S.blit(img, STAMP, x, y, scale=sc, alpha=a)


def pack_swap(img, t, t_swap, t_crisp, old, new):
    """Old pack breaks into big pixels, the new one resolves in the same slot."""
    mid = (t_swap + t_crisp) / 2 - 0.05
    if t < mid:
        k = 1 - ease((t - t_swap) / (mid - t_swap)) * 0.82
        return S.pack(img, old, PW, PX_, FLOOR, k=k)
    k = 0.18 + 0.82 * ease((t - mid) / (t_crisp - mid))
    return S.pack(img, new, PW, PX_, FLOOR, k=k)


def sniff_pose(lt, eyes="happy"):
    """Nose lifted, twitching; eyes closed in bliss."""
    tw = int(lt * 9) % 2
    return dict(eyes=eyes, mouth="closed", nose=1 if tw else 0, head_dy=-1 if tw else 0)


def aroma(img, t, t0, dur=0.75, n=7):
    """A few cream dots drawn from the pack to Noah's nose."""
    for k in range(n):
        u = (t - t0 - k * 0.05) / dur
        if not 0 <= u < 1:
            continue
        x0, y0 = PX_ - 170, FLOOR - 470 + (k % 3) * 50
        x1, y1 = NX + 6, FLOOR - 300
        e = ease(u)
        x = x0 + (x1 - x0) * e
        y = y0 + (y1 - y0) * e - 46 * math.sin(u * math.pi) + 10 * math.sin(k * 2.1 + u * 6)
        img = S.square(img, x, y, 6, CREAM, 0.75 * math.sin(u * math.pi))
    return img


def header(L, a=1.0):
    L.text((64, 150), "JUANITO COFFEE", font(600, 20), tracking=6, fill=(196, 186, 172), alpha=a)
    L.text((1016, 150), "NEW HARVEST", font(400, 20), tracking=6, anchor="ra", fill=(132, 124, 114), alpha=a)


# ---------------------------------------------------------------- acts
def act_sack(img, L, t):
    """0 – 4.5: the sack wobbles, Noah peeks out, sniffs, leaps to his mark."""
    cx, bottom = PX_, FLOOR
    # wobble
    sq = (1.0, 1.0)
    lean = 0
    for t0 in (T["wob1"], T["wob2"]):
        u = (t - t0) / 0.3
        if 0 <= u < 1:
            k = math.sin(u * math.pi)
            sq = (1 + 0.035 * k, 1 - 0.045 * k)
            lean = int(6 * math.sin(u * math.pi * 2))
    if T["duck"] <= t < T["leap"]:
        k = math.sin((t - T["duck"]) / (T["leap"] - T["duck"]) * math.pi)
        sq = (1 + 0.04 * k, 1 - 0.05 * k)
    if T["leap"] <= t < T["leap"] + 0.25:
        k = math.sin((t - T["leap"]) / 0.25 * math.pi)
        sq = (1 - 0.02 * k, 1 + 0.03 * k)
    img = shadow(img, cx, SACK_W - 40)
    img = S.blit(img, SACK_B, cx + lean, bottom, scale=SACK_SC, squash=sq)
    rim_y = bottom - (P.SH - 16) * SACK_SC * sq[1]          # bottom of the mouth opening

    def head(rows_visible, **pose):
        """Noah's head inside the sack with `rows_visible` sprite rows showing above the rim."""
        top = rim_y - rows_visible * SC
        return noah(img, cx + lean, top + rig.CH * SC, **pose)

    if T["knot"] <= t < T["leap"]:
        if t < T["head"]:                      # only the topknot shows
            rise = ease_out((t - T["knot"]) / 0.14)
            img = head(3 + 11 * rise, head_only=True, eyes="open", mouth="closed",
                       topknot=1 if t - T["knot"] < 0.1 else 0)
        elif t < T["duck"]:
            u = (t - T["head"]) / 0.2
            rows = 14 + 14 * ease_out(u) + 1.5 * math.sin(clamp01(u) * math.pi)
            eyes = "open"
            if T["look_l"] <= t < T["look_r"]:
                eyes = "left"
            elif T["look_r"] <= t < T["look_c"]:
                eyes = "right"
            elif T["look_c"] + 0.22 <= t < T["look_c"] + 0.34:
                eyes = "closed"
            pose = dict(head_only=True, eyes=eyes, mouth="closed",
                        perk=1 if t - T["head"] < 0.12 else 0, topknot=1 if 0.04 < t - T["head"] < 0.16 else 0)
            if t >= T["sniff0"]:               # rises a little more to sniff the air
                rows = 28 + 9 * ease_out((t - T["sniff0"]) / 0.18)
                pose = dict(head_only=True, **sniff_pose(t - T["sniff0"]))
                if t > T["sniff0"] + 0.62:
                    pose = dict(head_only=True, eyes="happy", mouth="tongue")
            img = head(rows, **pose)
        else:                                   # duck before the leap
            u = (t - T["duck"]) / (T["leap"] - T["duck"])
            img = head(37 - 27 * ease(u), head_only=True, eyes="open", mouth="closed")
        if T["head"] + 0.1 <= t < T["duck"]:    # paws over the rim
            for dx in (-96, 82):
                img = S.blit(img, PAW, cx + lean + dx, rim_y + 30, scale=SC)
    def leaping():
        u = (t - T["leap"]) / (T["land"] - T["leap"])
        x, y = S.hop(u, (cx - 20, rim_y + 150), (NX, FLOOR), 380)
        st = (0.94, 1.08) if u < 0.5 else (1.0, 1.0)
        return noah(img, x, y, squash=st, eyes="wide" if u < 0.6 else "open", mouth="tongue",
                    perk=2 if u < 0.7 else 1, topknot=1, tail=-1)

    early = T["leap"] <= t < T["leap"] + 0.3 * (T["land"] - T["leap"])
    if early:                                   # still coming out of the sack: behind its front
        img = leaping()
    img = S.blit(img, SACK_F, cx + lean, bottom, scale=SACK_SC, squash=sq)
    for t0 in (T["wob1"], T["wob2"], T["leap"]):
        img = S.dust(img, cx, rim_y + 6, t0, t, color=(190, 170, 136), seed=int(t0 * 10))
    # the leap
    if T["leap"] <= t < T["land"]:
        if not early:
            img = leaping()
    elif t >= T["land"]:
        u = (t - T["land"]) / 0.16
        k = math.sin(clamp01(u) * math.pi)
        img = shadow(img, NX, 250)
        img = noah(img, NX, FLOOR, squash=(1 + 0.07 * k, 1 - 0.09 * k), eyes="happy" if u < 1.2 else "open",
                   mouth="tongue", topknot=-1 if u < 0.6 else 0, tail=(1 if int(t * 10) % 2 else -1))
        img = S.dust(img, NX, FLOOR - 6, T["land"], t, seed=3)
    # brand line under the sack
    a = ease((t - T["text_origin"]) / 0.35) * clamp01((T["leap"] + 0.1 - t) / 0.3)
    if a > 0:
        L.text((cx, FLOOR + 92), "GREEN COFFEE", font(500, 26), anchor="ms", tracking=12, fill=CREAM, alpha=a)
        f1, f2 = font(300, 34, True), font(500, 20)
        w1 = f1.getlength("(origin ")
        w2 = sum(f2.getlength(ch) + 8 for ch in "HUILA  COLOMBIA")
        x0 = cx - (w1 + w2 + f1.getlength(")")) / 2
        L.text((x0, FLOOR + 148), "(origin ", f1, fill=SOFT, anchor="ls", alpha=a)
        L.text((x0 + w1, FLOOR + 146), "HUILA  COLOMBIA", f2, fill=CREAM, anchor="ls", tracking=8, alpha=a)
        L.text((x0 + w1 + w2 + 2, FLOOR + 148), ")", f1, fill=SOFT, anchor="ls", alpha=a)
    return img


def act_morph(img, L, t):
    """4.5 – 5.3: green becomes new — the sack breaks into big pixels and resolves as pack 1."""
    u = (t - T["morph"]) / (T["pack1"] - T["morph"])
    if u < 0.42:
        k = u / 0.42
        cell = [7, 14, 28, 42, 56][min(4, int(k * 5))]
        q = N.pixelate(SACK_IMG, cell)
        x0, y0 = int(PX_ - SACK_W / 2), FLOOR - SACK_H
        img = composite(img, np.ascontiguousarray(q[..., :3]), q[..., 3] * (1 - 0.25 * k), (x0, y0))
    else:
        k = (u - 0.42) / 0.58
        img = S.pack(img, "color", PW, PX_, FLOOR, k=0.12 + 0.88 * ease(k))
    return img


def noah_host(img, L, t):
    """Noah on his mark for acts 2-3: every pose is keyed to the timeline."""
    lt_land = t - T["land"]
    pose = dict(eyes="open", mouth="closed")
    sq = (1.0, 1.0)
    y = FLOOR
    breathe = 1 if int(t * 1.6) % 2 else 0
    pose["head_dy"] = breathe
    blink = (t % 2.9) > 2.78

    def stamp_seq(ts):                       # paw up 0.22 s before the thup
        d = t - ts
        if -0.26 <= d < -0.12:
            return dict(paw=1, eyes="open", mouth="closed")
        if -0.12 <= d < 0.5:
            return dict(paw=2, eyes="happy", mouth="tongue" if d > 0 else "closed", head_dy=0)
        if 0.5 <= d < 0.6:
            return dict(paw=1, eyes="happy", mouth="tongue")
        return None

    # morph: ears perk, eyes wide, then a tilt
    if T["morph"] <= t < T["pack1"]:
        d = t - T["morph"]
        pose = dict(eyes="wide", mouth="closed", perk=2 if d < 0.5 else 1, topknot=1 if d < 0.12 else 0)
        if d > 0.5:
            pose = dict(eyes="right", mouth="closed", tilt=1, perk=1)
    for k, (ts, tn) in enumerate(((T["sniff1"], T["stamp1"]), (T["sniff2"], T["stamp2"]),
                                  (T["sniff3"], T["stamp3"]), (T["sniff4"], T["pawup"]))):
        if tn - 1.1 <= t < ts and t >= [T["pack1"], T["pack2"], T["pack3"], T["pack4"]][k] - 0.35:
            pose = dict(eyes="right", mouth="closed", perk=1 if t < ts - 0.15 else 0)
        dur = min(0.55, tn - ts - 0.24)
        if ts <= t < ts + dur:
            pose = sniff_pose(t - ts)
    for ts in STAMPS[:3]:
        p = stamp_seq(ts)
        if p:
            pose = p
    # swaps: he watches the pack change
    for a, b in ((T["swap2"], T["pack2"]), (T["swap3"], T["pack3"]), (T["swap4"], T["pack4"])):
        if a <= t < b:
            pose = dict(eyes="right", mouth="closed", perk=1, tilt=1 if t - a > 0.25 else 0)
    # two excited hops after the third stamp
    for th in (T["hop_a"], T["hop_b"]):
        u = (t - th) / 0.3
        if 0 <= u < 1:
            y = FLOOR - 70 * 4 * u * (1 - u)
            pose = dict(eyes="happy", mouth="pant_a", perk=1, topknot=1, tail=1 if u < 0.5 else -1)
        elif 1 <= u < 1.25:
            k = math.sin((u - 1) / 0.25 * math.pi)
            sq = (1 + 0.05 * k, 1 - 0.07 * k)
            pose = dict(eyes="happy", mouth="pant_b", topknot=-1)
    if T["stamp3"] + 0.6 <= t < T["hop_a"]:
        pose = dict(eyes="happy", mouth="pant_a" if int(t * 8) % 2 else "pant_b", tail=1 if int(t * 10) % 2 else -1)
    # pack 4: the paw rises... and freezes
    if T["pawup"] <= t < T["stamp4"] - 0.12:
        pose = dict(paw=1 if t < T["pawup"] + 0.12 else 2, eyes="open", mouth="closed")
        if t >= T["freeze"]:
            pose.update(eyes="wide", perk=2 if t < T["freeze"] + 0.14 else 1,
                        topknot=1 if t < T["freeze"] + 0.1 else 0)
        if t >= T["bracket"] + 0.1:
            pose.update(eyes="right", perk=1)
        if t >= T["plate"] + 0.25:
            pose.update(eyes="wide", perk=1)
        if T["tilt_a"] <= t < T["tilt_b"]:
            pose.update(tilt=-1, eyes="open", perk=0)
        elif T["tilt_b"] <= t < T["close"]:
            pose.update(tilt=1, eyes="open", perk=0)
        if t >= T["back"]:
            wag = 14 if t > T["back"] + 0.45 else 6
            pose = dict(paw=2, eyes="squint", mouth="flat", tail=1 if int(t * wag) % 2 else -1)
    p = stamp_seq(T["stamp4"])
    if p and t >= T["stamp4"] - 0.12:
        pose = dict(p)
        pose["tail"] = 1 if int(t * 14) % 2 else -1
    if t >= T["stamp4"] + 0.6:
        pose = dict(eyes="happy", mouth="pant_a" if int(t * 8) % 2 else "pant_b",
                    tail=1 if int(t * 12) % 2 else -1)
    if blink and pose.get("eyes") == "open":
        pose["eyes"] = "closed"
    img = shadow(img, NX, 250)
    return noah(img, NX, y, squash=sq, **pose)


def act_test(img, L, t):
    """5.3 – 17.5: the sniff test."""
    # which pack
    if t < T["swap2"]:
        img = S.pack(img, "color", PW, PX_, FLOOR)
    elif t < T["pack2"]:
        img = pack_swap(img, t, T["swap2"], T["pack2"], "color", "cherries")
    elif t < T["swap3"]:
        img = S.pack(img, "cherries", PW, PX_, FLOOR)
    elif t < T["pack3"]:
        img = pack_swap(img, t, T["swap3"], T["pack3"], "cherries", "mule")
    elif t < T["swap4"]:
        img = S.pack(img, "mule", PW, PX_, FLOOR)
    elif t < T["pack4"]:
        img = pack_swap(img, t, T["swap4"], T["pack4"], "mule", "dog")
    else:
        img = S.pack(img, "dog", PW, PX_, FLOOR)
    for ts in (T["sniff1"], T["sniff2"], T["sniff3"], T["sniff4"]):
        img = aroma(img, t, ts - 0.1)
    img = noah_host(img, L, t)
    # verdicts
    lines = [(T["stamp1"], T["swap2"] - 0.05, "(new look: approved)"),
             (T["stamp2"], T["swap3"] - 0.05, "(approved)"),
             (T["stamp3"], T["swap4"] - 0.05, "(muy approved)")]
    for ts, te, txt in lines:
        say(L, t, ts, te, txt)
        f = font(300, 38, True)
        img = stamp_mark(img, t, ts, te, NX + 14 + f.getlength(txt) / 2 + 40, 912)
    for ts in STAMPS:
        for k, (dx, dy) in enumerate(((176, -392), (222, -300), (150, -250))):
            img = S.sparkle(img, NX + dx, FLOOR + dy, ts + 0.03 * k, t)
    # pack 4: the painted dog
    pw, ph = S.pack_size("dog", PW)
    bx0, by0 = PX_ - pw / 2, FLOOR - ph
    dog_box = (bx0 + 0.415 * pw, by0 + 0.815 * ph, bx0 + 0.585 * pw, by0 + 0.975 * ph)
    if T["bracket"] <= t < T["stamp4"] + 0.25:
        a = (1.0 if int((t - T["bracket"]) * 12) % 2 or t > T["bracket"] + 0.3 else 0.3) * clamp01((T["stamp4"] + 0.25 - t) / 0.25)
        x0, y0, x1, y1 = [int(v) for v in dog_box]
        s = 16
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            L.line([(x, y + dy * s), (x, y), (x + dx * s, y)], fill=CREAM, width=3, alpha=a)
    if T["plate"] <= t < T["close"]:
        u = ease_out((t - T["plate"]) / 0.22)
        a = u * clamp01((T["close"] - t) / 0.12 + 1)
        ps = 372
        x, y = NX + 10 - ps // 2, 330
        k = int(ps * (0.7 + 0.3 * u)) // 2 * 2
        pl = np.asarray(Image.fromarray(C.to_u8(PLATE)).resize((k, k), Image.NEAREST if u < 1 else Image.LANCZOS)).astype(np.float32) / 255
        ox = x + (ps - k) // 2
        oy = y + (ps - k) // 2
        composite(img, pl, np.full((k, k), a, np.float32), (ox, oy))
        L.rect((ox - 8, oy - 8, ox + k + 7, oy + k + 7), outline=CREAM, width=2, alpha=0.9 * a)
        L.line([(ox + k + 7, oy + k + 7), (int(dog_box[0]), int(dog_box[1]))], fill=CREAM, width=1, alpha=0.35 * a)
        say(L, t, T["plate"] + 0.3, T["close"], "(...who's HE?)", y=776)
    say(L, t, T["back"] + 0.3, T["stamp4"] - 0.05, "(not jealous.)")
    say(L, t, T["stamp4"], T["family"] - 0.05, "(...approved.)")
    img = stamp_mark(img, t, T["stamp4"], T["family"] - 0.05, NX + 14 + font(300, 38, True).getlength("(...approved.)") / 2 + 40, 912)
    if T["stamp4"] + 0.15 <= t < T["family"]:
        a = ease((t - T["stamp4"] - 0.15) / 0.3) * clamp01((T["family"] - t) / 0.2)
        L.text((PX_, FLOOR + 92), "(dog included.)", font(300, 36, True), anchor="ms", fill=SOFT, alpha=a)
    return img


def act_close(img, L, t):
    """14.75 – 15.75: crash zoom on the deadpan face."""
    u = t - T["close"]
    sc = [9, 12, 15][min(2, int(u / 0.045))]
    blink = 0.5 < u < 0.62
    spr = rig.sprite(head_only=True, eyes="closed" if blink else "squint", mouth="flat")
    return S.blit(img, spr, W // 2, 900 + 36 * sc - 40, scale=sc)


def act_family(img, L, t):
    """17.5 – 20.3: the four packs in a row, the varieties, Noah's sign-off."""
    lt = t - T["family"]
    out = ease((t - (T["end"] - 0.3)) / 0.3) if t > T["end"] - 0.3 else 0.0
    for i, key in enumerate(PACKS):
        k = ease((t - T["row"][i]) / 0.42) * (1 - out)
        img = S.pack(img, key, ROW_W, ROW_X0 + i * (ROW_W + ROW_GAP), ROW_BOTTOM, k=k, glow=0.16)
    a = (1 - out)
    xs = np.arange(60, W - 60, 12)
    for x in xs:                                         # shelf line
        img[ROW_BOTTOM + 6:ROW_BOTTOM + 9, x:x + 4] += 0.16 * a * ease(lt / 0.3)
    # Noah, centred below, counts them
    pose = dict(eyes="open", mouth="closed")
    for i, tr in enumerate(T["row"]):
        if tr <= t < tr + 0.25:
            pose = dict(eyes="left" if i < 2 else "right", mouth="closed", perk=1 if t - tr < 0.1 else 0)
    if t >= T["row"][3] + 0.3:
        pose = dict(eyes="happy" if t < T["varieties"] + 0.5 else "open", mouth="tongue")
    if t >= T["line1"]:
        pose = dict(eyes="open", mouth="tongue", paw=2 if T["line2"] <= t < T["line2"] + 0.5 else 0)
    if t >= T["line2"] + 0.5:
        pose = dict(eyes="happy", mouth="pant_a" if int(t * 8) % 2 else "pant_b",
                    tail=1 if int(t * 12) % 2 else -1)
    pose["tail"] = pose.get("tail", 1 if int(t * 7) % 2 else -1)
    ncx = W // 2
    nb = 1372
    img = shadow(img, ncx, 250, 0.5 * a)
    if out < 1:
        spr = rig.sprite(**pose)
        img = S.blit(img, spr, ncx, nb, scale=SC, alpha=1.0)
    al = ease((t - T["varieties"]) / 0.35) * a
    L.text((W // 2, ROW_BOTTOM + 74), "(four new varieties)", font(300, 32, True), anchor="ms", fill=SOFT, alpha=al)
    names = "JAVA   ·   CASTILLO   ·   GEISHA   ·   BOURBON"
    L.text((W // 2, ROW_BOTTOM + 130), names, font(500, 26), anchor="ms", tracking=5, fill=CREAM, alpha=al)
    L.text((W // 2, nb + 76), "New look?", font(400, 40), anchor="ms", fill=CREAM,
           alpha=ease((t - T["line1"]) / 0.25) * a)
    L.text((W // 2, nb + 132), "I sniffed it first.", font(300, 40, True), anchor="ms", fill=ORANGE,
           alpha=ease((t - T["line2"]) / 0.25) * a)
    return img


def act_end(img, L, t):
    """20.3 – 22: logo, coming soon, handle. Noah stays."""
    lt = t - T["end"]
    k = ease((t - T["logo"]) / 0.45)
    if k > 0:
        cell = [40, 24, 12, 6, 3, 1][min(5, int(k * 5.99))]
        la = LOGO_A
        if cell > 1:
            h, w = la.shape
            sm = np.asarray(Image.fromarray((la * 255).astype(np.uint8)).resize((max(1, w // cell), max(1, h // cell)), Image.BOX))
            la = np.asarray(Image.fromarray(sm).resize((w, h), Image.NEAREST)).astype(np.float32) / 255
        s = np.empty(la.shape + (3,), np.float32)
        s[:] = np.array(INK, np.float32) / 255
        composite(img, s, la * min(1.0, k * 1.5), ((W - LOGO_W) // 2, 330))
    C.fade_text(L, t, T["soon"], "COMING SOON", font(500, 30), (W // 2, 742), anchor="ms", tracking=14, color=CREAM)
    C.fade_text(L, t, T["soon"] + 0.12, "green coffee  ·  Huila, Colombia", font(300, 32, True), (W // 2, 800),
                anchor="ms", color=SOFT)
    C.fade_text(L, t, T["handle"], "@juanitocoffee", font(600, 28), (W // 2, 1372 + 84), anchor="ms",
                tracking=4, color=ORANGE)
    ncx, nb = W // 2, 1372
    blink = 0.95 < lt < 1.07
    pose = dict(eyes="closed" if blink else "open", mouth="tongue", tail=1 if int(t * 7) % 2 else -1,
                head_dy=1 if int(t * 1.6) % 2 else 0)
    if lt > 1.3:
        pose = dict(sniff_pose(lt - 1.3), tail=pose["tail"]) if lt < 1.55 else dict(eyes="happy", mouth="tongue", tail=pose["tail"])
    img = shadow(img, ncx, 250)
    return S.blit(img, rig.sprite(**pose), ncx, nb, scale=SC)


def render(i):
    t = i / C.FPS
    rng = np.random.default_rng(15000 + i)
    img = C.bg(BGC)
    L = Layer()
    if T["close"] <= t < T["back"]:
        img = act_close(img, L, t)
    elif t < T["family"]:
        img = floor(img, ease(t / 0.4))
        if t < T["morph"]:
            img = act_sack(img, L, t)
        elif t < T["pack1"]:
            img = act_morph(img, L, t)
            img = noah_host(img, L, t)
        else:
            img = act_test(img, L, t)
        header(L, ease(t / 0.5))
    elif t < T["end"]:
        img = act_family(img, L, t)
        header(L)
    else:
        img = act_end(img, L, t)
        header(L)
    img = L.apply(img)
    img = C.grain(img, rng, 0.028)
    if t < 0.35:
        img *= ease(t / 0.35)
    if t > DURATION - 0.3:
        img *= 0.3 + 0.7 * ease((DURATION - t) / 0.3)
    return C.to_u8(img).tobytes()


if __name__ == "__main__":
    if "--cues" in sys.argv:
        os.makedirs(C.BUILD, exist_ok=True)
        p = os.path.join(C.BUILD, NAME + "_cues.json")
        json.dump({"duration": DURATION, "fps": C.FPS, "cues": [{"name": n, "t": round(t, 3)} for n, t in cues()]},
                  open(p, "w"), indent=1)
        print(p)
    else:
        C.run(render, DURATION, NAME, [a for a in sys.argv[1:]])
