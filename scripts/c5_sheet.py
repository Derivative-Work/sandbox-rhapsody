"""C5 contact sheet: one set's anchor stills (scenes/blender/animatic.py --anchors), each captioned with its shot,
anchor (the sung line) and the brief's visual, three to a row.

Usage: .venv/bin/python -I scripts/c5_sheet.py SET  ->  renders/c5/set_<SET>/contact_sheet.jpg
"""
import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, COLS, PAD, CAP = 960, 540, 3, 16, 96
FONT = "assets/fonts/Inter[opsz,wght].ttf"


def brief_rows():
    rows = {}
    for line in Path("docs/brief.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and re.fullmatch(r"S\d+[a-z]?", cells[0]):
            rows[cells[0]] = dict(zip(["id", "section", "anchor", "set", "visual", "gag", "pipeline"], cells))
    return rows


def main():
    s = sys.argv[1].upper()
    src = Path(f"renders/c5/set_{s}/anchors")
    stills = sorted(src.glob("S*.png"), key=lambda p: (int(re.match(r"S(\d+)", p.stem).group(1)), p.stem))
    rows = brief_rows()
    n = len(stills)
    nr = (n + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * W + (COLS + 1) * PAD, nr * (H + CAP + PAD) + PAD), "#0a0814")
    d = ImageDraw.Draw(sheet)
    bold, small = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 19)
    for i, p in enumerate(stills):
        x, y = PAD + (i % COLS) * (W + PAD), PAD + (i // COLS) * (H + CAP + PAD)
        sheet.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
        r = rows.get(p.stem, {})
        d.text((x, y + H + 6), f"{p.stem}  ·  {r.get('anchor', '')}", font=bold, fill="#efe8da")
        for j, ln in enumerate(textwrap.wrap(r.get("visual", ""), 92)[:2]):
            d.text((x, y + H + 40 + 24 * j), ln, font=small, fill="#9a8fb0")
    out = src.parent / "contact_sheet.jpg"
    sheet.save(out, quality=90)
    print("wrote", out, n, "stills")


if __name__ == "__main__":
    main()
