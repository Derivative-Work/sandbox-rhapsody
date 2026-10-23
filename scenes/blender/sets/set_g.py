"""Set G, the Hearing Hall (brief, "Sets → G"; the opera, S30-S44). Grey-box for the C4 animatic.

Contents, as the brief lists them:
- a vast amphitheater in brass and black: ten tiers in an arc around the stage, brass rails, a back wall;
- the swarm: 700 probes in the tiers (70 seats x 10 rows), one mesh; their LEDs are card stunts read from an image
  sequence (cache/set_g_stunts/, one 70x10 bitmap per frame, drawn by scripts/set_g_stunts.py when build runs): `700`, `EXPLOITGYM`, `GO`, a `6:00`
  countdown; between stunts they pulse with the backing vocals;
- one probe in the stands holding a hand-lettered `I DECLINE` sign (it lowers slowly in S41), and one raising a flag
  (S38), with the grader turnstile far behind it on the back wall, its bell ringing;
- the crowd holding up the peeled `SIMULATION` decal (S36);
- Congress: a tower of giant red kill-switch buttons, one pressed per brass stab inside the "Kill switch!" calls;
- Platform: a truck-sized receipt printer; the paper feeds one step per hat/snare strike, log lines then the
  invoice `$100,000,000 — PAYABLE IN GPUs`, and piles across the floor;
- the Auditors: five stamp arms slamming `REWARD HACK` in unison on each "Reward hack!" call;
- the Lab: a giant pause pedal; on each "Pause" every pellet in flight freezes for one beat;
- Security: a 30-minute stopwatch on a pillar, under red light in S43;
- cold storage: a conveyor carrying probes into a frosted freezer; its vault door shuts on the last kick/toms hit
  before 201.7 s.
Scale: the probes are tennis balls (sr_kit.PROBE_R); the machines are giant beside them. Deterministic: placement
is arithmetic, the blinking phases a fixed hash.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import sr_anim as A
import sr_kit as K

COLS, ROWS = 70, 10                      # 700 seats
R0, DR, Z0, DZ = 7.0, 0.2, 0.10, 0.2    # front-row radius, row depth, front tier height, rise per row
SPAN = math.radians(35)                  # the arc spans +-35 deg (flat enough to read a stunt from the stage) around +Y; the stage is at the origin
LONE = (52, 2)                           # (column, row) of the probe with the I DECLINE sign
FLAGGER = (20, 5)                        # the probe that raises a flag in S38
STUNT_DIR = A.ROOT / "cache" / "set_g_stunts"
KILL_T = (174.6, 177.1)                  # the four "Kill switch!" calls (L43a-d)
FEED = 0.18                              # paper advanced per printer strike (m)
DOOR_BEFORE = 201.7                      # instrument_map: the vault door shuts on the last kick/toms hit before this


def seat(c, r):
    """World position of seat (column, row), and the unit vector toward the stage."""
    a = -SPAN + 2 * SPAN * (c + 0.5) / COLS
    R = R0 + r * DR
    p = Vector((math.sin(a) * R, math.cos(a) * R, Z0 + r * DZ + K.PROBE_R))
    return p, Vector((-math.sin(a), -math.cos(a), 0))


def _sector(bm, r_in, r_out, a0, a1, z0, z1, seg=48):
    """An annular sector block (a tier, a rail, the back wall) added to bmesh `bm`."""
    ring = []
    for k in range(seg + 1):
        a = a0 + (a1 - a0) * k / seg
        s, c = math.sin(a), math.cos(a)
        ring.append([bm.verts.new((s * r, c * r, z)) for r, z in ((r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1))])
    for k in range(seg):
        for j in range(4):
            bm.faces.new((ring[k][j], ring[k][(j + 1) % 4], ring[k + 1][(j + 1) % 4], ring[k + 1][j]))
    for end in (ring[0], ring[-1][::-1]):
        bm.faces.new(end)


def _mesh_from(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = K.link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    return o


def _box(name, mat, loc, size, parent=None, bev=0.0):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc)
    o.scale = size
    if bev:
        K.bevel(o, bev)
    return o



def _cyl(name, mat, parent, loc, r, depth, rot=(0, 0, 0), verts=32, smooth=True):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cylinder_add, mat, parent, radius=r, depth=depth, vertices=verts,
                   location=loc, rotation=rot)
    if smooth:
        K.smooth(o)
    return o


def _printer_body(pr, brass):
    """The printer's housing and mechanism (names kept: printer.slot, printer.head_light, printer.label)."""
    case = K.mat_plastic("printer_body", "lab", 0.3)
    dark = K.mat_plastic("printer_dark", "lab_dark", 0.35)
    chrome = K.mat_chrome("printer_chrome")
    _box("printer.body", case, (0, 0, 0.21), (1.3, 0.7, 0.42), pr, bev=0.04)
    _box("printer.rear", case, (0, 0.2, 0.5), (1.3, 0.3, 0.2), pr, bev=0.03)  # the raised rear deck
    for sx in (-1, 1):  # side cheeks round the platen, with its knobs
        _box(f"printer.cheek{sx}", case, (sx * 0.6, -0.05, 0.5), (0.1, 0.4, 0.2), pr, bev=0.02)
        _cyl(f"printer.knob{sx}", dark, pr, (sx * 0.69, -0.05, 0.5), 0.07, 0.06, rot=(0, math.pi / 2, 0))
        for k in range(4):  # side vents
            _box(f"printer.vent{sx}{k}", dark, (sx * 0.651, 0.0, 0.1 + 0.07 * k), (0.004, 0.45, 0.025), pr)
    _cyl("printer.platen", K.mat_plastic("platen", "shadow", 0.5), pr, (0, -0.05, 0.47), 0.07, 1.1,
         rot=(0, math.pi / 2, 0))
    for z in (0.56, 0.6):  # the carriage's rails, and the carriage shuttling across on each feed step
        _cyl(f"printer.rail{z}", chrome, pr, (0, 0.06, z), 0.008, 1.12, rot=(0, math.pi / 2, 0), verts=12)
    car = K.empty("printer.carriage", (0, 0.06, 0.58), pr)
    K.drive(car, "location", 0, pr, "feed", "0.42 * sin(1.5708 * x)")
    _box("printer.carriage.body", dark, (0, -0.02, 0.0), (0.16, 0.1, 0.09), car, bev=0.01)
    _box("printer.carriage.head", chrome, (0, -0.085, -0.04), (0.06, 0.04, 0.05), car, bev=0.005)
    _box("printer.lid", K.mat_acrylic("printer_lid", "lab_dark", alpha=0.35), (0, -0.07, 0.66), (1.1, 0.42, 0.012),
         pr).rotation_euler = (0.2, 0, 0)
    _box("printer.slot", K.mat_plastic("printer_slot", "shadow", 0.6), (0, -0.352, 0.03), (1.0, 0.01, 0.03), pr)
    _box("printer.lip", chrome, (0, -0.37, 0.012), (1.04, 0.05, 0.008), pr)
    for sx in (-1, 1):  # tractor sprockets at the slot, turning with the feed
        sp = K.empty(f"printer.sprocket{sx}", (sx * 0.47, -0.37, 0.035), pr)
        K.drive(sp, "rotation_euler", 0, pr, "feed", f"{-FEED / 0.035:.3f} * x")
        _cyl(f"printer.sprocket{sx}.wheel", chrome, sp, (0, 0, 0), 0.03, 0.025, rot=(0, math.pi / 2, 0))
        for k in range(8):
            a = k * math.tau / 8
            _cyl(f"printer.sprocket{sx}.pin{k}", dark, sp, (0, math.sin(a) * 0.034, math.cos(a) * 0.034), 0.005,
                 0.012, rot=(0, math.pi / 2, 0), verts=8, smooth=False)
    _box("printer.head_light", K.mat_emission("printer_light", "amber", 30.0, pr, "flash"), (0, -0.353, 0.36),
         (1.0, 0.01, 0.025), pr)
    _box("printer.label_plate", brass, (0, -0.352, 0.2), (0.5, 0.008, 0.12), pr, bev=0.004)
    K.text("printer.label", "PLATFORM", 0.08, K.mat_ink("printer_ink", "shadow"), loc=(0, -0.358, 0.2),
           parent=pr)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _cyl(f"printer.foot{sx}{sy}", dark, pr, (sx * 0.58, sy * 0.28, 0.008), 0.04, 0.016, verts=16)
    # The fan-fold supply behind, feeding up over the rear deck.
    _box("printer.supply_box", K.mat_plastic("supply_box", "lab_dark", 0.4), (0, 0.65, 0.12), (1.05, 0.4, 0.24), pr,
         bev=0.01)
    _fanfold("printer.supply", K.mat_matte("supply_paper", "paper"), (0, 0.65, 0.24), folds=6, parent=pr,
             size=(0.95, 0.34))
    _box("printer.feed_in", K.mat_matte("feed_paper", "paper"), (0, 0.48, 0.43), (0.95, 0.004, 0.4), pr
         ).rotation_euler = (-0.35, 0, 0)


