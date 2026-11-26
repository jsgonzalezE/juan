"""Procedural soundtrack engine (lo-fi / chiptune), 120 BPM, A minor."""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BEAT = 0.5

CHORDS = {
    "Am7": [57, 60, 64, 67],
    "Fmaj7": [53, 57, 60, 64],
    "Cmaj7": [55, 60, 64, 71],
    "G6": [55, 59, 62, 64],
    "Dm9": [50, 57, 60, 64],
    "Em7": [52, 55, 59, 62],
}
ROOT = {"Am7": 33, "Fmaj7": 29, "Cmaj7": 36, "G6": 31, "Dm9": 38, "Em7": 40}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, btype=kind, fs=SR, output="sos"), x)


def env(n, a=0.005, d=0.2, sustain=0.0, r=0.05):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), sustain + (1 - sustain) * np.exp(-(t - a) / max(d, 1e-4)))
    if r and n:
        rn = min(n, int(r * SR))
        e[-rn:] *= np.linspace(1, 0, rn)
    return e


class Track:
    def __init__(self, duration, seed=42):
        self.dur = duration
        self.N = int(duration * SR)
        self.L = np.zeros(self.N)
        self.R = np.zeros(self.N)
        self.send = np.zeros(self.N)
        self.rng = np.random.default_rng(seed)

    def add(self, sig, t0, gain=1.0, pan=0.0, rev=0.0):
        i0 = int(t0 * SR)
        if i0 >= self.N or i0 < 0:
            return
        sig = sig[: self.N - i0]
        n = len(sig)
        self.L[i0:i0 + n] += sig * gain * np.sqrt(0.5 * (1 - pan))
        self.R[i0:i0 + n] += sig * gain * np.sqrt(0.5 * (1 + pan))
        if rev:
            self.send[i0:i0 + n] += sig * gain * rev

    # -------------------------------------------------------------- voices
    def pad(self, notes, t0, t1, gain=0.08, cutoff=900):
        n = int((t1 - t0 + 0.6) * SR)
        t = np.arange(n) / SR
        sig = np.zeros(n)
        for m in notes:
            for d in (-7, 0, 7):
                sig += (2 * ((t * hz(m) * 2 ** (d / 1200)) % 1.0) - 1) * (0.6 if d else 0.8)
        sig = filt(sig, "lowpass", cutoff)
        e = env(n, a=0.35, d=99, sustain=1.0, r=0.6)
        self.add(sig * e, t0, gain, pan=-0.15, rev=0.5)
        self.add(filt(sig, "highpass", 300) * e, t0 + 0.012, gain * 0.5, pan=0.6)

    def bass(self, m, t0, dur, gain=0.32):
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = hz(m)
        sig = np.tanh((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * 1.6)
        self.add(sig * env(n, a=0.006, d=0.35, sustain=0.25, r=0.04), t0, gain)

    def kick(self, t0, gain=0.9):
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        ph = 2 * np.pi * np.cumsum(45 + 110 * np.exp(-t / 0.035)) / SR
        sig = np.sin(ph) * np.exp(-t / 0.16)
        k = int(0.001 * SR)
        sig[:k] += np.linspace(0.15, 0, k)
        self.add(np.tanh(sig * 1.4), t0, gain)

    def snare(self, t0, gain=0.28):
        n = int(0.25 * SR)
        t = np.arange(n) / SR
        noise = filt(self.rng.standard_normal(n), "bandpass", [1200, 6000]) * np.exp(-t / 0.07)
        sig = noise * 0.9 + np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.04) * 0.6
        self.add(np.round(sig * 64) / 64, t0, gain, pan=0.05, rev=0.35)

    def clap(self, t0, gain=0.25):
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        e = np.zeros(n)
        for k in (0, 0.011, 0.022):
            e += np.where(t >= k, np.exp(-(t - k) / (0.012 if k < 0.02 else 0.08)), 0)
        sig = filt(self.rng.standard_normal(n), "bandpass", [900, 5000]) * e
        self.add(sig, t0, gain, pan=-0.05, rev=0.4)

    def hat(self, t0, gain=0.08, open_=False):
        n = int((0.18 if open_ else 0.05) * SR)
        t = np.arange(n) / SR
        sig = filt(self.rng.standard_normal(n), "highpass", 7000) * np.exp(
            -t / (0.06 if open_ else 0.015))
        self.add(sig, t0, gain, pan=0.35)

    def chip(self, m, t0, dur=0.16, gain=0.06, duty=0.25, pan=0.0):
        n = int(dur * SR)
        t = np.arange(n) / SR
        sig = filt(np.where((t * hz(m)) % 1.0 < duty, 1.0, -1.0), "lowpass", 5000)
        self.add(sig * env(n, a=0.002, d=dur * 0.45, r=0.02), t0, gain, pan=pan, rev=0.25)

    def bell(self, m, t0, gain=0.1, pan=0.0, decay=0.55):
        n = int(1.8 * SR)
        t = np.arange(n) / SR
        f = hz(m)
        sig = (np.sin(2 * np.pi * f * t)
               + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.2)
               + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.08))
        self.add(sig * np.exp(-t / decay), t0, gain, pan=pan, rev=0.6)

    def blip(self, t0, gain=0.035, pan=None):
        m = self.rng.choice([81, 84, 86, 88, 91, 93])
        self.chip(m, t0, 0.045, gain, duty=0.5,
                  pan=self.rng.uniform(-0.5, 0.5) if pan is None else pan)

    def tick(self, t0, gain=0.05):
        n = int(0.012 * SR)
        sig = filt(self.rng.standard_normal(n), "highpass", 3000) * np.linspace(1, 0, n)
        self.add(sig, t0, gain, pan=self.rng.uniform(-0.4, 0.4))

    def thud(self, t0, gain=0.12, f=None):
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        f = f or 520 + self.rng.uniform(-90, 140)
        sig = np.sin(2 * np.pi * f * t * (1 - 0.35 * t / 0.14)) * np.exp(-t / 0.03)
        self.add(sig, t0, gain, pan=self.rng.uniform(-0.4, 0.4), rev=0.15)

    def whoosh(self, t_end, dur=0.3, gain=0.09):
        n = int(dur * SR)
        sig = self.rng.standard_normal(n)
        out = np.zeros(n)
        for k in range(12):
            a, b = k * n // 12, (k + 1) * n // 12
            fc = 500 * (10 ** (k / 12))
            out[a:b] = filt(sig[a:b], "bandpass", [fc * 0.6, min(fc * 1.6, 20000)])
        self.add(out * np.linspace(0, 1, n) ** 2, t_end - dur, gain, rev=0.2)

    def riser(self, t0, t1, gain=0.1):
        n = int((t1 - t0) * SR)
        sig = self.rng.standard_normal(n)
        out = np.zeros(n)
        for k in range(24):
            a, b = k * n // 24, (k + 1) * n // 24
            fc = 400 * (12 ** (k / 24))
            out[a:b] = filt(sig[a:b], "bandpass", [fc * 0.7, fc * 1.4])
        self.add(out * np.linspace(0, 1, n) ** 2, t0, gain, rev=0.3)

    def impact(self, t0, gain=0.5):
        self.kick(t0, gain * 1.2)
        n = int(1.2 * SR)
        t = np.arange(n) / SR
        sig = filt(self.rng.standard_normal(n), "lowpass", 2500) * np.exp(-t / 0.35)
        self.add(sig, t0, gain * 0.25, rev=0.6)

    def vinyl(self, gain=0.016):
        sig = filt(self.rng.standard_normal(self.N), "bandpass", [300, 5000]) * 0.25
        pops = (self.rng.random(self.N) > 0.99965).astype(float) * self.rng.uniform(-1, 1, self.N)
        sig += filt(pops, "highpass", 1500) * 4
        self.add(sig, 0.0, gain)

    def arp(self, chord, t0, t1, step=0.25, gain=0.04, octave=12, kind="chip"):
        notes = CHORDS[chord]
        seq = [notes[0], notes[1], notes[2], notes[3], notes[2], notes[1], notes[3], notes[2] + 12]
        k, tt = 0, t0
        while tt < t1 - 1e-6:
            m = seq[k % len(seq)] + octave
            if kind == "chip":
                self.chip(m, tt, step * 0.72, gain, pan=0.3 if k % 2 else -0.3)
            else:
                self.bell(m + 12, tt, gain, pan=0.3 if k % 2 else -0.3, decay=0.35)
            tt += step
            k += 1

    # -------------------------------------------------------------- output
    def write(self, path, fade=0.5):
        ir_n = int(1.4 * SR)
        ir = self.rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / 0.35)
        ir = filt(ir, "lowpass", 4000)
        ir /= np.abs(ir).sum() ** 0.5 * 6
        wet = fftconvolve(self.send, ir)[:self.N]
        L = self.L + wet
        R = self.R + np.roll(wet, int(0.011 * SR))
        mix = np.stack([L, R], 1)
        mix = filt(mix.T, "highpass", 28).T
        mix = np.tanh(mix * 1.3) / np.tanh(1.3)
        fn = int(fade * SR)
        mix[-fn:] *= np.linspace(1, 0, fn)[:, None]
        mix /= np.abs(mix).max() / 0.89
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((mix * 32767).astype("<i2").tobytes())
        return path
