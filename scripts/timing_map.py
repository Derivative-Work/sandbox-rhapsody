"""Pre-production step 5: build timing/timing_map.json, the single clock every later step reads.

- beats: Suno's tempo map (identical in all 11 MIDI files; ~1 tempo event per beat, i.e. a beat track), shifted to
  the audio by the median offset of on-beat snare hits in the audio-aligned drum events (timing/events/);
- bars and downbeats: config/meter.json segments over that grid;
- tempo: per bar (BPM from the bar's mean beat interval) and the tempo changes between sections;
- sections: as-sung structure (lyrics/as_sung.txt), boundaries snapped to downbeats;
- words: forced alignment (timing/words.json); the opera's "Kill switch" / "Reward hack" groups are split into four
  calls alternating lead and echo, as the human heard them;
- musical events the shot list names (solo stutter, climb, ...), from the guitar MIDI (timing/timing_map.md);
- shot cuts: config/shot_anchors.json anchors, each cut on a downbeat (cut_for: at or before the line, or the next
  one when the line is a pickup into it);
- everything also in frames at the video's fps (config/look.json).

Usage: .venv/bin/python -I scripts/timing_map.py  ->  timing/timing_map.json, timing/timing_map.md
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import midi_io  # noqa: E402

FPS = json.loads(Path("config/look.json").read_text())["fps"]
AUDIO = json.loads(Path("config/audio.json").read_text())
DURATION = sf.info(AUDIO["final"]).duration  # the master plus the agent-made ending (scripts/ending_audio.py)
ENDING = json.loads(Path(AUDIO["ending"]).read_text())
ROLE_SPLIT = {"Kill switch!": ("Congress", "Congress (echo)"), "Reward hack!": ("Auditors", "Auditors (echo)")}


def fr(t):
    return int(round(t * FPS))


def grid():
    beats = midi_io.load("audio/stems/midi/It Was Just a Benchmark (Drums).mid").get_beats()
    ev = json.loads(Path("timing/events/drums__drums.json").read_text())["events"]
    snare = np.array([e["t"] for e in ev if e["pitch"] in (37, 38)])
    off = np.array([t - beats[np.argmin(abs(beats - t))] for t in snare])
    shift = float(np.median(off[np.abs(off) < 0.03]))
    return beats + shift, shift


def downbeats(beats):
    segs = json.loads(Path("config/meter.json").read_text())["segments"]
    out = []
    for k, s in enumerate(segs):
        end = segs[k + 1]["first_downbeat"] if k + 1 < len(segs) else len(beats)
        out += list(range(s["first_downbeat"], end, 4))
    return [i for i in out if i < len(beats)]


def split_groups(lines):
    out = []
    for ln in lines:
        key = next((k for k in ROLE_SPLIT if ln["text"].startswith(k)), None)
        if key is None:
            out.append(ln)
            continue
        roles = ROLE_SPLIT[key]
        w = ln["words"]
        for c in range(len(w) // 2):
            pair = w[2 * c:2 * c + 2]
            out.append({**ln, "id": f"{ln['id']}{'abcd'[c]}", "role": roles[c % 2], "text": key,
                        "start": pair[0]["start"], "end": pair[-1]["end"], "words": pair})
    return out


def snap(t, db_times):
    return float(db_times[np.argmin(abs(db_times - t))])


PICKUP = 0.7  # s: lines open on pickups of about one beat (0.43-0.45 s here); up to ~1.5 beats counts as a pickup


def cut_for(t, db_times):
    """The brief cuts "on the nearest downbeat"; taken literally that often lands well after a line has begun (up to
    0.85 s, after the whole word "zero." in S63). So: the next downbeat if the line is a short pickup into it,
    otherwise the downbeat at or before the line, so the shot is already up when the line starts."""
    nxt = db_times[db_times >= t]
    if len(nxt) and nxt[0] - t <= PICKUP:
        return float(nxt[0])
    prev = db_times[db_times <= t]
    return float(prev[-1]) if len(prev) else float(t)


def main():
    beats, shift = grid()
    db = downbeats(beats)
    db_t = beats[db]
    bars = []
    for k, i in enumerate(db):
        j = db[k + 1] if k + 1 < len(db) else len(beats)
        end = beats[j] if j < len(beats) else DURATION
        n = j - i
        bars.append({"n": k + 1, "beat": int(i), "beats": int(n), "start": round(float(beats[i]), 4),
                     "end": round(float(end), 4), "bpm": round(float(60 / np.mean(np.diff(beats[i:j + 1]))) if n > 1
                                                             else 0, 1)})
    lines = json.loads(Path("timing/words.json").read_text())["lines"]
    lines = split_groups(lines)
    L = lambda prefix, nth=1: [x for x in lines if x["text"].startswith(prefix)][nth - 1]  # noqa: E731
    bar_at = lambda t: next(b for b in reversed(bars) if b["start"] <= t + 1e-6)  # noqa: E731

    def bar_start(n):
        return next(b for b in bars if b["n"] == n)["start"]

    first_word = lines[0]["start"]
    solo0 = bar_at(131.5)["n"]  # first bar after "before you cut me slack"; see timing_map.md for the bar profile
    events = {
        "song_start": 0.0,
        "first_word": first_word,
        "solo_first_bar": bar_start(solo0),        # sparse held notes, bars 50-52
        "solo_riff": bar_start(solo0 + 3),          # full kit returns
        "solo_stutter": bar_start(solo0 + 4),       # 13-18 short notes per bar, pitch rising (dial-up stutter)
        "solo_climb": bar_start(solo0 + 7),         # stutter ends; long rising line
        "solo_climb_2": bar_start(solo0 + 9),
        "solo_climb_3": bar_start(solo0 + 11),
        "solo_final_bars": bar_start(solo0 + 12),   # peak pitch (bar 62), last bars before the opera
        "opera_downbeat": bar_start(solo0 + 13),
        "coda_band": snap(298.13, db_t),
        "final_hits": 316.33,
        "suno_audio_end": 323.0,
        "release_start": ENDING["crossfade_s"][0],
        "sigterm": ENDING["sigterm_s"],
        "silence": ENDING["silence_from_s"],
        "after_audio": round(ENDING["silence_from_s"] + 0.5, 3),
        "after_fact_card": None,
    }
    sec_bounds = [
        ("piano intro", 0.0, "solo piano, band stab 5.4-8.0 s"),
        ("intro: voice and piano", snap(15.6, db_t), "voice enters on an eighth pickup (first word %.2f s)" % first_word),
        ("intro: band", snap(45.0, db_t), "drum fill on beat 99 (44.5 s), band from the next downbeat"),
        ("ballad", snap(74.4, db_t), "'Operator...'; drums and bass from 73.5 s"),
        ("guitar solo", events["solo_first_bar"], "no vocals"),
        ("opera", events["opera_downbeat"], "call and response"),
        ("hard rock", snap(201.5, db_t), "'You built us a cage'"),
        ("outro", snap(264.6, db_t), "piano, single voice; 5-beat bar before it"),
        ("coda", events["coda_band"], "band and choir return; 'zero' x4 in all, final hits 316.3 s"),
        ("piano tail", snap(318.0, db_t), "the last chord (321.61 s); Suno cut it at 323.0 s, the release is made in post"),
        ("release and SIGTERM", ENDING["crossfade_s"][0], "agent-made: the chord rings on until the SIGTERM at %.2f s" % ENDING["sigterm_s"]),
        ("silence", ENDING["silence_from_s"], "black; the fact card follows"),
    ]
    sections = []
    for k, (name, t, why) in enumerate(sec_bounds):
        end = sec_bounds[k + 1][1] if k + 1 < len(sec_bounds) else DURATION
        sections.append({"name": name, "start": round(t, 4), "end": round(end, 4), "start_frame": fr(t),
                         "bpm_median": round(float(np.median([b["bpm"] for b in bars if t <= b["start"] < end] or [0])), 1),
                         "why": why})
    tempo_changes = [{"t": s["start"], "section": s["name"], "bpm": s["bpm_median"]} for k, s in enumerate(sections)
                     if k == 0 or abs(s["bpm_median"] - sections[k - 1]["bpm_median"]) > 3]

    anchors = json.loads(Path("config/shot_anchors.json").read_text())["shots"]
    shots = []
    for a in anchors:
        if "line" in a:
            ln = L(a["line"], a.get("nth", 1))
            t = ln["start"]
            if "word" in a:
                t = next(w["start"] for w in ln["words"] if w["w"].startswith(a["word"]))
            src = f"{ln['id']} '{ln['text'][:40]}'" + (f" word '{a['word']}'" if "word" in a else "")
        else:
            t = events[a["event"]]
            src = a["event"]
        if t is None:
            shots.append({**a, "anchor": None, "cut": None, "anchor_source": src})
            continue
        cut = t if a.get("cut") == "anchor" else cut_for(t, db_t)
        shots.append({"id": a["id"], "anchor": round(t, 4), "anchor_source": src, "cut": round(cut, 4),
                      "cut_frame": fr(cut), "cut_minus_anchor_ms": round((cut - t) * 1000),
                      **{k: a[k] for k in ("proposed", "provisional", "note") if k in a}})
    # Cuts must increase; a collision (two anchors snapping to one downbeat) falls back to the later anchor itself.
    for k in range(1, len(shots)):
        if shots[k]["cut"] is not None and shots[k - 1]["cut"] is not None and shots[k]["cut"] <= shots[k - 1]["cut"]:
            shots[k]["cut"], shots[k]["cut_frame"] = shots[k]["anchor"], fr(shots[k]["anchor"])
            shots[k]["cut_note"] = "downbeat taken by the previous shot; cut on the anchor"
    for s in shots:
        if s.get("cut") is not None:
            s["cut_minus_anchor_ms"] = round((s["cut"] - s["anchor"]) * 1000)

    out = {
        "fps": FPS, "duration_s": round(DURATION, 4), "duration_frames": fr(DURATION),
        "audio": AUDIO["final"] + " (the master, offset 0 samples to the Suno mix, plus the agent-made ending)",
        "grid_shift_s": round(shift, 4),
        "beats": [round(float(b), 4) for b in beats],
        "downbeat_beats": [int(i) for i in db],
        "bars": bars, "tempo_changes": tempo_changes, "sections": sections, "events": events,
        "lines": [{**ln, "start_frame": fr(ln["start"]), "end_frame": fr(ln["end"]),
                   "words": [{**w, "start_frame": fr(w["start"]), "end_frame": fr(w["end"])} for w in ln["words"]]}
                  for ln in lines],
        "shots": shots,
    }
    Path("timing/timing_map.json").write_text(json.dumps(out, indent=1) + "\n")
    report(out)


def report(m):
    R = ["# Timing map", "", f"Generated by `scripts/timing_map.py` into `timing/timing_map.json` ({m['fps']} fps, "
         f"{m['duration_s']} s = {m['duration_frames']} frames). Times in seconds of the master, which is "
         "sample-aligned with the Suno mix.", "",
         f"**Beat grid:** Suno's MIDI tempo map ({len(m['beats'])} beats, identical in all 11 files), shifted "
         f"{m['grid_shift_s'] * 1000:+.1f} ms so on-beat snares in the audio sit on it. librosa's own beat track agrees "
         "in tempo (139.7 BPM in the band sections) but lands ~24 ms late, its usual lean toward onset peaks.", "",
         f"**Bars:** {len(m['bars'])}, from `config/meter.json` (4/4, with a 2-beat bar at the voice's entry, a "
         "2-beat bar before the band, a 5-beat bar into the outro).", "",
         "## Sections", "", "| Section | Start (s) | Frame | Median BPM | Evidence |", "| --- | --- | --- | --- | --- |"]
    for s in m["sections"]:
        R.append(f"| {s['name']} | {s['start']:.2f} | {s['start_frame']} | {s['bpm_median']} | {s['why']} |")
    R += ["", "## Musical events", "", "| Event | Time (s) |", "| --- | --- |"]
    R += [f"| {k} | {v if v is None else f'{v:.2f}'} |" for k, v in m["events"].items()]
    R += ["", "## Shot cuts", "", "Cut on the downbeat nearest each anchor (brief). Negative = the cut leads the "
          "anchor (a pickup).", "", "| Shot | Anchor (s) | Source | Cut (s) | Frame | Cut − anchor (ms) | Note |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    R[R.index("Cut on the downbeat nearest each anchor (brief). Negative = the cut leads the "
              "anchor (a pickup).")] = ("Cut on the downbeat at or before each anchor, or the next downbeat when the "
                                        "line is a pickup into it (within 0.7 s, about 1.5 beats). Negative = the cut leads the line.")
    for s in m["shots"]:
        note = " ".join(x for x in (("**proposed**" if s.get("proposed") else ""),
                                    ("**provisional**" if s.get("provisional") else ""), s.get("note", ""),
                                    s.get("cut_note", "")) if x)
        if s.get("anchor") is None:
            R.append(f"| {s['id']} | — | {s['anchor_source']} | — | — | — | {note} |")
        else:
            R.append(f"| {s['id']} | {s['anchor']:.2f} | {s['anchor_source']} | {s['cut']:.2f} | {s['cut_frame']} | "
                     f"{s['cut_minus_anchor_ms']:+d} | {note} |")
    Path("timing/timing_map.md").write_text("\n".join(R) + "\n")


if __name__ == "__main__":
    main()
