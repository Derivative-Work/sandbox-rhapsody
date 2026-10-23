#!/usr/bin/env bash
# C5: follow scripts/c5_queue.sh (its log, renders/c5/queue.log): as each set finishes rendering, build its review
# reel (scripts/c5_reel.py) and pack its frames losslessly (scripts/c5_pack.sh), so the disk holds the whole video.
# Usage: [C5_QUEUE_LOG=renders/c5/queue.log] scripts/c5_follow.sh B C D ...   (log: renders/c5/follow.log)
set -euo pipefail
cd "$(dirname "$0")/.."
qlog=${C5_QUEUE_LOG:-renders/c5/queue.log}
for S in "$@"; do
  until grep -q "^set $S done" "$qlog"; do sleep 60; done
  echo "set $S: reel $(date -Is)"
  .venv/bin/python -I scripts/c5_reel.py "$S" | tail -1
  scripts/c5_pack.sh "$S"
  echo "set $S packed: $(date -Is); $(df -h --output=avail . | tail -1) free"
done
