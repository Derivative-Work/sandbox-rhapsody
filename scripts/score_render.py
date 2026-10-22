"""Engrave cache/score/score.musicxml with Verovio, one system per page, and patch what the MusicXML import gets
wrong. Mid-score key changes that every pitched part shares become score-wide key signatures in Verovio's MEI, and
would be drawn on the drum staff too; each one gets an explicit no-key staffDef for the drum staff.

Used by scripts/c3_score_preview.py; run alone to write page PNGs for a look:
  .venv/bin/python -I scripts/score_render.py [page ...]  ->  cache/score/page_<n>.png
"""
import re
import sys
from pathlib import Path

import cairosvg
import verovio

OPTS = {"pageWidth": 3600, "pageHeight": 1500, "scale": 45, "breaks": "encoded", "adjustPageHeight": True,
        "header": "none", "footer": "none", "svgViewBox": True, "lyricSize": 5.0}
DRUM_STAFF = 6


def toolkit():
    tk = verovio.toolkit()
    tk.setOptions(OPTS)
    tk.loadFile("cache/score/score.musicxml")
    mei = tk.getMEI()
    # A scoreDef that only carries a keySig (a mid-score key change): add the drum staff's own empty key.
    mei = re.sub(r'(<scoreDef xml:id="[^"]+">\s*<keySig [^>]*/>)',
                 lambda m: m.group(1) + f'<staffGrp><staffDef n="{DRUM_STAFF}"><keySig sig="0" /></staffDef></staffGrp>',
                 mei)
    tk.loadData(mei)
    return tk


if __name__ == "__main__":
    tk = toolkit()
    print("pages", tk.getPageCount())
    for pg in [int(a) for a in sys.argv[1:]] or [1]:
        cairosvg.svg2png(bytestring=tk.renderToSVG(pg).encode(), write_to=str(Path(f"cache/score/page_{pg}.png")),
                         output_width=1800, background_color="white")
