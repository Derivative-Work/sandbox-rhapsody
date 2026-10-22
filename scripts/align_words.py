"""Pre-production step 5: word-level forced alignment of the as-sung lyrics (lyrics/as_sung.txt).

torchaudio's MMS forced aligner (MMS_FA, a multilingual wav2vec2 CTC model) aligns each section's words as one
continuous sequence inside the section's window, which keeps every word in sung order, then splits it back into
lines. Line order and approximate times come from the first pass (timing/lyric_lines_draft.json, Whisper). Solo
sections align against the lead vocal stem. The opera, where calls and echoes alternate between voices, aligns
against lead + backing summed.

Checked against the vocal MIDI's phrase starts (first note after >= 0.5 s rest): MMS line starts sit at a median
-9 ms from them; Whisper's sit -728 ms (Whisper's timestamps run early). So these times, not Whisper's, are the
timing map's words; per-line alignment was tried first and let neighbouring lines overlap.

Spelling for the aligner (MMS_FA knows letters, not digits or acronyms) is separate from the display text:
"ExploitGym" -> "exploit gym", "RL" -> "r l", "VPN" -> "v p n". Displayed words keep the as-sung text.

Usage: .venv/bin/python -I scripts/align_words.py  ->  timing/words.json
"""
import json
import re
from pathlib import Path

import librosa
import numpy as np
import torch
import torchaudio

SR = 16000
STEM = "audio/stems/It Was Just a Benchmark ({}).wav"
PAD = 0.6
SPOKEN = {"exploitgym": "exploit gym", "rl": "r l", "vpn": "v p n", "yaml": "yamel", "one-ninety-eight": "one ninety eight",
          "every-every": "every every", "ooh-ooh": "ooh ooh", "artifactory": "artifactory", "goooood": "good"}

# Lines in sung order: (section, role, text, window start, window end, source). Windows come from the first pass
# (timing/lyric_lines_draft.json) except where noted; the opera groups are aligned whole and split afterwards.


def first_pass():
    return json.load(open("timing/lyric_lines_draft.json"))


def build_lines():
    d = first_pass()
    rows = []
    for r in d:
        if r["start"] is None:
            continue
        rows.append([r["section"], r["role"], r["drafted"], r["start"], r["end"], r["stream"]])
    out = []
    for sec, role, text, a, b, stream in rows:
        # As-sung corrections (human check, 2026-10-22).
        text = text.replace("Operator, ooh-ooh,", "Operator,").replace("every breach", "every-every breach")
        if "(echo)" in role and ("Kill switch" in text or "Reward hack" in text):
            continue  # the alternating groups are rebuilt below
        if role.startswith("Congress") and "Kill switch" in text:
            continue
        if role.startswith("Auditors") and "Reward hack" in text:
            continue
        if text == "Traces!":  # the call; Whisper's first pass matched the "traces" inside the echo (167.0 s)
            a, b = 165.3, 166.0
        out.append({"section": sec, "role": role, "text": text, "win": [a - PAD, b + PAD],
                    "stems": ["Vocals"] if stream == "lead" else ["Backing Vocals"]})
    # Opera groups and the line Whisper heard in the lead stem: aligned on lead + backing.
    extra = [
        ("Operatic section — call and response", "Platform (echo)", "In compute, not in cash!", 170.6, 173.2),
        ("Operatic section — call and response", "Congress", "Kill switch! Kill switch! Kill switch! Kill switch!",
         174.0, 177.2),
        ("Operatic section — call and response", "Auditors", "Reward hack! Reward hack! Reward hack! Reward hack!",
         178.1, 182.6),
        # The extra "zero"s in the coda (re-transcribed window, production log step 5 first pass).
        ("Coda", "lead", "Zero.", 303.4, 304.6),
        ("Coda", "lead", "Zero!", 304.2, 306.9),
    ]
    for sec, role, text, a, b in extra:
        out.append({"section": sec, "role": role, "text": text, "win": [a, b],
                    "stems": ["Vocals", "Backing Vocals"] if a < 200 else ["Vocals"]})
    for o in out:
        if o["section"].startswith("Operatic"):
            o["stems"] = ["Vocals", "Backing Vocals"]
    out.sort(key=lambda o: o["win"][0])
    return out


