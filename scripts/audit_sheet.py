"""Contact sheet for one set's prop audit (scenes/blender/prop_audit.py): each prop's still, captioned with its name,
copies, size, and its bare boxes and flat-shaded meshes.

Usage: .venv/bin/python -I scripts/audit_sheet.py SET  ->  renders/audit/set_<SET>/sheet.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, COLS, PAD, CAP = 480, 360, 5, 10, 46
FONT = "assets/fonts/Inter[opsz,wght].ttf"

src = Path(f"renders/audit/set_{sys.argv[1].upper()}")
rows = [r.split("\t") for r in (src / "audit.tsv").read_text().splitlines()[1:]]
rows = [r for r in rows if (src / f"{r[0]}.png").exists()]
nr = (len(rows) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * W + (COLS + 1) * PAD, nr * (H + CAP + PAD) + PAD), "#0a0814")
d = ImageDraw.Draw(sheet)
f1, f2 = ImageFont.truetype(FONT, 18), ImageFont.truetype(FONT, 14)
for i, (name, count, size, meshes, bare, flat, note) in enumerate(rows):
    x, y = PAD + (i % COLS) * (W + PAD), PAD + (i // COLS) * (H + CAP + PAD)
    sheet.paste(Image.open(src / f"{name}.png").convert("RGB").resize((W, H)), (x, y))
    d.text((x, y + H + 4), f"{name}" + (f"  ×{count}" if count != "1" else ""), font=f1, fill="#efe8da")
    d.text((x, y + H + 26), f"{size} m · {meshes} meshes · {bare} bare boxes · {flat} flat", font=f2, fill="#9a8fb0")
sheet.save(src / "sheet.jpg", quality=88)
print("wrote", src / "sheet.jpg", len(rows))
