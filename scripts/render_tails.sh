#!/usr/bin/env bash
# C6: render the tails the final's dissolves need (timing/joins.json "tails", scripts/joins.py): for each set, its
# outgoing shots past their plates, at the set's longest tail (spare frames are harmless), full quality, two Blender
# sessions; then pack them like the plates (scripts/c5_pack.sh: frames/<shot>_tail.mkv, bit-exact).
# Usage: scripts/render_tails.sh [SET ...]   (default: every set with tails)
set -euo pipefail
cd "$(dirname "$0")/.."
mapfile -t plan < <(.venv/bin/python -I - "$@" <<'EOF'
import json, sys
t = json.load(open("timing/joins.json"))["tails"]
want = set(a.upper() for a in sys.argv[1:])
by = {}
for sid, x in t.items():
    by.setdefault(x["set"], []).append((sid, x["frames"]))
for s in sorted(by):
    if want and s not in want:
        continue
    ids = [i for i, _ in by[s]]
    half = (len(ids) + 1) // 2
    print(s, max(n for _, n in by[s]), " ".join(ids[:half]), "|", " ".join(ids[half:]))
EOF
)
for line in "${plan[@]}"; do
  read -r S N rest <<< "$line"
  g0=${rest%%|*}; g1=${rest#*|}
  size=3840x2160
  case "$S" in G|H|I) size=3840x3840 ;; esac
  out="renders/c5/set_$S"
  echo "set $S tails ($N frames, $size): $(date -Is)"
  pids=()
  k=0
  for grp in "$g0" "$g1"; do
    [ -n "${grp// /}" ] || continue
    blender -b --factory-startup --python scenes/blender/animatic.py -- "$S" $grp --size "$size" --samples 64 \
      --tail "$N" --out "$out/frames" > "$out/logs/tails_$k.log" 2>&1 &
    pids+=($!); k=$((k + 1))
  done
  for p in "${pids[@]}"; do wait "$p"; done
  grep -h ANIMATIC "$out"/logs/tails_*.log
  scripts/c5_pack.sh "$S" | grep _tail
  echo "set $S tails done: $(date -Is)"
done
