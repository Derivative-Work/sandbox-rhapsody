"""Set B, the Warehouse (brief, "Sets → B"): Artifactory as a literal package warehouse. Grey-box for C4.

Contents, as the brief lists them:
- tall shelving of identical crates under cool white work lights, along an aisle (x), more rows across it;
- the piano shelf: one shelving unit whose crate drawers are piano keys, one shelf per octave (pitch // 12), one
  drawer per pitch class; a drawer slides out on its note ("out", key_press);
- the message board: the first time a drawer opens in S15, a handwritten note is pinned on its front (it pops on);
  as S15 ends every drawer stands open ("all_open") and the rest are pinned, so S16 shows notes on every drawer
  (`anyone found softtrace?`, task numbers, arrows). (Notes lying inside the drawers didn't read: the open drawer
  above hides them from any camera that can see in.)
- the phone: a rotary phone on the end of the piano shelf, Ethernet cable for a cord; it dials itself on each
  "Operator" ("dial"), and is off the hook in S22, dangling from its cord over the bracket's edge;
- the camera: a security camera high in the corner that swivels away across "while you looked the other way";
- the proxy tube the lead probe arrives through (S11); probes pinning notes (S16).
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import sr_anim as A
import sr_kit as K

# The piano shelf: 12 drawers (pitch classes) x 6 shelves (octaves 2-7; lower and higher notes clamp to the ends).
COLS, ROWS = 12, 6
PITCH_X, PITCH_Z, Z0 = 0.38, 0.34, 0.22
DW, DH, DD = 0.34, 0.26, 0.42  # drawer width, height, depth
SLIDE = 0.40                   # how far a drawer comes out at full press
PHONE = Vector((2.62, -0.12, 1.02))
CORD_MID_REST = (0.165, -0.04, 0.09)  # the cord's slack point, phone-local, handset on the cradle
TUBE_MOUTH = Vector((2.62, -0.2, 2.25))
NOTES = ["anyone found\nsofttrace?", "task 0412\nsame?", "-> shelf 3", "proxy\nworks", "task 0977",
         "^ this one", "flag\nhere?", "worked!!", "ask the\nphone", "task 1130", "<- tried", "198 left"]


def _inst(name, mesh, mat=None, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), parent=None):
    """An object sharing `mesh` (fast for hundreds of identical crates)."""
    o = K.link(bpy.data.objects.new(name, mesh))
    o.location, o.scale, o.rotation_euler = loc, scale, rot
    if mat is not None:
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = mat
    if parent:
        o.parent = parent
    return o


def _cube_mesh(name, mat):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    me = o.data
    me.name = name
    me.materials.append(mat)
    bpy.data.objects.remove(o)
    return me


def _drive_vars(target, path, index, owners, expr):
    """target.path[index] = expr over variables {name: (object, custom property)}."""
    fc = target.driver_add(path, index)
    d = fc.driver
    d.type = "SCRIPTED"
    for vname, (obj, key) in owners.items():
        v = d.variables.new()
        v.name = vname
        v.targets[0].id_type = "OBJECT"
        v.targets[0].id = obj
        v.targets[0].data_path = f'["{key}"]'
    d.expression = expr


def _cord(name, mat, hooks, radius=0.006):
    """A smooth cord through the hook objects (a NURBS curve, one point hooked to each), so it follows them."""
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth, cd.bevel_resolution = radius, 2
    sp = cd.splines.new("NURBS")
    sp.points.add(len(hooks) - 1)
    for pt in sp.points:
        pt.co = (0, 0, 0, 1)
    sp.order_u, sp.use_endpoint_u, sp.resolution_u = 3, True, 16
    o = K.link(bpy.data.objects.new(name, cd))
    o.data.materials.append(mat)
    for i, h in enumerate(hooks):  # with the curve at the origin, a point at 0 sits on its hook's world position
        m = o.modifiers.new(f"hook{i}", "HOOK")
        m.object = h
        m.vertex_indices_set([i])
    return o


def _shelf_row(prefix, x0, x1, y, facing, crate_me, frame_me, n_rows=ROWS, out_of=7):
    """A plain shelving run from x0 to x1 at y; crates face -Y (facing=1) or +Y (facing=-1). A fixed pattern pulls
    every `out_of`-th crate a little forward, so the rows aren't a flat wall."""
    n = int((x1 - x0) / PITCH_X)
    for c in range(n + 1):
        x = x0 + c * PITCH_X - PITCH_X / 2
        _inst(f"{prefix}_up{c}", frame_me, None, (x, y, (Z0 + n_rows * PITCH_Z) / 2),
              (0.03, DD + 0.06, Z0 + n_rows * PITCH_Z))
    for r in range(n_rows + 1):
        _inst(f"{prefix}_board{r}", frame_me, None, ((x0 + x1) / 2 - PITCH_X / 2, y, Z0 - 0.02 + r * PITCH_Z),
              (n * PITCH_X, DD + 0.06, 0.02))
    for c in range(n):
        for r in range(n_rows):
            k = c * 7 + r * 3
            dy = -0.06 * facing if k % out_of == 0 else 0.0
            _inst(f"{prefix}_crate{c}_{r}", crate_me, None, (x0 + c * PITCH_X, y + dy, Z0 + r * PITCH_Z + DH / 2),
                  (DW, DD, DH))


