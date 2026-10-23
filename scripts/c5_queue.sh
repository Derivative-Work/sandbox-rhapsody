#!/usr/bin/env bash
# C5: render sets in turn: each set's 4K anchor stills and contact sheet first, then the full render
# (scripts/render_c5.sh, two sessions). Sets G, H and I hold the vertical cut's shots (S30-S65) and render square,
# 3840x3840 (production log: the vertical cut's render format).
# Usage: scripts/c5_queue.sh B C D ...   (waits for any C5 render already running to finish first)
set -euo pipefail
cd "$(dirname "$0")/.."
while pgrep -f "render_c5.sh" > /dev/null; do sleep 60; done
for S in "$@"; do
  size=3840x2160
  case "$S" in G|H|I) size=3840x3840 ;; esac
  echo "set $S ($size): $(date -Is)"
  mkdir -p "renders/c5/set_$S/logs"
  blender -b --factory-startup --python scenes/blender/animatic.py -- "$S" --size "$size" --samples 64 --anchors \
    --out "renders/c5/set_$S/anchors" > "renders/c5/set_$S/logs/anchors.log" 2>&1
  .venv/bin/python -I scripts/c5_sheet.py "$S"
  scripts/render_c5.sh "$S" 2 --size "$size"
  echo "set $S done: $(date -Is)"
done
