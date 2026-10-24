"""How each shot joins the next in the final (style spec, "Joins"; human, C6: dissolves start on the cut).

A join dissolves when both shots are in the intro, ballad, hard rock or outro, and is a hard cut everywhere else:
into and through the opera, into and out of the solo and the coda, and into S65's SIGTERM. A dissolve starts on
the cut and lasts DISSOLVE_BEATS of the beat there (2 in the slow sections, 1 in the hard rock), the incoming shot
on time from its first frame and the outgoing shot running on under it, from its tail render
(animatic.py --tail; its plate already runs one frame past its end).

Usage: .venv/bin/python -I scripts/joins.py  ->  timing/joins.json, and the tail renders each set needs
"""
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TM = json.loads((ROOT / "timing/timing_map.json").read_text())
FPS = TM["fps"]
BEATS = np.array(TM["beats"])
DISSOLVE_BEATS = {"Intro": 2, "Ballad": 2, "Hard rock": 1, "Outro": 2}


def sections():
    out = {}
    for line in (ROOT / "shots/pipeline.md").read_text().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) > 2 and re.fullmatch(r"S\d+[a-z]?", c[0]):
            out[c[0]] = (c[1], c[2].split(",")[0].split(" ")[0])
    return out


def main():
    sec = sections()
    shots = [s for s in TM["shots"] if s.get("cut") is not None and s["id"] != "S66"]
    joins, tails = [], {}
    for a, b in zip(shots, shots[1:]):
        sa, sb = sec[a["id"]][0], sec[b["id"]][0]
        kind = "dissolve" if sa in DISSOLVE_BEATS and sb in DISSOLVE_BEATS and b["id"] != "S65" else "cut"
        j = {"from": a["id"], "to": b["id"], "at_s": b["cut"], "at_frame": b["cut_frame"], "kind": kind}
        if kind == "dissolve":
            k = int(np.searchsorted(BEATS, b["cut"]))
            beat = float(BEATS[min(k, len(BEATS) - 1)] - BEATS[max(k - 1, 0)])
            n = round(DISSOLVE_BEATS[sa] * beat * FPS)
            j.update({"beats": DISSOLVE_BEATS[sa], "frames": n})
            tails[a["id"]] = {"set": sec[a["id"]][1], "frames": n - 1}  # the plate already has one frame past
        joins.append(j)
    (ROOT / "timing/joins.json").write_text(json.dumps({"rule": __doc__.split("\n\n")[1], "joins": joins,
                                                        "tails": tails}, indent=1) + "\n")
    nd = sum(j["kind"] == "dissolve" for j in joins)
    print(f"{len(joins)} joins: {nd} dissolves, {len(joins) - nd} cuts; tail frames {sum(t['frames'] for t in tails.values())}")
    by = {}
    for sid, t in tails.items():
        by.setdefault((t["set"], t["frames"]), []).append(sid)
    for (st, n), ids in sorted(by.items()):
        print(f"set {st} --tail {n}: {' '.join(ids)}")


if __name__ == "__main__":
    main()
