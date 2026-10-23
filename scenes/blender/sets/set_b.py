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
from mathutils import Matrix, Vector

import sr_anim as A
import sr_kit as K

# The piano shelf: 12 drawers (pitch classes) x 6 shelves (octaves 2-7; lower and higher notes clamp to the ends).
COLS, ROWS = 12, 6
PITCH_X, PITCH_Z, Z0 = 0.38, 0.34, 0.22
DW, DH, DD = 0.34, 0.26, 0.42  # drawer width, height, depth
SLIDE = 0.40                   # how far a drawer comes out at full press
PHONE = Vector((2.62, -0.12, 1.02))
CORD_MID_REST = (0.19, 0.03, 0.05)  # the cord's slack point, phone-local, handset on the cradle
PHONE_BLEND = K.ROOT / "assets" / "models" / "rotary_phone.blend"  # scripts/phone_prep.py
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


def _coil_cord(name, mat, hooks, turns=70, coil_r=0.007, wire_r=0.0018):
    """A coiled phone cord through the hook objects: a NURBS path with one point hooked to each (it follows them),
    and a coil mesh bent along it that stretches to the path's length, so it lengthens like a real coiled cord."""
    cd = bpy.data.curves.new(f"{name}.path", "CURVE")
    cd.dimensions = "3D"
    cd.use_path, cd.use_stretch, cd.use_deform_bounds = True, True, True
    sp = cd.splines.new("NURBS")
    sp.points.add(len(hooks) - 1)
    for i, pt in enumerate(sp.points):  # inner points weighted, so the cord hugs them (the drape over the bracket)
        pt.co = (0, 0, 0, 3.0 if 0 < i < len(hooks) - 1 else 1.0)
    sp.order_u, sp.use_endpoint_u, sp.resolution_u = 3, True, 32
    path = K.link(bpy.data.objects.new(f"{name}.path", cd))  # no bevel: the path itself never renders
    for i, h in enumerate(hooks):  # with the path at the origin, a point at 0 sits on its hook's world position
        m = path.modifiers.new(f"hook{i}", "HOOK")
        m.object = h
        m.vertex_indices_set([i])
    hd = bpy.data.curves.new(f"{name}.helix", "CURVE")
    hd.dimensions = "3D"
    hd.bevel_depth, hd.bevel_resolution = wire_r, 2
    hp = hd.splines.new("POLY")
    n = turns * 16
    hp.points.add(n)
    for i, pt in enumerate(hp.points):
        a = i / n * turns * 2 * math.pi
        pt.co = (i / n, coil_r * math.cos(a), coil_r * math.sin(a), 1)
    coil = K.link(bpy.data.objects.new(name, hd))
    coil.data.materials.append(mat)
    # As a mesh: bending the bevelled curve itself threw a stray sheet off the coil's start.
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = coil
    coil.select_set(True)
    bpy.ops.object.convert(target="MESH")
    coil = bpy.context.view_layer.objects.active
    m = coil.modifiers.new("along", "CURVE")
    m.object, m.deform_axis = path, "POS_X"
    return coil


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
    ink = K.mat_ink("note_ink", "shadow")
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
        for sx in (-1, 1):  # hung from the dark on two wires
            _inst(f"work_wire{k}{sx}", frame_me, None, (-10.5 + k * 3.0 + sx * 0.95, -1.7, 4.36), (0.008, 0.008, 2.0))
    out["work_lights"] = lights

    # The phone on a bracket at the piano shelf's right end.
    out.update(_phone())

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

    # The security camera, high in the corner. At "swivel" 0 its lens (local -Y) aims at the piano shelf's centre;
    # at 1 it has swung about 140 degrees away from the shelf (it used to start facing away and swing toward it,
    # human, C4 v7).
    # The kit's CCTV camera (C5): its pan head sits where the grey-box one turned (-2.9, -0.8, 2.75), hung from a
    # wall plate on a chrome bracket; it tilts down toward the drawers.
    cam, yaw, tilt = K.security_camera("sec_cam_b", (-2.9, -0.8, 2.75 + 0.17 * 1.15), scale=1.15)
    K.prop(cam, "swivel", 0.0)
    K.mesh_obj("sec_cam_b.bracket", bpy.ops.mesh.primitive_cylinder_add, frame_m, cam, radius=0.022, depth=0.3,
               location=(0, 0, 0.15))
    K.mesh_obj("sec_cam_b.plate", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("seccam_plate", "lab_dark", 0.3),
               cam, size=1, location=(0, 0, 0.31)).scale = (0.16, 0.16, 0.025)
    _drive_vars(yaw, "rotation_euler", 2, {"x": (cam, "swivel")}, "1.84 - 2.4 * x")
    tilt.rotation_euler = (0.2, 0, 0)  # lens (local -Y) pitched a little down toward the shelf
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


