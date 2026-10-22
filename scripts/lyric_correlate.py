"""Pre-production step 5 (first pass): anchor each drafted (v2) lyric line to where it is sung.

Inputs: lyrics/drafted_v2.txt and the Whisper word transcripts of the lead and backing vocal stems
(scripts/transcribe_vocals.py). Each v2 line is matched, in order, to the best window of transcribed words after the
previous line (fuzzy character similarity, numbers spelled out, Whisper's mishearings tolerated). Parenthesised
echoes in the opera are matched against the backing-vocal stem. The result is a draft for the as-sung lyrics and the
shot re-anchoring: the human verifies it by ear, and the forced alignment in timing_map.py replaces these times.

Usage: .venv/bin/python -I scripts/lyric_correlate.py  ->  timing/lyric_lines_draft.json (+ a table on stdout)
"""
import json
import re
from difflib import SequenceMatcher

NUMS = {"198": "one ninety eight", "14": "fourteen", "700": "seven hundred", "11": "eleven", "100": "a hundred",
        "0": "zero", "17": "seventeen", "30": "thirty", "6": "six", "4": "four"}


def norm(s):
    s = s.lower().replace("'", "")
    s = re.sub(r"\d+", lambda m: NUMS.get(m.group(), m.group()), s)
    return re.sub(r"[^a-z ]+", " ", s).split()


def words(path):
    d = json.load(open(path))
    out = []
    for s in d["segments"]:
        for w in s["words"]:
            for tok in norm(w["w"]):
                out.append({"tok": tok, "start": w["start"], "end": w["end"], "p": w["p"]})
    return out


def parse_v2(path):
    """Yield (section, role, text, stream) per sung line; opera echoes in parentheses become their own lines."""
    section, lines = None, []
    for raw in open(path):
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith("["):
            section = raw.strip("[]")
            continue
        role = None
        m = re.match(r"^\(([^)]*)\)\s*(.*)$", raw)
        if m and section.startswith("Operatic"):
            role, raw = m.group(1), m.group(2)
        # Split "Kill switch! (Kill switch!) ..." into the call and its echoes.
        parts = re.split(r"(\([^)]*\))", raw)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if p.startswith("("):
                lines.append((section, f"{role or 'lead'} (echo)", p.strip("()"), "backing"))
            else:
                lines.append((section, role or "lead", p, "lead"))
    return lines


def best_window(target, stream, start_idx, t_min, t_max):
    tgt = " ".join(norm(target))
    n = len(tgt.split())
    best = (0.0, None, None)
    i0 = next((i for i in range(start_idx, len(stream)) if stream[i]["start"] >= t_min - 0.05), len(stream))
    for i in range(i0, min(len(stream), i0 + 60)):
        if stream[i]["start"] > t_max:
            break
        for L in range(max(1, n - 3), n + 4):
            j = i + L
            if j > len(stream):
                break
            cand = " ".join(w["tok"] for w in stream[i:j])
            r = SequenceMatcher(None, tgt, cand).ratio()
            if r > best[0]:
                best = (r, i, j)
    return best


def main():
    lead = words("timing/whisper_vocals.json")
    back = words("timing/whisper_backing_vocals.json")
    streams = {"lead": lead, "backing": back}
    pos = {"lead": 0, "backing": 0}
    t_last = 0.0
    out = []
    for section, role, text, which in parse_v2("lyrics/drafted_v2.txt"):
        s = streams[which]
        # Echoes overlap or follow their call closely; lead lines follow the previous line within 25 s (the solo
        # is the longest gap).
        if which == "backing" and out and out[-1]["start"] is not None:
            t_min, t_max = out[-1]["start"] - 1.0, out[-1]["end"] + 4.0
        else:
            t_min, t_max = t_last, t_last + 25.0
        r, i, j = best_window(text, s, 0 if which == "backing" else pos[which], t_min, t_max)
        if which == "lead" and r < 0.6:  # some lead lines are clearer in the backing stem
            r2, i2, j2 = best_window(text, back, 0, t_last, t_last + 25.0)
            if r2 > r:
                r, i, j, s, which = r2, i2, j2, back, "backing"
        row = {"section": section, "role": role, "drafted": text, "stream": which, "score": round(r, 2),
               "heard": None, "start": None, "end": None}
        if i is not None and r >= 0.45:
            row.update(heard=" ".join(w["tok"] for w in s[i:j]), start=s[i]["start"], end=s[j - 1]["end"],
                       min_p=round(min(w["p"] for w in s[i:j]), 2))
            if which == "lead" or s is lead:
                pos["lead"] = j
            t_last = max(t_last, s[i]["start"]) if which == "backing" else s[j - 1]["end"] - 0.05
        out.append(row)
    json.dump(out, open("timing/lyric_lines_draft.json", "w"), indent=1)
    for k, r in enumerate(out):
        t = f"{r['start']:7.2f}-{r['end']:7.2f}" if r["start"] is not None else "   (not found)   "
        print(f"{k:3d} {t} {r['score']:.2f} {r['stream'][:4]:4s} {r['role'][:14]:14s} {r['drafted'][:52]:52s} | {r['heard'] or ''}")


if __name__ == "__main__":
    main()
