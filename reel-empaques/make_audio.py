"""Procedural lo-fi / chiptune soundtrack synced to the reel timeline (120 BPM, A minor)."""
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from make_reel import DURATION, BUILD

SR = 48000
N = int(DURATION * SR)
BEAT = 0.5
rng = np.random.default_rng(42)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def filt(x, kind, f, order=2):
    sos = butter(order, f, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def env(n, a=0.005, d=0.2, sustain=0.0, r=0.05, hold=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    dec = sustain + (1 - sustain) * np.exp(-(t - a).clip(0) / max(d, 1e-4))
    e = np.where(t < a, e, dec)
    if r and n > 0:
        rn = min(n, int(r * SR))
        e[-rn:] *= np.linspace(1, 0, rn)
    return e


L = np.zeros(N)
Rr = np.zeros(N)
send = np.zeros(N)  # reverb bus (mono)


def add(sig, t0, gain=1.0, pan=0.0, rev=0.0):
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    sig = sig[: N - i0]
    gl = gain * np.sqrt(0.5 * (1 - pan))
    gr = gain * np.sqrt(0.5 * (1 + pan))
    L[i0:i0 + len(sig)] += sig * gl
    Rr[i0:i0 + len(sig)] += sig * gr
    if rev:
        send[i0:i0 + len(sig)] += sig * gain * rev


# ---------------------------------------------------------------- instruments

def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    ph = (t * f * 2 ** (detune / 1200)) % 1.0
    return 2 * ph - 1


def pulse(f, n, duty=0.25):
    t = np.arange(n) / SR
    return np.where((t * f) % 1.0 < duty, 1.0, -1.0)


def pad(notes, t0, t1, gain=0.08):
    n = int((t1 - t0 + 0.6) * SR)
    sig = np.zeros(n)
    for m in notes:
        for d in (-7, 0, 7):
            sig += saw(hz(m), n, d) * (0.6 if d else 0.8)
    sig = filt(sig, "lowpass", 900)
    e = env(n, a=0.35, d=99, sustain=1.0, r=0.6)
    add(sig * e, t0, gain, pan=-0.15, rev=0.5)
    add(filt(sig, "highpass", 300) * e, t0 + 0.012, gain * 0.5, pan=0.6)


def bass(m, t0, dur, gain=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    sig = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    sig = np.tanh(sig * 1.6)
    add(sig * env(n, a=0.006, d=0.35, sustain=0.25, r=0.04), t0, gain)


def kick(t0, gain=0.9):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sig = np.sin(ph) * np.exp(-t / 0.16)
    sig[: int(0.001 * SR)] += np.linspace(0.15, 0, int(0.001 * SR))
    add(np.tanh(sig * 1.4), t0, gain)


def snare(t0, gain=0.28):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = filt(rng.standard_normal(n), "bandpass", [1200, 6000]) * np.exp(-t / 0.07)
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.04)
    sig = noise * 0.9 + body * 0.6
    sig = np.round(sig * 64) / 64  # a little bit-crush grit
    add(sig, t0, gain, pan=0.05, rev=0.35)


def hat(t0, gain=0.08, open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    sig = filt(rng.standard_normal(n), "highpass", 7000) * np.exp(-t / (0.06 if open_ else 0.015))
    add(sig, t0, gain, pan=0.35)


def chip(m, t0, dur=0.16, gain=0.06, duty=0.25, pan=0.0):
    n = int(dur * SR)
    sig = pulse(hz(m), n, duty)
    sig = filt(sig, "lowpass", 5000)
    add(sig * env(n, a=0.002, d=dur * 0.45, r=0.02), t0, gain, pan=pan, rev=0.25)


def blip(t0, gain=0.05, pan=0.0):
    m = rng.choice([81, 84, 86, 88, 91, 93])
    chip(m, t0, 0.045, gain, duty=0.5, pan=pan)


def ticks(t0, count=7, span=0.22, gain=0.05):
    for k in range(count):
        n = int(0.012 * SR)
        sig = filt(rng.standard_normal(n), "highpass", 3000) * np.linspace(1, 0, n)
        add(sig, t0 + k * span / count, gain, pan=rng.uniform(-0.4, 0.4))


def static_noise(t0, t1, gain=0.12, sweep=False):
    n = int((t1 - t0) * SR)
    sig = rng.standard_normal(n)
    sig = filt(sig, "bandpass", [600, 9000])
    # AM crackle like a de-tuned TV
    am = (rng.random(n // 400 + 1) > 0.5).astype(float) * 0.5 + 0.5
    sig *= np.repeat(am, 400)[:n]
    if sweep:
        sig *= np.linspace(0.3, 1.0, n) ** 2
    e = np.ones(n)
    fade = min(n // 4, int(0.02 * SR))
    if fade:
        e[:fade] = np.linspace(0, 1, fade)
        e[-fade:] = np.linspace(1, 0, fade)
    add(sig * e, t0, gain)


def riser(t0, t1, gain=0.12):
    n = int((t1 - t0) * SR)
    sig = rng.standard_normal(n)
    out = np.zeros(n)
    chunks = 24
    for k in range(chunks):
        a, b = k * n // chunks, (k + 1) * n // chunks
        fc = 400 * (12 ** (k / chunks))
        out[a:b] = filt(sig[a:b], "bandpass", [fc * 0.7, fc * 1.4])
    out *= np.linspace(0, 1, n) ** 2
    add(out, t0, gain, rev=0.3)


def impact(t0, gain=0.5):
    kick(t0, gain * 1.2)
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    sig = filt(rng.standard_normal(n), "lowpass", 2500) * np.exp(-t / 0.35)
    add(sig, t0, gain * 0.25, rev=0.6)


def vinyl(gain=0.018):
    sig = filt(rng.standard_normal(N), "bandpass", [300, 5000]) * 0.25
    pops = (rng.random(N) > 0.99965).astype(float) * rng.uniform(-1, 1, N)
    sig += filt(pops, "highpass", 1500) * 4
    add(sig, 0.0, gain)


# ---------------------------------------------------------------- arrangement

CHORDS = {  # midi notes (A minor: Am7 – Fmaj7 – Cmaj7 – G6)
    "Am7": [57, 60, 64, 67],
    "Fmaj7": [53, 57, 60, 64],
    "Cmaj7": [55, 60, 64, 71],
    "G6": [55, 59, 62, 64],
}
ROOT = {"Am7": 33, "Fmaj7": 29, "Cmaj7": 36, "G6": 31}
PROG = ["Am7", "Fmaj7", "Cmaj7", "G6"]

vinyl()
# intro: TV static rising into the first downbeat
static_noise(0.0, 0.98, 0.11, sweep=True)
riser(0.2, 1.0, 0.10)

bars = []
t = 1.0
k = 0
while t < 21.5:
    bars.append((t, PROG[k % 4]))
    t += 2.0
    k += 1

for (t0, ch) in bars:
    t1 = min(t0 + 2.0, 21.5)
    pad(CHORDS[ch], t0, t1)

# final chord rings out
pad(CHORDS["Am7"] + [71], 21.5, DURATION - 0.1, gain=0.09)
bass(ROOT["Am7"], 21.5, 1.6, 0.3)


def drums_on(t):
    if 4.0 <= t < 5.5:      # coordinates breakdown
        return False
    if t >= 19.5:           # outro
        return False
    return t >= 1.0


beat_t = 1.0
i = 0
while beat_t < 21.5:
    if drums_on(beat_t):
        if i % 2 == 0:
            kick(beat_t)
        else:
            snare(beat_t)
        hat(beat_t + BEAT / 2 + 0.012, open_=(i % 4 == 3))
        hat(beat_t, 0.04)
    beat_t += BEAT
    i += 1
# extra kick pickups
for t0 in (8.75, 12.75, 16.75):
    kick(t0, 0.6)

# bass line
for (t0, ch) in bars:
    r = ROOT[ch]
    if t0 >= 19.5:
        bass(r, t0, 1.9, 0.26)
        continue
    for off, dur, dm in ((0, 0.45, 0), (0.75, 0.2, 12), (1.0, 0.45, 0), (1.5, 0.4, 7)):
        tt = t0 + off
        if 4.0 <= tt < 5.5:
            continue
        bass(r + dm, tt, dur)

# chiptune arpeggio from the varieties onward
for (t0, ch) in bars:
    if t0 < 9.0:
        continue
    notes = CHORDS[ch]
    seq = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[3] + 12,
           notes[2] + 12, notes[1] + 12, notes[3] + 12, notes[2] + 24]
    for s in range(8):
        tt = t0 + s * 0.25
        if tt >= 21.5:
            break
        chip(seq[s], tt, 0.18, 0.045 if t0 < 19.5 else 0.035, pan=0.3 if s % 2 else -0.3)

# accents on cuts
impact(1.0)
impact(9.0, 0.45)
impact(13.5, 0.4)
static_noise(8.85, 9.0, 0.10)
static_noise(15.38, 15.58, 0.10)
static_noise(17.38, 17.5, 0.08)
static_noise(18.41, 18.59, 0.08)
static_noise(19.43, 19.62, 0.14)
riser(12.5, 13.5, 0.06)

# coordinates: data ticks + tone per item
for j, t0 in enumerate((4.0, 4.5, 5.0)):
    ticks(t0, 8, 0.22, 0.06)
    chip([69, 72, 76][j] + 12, t0 + 0.22, 0.25, 0.07, duty=0.125)

# variety names: pitched pings
for j, t0 in enumerate((9.5, 10.5, 11.5, 12.5)):
    chip([81, 84, 88, 86][j], t0, 0.3, 0.08, duty=0.125, pan=[-0.4, 0.4, -0.4, 0.4][j])
    ticks(t0, 5, 0.18, 0.04)

# text decode blips
for t0 in (2.0, 2.2, 2.6, 5.7, 6.1, 6.6, 6.9, 7.4, 7.6, 9.3, 9.45, 13.0, 13.55, 13.8, 14.5,
           17.65, 17.75, 18.65, 18.75, 19.8, 20.6, 20.9, 21.3, 21.5):
    blip(t0, 0.035, pan=rng.uniform(-0.5, 0.5))

# ---------------------------------------------------------------- mix
ir_n = int(1.4 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / 0.35)
ir = filt(ir, "lowpass", 4000)
ir /= np.abs(ir).sum() ** 0.5 * 6
wet = fftconvolve(send, ir)[:N]
L += wet
Rr += np.roll(wet, int(0.011 * SR))

mix = np.stack([L, Rr], 1)
mix = filt(mix.T, "highpass", 28).T
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
fade = int(0.5 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix /= np.abs(mix).max() / 0.89

os.makedirs(BUILD, exist_ok=True)
out = os.path.join(BUILD, "soundtrack.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(out)