def _phone():
    """Rotary phone on a bracket, from a CC BY model (scripts/phone_prep.py: "Rotary Phone" by lobstor; human, C4 v4:
    "see if you can find a CC asset"): the body, its finger wheel ("dial" 0-1 is one pull of the dial) and the handset
    on the cradle, recoloured to the set's red. Its coiled cord is ours, Ethernet blue, from the base's right side to
    the handset's end. The handset root is keyed in animate() (S22: off the hook)."""
    out = {}
    # Rough, not the shelf frames' chrome: a chrome bracket smeared the cord's reflection into a blue sheet (C4 v5).
    K.mesh_obj("phone.bracket", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("phone_bracket", "shadow", 0.7), None,
               size=1, location=PHONE + Vector((0, 0.05, -0.04))).scale = (0.34, 0.36, 0.03)
    base_root = K.empty("phone", PHONE)
    K.prop(base_root, "dial", 0.0)
    with bpy.data.libraries.load(str(PHONE_BLEND)) as (src, dst):
        dst.objects = ["phone_body", "phone_handset", "phone_wheel"]
    body, hs_mesh, wheel = dst.objects
    for o in dst.objects:
        K.link(o)
    body_m = K.mat_plastic("phone_body", "alarm", 0.15)
    for o in (body, hs_mesh):
        o.data.materials[0] = body_m
    wheel.data.materials[0] = K.mat_plastic("dial_wheel", "paper", 0.25)
    body.parent = base_root
    body.location = (0, 0, 0)
    # The wheel turns about its own axis (its local Z) under a pivot that holds its rest placement on the body.
    pivot = K.empty("phone.wheel", (0, 0, 0), body)
    pivot.matrix_basis = wheel.matrix_basis.copy()  # matrix_local isn't evaluated yet on freshly appended objects
    wheel.parent = pivot
    wheel.matrix_basis = Matrix.Identity(4)
    _drive_vars(wheel, "rotation_euler", 2, {"x": (base_root, "dial")}, "-5.0 * x")
    hs = K.empty("phone.handset", hs_mesh.location.copy(), base_root)
    hs_mesh.parent = hs
    hs_mesh.location = (0, 0, 0)
    top = max((hs_mesh.matrix_local @ Vector(c)).z for c in hs_mesh.bound_box)
    out["perch"] = PHONE + hs.location + Vector((0, 0, top + K.PROBE_R))  # the probe sits on top of the handset
    # The cord runs from the grommet in the base's right side through a slack point ("phone.cord_mid", keyed with the
    # handset in animate()) to the handset's end, so it stays outside the body and drapes over the bracket's edge.
    cord_m = K.mat_plastic("ethernet", "lab_glow", 0.3)
    ends = [K.empty("phone.cord_start", Vector(body["cord_anchor"]), base_root),
            K.empty("phone.cord_mid", CORD_MID_REST, base_root),
            K.empty("phone.cord_end", Vector(hs_mesh["cord_anchor"]), hs)]
    _coil_cord("phone.cord", cord_m, ends)
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
    # The phone dials itself on each "Operator": three pulls over a long one, one over a short one. In S22 it dials
    # 0, the operator (the full pull, 1.0), just after the cut, so it reads before the handset goes (human, C4 v5).
    keys = [(0, 0.0, "CONSTANT")]
    s22 = _dial_zero(shot)
    for w in A.words_starting("Operator"):
        if not (t0 - 2 <= w["t"] <= t1 + 1):
            continue
        if abs(w["t"] - shot["S22"]["cut"]) < 1.0:
            keys += [(A.frame(s22), 0.0, "BEZIER"), (A.frame(s22 + 0.65), 1.0, "BEZIER"),
                     (A.frame(s22 + 1.6), 0.0, "BEZIER")]
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
    _handset(S, shot)
    _pinners(S, shot)


