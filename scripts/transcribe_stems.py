"""Re-transcribe the pitched stems with Spotify's Basic Pitch (Bittner et al. 2022, ICASSP model, ONNX backend),
because Suno's MIDI is incomplete for every pitched instrument (human, C3: bars 44, 58, 62 -- eighth-note chords
missing in guitar, bass, synth, strings; Suno's bass in bar 58 has 4 notes where the stem has 10 onsets).

Per stem a frequency range keeps the model on the instrument (no bass notes from the guitar's low strings ringing,
and so on). Usage: .venv/bin/python -I scripts/transcribe_stems.py [stem ...]  ->  timing/transcriptions/<stem>.json
"""
import json
import sys
from pathlib import Path

from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import Model, predict

STEMS = {  # stem: (min Hz, max Hz, onset threshold, frame threshold, min note ms)
    "Guitar": (60, 1600, 0.5, 0.3, 58),
    "Bass": (30, 220, 0.5, 0.3, 58),  # fundamentals only: up to 400 Hz it took 2nd harmonics as notes (octave jumps)
    "Synth": (40, 2500, 0.5, 0.3, 58),
    "Strings": (40, 2500, 0.45, 0.3, 80),
    "Brass": (50, 1500, 0.45, 0.3, 58),
    "Keyboard": (27, 4200, 0.5, 0.3, 58),  # comparison with the piano model (C3 revision 2)
}


def main():
    model = Model(ICASSP_2022_MODEL_PATH)
    out = Path("timing/transcriptions")
    out.mkdir(parents=True, exist_ok=True)
    for stem in sys.argv[1:] or STEMS:
        lo, hi, on_t, fr_t, min_ms = STEMS[stem]
        _, midi, notes = predict(f"audio/stems/It Was Just a Benchmark ({stem}).wav", model, onset_threshold=on_t,
                                 frame_threshold=fr_t, minimum_note_length=min_ms, minimum_frequency=lo,
                                 maximum_frequency=hi, melodia_trick=True)
        ev = sorted(({"t": round(float(s), 4), "end": round(float(e), 4), "pitch": int(p), "vel": int(round(a * 127))}
                     for s, e, p, a, _ in notes), key=lambda n: (n["t"], n["pitch"]))
        (out / f"{stem.lower()}.json").write_text(json.dumps(
            {"stem": stem, "model": "basic-pitch 0.4.0 (ICASSP 2022, ONNX)",
             "params": dict(zip(["min_hz", "max_hz", "onset_threshold", "frame_threshold", "min_note_ms"],
                                STEMS[stem])), "notes": ev}) + "\n")
        midi.write(str(out / f"{stem.lower()}.mid"))
        print(stem, len(ev), "notes")


if __name__ == "__main__":
    main()
