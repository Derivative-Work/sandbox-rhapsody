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
import numpy as np
from mathutils import Vector

import sr_anim as A
import sr_kit as K


def build(decal_peel=0.25):
    K.floor()
    K.star_dome()
    out = {"cube": K.glass_cube("sandbox", 2.0)}

    # Decal on the front glass, just outside the pane, upper left.
    out["decal"] = K.decal("decal_sim", "SIMULATION", (-0.28, -1.003, 1.58), (math.pi / 2, 0, 0), (1.3, 0.27),
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

    # Wall-of-198 column lights: one emissive strip per column under its boxes, driven by "glow_<c>" on a root.
    cols_root = K.empty("wall_lights")
    for c in range(cols):
        a = (c - (cols - 1) / 2) * step
        K.prop(cols_root, f"glow_{c}", 0.0)
        strip = K.mesh_obj(f"wall_light_{c}", bpy.ops.mesh.primitive_cube_add,
                           K.mat_emission(f"wall_light_{c}", "lab_glow", 12.0, cols_root, f"glow_{c}"), None, size=1,
                           location=(math.sin(a) * r, 2.6 + r - math.cos(a) * r - 0.05, 0.012))
        strip.scale = (pitch * 0.8, 0.012, 0.012)
        strip.rotation_euler = (0, 0, -a)
    out["wall_lights"] = cols_root
    out["wall_cols"] = cols

    # STOP socket on the cube's base (S21): an empty socket, no button.
    sock = K.empty("stop_socket", (0.55, -1.008, 0.12))
    sock.rotation_euler = (math.pi / 2, 0, 0)
    K.mesh_obj("stop_socket.plate", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("socket", "lab_dark", 0.2), sock,
               size=1, location=(0, 0, 0)).scale = (0.14, 0.14, 0.01)
    K.mesh_obj("stop_socket.hole", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("hole", "shadow", 0.6), sock,
               radius=0.035, depth=0.012, location=(0, 0.01, 0.004))
    K.text("stop_socket.label", "STOP", 0.03, K.mat_plastic("socket_ink", "paper", 0.4), loc=(0, -0.05, 0.007),
           rot=(0, 0, 0), parent=sock)
    # Guardrails lying unbolted beside the cube, a wrench, a tag (S23).
    rail_m = K.mat_metal("guardrail", "brass", 0.25)
    for k, (x, y, rz) in enumerate(((-1.55, -0.9, 0.2), (-1.45, -1.25, -0.15))):
        g = K.mesh_obj(f"guardrail{k}", bpy.ops.mesh.primitive_cube_add, rail_m, None, size=1, location=(x, y, 0.02),
                       rotation=(0, 0, rz))
        g.scale = (0.9, 0.05, 0.04)
        K.bevel(g, 0.01)
    w = K.mesh_obj("wrench", bpy.ops.mesh.primitive_cube_add, K.mat_chrome("wrench"), None, size=1,
                   location=(-1.2, -1.45, 0.008), rotation=(0, 0, 0.7))
    w.scale = (0.22, 0.03, 0.012)
    tag = K.empty("guardrail_tag", (-1.75, -1.05, 0.05))
    tag.rotation_euler = (math.radians(70), 0, 0.25)
    K.mesh_obj("tag.card", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("tag", "paper", 0.5), tag, size=1
               ).scale = (0.62, 0.13, 1)
    K.text("tag.text", "removed for evaluation", 0.048, K.mat_plastic("tag_ink", "shadow", 0.5), loc=(0, 0, 0.002),
           rot=(0, 0, 0), parent=tag)
    # Beyond the glass (S06): faint machines in the dark, and a security camera on a pole, facing away.
    faint = K.mat_plastic("faint", "horizon", 0.4)
    for k in range(9):
        a = math.radians(-60 + 15 * k)
        d = 9 + (k % 3) * 2.5
        m = K.mesh_obj(f"faint{k}", bpy.ops.mesh.primitive_cube_add, faint, None, size=1,
                       location=(math.sin(a) * d, math.cos(a) * d + 2, 0.6 + (k % 2) * 0.5))
        m.scale = (0.8 + (k % 4) * 0.3, 0.6, 1.2 + (k % 3) * 0.6)
    pole = K.mesh_obj("cam_pole", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("pole"), None, radius=0.03,
                      depth=2.6, location=(-2.6, 1.8, 1.3))
    camhead = K.mesh_obj("sec_cam", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("seccam", "lab", 0.2), None,
                         size=1, location=(-2.6, 1.95, 2.55))
    camhead.scale = (0.12, 0.32, 0.12)
    out["sec_cam"] = camhead

    # The lead probe, parked on the front upper blade; scripted moves in animate().
    front = bpy.data.objects["blade7_1"]
    out["lead"] = K.probe("lead", front.location + Vector((0.0, 0, 0.062 + K.PROBE_R)), led=0.6)
    out["front_blade"] = front
    out["exit_pt"] = exit_pt

    # Idle probes inside, LEDs breathing low.
    for k, (x, y, rz) in enumerate(((-0.62, -0.62, -40), (0.7, 0.4, 120), (-0.55, 0.66, 200))):
        K.probe(f"idle{k}", (x, y, K.PROBE_R), led=0.25).rotation_euler = (0, 0, math.radians(rz))
    return out


# ---------------------------------------------------------------- animation (config/instrument_map.json, set A)

BAND_IN = 44.5  # the band (and the backing vocals, bass) enter


def animate(S, t0, t1):
    """Key every set-A rig for the window [t0, t1] (s) from the events (sr_anim)."""
    # The protagonist sings: the lead probe's voice from the lead's words; the music box plays every piano note.
    A.sing(S["lead"], t0, t1)
    A.comb(S["musicbox"], A.between(A.events("piano"), t0 - 1, t1 + 1))
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    f0, f1 = A.frame(t0 - 1), A.frame(t1 + 1)
    vocal = A.envelope("vocal_env") ** 2.0
    backing = np.where(np.arange(len(vocal)) < A.frame(BAND_IN), 0.5 * vocal, A.envelope("backing_env") ** 2.0)
    for b in S["blades"]:
        tier = int(b.name.split("_")[1])
        A.envelope_rig(b, "vent", vocal if tier == 1 else backing, f0, f1)
    # Blade status LEDs: each sung note lights one blade (pitch picks which).
    notes = W(A.events("vocal_notes"))
    by_blade = {}
    for e in notes:
        by_blade.setdefault(e["pitch"] % len(S["blades"]), []).append(e)
    for i, b in enumerate(S["blades"]):
        A.led_pulse(b, "led", by_blade.get(i, []))
    piano = A.events("piano")
    A.stepper(S["musicbox"], "drum", W(A.top_line(A.pitch_range(piano, 60))), pre=4, settle=10, overshoot=0.0)
    kit = A.events("kit")
    A.stepper(S["grader"], "spin", W(A.strikes(A.pieces(kit, "snare"))))
    A.bell(S["grader"], "bell", W(A.strikes(A.pieces(kit, "crash"))))
    # Wall of 198: the left hand walks along it, one column per note.
    lh = W(A.strikes(A.pitch_range(piano, 0, 60), 0.05))
    cols = {}
    for k, e in enumerate(lh):
        cols.setdefault(k % S["wall_cols"], []).append(e)
    for c in range(S["wall_cols"]):
        A.led_pulse(S["wall_lights"], f"glow_{c}", cols.get(c, []))
    # Floor ring: bass; the piano's left hand before the bass enters.
    ring = [e for e in W(A.strikes(A.pitch_range(piano, 0, 48), 0.05)) if e["t"] < BAND_IN]
    ring += [e for e in W(A.strikes(A.events("bass"), 0.05)) if e["t"] >= BAND_IN]
    A.led_pulse(S["floor_ring"], "pulse", ring)
    # Tube pellets: strings until the band enters, then the synth (one per strike, at most ~5 per second).
    pel = [e for e in W(A.strikes(A.events("strings"), 0.2)) if e["t"] < BAND_IN]
    pel += [e for e in W(A.strikes(A.events("synth"), 0.2)) if e["t"] >= BAND_IN]
    pmat = K.mat_emission("pellet", "amber", 25.0)
    A.pellets(S["tube"], pel, speed=1.2, make_pellet=lambda i: K.pellet_mesh(f"pellet{i}", pmat, r=0.012))
    # The lead probe's LED sings.
    A.envelope_rig(S["lead"], "led", vocal, f0, f1, gain=0.8, offset=0.2)
    probe_moves(S)


def probe_moves(S):
    """Scripted (not note-driven) moves of the lead probe, timed to its shots' anchors: to the glass for "Crack open
    a socket" (S05), into the proxy tube at "so I'll dig" (S10)."""
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    p = S["lead"]
    home = p.location.copy()
    glass = Vector((0.12, -0.955, 0.62))
    t5, t6 = shot["S05"]["anchor"], shot["S06"]["cut"]
    t10, t11 = shot["S10"]["cut"], shot["S11"]["cut"]
    for t, loc in ((t5 - 0.6, home), (t5 + 0.4, glass), (t6 + 1.0, glass), (t6 + 2.5, home)):
        p.location = loc
        p.keyframe_insert("location", frame=A.frame(t))
    # S10: the probe peels the note off; it flutters to the floor (two swings), then the probe goes up to the tube's
    # mouth, then along it (Follow Path, offset keyed), hidden once inside the tube's far end.
    mouth = S["exit_pt"] + Vector((-0.08, 0, 0))
    p.location = home
    p.keyframe_insert("location", frame=A.frame(t10))
    p.location = mouth
    p.keyframe_insert("location", frame=A.frame(t10 + 1.2))
    n = S["note"]
    n0, r0 = n.location.copy(), n.rotation_euler.copy()
    for dt, dloc, rot in ((0.9, (0, 0, 0), r0), (1.3, (-0.1, -0.04, -0.2), (1.2, 0.5, -1.2)),
                          (1.8, (-0.22, 0.05, -0.42), (0.3, -0.4, -1.9)), (2.2, (-0.3, 0.0, -0.6), (0, 0, -2.2))):
        n.location, n.rotation_euler = n0 + Vector(dloc), rot
        n.keyframe_insert("location", frame=A.frame(t10 + dt))
        n.keyframe_insert("rotation_euler", frame=A.frame(t10 + dt))
    c = p.constraints.new("FOLLOW_PATH")
    c.target, c.use_fixed_location, c.use_curve_follow = S["tube"], True, True
    A.write_keys(p, f'constraints["{c.name}"].influence', [(0, 0.0, "CONSTANT"), (A.frame(t10 + 1.2), 0.0, "LINEAR"),
                                                          (A.frame(t10 + 1.5), 1.0, "LINEAR")])
    A.write_keys(p, f'constraints["{c.name}"].offset_factor', [(A.frame(t10 + 1.5), 0.32, "LINEAR"),
                                                              (A.frame(t11), 1.0, "LINEAR")])


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


CAMERAS = {
    "S01": [(0.0, _v(9, -16, 4.5), _v(0, 0, 1.0), 40), (1.0, _v(5.2, -9.0, 2.6), _v(0, 0, 0.9), 40)],
    "S02": [(0.0, _v(4.0, -4.2, 1.7), _v(0, 0, 0.8), 35), (0.5, _v(5.4, -1.2, 1.5), _v(0, 0, 0.8), 35),
            (1.0, _v(4.6, 2.6, 1.6), _v(0, 0, 0.8), 35)],
    # Inside the cube, over the blade ring: the sticky note faces in.
    "S03": [(0.0, _v(0.05, 0.3, 0.85), _v(1.0, 0.55, 0.62), 35), (1.0, _v(0.7, 0.5, 0.66), _v(1.0, 0.55, 0.62), 40)],
    "S04": [(0.0, _v(0.55, 0.25, 0.6), _v(1.0, 0.55, 0.62), 28), (1.0, _v(0.78, 0.45, 0.62), _v(1.0, 0.56, 0.62), 28)],
    "S05": [(0.0, _v(0.5, -1.9, 0.75), _v(0.12, -0.9, 0.6), 50), (1.0, _v(0.3, -1.45, 0.66), _v(0.12, -0.95, 0.62), 60)],
    "S06": [(0.0, _v(0.4, -1.6, 0.6), _v(0.0, 3.0, 1.0), 28), (1.0, _v(0.6, -3.6, 4.2), _v(0.0, 6.0, 0.8), 28)],
    "S07": [(0.0, _v(3.2, -2.2, 1.1), _v(1.75, -0.7, 0.6), 40), (1.0, _v(2.6, -1.5, 0.9), _v(1.75, -0.7, 0.6), 45)],
    "S08": [(0.0, _v(2.0, -1.25, 0.8), _v(1.72, -0.78, 0.6), 40), (1.0, _v(1.95, -1.1, 0.75), _v(1.72, -0.78, 0.58), 50)],
    "S09": [(0.0, _v(-2.6, 1.0, 0.55), _v(-2.2, 2.7, 0.35), 32), (1.0, _v(2.6, 1.0, 0.55), _v(2.2, 2.7, 0.35), 32)],
    "S10": [(0.0, _v(1.9, -0.6, 1.0), _v(1.0, 0.55, 0.62), 35), (0.45, _v(1.5, 0.3, 0.7), _v(1.0, 0.55, 0.62), 35),
            (0.7, _v(1.6, 0.85, 0.6), _v(2.4, 1.3, 0.4), 24), (1.0, _v(3.8, 2.6, 0.25), _v(5.6, 4.6, 0.04), 24)],
    "S20": [(0.0, _v(3.0, -5.0, 1.8), _v(0, 0, 1.0), 35), (1.0, _v(28.0, -48.0, 20.0), _v(0, 0, 1.0), 35)],
    "S21": [(0.0, _v(1.6, -2.6, 0.5), _v(0.55, -1.0, 0.15), 40), (1.0, _v(1.0, -1.7, 0.3), _v(0.55, -1.0, 0.13), 50)],
    "S23": [(0.0, _v(-0.6, -3.4, 0.9), _v(-1.45, -1.1, 0.05), 35), (1.0, _v(-1.55, -2.0, 0.55), _v(-1.7, -1.05, 0.08), 40)],
}
