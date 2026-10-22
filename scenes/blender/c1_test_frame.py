"""C1 test frame: set A in this video's look (brief, checkpoint C1: "the cube, a blade and a probe").

The glass cube on the black mirror floor, a ring of server blades inside (one in the foreground with its vents half
open), the lead probe at the glass with its amber LED lit, the proxy tube leaving through the wall. Deterministic
(no random calls). Colours, materials and lights from config/look.json.

Usage: blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- <out.png> [width height samples [close|wide]]
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import sr_kit as K  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
out_path = args[0]
w, h, samples = (int(a) for a in args[1:4]) if len(args) >= 4 else (1920, 1080, 64)
framing = args[4] if len(args) >= 5 else "close"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, w, h, samples)

K.floor()
K.star_dome()
cube = K.glass_cube("sandbox", 2.0)

# Ring of eight blades around the centre, stacked two high on chrome posts, fronts facing inward.
for i in range(8):
    a = math.tau * i / 8 + math.pi / 8
    r = 0.5
    for level, z in enumerate((0.17, 0.30)):
        b = K.blade(f"blade{i}_{level}", (math.cos(a) * r, math.sin(a) * r, z), rot_z=a + math.pi / 2,
                    width=0.3, height=0.062, depth=0.22)
        b["vent"] = 0.35 + 0.65 * ((i + level) % 3) / 2  # a still of the choir mid-phrase
        b["led"] = 0.6
# The blades sit on a two-tier chrome ring rack.
for z in (0.165, 0.295):
    ring = K.mesh_obj(f"rack{z}", bpy.ops.mesh.primitive_torus_add, K.mat_chrome(f"rack{z}"), None,
                      major_radius=0.5, minor_radius=0.009, location=(0, 0, z))
for i in range(8):
    a = math.tau * i / 8
    K.mesh_obj(f"post{i}", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome(f"post{i}"), None,
               radius=0.008, depth=0.4, location=(math.cos(a) * 0.5, math.sin(a) * 0.5, 0.2))

# Centre: a small music box with a brass comb (set A).
box = K.mesh_obj("musicbox", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("musicbox", "lab_dark", 0.15), None,
                 size=1, location=(0, 0, 0.06))
box.scale = (0.16, 0.1, 0.12)
K.bevel(box, 0.008)
for k in range(12):
    tooth = K.mesh_obj(f"comb{k}", bpy.ops.mesh.primitive_cube_add, K.mat_metal(f"comb", "brass", 0.18), None,
                       size=1, location=(-0.055 + k * 0.01, 0.0, 0.125))
    tooth.scale = (0.006, 0.07 - k * 0.003, 0.002)
drum = K.mesh_obj("musicbox_drum", bpy.ops.mesh.primitive_cylinder_add, K.mat_metal("drum", "brass", 0.12), None,
                  radius=0.018, depth=0.13, location=(0, 0.045, 0.14), rotation=(0, math.pi / 2, 0))

# The one door: a fiber tube from the music box out through the back-left wall, plugged with a sticky note.
cd = bpy.data.curves.new("proxy_tube", "CURVE")
cd.dimensions = "3D"
cd.bevel_depth = 0.022
cd.bevel_resolution = 6
sp = cd.splines.new("BEZIER")
pts = [(0.08, 0.06, 0.1), (0.5, 0.55, 0.12), (1.0, 0.86, 0.55), (2.6, 1.6, 0.4), (5.0, 3.5, 0.05)]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts):
    bp.co = p
    bp.handle_left_type = bp.handle_right_type = "AUTO"
tube = K.link(bpy.data.objects.new("proxy_tube", cd))
tube.data.materials.append(K.mat_acrylic("tube", "lab_glow", alpha=0.45, emit=0.6))
note = K.mesh_obj("sticky", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("sticky", "note", 0.5), None, size=0.07,
                  location=(0.985, 0.8, 0.53), rotation=(math.pi / 2, 0.05, math.pi / 2 + 0.12))

# The lead probe sits on the nearest upper blade, lens toward us, LED lit, one arm reaching for the glass.
front = bpy.data.objects["blade6_1"]
probe_at = front.location + Vector((0, 0, 0.062 + K.PROBE_R))
p = K.probe("lead", probe_at, led=1.0)
p.rotation_euler = (0, 0, math.radians(25))
p["arm_l"], p["arm_r"] = 0.2, 0.9
front["vent"] = 1.0  # the blade under the probe is mid-note
K.probe("idle", (-0.35, -0.2, 0.06 + K.PROBE_R), led=0.25).rotation_euler = (0, 0, math.radians(-40))

K.studio_lights(center=(0, 0, 0.8), radius=6.0)
K.reflection_cards(center=(0, 0, 0.8))

# Camera: outside the front glass, low and three-quarter, the probe on the right third looking out at us; the blade
# ring, music box and the tube's exit behind it. Shallow DOF on the probe.
eye = probe_at + Vector((0.5, -0.78, -0.02))
cam = K.camera("cam", eye, probe_at + Vector((-0.12, 0.2, -0.07)), lens=45, dof_fstop=3.2,
               focus=(eye - probe_at).length)
K.reflection_probe(center=probe_at, radius=0.2)
if framing == "wide":  # the whole sandbox on the mirror floor, low three-quarter
    eye = Vector((2.9, -4.3, 1.35))
    cam = K.camera("cam", eye, Vector((0.1, 0.0, 0.75)), lens=35, dof_fstop=8.0, focus=(eye - Vector((0, 0, 0.8))).length)

K.refresh()
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
