#!/usr/bin/env bash
# C4: render the animatic plates of the given sets (default: all), one Blender session per set, then assemble.
# Usage: scripts/render_animatic.sh [A B ...]   (logs in renders/animatic/logs/)
set -euo pipefail
cd "$(dirname "$0")/.."
sets=("${@:-A B C D E F G H I}")
mkdir -p renders/animatic/logs
for s in ${sets[@]}; do
  echo "set $s: $(date -Is)"
  blender -b --factory-startup --python scenes/blender/animatic.py -- "$s" > "renders/animatic/logs/set_$s.log" 2>&1
  grep ANIMATIC "renders/animatic/logs/set_$s.log"
done