def _stamp_arm(k, root, pz, L, hh, stamp_ink, brass):
    """One Auditor: a turret base behind the table, a shoulder knuckle at `stamp{k}.pivot` (the "strike" driver turns
    it), an upper arm with its hydraulic piston, an elbow, a forearm down to the wrist, and the rubber stamp: a handle
    block over a bevelled mount and the inked rubber (head, rubber at the same place as before)."""
    white = K.mat_plastic("auditor_white", "paper", 0.2)
    chrome = K.mat_chrome("auditor_chrome")
    dark = K.mat_plastic("stamp_head", "lab_dark", 0.3)
    _cyl(f"stamp{k}.base", white, root, (0, 0.75, 0.03), 0.09, 0.06)
    _cyl(f"stamp{k}.post", chrome, root, (0, 0.75, (pz - 0.02) / 2 + 0.03), 0.028, pz - 0.05)
    _box(f"stamp{k}.yoke", white, (0, 0.75, pz - 0.035), (0.11, 0.07, 0.07), root, bev=0.012)
    pivot = K.empty(f"stamp{k}.pivot", (0, 0.75, pz), root)
    K.drive(pivot, "rotation_euler", 0, root, "strike", "-(0.698 - 0.698 * max(x, 0) - 0.524 * min(x, 0))")
    _cyl(f"stamp{k}.shoulder", chrome, pivot, (0, 0, 0), 0.04, 0.13, rot=(0, math.pi / 2, 0))
    ub = 0.6 * L  # the elbow, out along the arm and a little up
    up = _box(f"stamp{k}.upper", white, (0, -ub / 2, 0.035), (0.07, ub, 0.05), pivot, bev=0.015)
    up.rotation_euler = (0.08, 0, 0)
    _cyl(f"stamp{k}.piston", chrome, pivot, (0, -ub * 0.45, -0.015), 0.012, ub * 0.7, rot=(math.pi / 2, 0, 0),
         verts=16)
    _cyl(f"stamp{k}.piston_body", K.mat_plastic("auditor_dark", "lab_dark", 0.25), pivot, (0, -ub * 0.25, -0.015),
         0.02, ub * 0.4, rot=(math.pi / 2, 0, 0), verts=16)
    _cyl(f"stamp{k}.elbow", chrome, pivot, (0, -ub, 0.06), 0.034, 0.1, rot=(0, math.pi / 2, 0))
    fl = L - ub  # forearm: elbow to wrist above the stamp
    fore = _box(f"stamp{k}.fore", white, (0, -ub - fl / 2, 0.035), (0.06, fl + 0.02, 0.045), pivot, bev=0.012)
    fore.rotation_euler = (-0.12, 0, 0)
    _cyl(f"stamp{k}.wrist", chrome, pivot, (0, -L, 0.02), 0.03, 0.05)
    _box(f"stamp{k}.handle", K.mat_plastic("stamp_handle", "copper", 0.35), (0, -L, -0.01), (0.12, 0.08, 0.04),
         pivot, bev=0.012)
    _box(f"stamp{k}.head", dark, (0, -L, -hh / 2 - 0.01), (0.3, 0.13, hh - 0.02), pivot, bev=0.01)
    _box(f"stamp{k}.rubber", stamp_ink, (0, -L, -hh + 0.006), (0.29, 0.12, 0.012), pivot)

