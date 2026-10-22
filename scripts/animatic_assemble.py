"""C4 animatic: every shot at its final timing on the 60 fps timeline, with the final audio.

Each frame comes from its shot's plate (renders/animatic/plates/<shot>/f_<frame>.png, scenes/blender/animatic.py);
a shot without a plate yet is a grey card naming the shot, its set and the brief's visual, so the cut is complete
from the first version. Burnt in for review: shot id and set (top left), bar.beat and timecode (top right), the
sung line with the current word highlighted (bottom), the brief's on-screen text for the shot (bottom right).
Hard cuts; S01's fade up from black is applied here, and the S22 rewind and the S65 CRT collapse come from
scripts/edit_fx.py (edit effects, as the pipeline table says).

Usage: .venv/bin/python -I scripts/animatic_assemble.py [out.mp4] [--from S] [--to S]  (default
renders/animatic/animatic_v1.mp4, the whole song)
"""
import bisect
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edit_fx  # noqa: E402

W, H = 640, 360
FPS = 60
TM = json.loads(Path("timing/timing_map.json").read_text())
AUDIO = json.loads(Path("config/audio.json").read_text())["final"]
FONT = "assets/fonts/Inter[opsz,wght].ttf"
FADE_UP_S = 3.0


def brief_rows():
    rows = {}
    for line in Path("docs/brief.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and re.fullmatch(r"S\d+[a-z]?", cells[0]):
            rows[cells[0]] = dict(zip(["id", "section", "anchor", "set", "visual", "gag", "pipeline"], cells))
    return rows


def wrap(draw, text, font, width):
    out, cur = [], ""
    for w in text.split():
        nxt = f"{cur} {w}".strip()
        if draw.textlength(nxt, font=font) > width and cur:
            out.append(cur)
            cur = w
        else:
            cur = nxt
    return out + ([cur] if cur else [])


def main():
    args = sys.argv[1:]
    out = Path(next((a for a in args if a.endswith(".mp4")), "renders/animatic/animatic_v1.mp4"))
    shots = [s for s in TM["shots"] if s["cut"] is not None]  # S67 waits on the fact card's length
    ids = [s["id"] for s in shots]
    a = ids.index(args[args.index("--from") + 1]) if "--from" in args else 0
    b = ids.index(args[args.index("--to") + 1]) + 1 if "--to" in args else len(shots)
    f_start = shots[a]["cut_frame"]
    f_end = shots[b]["cut_frame"] if b < len(shots) else TM["duration_frames"]
    cuts = [s["cut_frame"] for s in shots]
    rows = brief_rows()
    beats = np.array(TM["beats"])
    bars = TM["bars"]
    bar_starts = [x["start"] for x in bars]
    lines = [(li["start_frame"], li["end_frame"], li) for li in TM["lines"]]
    f_small = ImageFont.truetype(FONT, 13)
    f_line = ImageFont.truetype(FONT, 18)
    f_card = ImageFont.truetype(FONT, 16)
    f_big = ImageFont.truetype(FONT, 34)
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-ss", f"{f_start / FPS:.6f}", "-t", f"{(f_end - f_start) / FPS:.6f}", "-i", AUDIO,
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], stdin=subprocess.PIPE)
    missing, used = set(), set()
    for f in range(f_start, f_end):
        k = bisect.bisect_right(cuts, f) - 1
        sid = ids[k]
        r = rows.get(sid, {})
        plate = Path(f"renders/animatic/plates/{sid}/f_{edit_fx.source_frame(sid, f):04d}.png")
        if plate.exists():
            img = Image.open(plate).convert("RGB").resize((W, H))
            used.add(sid)
        else:
            missing.add(sid)
            img = Image.new("RGB", (W, H), (46, 44, 54))
            d = ImageDraw.Draw(img)
            d.text((W / 2, 110), sid, font=f_big, fill=(200, 200, 210), anchor="mm")
            d.text((W / 2, 145), f"set {r.get('set', '?')}  ·  not rendered yet", font=f_card, fill=(150, 150, 165),
                   anchor="mm")
            for j, ln in enumerate(wrap(d, r.get("visual", ""), f_card, W - 120)[:4]):
                d.text((W / 2, 180 + 22 * j), ln, font=f_card, fill=(190, 190, 200), anchor="mm")
        t = f / FPS
        if sid == "S01" and t < FADE_UP_S:
            img = Image.fromarray((np.asarray(img) * (t / FADE_UP_S)).astype(np.uint8))
        img = edit_fx.apply(sid, f, img)
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle((0, 0, W, 20), fill=(0, 0, 0, 150))
        d.text((6, 3), f"{sid}  ·  set {r.get('set', '—')}  ·  {r.get('section', '')}", font=f_small,
               fill=(235, 235, 240))
        bi = bisect.bisect_right(bar_starts, t) - 1
        bb = ""
        if bi >= 0:
            j = int(np.searchsorted(beats, t, side="right")) - 1
            bb = f"bar {bars[bi]['n']}.{max(1, j - bars[bi]['beat'] + 2)}  "
        d.text((W - 6, 3), f"{bb}{int(t // 60)}:{t % 60:05.2f}  f{f}", font=f_small, fill=(235, 235, 240),
               anchor="ra")
        cur = [li for s0, s1, li in lines if s0 <= f <= s1 + 12]
        if cur:
            li = cur[-1]
            x = W / 2 - d.textlength(li["text"], font=f_line) / 2
            d.rectangle((0, H - 34, W, H), fill=(0, 0, 0, 140))
            for wd in li["words"]:
                on = wd["start_frame"] <= f
                txt = wd["w"] + " "
                d.text((x, H - 26), txt, font=f_line, fill=(255, 214, 120) if on else (200, 200, 210))
                x += d.textlength(txt, font=f_line)
        gag = r.get("gag", "—")
        if gag and gag != "—":
            for j, ln in enumerate(wrap(d, gag, f_small, 260)[:3]):
                d.text((W - 6, 26 + 16 * j), ln, font=f_small, fill=(140, 230, 210), anchor="ra")
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print(f"wrote {out}: frames {f_start}-{f_end}, plates for {sorted(used)}; cards for {len(missing)} shots")


if __name__ == "__main__":
    main()
