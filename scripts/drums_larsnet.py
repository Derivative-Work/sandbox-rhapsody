"""Drum events from LarsNet-separated kit stems (replaces Suno's drum MIDI + the NMF additions).

LarsNet (Mezza et al. 2024, "Toward deep drum source separation", Pattern Recognition Letters 183; checkpoints
CC BY-NC 4.0, used here for analysis only) splits the Drums stem into kick, snare, toms, hi-hat and cymbals:
  cd cache/larsnet && ../../.venv/bin/python separate.py -i ../larsnet_in -o ../larsnet_out -w 1.0 -d cuda:0
(Wiener-filtered, alpha 1.0), copied to audio/derived/drums_larsnet/<piece>.wav.

Why: Suno's drum labels were unreliable (human, C3: bar 58's hits on 2 and 4 are toms that Suno called kick + hat;
bar 62 has snares on 1, 2 and 3 that Suno's MIDI lacks), and NMF templates learned from those labels inherited the
errors ("hats" templates with strong lows). Separation gives each piece its own signal, so a hit is found where its
own stem has one.

Per piece: onsets in the separated stem (librosa, 2.9 ms hop); a hit is kept when the stem's level within 40 ms
reaches LEVEL dB of the stem's loud level (99th-percentile RMS) and rises at least RISE dB from the 30 ms before
(bleed and cymbal wash don't). Its time is the physical attack in that stem (scripts/attack_times.py).
Suno's hits are compared, not used.

Usage: .venv/bin/python -I scripts/drums_larsnet.py  ->  timing/events/drums__kit.json, timing/drums_larsnet.md
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attack_times  # noqa: E402

SR, HOP = 44100, 128
PIECES = {  # separated stem -> (piece name in events, GM pitch, LEVEL dB, RISE dB)
    "kick": ("kick", 36, -20, 8),
    "snare": ("snare", 38, -20, 8),
    "toms": ("toms", 45, -20, 8),
    "hihat": ("hats", 42, -26, 3),  # steady eighth-note hats barely decay between strokes (bar 44)
    "cymbals": ("crash", 49, -14, 6),
}


def main():
    TM = json.loads(Path("timing/timing_map.json").read_text())
    beats = np.array(TM["beats"])
    suno = json.loads(Path("timing/events/drums__drums.json").read_text())["events"]
    gm_piece = {36: "kick", 37: "snare", 38: "snare", 40: "snare", 42: "hats", 44: "hats", 46: "hats",
                49: "crash", 51: "crash", 52: "crash", 55: "crash", 57: "crash", 41: "toms", 43: "toms", 45: "toms",
                47: "toms", 48: "toms", 50: "toms"}

    def pos(t):
        i = np.searchsorted(beats, t) - 1
        return None if i < 0 or i >= len(beats) - 1 else round((t - beats[i]) / (beats[i + 1] - beats[i]) * 4) % 4

    events, rows = [], []
    for stem, (piece, gm, level, rise) in PIECES.items():
        path = f"audio/derived/drums_larsnet/{stem}.wav"
        y, _ = librosa.load(path, sr=SR, mono=True)
        db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=512, hop_length=HOP)[0] + 1e-9)
        loud = float(np.percentile(db, 99))
        env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
        on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="time", wait=8, delta=0.03)
        kept = []
        for t in on:
            f = int(t * SR / HOP)
            pk = db[f:f + int(0.04 * SR / HOP) + 1].max()
            pre = db[max(0, f - int(0.03 * SR / HOP)):f + 1].min()
            if pk >= loud + level and pk - pre >= rise:
                kept.append(t)
        att = attack_times.attack_offsets(path, np.array(kept), before=0.04, after=0.03, quiet=0.5)
        times = sorted(float(t + a) if not np.isnan(a) else float(t) for t, a in zip(kept, att))
        merged = []  # one hit per stroke: detections within 40 ms of each other are the same hit
        for t in times:
            if not merged or t - merged[-1] >= 0.04:
                merged.append(t)
        times = merged
        s = np.array(sorted(e["t"] for e in suno if gm_piece.get(e["pitch"]) == piece))
        for t in times:
            f = int(t * SR / HOP)
            lvl = float(db[f:f + int(0.04 * SR / HOP) + 1].max() - loud)
            events.append({"t": round(t, 4), "end": round(t + 0.1, 4), "pitch": gm, "piece": piece,
                           "vel": int(np.clip(127 + lvl * 3, 30, 127)), "source": "larsnet",
                           "in_suno": bool(len(s) and np.min(np.abs(s - t)) < 0.04)})
        tt = np.array(times)
        recall = float(np.mean([np.min(np.abs(tt - x)) < 0.04 for x in s])) if len(s) and len(tt) else 0.0
        new = [t for t in times if not len(s) or np.min(np.abs(s - t)) >= 0.04]
        by = [sum(1 for t in new if pos(t) == q) for q in range(4)]
        rows.append((piece, len(times), len(s), recall, len(new), by))
        print(f"{piece:6s} hits {len(times):4d}; Suno {len(s):4d}, of which found {recall:.0%}; "
              f"not in Suno {len(new)} (beat, e, and, a) {by}")
    events.sort(key=lambda e: (e["t"], e["pitch"]))
    Path("timing/events/drums__kit.json").write_text(json.dumps(
        {"stem": "Drums", "track": "kit from LarsNet-separated pieces", "method": "scripts/drums_larsnet.py",
         "shift_ms": 0.0, "events": events}) + "\n")
    L = ["# Drum events from LarsNet-separated pieces", "", "`scripts/drums_larsnet.py`. Suno's hits are compared, "
         "not used.", "", "| Piece | Hits | Suno hits | Suno hits found | Hits not in Suno | on beat | e | and | a |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for p, n, ns, rec, nn, by in rows:
        L.append(f"| {p} | {n} | {ns} | {rec:.0%} | {nn} | {by[0]} | {by[1]} | {by[2]} | {by[3]} |")
    Path("timing/drums_larsnet.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
