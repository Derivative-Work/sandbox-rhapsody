"""C4 animatic plates: build one set, key its rigs from the events, and render every shot that set owns (the brief's
Set column, first set listed) at its final timing, low-res, one PNG sequence per shot.

A shot's camera comes from the set module's CAMERAS[shot] = [(u, eye, target, lens), ...] with u the fraction of the
shot (0 = cut, 1 = next cut), or a list of such moves for cuts inside the shot; shots without one get a slow push-in on the set's centre, flagged in the run's report.
Plates run one frame past the shot's end on each side, so the edit can dissolve.

Usage: blender -b --factory-startup --python scenes/blender/animatic.py -- SET [shot ...] [--size 640x360]
       [--samples 8] [--step 1] [--out DIR]
  -> renders/animatic/plates/<shot>/f_<frame>.png  (frame numbers are the 60 fps timeline's)
"""
import importlib
import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE / "lib"), str(HERE / "sets")]
import sr_anim as A  # noqa: E402
import sr_kit as K  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
opts = {"--size": "640x360", "--samples": "8", "--step": "1", "--out": str(ROOT / "renders" / "animatic" / "plates")}
pos = []
i = 0
while i < len(args):
    if args[i] in opts:
        opts[args[i]] = args[i + 1]
        i += 2
    else:
        pos.append(args[i])
        i += 1
SET, only = pos[0].upper(), set(pos[1:])
w, h = (int(v) for v in opts["--size"].split("x"))


def brief_sets():
    """Shot id -> its set letter (first set named in the brief's Set column)."""
    out = {}
    for line in (ROOT / "docs" / "brief.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and re.fullmatch(r"S\d+[a-z]?", cells[0]):
            m = re.match(r"([A-I])\b", cells[3])
            if m:
                out[cells[0]] = m.group(1)
    return out


tm = A.timing_map()
shots = [s for s in tm["shots"] if s["cut"] is not None]  # S67 waits on the fact card's length
end_of = {s["id"]: (shots[k + 1]["cut"] if k + 1 < len(shots) else tm["duration_s"]) for k, s in enumerate(shots)}
owner = brief_sets()
mine = [s for s in shots if owner.get(s["id"]) == SET and (not only or s["id"] in only)]
assert mine, f"no shots for set {SET}"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, w, h, int(opts["--samples"]))
mod = importlib.import_module(f"set_{SET.lower()}")
S = mod.build()
if hasattr(mod, "lights"):  # a set larger or darker than the sandbox lights itself
    mod.lights(S)
else:
    K.studio_lights(center=(0, 0, 0.8), radius=6.0)
    K.reflection_cards(center=(0, 0, 0.8))
t0, t1 = min(s["cut"] for s in mine), max(end_of[s["id"]] for s in mine)
mod.animate(S, t0, t1)
K.bloom(scene)
K.rebind_drivers()
K.refresh()
scene.frame_set(A.frame(t0))
bad = K.invalid_drivers()

report = [f"invalid drivers after rebind: {len(bad)} {bad[:5]}"]
for s in mine:
    sid, a, b = s["id"], s["cut"], end_of[s["id"]]
    keys = getattr(mod, "CAMERAS", {}).get(sid)
    if keys is None:
        report.append(f"{sid}: no camera in set_{SET.lower()}.CAMERAS, default push-in")
        keys = [(0.0, Vector((4, -6, 2)), Vector((0, 0, 0.6)), 35), (1.0, Vector((3, -4.5, 1.6)), Vector((0, 0, 0.6)), 35)]
    # A shot is one camera move, or a list of moves with hard cuts between them (each starts at its first key's u);
    # cuts switch cameras through timeline markers.
    scene.timeline_markers.clear()
    segments = keys if isinstance(keys[0], list) else [keys]
    for j, seg in enumerate(segments):
        cam = K.camera_move(f"cam_{sid}" + (f".{j}" if len(segments) > 1 else ""),
                            [(a + u * (b - a), e, t, l) for u, e, t, l in seg])
        if len(segments) > 1:
            m = scene.timeline_markers.new(f"{sid}.{j}", frame=A.frame(a + seg[0][0] * (b - a)) if j else 0)
            m.camera = cam
    scene.camera = bpy.data.objects[f"cam_{sid}" + (".0" if len(segments) > 1 else "")]
    scene.frame_start, scene.frame_end = A.frame(a) - 1, A.frame(b) + 1
    scene.frame_step = int(opts["--step"])
    out = Path(opts["--out"]) / sid
    out.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out / "f_")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
    (out / "plate.json").write_text(json.dumps({"shot": sid, "set": SET, "cut_s": a, "end_s": b,
                                                "frames": [scene.frame_start, scene.frame_end],
                                                "size": [w, h], "samples": int(opts["--samples"]),
                                                "step": scene.frame_step}) + "\n")
print("ANIMATIC", SET, [s["id"] for s in mine], report)
