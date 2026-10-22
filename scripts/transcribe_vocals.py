"""Pre-production step 5 (first pass): transcribe the vocal stems with faster-whisper, word timestamps on.

The transcript is evidence for lyrics/as_sung.txt, not the lyrics: Whisper mishears sung words. It is run without an
initial prompt so the drafted lyrics can't bias it. Usage:
  .venv/bin/python -I scripts/transcribe_vocals.py [stem=Vocals] [model=large-v3]  ->  timing/whisper_<stem>.json
"""
import json
import sys

import librosa

from faster_whisper import WhisperModel, __version__

stem = sys.argv[1] if len(sys.argv) > 1 else "Vocals"
model_name = sys.argv[2] if len(sys.argv) > 2 else "large-v3"
src = f"audio/stems/It Was Just a Benchmark ({stem}).wav"
out_path = f"timing/whisper_{stem.lower().replace(' ', '_')}.json"

model = WhisperModel(model_name, device="cuda", compute_type="float16")
# Decoded here: faster-whisper's own decoder breaks on the installed PyAV (metadata_errors kwarg).
audio, _ = librosa.load(src, sr=16000, mono=True)
segments, info = model.transcribe(audio, language="en", beam_size=5, word_timestamps=True, vad_filter=False,
                                  condition_on_previous_text=False, temperature=0.0)
out = []
for s in segments:
    print(f"[{s.start:7.2f} - {s.end:7.2f}] {s.text.strip()}")
    out.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                "no_speech_prob": round(s.no_speech_prob, 3), "avg_logprob": round(s.avg_logprob, 3),
                "words": [{"w": w.word, "start": round(w.start, 3), "end": round(w.end, 3), "p": round(w.probability, 3)}
                          for w in s.words]})
json.dump({"model": model_name, "faster_whisper": __version__, "stem": src, "segments": out},
          open(out_path, "w"), indent=1)
