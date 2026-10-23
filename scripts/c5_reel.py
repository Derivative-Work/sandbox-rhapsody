"""C5 review reel for one set: its shots at full quality (renders/c5/set_<SET>/frames/<shot>/), in timeline order,
each with its own stretch of the final audio, joined by hard cuts. Square renders (S30-S65) are cut to their
16:9 centre band; S01's fade up and scripts/edit_fx.py's effects (S22 rewind, S65 CRT collapse) are applied, as in
the animatic. No burn-ins: this is the picture as it will be.

Usage: .venv/bin/python -I scripts/c5_reel.py SET  ->  renders/c5/set_<SET>/set_<SET>.mp4
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edit_fx  # noqa: E402

FPS = 60
W, H = 3840, 2160
TM = json.loads(Path("timing/timing_map.json").read_text())
AUDIO = json.loads(Path("config/audio.json").read_text())["final"]
FADE_UP_S = 3.0


def owner():
    out = {}
    for line in Path("docs/brief.md").read_text().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 7 and re.fullmatch(r"S\d+[a-z]?", c[0]) and (m := re.match(r"([A-I])\b", c[3])):
            out[c[0]] = m.group(1)
    return out


def main():
    s = sys.argv[1].upper()
    root = Path(f"renders/c5/set_{s}")
    shots = [x for x in TM["shots"] if x["cut"] is not None]
    ends = {x["id"]: (shots[k + 1]["cut_frame"] if k + 1 < len(shots) else TM["duration_frames"]) for k, x in enumerate(shots)}
    own = owner()
    mine = [x for x in shots if own.get(x["id"]) == s and (root / "frames" / x["id"]).is_dir()]
    parts = []
    for x in mine:
        sid, f0, f1 = x["id"], x["cut_frame"], ends[x["id"]]
        part = root / f"reel_{sid}.mp4"
        ff = subprocess.Popen(
            ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
             "-i", "-", "-ss", f"{f0 / FPS:.6f}", "-t", f"{(f1 - f0) / FPS:.6f}", "-i", AUDIO, "-map", "0:v", "-map", "1:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
             "-shortest", str(part)], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            src = root / "frames" / sid / f"f_{edit_fx.source_frame(sid, f):04d}.png"
            img = Image.open(src).convert("RGB")
            if img.height > img.width * 9 // 16:  # square: the 16:9 centre band
                band = img.width * 9 // 16
                img = img.crop((0, (img.height - band) // 2, img.width, (img.height + band) // 2))
            if img.size != (W, H):
                img = img.resize((W, H), Image.LANCZOS)
            if sid == "S01" and f / FPS < FADE_UP_S:
                img = Image.fromarray((np.asarray(img) * (f / FPS / FADE_UP_S)).astype(np.uint8))
            img = edit_fx.apply(sid, f, img)
            ff.stdin.write(img.tobytes())
        ff.stdin.close()
        ff.wait()
        parts.append(part)
        print(sid, f1 - f0, "frames")
    lst = root / "reel_parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    out = root / f"set_{s}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(out)], check=True)
    for p in parts:
        p.unlink()
    lst.unlink()
    print("wrote", out)


if __name__ == "__main__":
    main()
