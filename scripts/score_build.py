"""Build a readable score of the timing data (for the C3 check; human, C3: "an actual score would be even easier").

Parts: Vocals (lead melody, with the aligned lyrics), Piano (the model transcription, right hand >= C4, left hand
below), Bass, Guitar (distortion), Drums (kick, snare, toms, hats, crash; hits the NMF added are amber). Every event
is placed on the measured beat grid (timing/timing_map.json) at sixteenth-note resolution, so the notation shows
what the animation will hit, in the song's own bars (incl. its 2/4 and 5/4 bars). Held notes, rests and ties show
durations and note-offs.

Usage: .venv/bin/python -I scripts/score_build.py  ->  cache/score/score.musicxml (+ score_meta.json)
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from music21 import chord, clef, instrument, key, layout, meter, metadata, note, percussion, pitch, stream, tempo

TM = json.loads(Path("timing/timing_map.json").read_text())
BEATS = np.array(TM["beats"])
Q = 0.25  # sixteenth-note grid, in quarters
OUT = Path("cache/score")
BARS_PER_SYSTEM = 3
AMBER = "#e08a00"
# Keys per section (music21 Krumhansl analysis of piano + bass + vocal notes per section, log step 5 / C3): key
# signatures keep in-key notes free of accidentals (human, C3). The 5 s piano tail joins the coda's E-flat.
KEYS = {"piano intro": "G", "intro: voice and piano": "g", "intro: band": "c", "ballad": "B-", "guitar solo": "B-",
        "opera": "B-", "hard rock": "B-", "outro": "B-", "coda": "E-", "piano tail": "E-"}
DRUM = {  # piece -> (display step, octave, notehead)
    "kick": ("F", 4, "normal"), "snare": ("C", 5, "normal"), "toms": ("A", 4, "normal"),
    "hats": ("G", 5, "x"), "crash": ("A", 5, "x"),
}


def qpos(t):
    """Song time -> quarters from beat 0, through the beat grid (one beat = one quarter)."""
    i = int(np.clip(np.searchsorted(BEATS, t) - 1, 0, len(BEATS) - 2))
    return i + (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])


def qz(x):
    return round(x / Q) * Q


def events(path, lo=None, hi=None):
    ev = json.loads(Path(path).read_text())["events"]
    return [e for e in ev if (lo is None or e["pitch"] >= lo) and (hi is None or e["pitch"] < hi)
            and e["t"] < TM["duration_s"]]


def mono(evs, top=True):
    """One line: the highest (or lowest) note at each onset, each held until the next onset."""
    by = defaultdict(list)
    for e in evs:
        by[qz(qpos(e["t"]))].append(e)
    on = sorted(by)
    out = []
    for k, q in enumerate(on):
        e = (max if top else min)(by[q], key=lambda x: x["pitch"])
        end = min(qz(qpos(e["end"])), on[k + 1] if k + 1 < len(on) else 1e9)
        out.append((q, max(Q, end - q), [e]))
    return out


def poly(evs):
    """Chords: notes sharing a quantised onset; each held to its own end, cut at the next onset (no overlaps, so
    each staff stays one readable voice)."""
    by = defaultdict(list)
    for e in evs:
        by[qz(qpos(e["t"]))].append(e)
    on = sorted(by)
    out = []
    for k, q in enumerate(on):
        end = max(qz(qpos(e["end"])) for e in by[q])
        end = min(end, on[k + 1] if k + 1 < len(on) else 1e9)
        out.append((q, max(Q, end - q), by[q]))
    return out


def key_at(t):
    sec = next(x for x in reversed(TM["sections"]) if x["start"] <= t + 1e-6)
    return key.Key(KEYS[sec["name"]])


def spell(midi, k):
    """Spell a MIDI pitch in key k: scale tones by the scale; the raised leading tone in minor; other chromatic
    tones as flats in flat keys, sharps in sharp keys."""
    p = pitch.Pitch(midi=midi)
    cands = [p, p.getHigherEnharmonic(), p.getLowerEnharmonic()]
    cands = [c for c in cands if c is not None and abs(c.alter) <= 1]
    scale = {x.name for x in k.pitches}
    if k.mode == "minor":
        scale.add(k.pitchFromDegree(7).transpose("A1").name)
    for c in cands:
        if c.name in scale:
            return c
    want = -1 if k.sharps < 0 else 1
    for c in cands:
        if c.alter == want:
            return c
    return p


def key_signatures(part, empty=False):
    """Key signature at each section whose key changes; `empty` (drums) puts a no-sharps/flats signature at the same
    places, or the engraver carries the pitched parts' signatures onto the percussion staff."""
    last = None
    for sec in TM["sections"]:
        if KEYS[sec["name"]] != last:
            b = next(b for b in TM["bars"] if abs(b["start"] - sec["start"]) < 1e-3) if sec["start"] > 0 else None
            part.insert(b["beat"] if b else 0, key.KeySignature(0 if empty else key.Key(KEYS[sec["name"]]).sharps))
            last = KEYS[sec["name"]]


