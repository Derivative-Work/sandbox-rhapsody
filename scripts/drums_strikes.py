"""Drum events: strikes from the Drums stem, pieces from the LarsNet-separated kit (supersedes drums_larsnet.py).

1. Strikes = onsets of the original Drums stem (onset strength normalised by its local +-2 s maximum, so soft fills
   register), merged within MERGE (a kick's body swells ~50 ms after its attack and reads as a second onset).
   A strike must also reach FLOOR dB of the drum stem's loud level (99th-percentile RMS): local normalisation lifts
   the stem's leakage in drumless passages (piano, voice) into onsets -- 63 "strikes" in the intro and outro, all
   at or below -44.6 dB, against a median of -2.2 dB for strikes in the band sections.
   A hit exists exactly where the drum stem has one: hits found in the separated stems alone included bleed
   (human, C3: "inventing drum hits that don't exist"), and global loudness thresholds tuned on Suno's backbeats
   threw away soft fills and off-beat kicks (human, C3: bars 59-60, "missing eighth note kicks and snare fill
   into 61").
2. Pieces per strike, from the separated stems (audio/derived/drums_larsnet/, see drums_larsnet.py), each measured
   in its own band: rise = peak within RISE_WIN after the strike over the minimum in the 30 ms before. The piece with
   the largest rise is always credited; another piece is credited too when its rise is at least SHARE of the largest
   and it is within LEVEL dB of its stem's loud level (bleed rises less than the struck piece, and is quiet).
   Hats and cymbals, additionally: credited on their own in-band evidence (rise >= CYM_RISE dB, level >= CYM_LEVEL
   dB of their stem's loud level), whatever else is struck: they sit in their own high band, where kick and snare
   barely leak, and they're rarely the largest rise at a strike (bar 44's eighth-note hats came out as one hit).
   Kick, additionally: credited where the original drum stem's 30-70 Hz band rises >= SUB_RISE dB to within
   SUB_LEVEL dB of the median on-beat kick. Soft kicks layered under snare and tom on the off-beats (human, C3:
   "eighth note kicks" in bars 59-60) show there as 7-17 dB sub-bass attacks while LarsNet files their energy
   under toms.
3. Times: the strike's onset, moved to the physical attack in the drum stem.

Usage: .venv/bin/python -I scripts/drums_strikes.py  ->  timing/events/drums__kit.json, timing/drums_strikes.md
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import scipy.signal as sg
from scipy.ndimage import maximum_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attack_times  # noqa: E402

SR, HOP = 44100, 128
MERGE, SHARE, LEVEL, FLOOR = 0.06, 0.6, -24.0, -40.0
SUB_RISE, SUB_LEVEL = 6.0, 12.0
CYM_RISE, CYM_LEVEL = 8.0, -20.0
STEM = "audio/stems/It Was Just a Benchmark (Drums).wav"
PIECES = {  # separated stem -> (piece, GM pitch, band Hz, rise window s)
    "kick": ("kick", 36, (30, 120), 0.06),
    "snare": ("snare", 38, (150, 4000), 0.04),
    "toms": ("toms", 45, (70, 400), 0.05),
    "hihat": ("hats", 42, (6000, 16000), 0.03),
    "cymbals": ("crash", 49, (4000, 14000), 0.04),
}


def main():
    TM = json.loads(Path("timing/timing_map.json").read_text())
    beats = np.array(TM["beats"])
    y, _ = librosa.load(STEM, sr=SR, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
    env = env / (maximum_filter1d(env, size=int(4.0 * SR / HOP)) + 1e-6)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="time", delta=0.05,
                                    normalize=False)
    mdb = 20 * np.log10(librosa.feature.rms(y=y, frame_length=512, hop_length=HOP)[0] + 1e-9)
    mloud = float(np.percentile(mdb, 99))
    strikes = []
    for t in on:
        f = int(t * SR / HOP)
        if mdb[f:f + int(0.04 * SR / HOP) + 1].max() < mloud + FLOOR:
            continue
        if not strikes or t - strikes[-1] >= MERGE:
            strikes.append(float(t))
    att = attack_times.attack_offsets(STEM, np.array(strikes), before=0.03, after=0.02, quiet=0.6)
    times = [t + a if not np.isnan(a) else t for t, a in zip(strikes, att)]
    lv = {}
    for stem, (piece, gm, band, win) in PIECES.items():
        ys, _ = librosa.load(f"audio/derived/drums_larsnet/{stem}.wav", sr=SR, mono=True)
        yb = sg.sosfiltfilt(sg.butter(4, band, btype="band", fs=SR, output="sos"), ys)
        db = 20 * np.log10(librosa.feature.rms(y=yb, frame_length=512, hop_length=HOP)[0] + 1e-9)
        lv[stem] = (db, float(np.percentile(db, 99)), win)
    suno = json.loads(Path("timing/events/drums__drums.json").read_text())["events"]
    ysub = sg.sosfiltfilt(sg.butter(4, (30, 70), btype="band", fs=SR, output="sos"), y)
    sub = 20 * np.log10(librosa.feature.rms(y=ysub, frame_length=512, hop_length=HOP)[0] + 1e-9)

    def sub_at(t):
        f = int(t * SR / HOP)
        pk = sub[f:f + int(0.06 * SR / HOP) + 1].max()
        return pk - sub[max(0, f - int(0.03 * SR / HOP)):f + 1].min(), pk

    kick_db = lv["kick"]
    on_beat_kicks = [sub_at(t)[1] for t in strikes
                     if kick_db[0][int(t * SR / HOP):int(t * SR / HOP) + int(0.06 * SR / HOP) + 1].max()
                     - kick_db[0][max(0, int(t * SR / HOP) - int(0.03 * SR / HOP)):int(t * SR / HOP) + 1].min() > 20]
    kick_ref = float(np.median(on_beat_kicks))
    events, counts = [], {v[0]: 0 for v in PIECES.values()}
    for t0, t in zip(strikes, times):
        f = int(t0 * SR / HOP)
        rise, level = {}, {}
        for stem, (db, loud, win) in lv.items():
            pk = db[f:f + int(win * SR / HOP) + 1].max()
            pre = db[max(0, f - int(0.03 * SR / HOP)):f + 1].min()
            rise[stem], level[stem] = pk - pre, pk - loud
        top = max(rise, key=rise.get)
        sr_, sl_ = sub_at(t0)
        sub_kick = sr_ >= SUB_RISE and sl_ >= kick_ref - SUB_LEVEL
        for stem, (piece, gm, _, _) in PIECES.items():
            cym = stem in ("hihat", "cymbals") and rise[stem] >= CYM_RISE and level[stem] >= CYM_LEVEL
            if stem == top or (rise[stem] >= SHARE * rise[top] and level[stem] >= LEVEL) or (stem == "kick" and sub_kick) or cym:
                in_suno = any(abs(e["t"] - t) < 0.04 for e in suno)
                events.append({"t": round(t, 4), "end": round(t + 0.1, 4), "pitch": gm, "piece": piece,
                               "vel": int(np.clip(127 + 3 * level[stem], 30, 127)), "source": "strike+larsnet",
                               "rise_db": round(float(rise[stem]), 1), "in_suno": bool(in_suno)})
                counts[piece] += 1

    def pos(x):
        i = np.searchsorted(beats, x) - 1
        return None if i < 0 or i >= len(beats) - 1 else round((x - beats[i]) / (beats[i + 1] - beats[i]) * 4) % 4

    by = [sum(1 for x in times if pos(x) == q) for q in range(4)]
    print(f"strikes {len(strikes)} (from {len(on)} onsets); by position (beat, e, and, a) {by}; pieces {counts}")
    Path("timing/events/drums__kit.json").write_text(json.dumps(
        {"stem": "Drums", "track": "strikes from the drum stem, pieces from LarsNet", "method": "scripts/drums_strikes.py",
         "shift_ms": 0.0, "events": events}) + "\n")
    Path("timing/drums_strikes.md").write_text(
        "# Drum strikes\n\n`scripts/drums_strikes.py`: strikes from the Drums stem's onsets, pieces from the LarsNet "
        f"stems.\n\n- Strikes: {len(strikes)} (beat {by[0]}, e {by[1]}, and {by[2]}, a {by[3]})\n"
        + "".join(f"- {p}: {n}\n" for p, n in counts.items()))


if __name__ == "__main__":
    main()
