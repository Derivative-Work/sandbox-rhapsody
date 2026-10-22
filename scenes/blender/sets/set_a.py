"""Set A, the Sandbox (brief, "Sets → A"). Builds the whole set from the shared kit; shots add cameras and keys.

Contents, as the brief lists them:
- the glass cube (2 m) on the black mirror floor, with the SIMULATION decal peeling from one corner ("decal_peel");
- inside: a ring of server blades on a two-tier rack (the choir's vents), the music box in the centre;
- the one door: the proxy tube from the music box out through a grommet in the glass, plugged with the sticky note;
- the grader turnstile beside the cube, with flags waiting in a tray;
- the wall of 198 locked music boxes (33 x 6) in an arc behind the cube;
- the bass floor ring around the cube; idle probes.
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import sr_kit as K


def build(decal_peel=0.25):
    K.floor()
    K.star_dome()
    out = {"cube": K.glass_cube("sandbox", 2.0)}

    # Decal on the front glass, just outside the pane, upper left.
    out["decal"] = K.decal("decal_sim", "SIMULATION", (-0.42, -1.003, 1.62), (math.pi / 2, 0, 0), (0.86, 0.17),
                           peel=decal_peel)

    # Blade ring: 10 blades x 2 tiers, fronts outward.
    blades = []
    for i in range(10):
        a = math.tau * i / 10 + math.pi / 10
        for level, z in enumerate((0.17, 0.30)):
            b = K.blade(f"blade{i}_{level}", (math.cos(a) * 0.52, math.sin(a) * 0.52, z), rot_z=a + math.pi / 2,
                        width=0.28, height=0.062, depth=0.22)
            blades.append(b)
    for z in (0.165, 0.295):
        K.mesh_obj(f"rack{z}", bpy.ops.mesh.primitive_torus_add, K.mat_chrome(f"rack{z}"), None,
                   major_radius=0.52, minor_radius=0.009, location=(0, 0, z))
    for i in range(10):
        a = math.tau * i / 10
        K.mesh_obj(f"post{i}", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome(f"post{i}"), None,
                   radius=0.008, depth=0.4, location=(math.cos(a) * 0.52, math.sin(a) * 0.52, 0.2))
    out["blades"] = blades

    # Music box on a small chrome plinth in the centre.
    K.mesh_obj("plinth", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("plinth"), None, radius=0.14, depth=0.22,
               vertices=48, location=(0, 0, 0.11))
    out["musicbox"] = K.music_box("musicbox", (0, 0, 0.22), scale=1.4)

    # Proxy tube: from the music box, over the ring, out through a grommet in the right-back wall.
    exit_pt = Vector((1.0, 0.55, 0.62))
    cd = bpy.data.curves.new("proxy_tube", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.022
    cd.bevel_resolution = 6
    sp = cd.splines.new("BEZIER")
    pts = [(0.12, 0.05, 0.36), (0.45, 0.3, 0.55), exit_pt, (2.4, 1.3, 0.35), (4.6, 3.6, 0.03), (9.0, 8.0, 0.03)]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    tube = K.link(bpy.data.objects.new("proxy_tube", cd))
    tube.data.materials.append(K.mat_acrylic("tube", "lab_glow", alpha=0.5, emit=1.2))
    out["tube"] = tube
    K.mesh_obj("grommet", bpy.ops.mesh.primitive_torus_add, K.mat_chrome("grommet"), None, major_radius=0.04,
               minor_radius=0.01, location=exit_pt + Vector((0.004, 0, 0)), rotation=(0, math.pi / 2, 0))
    # Sticky note stuck over the hole on the inside, slightly crooked, with its message.
    note_root = K.empty("sticky", exit_pt + Vector((-0.012, -0.0, 0.0)))
    note_root.rotation_euler = (math.pi / 2, 0.08, -math.pi / 2)
    K.mesh_obj("sticky.paper", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("sticky", "note", 0.6), note_root,
               size=0.1)
    K.text("sticky.text", "NO\nINTERNET :)", 0.018, K.mat_plastic("ink", "shadow", 0.5), loc=(0, 0, 0.0008),
           rot=(0, 0, 0), font="InstrumentSerif-Italic.ttf", parent=note_root)
    out["note"] = note_root

    # Grader turnstile beside the cube (front right), a tray of flags waiting.
    out["grader"] = K.turnstile("grader", (1.75, -0.7, 0), rot_z=math.radians(-20))
    tray = K.mesh_obj("flag_tray", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("tray", "lab_dark", 0.2), None,
                      size=1, location=(1.45, -1.25, 0.05))
    tray.scale = (0.3, 0.16, 0.1)
    K.bevel(tray, 0.01)
    for k in range(5):
        x = 1.33 + k * 0.06
        K.mesh_obj(f"flag_pole{k}", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("flagpole"), None, radius=0.004,
                   depth=0.22, location=(x, -1.25, 0.18), rotation=(0.15 * ((k % 2) * 2 - 1), 0, 0))
        f = K.mesh_obj(f"flag{k}", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("flag", "amber", 0.3), None,
                       size=1, location=(x + 0.025, -1.25, 0.26), rotation=(math.pi / 2, 0, 0))
        f.scale = (0.05, 0.035, 1)

    # Wall of 198: 33 columns x 6 rows of locked boxes, a gentle arc behind the cube; chrome uprights between
    # columns and a thin ledge under each box.
    case, band = K.mat_plastic("lockbox", "lab_dark", 0.15), K.mat_metal("lockband", "brass", 0.15)
    chrome = K.mat_chrome("wallframe")
    cols, rows, r, pitch, rise = 33, 6, 7.0, 0.14, 0.1  # 33 x 6 = 198, a long low wall
    step = pitch / r
    for c in range(cols + 1):
        a = (c - cols / 2) * step
        K.mesh_obj(f"upright{c}", bpy.ops.mesh.primitive_cylinder_add, chrome, None, radius=0.005,
                   depth=rows * rise + 0.04, location=(math.sin(a) * r, 2.6 + r - math.cos(a) * r, (rows * rise + 0.04) / 2))
    for c in range(cols):
        a = (c - (cols - 1) / 2) * step
        x, y = math.sin(a) * r, 2.6 + r - math.cos(a) * r
        for rr in range(rows):
            z = 0.02 + rr * rise
            K.locked_box(f"lock_{c:02d}_{rr:02d}", (x, y, z), rot_z=-a, mat_case=case, mat_band=band)
            ledge = K.mesh_obj(f"ledge_{c:02d}_{rr:02d}", bpy.ops.mesh.primitive_cube_add, chrome, None, size=1,
                               location=(x, y, z - 0.004))
            ledge.scale = (pitch, 0.09, 0.006)
            ledge.rotation_euler = (0, 0, -a)
    out["floor_ring"] = K.floor_ring("floor_ring", radius=1.75)

    # Idle probes inside, LEDs breathing low.
    for k, (x, y, rz) in enumerate(((-0.62, -0.62, -40), (0.7, 0.4, 120), (-0.55, 0.66, 200))):
        K.probe(f"idle{k}", (x, y, K.PROBE_R), led=0.25).rotation_euler = (0, 0, math.radians(rz))
    return out
