"""Edit effects the brief gives to the edit ("Blender + ffmpeg" rows), applied frame by frame to the cut's pictures, so
the animatic and the final assembly share them:

- S22, rewind glitch: on "back" (L31, "please don't roll me back."), the shot runs backward two beats in the space of
  one, with a tape-rewind look (colour split, tearing bands, scanlines), then snaps to real time and plays on. The
  picture rewinds; the music never does, so sync holds either side of it.
- S65, CRT collapse: just after the SIGTERM, as the LED flashes out, the picture squashes to a bright horizontal line,
  the line shrinks to a dot, and the dot fades to black.

Use: `source_frame(sid, f)` gives the plate frame to show at timeline frame f; `apply(sid, f, img)` treats the
picture (a PIL RGB image) and returns it.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

FPS = 60
TM = json.loads(Path("timing/timing_map.json").read_text())
BEATS = np.array(TM["beats"])


def _frame(t):
    return int(round(t * FPS))


def _word(line_id, prefix):
    li = next(x for x in TM["lines"] if x["id"] == line_id)
    return next(w["start"] for w in li["words"] if w["w"].lower().startswith(prefix))


def _beat_len(t):
    k = int(np.searchsorted(BEATS, t))
    return float(BEATS[k] - BEATS[k - 1])


REWIND_AT = _word("L31", "back")
REWIND_BEAT = _beat_len(REWIND_AT)
REW0, REW1 = _frame(REWIND_AT), _frame(REWIND_AT + REWIND_BEAT)  # timeline frames the rewind plays over
REW_SPAN = 2 * REWIND_BEAT  # how far back the picture goes
SIGTERM = _frame(TM["events"]["sigterm"])
CRT_DELAY = 12  # after the LED's last flash (set I keys it at +4 frames), so the dot lands as the whine ends (+27)
SQUASH, SHRINK, FADE = 7, 6, 18  # frames for each stage of the collapse


def source_frame(sid, f):
    if sid == "S22" and REW0 <= f < REW1:
        u = (f - REW0) / (REW1 - REW0)
        return _frame(REWIND_AT - REW_SPAN * u)
    return f


def apply(sid, f, img):
    if sid == "S22" and REW0 <= f < REW1 + 2:
        return _rewind_look(img, f, snap=f >= REW1)
    if f >= SIGTERM + CRT_DELAY:
        return _crt(img, f - SIGTERM - CRT_DELAY)
    return img


def _rewind_look(img, f, snap=False):
    a = np.asarray(img).astype(np.int16)
    h, w, _ = a.shape
    rng = np.random.default_rng(f)  # deterministic per frame
    out = a.copy()
    out[:, :, 0] = np.roll(a[:, :, 0], 4, axis=1)  # colour split
    out[:, :, 2] = np.roll(a[:, :, 2], -4, axis=1)
    for _ in range(2 if snap else 4):  # tearing bands, shoved sideways
        y = int(rng.integers(0, h - 12))
        bh = int(rng.integers(4, 24 if snap else 14))
        out[y:y + bh] = np.roll(out[y:y + bh], int(rng.integers(-40, 40)), axis=1)
    if snap:  # the tracking bar as it locks back to real time
        y = int(h * (0.85 if f % 2 else 0.4))
        out[y:y + 10] = 235
    out[::3] = out[::3] * 0.7  # scanlines
    grey = out.mean(axis=2, keepdims=True)
    out = 0.75 * out + 0.25 * grey + 10  # washed out, lifted blacks
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def _crt(img, k):
    """k frames after the SIGTERM: squash to a line, shrink to a dot, fade."""
    w, h = img.size
    out = Image.new("RGB", (w, h))
    if k < SQUASH:
        u = (k + 1) / SQUASH
        hh = max(2, int(h * (1 - u) ** 2))
        line = img.resize((w, hh))
        boost = np.asarray(line).astype(np.float32) * (1 + 2.5 * u) + 60 * u
        out.paste(Image.fromarray(np.clip(boost, 0, 255).astype(np.uint8)), (0, (h - hh) // 2))
        return out
    k -= SQUASH
    a = np.zeros((h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    if k < SHRINK:  # the line shrinks toward the centre
        half = max(3, int(w / 2 * (1 - (k + 1) / SHRINK) ** 1.5))
        m = (np.abs(xx - w / 2) < half) & (np.abs(yy - h / 2) < 1.5)
        a[m] = 250
    elif k < SHRINK + FADE:  # the dot glows and fades
        g = 1 - (k - SHRINK) / FADE
        r2 = (xx - w / 2) ** 2 + (yy - h / 2) ** 2
        a += (250 * g * np.exp(-r2 / (2 * (2.0 + 2 * g) ** 2)))[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
