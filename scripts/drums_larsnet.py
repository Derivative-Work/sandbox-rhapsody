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
A hit must also coincide (within MATCH) with an onset in the original, unseparated Drums stem (locally normalised
onset strength): LarsNet's stems carry bleed between pieces, and without this check 204 of 895 strike times (23%)
had no onset in the drum stem at all -- invented hits (human, C3: "this is inventing drum hits that don't exist").
LarsNet decides which pieces play at a strike; the drum stem decides that there is a strike.
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
MATCH = 0.04
BAND = {"kick": (30, 120), "snare": (150, 4000), "toms": (70, 400), "hihat": (6000, 16000), "cymbals": (4000, 14000)}
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

    from scipy.ndimage import maximum_filter1d
    ymix, _ = librosa.load("audio/stems/It Was Just a Benchmark (Drums).wav", sr=SR, mono=True)
    menv = librosa.onset.onset_strength(y=ymix, sr=SR, hop_length=HOP, lag=1, max_size=3)
    menv = menv / (maximum_filter1d(menv, size=int(4.0 * SR / HOP)) + 1e-6)
    mix_on = librosa.onset.onset_detect(onset_envelope=menv, sr=SR, hop_length=HOP, units="time", delta=0.05,
                                        normalize=False)
    events, rows = [], []
    for stem, (piece, gm, level, rise) in PIECES.items():
        path = f"audio/derived/drums_larsnet/{stem}.wav"
        y, _ = librosa.load(path, sr=SR, mono=True)
        # Level and rise are measured in the piece's own band: bleed from another piece rises at that piece's
        # strike too, but in the other piece's spectrum (kick bleed in the hi-hat stem is low-frequency).
        import scipy.signal as sg
        sos = sg.butter(4, BAND[stem], btype="band", fs=SR, output="sos")
        yb = sg.sosfiltfilt(sos, y)
        db = 20 * np.log10(librosa.feature.rms(y=yb, frame_length=512, hop_length=HOP)[0] + 1e-9)
        loud = float(np.percentile(db, 99))
        env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
        on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="time", wait=8, delta=0.03)
        kept, meas = [], {}
        for t in on:
            f = int(t * SR / HOP)
            pk = db[f:f + int(0.04 * SR / HOP) + 1].max()
            pre = db[max(0, f - int(0.03 * SR / HOP)):f + 1].min()
            if pk >= loud + level and pk - pre >= rise:
                kept.append(t)
                meas[t] = (pk - loud, pk - pre)
        att = attack_times.attack_offsets(path, np.array(kept), before=0.04, after=0.03, quiet=0.5)
        timed = sorted((float(t + a) if not np.isnan(a) else float(t), meas[t]) for t, a in zip(kept, att))
        times = [t for t, _ in timed]
        lvl_of = dict(timed)
        merged = []  # one hit per stroke: detections within 40 ms of each other are the same hit
        for t in times:
            if not merged or t - merged[-1] >= 0.04:
                merged.append(t)
        n_before = len(merged)
        times = [t for t in merged if np.min(np.abs(mix_on - t)) < MATCH]  # a real strike in the drum stem
        print(f"{piece:6s} {n_before - len(times)} of {n_before} dropped: no onset in the drum stem")
        s = np.array(sorted(e["t"] for e in suno if gm_piece.get(e["pitch"]) == piece))
        # A hit Suno's MIDI lacks must look like a typical confirmed hit of this piece: level and rise at least the
        # 25th percentile of the hits Suno does have (a missed hit is better than an invented one; human, C3).
        conf = [lvl_of[t] for t in times if len(s) and np.min(np.abs(s - t)) < 0.04]
        if conf:
            lv25, ri25 = np.percentile([c[0] for c in conf], 25), np.percentile([c[1] for c in conf], 25)
            n0 = len(times)
            times = [t for t in times if (len(s) and np.min(np.abs(s - t)) < 0.04)
                     or (lvl_of[t][0] >= lv25 and lvl_of[t][1] >= ri25)]
            print(f"{piece:6s} additions need level >= {lv25:.1f} dB and rise >= {ri25:.1f} dB: {n0 - len(times)} dropped")
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
    # Suno's hits at real strikes where LarsNet found no piece at all are kept, with Suno's label (LarsNet's
    # snare stem misses about half of Suno's snares; dropping them would lose real hits). Where LarsNet found some
    # piece at the strike, its labels stand (bar 58: toms, not Suno's kick + hat). Suno hits with no drum-stem
    # onset are dropped.
    lt = np.array(sorted(e["t"] for e in events))
    kept_suno = 0
    for e in suno:
        pc = gm_piece.get(e["pitch"])
        if pc is None or np.min(np.abs(mix_on - e["t"])) >= MATCH:
            continue
        if len(lt) and np.min(np.abs(lt - e["t"])) < MATCH:
            continue
        events.append({"t": e["t"], "end": e["end"], "pitch": e["pitch"], "piece": pc, "vel": e["vel"],
                       "source": "suno", "in_suno": True})
        kept_suno += 1
    print(f"Suno hits kept at strikes LarsNet left empty: {kept_suno}")
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
