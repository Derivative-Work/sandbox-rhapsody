"""C6 final assembly: the main video (3840x2160) and the vertical shorts (2160x3840), frame by frame on the 60 fps
timeline, from the C5 plates, the overlay tracks and the audio.

Per frame:
- the shot's plate (renders/c5/set_*/frames/<shot>.mkv; square sets G-I centre-cropped to the format), its frame from
  edit_fx.source_frame (S22's rewind), treated by edit_fx.apply (the rewind look, S65's CRT collapse); S01 fades up
  from black over 3 s;
- POV shots (overlays/cards.json HUD shots with a lens frame) through a 2.5% barrel distortion (style spec, "Lens");
- joins from timing/joins.json: a dissolve starts on the cut, the incoming shot on time, the outgoing one running on
  from its tail render (frames/<shot>_tail.mkv) under it, smoothstepped; cuts elsewhere;
- main: from S66, the card backdrop (renders/c6/cards_backdrop.mkv, dimmed footage); then the overlay track
  (renders/overlays/overlay_main.mkv, alpha) over everything.
- shorts: the short's span (overlays/cues.json "shorts"); its first shot's first frame held for its lead-in
  ("freeze_s"); the short's overlay (overlay_short_<id>.mkv).
Audio: main = the final song audio (config/audio.json) up to S66, then the card bounce (audio/post/cards_audio.wav);
shorts = the final song audio over the short's span.
Encoded in parallel chunks with NVENC HEVC (BT.709, tagged: YouTube reads untagged HD as BT.709; Folks Like Us),
concatenated, muxed with AAC.

Usage: .venv/bin/python -I scripts/assemble.py main|short:<id> [--range a:b] [--scale WxH] [--jobs n] [--bitrate 60M --maxrate 120M] [--out file]
  --range: song seconds (previews); --scale: output size (previews)
"""
import glob
import json
import os
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
import edit_fx  # noqa: E402

TM = json.loads(Path("timing/timing_map.json").read_text())
CUES = json.loads(Path("overlays/cues.json").read_text())
CARDS = json.loads(Path("overlays/cards.json").read_text())
JOINS = json.loads(Path("timing/joins.json").read_text())
AUDIO = json.loads(Path("config/audio.json").read_text())["final"]
FPS = TM["fps"]
FADE_UP_S = 3.0
BARREL_K = 0.025
POV = {sid for sid, c in CARDS["hud"]["shots"].items() if c.get("frame")}
SHOTS = [s for s in TM["shots"] if s.get("cut") is not None and s["id"] != "S66"]
S66 = round(CUES["s66"] * FPS)
JOIN_IN = {j["to"]: j for j in JOINS["joins"]}


def shot_at(f):
    k = max(i for i, s in enumerate(SHOTS) if s["cut_frame"] <= f)
    return k, SHOTS[k]


DEC_THREADS = ["-threads", "2", "-filter_threads", "2"]  # FFV1 frame threads otherwise buffer ~2 GB of 4K per decoder

