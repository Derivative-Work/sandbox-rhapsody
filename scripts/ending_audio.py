"""The ending Suno didn't make (human-approved plan, 2026-10-22): the piano's release and the SIGTERM.

Suno ends on a B-flat major chord struck at 321.61 s and cuts the audio at 323.0 s, mid-ring at -32 dBFS.
1. Release: the chord's last steady 0.25 s (FREEZE_A..FREEZE_B) is resynthesised as its spectral peaks (a sum of
   sinusoids) and decays like a piano string: DECAY_DB per second, plus HF_DB per second
   per kHz (high partials die first). It crossfades in over XFADE before the cut (equal power), so there is no seam.
2. SIGTERM at SIGTERM_S, while the chord still rings: a click, then a falling whine (2.2 kHz -> 80 Hz,
   exponential, 0.4 s) with a low thump, at a quiet level. The chord is cut with it (12 ms fade): the agent is
   killed mid-note. Silence follows (the fact card).
Agent-made sound design; logged. The master before 322.6 s is untouched, sample for sample.

Usage: .venv/bin/python -I scripts/ending_audio.py  ->  audio/post/sandbox_rhapsody_final.wav, timing/ending.json
"""
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SRC = "audio/master/sandbox_rhapsody_master_nofallback.wav"
OUT = Path("audio/post/sandbox_rhapsody_final.wav")
FREEZE_A, FREEZE_B = 322.55, 322.80
XFADE = (322.60, 322.85)
DECAY_DB, HF_DB = 6.0, 1.5
SIGTERM_S, SILENCE_AFTER = 325.5, 1.5
NFFT, HOP = 4096, 512


def freeze_tail(ch, sr, start, dur, max_partials=80):
    """The chord as a sum of sinusoids: spectral peaks of the frozen window (parabolic-interpolated frequency and
    amplitude) resynthesised with piano-like decay. (A phase-vocoder freeze, tried first, made partials that straddle
    bins beat, so the tail's level wobbled 4-7 dB.) Phases are seeded (config/seeds.json main = 41); the equal-power
    crossfade hides the phase change."""
    from scipy.signal import find_peaks
    a, b = int(FREEZE_A * sr), int(FREEZE_B * sr)
    seg = ch[a:b] * np.hanning(b - a)
    n = 1 << 16
    spec = np.abs(np.fft.rfft(seg, n=n))
    db = 20 * np.log10(spec + 1e-12)
    pk, _ = find_peaks(db, height=db.max() - 60, distance=8)
    pk = pk[np.argsort(db[pk])[::-1][:max_partials]]
    t = np.arange(int(dur * sr)) / sr
    rng = np.random.default_rng(41)
    out = np.zeros_like(t)
    win_gain = np.hanning(b - a).sum() / 2  # rfft magnitude of a sinusoid of amplitude A through the window
    for k in pk:
        if k <= 0 or k >= len(db) - 1:
            continue
        al, am, ar = db[k - 1], db[k], db[k + 1]
        d = 0.5 * (al - ar) / (al - 2 * am + ar)
        f = (k + d) * sr / n
        amp = 10 ** ((am - 0.25 * (al - ar) * d) / 20) / win_gain
        rate = DECAY_DB + HF_DB * f / 1000
        out += amp * np.exp(-rate * np.log(10) / 20 * t) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return out


def sigterm(sr, level_db=-24.0):
    n = int(0.45 * sr)
    t = np.arange(n) / sr
    f = 2200 * (80 / 2200) ** (t / 0.4)
    whine = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.25)
    click = np.zeros(n)
    click[:int(0.004 * sr)] = np.random.default_rng(41).standard_normal(int(0.004 * sr)) * np.hanning(int(0.004 * sr))
    thump = np.sin(2 * np.pi * 55 * t) * np.exp(-t / 0.08)
    x = 0.6 * whine + 0.8 * click + 0.5 * thump
    return x / np.abs(x).max() * 10 ** (level_db / 20)


def main():
    y, sr = sf.read(SRC, always_2d=True)
    total = int((SIGTERM_S + 0.45 + SILENCE_AFTER) * sr)
    out = np.zeros((total, y.shape[1]))
    x0, x1 = int(XFADE[0] * sr), int(XFADE[1] * sr)
    out[:x1] = y[:x1]
    tail_len = (SIGTERM_S + 0.012) - XFADE[0]
    g = np.linspace(0, 1, x1 - x0)
    for c in range(y.shape[1]):
        tail = freeze_tail(y[:, c], sr, XFADE[0], tail_len + 0.1)
        # Level-match the tail's start to the master over the 0.15 s before the crossfade.
        ref = np.sqrt((y[int((XFADE[0] - 0.15) * sr):x0, c] ** 2).mean())
        cur = np.sqrt((tail[:int(0.15 * sr)] ** 2).mean()) + 1e-12
        tail *= ref / cur
        seg = np.zeros(total - x0)
        n = min(len(tail), len(seg))
        seg[:n] = tail[:n]
        out[x0:x1, c] = y[x0:x1, c] * np.cos(g * np.pi / 2) + seg[:x1 - x0] * np.sin(g * np.pi / 2)
        out[x1:, c] = seg[x1 - x0:]
    # Kill the chord at SIGTERM (12 ms fade), then the SIGTERM sound.
    s0 = int(SIGTERM_S * sr)
    fade = int(0.012 * sr)
    out[s0:s0 + fade] *= np.linspace(1, 0, fade)[:, None]
    out[s0 + fade:] = 0
    st = sigterm(sr)
    out[s0:s0 + len(st)] += st[:, None]
    assert np.array_equal(out[:x0], y[:x0]), "the master before the crossfade must be untouched"
    peak = np.abs(out).max()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sf.write(OUT, out, sr, subtype="PCM_24")
    info = {"source": SRC, "output": str(OUT), "sr": sr, "duration_s": round(total / sr, 4),
            "untouched_until_s": XFADE[0], "crossfade_s": XFADE, "freeze_window_s": [FREEZE_A, FREEZE_B],
            "decay_db_per_s": DECAY_DB, "hf_db_per_s_per_khz": HF_DB, "sigterm_s": SIGTERM_S,
            "silence_from_s": round(SIGTERM_S + 0.45, 3), "peak_dbfs": round(20 * np.log10(peak), 2)}
    Path("timing/ending.json").write_text(json.dumps(info, indent=1) + "\n")
    print(info)


if __name__ == "__main__":
    main()