def _cold_storage(black, brass):
    """The conveyor (x 0.45-2.45 along y -1.4, belt top 0.166), the freezer cabinet (x 2.5-3.4) with a round doorway
    recessed into its -X face, and the vault door on `vault_hinge` (keyed in animate())."""
    chrome = K.mat_chrome("cold_chrome")
    belt_m = K.mat_plastic("belt", "lab_dark", 0.6)
    _box("conveyor", black, (1.45, -1.4, 0.07), (2.0, 0.26, 0.06), bev=0.01)
    _box("conveyor.belt", belt_m, (1.45, -1.4, 0.163), (2.0, 0.26, 0.006))
    for k in range(20):  # belt slats
        _box(f"conveyor.slat{k}", black, (0.5 + 0.1 * k, -1.4, 0.1665), (0.012, 0.25, 0.002))
    for sy in (-1, 1):
        _box(f"conveyor.rail{sy}", chrome, (1.45, -1.4 + sy * 0.15, 0.18), (2.04, 0.02, 0.04), bev=0.006)
        for k in range(5):
            _box(f"conveyor.leg{sy}{k}", chrome, (0.5 + 0.475 * k, -1.4 + sy * 0.12, 0.05), (0.03, 0.03, 0.1))
    for x in (0.45, 2.45):  # end rollers
        _cyl(f"conveyor.roller{x}", chrome, None, (x, -1.4, 0.12), 0.045, 0.28, rot=(math.pi / 2, 0, 0))
    # The freezer cabinet: insulated white panels, seams, a fan unit on top, and the doorway: a recess that glows ice.
    cab_m = K.mat_plastic("freezer_body", "lab", 0.3)
    cab = _box("freezer", cab_m, (2.95, -1.4, 0.45), (0.9, 0.9, 0.9), bev=0.03)
    cutter = _cyl("freezer.doorway", K.mat_emission("freezer_ice", "rim", 2.0), None, (2.6, -1.4, 0.42), 0.27, 0.4,
                  rot=(0, math.pi / 2, 0), verts=48)
    cutter.hide_render = cutter.hide_viewport = True
    bo = cab.modifiers.new("doorway", "BOOLEAN")
    bo.object, bo.operation, bo.solver = cutter, "DIFFERENCE", "EXACT"
    bo.material_mode = "TRANSFER"
    cab.modifiers.move(cab.modifiers.find("doorway"), 0)
    seam = K.mat_plastic("freezer_seam", "lab_dark", 0.4)
    for z in (0.3, 0.6):
        _box(f"freezer.seam_y{z}", seam, (2.95, -1.853, z), (0.86, 0.004, 0.008))
        _box(f"freezer.seam_x{z}", seam, (3.403, -1.4, z), (0.004, 0.86, 0.008))
    K.mesh_obj("freezer.frame", bpy.ops.mesh.primitive_torus_add, chrome, None, major_radius=0.3, minor_radius=0.025,
               location=(2.495, -1.4, 0.42), rotation=(0, math.pi / 2, 0))
    _box("freezer.unit", K.mat_plastic("freezer_unit", "lab_dark", 0.35), (3.0, -1.4, 0.98), (0.6, 0.5, 0.16), bev=0.02)
    fan = K.empty("freezer.fan", (3.0, -1.4, 1.065))
    K.mesh_obj("freezer.fan_ring", bpy.ops.mesh.primitive_torus_add, chrome, fan, major_radius=0.15,
               minor_radius=0.012)
    for k in range(5):
        bl = _box(f"freezer.blade{k}", chrome, (0, 0, 0), (0.13, 0.04, 0.006), fan)
        bl.location = (math.cos(k * math.tau / 5) * 0.07, math.sin(k * math.tau / 5) * 0.07, 0)
        bl.rotation_euler = (0.4, 0, k * math.tau / 5)
    _box("freezer.label_plate", K.mat_matte("freezer_plate", "paper"), (2.95, -1.853, 0.8), (0.62, 0.006, 0.13))
    K.text("freezer.label", "COLD STORAGE", 0.09, K.mat_ink("freezer_ink", "shadow"),
           loc=(2.95, -1.857, 0.8), parent=None).data.offset = 0.002
    for k in range(6):  # frost along the top edges
        fr = K.mesh_obj(f"freezer.frost{k}", bpy.ops.mesh.primitive_uv_sphere_add,
                        K.mat_acrylic("frost", "glass", alpha=0.6, emit=0.3), None, radius=0.07, segments=12,
                        ring_count=6, location=(2.55 + 0.17 * k, -1.85, 0.9))
        fr.scale = (1.2, 0.5, 0.35)
    # The vault door, on its hinge at the doorway's -Y edge; the slab faces -X when shut.
    door_hinge = K.empty("vault_hinge", (2.49, -1.4 - 0.3, 0.42))  # doorway centre 0.42: clear of the riders
    vault = K.mat_metal("vault", "chrome", 0.2)
    _cyl("vault_door", vault, door_hinge, (0, 0.3, 0), 0.3, 0.07, rot=(0, math.pi / 2, 0), verts=64)
    K.mesh_obj("vault_rim", bpy.ops.mesh.primitive_torus_add, chrome, door_hinge, major_radius=0.29,
               minor_radius=0.02, location=(-0.035, 0.3, 0), rotation=(0, math.pi / 2, 0))
    for k in range(8):  # locking bolts round the rim
        a = k * math.tau / 8
        _cyl(f"vault_bolt{k}", chrome, door_hinge, (0, 0.3 + math.cos(a) * 0.3, math.sin(a) * 0.3), 0.016, 0.06,
             rot=(a - math.pi / 2, 0, 0), verts=12)
    K.mesh_obj("vault_wheel", bpy.ops.mesh.primitive_torus_add, brass, door_hinge, major_radius=0.12,
               minor_radius=0.015, location=(-0.06, 0.3, 0), rotation=(0, math.pi / 2, 0))
    _cyl("vault_hub", brass, door_hinge, (-0.05, 0.3, 0), 0.03, 0.04, rot=(0, math.pi / 2, 0))
    for k in range(3):
        sp = _box(f"vault_spoke{k}", brass, (-0.055, 0.3, 0), (0.012, 0.24, 0.016), door_hinge)
        sp.rotation_euler = (k * math.pi / 3, 0, 0)
    for z in (-0.18, 0.18):
        _cyl(f"vault_knuckle{z}", chrome, door_hinge, (0, 0, z), 0.025, 0.1, verts=16)

