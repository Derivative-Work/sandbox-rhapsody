"""Step 7 check: drive set-A rigs from the real events over a window and verify every contact lands on its event's
frame; optionally render the window (low-res) with the master audio for a look.

Usage: blender -b --factory-startup --python scenes/blender/anim_test.py -- [t0 t1 [render_dir]]
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE / "sets")]
import sr_anim as A  # noqa: E402
import sr_kit as K  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
t0, t1 = (float(args[0]), float(args[1])) if len(args) >= 2 else (44.0, 54.0)
render_dir = args[2] if len(args) >= 3 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, 640, 360, 8)
scene.frame_start, scene.frame_end = A.frame(t0), A.frame(t1)
K.floor()
K.studio_lights(center=(0, 0, 0.4), radius=4)
K.reflection_cards(center=(0, 0, 0.4), radius=4)

blade = K.blade("blade", (-0.75, 0.35, 0.0), width=0.3, height=0.062, depth=0.22)
box = K.music_box("musicbox", (-0.3, 0.0, 0.0), scale=2.2)
grader = K.turnstile("grader", (0.95, 0.55, 0), rot_z=math.radians(-20))
kick_pad = K.mallet_pad("kick_pad", (0.15, -0.05, 0.0), rot_z=math.radians(-15), pad_role="lab_dark", pad_r=0.16,
                        arm_len=0.40, glow_role="alarm")
snare_pad = K.mallet_pad("snare_pad", (0.55, 0.15, 0.0), rot_z=math.radians(-30), pad_role="lab_dark", pad_r=0.11,
                         glow_role="amber")
probe = K.probe("lead", (-0.75, 0.35, 0.062 + K.PROBE_R), led=0.2)
ring = K.floor_ring("ring", radius=1.4)

# Tube for pellets: from the back left into the music box.
cd = bpy.data.curves.new("tube", "CURVE")
cd.dimensions = "3D"
cd.bevel_depth = 0.02
sp = cd.splines.new("BEZIER")
pts = [(-1.8, 1.4, 0.7), (-1.0, 1.0, 0.8), (-0.5, 0.4, 0.5), (-0.3, 0.05, 0.3)]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts):
    bp.co = p
    bp.handle_left_type = bp.handle_right_type = "AUTO"
tube = K.link(bpy.data.objects.new("tube", cd))
tube.data.materials.append(K.mat_acrylic("tube", "lab_glow", alpha=0.3, emit=0.3))
pmat = K.mat_emission("pellet", "amber", 25.0)


def make_pellet(i):
    return K.pellet_mesh(f"pellet{i}", pmat, r=0.015)


# Drive the rigs (config/instrument_map.json, set A + global).
W = lambda evs: A.between(evs, t0, t1)  # noqa: E731
A.envelope_rig(blade, "vent", A.envelope("vocal_env") ** 2.0, A.frame(t0), A.frame(t1))  # squared: decisive opening
piano_top = W(A.top_line(A.pitch_range(A.events("piano"), 60)))
A.stepper(box, "drum", piano_top, pre=4, settle=10, overshoot=0.0)  # a twelfth of a turn per note (driver below)
box_drv = bpy.data.objects["musicbox.axle"].animation_data.drivers[0].driver
box_drv.expression = "0.5236 * x"
snare = W(A.strikes(A.pieces(A.events("kit"), "snare")))
crash = W(A.strikes(A.pieces(A.events("kit"), "crash")))
kick = W(A.strikes(A.pieces(A.events("kit"), "kick")))
A.stepper(grader, "spin", snare)
A.bell(grader, "bell", crash)
A.striker(kick_pad, "strike", kick)
A.hit_flash(kick_pad, "flash", kick)
A.striker(snare_pad, "strike", snare)
A.hit_flash(snare_pad, "flash", snare)
A.led_pulse(probe, "led", kick)
bass = W(A.events("bass"))
A.led_pulse(ring, "pulse", bass)
synth = W(A.strikes(A.events("synth"), 0.2))
pel = A.pellets(tube, synth, speed=1.2, make_pellet=make_pellet)
hammer = kick_pad

# Verify contacts land on event frames.
def value_at(owner, prop, f):
    fc = A._fcurve(owner, A.prop_path(prop))
    return fc.evaluate(f)

bad = []
for k, e in enumerate(snare):
    f = A.frame(e["t"])
    if abs(value_at(grader, "spin", f) - (k + 1.15)) > 1e-3:
        bad.append(("stepper", e["t"], value_at(grader, "spin", f)))
for e in kick:
    f = A.frame(e["t"])
    if abs(value_at(hammer, "strike", f) - 1.0) > 1e-3:
        bad.append(("striker", e["t"], value_at(hammer, "strike", f)))
    if value_at(probe, "led", f) < 0.6 - 1e-3:
        bad.append(("led", e["t"], value_at(probe, "led", f)))
for i, (p, e) in enumerate(zip(pel, synth)):
    c = p.constraints[-1]
    fc = A._fcurve(p, f'constraints["{c.name}"].offset_factor')
    if abs(fc.evaluate(A.frame(e["t"])) - 1.0) > 1e-3:
        bad.append(("pellet", e["t"], fc.evaluate(A.frame(e["t"]))))
print(f"CHECK snare strikes {len(snare)}, kicks {len(kick)}, crash {len(crash)}, piano notes {len(piano_top)}, "
      f"bass {len(bass)}, pellets {len(pel)}; contacts off their frame: {len(bad)} {bad[:5]}")

if render_dir:
    K.camera("cam", (0.55, -1.55, 0.62), (0.05, 0.2, 0.18), lens=28)
    K.bloom(scene)
    scene.render.filepath = str(Path(render_dir) / "f_")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
