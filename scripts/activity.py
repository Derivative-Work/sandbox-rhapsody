"""Which stems play in which section: timing/activity.json.

A stem is active in a section when the section's 75th-percentile RMS is within ACTIVE_DB of the stem's loud level
(99th percentile). Transcriptions are filtered by it (scripts/events_from_transcriptions.py): Basic Pitch transcribes
bleed in sections where a stem doesn't play (brass at 2.7 notes/s in the voice-and-piano intro, where the brass stem
sits 37 dB under its loud level). The values separate cleanly: active sections sit within 26 dB, inactive ones
32 dB or more below.

Usage: .venv/bin/python -I scripts/activity.py  ->  timing/activity.json
"""
import json
from pathlib import Path

import librosa
import numpy as np

ACTIVE_DB = -28.0
STEMS = ["Vocals", "Backing Vocals", "Keyboard", "Guitar", "Bass", "Synth", "Strings", "Brass", "Drums", "Percussion",
         "FX"]


def main():
    TM = json.loads(Path("timing/timing_map.json").read_text())
    out = {"_doc": __doc__.split("\n\n")[1].replace("\n", " "), "active_db": ACTIVE_DB, "stems": {}}
    for s in STEMS:
        y, sr = librosa.load(f"audio/stems/It Was Just a Benchmark ({s}).wav", sr=11025)
        r = 20 * np.log10(librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0] + 1e-9)
        loud = float(np.percentile(r, 99))
        t = np.arange(len(r)) * 512 / 11025
        out["stems"][s] = {}
        for sec in TM["sections"]:
            v = float(np.percentile(r[(t >= sec["start"]) & (t < sec["end"])], 75) - loud)
            out["stems"][s][sec["name"]] = {"db": round(v, 1), "active": v >= ACTIVE_DB}
        print(s, [sec for sec, v in out["stems"][s].items() if v["active"]])
    Path("timing/activity.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