def time_signatures(part):
    part.insert(0, meter.TimeSignature("1/4"))  # beat 0 to the first downbeat
    last = None
    for b in TM["bars"]:
        if b["beats"] != last:
            part.insert(b["beat"], meter.TimeSignature(f"{b['beats']}/4"))
            last = b["beats"]


def build_part(name, inst, cl, items, color_of=None, lyrics=None, drums=False):
    p = stream.Part()
    p.partName = name
    p.insert(0, inst)
    p.insert(0, cl)
    time_signatures(p)
    key_signatures(p, empty=drums)
    for q, dur, evs in items:
        if drums:
            pieces = sorted({e["piece"] for e in evs}, key=lambda x: DRUM[x][1] * 7 + "CDEFGAB".index(DRUM[x][0]))
            ns = []
            for pc in pieces:
                n = note.Unpitched()
                n.displayStep, n.displayOctave = DRUM[pc][0], DRUM[pc][1]
                n.notehead = DRUM[pc][2]
                if all(e.get("source") == "stem_nmf" for e in evs if e["piece"] == pc):
                    n.style.color = AMBER
                ns.append(n)
            el = ns[0] if len(ns) == 1 else percussion.PercussionChord(ns)
        else:
            k = key_at(evs[0]["t"])
            pitches = [spell(m, k) for m in sorted({e["pitch"] for e in evs})]
            el = note.Note(pitches[0]) if len(pitches) == 1 else chord.Chord(pitches)
        el.quarterLength = dur
        if lyrics and q in lyrics:
            el.lyric = lyrics[q]
        p.insert(q, el)
    end = TM["bars"][-1]["beat"] + TM["bars"][-1]["beats"]
    last = max((q + d for q, d, _ in items), default=0)
    if last < end:  # pad to the song's last bar, so every part has every measure
        p.insert(last, note.Rest(quarterLength=end - last))
    p = p.makeMeasures()
    for k, m in enumerate(p.getElementsByClass("Measure")):
        m.number = k  # the 1/4 pickup is bar 0, so score bars match timing_map bars
    p.makeTies(inPlace=True)
    p.makeRests(fillGaps=True, inPlace=True)
    if not drums:
        # Accidentals from the key signature in force (music21 otherwise writes one on every altered note).
        for m in p.getElementsByClass("Measure"):
            m.makeAccidentals(searchKeySignatureByContext=True, cautionaryPitchClass=False,
                              cautionaryNotImmediateRepeat=False, overrideStatus=True, inPlace=True)
    return p