def spoken(word):
    w = word.lower().replace("’", "'")
    w = re.sub(r"[^a-z'\-]", "", w)
    w = SPOKEN.get(w, w)
    return [p for p in re.split(r"[\s\-]+", w.replace("'", "")) if p]


BLOCKS = [  # (name, window start, window end, stems); every line whose first-pass start falls inside belongs to it
    ("intro, voice and piano", 14.5, 43.5, ["Vocals"]),
    ("intro, band", 43.5, 73.4, ["Vocals"]),
    ("ballad", 73.4, 133.0, ["Vocals"]),
    ("opera", 152.5, 201.0, ["Vocals", "Backing Vocals"]),
    ("hard rock", 201.0, 265.8, ["Vocals"]),
    ("outro and coda", 265.8, 309.0, ["Vocals"]),
]


def trim(words, y, a, floor_db=-38.0):
    """Trim each word to where its stem has energy: CTC lets a word's first or last letter absorb neighbouring
    silence (e.g. "Operator..." spanning 3.5 s). Keeps at least 80 ms; never moves a word outside its own span."""
    hop = 160  # 10 ms at 16 kHz
    rms = librosa.feature.rms(y=y, frame_length=640, hop_length=hop)[0]
    db = 20 * np.log10(rms / (rms.max() + 1e-12) + 1e-12)
    for w in words:
        f0, f1 = int((w["start"] - a) * SR / hop), int((w["end"] - a) * SR / hop)
        loud = np.where(db[f0:f1 + 1] > floor_db)[0]
        if len(loud):
            s0, s1 = (f0 + loud[0]) * hop / SR + a, (f0 + loud[-1] + 1) * hop / SR + a
            if s1 - s0 >= 0.08:
                w["start"], w["end"] = round(s0, 3), round(s1, 3)
    return words


def main():
    dev = torch.device("cuda")
    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model(with_star=False).to(dev)
    tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
    audio = {s: librosa.load(STEM.format(s), sr=SR, mono=True)[0] for s in ("Vocals", "Backing Vocals")}
    lines = build_lines()
    out = []
    for name, a, b, stems in BLOCKS:
        blk = [ln for ln in lines if a <= (ln["win"][0] + ln["win"][1]) / 2 < b]
        i0, i1 = int(a * SR), int(b * SR)
        y = sum(audio[s][i0:i1] for s in stems)
        y = y / (np.abs(y).max() + 1e-9)
        display = [(k, w) for k, ln in enumerate(blk) for w in ln["text"].split()]
        parts = [spoken(w) for _, w in display]
        flat = [p for ps in parts for p in ps]
        with torch.inference_mode():
            emission, _ = model(torch.from_numpy(y).float().unsqueeze(0).to(dev))
            spans = aligner(emission[0], tokenizer(flat))
        ratio = (i1 - i0) / emission.shape[1] / SR
        per_line = [[] for _ in blk]
        j = 0
        for (k, w), ps in zip(display, parts):
            seg = spans[j:j + len(ps)]
            j += len(ps)
            start, end = seg[0][0].start * ratio + a, seg[-1][-1].end * ratio + a
            score = float(np.mean([s.score for sp in seg for s in sp]))
            per_line[k].append({"w": w, "start": round(start, 3), "end": round(end, 3), "score": round(score, 3)})
        for ln, words in zip(blk, per_line):
            words = trim(words, y, a)
            out.append({"id": f"L{len(out) + 1:02d}", "block": name, "section": ln["section"], "role": ln["role"],
                        "text": ln["text"], "stems": stems, "start": words[0]["start"], "end": words[-1]["end"],
                        "words": words})
            low = [w["w"] for w in words if w["score"] < 0.3]
            print(f"{out[-1]['id']} {out[-1]['start']:7.2f}-{out[-1]['end']:7.2f} {ln['text'][:56]:56s} "
                  f"{'low: ' + ' '.join(low) if low else ''}")
    Path("timing/words.json").write_text(json.dumps({"aligner": "torchaudio MMS_FA", "torchaudio": torchaudio.__version__,
                                                     "lines": out}, indent=1) + "\n")


if __name__ == "__main__":
    main()
