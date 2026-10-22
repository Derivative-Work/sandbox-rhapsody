"""Turn the Basic Pitch transcriptions (scripts/transcribe_stems.py) into animation events, and record which source
drives each instrument in config/event_sources.json.

Per stem:
- shift: the median offset to physical attacks of isolated notes (scripts/attack_times.py);
- ghosts dropped: notes starting more than GHOST_DB below the stem's loud level (its 95th-percentile RMS), or with
  model amplitude under MIN_AMP. A fixed dBFS floor (step 4) was unfair to quiet stems (brass averages -45 dBFS).

Basic Pitch replaces Suno's MIDI for guitar, bass, synth, strings and brass: it explains 86-97% of each stem's
detected onsets against Suno's 12-82% (log, C3 revision 2). Piano stays on the dedicated piano model, drums on
Suno + NMF additions, vocals on the word alignment.

Usage: .venv/bin/python -I scripts/events_from_transcriptions.py  ->  timing/events/<stem>__basic_pitch.json
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attack_times  # noqa: E402

SR, HOP = 22050, 256
GHOST_DB, MIN_AMP = 30.0, 0.12
SUPPORTED = {"Guitar", "Bass", "Synth"}  # struck/plucked: a note must show an onset in its stem (see support())
STEMS = ["Guitar", "Bass", "Synth", "Strings", "Brass"]


def support(y, times):
    """True where the stem's onset strength peaks above its local (2 s) 60th percentile within -10/+40 ms of the
    note: Basic Pitch re-triggers notes on decaying overtones of distorted chords (bar 44's guitar came out as
    irregular sixteenths where the stem plays eighths). Not applied to strings and brass, whose soft attacks
    rarely show as onsets."""
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
    w = int(1.0 * SR / HOP)
    out = []
    for t in times:
        f = int(t * SR / HOP)
        lo, hi = max(0, f - 1), min(len(env), f + int(0.04 * SR / HOP) + 1)
        local = env[max(0, f - w):min(len(env), f + w)]
        out.append(lo < hi and env[lo:hi].max() > np.percentile(local, 60))
    return out


DET_LAG = 0.012  # s: onset-detector peaks trail real attacks by this much (drums: detector +19.9 ms vs attack +7.5)
SNAP = 0.08      # s: a chord snaps to a detected stem onset this close


def chords(notes, src, gap=0.06):
    """Group notes whose onsets fall within `gap` of a group's first note into one chord, timed at the stem's
    detected onset nearest it (within SNAP, minus DET_LAG), else its physical attack, else the earliest note.
    Basic Pitch's onsets in sustained distorted parts run ~50 ms late (bar 44), and with no decay between strums
    the physical-attack measure finds no clean rise there; the onset detector's peaks track the strums. Basic Pitch spreads one strummed or struck chord over 50-100 ms;
    quantised, that read as a sixteenth plus a dotted note, different each time (human, C3: bar 44's guitar). One
    strum is one strike for the animation too."""
    notes = sorted(notes, key=lambda n: n["t"])
    groups = []
    for n in notes:
        if groups and n["t"] - groups[-1][0]["t"] < gap:
            groups[-1].append(n)
        else:
            groups.append([n])
    starts = np.array([g[0]["t"] for g in groups])
    att = attack_times.attack_offsets(src, starts, before=0.05, after=0.06, quiet=0.6) if len(starts) else []
    y, _ = librosa.load(src, sr=22050, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=22050, hop_length=128, lag=1, max_size=3)
    # Normalised by the local (+-2 s) maximum, so quiet passages register (globally normalised, the ballad's
    # guitar showed no onsets at all in bar 44).
    from scipy.ndimage import maximum_filter1d
    env = env / (maximum_filter1d(env, size=int(4.0 * 22050 / 128)) + 1e-6)
    det = librosa.onset.onset_detect(onset_envelope=env, sr=22050, hop_length=128, units="time", delta=0.05,
                                     normalize=False) - DET_LAG
    out = []
    last_t = None
    for g, t0, a in zip(groups, starts, att):
        k = int(np.argmin(np.abs(det - t0))) if len(det) else -1
        if k >= 0 and abs(det[k] - t0) <= SNAP:
            t = float(det[k])
        elif last_t is not None and t0 - last_t < 0.15:  # under an eighth at 140 bpm (0.21 s)
            t = last_t  # no onset of its own: a continuation Basic Pitch split off, folded into the previous chord
        else:
            t = float(t0 + a) if not np.isnan(a) else float(t0)
        last_t = t
        for n in g:
            out.append({**n, "t": round(t, 4), "end": round(max(n["end"], t + 0.05), 4)})
    return out


def active_filter(stem, events):
    """Keep an event only where its stem is playing: the stem's RMS in the 0.3 s after the event reaches the
    activity threshold of timing/activity.json (active playing sits within 26 dB of the stem's loud level, bleed 32 dB
    or more below). Judged per event, not per section, so short real passages survive (the band stab at 5.4-8.0 s
    in the piano intro) while bleed in silent sections doesn't (409 brass notes in the voice-and-piano intro)."""
    thr = json.loads(Path("timing/activity.json").read_text())["active_db"]
    y, sr = librosa.load(f"audio/stems/It Was Just a Benchmark ({stem}).wav", sr=11025)
    r = 20 * np.log10(librosa.feature.rms(y=y, frame_length=2048, hop_length=256)[0] + 1e-9)
    loud = float(np.percentile(r, 99))
    k = lambda t: int(t * 11025 / 256)  # noqa: E731
    return [e for e in events if r[k(e["t"]):k(e["t"] + 0.3) + 1].max(initial=-200) >= loud + thr]


def main():
    sources = {
        "_doc": "Which event file drives each instrument's machines (steps 4-5, C3 revisions). Written by "
                "scripts/events_from_transcriptions.py.",
        "vocals": {"events": "timing/timing_map.json lines/words", "why": "forced alignment of the as-sung lyrics"},
        "piano": {"events": "timing/events/keyboard__piano_model.json", "why": "dedicated piano model; Suno held ~40%"},
        "drums": {"events": "timing/events/drums__kit.json", "why": "Suno hits + NMF additions (off-beat kicks)"},
        "percussion": {"events": "timing/stem_events/percussion.json", "why": "stem onsets; Suno MIDI had 5 notes"},
        "fx": {"events": "timing/stem_events/fx.json", "why": "stem onsets; Suno MIDI explained 8%"},
    }
    for stem in STEMS:
        src = f"audio/stems/It Was Just a Benchmark ({stem}).wav"
        notes = json.loads(Path(f"timing/transcriptions/{stem.lower()}.json").read_text())["notes"]
        y, _ = librosa.load(src, sr=SR, mono=True)
        db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=1024, hop_length=HOP)[0] + 1e-9)
        floor = float(np.percentile(db, 95)) - GHOST_DB
        keep = []
        sup = support(y, [n["t"] for n in notes]) if stem in SUPPORTED else [True] * len(notes)
        for n, ok in zip(notes, sup):
            f0 = int(n["t"] * SR / HOP)
            level = db[f0:int((n["t"] + 0.08) * SR / HOP) + 1].max() if f0 < len(db) else -120
            if level >= floor and n["vel"] / 127 >= MIN_AMP and ok:
                keep.append(n)
        t = np.unique(np.round([n["t"] for n in keep], 3))
        att = attack_times.attack_offsets(src, attack_times.isolated(t)) * 1000
        att = att[~np.isnan(att)]
        shift = float(np.median(att)) if len(att) >= 8 else 0.0
        ev = [{**n, "t": round(n["t"] + shift / 1000, 4), "end": round(n["end"] + shift / 1000, 4)} for n in keep]
        if stem in SUPPORTED:
            ev = chords(ev, src)
        n_all = len(ev)
        ev = active_filter(stem, ev)
        print(f"{stem:8s} {n_all - len(ev)} events dropped in sections where the stem doesn't play")
        slug = f"{stem.lower()}__basic_pitch"
        Path(f"timing/events/{slug}.json").write_text(json.dumps(
            {"stem": stem, "track": "basic-pitch transcription", "shift_ms": round(shift, 1),
             "dropped_ghosts": len(notes) - len(keep), "ghost_floor_dbfs": round(floor, 1), "events": ev}) + "\n")
        sources[stem.lower()] = {"events": f"timing/events/{slug}.json",
                                 "why": f"basic-pitch; shift {shift:+.1f} ms; {len(notes) - len(keep)} of {len(notes)} "
                                        f"notes dropped (ghosts < {floor:.0f} dBFS, amplitude < {MIN_AMP}"
                                        f"{', or no onset in the stem' if stem in SUPPORTED else ''})"}
        print(f"{stem:8s} kept {len(keep):5d}/{len(notes)}  floor {floor:6.1f} dBFS  shift {shift:+.1f} ms")
    # Piano: the piano model's notes, plus Basic Pitch's where the model has no onset within 50 ms (the model
    # misses some chords, e.g. bar 58 beat 4; Basic Pitch explains 99.4% of the keyboard stem's onsets, the model
    # 89.8%). The model keeps priority: it is the more accurate on pitch.
    model = json.loads(Path("timing/events/keyboard__piano_model.json").read_text())
    bp = json.loads(Path("timing/transcriptions/keyboard.json").read_text())["notes"]
    m_t = np.array(sorted(e["t"] for e in model["events"]))
    yk, _ = librosa.load("audio/stems/It Was Just a Benchmark (Keyboard).wav", sr=SR, mono=True)
    sup = support(yk, [n["t"] for n in bp])
    add = [n for n, ok in zip(bp, sup) if ok and n["vel"] / 127 >= MIN_AMP
           and np.min(np.abs(m_t - (n["t"] + model["shift_ms"] / 1000))) >= 0.05]
    fill = chords([{**n, "t": round(n["t"] + model["shift_ms"] / 1000, 4), "end": round(n["end"] + model["shift_ms"] / 1000, 4),
                    "source": "basic_pitch"} for n in add], "audio/stems/It Was Just a Benchmark (Keyboard).wav")
    ev = active_filter("Keyboard", sorted(model["events"] + fill, key=lambda e: (e["t"], e["pitch"])))
    Path("timing/events/keyboard__piano.json").write_text(json.dumps(
        {"stem": "Keyboard", "track": "piano model + basic-pitch fill-ins", "shift_ms": model["shift_ms"],
         "events": ev}) + "\n")
    sources["piano"] = {"events": "timing/events/keyboard__piano.json",
                        "why": f"piano model ({len(model['events'])} notes) + {len(add)} basic-pitch notes where the "
                               f"model had no onset within 50 ms"}
    print(f"Piano    model {len(model['events'])} + basic-pitch fill-ins {len(add)}")
    sources["drums"] = {"events": "timing/events/drums__kit.json",
                        "why": "strikes from the Drums stem onsets, pieces from LarsNet-separated stems + sub-bass kick check (scripts/drums_strikes.py)"}
    Path("config/event_sources.json").write_text(json.dumps(sources, indent=1) + "\n")


if __name__ == "__main__":
    main()
