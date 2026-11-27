"""Soundtrack for T2 (Noah's shift): lo-fi bed made in code + effects made with earshot, placed on
the cue times exported by `t2_noah.py --cues`. Run with a Python that has soundfile (earshot's venv).
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from audio import BEAT, CHORDS, ROOT, SR, Track

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SFX = os.path.join(BUILD, "sfx")
J = json.load(open(os.path.join(BUILD, "t2_noah_cues.json")))
DUR = J["duration"]
CUES = {}
for c in J["cues"]:
    CUES.setdefault(c["name"], []).append(c["t"])
_cache = {}


def smp(name, pitch=1.0):
    key = (name, pitch)
    if key not in _cache:
        p = os.path.join(SFX, name + ".wav")
        if not os.path.exists(p):
            p = os.path.join(SFX, "cand", name + ".wav")
        x, sr = sf.read(p)
        if x.ndim > 1:
            x = x.mean(1)
        if sr != SR:
            x = resample_poly(x, SR, sr)
        if pitch != 1.0:
            x = resample_poly(x, 100, int(round(100 * pitch)))
        pk = np.abs(x).max()
        _cache[key] = x / pk if pk > 0 else x
    return _cache[key]


def build(path):
    tr = Track(DUR, seed=91)

    def put(name, t, gain=0.3, pitch=1.0, pan=0.0, rev=0.12):
        tr.add(smp(name, pitch), t, gain, pan=pan, rev=rev)

    one = lambda k: CUES[k][0]
    HUH, FAM, END = one("huh"), one("family"), one("end")
    prog = ["Fmaj7", "G6", "Am7", "Cmaj7"]
    tr.vinyl(0.008)

    def groove(g0, g1, drums=True, level=1.0):
        k, t0 = 0, g0
        while t0 < g1 - 1e-6:
            ch = prog[k % 4]
            t1 = min(t0 + 2.0, g1)
            tr.pad(CHORDS[ch], t0, t1 - 0.05, gain=0.05 * level, cutoff=1100)
            r = ROOT[ch]
            for off, dur, dm in ((0, 0.4, 0), (0.75, 0.2, 12), (1.0, 0.4, 7), (1.5, 0.3, 12)):
                if t0 + off < g1 - 0.05:
                    tr.bass(r + dm, t0 + off, dur, 0.2 * level)
            if drums:
                tr.arp(ch, t0, t1, step=0.25, gain=0.016)
            t0 += 2.0
            k += 1
        if drums:
            b, i = g0, 0
            while b < g1 - 1e-6:
                if i % 2 == 0:
                    tr.kick(b, 0.5)
                else:
                    tr.clap(b, 0.07)
                tr.hat(b + BEAT / 2, 0.035, open_=(i % 4 == 3))
                b += BEAT
                i += 1

    groove(1.0, 3.0, drums=False, level=0.8)        # sack: just chords and bass
    groove(3.0, HUH)                                 # roaster, cupping, packs
    groove(FAM, END)                                 # family shot
    tr.pad(CHORDS["Fmaj7"] + [72], END, DUR - 0.2, gain=0.07, cutoff=900)
    tr.bass(ROOT["Fmaj7"], END, 1.8, 0.2)
    tr.impact(END, 0.3)
    for k, m in enumerate((77, 81, 84, 88)):
        tr.bell(m, END + k * 0.16, 0.06, pan=-0.3 + 0.2 * k)

    # ---------------------------------------------------------------- effects
    put("pop", one("pop"), 0.34, pitch=0.9)
    put("rustle", one("rustle"), 0.22)
    put("yap", 1.0, 0.16, rev=0.15)
    for t in CUES["cut"]:
        put("whoosh", t - 0.12, 0.13)
        put("pop", t + 0.02, 0.24)
    for k, t in enumerate(CUES["crack"]):
        put("crack", t, 0.3, pitch=1.0 + 0.15 * k, pan=0.3, rev=0.08)
        put("shutter", t + 0.03, 0.12, pan=0.3)
    for k, t in enumerate(CUES["name"]):
        tr.bell([81, 84, 88, 86][k], t, 0.08, pan=[-0.4, -0.15, 0.15, 0.4][k])
        put("blip", t, 0.08)
    for k, t in enumerate(CUES["swap"]):
        if k:
            put("glitch_short", t, 0.13, pan=0.3)
        put("whoosh", t + 0.04, 0.12, pan=0.3)
    for t in CUES["resolve"]:
        put("shine", t - 0.12, 0.2, pan=0.3)
        put("sparkle", t, 0.1, pan=0.3, rev=0.3)
    put("yap", CUES["resolve"][2] + 0.5, 0.15, pan=-0.3, rev=0.15)
    # the side-eye: music stops on a record scratch
    put("scratch", HUH - 0.08, 0.28)
    put("shutter", one("tick"), 0.2, pan=0.35)
    put("boop", one("who"), 0.22, pitch=0.85, pan=-0.3)
    put("boop", one("who") + 0.5, 0.2, pitch=1.15, pan=-0.3)
    put("stamp", one("incl") - 0.03, 0.34, pan=0.3)
    put("sparkle", one("incl") + 0.04, 0.1, pan=0.3, rev=0.3)
    t, gap = one("incl") + 0.45, 0.2                 # a reluctant tail starts thumping
    while t < FAM - 0.1:
        put("thump", t, 0.18, pitch=1.3, pan=-0.4, rev=0.03)
        gap = max(0.08, gap * 0.88)
        t += gap
    put("whoosh", FAM - 0.1, 0.14)
    for k, t in enumerate(CUES["pack_pop"]):
        put("pop", t, 0.24, pitch=1.0 + 0.12 * k, pan=-0.45 + 0.3 * k)
    put("yap", one("yap") + 0.02, 0.2, rev=0.15)
    put("dogpant_1", one("yap") + 0.4, 0.1, rev=0.05)
    put("magic", END - 0.1, 0.1, rev=0.4)
    put("twinkle", END + 0.5, 0.1, rev=0.3)
    for t in CUES["blip"]:
        put("blip", t, 0.12)
    return tr.write(path, fade=0.6)


if __name__ == "__main__":
    print(build(os.path.join(BUILD, "t2_noah.wav")))
