"""Soundtrack for T1 (The Sniff Test): procedural lo-fi bed + sound effects made with earshot,
placed on the cue times exported by t1_sniff_test.py --cues.

Run with a Python that has numpy, scipy and soundfile (earshot's venv works):
    python t1_audio.py            # writes build/t1_sniff_test.wav
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from audio import BEAT, CHORDS, ROOT, SR, Track, filt

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SFX = os.path.join(BUILD, "sfx")
J = json.load(open(os.path.join(BUILD, "t1_sniff_test_cues.json")))
DUR = J["duration"]
CUES = {}
for c in J["cues"]:
    CUES.setdefault(c["name"], []).append(c["t"])

_cache = {}


def smp(name, pitch=1.0):
    """Load an effect (mono, 48 kHz), optionally re-pitched (also changes its length)."""
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
    tr = Track(DUR, seed=81)

    def put(name, t, gain=0.3, pitch=1.0, pan=0.0, rev=0.12):
        tr.add(smp(name, pitch), t, gain, pan=pan, rev=rev)

    one = lambda k: CUES[k][0]
    # ------------------------------------------------------------- music
    tr.vinyl(0.008)
    FREEZE, BACK = one("freeze"), CUES["stamp"][-1]
    END = one("end")
    prog = ["Fmaj7", "G6", "Am7", "Cmaj7"]
    # intro: just a soft pad and two curious bell notes
    tr.pad(CHORDS["Fmaj7"], 0.2, 4.5, gain=0.045, cutoff=900)
    tr.bell(84, CUES["pop_soft"][1] + 0.05, 0.05, pan=0.2)
    tr.bell(88, 2.6, 0.04, pan=-0.2)
    # groove A: from the morph to the freeze; groove B: from the last stamp to the end card
    for (g0, g1) in ((4.5, FREEZE), (BACK, END)):
        k = 0
        t0 = g0
        while t0 < g1 - 1e-6:
            ch = prog[k % 4]
            t1 = min(t0 + 2.0, g1)
            tr.pad(CHORDS[ch], t0, t1 - 0.05, gain=0.05, cutoff=1100)
            r = ROOT[ch]
            for off, dur, dm in ((0, 0.4, 0), (0.75, 0.2, 12), (1.0, 0.4, 7), (1.5, 0.3, 12)):
                if t0 + off < g1 - 0.05:
                    tr.bass(r + dm, t0 + off, dur, 0.2)
            tr.arp(ch, t0, t1, step=0.25, gain=0.016)
            t0 += 2.0
            k += 1
        b = g0
        i = 0
        while b < g1 - 1e-6:
            if i % 2 == 0:
                tr.kick(b, 0.5)
            else:
                tr.clap(b, 0.07)
            tr.hat(b + BEAT / 2, 0.035, open_=(i % 4 == 3))
            b += BEAT
            i += 1
    # end card: one chord ringing out with a little bell figure
    tr.pad(CHORDS["Fmaj7"] + [72], END, DUR - 0.2, gain=0.07, cutoff=900)
    tr.bass(ROOT["Fmaj7"], END, 1.8, 0.2)
    tr.impact(END, 0.3)
    for k, m in enumerate((77, 81, 84, 88)):
        tr.bell(m, END + k * 0.16, 0.06, pan=-0.3 + 0.2 * k)

    # ------------------------------------------------------------- effects
    put("rustle", CUES["sack_rustle"][0], 0.2, pan=0.3)
    put("rustle2", CUES["sack_rustle"][1], 0.22, pan=0.3)
    put("pop", CUES["pop_soft"][0], 0.3, pitch=1.3, pan=0.3)
    put("bubble", CUES["pop_soft"][1], 0.3, pan=0.3)
    sn = sorted(set(CUES["sniff"]))
    used = []
    for t in sn:                                   # one double-sniff per sniffing moment
        if not used or t - used[-1] > 0.6:
            used.append(t)
            put("psn_a", t, 0.3, pan=0.25 if t < 4 else -0.3, rev=0.05)
    put("jump", one("jump"), 0.3, pan=0.1)
    put("thump", one("land"), 0.5, pitch=0.8, pan=-0.3)
    put("drop", one("land"), 0.2, pan=-0.3)
    put("glitch_burst", one("morph"), 0.2, pan=0.3)
    for k, t in enumerate(CUES["resolve"]):
        put("shine", t - 0.12, 0.2, pan=0.3)
        if k == 0:
            put("appear", t - 0.25, 0.14, pan=0.3, rev=0.3)
    for t in CUES["swap"]:
        put("glitch_short", t, 0.14, pan=0.3)
        put("whoosh", t + 0.05, 0.14, pan=0.3)
    for k, t in enumerate(CUES["stamp"]):
        put("stamp", t - 0.03, 0.42, pan=-0.25, rev=0.1)
        put("sparkle", t + 0.04, 0.12, pan=-0.1, rev=0.3)
    put("gem", CUES["stamp"][-1] + 0.08, 0.14, rev=0.4)
    put("yap", CUES["stamp"][2] + 0.22, 0.2, pan=-0.3, rev=0.15)        # "muy approved"
    for k, t in enumerate(CUES["hop"]):
        put("jump", t, 0.18, pitch=1.25 + 0.1 * k, pan=-0.3)
        put("thump", t + 0.3, 0.3, pan=-0.3)
    put("dogpant_1", CUES["hop"][1] + 0.34, 0.16, pan=-0.3, rev=0.05)
    # the freeze: the music stops with a record scratch; small sounds only until the last stamp
    put("scratch", FREEZE - 0.08, 0.28)
    put("shutter", one("tick"), 0.2, pan=0.35)
    put("bubble", one("plate"), 0.25, pitch=0.85, pan=-0.3)
    put("boop", CUES["huh"][0], 0.2, pitch=0.9, pan=-0.3)
    put("boop", CUES["huh"][1], 0.2, pitch=1.2, pan=-0.3)
    put("whoosh_fast", one("zoom") - 0.04, 0.22)
    put("slam", one("zoom"), 0.2, rev=0.2)
    put("whoosh", one("zoom_out"), 0.16)
    put("thump", one("zoom_out") + 0.02, 0.3, pitch=0.9)
    t, gap = one("zoom_out") + 0.3, 0.2                # the tail starts thumping, faster and faster
    while t < CUES["stamp"][-1] - 0.05:
        put("thump", t, 0.2, pitch=1.3, pan=-0.45, rev=0.03)
        gap = max(0.07, gap * 0.86)
        t += gap
    put("whoosh", one("family") - 0.1, 0.14)
    for k, t in enumerate(CUES["pack_pop"]):
        put("pop", t, 0.24, pitch=1.0 + 0.12 * k, pan=-0.45 + 0.3 * k)
    put("twinkle", one("chime"), 0.12, rev=0.3)
    put("yap", 20.02, 0.18, rev=0.15)                  # "I sniffed it first."
    put("dogpant_1", 20.45, 0.12, rev=0.05)
    put("magic", one("end") - 0.1, 0.1, rev=0.4)
    for t in CUES["blip"]:
        put("blip", t, 0.12)
    return tr.write(path, fade=0.6)


if __name__ == "__main__":
    print(build(os.path.join(BUILD, "t1_sniff_test.wav")))
