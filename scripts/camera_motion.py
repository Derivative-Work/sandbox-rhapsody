"""Measure camera motion in the Animusic references: how fast and in what way the camera moves.

Decodes each video at 10 fps, 320 px wide (NVDEC), and computes dense optical flow (Farneback) between consecutive
frames. Per frame pair, the flow field is fitted with a similarity model (translation, zoom, roll) whose residual
stands for parallax. Pan/track = translation, push/pull = zoom, orbit = translation plus strong parallax.
Speeds are in frame widths per second.

Shot boundaries: Animusic joins most shots with dissolves, which ffmpeg's scene score misses. Each frame is warped
onto the next by its flow; inside a continuous move the warp predicts the next frame well, while a cut or the middle
of a dissolve doesn't. Boundaries are peaks of that prediction error (cuts: one-pair spikes; dissolves: runs). Usage: .venv/bin/python -I scripts/camera_motion.py -> style/camera_motion.json
"""
import json
import re
import sys
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H43, H169, FPS = 320, 240, 180, 10


def frames(path, h):
    cmd = ["ffmpeg", "-v", "error", "-hwaccel", "cuda", "-i", str(path), "-an", "-vf", f"fps={FPS},scale={W}:{h},format=gray",
           "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = W * h
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, W)
    p.wait()


def fit(flow, h):
    ys, xs = np.mgrid[0:h:8, 0:W:8]
    f = flow[0:h:8, 0:W:8]
    x, y = (xs - W / 2).ravel() / W, (ys - h / 2).ravel() / W
    u, v = f[..., 0].ravel() / W, f[..., 1].ravel() / W
    # u = tx + s*x - r*y ; v = ty + s*y + r*x
    A = np.zeros((2 * len(x), 4))
    A[0::2] = np.c_[np.ones_like(x), np.zeros_like(x), x, -y]
    A[1::2] = np.c_[np.zeros_like(x), np.ones_like(x), y, x]
    b = np.empty(2 * len(x)); b[0::2], b[1::2] = u, v
    p, *_ = np.linalg.lstsq(A, b, rcond=None)
    res = np.sqrt(np.mean((A @ p - b) ** 2))
    return p, res


def boundaries(err, k=4.0, min_gap=FPS * 1.5):
    """Indices where the warp error rises well above its rolling median (robust z > k), merged within 1.5 s, so a
    dissolve's run counts once."""
    pad = FPS * 5
    e = np.pad(err, pad, mode="edge")
    med = np.array([np.median(e[i:i + 2 * pad]) for i in range(len(err))])
    mad = np.array([np.median(np.abs(e[i:i + 2 * pad] - med[i])) for i in range(len(err))]) + 0.5
    hits = np.where((err - med) / mad > k)[0]
    out = []
    for h in hits:
        if not out or h - out[-1] > min_gap:
            out.append(int(h))
    return out


def main():
    only = sys.argv[1:]  # optional slugs, for a test run
    out = {}
    for path in sorted(Path("reference/inspiration").glob("*.webm")):
        slug = re.sub(r" \(Animusic\).*", "", path.name).lower().replace(" ", "-")
        if only and slug not in only:
            continue
        wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                             "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip().split(",")
        h = H43 if int(wh[0]) * 3 == int(wh[1]) * 4 else H169
        prev, rows = None, []
        for g in frames(path, h):
            if prev is not None:
                fl = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 21, 3, 5, 1.1, 0)
                (tx, ty, s, r), res = fit(fl, h)
                hh, ww = g.shape
                gx, gy = np.meshgrid(np.arange(ww, dtype=np.float32), np.arange(hh, dtype=np.float32))
                pred = cv2.remap(prev, gx - fl[..., 0], gy - fl[..., 1], cv2.INTER_LINEAR)
                err = float(np.mean(np.abs(pred.astype(np.int16) - g.astype(np.int16))))
                cut = float(np.mean(np.abs(g.astype(int) - prev.astype(int)))) > 40
                rows.append((np.hypot(tx, ty) * FPS, s * FPS, r * FPS, res * FPS, cut, err))
            prev = g
        errs = np.array([r[5] for r in rows])
        bounds = boundaries(errs)
        a = np.array([r[:4] for r in rows if not r[4]])
        speed, zoom, roll, par = a.T
        moving = (speed > 0.01) | (np.abs(zoom) > 0.01) | (par > 0.01)
        out[slug] = {
            "pairs": len(rows),
            "translation_fw_per_s": {"median": round(float(np.median(speed)), 4), "p90": round(float(np.percentile(speed, 90)), 4)},
            "zoom_per_s": {"median_abs": round(float(np.median(np.abs(zoom))), 4), "p90_abs": round(float(np.percentile(np.abs(zoom), 90)), 4)},
            "roll_rad_per_s": {"median_abs": round(float(np.median(np.abs(roll))), 4)},
            "parallax_fw_per_s": {"median": round(float(np.median(par)), 4), "p90": round(float(np.percentile(par, 90)), 4)},
            "share_moving": round(float(moving.mean()), 3),
            "share_static": round(float(1 - moving.mean()), 3),
            "shot_boundaries_s": [round(b / FPS, 1) for b in bounds],
            "shots": len(bounds) + 1,
            "avg_shot_length_s": round(len(rows) / FPS / (len(bounds) + 1), 2),
            "median_shot_length_s": round(float(np.median(np.diff([0] + bounds + [len(rows)]))) / FPS, 2),
        }
        print(slug, out[slug])
    if only:
        return
    Path("style/camera_motion.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