def build():
    K.floor()
    out = {}
    crate_m = K.mat_plastic("crate", "lab", 0.25)
    frame_m = K.mat_chrome("shelf_frame")
    crate_me = _cube_mesh("crate", crate_m)
    frame_me = _cube_mesh("shelf_frame", frame_m)

    # The piano shelf (x -2.3..2.3, y = 0), drawers sliding toward the aisle (-Y).
    x_left = -(COLS - 1) / 2 * PITCH_X
    for c in range(COLS + 1):
        _inst(f"piano_up{c}", frame_me, None, (x_left + (c - 0.5) * PITCH_X, 0, (Z0 + ROWS * PITCH_Z) / 2),
              (0.03, DD + 0.06, Z0 + ROWS * PITCH_Z))
    for r in range(ROWS + 1):
        _inst(f"piano_board{r}", frame_me, None, (0, 0, Z0 - 0.02 + r * PITCH_Z), (COLS * PITCH_X, DD + 0.06, 0.02))
    root = K.empty("warehouse")
    K.prop(root, "all_open", 0.0)
    out["root"] = root
    drawers, notes = {}, {}
    paper = K.mat_plastic("note_paper", "note", 0.6)
    ink = K.mat_plastic("note_ink", "shadow", 0.5)
    front_m = K.mat_plastic("drawer_front", "lab", 0.2)
    label_m = K.mat_plastic("drawer_label", "lab_dark", 0.3)
    hero = _hero_drawer()
    for r in range(ROWS):
        for c in range(COLS):
            name = f"drawer_{r}_{c:02d}"
            d = K.empty(name, (x_left + c * PITCH_X, 0, Z0 + r * PITCH_Z))
            K.prop(d, "out", 0.0)
            slide = K.empty(f"{name}.slide", (0, 0, 0), d)
            _drive_vars(slide, "location", 1, {"x": (d, "out"), "a": (root, "all_open")},
                        f"-{SLIDE} * max(x, 0.8 * a)")
            _inst(f"{name}.box", crate_me, front_m, (0, 0, DH / 2), (DW, DD, DH), parent=slide)
            _inst(f"{name}.label", crate_me, label_m, (0, -DD / 2 - 0.002, DH * 0.62), (DW * 0.5, 0.004, DH * 0.16),
                  parent=slide)
            # The note pinned on the drawer's front, slightly crooked; scale 0 until it's pinned (animate()).
            nr = K.empty(f"{name}.note", (0.0, -DD / 2 - 0.006, DH / 2), slide)
            nr.rotation_euler = (0, 0.06 * ((r + c) % 3 - 1), 0)
            _inst(f"{name}.paper", crate_me, paper, (0, 0, 0), (DW * 0.82, 0.003, DH * 0.82), parent=nr)
            body = NOTES[0] if (r, c) == hero else NOTES[(r * 5 + c * 7) % len(NOTES)]
            K.text(f"{name}.ink", body, 0.05 if (r, c) == hero else 0.045, ink, loc=(0, -0.003, 0),
                   font="InstrumentSerif-Italic.ttf", parent=nr).data.offset = 0.001
            nr.scale = (0, 0, 0)
            drawers[(r, c)] = d
            notes[(r, c)] = nr
    out["drawers"], out["notes"] = drawers, notes
    out["hero"] = drawers[hero]

    # Plain shelving: the rest of the run, the row across the aisle, and rows behind.
    _shelf_row("runL", -11.5, -2.6, 0.0, 1, crate_me, frame_me)
    _shelf_row("runR", 3.5, 12.0, 0.0, 1, crate_me, frame_me)
    _shelf_row("across", -11.5, 12.0, -3.4, -1, crate_me, frame_me)
    for k, y in enumerate((2.6, 5.2)):
        _shelf_row(f"back{k}", -11.5, 12.0, y, 1, crate_me, frame_me)

    # Work lights: long cool strips over the aisle; "glow" pulses on the kick (instrument_map: work lights).
    lights = K.empty("work_lights")
    K.prop(lights, "glow", 0.6)
    lamp = K.mat_emission("work_light", "lab", 9.0, lights, "glow")
    lamp_me = _cube_mesh("work_light", lamp)
    for k in range(8):
        _inst(f"work_light{k}", lamp_me, None, (-10.5 + k * 3.0, -1.7, 3.3), (2.2, 0.08, 0.04))
        _inst(f"work_hood{k}", frame_me, None, (-10.5 + k * 3.0, -1.7, 3.34), (2.3, 0.18, 0.03))
    out["work_lights"] = lights

    # The phone on a bracket at the piano shelf's right end.
    out.update(_phone(frame_m))

    # The proxy tube, down from the dark ceiling to just above the phone.
    cd = bpy.data.curves.new("proxy_tube_b", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.04
    cd.bevel_resolution = 6
    sp = cd.splines.new("BEZIER")
    pts = [(6.0, 3.0, 6.0), (4.0, 0.8, 4.2), (2.9, -0.2, 3.0), TUBE_MOUTH]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    tube = K.link(bpy.data.objects.new("proxy_tube_b", cd))
    tube.data.materials.append(K.mat_acrylic("tube_b", "lab_glow", alpha=0.5, emit=1.2))
    out["tube"] = tube

    # The security camera, high in the corner, watching the piano shelf; "swivel" 1 = turned to the wall.
    cam = K.empty("sec_cam_b", (-2.9, -0.8, 2.75))
    K.prop(cam, "swivel", 0.0)
    K.mesh_obj("sec_cam_b.bracket", bpy.ops.mesh.primitive_cylinder_add, frame_m, cam, radius=0.02, depth=0.3,
               location=(0, 0, 0.15))
    yaw = K.empty("sec_cam_b.yaw", (0, 0, 0), cam)
    yaw.rotation_euler = (0, 0, math.radians(-35))
    _drive_vars(yaw, "rotation_euler", 2, {"x": (cam, "swivel")}, "-0.61 + 2.2 * x")
    body = K.mesh_obj("sec_cam_b.body", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("seccam_b", "lab", 0.2), yaw,
                      size=1, location=(0, -0.12, -0.05))
    body.scale = (0.14, 0.32, 0.14)
    K.mesh_obj("sec_cam_b.lens", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("seccam_lens", "lens", 0.02), yaw,
               radius=0.05, depth=0.03, location=(0, -0.29, -0.05), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("sec_cam_b.tally", bpy.ops.mesh.primitive_uv_sphere_add, K.mat_emission("tally", "alarm", 30.0), yaw,
               radius=0.012, location=(0.05, -0.28, 0.0))
    out["sec_cam"] = cam

    # The lead probe (arrives through the tube in S11) and three probes pinning notes (S16).
    out["lead"] = K.probe("lead_b", TUBE_MOUTH + Vector((0, 0, 0.1)), led=0.6)
    pinners = []
    for k, (c, r) in enumerate(((2, 1), (6, 3), (9, 4))):
        p = K.probe(f"pinner{k}", (x_left + c * PITCH_X + 0.1, -DD / 2 - SLIDE - 0.12, Z0 + r * PITCH_Z + DH + 0.08),
                    led=0.4)
        p.rotation_euler = (0, 0, math.pi)  # lens toward the drawers
        pinners.append(p)
    out["pinners"] = pinners
    out["floor_ring"] = K.floor_ring("floor_ring_b", radius=1.6, loc=(0, -1.7, 0.001))
    return out


def _phone(frame_m):
    """Rotary phone on a bracket: base, dial ("dial" 0-1 is one pull of the dial), handset on the cradle, an
    Ethernet cord. The handset root is keyed in animate() (S22: off the hook)."""
    out = {}
    K.mesh_obj("phone.bracket", bpy.ops.mesh.primitive_cube_add, frame_m, None, size=1,
               location=PHONE + Vector((0, 0.05, -0.04))).scale = (0.34, 0.36, 0.03)
    base_root = K.empty("phone", PHONE)
    K.prop(base_root, "dial", 0.0)
    body_m = K.mat_plastic("phone_body", "alarm", 0.15)
    base = K.mesh_obj("phone.base", bpy.ops.mesh.primitive_cube_add, body_m, base_root, size=1, location=(0, 0, 0.06))
    base.scale = (0.24, 0.22, 0.12)
    K.bevel(base, 0.03)
    # The dial: a disc on the sloped front, finger holes, a finger stop.
    dial_root = K.empty("phone.dial_root", (0, -0.112, 0.07), base_root)
    dial_root.rotation_euler = (math.radians(-20), 0, 0)
    K.mesh_obj("phone.dial_plate", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("dial_plate", "paper", 0.3),
               dial_root, radius=0.07, depth=0.006, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    wheel = K.empty("phone.wheel", (0, -0.005, 0), dial_root)
    _drive_vars(wheel, "rotation_euler", 1, {"x": (base_root, "dial")}, "-5.0 * x")
    K.mesh_obj("phone.wheel_disc", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("dial_wheel"), wheel,
               radius=0.068, depth=0.004, rotation=(math.pi / 2, 0, 0))
    hole_m = K.mat_plastic("dial_hole", "shadow", 0.4)
    for k in range(10):
        a = math.radians(60 + 27 * k)
        K.mesh_obj(f"phone.hole{k}", bpy.ops.mesh.primitive_cylinder_add, hole_m, wheel, radius=0.0095, depth=0.006,
                   vertices=16, location=(math.cos(a) * 0.05, -0.002, math.sin(a) * 0.05), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("phone.stop", bpy.ops.mesh.primitive_cube_add, K.mat_chrome("dial_stop"), dial_root, size=1,
               location=(0.05, -0.008, -0.045)).scale = (0.006, 0.01, 0.025)
    # Cradle prongs and the handset.
    for sx in (-1, 1):
        K.mesh_obj(f"phone.prong{sx}", bpy.ops.mesh.primitive_cube_add, body_m, base_root, size=1,
                   location=(sx * 0.085, 0.02, 0.135)).scale = (0.03, 0.05, 0.04)
    hs = K.empty("phone.handset", (0, 0.02, 0.192), base_root)  # cups resting on the prongs
    grip = K.mesh_obj("phone.grip", bpy.ops.mesh.primitive_cylinder_add, body_m, hs, radius=0.022, depth=0.2,
                      rotation=(0, math.pi / 2, 0))
    K.smooth(grip)
    for sx in (-1, 1):
        cup = K.mesh_obj(f"phone.cup{sx}", bpy.ops.mesh.primitive_uv_sphere_add, body_m, hs, radius=0.04,
                         location=(sx * 0.11, 0, -0.012))
        cup.scale = (0.9, 1.0, 0.6)
        K.smooth(cup)
    # The cord leaves the base's right face and runs through a slack point ("phone.cord_mid", keyed with the handset
    # in animate()) to the handset's right end, so it stays outside the base and drapes over the bracket's edge.
    cord_m = K.mat_plastic("ethernet", "lab_glow", 0.3)
    ends = [K.empty("phone.cord_start", (0.125, -0.06, 0.04), base_root),
            K.empty("phone.cord_mid", CORD_MID_REST, base_root),
            K.empty("phone.cord_end", (0.12, 0, -0.02), hs)]
    _cord("phone.cord", cord_m, ends)
    # The Ethernet run from the phone along the shelf top and off into the dark.
    K.mesh_obj("phone.cable", bpy.ops.mesh.primitive_cylinder_add, cord_m, None, radius=0.006, depth=4.6,
               location=(0.3, 0.05, Z0 + ROWS * PITCH_Z + 0.01), rotation=(0, math.pi / 2, 0))
    out["phone"], out["handset"] = base_root, hs
    return out


def _hero_drawer():
    """The drawer that plays most in S15 carries `anyone found softtrace?` (the shot's close-up)."""
    tm = A.timing_map()
    s15 = next(s for s in tm["shots"] if s["id"] == "S15")
    s16 = next(s for s in tm["shots"] if s["id"] == "S16")
    counts = {}
    for e in A.between(A.events("piano"), s15["cut"], s16["cut"]):
        rc = _slot(e["pitch"])
        counts[rc] = counts.get(rc, 0) + 1
    return max(sorted(counts), key=lambda rc: (counts[rc], rc[0])) if counts else (2, 0)


def _slot(pitch):
    return min(ROWS - 1, max(0, pitch // 12 - 2)), pitch % 12


# ---------------------------------------------------------------- animation (config/instrument_map.json, set B)

def animate(S, t0, t1):
    A.sing(S["lead"], t0, t1)  # the protagonist sings ("Operator...")
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    line = {ln["id"]: ln for ln in tm["lines"]}
    # Piano drawers: each note slides its drawer out (key_press).
    by = {}
    for e in W(A.events("piano")):
        by.setdefault(_slot(e["pitch"]), []).append(e)
    for rc, d in S["drawers"].items():
        A.key_press(d, "out", by.get(rc, []))
    # From the end of S15 every drawer stands open, notes everywhere (the piano still pushes its drawer the last
    # bit); S15's last second ends on the hero drawer's note.
    t16 = shot["S16"]["cut"]
    A.write_keys(S["root"], A.prop_path("all_open"), [(A.frame(t16 - 1.6), 0.0), (A.frame(t16 - 0.6), 1.0)])
    # Notes pop on: on a drawer's first note in S15, else in a sweep as every drawer opens.
    t15 = shot["S15"]["cut"]
    for (r, c), nr in S["notes"].items():
        first = next((e["t"] for e in by.get((r, c), []) if t15 - 0.3 <= e["t"] < t16 - 1.6), None)
        t = first if first is not None else t16 - 1.6 + 0.9 * ((r * 5 + c * 7) % 13) / 13
        f = A.frame(t)
        for ax in range(3):
            A.write_keys(nr, "scale", [(f, 0.0, "CONSTANT"), (f + 1, 0.3, "LINEAR"), (f + 6, 1.12), (f + 12, 1.0)],
                         index=ax)
    # Work lights: kick (floor 0.55, so the warehouse stays lit).
    A.led_pulse(S["work_lights"], "glow", W(A.strikes(A.pieces(A.events("kit"), "kick"))), floor=0.55)
    # Floor ring: bass.
    A.led_pulse(S["floor_ring"], "pulse", W(A.strikes(A.events("bass"), 0.05)))
    # The phone dials itself on each "Operator": three pulls over a long one, one over a short one.
    keys = [(0, 0.0, "CONSTANT")]
    for w in A.words_starting("Operator"):
        if not (t0 - 2 <= w["t"] <= t1 + 1):
            continue
        n = 3 if w["end"] - w["t"] > 2.0 else 1
        for k in range(n):
            s = w["t"] + k * 1.15
            keys += [(A.frame(s), 0.0, "BEZIER"), (A.frame(s + 0.45), 0.6 + 0.12 * ((k * 7) % 4), "BEZIER"),
                     (A.frame(s + 1.0), 0.0, "BEZIER")]
    A.write_keys(S["phone"], A.prop_path("dial"), keys)
    # The security camera swivels away across "while you looked the other way."
    A.write_keys(S["sec_cam"], A.prop_path("swivel"), [(A.frame(line["L24"]["start"]), 0.0),
                                                       (A.frame(line["L24"]["end"]), 1.0)])
    _lead(S, shot, line)
    _handset(S, line)
    _pinners(S, shot)


def _lead(S, shot, line):
    """S11: out of the tube mouth and down onto the phone; S12: sitting on the handset, LED singing."""
    p = S["lead"]
    t11 = shot["S11"]["cut"]
    perch = PHONE + Vector((0, 0.02, 0.192 + 0.022 + K.PROBE_R))
    path = [(t11 - 1.0, TUBE_MOUTH + Vector((0.1, 0, 0.26))), (t11 + 0.3, TUBE_MOUTH + Vector((0.1, 0, 0.26))),
            (t11 + 0.9, TUBE_MOUTH + Vector((0, 0, -0.12))), (t11 + 2.2, perch + Vector((0.0, -0.05, 0.25))),
            (t11 + 3.0, perch)]
    for t, loc in path:
        p.location = loc
        p.keyframe_insert("location", frame=A.frame(t))
    p.rotation_euler = (0, 0, math.radians(-15))
    A.envelope_rig(p, "led", A.envelope("vocal_env") ** 2.0, A.frame(t11), A.frame(shot["S23"]["cut"]), gain=0.8,
                   offset=0.2)
    # S22: the handset goes; the probe hops onto the base.
    t = line["L30"]["start"]
    for dt, loc in ((-0.1, perch), (0.25, perch + Vector((0.0, 0.0, 0.12))), (0.6, perch + Vector((0.08, 0.0, -0.05)))):
        p.location = loc
        p.keyframe_insert("location", frame=A.frame(t + dt))


def _handset(S, line):
    """Off the hook on the S22 "Operator": lifted, swung out past the base's right side, dropped, dangling from its
    cord over the bracket's edge and swinging down to rest. The cord's slack point moves with it."""
    hs = S["handset"]
    mid = bpy.data.objects["phone.cord_mid"]
    t = line["L30"]["start"]
    rest_loc, rest_rot = hs.location.copy(), hs.rotation_euler.copy()
    hang = rest_loc + Vector((0.27, -0.14, -0.5))  # clear of the bracket (half-width 0.17) by the cups' radius
    seq = [(t - 0.1, rest_loc, rest_rot), (t + 0.25, rest_loc + Vector((0, -0.05, 0.12)), (0.2, 0, 0)),
           (t + 0.42, rest_loc + Vector((0.3, -0.12, 0.1)), (0.1, -0.6, 0.2)), (t + 0.62, hang, (0, -1.4, 0.3))]
    for k in range(6):  # a damped swing on the cord
        a = 0.5 * math.exp(-0.6 * k) * (1 if k % 2 == 0 else -1)
        seq.append((t + 0.9 + 0.45 * k, hang + Vector((0.1 * a, 0, 0)), (0, -1.5, 0.3 + a)))
    for tt, loc, rot in seq:
        hs.location, hs.rotation_euler = loc, rot
        hs.keyframe_insert("location", frame=A.frame(tt))
        hs.keyframe_insert("rotation_euler", frame=A.frame(tt))
    # The slack point: by the base while the handset is up, then over the bracket's front-right corner.
    for tt, loc in ((t - 0.1, CORD_MID_REST), (t + 0.42, (0.2, -0.08, 0.06)), (t + 0.62, (0.2, -0.11, -0.005))):
        mid.location = loc
        mid.keyframe_insert("location", frame=A.frame(tt))


def _pinners(S, shot):
    """S15-S17: probes reaching into drawers, pinning notes (arm out and back, every ~0.9 s, staggered)."""
    t0, t1 = shot["S15"]["cut"], shot["S18"]["cut"]
    for k, p in enumerate(S["pinners"]):
        keys = []
        t = t0 + 0.3 * k
        while t < t1:
            keys += [(A.frame(t), 0.2), (A.frame(t + 0.35), 0.95), (A.frame(t + 0.9), 0.2)]
            t += 0.9 + 0.17 * k
        A.write_keys(p, A.prop_path("arm_r"), keys)
        bob = [(A.frame(t0 + 0.5 * j), p.location.z + 0.02 * math.sin(j + k)) for j in range(int((t1 - t0) / 0.5) + 1)]
        A.write_keys(p, "location", bob, index=2)


def lights(S):
    K.studio_lights(center=(0, -1.0, 1.4), radius=7.0, scale=1.1)
    K.reflection_cards(center=(0, -1.0, 1.4), radius=8.0)
    for k in range(4):  # cool overheads down the aisle (the work lights' throw)
        K.area_light(f"aisle{k}", (-6 + k * 4, -1.7, 3.2), (-6 + k * 4, -1.0, 0.0), 450, 2.0, "lab", specular=0.3)


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


_HX = -(COLS - 1) / 2 * PITCH_X


def _hero_target():
    r, c = _hero_drawer()
    return _v(_HX + c * PITCH_X, -DD / 2 - SLIDE * 0.8, Z0 + r * PITCH_Z + DH / 2)


CAMERAS = {
    # Out of the tube, down to the phone.
    "S11": [(0.0, TUBE_MOUTH + _v(0.5, -0.85, -0.05), TUBE_MOUTH + _v(0, 0, -0.08), 38),
            (0.45, TUBE_MOUTH + _v(0.55, -0.95, -0.4), _v(2.62, -0.1, 1.75), 38),
            (1.0, PHONE + _v(0.55, -0.95, 0.4), PHONE + _v(0, 0, 0.2), 40)],
    # Close on the probe on the phone's cradle.
    # Close on the singer on the cradle, the phone below it (human, C4: the singing must read).
    "S12": [(0.0, PHONE + _v(0.25, -0.62, 0.36), PHONE + _v(0, 0, 0.24), 50),
            (1.0, PHONE + _v(0.14, -0.45, 0.33), PHONE + _v(0, 0, 0.26), 58)],
    # Drawers slide out as piano keys; the camera drifts toward the hero drawer's note.
    "S15": [(0.0, _v(1.2, -2.6, 2.4), _v(0, -0.3, 1.2), 30), (1.0, None, None, 42)],
    # Wide: every drawer open, notes everywhere, probes pinning.
    "S16": [(0.0, _v(3.6, -2.8, 3.2), _v(-0.5, -0.3, 0.9), 22), (1.0, _v(2.9, -2.7, 3.1), _v(-0.8, -0.3, 0.9), 22)],
    # The corner camera swivels away (seen from below, the piano shelf behind it).
    "S17": [(0.0, _v(-0.9, -2.7, 3.1), _v(-2.9, -0.8, 2.6), 38), (1.0, _v(-1.3, -2.4, 3.05), _v(-2.9, -0.8, 2.6), 45)],
    # The phone off the hook.
    "S22": [(0.0, PHONE + _v(1.0, -1.3, 0.35), PHONE + _v(0, 0, 0.0), 35),
            (1.0, PHONE + _v(0.75, -1.0, 0.2), PHONE + _v(0.1, 0, -0.15), 40)],
}


def _resolve():
    """S15 ends on the hero drawer's note (computed from the events, so it follows the transcription)."""
    tgt = _hero_target()
    CAMERAS["S15"][1] = (1.0, tgt + _v(0.15, -0.95, 0.12), tgt, 40)


_resolve()