def vocal_line():
    """The lead vocal staff built from the aligned words (human, C3: "the lyrics don't appear aligned with the
    notes"; attaching words to the nearest note of Suno's vocal transcription piled several words onto one note).
    Each word starts a note at its aligned start, carrying the word; its pitch is the vocal-MIDI pitch sounding at
    that moment (else the nearest). A pitch change inside the word adds a lyric-less note (a melisma). Echo lines
    (backing voices) are left out of this staff."""
    vm = sorted(events("timing/events/vocals__synth_choir.json"), key=lambda e: e["t"])
    vt = np.array([e["t"] for e in vm])

    def pitch_at(t):
        sounding = [e for e in vm if e["t"] - 0.08 <= t < e["end"]]
        if sounding:
            return max(sounding, key=lambda e: e["pitch"])["pitch"]
        return vm[int(np.argmin(np.abs(vt - t)))]["pitch"]

    words = [w for ln in TM["lines"] if "(echo)" not in ln["role"] for w in ln["words"]]
    words.sort(key=lambda w: w["start"])
    items, lyr = [], {}
    for k, w in enumerate(words):
        q0 = qz(qpos(w["start"]))
        q_end = qz(qpos(w["end"]))
        if k + 1 < len(words):
            q_end = min(q_end, qz(qpos(words[k + 1]["start"])))
        q_end = max(q_end, q0 + Q)
        if items and q0 < items[-1][0] + items[-1][1]:  # never overlap the previous word's notes
            prev = items[-1]
            items[-1] = (prev[0], max(Q, q0 - prev[0]), prev[2])
            if q0 <= prev[0]:
                q0 = prev[0] + Q
        # Pitch changes inside the word, from the vocal MIDI onsets that fall inside it.
        marks = [q0] + [qz(qpos(e["t"])) for e in vm if w["start"] + 0.06 < e["t"] < w["end"] - 0.06]
        marks = sorted(set(m for m in marks if q0 <= m < q_end))
        last_pitch = None
        for j, m in enumerate(marks):
            m_end = marks[j + 1] if j + 1 < len(marks) else q_end
            t_m = w["start"] if j == 0 else next(e["t"] for e in vm if qz(qpos(e["t"])) == m)
            pt = pitch_at(t_m + 0.04)
            if pt == last_pitch and items:  # same pitch: extend instead of re-striking
                q_prev, d_prev, ev_prev = items[-1]
                items[-1] = (q_prev, m_end - q_prev, ev_prev)
                continue
            items.append((m, m_end - m, [{"pitch": pt, "t": w["start"]}]))
            last_pitch = pt
        lyr[q0] = w["w"]
    return items, lyr


def vocal_lyrics(items):
    """Attach each aligned word to the vocal note it starts on (nearest onset within 0.3 s)."""
    ons = np.array([q for q, _, _ in items])
    times = np.array([evs[0]["t"] for _, _, evs in items])
    out = {}
    for ln in TM["lines"]:
        if "(echo)" in ln["role"]:
            continue
        for w in ln["words"]:
            if not len(times):
                break
            k = int(np.argmin(np.abs(times - w["start"])))
            if abs(times[k] - w["start"]) <= 0.3:
                out[ons[k]] = (out[ons[k]] + " " + w["w"]) if ons[k] in out else w["w"]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    voc, lyr = vocal_line()
    parts = [
        build_part("Vocals", instrument.Vocalist(), clef.TrebleClef(), voc, lyrics=lyr),
        build_part("Piano RH", instrument.Piano(), clef.TrebleClef(), poly(events("timing/events/keyboard__piano_model.json", lo=60))),
        build_part("Piano LH", instrument.Piano(), clef.BassClef(), poly(events("timing/events/keyboard__piano_model.json", hi=60))),
        build_part("Bass", instrument.ElectricBass(), clef.Bass8vbClef(),
                   mono(events("timing/events/bass__electric_bass_finger.json"), top=False)),
        build_part("Guitar", instrument.ElectricGuitar(), clef.Treble8vbClef(),
                   poly(events("timing/events/guitar__distortion_guitar.json"))),
        build_part("Drums", instrument.UnpitchedPercussion(), clef.PercussionClef(),
                   poly(events("timing/events/drums__kit.json")), drums=True),
    ]
    sc = stream.Score()
    sc.metadata = metadata.Metadata(title="Sandbox Rhapsody (timing check)")
    for p in parts:
        sc.insert(0, p)
    # One system per page, BARS_PER_SYSTEM bars each, so the preview can show one system at a time.
    nmeas = len(parts[0].getElementsByClass("Measure"))
    for p in parts:
        for k, m in enumerate(p.getElementsByClass("Measure")):
            if k and k % BARS_PER_SYSTEM == 0:
                m.insert(0, layout.PageLayout(isNew=True))
                m.insert(0, layout.SystemLayout(isNew=True))
    sc.parts[0].measure(1).insert(0, tempo.MetronomeMark(number=60))  # 1 quarter = 1 s: timemap ms = quarters x 1000
    sc.write("musicxml", fp=str(OUT / "score.musicxml"))
    print("measures", nmeas)


if __name__ == "__main__":
    main()
