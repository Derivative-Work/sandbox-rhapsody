#!/usr/bin/env bash
# C5: render one set at full quality (3840x2160, 64 samples, every frame), its shots split across N concurrent
# Blender sessions on the one GPU (each session's set-up is mostly CPU, so sessions overlap). Shots are dealt
# longest-first to the least-loaded session.
# Usage: scripts/render_c5.sh SET [N=2] [extra animatic.py args]   (frames in renders/c5/set_<SET>/frames/<shot>/,
#        logs in renders/c5/set_<SET>/logs/)
set -euo pipefail
cd "$(dirname "$0")/.."
SET=${1^^}; N=${2:-2}; shift $(( $# >= 2 ? 2 : 1 ))
out="renders/c5/set_$SET"
mkdir -p "$out/logs" "$out/frames"
mapfile -t groups < <(.venv/bin/python -I - "$SET" "$N" <<'EOF'
import json, re, sys
from pathlib import Path
s, n = sys.argv[1], int(sys.argv[2])
owner = {}
for line in Path("docs/brief.md").read_text().splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 7 and re.fullmatch(r"S\d+[a-z]?", c[0]) and (m := re.match(r"([A-I])\b", c[3])):
        owner[c[0]] = m.group(1)
tm = json.load(open("timing/timing_map.json"))
shots = [x for x in tm["shots"] if x["cut"] is not None]
dur = {x["id"]: (shots[k + 1]["cut"] if k + 1 < len(shots) else tm["duration_s"]) - x["cut"] for k, x in enumerate(shots)}
mine = sorted((sid for sid in dur if owner.get(sid) == s), key=lambda sid: -dur[sid])
load, groups = [0.0] * n, [[] for _ in range(n)]
for sid in mine:
    k = load.index(min(load)); groups[k].append(sid); load[k] += dur[sid]
for g in groups:
    if g:
        print(" ".join(g))
EOF
)
pids=()
for k in "${!groups[@]}"; do
  echo "session $k: ${groups[$k]}"
  blender -b --factory-startup --python scenes/blender/animatic.py -- "$SET" ${groups[$k]} --size 3840x2160 \
    --samples 64 --out "$out/frames" "$@" > "$out/logs/session_$k.log" 2>&1 &
  pids+=($!)
done
status=0
for p in "${pids[@]}"; do wait "$p" || status=1; done
grep -h ANIMATIC "$out"/logs/session_*.log
exit $status