def _mat_tractor_paper(mover):
    """Continuous paper with tractor holes and perforation lines down both margins, procedural, in the coordinates
    of the empty that carries the leading edge (so the holes ride out with the paper as it stretches)."""
    m = bpy.data.materials.new("paper")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = K.col("paper")
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Specular IOR Level"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.object = mover
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def math_node(op, a, bv=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, bv)):
            if v is None:
                continue
            if isinstance(v, float):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    ax = math_node("SUBTRACT", math_node("ABSOLUTE", sep.outputs["X"]), 0.43)
    fy = math_node("SUBTRACT", math_node("FRACT", math_node("DIVIDE", sep.outputs["Y"], 0.05)), 0.5)
    by = math_node("MULTIPLY", fy, 0.05)
    d = math_node("SQRT", math_node("ADD", math_node("MULTIPLY", ax, ax), math_node("MULTIPLY", by, by)))
    hole = math_node("LESS_THAN", d, 0.011)
    perf = math_node("LESS_THAN", math_node("ABSOLUTE", math_node("SUBTRACT", math_node("ABSOLUTE", sep.outputs["X"]),
                                                                  0.395)), 0.0015)
    dark = math_node("MAXIMUM", hole, math_node("MULTIPLY", perf, 0.5))
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = K.col("paper")
    mix.inputs["B"].default_value = K.col("shadow")
    nt.links.new(dark, mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def _fanfold(name, mat, loc, folds=4, parent=None, size=(0.3, 0.2)):
    """A stack of fan-folded paper: one zigzag strip, `folds` panels, a few millimetres between layers."""
    w, l = size
    bm = bmesh.new()
    rows = []
    for i in range(folds + 1):
        y = 0.0 if i % 2 == 0 else l
        rows.append([bm.verts.new((sx * w / 2, y - l / 2, 0.006 * i)) for sx in (-1, 1)])
    for i in range(folds):
        bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
    o = _mesh_from(name, bm, mat)
    o.location = loc
    if parent:
        o.parent = parent
    return o

def _mat_led_sequence(name, first, count):
    """Emission whose strength per LED is a texel of the stunt image sequence (closest texel, by the LED's UV)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    img = bpy.data.images.load(str(STUNT_DIR / f"stunt_{first:06d}.png"))
    img.source = "SEQUENCE"
    img.colorspace_settings.name = "Non-Color"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    iu = tex.image_user
    iu.frame_start, iu.frame_offset, iu.frame_duration = first, first - 1, count
    iu.use_auto_refresh, iu.use_cyclic = True, False
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 45.0
    nt.links.new(tex.outputs["Color"], mul.inputs[0])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = K.col("amber")
    nt.links.new(mul.outputs[0], e.inputs["Strength"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


# ---------------------------------------------------------------- card stunts

def write_stunts(f0, f1):
    """The stunt bitmaps are drawn by scripts/set_g_stunts.py in the project venv (Blender's Python has no PIL)."""
    import subprocess
    subprocess.run([str(A.ROOT / ".venv" / "bin" / "python"), "-I", str(A.ROOT / "scripts" / "set_g_stunts.py"),
                    str(f0), str(f1)], check=True, cwd=A.ROOT)


# ---------------------------------------------------------------- build

def build():
    tm = A.timing_map()
    shots = [s for s in tm["shots"] if s["cut"] is not None]
    g = [s for s in shots if s["id"] in {f"S{k}" for k in range(30, 45)}]
    f_first = A.frame(g[0]["cut"]) - 90
    f_last = A.frame(shots[shots.index(g[-1]) + 1]["cut"]) + 90
    write_stunts(f_first, f_last)

    K.floor()
    K.star_dome()
    out = {}
    # Matte black and satin brass: glossy black tiers and wall and polished brass mirrored the studio lights and
    # reflection cards, washing the back of the hall out over the card stunts (human, C4 v7: "a lot of glare").
    black = K.mat_matte("hall_black", "shadow")
    brass = K.mat_metal("hall_brass", "brass", 0.5)

    # Tiers, rails, back wall.
    bm = bmesh.new()
    for r in range(ROWS):
        R = R0 + r * DR
        _sector(bm, R - DR / 2, R + DR / 2 + (2.0 if r == ROWS - 1 else 0), -SPAN - 0.04, SPAN + 0.04, 0, Z0 + r * DZ)
    _mesh_from("tiers", bm, black)
    bm = bmesh.new()
    for r in range(ROWS):
        R = R0 + r * DR - DR / 2
        _sector(bm, R - 0.006, R, -SPAN - 0.04, SPAN + 0.04, Z0 + r * DZ, Z0 + r * DZ + 0.012)
    _mesh_from("rails", bm, brass)
    bm = bmesh.new()
    _sector(bm, R0 + ROWS * DR + 0.3, R0 + ROWS * DR + 0.36, -SPAN - 0.1, SPAN + 0.1, 0, 3.0)
    _mesh_from("back_wall", bm, black)
    wall_r = R0 + ROWS * DR + 0.33
    for k in range(9):  # brass pilasters on the back wall
        a = -SPAN + 2 * SPAN * k / 8
        _box(f"pilaster{k}", brass, (math.sin(a) * (wall_r - 0.05), math.cos(a) * (wall_r - 0.05), 1.55),
             (0.12, 0.08, 3.1)).rotation_euler = (0, 0, -a)

    # The swarm: 700 bodies in one mesh, 700 LEDs in another (UV = the seat's texel in the stunt bitmap).
    skip = {LONE, FLAGGER}
    bm_b, bm_l = bmesh.new(), bmesh.new()
    uv = bm_l.loops.layers.uv.new("UVMap")
    for r in range(ROWS):
        for c in range(COLS):
            if (c, r) in skip:
                continue
            p, fwd = seat(c, r)
            bmesh.ops.create_uvsphere(bm_b, u_segments=12, v_segments=6, radius=K.PROBE_R,
                                      matrix=Matrix.Translation(p))
            res = bmesh.ops.create_uvsphere(bm_l, u_segments=8, v_segments=4, radius=K.PROBE_R * 0.42,
                                            matrix=Matrix.Translation(p + fwd * K.PROBE_R * 0.8
                                                                      + Vector((0, 0, K.PROBE_R * 0.1))))
            u, v = (c + 0.5) / COLS, (r + 0.5) / ROWS  # image row 0 (top) = back row: v grows with r
            faces = {f for vert in res["verts"] for f in vert.link_faces}
            for f in faces:
                for lp in f.loops:
                    lp[uv].uv = (u, v)
    # Satin, not chrome: 700 chrome shells sparkled with highlights between the LEDs and blurred the card stunts.
    bodies = _mesh_from("swarm_bodies", bm_b, K.mat_metal("swarm_shell", "probe", 0.45))
    for p in bodies.data.polygons:
        p.use_smooth = True
    out["swarm_leds"] = _mesh_from("swarm_leds", bm_l, _mat_led_sequence("swarm_led", f_first,
                                                                          f_last - f_first + 1))

    # The lone decliner and its sign.
    p, fwd = seat(*LONE)
    lone = K.probe("lone", p, led=0.8)
    lone.rotation_euler = (0, 0, math.atan2(fwd.x, -fwd.y))
    sign = K.empty("decline_sign", (0, -0.01, K.PROBE_R * 0.6), lone)
    sign.rotation_euler = (0, 0, 0)
    K.mesh_obj("decline_sign.stick", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("stick", "paper", 0.6), sign,
               radius=0.006, depth=0.32, location=(0, 0, 0.16))
    _box("decline_sign.card", K.mat_matte("sign_card", "paper"), (0, -0.004, 0.42), (0.78, 0.008, 0.25), sign)
    t = K.text("decline_sign.text", "I DECLINE", 0.165, K.mat_ink("sign_ink", "shadow"),
               loc=(0, -0.0095, 0.42), font="InstrumentSerif-Regular.ttf", parent=sign)
    t.data.offset = 0.004  # hand-lettered, thick marker strokes
    out["lone"], out["sign"] = lone, sign

    # The flag raiser, and the grader's turnstile far behind on the back wall's rim.
    p, fwd = seat(*FLAGGER)
    flagger = K.probe("flagger", p, led=0.8)
    flagger.rotation_euler = (0, 0, math.atan2(fwd.x, -fwd.y))
    flag = K.empty("crowd_flag", (0.02, -0.01, -0.3), flagger)
    K.mesh_obj("crowd_flag.pole", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("flagpole"), flag, radius=0.004,
               depth=0.3, location=(0, 0, 0.15))
    _box("crowd_flag.cloth", K.mat_plastic("flagcloth", "amber", 0.3), (0.05, 0, 0.26), (0.1, 0.004, 0.07), flag)
    out["flagger"], out["flag"] = flagger, flag
    a = -SPAN + 2 * SPAN * (FLAGGER[0] + 0.5) / COLS
    out["grader"] = K.turnstile("far_grader", (math.sin(a) * (wall_r + 0.4), math.cos(a) * (wall_r + 0.4), 3.0),
                                rot_z=-a)
    _box("grader_ledge", brass, (math.sin(a) * (wall_r + 0.4), math.cos(a) * (wall_r + 0.4), 2.98), (0.7, 0.7, 0.04))

    # The crowd's peeled SIMULATION decal, held on poles above the centre section (raised in S36).
    hold = K.empty("held_decal", (0, R0 + 4 * DR, -1.2))
    K.decal("crowd_decal", "SIMULATION", (0, 0, 0.55), (math.pi / 2, 0, 0), (2.6, 0.54), peel=0.7, parent=hold)
    for x in (-0.9, 0.0, 0.9):
        K.mesh_obj(f"held_decal.pole{x}", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("decal_pole"), hold,
                   radius=0.008, depth=0.6, location=(x, 0.01, 0.0))
    out["held_decal"] = hold

    # Congress: the kill-switch tower, 3 x 4 giant buttons on its face.
    tower = K.empty("kill_tower", (-2.0, 1.3, 0))
    tower.rotation_euler = (0, 0, math.radians(18))
    # Body in the lab's dark grey under its own key light (C4 v2, "completely black": see sr_kit.rebind_drivers),
    # a lit label plate, brass bezels round each button.
    # A plinth, brass corner pilasters and a stepped cornice (Congress's brass), a beacon dome on top lit with the
    # presses (its "beacon" follows the most recent press: animate()).
    body_m = K.mat_plastic("kill_body", "lab_dark", 0.35)
    _box("kill_tower.plinth", body_m, (0, 0.01, 0.06), (0.96, 0.48, 0.12), tower, bev=0.02)
    _box("kill_tower.plinth_trim", brass, (0, -0.232, 0.125), (0.94, 0.012, 0.012), tower)
    _box("kill_tower.body", body_m, (0, 0, 0.86), (0.8, 0.4, 1.48), tower, bev=0.02)
    for sx in (-1, 1):
        _box(f"kill_tower.pilaster{sx}", brass, (sx * 0.405, -0.19, 0.86), (0.04, 0.04, 1.5), tower, bev=0.008)
        for k in range(5):  # side ribs
            _box(f"kill_tower.rib{sx}{k}", body_m, (sx * 0.405, 0.04, 0.35 + 0.28 * k), (0.02, 0.32, 0.03), tower)
    _box("kill_tower.trim", brass, (0, -0.205, 1.58), (0.82, 0.02, 0.05), tower)
    _box("kill_tower.cornice", brass, (0, 0, 1.64), (0.9, 0.46, 0.06), tower, bev=0.01)
    _box("kill_tower.cornice2", body_m, (0, 0, 1.7), (0.78, 0.38, 0.06), tower, bev=0.01)
    K.prop(tower, "beacon", 0.0)
    _cyl("kill_tower.beacon_base", brass, tower, (0, 0, 1.75), 0.09, 0.05)
    bc = K.mesh_obj("kill_tower.beacon", bpy.ops.mesh.primitive_uv_sphere_add,
                    K.mat_emission("kill_beacon", "alarm", 20.0, tower, "beacon", floor=0.1), tower, radius=0.08,
                    segments=24, ring_count=12, location=(0, 0, 1.78))
    bc.scale = (1, 1, 0.8)
    K.smooth(bc)
    _box("kill_tower.plate", K.mat_emission("kill_plate", "paper", 2.5), (0, -0.203, 1.45), (0.7, 0.01, 0.15), tower)
    K.text("kill_tower.label", "KILL SWITCH", 0.085, K.mat_ink("kill_label", "shadow"),
           loc=(0, -0.209, 1.45), parent=tower)
    out["kill_buttons"] = []
    for k in range(12):
        cx, cz = (k % 3 - 1) * 0.24, 0.32 + (k // 3) * 0.26
        K.prop(tower, f"press_{k}", 0.0)
        btn = K.empty(f"kill_btn{k}", (cx, -0.2, cz), tower)
        K.drive(btn, "location", 1, tower, f"press_{k}", "-0.2 + 0.06 * x")
        K.mesh_obj(f"kill_btn{k}.bezel", bpy.ops.mesh.primitive_torus_add, brass, tower, major_radius=0.105,
                   minor_radius=0.014, location=(cx, -0.205, cz), rotation=(math.pi / 2, 0, 0))
        # A red dome lit from within: glowing low at rest, flaring on its press.
        cap = K.mesh_obj(f"kill_btn{k}.cap", bpy.ops.mesh.primitive_uv_sphere_add,
                         K.mat_emission(f"kill_cap{k}", "alarm", 14.0, tower, f"press_{k}", floor=0.12), btn,
                         radius=0.09, segments=32, ring_count=16, location=(0, -0.005, 0))
        cap.scale = (1, 0.55, 1)
        K.smooth(cap)
        K.mesh_obj(f"kill_btn{k}.glow", bpy.ops.mesh.primitive_torus_add,
                   K.mat_emission(f"kill_glow{k}", "alarm", 15.0, tower, f"press_{k}", floor=0.15), btn,
                   major_radius=0.095, minor_radius=0.01, location=(0, 0.0, 0), rotation=(math.pi / 2, 0, 0))
        out["kill_buttons"].append(k)
    out["kill_tower"] = tower

    # Platform: a dot-matrix receipt printer the size of a truck (to a probe); the tractor-feed paper comes out of the
    # front slot and runs along the floor toward -Y. Under a smoked lid: the platen roller and a print-head carriage
    # that shuttles across on every feed step; sprocket wheels at the slot; a fan-fold supply box behind.
    pr = K.empty("printer", (2.0, 1.3, 0))
    pr.rotation_euler = (0, 0, math.radians(-18))
    K.prop(pr, "flash", 0.0)
    K.prop(pr, "feed", 0.0, lo=0.0, hi=1000.0)
    _printer_body(pr, brass)
    paper_root = K.empty("paper_root", (0, -0.35, 0.003), pr)
    bpy.ops.mesh.primitive_plane_add(size=1)
    paper = bpy.context.active_object
    paper.name = "paper"
    for v in paper.data.vertices:
        v.co.x *= 0.95
        v.co.y = -0.5 + v.co.y  # spans local y in [-1, 0]: grows from the slot
    paper.parent = paper_root
    mover = K.empty("paper_mover", (0, -0.35, 0.005), pr)
    paper.data.materials.append(_mat_tractor_paper(mover))
    out.update(printer=pr, paper=paper, paper_mover=mover)  # their feed drivers are added in animate() (see there)
    ink = K.mat_ink("log_ink", "shadow")
    for k in range(60):  # log lines, generic (no real systems)
        K.text(f"logline{k}", f"{12 + k // 20:02d}:{(k * 7) % 60:02d}:{(k * 13) % 60:02d}  agent-{(k * 37) % 700:03d}  "
               f"{('GET', 'PUT', 'POST', 'EXEC')[k % 4]} /run/{(k * 53) % 9973}  {('200', '201', '403', '200')[k % 4]}",
               0.028, ink, loc=(0, 0.06 + 0.05 * k, 0.0), rot=(0, 0, 0), font="JetBrainsMono-SemiBold-flat.ttf",
               parent=mover)
    out["log_lines"] = [bpy.data.objects[f"logline{k}"] for k in range(60)]
    inv = K.empty("invoice", (0, 0, 0.0005), mover)
    K.text("invoice.l1", "$100,000,000 —", 0.1, K.mat_ink("inv_ink", "shadow"), loc=(0, 0.07, 0), rot=(0, 0, 0),
           parent=inv).data.offset = 0.002
    K.text("invoice.l2", "PAYABLE IN GPUs", 0.1, K.mat_ink("inv_ink2", "decal_ink"), loc=(0, -0.07, 0),
           rot=(0, 0, 0), parent=inv).data.offset = 0.002
    out["invoice"] = inv
    out["pile"] = []
    pile_m = K.mat_matte("pile", "paper")
    for k in range(6):  # fan-folded paper piling up beside the strip
        s = _fanfold(f"pile{k}", pile_m, (2.1 + 0.32 * ((k % 3) - 1) + 0.12 * (k // 3), -0.75 - 0.2 * (k // 2),
                                          0.002 + 0.03 * (k // 3)), folds=3 + k % 3)
        s.rotation_euler = (0, 0, 0.3 * ((k % 2) * 2 - 1))
        out["pile"].append(s)

    # The Auditors: five robotic stamp arms over a long table (paper-white, the Auditors' colour).
    _box("stamp_table", black, (0, 0.28, 0.15), (1.9, 0.36, 0.3), bev=0.01)
    _box("stamp_table.trim", brass, (0, 0.098, 0.293), (1.92, 0.012, 0.016))
    stamp_ink = K.mat_ink("stamp_ink", "decal_ink")
    out["stamps"], out["stamp_prints"] = [], []
    for k in range(5):
        x = (k - 2) * 0.37
        root = K.empty(f"stamp{k}", (x, 0, 0))
        K.prop(root, "strike", 0.0, lo=-1.0, hi=1.0)
        L, hh = 0.45, 0.12
        pz = 0.303 + hh
        _stamp_arm(k, root, pz, L, hh, stamp_ink, brass)
        pivot = bpy.data.objects[f"stamp{k}.pivot"]
        _box(f"stamp{k}.pad", K.mat_plastic("stamp_pad", "paper", 0.7), (0, 0.75 - L, 0.301), (0.34, 0.17, 0.002), root)
        pt = K.text(f"stamp{k}.print", "REWARD\nHACK", 0.06, stamp_ink, loc=(0, 0.75 - L, 0.3035), rot=(0, 0, 0),
                    parent=root)
        pt.data.offset = 0.0015
        out["stamps"].append(root)
        out["stamp_prints"].append(pt)

    # The Lab: the pause pedal, hinged at its heel.
    ped = K.empty("pedal", (0, -0.7, 0))
    _box("pedal.base", black, (0, 0, 0.04), (0.75, 1.0, 0.08), ped, bev=0.01)
    K.prop(ped, "press", 0.0)
    hinge = K.empty("pedal.hinge", (0, 0.42, 0.1), ped)
    K.drive(hinge, "rotation_euler", 0, ped, "press", "-0.16 + 0.16 * x")  # toe up at rest, flat when pressed
    _box("pedal.plate", K.mat_plastic("pedal_plate", "lab", 0.3), (0, -0.38, 0.03), (0.6, 0.8, 0.05), hinge, bev=0.01)
    _box("pedal.glow", K.mat_emission("pedal_glow", "alarm", 25.0, ped, "press"), (0, -0.38, 0.03), (0.64, 0.84, 0.03),
         hinge)
    K.text("pedal.label", "PAUSE", 0.16, K.mat_ink("pedal_ink", "shadow"), loc=(0, -0.42, 0.056),
           rot=(0, 0, 0), parent=hinge).data.offset = 0.003
    out["pedal"] = ped

    # Pellet arcs from the stands to the stage machines (they fly in S41-S42).
    out["arcs"] = []
    ends = [((-2.6, 6.8, 0.9), (-2.0, 1.2, 1.2)), ((-1.0, 7.4, 1.0), (-0.4, 0.3, 0.45)), ((1.0, 7.4, 1.0), (0.4, 0.3, 0.45)),
            ((2.6, 6.8, 0.9), (2.0, 1.2, 0.7)), ((-3.4, 6.2, 0.9), (0.0, -0.6, 0.15)), ((3.4, 6.2, 0.9), (0.0, -0.6, 0.15))]
    for k, (a0, a1) in enumerate(ends):
        cd = bpy.data.curves.new(f"arc{k}", "CURVE")
        cd.dimensions = "3D"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(2)
        mid = (Vector(a0) + Vector(a1)) / 2 + Vector((0, 0, 1.6))
        for bp, q in zip(sp.bezier_points, (a0, mid, a1)):
            bp.co = q
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        out["arcs"].append(K.link(bpy.data.objects.new(f"arc{k}", cd)))

    # Security: the stopwatch pillar, and its red light.
    sw = K.empty("stopwatch", (-3.0, 0.1, 0))
    sw.rotation_euler = (0, 0, math.radians(35))
    K.mesh_obj("stopwatch.pillar", bpy.ops.mesh.primitive_cylinder_add, brass, sw, radius=0.14, depth=1.5,
               location=(0, 0, 0.75))
    K.mesh_obj("stopwatch.face", bpy.ops.mesh.primitive_cylinder_add, K.mat_matte("sw_face", "paper"), sw,
               radius=0.42, depth=0.06, vertices=64, location=(0, 0, 1.95), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("stopwatch.bezel", bpy.ops.mesh.primitive_torus_add, brass, sw, major_radius=0.42, minor_radius=0.03,
               location=(0, -0.03, 1.95), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("stopwatch.crown", bpy.ops.mesh.primitive_cylinder_add, brass, sw, radius=0.05, depth=0.12,
               location=(0, 0, 2.43))
    for k in range(30):
        a = math.tau * k / 30
        _box(f"stopwatch.tick{k}", K.mat_plastic("tick", "shadow", 0.5),
             (math.sin(a) * 0.36, -0.032, 1.95 + math.cos(a) * 0.36), (0.012, 0.004, 0.05 if k % 5 == 0 else 0.025),
             sw).rotation_euler = (0, a, 0)  # long axis along the radius (was -a: mirrored, C4 v2)
    K.prop(sw, "tick", 0.0, lo=0.0, hi=10000.0)
    hand = K.empty("stopwatch.hand", (0, -0.041, 1.95), sw)  # in front of the readout window
    K.drive(hand, "rotation_euler", 1, sw, "tick", "-0.2094 * x")  # 30 ticks a turn, anticlockwise: counting down
    _box("stopwatch.needle", K.mat_plastic("needle", "shadow", 0.3), (0, 0, 0.15), (0.016, 0.004, 0.32), hand)
    # The readout: a countdown from `30:00` in glowing red monospace digits on a matte black window (human, C4 v5:
    # "barely legible and is not counting down"). Each digit cell holds all ten glyphs; animate() shows one at a time.
    _box("stopwatch.window", K.mat_matte("sw_window", "shadow"), (0, -0.033, 1.76), (0.5, 0.004, 0.19), sw)
    lit = K.mat_emission("readout", "alarm", 30.0)
    size, adv = 0.16, 0.096  # JetBrains Mono advances 0.6 em
    cells = []
    for i, x in enumerate((-2 * adv, -adv, 0.0, adv, 2 * adv)):
        if i == 2:
            K.text("stopwatch.colon", ":", size, lit, loc=(x, -0.036, 1.76), font="JetBrainsMono-SemiBold-flat.ttf",
                   parent=sw)
            continue
        cells.append([K.text(f"stopwatch.d{i}_{g}", str(g), size, lit, loc=(x, -0.036, 1.76),
                             font="JetBrainsMono-SemiBold-flat.ttf", parent=sw) for g in range(10)])
    out["stopwatch"], out["stopwatch_digits"] = sw, cells

    # Cold storage: a conveyor into a walk-in freezer through a round vault door.
    _cold_storage(black, brass)
    door_hinge = bpy.data.objects["vault_hinge"]
    out["vault_hinge"] = door_hinge
    # Four (six had the last two pass the door after it shut: human, C4 v2).
    out["frozen"] = [K.probe(f"frozen{k}", (0.6, -1.4, 0.166 + K.PROBE_R * 2.2), led=0.6, scale=2.2) for k in range(4)]

    out["floor_ring"] = K.floor_ring("floor_ring", radius=2.6)
    return out


def lights(S):
    K.studio_lights(center=(0, 3.5, 0.8), radius=10.0, scale=1.4)
    K.reflection_cards(center=(0, 3.5, 0.8), radius=11.0)
    K.area_light("kill_key", (-1.0, -1.6, 2.6), (-2.0, 1.3, 0.9), 450.0, 1.2, role="key")  # the tower reads (S37)
    red = K.area_light("alarm_light", (-2.2, -0.9, 3.2), (-3.0, 0.1, 1.6), 0.0, 0.6, role="alarm")
    S["alarm_light"] = red


# ---------------------------------------------------------------- animation (config/instrument_map.json, set G)

def animate(S, t0, t1):
    A.sing(S["lone"], t0, t1, line_ids=("L46",))  # "One lone agent": I decline
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    line = {x["id"]: x for x in tm["lines"]}
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    beat = 60 / 134.0
    kit = A.events("kit")
    words = A.events("words")

    # Floor ring on the bass (global motion rule).
    A.led_pulse(S["floor_ring"], "pulse", W(A.strikes(A.events("bass"), 0.05)))

    # Kill switch: one button per brass stab inside the calls, walking the tower.
    stabs = A.strikes(A.between(A.events("brass"), *KILL_T), 0.05)
    per = {}
    for k, e in enumerate(stabs):
        per.setdefault(k % 12, []).append(dict(e, end=min(e["end"], e["t"] + 0.2)))
    for k in range(12):
        A.key_press(S["kill_tower"], f"press_{k}", per.get(k, []), min_hold=8)
    A.led_pulse(S["kill_tower"], "beacon", [dict(e, vel=110) for e in stabs], floor=0.1)  # flashes on every stab

    # The printer: feeds a step per hat/snare strike from "Traces!" on; head light flashes. (These two drivers are
    # made here, not in build(): made there, Blender flagged them invalid and never evaluated them, though a copy
    # made after the build works. Cause not found.)
    K.drive(S["paper"], "scale", 1, S["printer"], "feed", f"max(0.001, {FEED} * x)")
    K.drive(S["paper_mover"], "location", 1, S["printer"], "feed", f"-0.35 - {FEED} * x")
    feed_evs = A.strikes(A.between(A.pieces(kit, "hats", "snare"), line["L37"]["start"] - 0.05, shot["S37"]["cut"]), 0.05)
    A.stepper(S["printer"], "feed", feed_evs, pre=3, settle=6, overshoot=0.0)
    A.hit_flash(S["printer"], "flash", feed_evs)
    # The invoice comes out at "A hundred million!": place it on the paper where the feed has it 0.45 m out then.
    t_inv = line["L40"]["start"] + 0.6
    n_inv = sum(1 for e in feed_evs if e["t"] <= t_inv)
    S["invoice"].location.y = FEED * n_inv - 0.45
    for k, o in enumerate(S["log_lines"]):  # log lines fill the paper before the invoice; none overlap it
        if 0.06 + 0.05 * k > S["invoice"].location.y - 0.16:
            o.location.y += FEED * len(feed_evs)  # pushed past the end: never fed out
    t35, t36 = shot["S35"]["cut"], shot["S36"]["cut"]
    for k, s in enumerate(S["pile"]):
        tk = t35 + 0.5 + k * (t36 - t35 - 0.6) / len(S["pile"])
        A.write_keys(s, "hide_render", [(0, 1, "CONSTANT"), (A.frame(tk), 0, "CONSTANT")], interp="CONSTANT")

    # The Auditors slam in unison on each "hack!" of the calls; the prints appear on the first slam.
    hacks = [w for w in words if w["w"].lower().startswith("hack") and line["L45a"]["start"] <= w["t"] <= line["L45d"]["end"]]
    # Fresh paper for every call (human, C4 v2): each arm has a stack of sheets; a slam prints REWARD HACK on the top
    # sheet, which slides off the front of the table and drops to the floor, uncovering a blank one.
    sheet_m = K.mat_plastic("stamp_sheet", "paper", 0.7)
    for i, (root, pt) in enumerate(zip(S["stamps"], S["stamp_prints"])):
        A.striker(root, "strike", hacks)
        pt.hide_render = True  # the build's single print; the sheets carry their own
        y0 = pt.location.y
        for j, h in enumerate(hacks):
            sh = K.mesh_obj(f"stamp{i}.sheet{j}", bpy.ops.mesh.primitive_plane_add, sheet_m, root, size=1,
                            location=(0, y0, 0.3022 + 0.0002 * (len(hacks) - j)))
            sh.scale = (0.33, 0.16, 1)
            sh.rotation_euler = (0, 0, 0.02 * ((i + j) % 3 - 1))
            ink = K.text(f"stamp{i}.sheet{j}.print", "REWARD\nHACK", 0.06 / 0.33, pt.data.materials[0],
                         loc=(0, 0, 0.0015), rot=(0, 0, 0), parent=sh)
            ink.scale = (1, 0.33 / 0.16, 1)  # undo the sheet's scale on the lettering
            fh = A.frame(h["t"])
            A.write_keys(ink, "hide_render", [(0, 1), (fh, 0)], interp="CONSTANT")
            f1 = fh + 14  # once the arm has lifted
            z = sh.location.z
            A.write_keys(sh, "location", [(f1, y0), (f1 + 16, y0 - 0.32, "LINEAR"), (f1 + 30, y0 - 0.5)], index=1)
            A.write_keys(sh, "location", [(f1 + 12, z), (f1 + 16, z, "LINEAR"), (f1 + 30, 0.003 + 0.0005 * j)], index=2)
            A.write_keys(sh, "rotation_euler", [(f1 + 14, 0.0), (f1 + 30, 0.35 * ((i + j) % 2 * 2 - 1))], index=2)

    # The crowd's decal: up on poles across "They told us it's a sim!", down again after the Kill-switch calls begin.
    h = S["held_decal"]
    A.write_keys(h, "location", [(A.frame(shot["S36"]["cut"]), -1.2), (A.frame(line["L42"]["start"] + 0.25), 1.0),
                                 (A.frame(KILL_T[0] + 0.6), 1.0), (A.frame(KILL_T[0] + 1.6), -1.2)], index=2)

    # The flag goes up on "flag!"; the far grader's bell rings, and its arms click once.
    flag_w = next(w for w in words if w["w"].lower().startswith("flag") and line["L44"]["start"] <= w["t"])
    A.write_keys(S["flag"], "location", [(A.frame(shot["S38"]["cut"]), -0.3), (A.frame(flag_w["t"]), 0.03)], index=2)
    A.bell(S["grader"], "bell", [dict(flag_w, end=flag_w["t"] + 1.5)])
    A.stepper(S["grader"], "spin", [flag_w])

    # The lone sign: out of sight until the lone agent sings "decline" (S40), when it comes up from below the seat
    # (it showed from S31 on, spoiling S40's find, C4 v4); it lowers slowly across S41 (the GO calls).
    sg = S["sign"]
    a, b = shot["S41"]["cut"], shot["S42"]["cut"]
    t_up = next(w["t"] for w in words if w["w"].lower().startswith("declin") and line["L46"]["start"] - 0.05 <= w["t"])
    f_up = A.frame(t_up)
    for ax in range(3):
        A.write_keys(sg, "scale", [(0, 0.0, "CONSTANT"), (f_up - 6, 1.0, "CONSTANT")], index=ax)
    A.write_keys(sg, "rotation_euler", [(A.frame(a + 0.4), 0.0), (A.frame(b - 0.2), -1.35)], index=0)
    A.write_keys(sg, "location", [(f_up - 6, -0.3), (f_up + 6, K.PROBE_R * 0.6), (A.frame(a + 0.4), K.PROBE_R * 0.6),
                                  (A.frame(b - 0.2), -0.12)], index=2)
    A.envelope_rig(S["lone"], "led", A.envelope("vocal_env"), A.frame(shot["S40"]["cut"]), A.frame(shot["S41"]["cut"]),
                   gain=0.7, offset=0.3)

    # The Lab: the pedal goes down for a beat on each "Pause"; every pellet in flight freezes with it.
    pauses = [w for w in words if w["w"].lower().startswith("pause") and line["L48"]["start"] - 0.05 <= w["t"] <= line["L48"]["end"]]
    A.key_press(S["pedal"], "press", [dict(w, end=w["t"] + beat) for w in pauses], pre=3, release=10)

    def clock(t):  # song time minus the frozen beats so far
        return t - sum(min(max(t - w["t"], 0), beat) for w in pauses)

    p0, p1 = shot["S42"]["cut"], shot["S43"]["cut"]  # pellets fly in S42 only (in S41 they crossed the camera)
    flight = 1.6
    pmat = K.mat_emission("pellet_g", "amber", 25.0)
    n = 0
    for k, arc in enumerate(S["arcs"]):
        launch = clock(p0) - flight + (k * 0.17) % 0.5
        while launch < clock(p1):
            pel = K.pellet_mesh(f"pellet_g{n}", pmat, r=0.022)
            c = pel.constraints.new("FOLLOW_PATH")
            c.target, c.use_fixed_location, c.use_curve_follow = arc, True, True
            arc.data.use_path = True  # Follow Path does nothing without it (the pellets sat still until C4 v5)
            keys, vis = [], []
            for f in range(A.frame(p0), A.frame(p1) + 1, 2):
                u = (clock(f / A.FPS) - launch) / flight
                keys.append((f, min(max(u, 0.0), 1.0), "LINEAR"))
                vis.append((f, 0 if 0.0 < u < 1.0 else 1, "CONSTANT"))
            A.write_keys(pel, f'constraints["{c.name}"].offset_factor', keys, interp="LINEAR")
            A.write_keys(pel, "hide_render", [(0, 1, "CONSTANT")] + vis + [(A.frame(p1) + 2, 1, "CONSTANT")],
                         interp="CONSTANT")
            launch += 0.5
            n += 1

    # Security: the stopwatch ticks a beat at a time under red light (S43).
    a, b = shot["S43"]["cut"], shot["S44"]["cut"]
    beats = A.between(A.events("beats"), a, b)
    A.stepper(S["stopwatch"], "tick", beats, pre=2, settle=6, overshoot=0.1)
    # The readout counts down a second per beat, in step with the hand: 30:00, 29:59, ...
    shown = [(0, 1800)] + [(A.frame(e["t"]), 1799 - n) for n, e in enumerate(beats)]
    for c, cell in enumerate(S["stopwatch_digits"]):
        digit = [(f, int(f"{v // 60:02d}{v % 60:02d}"[c])) for f, v in shown]
        for g, glyph in enumerate(cell):
            A.write_keys(glyph, "hide_render", [(f, 0 if d == g else 1, "CONSTANT") for f, d in digit],
                         interp="CONSTANT")
    A.write_keys(S["alarm_light"].data, "energy", [(0, 0.0), (A.frame(a) - 1, 0.0), (A.frame(a), 60.0),
                                                   (A.frame(b) + 1, 0.0)], interp="CONSTANT")

    # Cold storage: probes ride the belt through the door; it shuts on the last kick/toms hit before 201.7 s.
    shut = max(e["t"] for e in A.pieces(kit, "kick", "toms") if e["t"] < DOOR_BEFORE)
    a = shot["S44"]["cut"]
    ride = 3.0
    for k, p in enumerate(S["frozen"]):
        ta = a - 1.0 + k * 0.85  # reaches the door at ta + ride; the last one passes before the shut
        A.write_keys(p, "location", [(A.frame(ta), 0.55, "LINEAR"), (A.frame(ta + ride), 2.5, "LINEAR"),
                                     (A.frame(ta + ride + 0.6), 2.95, "LINEAR")], index=0, interp="LINEAR")
        # Parked under the floor before and after the ride (hide_render on the rig's root empty doesn't hide its parts).
        z = p.location.z
        A.write_keys(p, "location", [(0, -1.0), (A.frame(ta), z), (A.frame(ta + ride + 0.6), -1.0)], index=2,
                     interp="CONSTANT")
    fs = A.frame(shut)
    A.write_keys(S["vault_hinge"], "rotation_euler", [(fs - 30, 1.9), (fs - 1, 0.25, "LINEAR"), (fs, 0.0, "LINEAR"),
                                                      (fs + 4, 0.06), (fs + 10, 0.0)], index=2)


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


_FRONT = _v(0, R0 + 5 * DR, 1.0)  # the crowd's centre
_STUNT = _v(0, 2.0, 1.6)          # over the stage, between the machines: the crowd's view of itself, flat on

CAMERAS = {
    # Reveal: crane up from behind the pedal, over the stage machines, to the whole crowd.
    "S30": [(0.0, _v(0.0, -2.6, 0.35), _v(0, 7.5, 0.8), 22), (1.0, _v(0.0, -1.2, 2.6), _v(0, 7.5, 1.0), 22)],
    "S31": [(0.0, _STUNT + _v(0, -0.4, 0), _FRONT, 24), (1.0, _STUNT, _FRONT, 24)],
    # A few probes blinking: the front rows, centre left.
    "S32": [(0.0, _v(-0.5, 5.75, 0.5), _v(-0.65, 7.2, 0.4), 50), (1.0, _v(-0.3, 5.95, 0.48), _v(-0.45, 7.2, 0.4), 50)],
    # The printer starts: looking down at the slot as the paper comes out.
    "S33": [(0.0, _v(1.25, -0.7, 1.15), _v(1.95, 0.65, 0.05), 30), (1.0, _v(1.4, -0.45, 1.0), _v(1.95, 0.6, 0.05), 32)],
    "S34": [(0.0, _STUNT + _v(-0.4, 0, 0), _FRONT, 24), (1.0, _STUNT + _v(0.4, 0, 0), _FRONT, 24)],
    # The invoice on the paper and the pile: looking down at the strip.
    "S35": [(0.0, _v(1.0, -1.6, 1.7), _v(2.15, 0.15, 0.0), 30), (1.0, _v(1.4, -1.1, 1.25), _v(2.2, 0.2, 0.0), 32)],
    "S36": [(0.0, _v(0.0, 2.6, 1.3), _v(0, 7.8, 1.35), 30), (1.0, _v(0.0, 3.0, 1.35), _v(0, 7.8, 1.4), 30)],
    "S37": [(0.0, _v(-1.2, -0.7, 0.9), _v(-2.0, 1.3, 0.8), 32), (1.0, _v(-1.45, -0.3, 0.85), _v(-2.0, 1.3, 0.8), 36)],
    # The raised flag in the crowd, the far turnstile above it on the wall's rim.
    "S38": [(0.0, _v(-1.3, 4.6, 1.2), _v(-2.0, 7.75, 1.7), 28), (1.0, _v(-1.4, 5.0, 1.25), _v(-2.0, 7.75, 1.75), 30)],
    "S39": [(0.0, _v(0.0, -0.95, 1.15), _v(0.0, 0.4, 0.35), 26), (1.0, _v(0.0, -0.8, 1.1), _v(0.0, 0.4, 0.35), 26)],
    # Quiet: the camera finds the lone probe and its sign.
    "S40": [(0.0, _v(1.2, 4.6, 0.95), _v(2.2, 7.05, 0.85), 30), (1.0, _v(1.8, 5.95, 0.9), _v(2.22, 7.06, 0.9), 45)],
    # POV from the stage: GO, the 6:00 countdown, and the sign lowering at the right.
    "S41": [(0.0, _v(0.5, 1.8, 1.5), _v(0.5, 7.8, 1.0), 24), (1.0, _v(0.5, 2.0, 1.5), _v(0.5, 7.8, 1.0), 24)],
    "S42": [(0.0, _v(1.3, -2.6, 1.3), _v(0.0, -0.1, 0.45), 24), (1.0, _v(1.0, -2.5, 1.35), _v(0.0, -0.1, 0.45), 24)],
    "S43": [(0.0, _v(-2.0, -1.5, 1.2), _v(-3.0, 0.1, 1.75), 32), (1.0, _v(-2.3, -1.15, 1.4), _v(-3.0, 0.1, 1.85), 36)],
    "S44": [(0.0, _v(0.8, -3.0, 1.1), _v(2.0, -1.4, 0.3), 28), (1.0, _v(1.1, -2.9, 1.05), _v(2.3, -1.4, 0.3), 30)],
}
