"""Static, overlap-free instances of the variable fonts, for Blender's text objects.

Blender fills glyph outlines even-odd, and the variable fonts build glyphs from overlapping contours, so wherever two
overlap the fill cancels: the A lost its crossbar (human, C4 v5: "'A's throughout are missing the horizontal line").
fontTools' instancer pins the axes and merges the overlaps (skia-pathops). Both fonts are OFL 1.1 with no Reserved
Font Name; the instances are renamed "... Flat" all the same. PIL (burn-ins, previews) draws the variable fonts
correctly and keeps them.

Usage: .venv/bin/python -I scripts/flat_fonts.py  ->  assets/fonts/Inter-Medium-flat.ttf,
       assets/fonts/JetBrainsMono-SemiBold-flat.ttf
"""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import OverlapMode, instantiateVariableFont

FONTS = [("Inter[opsz,wght].ttf", {"wght": 500, "opsz": 32}, "Inter-Medium-flat.ttf", "Inter Medium Flat"),
         ("JetBrainsMono[wght].ttf", {"wght": 600}, "JetBrainsMono-SemiBold-flat.ttf", "JetBrains Mono SemiBold Flat")]

for src, axes, out, family in FONTS:
    inst = instantiateVariableFont(TTFont(f"assets/fonts/{src}"), axes, overlap=OverlapMode.REMOVE)
    for rec in inst["name"].names:
        if rec.nameID in (1, 4, 16):
            rec.string = family
    inst.recalcTimestamp = False  # keep the source's timestamp, so the output is the same on every run
    inst.save(f"assets/fonts/{out}")
    print("wrote", out)
