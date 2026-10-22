"""Check figure for a stretch of bars: the master's spectrogram, beat grid (downbeats thicker), and each track's
events as ticks in its own row. Usage: .venv/bin/python -I scripts/bar_check_plot.py <first bar> <last bar> <out.png>"""
import json
import sys

import librosa
import librosa.display
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TM = json.load(open("timing/timing_map.json"))
bars = {b["n"]: b for b in TM["bars"]}
b0, b1, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
T0, T1 = bars[b0]["start"], bars[b1]["end"]
y, sr = librosa.load("audio/master/sandbox_rhapsody_master_nofallback.wav", sr=44100, offset=T0, duration=T1 - T0)
S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=128)), ref=np.max)
TRACKS = [("vocal words", None), ("piano", "keyboard__piano_model"), ("guitar", "guitar__distortion_guitar"),
          ("bass", "bass__electric_bass_finger"), ("synth", "synth__lead_2_sawtooth"),
          ("strings", "strings__string_ensemble_1"), ("drums", "drums__kit")]
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, gridspec_kw={"height_ratios": [3, 2]},
                              facecolor="#0a0814")
librosa.display.specshow(S, sr=sr, hop_length=128, x_axis="time", y_axis="log", ax=ax, cmap="magma", vmin=-75)
beats = np.array(TM["beats"])
down = set(TM["downbeat_beats"])
for i, b in enumerate(beats):
    if T0 <= b <= T1:
        for a in (ax, ax2):
            a.axvline(b - T0, color="w", lw=1.6 if i in down else 0.5, alpha=0.6)
for k, (name, slug) in enumerate(TRACKS):
    if slug is None:
        ts = [w["start"] for ln in TM["lines"] for w in ln["words"]]
    else:
        ts = [e["t"] for e in json.load(open(f"timing/events/{slug}.json"))["events"]]
    ts = [t - T0 for t in ts if T0 <= t <= T1]
    ax2.plot(ts, [k] * len(ts), "|", ms=16, mew=2, color="#ffa21f")
ax2.set_yticks(range(len(TRACKS)), [n for n, _ in TRACKS], color="w")
ax2.set_facecolor("#0a0814")
ax.set_title(f"Master, bars {b0}-{b1} ({T0:.2f}-{T1:.2f} s): beats (white, downbeats thick); events per track (amber)",
             color="w")
for a in (ax, ax2):
    a.tick_params(colors="w")
plt.tight_layout()
plt.savefig(out, dpi=80, facecolor="#0a0814")