def _lead(S, shot, line):
    """S11: out of the tube mouth and down onto the phone; S12: sitting on the handset, LED singing."""
    p = S["lead"]
    t11 = shot["S11"]["cut"]
    perch = S["perch"]
    path = [(t11 - 1.0, TUBE_MOUTH + Vector((0.1, 0, 0.26))), (t11 + 0.3, TUBE_MOUTH + Vector((0.1, 0, 0.26))),
            (t11 + 0.9, TUBE_MOUTH + Vector((0, 0, -0.12))), (t11 + 2.2, perch + Vector((0.0, -0.05, 0.25))),
            (t11 + 3.0, perch)]
    for t, loc in path:
        p.location = loc
        p.keyframe_insert("location", frame=A.frame(t))
    p.rotation_euler = (0, 0, math.radians(-15))
    A.envelope_rig(p, "led", A.envelope("vocal_env") ** 2.0, A.frame(t11), A.frame(shot["S23"]["cut"]), gain=0.8,
                   offset=0.2)
    # S22: the handset goes; the probe hops up and settles on the cradle's posts, where the handset lay.
    t = _off_hook(shot)
    # It rises with the lifted handset and stays up until the handset has swung clear, then settles.
    for dt, d in ((-0.1, (0, 0, 0)), (0.35, (0.0, -0.02, 0.13)), (0.85, (0.0, -0.03, 0.13)), (1.1, (0.0, -0.03, -0.02))):
        loc = perch + Vector(d)
        p.location = loc
        p.keyframe_insert("location", frame=A.frame(t + dt))


def _dial_zero(shot):
    """S22: when the dial starts its pull to 0."""
    return shot["S22"]["cut"] + 0.05


def _off_hook(shot):
    """S22: the handset goes once the dial has run back from 0."""
    return _dial_zero(shot) + 1.8


def _handset(S, shot):
    """Off the hook in S22, after the dial's 0: lifted, swung out past the base's right side, dropped, and hanging
    straight down from its cord where the cord goes over the bracket's edge, swinging there like a pendulum and
    settling. The cord's slack point moves with it."""
    hs = S["handset"]
    mid = bpy.data.objects["phone.cord_mid"]
    t = _off_hook(shot)
    rest_loc, rest_rot = hs.location.copy(), hs.rotation_euler.copy()
    drape = Vector((0.2, -0.04, -0.01))  # phone-local: just past the bracket's edge (x 0.17), above its top
    length = 0.42  # drape point to the handset's centre (cord drop plus half the handset)
    # Lifted (0.35 s), carried out past the base's side (0.5 s; it shot sideways in 0.17 s, C4 v6), dropped (0.4 s).
    seq = [(t - 0.1, rest_loc, rest_rot), (t + 0.35, rest_loc + Vector((0, -0.05, 0.12)), (0.2, 0, 0)),
           (t + 0.85, rest_loc + Vector((0.32, -0.12, 0.1)), (0.1, -0.6, 0.2))]
    for k in range(7):  # a damped pendulum about the drape point: it tilts as it swings, cord end toward the drape
        phi = 0.0 if k == 0 else 0.22 * math.exp(-0.55 * (k - 1)) * (1 if k % 2 else -1)
        centre = drape + Vector((length * math.sin(phi), 0.0, -length * math.cos(phi)))
        seq.append((t + 1.25 + 0.42 * k, centre, (0, -math.pi / 2 - phi, 0.3 * phi)))
    for tt, loc, rot in seq:
        hs.location, hs.rotation_euler = loc, rot
        hs.keyframe_insert("location", frame=A.frame(tt))
        hs.keyframe_insert("rotation_euler", frame=A.frame(tt))
    # The slack point: by the base while the handset is up, then on the drape point over the bracket's edge.
    for tt, loc in ((t - 0.1, CORD_MID_REST), (t + 0.85, (0.21, -0.04, 0.05)), (t + 1.25, tuple(drape))):
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
    # Over the corner camera's shoulder: it big in the foreground left, watching the noted drawers behind it; on
    # "while you looked the other way" it swings off them, round toward us.
    "S17": [(0.0, _v(-3.95, -1.75, 3.05), _v(-0.8, -0.25, 1.75), 28), (1.0, _v(-3.85, -1.65, 3.0), _v(-0.8, -0.25, 1.75), 30)],
    # The phone off the hook.
    "S22": [(0.0, PHONE + _v(1.0, -1.3, 0.35), PHONE + _v(0, 0, 0.0), 35),
            (1.0, PHONE + _v(0.75, -1.0, 0.2), PHONE + _v(0.1, 0, -0.15), 40)],
}


def _resolve():
    """S15 ends on the hero drawer's note (computed from the events, so it follows the transcription)."""
    tgt = _hero_target()
    CAMERAS["S15"][1] = (1.0, tgt + _v(0.15, -0.95, 0.12), tgt, 40)


_resolve()
