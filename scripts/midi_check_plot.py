"""C2 figure: for four parts over the same 4 s of the hard rock, the stem's onset-strength envelope with the raw
MIDI onsets (grey) and the exported, shifted events (amber). Usage: .venv/bin/python -I scripts/midi_check_plot.py"""
import json
import sys
from pathlib import Path

import librosa
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import midi_io  # noqa: E402

SR, HOP, T0, T1 = 22050, 128, 214.0, 218.0
PARTS = [("Drums", "drums", "drums__drums"), ("Bass", "Electric Bass (finger)", "bass__electric_bass_finger"),
         ("Guitar", "Distortion Guitar", "guitar__distortion_guitar"), ("Brass", "Brass Section", "brass__brass_section")]
fig, axes = plt.subplots(len(PARTS), 1, figsize=(12, 7.5), sharex=True, facecolor="#0a0814")
for ax, (stem, track, slug) in zip(axes, PARTS):
    y, _ = librosa.load(f"audio/stems/It Was Just a Benchmark ({stem}).wav", sr=SR, offset=T0 - 0.5, duration=T1 - T0 + 1)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
    t = T0 - 0.5 + np.arange(len(env)) * HOP / SR
    ax.set_facecolor("#0a0814")
    ax.fill_between(t, env / env.max(), color="#7a63d6", alpha=0.6, lw=0)
    pm = midi_io.load(f"audio/stems/midi/It Was Just a Benchmark ({stem}).mid")
    raw = [n.start for i in pm.instruments if (i.name if not i.is_drum else "drums") == track for n in i.notes]
    ev = json.loads(Path(f"timing/events/{slug}.json").read_text())
    for x in raw:
        if T0 - 0.5 <= x <= T1 + 0.5:
            ax.axvline(x, ymin=0.55, ymax=1.0, color="#9a8fb0", lw=0.8)
    for e in ev["events"]:
        if T0 - 0.5 <= e["t"] <= T1 + 0.5:
            ax.axvline(e["t"], ymin=0.0, ymax=0.5, color="#ffa21f", lw=1.0)
    ax.set_ylabel(f"{stem}\n{ev['shift_ms']:+.0f} ms", color="#efe8da", rotation=0, ha="right", va="center", fontsize=9)
    ax.set_yticks([])
    ax.tick_params(colors="#efe8da")
    for s in ax.spines.values():
        s.set_visible(False)
axes[0].set_title("Stem onset strength (violet); MIDI as transcribed (grey, top); exported events after shift (amber, bottom)",
                  color="#efe8da", fontsize=10)
axes[-1].set_xlabel("song time (s)", color="#efe8da")
plt.tight_layout()
plt.savefig("timing/midi_check.png", dpi=110, facecolor="#0a0814")