class Pack:
    """Sequential reader of one packed shot (or tail), cropped to the format; reopens on a jump back."""

    def __init__(self, path, w, h):
        self.path, self.w, self.h = path, w, h
        self.start = int(Path(path[:-4] + ".start").read_text().split()[0])
        self.p, self.next, self.cache = None, None, {}
        self.keep = 90 if Path(path).stem == "S22" else 2  # S22's rewind reads two beats back; 4K frames are 25 MB

    def frame(self, f):
        if f in self.cache:
            return self.cache[f]
        if self.p is None or f < self.next or f > self.next + 120:
            self._open(f)
        while self.next <= f:
            buf = self.p.stdout.read(self.w * self.h * 3)
            if len(buf) < self.w * self.h * 3:
                raise RuntimeError(f"{self.path}: no frame {f}")
            a = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3)
            self.cache[self.next] = a
            self.cache.pop(self.next - self.keep, None)
            self.next += 1
        return self.cache[f]

    def _open(self, f):
        if self.p:
            self.p.kill()
        self.cache.clear()
        crop = f"crop={self.cw}:{self.ch}:(iw-{self.cw})/2:(ih-{self.ch})/2,scale={self.w}:{self.h}:flags=lanczos"
        self.p = subprocess.Popen(["ffmpeg", "-v", "quiet", *DEC_THREADS, "-ss", f"{(f - self.start) / FPS:.6f}", "-i", self.path,
                                   "-vf", crop, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, bufsize=1 << 26)
        self.next = f

    def close(self):
        if self.p:
            self.p.kill()


class Plates:
    def __init__(self, fw, fh, w, h):
        self.fw, self.fh, self.w, self.h, self.packs = fw, fh, w, h, {}
        self.maps = None

    def pack(self, name):
        if name not in self.packs:
            path = glob.glob(f"renders/c5/set_*/frames/{name}.mkv")
            if not path:
                raise SystemExit(f"no pack {name}")
            pk = Pack(path[0], self.w, self.h)
            sw, sh = (int(x) for x in subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", path[0]],
                capture_output=True, text=True).stdout.strip().split(","))
            # crop the format's aspect out of the plate's centre (the square sets' 16:9 band or 9:16 column)
            if sw / sh > self.fw / self.fh:
                pk.ch, pk.cw = sh, round(sh * self.fw / self.fh)
            else:
                pk.cw, pk.ch = sw, round(sw * self.fh / self.fw)
            self.packs[name] = pk
        return self.packs[name]

    def shot_frame(self, sid, f):
        """Shot sid's picture at timeline frame f (its plate, or its tail past the plate), effects applied."""
        src = edit_fx.source_frame(sid, f)
        pk = self.pack(sid)
        if not hasattr(pk, "last"):
            pk.last = json.loads(Path(pk.path[:-4] + ".plate.json").read_text())["frames"][1]
        a = pk.frame(src) if src <= pk.last else self.pack(f"{sid}_tail").frame(src)
        if sid == "S22" or f >= edit_fx.SIGTERM:  # the only frames edit_fx treats
            a = np.asarray(edit_fx.apply(sid, f, Image.fromarray(a)))
        if sid == "S01" and f < FADE_UP_S * FPS:
            a = (a.astype(np.float32) * (f / (FADE_UP_S * FPS))).astype(np.uint8)
        if sid in POV:
            a = self.barrel(a)
        return a

    def barrel(self, a):
        if self.maps is None:
            h, w = a.shape[:2]
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (w / 2)
            r2 = nx * nx + ny * ny
            s = (1 + BARREL_K * r2) / (1 + BARREL_K * 1.0)  # corners stay put; the centre bulges
            self.maps = ((nx * s) * (w / 2) + w / 2, (ny * s) * (w / 2) + h / 2)
        return cv2.remap(a, self.maps[0], self.maps[1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    def picture(self, f):
        k, s = shot_at(f)
        j = JOIN_IN.get(s["id"])
        live = {s["id"], j["from"] if j else None}
        for name in [n for n in self.packs if n.removesuffix("_tail") not in live]:
            self.packs.pop(name).close()  # one decoder per live shot, not one per shot so far
        img = self.shot_frame(s["id"], f)
        if j and j["kind"] == "dissolve" and f - s["cut_frame"] < j["frames"]:
            u = (f - s["cut_frame"] + 0.5) / j["frames"]
            u = u * u * (3 - 2 * u)
            out = self.shot_frame(j["from"], f)
            img = cv2.addWeighted(img, u, out, 1 - u, 0)
        return img


class Overlay(Pack):
    def __init__(self, path, w, h, t0):
        self.path, self.w, self.h = path, w, h
        self.f0 = round(t0 * FPS)  # the track's first frame, as overlays/render.mjs numbers it (t0 may fall between frames)
        self.p, self.next, self.cache, self.keep = None, None, {}, 2

    def _open(self, f):
        if self.p:
            self.p.kill()
        self.cache.clear()
        self.p = subprocess.Popen(["ffmpeg", "-v", "quiet", *DEC_THREADS, "-ss", f"{(f - self.f0) / FPS:.6f}", "-i", self.path, "-vf",
                                   f"scale={self.w}:{self.h}", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                                  stdout=subprocess.PIPE, bufsize=1 << 26)
        self.next = f

    def frame(self, f):
        if self.p is None or f != self.next:
            self._open(f)
        buf = self.p.stdout.read(self.w * self.h * 4)
        if len(buf) < self.w * self.h * 4:
            raise RuntimeError(f"{self.path}: no frame {f} (track frame {f - self.f0})")
        self.next += 1
        return np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 4)


def over(base, ov):
    a = ov[:, :, 3:4].astype(np.uint16)
    if not a.any():
        return base
    return ((base.astype(np.uint16) * (255 - a) + ov[:, :, :3].astype(np.uint16) * a + 127) // 255).astype(np.uint8)


def job(spec):
    """Render timeline frames [f0, f1) to an encoded chunk."""
    k, f0, f1, cfg = spec
    W, H = cfg["size"]
    plates = Plates(*cfg["format"], W, H)
    ov = Overlay(cfg["overlay"], W, H, cfg["overlay_t0"])
    back = Overlay(cfg["backdrop"], W, H, CUES["s66"]) if cfg.get("backdrop") else None
    out = Path(cfg["tmp"]) / f"chunk{k:03d}.mkv"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                            "-c:v", "hevc_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "16",
                            "-b:v", cfg["bitrate"], "-maxrate", cfg["maxrate"], "-bufsize", cfg["maxrate"],
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)],
                           stdin=subprocess.PIPE)
    for f in range(f0, f1):
        src = max(f, cfg["hold_to"]) if cfg.get("hold_to") is not None else f  # a short's lead-in holds its plate
        if back is not None and src >= S66:
            pic = back.frame(src)[:, :, :3]
        else:
            pic = plates.picture(src)
        enc.stdin.write(over(pic, ov.frame(f)).tobytes())
    enc.stdin.close()
    enc.wait()
    for pk in plates.packs.values():
        pk.close()
    return str(out)


