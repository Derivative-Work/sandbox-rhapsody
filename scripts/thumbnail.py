"""The video's thumbnail (brief: the S41 frame, the crowd spelling GO and the lone I DECLINE sign in the stands).

The frame is S41's clean plate (no captions or HUD; the POV lens applied) at the second GO (song 185.5 s, frame
11130), cropped to the letters and the sign. The letters are 22 x 8 LEDs on tiers set wider apart than the seats, so
at thumbnail size they fall apart into rows of dots: the lit LED cores (luminance > 0.9; the unlit shells peak at
0.6-0.8) get a warm glow stretched across the tier gap, and the unlit hall is darkened. Two versions: clean, and with
the title in Neuropol (the title card's face).

Usage: .venv/bin/python -I scripts/thumbnail.py  ->  deliverables/thumbnail.jpg, deliverables/thumbnail_title.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import assemble as A  # noqa: E402

FRAME = 11130                       # S41, the second GO (185.43-185.81 s), I DECLINE still raised
CROP = (840, 520, 2280)             # x0, y0, width at 3840x2160; height is width * 9/16
SIGN = (1030, 1230, 2560, 3010)     # y0, y1, x0, x1 of the I DECLINE sign: white, but not part of the letters
WARM = np.array([1.0, 0.58, 0.18], np.float32)


def main():
    a = A.Plates(3840, 2160, 3840, 2160).picture(FRAME).astype(np.float32) / 255
    x0, y0, w = CROP
    a = a[y0:y0 + round(w * 9 / 16), x0:x0 + w]
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lit = (lum > 0.9).astype(np.float32)
    sign = np.zeros_like(lit)
    sign[SIGN[0] - y0:SIGN[1] - y0, SIGN[2] - x0:SIGN[3] - x0] = 1
    lit[sign > 0] = 0
    sign = cv2.GaussianBlur(sign, (0, 0), 8)
    halo = cv2.GaussianBlur(cv2.dilate(lit, np.ones((15, 15), np.uint8)), (0, 0), 18)
    base = a * (0.38 + 0.62 * np.clip(halo * 4 + sign, 0, 1))[..., None]
    glow = (1.6 * cv2.GaussianBlur(lit, (0, 0), sigmaX=26, sigmaY=40)
            + 0.8 * cv2.GaussianBlur(lit, (0, 0), sigmaX=70, sigmaY=90))
    glow = np.clip(glow * 9, 0, 1)[..., None] * WARM
    out = 1 - (1 - base) * (1 - 0.75 * glow)  # screen
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((1920, 1080), Image.LANCZOS)
    img.save(ROOT / "deliverables/thumbnail.jpg", quality=92)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(ROOT / "assets/fonts/Neuropol.otf"), 104)
    txt = "SANDBOX RHAPSODY"
    x, y = (1920 - d.textlength(txt, font=f)) / 2, 905
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).text((x, y + 5), txt, font=f, fill=230)
    img.paste((0, 0, 0), mask=sh.filter(ImageFilter.GaussianBlur(14)))
    d.text((x, y), txt, font=f, fill=(245, 240, 230))
    img.save(ROOT / "deliverables/thumbnail_title.jpg", quality=92)
    print("deliverables/thumbnail.jpg, deliverables/thumbnail_title.jpg (1920x1080)")


if __name__ == "__main__":
    main()
