"""Re-transcribe the Keyboard stem with a dedicated piano model, because Suno's piano MIDI misses notes in faster
runs (the human, C3: "missing piano notes ... in faster runs -- mostly the off-beat 'and's").

Model: ByteDance high-resolution piano transcription (Kong et al. 2021, "High-resolution Piano Transcription with
Pedals by Regressing Onset and Offset Times"), via piano_transcription_inference on the GPU. Onsets and offsets are
regressed to ~10 ms, so they need no grid; velocities come with them.

Usage: .venv/bin/python -I scripts/transcribe_piano.py  ->  timing/piano_transcription.mid, timing/piano_notes.json
"""
import json
from pathlib import Path

import librosa
from piano_transcription_inference import PianoTranscription, sample_rate

STEM = "audio/stems/It Was Just a Benchmark (Keyboard).wav"

audio, _ = librosa.load(STEM, sr=sample_rate, mono=True)
tr = PianoTranscription(device="cuda")
res = tr.transcribe(audio, "timing/piano_transcription.mid")
notes = sorted(({"t": round(float(n["onset_time"]), 4), "end": round(float(n["offset_time"]), 4),
                 "pitch": int(n["midi_note"]), "vel": int(n["velocity"])} for n in res["est_note_events"]),
               key=lambda n: (n["t"], n["pitch"]))
Path("timing/piano_notes.json").write_text(json.dumps({"stem": STEM, "model": "piano_transcription_inference "
                                                       "(Kong et al. 2021)", "notes": notes}) + "\n")
print(len(notes), "notes")