def main():
    args = sys.argv[1:]
    opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d  # noqa: E731
    what = args[0]
    jobs = int(opt("--jobs", 6))
    if what == "main":
        fmt, size = (3840, 2160), (3840, 2160)
        a, b = 0.0, CUES["end"]
        cfg = {"format": fmt, "overlay": "renders/overlays/overlay_main.mkv", "overlay_t0": 0,
               "backdrop": "renders/c6/cards_backdrop.mkv", "bitrate": "60M", "maxrate": "120M"}
        out = opt("--out", "deliverables/sandbox_rhapsody_main.mp4")
    else:
        sid = what.split(":", 1)[1]
        sh = next(x for x in CUES["shorts"] if x["id"] == sid)
        fmt, size = (2160, 3840), (2160, 3840)
        a, b = sh["from"], sh["to"]
        cfg = {"format": fmt, "overlay": f"renders/overlays/overlay_short_{sid}.mkv", "overlay_t0": sh["from"],
               "bitrate": "50M", "maxrate": "100M", "hold_to": round(sh["plate_from"] * FPS)}
        out = opt("--out", f"deliverables/shorts/sandbox_rhapsody_short_{sid}.mp4")
    if opt("--range"):
        a, b = (float(x) for x in opt("--range").split(":"))
    if opt("--scale"):
        size = tuple(int(x) for x in opt("--scale").split("x"))
    cfg["size"] = size
    cfg["bitrate"], cfg["maxrate"] = opt("--bitrate", cfg["bitrate"]), opt("--maxrate", cfg["maxrate"])
    tmp = Path(out + ".parts")
    tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.glob("chunk*.mkv"):  # an interrupted run's chunks
        p.unlink()
    cfg["tmp"] = str(tmp)
    F0, F1 = round(a * FPS), round(b * FPS)
    n = -(-(F1 - F0) // jobs)
    specs = [(k, F0 + k * n, min(F1, F0 + (k + 1) * n), cfg) for k in range(jobs) if F0 + k * n < F1]
    with Pool(len(specs)) as pool:
        parts = pool.map(job, specs)
    (tmp / "list.txt").write_text("".join(f"file '{Path(p).resolve()}'\n" for p in parts))
    # audio
    if what == "main":
        s66 = CUES["s66"]
        ac = ["-ss", str(a), "-t", str(min(b, s66) - a), "-i", AUDIO] if a < s66 else []
        cc = (["-ss", str(max(0.0, a - s66)), "-t", str(b - max(a, s66)), "-i", "audio/post/cards_audio.wav"]
              if b > s66 else [])
        inputs = ac + cc
        nin = (1 if ac else 0) + (1 if cc else 0)
        af = (f"{''.join(f'[{i + 1}:a]' for i in range(nin))}concat=n={nin}:v=0:a=1[a]" if nin > 1
              else "[1:a]anull[a]")
    else:
        inputs = ["-ss", str(a), "-t", str(b - a), "-i", AUDIO]
        af = "[1:a]anull[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), *inputs,
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-tag:v", "hvc1",
                    # BT.709 primaries, transfer and matrix in the bitstream's VUI (the concat lost two of the three)
                    "-bsf:v", "hevc_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{(F1 - F0) / FPS:.6f}", out],  # not -shortest: it dropped 4 frames
                   check=True)
    for p in parts:
        Path(p).unlink()
    (tmp / "list.txt").unlink()
    tmp.rmdir()
    print(f"{what}: {(F1 - F0) / FPS:.2f} s ({F1 - F0} frames, {size[0]}x{size[1]}) -> {out}")


if __name__ == "__main__":
    main()
