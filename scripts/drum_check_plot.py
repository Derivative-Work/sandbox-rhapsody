"""Check figure for the drum additions: Drums stem spectrogram over a window, beats, Suno's hits (filled) and the
NMF additions (rings) per piece. Usage: .venv/bin/python -I scripts/drum_check_plot.py <t0> <t1> <out.png>"""
import json
import sys

import librosa
import librosa.display
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

T0, T1, OUT = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
y, sr = librosa.load("audio/stems/It Was Just a Benchmark (Drums).wav", sr=44100, offset=T0, duration=T1 - T0)
S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=128)), ref=np.max)
ev = json.load(open("timing/events/drums__kit.json"))["events"]
beats = np.array(json.load(open("timing/timing_map.json"))["beats"])
fig, ax = plt.subplots(figsize=(14, 6), facecolor="#0a0814")
librosa.display.specshow(S, sr=sr, hop_length=128, x_axis="time", y_axis="log", ax=ax, cmap="magma", vmin=-70)
for b in beats[(beats > T0) & (beats < T1)]:
    ax.axvline(b - T0, color="w", lw=0.6, alpha=0.5)
rows = {"kick": 50, "toms": 110, "snare": 300, "crash": 5000, "hats": 12000}
for e in ev:
    if T0 <= e["t"] <= T1:
        c = "#3fd0ff" if e["source"] == "suno" else "#ffa21f"
        ax.plot(e["t"] - T0, rows[e["piece"]], "o", ms=6 if e["source"] == "suno" else 9,
                mfc=c if e["source"] == "suno" else "none", mec=c, mew=2)
for k, v in rows.items():
    ax.text(-0.02 * (T1 - T0), v, k, color="w", ha="right", va="center", fontsize=9)
ax.set_title(f"Drums stem {T0:.0f}-{T1:.0f} s; beats (white); Suno hits (filled cyan); NMF additions (amber rings)",
             color="w")
ax.tick_params(colors="w")
plt.tight_layout()
plt.savefig(OUT, dpi=90, facecolor="#0a0814")
