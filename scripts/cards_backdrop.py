"""The dimmed footage under the fact card and end card (human, C6: "a dimmed version of the part of the video where
each card was mentioned behind the text"), from overlays/cues.json "backdrop": per segment, the plates from its
source song time for the segment's length, centre-cropped to 16:9 from the square sets, multiplied by DIM; black
after the last segment. With --preview, also composites the card overlay and the card audio into a 1080p MP4.

Plates come from the C5 packs (renders/c5/set_*/frames/<shot>.mkv). A shot that's being re-rendered falls back to
its superseded pack, but only with --allow-superseded (previews), and says so.

Usage: .venv/bin/python -I scripts/cards_backdrop.py [--size 3840x2160] [--preview out.mp4 [--overlay file]]
                                                     [--allow-superseded]
       ->  renders/c6/cards_backdrop.mkv (FFV1), and the preview if asked
"""
import glob
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TM = json.loads((ROOT / "timing/timing_map.json").read_text())
CUES = json.loads((ROOT / "overlays/cues.json").read_text())
DIM = 0.3
FPS = TM["fps"]
SHOTS = [s for s in TM["shots"] if s.get("cut") is not None and s["id"] != "S66"]
args = sys.argv[1:]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d  # noqa: E731
W, H = map(int, opt("--size", "3840x2160").split("x"))
OUT = ROOT / "renders/c6/cards_backdrop.mkv"


def pack(sid):
    cur = glob.glob(str(ROOT / f"renders/c5/set_*/frames/{sid}.mkv"))
    if cur:
        return cur[0], False
    old = glob.glob(str(ROOT / f"renders/c5/set_*/frames_superseded_*/{sid}.mkv"))
    if old and "--allow-superseded" in args:
        return old[0], True
    raise SystemExit(f"no plates for {sid} (re-rendering?); --allow-superseded for a preview")


def pieces(src, dur):
    """[(pack, first frame in the pack, frame count)] covering song frames src..src+dur, shot by shot."""
    f0, f1 = round(src * FPS), round((src + dur) * FPS)
    out = []
    for k, s in enumerate(SHOTS):
        a = s["cut_frame"]
        b = SHOTS[k + 1]["cut_frame"] if k + 1 < len(SHOTS) else round(CUES["s66"] * FPS)
        lo, hi = max(f0, a), min(f1, b)
        if lo < hi:
            p, old = pack(s["id"])
            if old:
                print(f"WARNING: {s['id']} from its superseded pack (preview only)")
            start = int(Path(p[:-4] + ".start").read_text().split()[0])
            out.append((p, lo - start, hi - lo))
    return out


def main():
    segs = CUES["backdrop"]
    v0, end = CUES["s66"], CUES["end"]
    ins, chains, labels = [], [], []
    for seg in segs:
        n = round((seg["off"] - seg["on"]) * FPS)
        for p, a, cnt in pieces(seg["src"], seg["off"] - seg["on"]):
            i = len(ins) // 2
            ins += ["-i", p]
            chains.append(f"[{i}]trim=start_frame={a}:end_frame={a + cnt},setpts=PTS-STARTPTS,"
                          f"crop=iw:iw*9/16:0:(ih-iw*9/16)/2,scale={W}:{H},setsar=1,format=gbrp[c{i}]")
            labels.append(f"[c{i}]")
    tail = round((end - segs[-1]["off"]) * FPS)
    i = len(ins) // 2
    ins += ["-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={tail / FPS}"]
    chains.append(f"[{i}]format=gbrp[c{i}]")
    labels.append(f"[c{i}]")
    dim = f"colorchannelmixer=rr={DIM}:gg={DIM}:bb={DIM}"
    fc = ";".join(chains) + f";{''.join(labels)}concat=n={len(labels)}:v=1,{dim}[v]"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[v]", "-r", str(FPS),
                    "-c:v", "ffv1", "-level", "3", "-slices", "16", str(OUT)], check=True)
    print(f"backdrop: {len(segs)} segments, {end - v0:.2f} s from {v0} s -> {OUT.relative_to(ROOT)}")
    prev = opt("--preview")
    if prev:
        # --overlay: an overlay render that starts at S66 (render.mjs main --from <s66>); else the full one.
        ov = (["-i", opt("--overlay")] if opt("--overlay") else
              ["-ss", str(v0), "-t", str(end - v0), "-i", str(ROOT / "renders/overlays/overlay_main.mkv")])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT), *ov, "-i", str(ROOT / "audio/post/cards_audio.wav"),
                        "-filter_complex", "[0]scale=1920:1080,format=yuv420p[b];[1]scale=1920:1080[o];"
                        "[b][o]overlay=format=auto,format=yuv420p[v]", "-map", "[v]", "-map", "2:a",
                        "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", prev], check=True)
        print(f"preview -> {prev}")


if __name__ == "__main__":
    main()
