#!/usr/bin/env bash
# Step 8: a re-run must reproduce its frames. Renders the C1 test frame (close) twice at 640x360 and compares.
# Pass: identical, or differing by at most 1 level (of 255) on under 0.1% of pixels. On the RTX 5090, Eevee + the
# compositor bloom differ by exactly that between runs (max 1 level, 0.04% of pixels: GPU float rounding, not a
# seed); Ghost (no bloom) was bit-identical. Every random process reads config/seeds.json. Run on each render box.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
out=$(mktemp -d)
for i in 1 2; do
  blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- "$out/c1_$i.png" 640 360 16 close >/dev/null 2>&1
done
.venv/bin/python -I - "$out" <<'PY'
import hashlib, sys
from PIL import Image
d = sys.argv[1]
import numpy as np
a, b = (np.asarray(Image.open(f"{d}/c1_{i}.png").convert("RGB")).astype(int) for i in (1, 2))
diff = np.abs(a - b)
share = float((diff.max(2) > 0).mean())
ok = diff.max() <= 1 and share < 0.001
print(f"c1 close, two renders: max diff {diff.max()} levels, {share:.4%} of pixels differ -> {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
PY
