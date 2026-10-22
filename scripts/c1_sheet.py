"""C1 review sheet: the middle 5 s still of each Animusic reference (top) above the two set-A test frames (bottom).

The middle still is chosen mechanically, not hand-picked. The sheet is a review aid only: it holds other creators'
frames, so it stays in renders/ (not published).
Usage: .venv/bin/python -I scripts/c1_sheet.py <close.png> <wide.png> <out.jpg>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, COLS, PAD, LABEL = 384, 216, 5, 8, 26
MONO = "assets/fonts/JetBrainsMono[wght].ttf"


def main():
    close, wide, out = sys.argv[1:4]
    font = ImageFont.truetype(MONO, 17)
    pieces = sorted(p for p in Path("reference/stills").iterdir() if p.is_dir())
    rows = (len(pieces) + COLS - 1) // COLS
    ref_h = rows * (H + LABEL) + PAD
    tw = COLS * W + (COLS - 1) * PAD
    th = (tw - PAD) // 2 * 9 // 16
    sheet = Image.new("RGB", (tw + 2 * PAD, ref_h + LABEL + th + 2 * PAD), "#0a0814")
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(pieces):
        stills = sorted((p / "every5s").glob("*.jpg"))
        s = stills[len(stills) // 2]
        x, y = PAD + (i % COLS) * (W + PAD), PAD + (i // COLS) * (H + LABEL)
        d.text((x, y + 3), f"{p.name} @ {(int(s.stem) - 1) * 5}s", fill="#9a8fb0", font=font)
        im = Image.open(s).convert("RGB")
        im.thumbnail((W, H))
        sheet.paste(im, (x + (W - im.width) // 2, y + LABEL + (H - im.height) // 2))
    d.text((PAD, ref_h + 3), "Sandbox Rhapsody, set A test frames (close, wide); 4K Eevee, 64 samples, seed-free",
           fill="#efe8da", font=font)
    for j, f in enumerate((close, wide)):
        im = Image.open(f).convert("RGB").resize(((tw - PAD) // 2, th), Image.LANCZOS)
        sheet.paste(im, (PAD + j * ((tw - PAD) // 2 + PAD), ref_h + LABEL))
    sheet.save(out, quality=90)


if __name__ == "__main__":
    main()
