"""Card stunts for set G's swarm (scenes/blender/sets/set_g.py): one 70 x 10 greyscale PNG per frame, each pixel one
probe's LED (row 0 = the back row, column 0 = stage left). `700` on "Just a swarm! Seven hundred strong!",
`EXPLOITGYM` on "It was ExploitGym!", `GO` on each "GO!", then a `6:00` countdown from "Six minutes" (a second at a
time) until S44; the probes blink out of phase in S32 ("blinking pleadingly"); otherwise a slow ripple scaled by the
backing-vocal envelope. Deterministic (a fixed hash, no RNG). Regenerable: cache/set_g_stunts/.

Usage: .venv/bin/python -I scripts/set_g_stunts.py FIRST_FRAME LAST_FRAME
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scenes" / "blender" / "lib"))
import sr_anim as A  # noqa: E402

COLS, ROWS = 70, 10
STUNT_DIR = ROOT / "cache" / "set_g_stunts"


# A 5 x 8 pixel font for the stunts: at one LED per pixel, a TrueType raster thinned EXPLOITGYM's strokes into gaps.
GLYPHS = {
    "0": ".###.|##.##|##.##|##.##|##.##|##.##|##.##|.###.",
    "1": "..##.|.###.|..##.|..##.|..##.|..##.|..##.|.####",
    "2": ".###.|##.##|...##|..##.|.##..|##...|##...|#####",
    "3": "####.|...##|...##|.###.|...##|...##|...##|####.",
    "4": "...##|..###|.####|##.##|#####|...##|...##|...##",
    "5": "#####|##...|##...|####.|...##|...##|##.##|.###.",
    "6": ".###.|##...|##...|####.|##.##|##.##|##.##|.###.",
    "7": "#####|...##|...##|..##.|..##.|.##..|.##..|.##..",
    "8": ".###.|##.##|##.##|.###.|##.##|##.##|##.##|.###.",
    "9": ".###.|##.##|##.##|##.##|.####|...##|...##|.###.",
    ":": ".|.|#|.|.|#|.|.",
    "E": "#####|##...|##...|####.|##...|##...|##...|#####",
    "X": "##.##|##.##|.###.|..#..|.###.|##.##|##.##|##.##",
    "P": "####.|##.##|##.##|####.|##...|##...|##...|##...",
    "L": "##...|##...|##...|##...|##...|##...|##...|#####",
    "O": ".###.|##.##|##.##|##.##|##.##|##.##|##.##|.###.",
    "I": "####|.##.|.##.|.##.|.##.|.##.|.##.|####",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..|..#..",
    "G": ".###.|##.##|##...|##...|##.##|##.##|##.##|.####",
    "Y": "##.##|##.##|##.##|.###.|..#..|..#..|..#..|..#..",
    "M": "#...#|##.##|#####|#.#.#|#...#|#...#|#...#|#...#",
}


def _text_bitmap(s):
    """`s` in the stunt font, centred in a ROWS x COLS 0/1 array; short words doubled in width (bolder, bigger)."""
    gl = [np.array([[ch == "#" for ch in row] for row in GLYPHS[c].split("|")], dtype=np.float32) for c in s]
    wide = sum(g.shape[1] + 1 for g in gl) * 2 <= COLS - 4
    if wide:
        gl = [np.repeat(g, 2, axis=1) for g in gl]
    gap = 2 if wide else 1
    w = sum(g.shape[1] for g in gl) + gap * (len(gl) - 1)
    out = np.zeros((ROWS, COLS), dtype=np.float32)
    x, y = (COLS - w) // 2, (ROWS - 8) // 2
    for g in gl:
        out[y:y + 8, x:x + g.shape[1]] = g
        x += g.shape[1] + gap
    return out


def stunt_frames(f0, f1):
    """Per frame f in [f0, f1]: a ROWS x COLS brightness array (row 0 = the back row, column 0 = stage left)."""
    tm = A.timing_map()
    words = A.events("words")
    benv = A.envelope("backing_env")
    line = {x["id"]: x for x in tm["lines"]}
    shot = {s["id"]: s for s in tm["shots"]}
    go = [w["t"] for w in words if w["w"].startswith("GO") and 184 < w["t"] < 188]
    six = next(w["t"] for w in words if w["w"] == "Six" and 185 < w["t"] < 187)
    cols, rows = np.meshgrid(np.arange(COLS), np.arange(ROWS)[::-1])  # rows[0] = back row index ROWS-1
    phase = ((cols * 7919 + rows * 104729) % 997) / 997.0               # fixed hash, no RNG
    cache = {}

    def txt(s):
        if s not in cache:
            cache[s] = _text_bitmap(s)
        return cache[s]

    def lit(s):
        return 0.015 + 0.985 * txt(s)

    for f in range(f0, f1 + 1):
        t = f / A.FPS
        e = float(benv[min(f, len(benv) - 1)])
        idle = 0.08 + 0.45 * e * (0.5 + 0.5 * np.sin(0.35 * cols + 0.6 * rows - 7.0 * t))
        if line["L35"]["start"] <= t < line["L35"]["end"] + 0.2:
            out = lit("700")
        elif line["L39"]["start"] <= t < line["L39"]["end"] + 0.2:
            out = lit("EXPLOITGYM")
        elif any(g <= t < g + 0.38 for g in go):
            out = lit("GO")
        elif six <= t < shot["S44"]["cut"]:
            left = 360 - int(t - six)
            out = lit(f"{left // 60}:{left % 60:02d}")
        elif shot["S32"]["cut"] <= t < shot["S33"]["cut"]:  # blinking pleadingly
            out = 0.1 + 0.9 * (((t * 1.4 + phase) % 1.0) < 0.3)
        else:
            out = idle
        yield f, out.astype(np.float32)


def write_stunts(f0, f1):
    from PIL import Image
    STUNT_DIR.mkdir(parents=True, exist_ok=True)
    for f, a in stunt_frames(f0, f1):
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").save(STUNT_DIR / f"stunt_{f:06d}.png")


if __name__ == "__main__":
    write_stunts(int(sys.argv[1]), int(sys.argv[2]))
