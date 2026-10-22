"""C1 test frames: set A in this video's look (brief, checkpoint C1: "the cube, a blade and a probe").

Builds the whole set (scenes/blender/sets/set_a.py), poses it as a still of the choir mid-phrase, and frames it
"close" (the lead probe on a singing blade, music box and ring behind, through the glass) or "wide" (the whole
sandbox: cube and decal, the grader, the tube and its note, the wall of 198). Deterministic (no random calls).

Usage: blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- <out.png> [width height samples [close|wide]]
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE / "sets")]
import set_a  # noqa: E402
import sr_kit as K  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
out_path = args[0]
w, h, samples = (int(a) for a in args[1:4]) if len(args) >= 4 else (1920, 1080, 64)
framing = args[4] if len(args) >= 5 else "close"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, w, h, samples)
S = set_a.build(decal_peel=0.6)

# The choir mid-phrase: vents in a wave around the ring; the blade under the lead probe fully open.
for k, b in enumerate(S["blades"]):
    b["vent"] = 0.5 + 0.5 * math.sin(k * 0.9)
    b["led"] = 0.7
front = bpy.data.objects["blade7_1"]  # front centre, upper tier
front["vent"] = 1.0
S["musicbox"]["drum"] = 0.13
S["floor_ring"]["pulse"] = 0.6
S["grader"]["spin"] = 0.08

# The lead probe sits on the front blade, lens toward us, LED lit, one arm reaching for the glass.
probe_at = front.location + Vector((-0.03, 0, 0.062 + K.PROBE_R))
p = S["lead"]
p.location, p["led"] = probe_at, 1.0
p.rotation_euler = (0, 0, math.radians(-22))
p["arm_l"], p["arm_r"] = 0.2, 0.9

K.studio_lights(center=(0, 0, 0.8), radius=6.0)
K.reflection_cards(center=(0, 0, 0.8))

if framing == "wide":  # the whole sandbox, low three-quarter from front right
    eye = Vector((3.3, -4.6, 1.45))
    K.camera("cam", eye, Vector((0.35, 0.4, 0.7)), lens=30, dof_fstop=11.0, focus=(eye - Vector((0, 0, 0.8))).length)
else:  # outside the front glass, on the probe and its blade
    K.reflection_probe(center=probe_at, radius=0.2)
    eye = probe_at + Vector((-0.42, -0.82, 0.0))
    K.camera("cam", eye, probe_at + Vector((0.14, 0.2, -0.07)), lens=45, dof_fstop=3.2,
             focus=(eye - probe_at).length)

K.bloom(scene)
K.refresh()
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
