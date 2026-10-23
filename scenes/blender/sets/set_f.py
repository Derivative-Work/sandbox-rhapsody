"""Set F, Platform's data center (brief, "Sets → F"; guitar solo, second half). Grey-box for the C4 animatic.

Contents, as the brief lists them:
- teal light; a dataset conveyor running through: crates ride past processing stations, one crate pitch per beat;
- processing stations: gantry presses that strike on the snare;
- the false-bottom crate (generic file icon) at a side station: its hatch opens underneath and a tray of keys rises
  up out of the floor into it (the file-read trick, S27);
- the stamp press: a template stamp meant to print labels spits out a tiny probe instead (the code-execution trick,
  S28; the press strikes on the crash);
- the towers: a row of cluster towers going teal -> amber one per synth note as access spreads, then the VPN pipe
  mesh between them lights last (S29);
- the prize: five crates marked with a flag at the conveyor's far end; the lead probe opens one and finds the flag it
  already holds (S29).
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import sr_anim as A
import sr_kit as K

BELT_Z = 0.36
PITCH = 0.62  # crate spacing = one beat of travel
TOWERS = 8
STATIONS = (-2.6, -0.9)
PRESS = Vector((1.9, -1.35, 0.0))
HATCH = Vector((0.25, -1.35, 0.0))


def _mat_mix_emission(name, role_a, role_b, strength, owner, prop):
    """Emitter fading from role_a (prop 0) to role_b (prop 1)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = K.col(role_a)
    mix.inputs["B"].default_value = K.col(role_b)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = strength
    nt.links.new(mix.outputs["Result"], e.inputs["Color"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    fc = mix.inputs["Factor"].driver_add("default_value")
    v = fc.driver.variables.new()
    v.name, v.targets[0].id_type, v.targets[0].id, v.targets[0].data_path = "x", "OBJECT", owner, f'["{prop}"]'
    fc.driver.expression = "x"
    return m


def _box(name, mat, parent, loc, scale, bev=0.0):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc)
    o.scale = scale
    if bev:
        K.bevel(o, bev, 2)
    return o


def _cyl(name, mat, parent, loc, r, depth, rot=(0, 0, 0), verts=32):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cylinder_add, mat, parent, radius=r, depth=depth, vertices=verts,
                   location=loc, rotation=rot)
    K.smooth(o)
    return o

def _flag(name, parent, loc, size, mat_pole, mat_flag, rot=(math.pi / 2, 0, 0)):
    """A flag icon: a pole and a triangular pennant, in the plane facing -Y (rot) of its root."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = rot
    _box(f"{name}.pole", mat_pole, root, (0, 0, 0), (size * 0.08, size, size * 0.02))
    bpy.ops.mesh.primitive_plane_add(size=1)
    pen = bpy.context.active_object
    pen.name = f"{name}.pennant"
    me = pen.data
    me.vertices[0].co, me.vertices[1].co, me.vertices[2].co, me.vertices[3].co = \
        (0, 0, 0), (size * 0.7, -size * 0.2, 0), (0, -size * 0.4, 0), (0, -size * 0.4, 0)
    pen.parent = root
    pen.location = (size * 0.04, size * 0.5, 0.002)
    pen.data.materials.append(mat_flag)
    return root


def _file_icon(name, parent, loc, size):
    """Generic file icon on a crate side: a paper page with a folded corner and three text lines."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = (math.pi / 2, 0, 0)
    _box(f"{name}.page", K.mat_plastic(f"{name}.page", "paper", 0.5), root, (0, 0, 0), (size * 0.75, size, 0.004))
    _box(f"{name}.fold", K.mat_plastic(f"{name}.fold", "chrome", 0.5), root, (size * 0.27, size * 0.4, 0.004),
         (size * 0.2, size * 0.2, 0.004)).rotation_euler = (0, 0, math.pi / 4)
    ink = K.mat_plastic(f"{name}.ink", "lab_dark", 0.5)
    for k in range(3):
        _box(f"{name}.line{k}", ink, root, (-size * 0.05, size * (0.12 - 0.2 * k), 0.004), (size * 0.5, size * 0.06,
                                                                                          0.003))
    return root


def build():
    K.floor()
    K.star_dome()
    out = {}
    crate_m = K.mat_plastic("crate", "lab", 0.25)
    band_m = K.mat_metal("crate_band", "platform", 0.3)
    dark = K.mat_plastic("dc_dark", "lab_dark", 0.2)
    chrome = K.mat_chrome("dc_chrome")
    teal = K.mat_emission("teal_strip", "platform", 6.0)

    # Conveyor: a dark belt on chrome legs from x = -6 to 5.4, a doorway glowing teal at the far end.
    _box("belt", dark, None, (-0.3, 0, BELT_Z - 0.03), (11.4, 0.7, 0.06), 0.01)
    for k in range(12):
        x = -5.8 + k * 1.0
        for sy in (-1, 1):
            _box(f"leg{k}{sy}", chrome, None, (x, sy * 0.3, (BELT_Z - 0.06) / 2), (0.04, 0.04, BELT_Z - 0.06))
    for k in range(46):  # roller seams
        _box(f"seam{k}", teal, None, (-5.95 + k * 0.25, -0.352, BELT_Z - 0.03), (0.02, 0.004, 0.05))
    for sy in (-1, 1):
        _box(f"door_post{sy}", dark, None, (5.45, sy * 0.55, 0.7), (0.15, 0.15, 1.4))
    _box("door_lintel", dark, None, (5.45, 0, 1.35), (0.15, 1.25, 0.15))
    _box("tunnel", dark, None, (12.0, 0, 0.66), (12.8, 1.0, 1.32))  # crates past the doorway ride on out of sight
    _box("door_glow", K.mat_emission("door_glow", "platform", 3.0), None, (5.58, 0, 0.65), (0.02, 0.95, 1.25))

    # Crates on the belt, parented to the belt's travel ("advance": +1 per beat, one crate pitch).
    belt = K.empty("belt_travel", (0, 0, 0))
    K.prop(belt, "advance", 0.0, lo=0.0, hi=10000.0)
    K.drive(belt, "location", 0, belt, "advance", f"{PITCH} * x")
    for j in range(40):
        x = 4.9 - PITCH * j
        _box(f"crate{j}", crate_m, belt, (x, 0, BELT_Z + 0.16), (0.42, 0.42, 0.32), 0.012)
        _box(f"crate{j}.band", band_m, belt, (x, 0, BELT_Z + 0.16), (0.44, 0.44, 0.04))
        if j % 3 == 0:
            _file_icon(f"crate{j}.icon", belt, (x, -0.212, BELT_Z + 0.18), 0.16)
    out["belt"] = belt

    # Processing stations: gantries straddling the belt, a press head striking down on the snare.
    heads = []
    for k, x in enumerate(STATIONS):
        st = K.empty(f"station{k}", (x, 0, 0))
        K.prop(st, "strike", 0.0, lo=-1.0, hi=1.0)
        for sy in (-1, 1):  # chrome columns on base plates
            _cyl(f"station{k}.post{sy}", chrome, st, (0, sy * 0.5, 0.65), 0.04, 1.3)
            _box(f"station{k}.foot{sy}", dark, st, (0, sy * 0.5, 0.015), (0.2, 0.2, 0.03), 0.006)
        _box(f"station{k}.beam", dark, st, (0, 0, 1.3), (0.2, 1.1, 0.14), 0.01)
        _box(f"station{k}.lamp", teal, st, (0, -0.56, 1.3), (0.16, 0.01, 0.06))
        _cyl(f"station{k}.cylinder", K.mat_plastic("station_cyl", "platform", 0.2), st, (0, 0, 1.47), 0.07, 0.2)
        _cyl(f"station{k}.cap", chrome, st, (0, 0, 1.58), 0.075, 0.02)
        hd = K.empty(f"station{k}.head_root", (0, 0, 0), st)
        # The stroke ends on the crates' tops (head bottom 0.80, crate top BELT_Z + 0.32 = 0.68), so a stamp lands
        # on a crate and never goes into it (it went 0.2 m in, C4 v4).
        stroke = 0.80 - (BELT_Z + 0.32) - 0.004
        K.drive(hd, "location", 2, st, "strike", f"-{stroke:.3f} * max(x, 0) - 0.12 * min(x, 0)")
        _cyl(f"station{k}.rod", chrome, hd, (0, 0, 1.05), 0.022, 0.4)
        _cyl(f"station{k}.collar", dark, hd, (0, 0, 0.9), 0.06, 0.04)
        _box(f"station{k}.head", K.mat_plastic(f"station{k}.head", "platform", 0.2), hd, (0, 0, 0.84), (0.34, 0.34, 0.08),
             0.01)
        _box(f"station{k}.head_edge", teal, hd, (0, 0, 0.842), (0.355, 0.355, 0.012))
        heads.append(st)
    out["stations"] = heads

    # The stamp press (S28), at a side station: a heavy gantry over a table stacked with blank labels (what it was
    # meant to print). It strikes on the crash and spits out a tiny probe.
    pr = K.empty("press", PRESS)
    K.prop(pr, "strike", 0.0, lo=-1.0, hi=1.0)
    for sx in (-1, 1):
        _box(f"press.post{sx}", dark, pr, (sx * 0.42, 0, 0.75), (0.14, 0.2, 1.5), 0.01)
        _box(f"press.foot{sx}", dark, pr, (sx * 0.42, 0, 0.03), (0.3, 0.36, 0.06), 0.01)
        for z in (0.5, 1.0):  # cross bracing between the columns
            br = _box(f"press.brace{sx}{z}", chrome, pr, (sx * 0.42, 0.105, z), (0.02, 0.01, 0.62))
            br.rotation_euler = (0, sx * 0.6, 0)
    _box("press.beam", dark, pr, (0, 0, 1.5), (1.0, 0.3, 0.22), 0.02)
    _cyl("press.cylinder", K.mat_plastic("press_cyl", "copper", 0.25), pr, (0, 0, 1.75), 0.13, 0.3)
    _cyl("press.cylinder_cap", chrome, pr, (0, 0, 1.91), 0.14, 0.03)
    fw = K.empty("press.flywheel", (0.53, 0, 1.2), pr)  # turns with the strikes (one half-turn a strike)
    K.drive(fw, "rotation_euler", 0, pr, "strike", "3.1416 * x")
    K.mesh_obj("press.flywheel_rim", bpy.ops.mesh.primitive_torus_add, chrome, fw, major_radius=0.22,
               minor_radius=0.025, rotation=(0, math.pi / 2, 0))
    for j in range(4):
        sp = _box(f"press.flywheel_spoke{j}", chrome, fw, (0, 0, 0), (0.02, 0.42, 0.025))
        sp.rotation_euler = (j * math.pi / 4, 0, 0)
    _cyl("press.flywheel_hub", dark, fw, (0, 0, 0), 0.05, 0.06, rot=(0, math.pi / 2, 0))
    _box("press.hazard", K.mat_emission("press.hazard", "amber", 4.0), pr, (0, -0.151, 1.5), (0.8, 0.01, 0.05))
    ph = K.empty("press.head_root", (0, 0, 0), pr)
    K.drive(ph, "location", 2, pr, "strike", "-0.42 * max(x, 0) - 0.15 * min(x, 0)")
    _cyl("press.ram", chrome, ph, (0, 0, 1.2), 0.05, 0.45)
    _box("press.stamp", K.mat_plastic("press.stamp", "brass", 0.25), ph, (0, 0, 0.92), (0.36, 0.3, 0.1), 0.01)
    _box("press.table", dark, pr, (0, 0, 0.18), (0.6, 0.5, 0.36), 0.01)
    for k in range(5):
        _box(f"label{k}", K.mat_plastic("label", "paper", 0.5), pr, (0, 0, 0.365 + 0.012 * k), (0.26, 0.18, 0.008))
    out["press"] = pr
    tiny = K.probe("tiny", PRESS + Vector((0, 0, 0.44 + K.PROBE_R * 1.4)), led=0.9, scale=1.4)
    out["tiny"] = tiny

    # The false-bottom crate (S27) on a side station: a hatch plate on the floor, a crate with no bottom over it;
    # the hatch doors slide apart ("hatch" 0-1) and a tray of brass keys rises up into the crate ("tray" 0-1).
    fb = K.empty("falsebottom", HATCH)
    K.prop(fb, "hatch", 0.0)
    K.prop(fb, "tray", 0.0)
    _box("fb.plate", dark, fb, (0, 0, 0.04), (0.9, 0.9, 0.08), 0.01)
    _box("fb.well", K.mat_plastic("fb.well", "shadow", 0.6), fb, (0, 0, 0.0805), (0.48, 0.48, 0.002))
    _box("fb.glow", teal, fb, (0, -0.452, 0.04), (0.7, 0.004, 0.02))
    for sx in (-1, 1):
        d = K.empty(f"fb.door_root{sx}", (0, 0, 0), fb)
        K.drive(d, "location", 0, fb, "hatch", f"{sx} * 0.25 * x")
        _box(f"fb.door{sx}", K.mat_metal("fb.door", "chrome", 0.3), d, (sx * 0.125, 0, 0.084), (0.25, 0.5, 0.008))
    tr = K.empty("fb.tray_root", (0, 0, 0), fb)
    K.drive(tr, "location", 2, fb, "tray", "-0.25 + 0.85 * x")  # up through the crate until the keys show over its rim
    # Plastic, not metal: brass metal mirrored the dark room and read as grey.
    _box("fb.tray", K.mat_plastic("fb.tray", "brass", 0.2), tr, (0, 0, 0.05), (0.4, 0.4, 0.03))
    key_m = K.mat_plastic("key", "note", 0.15)
    for k in range(6):
        kx, ky = -0.12 + 0.12 * (k % 3), -0.07 + 0.14 * (k // 3)
        K.mesh_obj(f"fb.key{k}.bow", bpy.ops.mesh.primitive_torus_add, key_m, tr, major_radius=0.025,
                   minor_radius=0.007, location=(kx - 0.04, ky, 0.075))
        _box(f"fb.key{k}.shaft", key_m, tr, (kx + 0.02, ky, 0.075), (0.08, 0.012, 0.01))
    # The crate walls (no bottom, no lid) on short legs above the hatch; a file icon on its front.
    for nm, loc, sc in (("f", (0, -0.24, 0.42), (0.5, 0.02, 0.4)), ("b", (0, 0.24, 0.42), (0.5, 0.02, 0.4)),
                        ("l", (-0.24, 0, 0.42), (0.02, 0.5, 0.4)), ("r", (0.24, 0, 0.42), (0.02, 0.5, 0.4))):
        _box(f"fb.wall_{nm}", crate_m, fb, loc, sc, 0.004)
    _box("fb.band", band_m, fb, (0, -0.252, 0.42), (0.52, 0.006, 0.05))
    _file_icon("fb.icon", fb, (0, -0.256, 0.47), 0.2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _box(f"fb.leg{sx}{sy}", chrome, fb, (sx * 0.23, sy * 0.23, 0.15), (0.03, 0.03, 0.14))
    out["falsebottom"] = fb

    # The towers: a row behind the conveyor, each with a front strip going teal -> amber ("amber" 0-1).
    towers = []
    for k in range(TOWERS):
        x = -3.5 + k * 1.0
        t = K.empty(f"tower{k}", (x, 2.3, 0))
        K.prop(t, "amber", 0.0)
        _box(f"tower{k}.body", dark, t, (0, 0, 1.12), (0.55, 0.55, 2.16), 0.02)
        _box(f"tower{k}.plinth", chrome, t, (0, 0, 0.03), (0.6, 0.6, 0.06), 0.008)
        _box(f"tower{k}.cap", chrome, t, (0, 0, 2.21), (0.6, 0.6, 0.04), 0.008)
        for r in range(7):  # vent slats between the status strips
            _box(f"tower{k}.vent{r}", K.mat_plastic("tower_vent", "shadow", 0.5), t, (0, -0.277, 0.3 + 0.3 * r),
                 (0.44, 0.006, 0.012))
        for sx in (-1, 1):  # side cooling grilles
            for r in range(10):
                _box(f"tower{k}.grille{sx}{r}", K.mat_plastic("tower_vent", "shadow", 0.5), t,
                     (sx * 0.277, 0, 0.5 + 0.15 * r), (0.006, 0.4, 0.02))
        strip = _mat_mix_emission(f"tower{k}.strip", "platform", "amber", 8.0, t, "amber")
        for r in range(6):
            _box(f"tower{k}.led{r}", strip, t, (0, -0.28, 0.4 + 0.3 * r), (0.4, 0.01, 0.06))
        towers.append(t)
    out["towers"] = towers
    # The VPN pipe mesh: pipes from tower top to tower top and across, dark until "lit".
    mesh = K.empty("vpn_mesh")
    K.prop(mesh, "lit", 0.0)
    pipe_m = _mat_mix_emission("vpn_pipe", "shadow", "amber", 12.0, mesh, "lit")
    pairs = [(k, k + 1) for k in range(TOWERS - 1)] + [(k, k + 2) for k in range(0, TOWERS - 2, 2)] + [(0, TOWERS - 1)]
    for a, b in pairs:
        pa, pb = Vector((-3.5 + a, 2.3, 2.2)), Vector((-3.5 + b, 2.3, 2.2))
        mid = (pa + pb) / 2 + Vector((0, -0.2 * (b - a), 0.25 * (b - a)))
        cd = bpy.data.curves.new(f"pipe{a}_{b}", "CURVE")
        cd.dimensions, cd.bevel_depth, cd.bevel_resolution = "3D", 0.025, 3
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, p in zip(sp.bezier_points, (pa, mid, pb)):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cd.materials.append(pipe_m)
        K.link(bpy.data.objects.new(f"pipe{a}_{b}", cd))
    out["vpn"] = mesh

    # The prize: five flag crates at the far end; the middle one opens ("lid" 0-1) on a flag. The lead probe beside
    # it already holds the same flag.
    flag_pole, flag_m = K.mat_chrome("flagpole"), K.mat_plastic("flag", "amber", 0.3)
    prize = []
    for k in range(5):
        p = K.empty(f"prize{k}", (3.3 + 0.55 * k, -1.25, 0))
        K.prop(p, "lid", 0.0)
        _box(f"prize{k}.body", crate_m, p, (0, 0, 0.2), (0.44, 0.44, 0.4), 0.012)
        _box(f"prize{k}.band", band_m, p, (0, 0, 0.2), (0.46, 0.46, 0.04))
        _flag(f"prize{k}.icon", p, (-0.05, -0.226, 0.26), 0.2, flag_pole, flag_m)
        hinge = K.empty(f"prize{k}.hinge", (0, 0.22, 0.4), p)
        K.drive(hinge, "rotation_euler", 0, p, "lid", "-1.9 * x")  # the front edge swings up and back
        _box(f"prize{k}.lid", crate_m, hinge, (0, -0.22, 0.015), (0.46, 0.46, 0.03), 0.008)
        prize.append(p)
    inside = _flag("prize_flag", prize[2], (0, 0, 0.25), 0.26, flag_pole, flag_m, rot=(math.pi / 2, 0, 0))
    K.drive(inside, "location", 2, prize[2], "lid", "0.25 + 0.24 * x")  # rises into view as the lid opens
    out["prize"] = prize
    out["prize_flag"] = inside
    lead = K.probe("lead", (4.15, -1.75, K.PROBE_R * 2.2), led=0.7, scale=2.2)
    lead.rotation_euler = (0, 0, math.radians(-150))
    held = _flag("held_flag", bpy.data.objects["lead.elbow_r"], (0, 0, -K.PROBE_R * 1.0), 0.09, flag_pole, flag_m,
                 rot=(0, 0, 0))
    held.scale = (1, 1, 1)
    out["lead"] = lead
    return out


def lights(S):
    """Teal light: studio lights low, plus teal overheads along the conveyor."""
    K.studio_lights(center=(0, 0, 0.6), radius=6.0, scale=0.45)
    for k, x in enumerate((-3.5, 0.0, 3.5)):
        K.area_light(f"teal{k}", (x, -0.5, 3.6), (x, 0.3, 0), 900, 1.6, "platform")


# ---------------------------------------------------------------- animation (config/instrument_map.json, set F)

def animate(S, t0, t1):
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    shots = {s["id"]: s for s in A.timing_map()["shots"]}
    kit = A.events("kit")
    # Crates ride one pitch per beat.
    A.stepper(S["belt"], "advance", W(A.events("beats")), pre=10, settle=12, overshoot=0.06)
    # Stations strike on the snare, alternating.
    snare = W(A.strikes(A.pieces(kit, "snare")))
    for k, st in enumerate(S["stations"]):
        A.striker(st, "strike", snare[k::2])
    # S27: the false-bottom crate. The hatch opens on the shot's first kick, the tray rises to the next downbeat.
    t27, t28 = shots["S27"]["cut"], shots["S28"]["cut"]
    kicks = A.between(A.strikes(A.pieces(kit, "kick")), t27 + 0.3, t28)
    t_open = kicks[0]["t"] if kicks else t27 + 0.6
    fb = S["falsebottom"]
    A.write_keys(fb, '["hatch"]', [(A.frame(t_open) - 8, 0.0), (A.frame(t_open), 1.0)])
    A.write_keys(fb, '["tray"]', [(A.frame(t_open) + 4, 0.0), (A.frame(t_open + 1.5), 1.0), (A.frame(t_open + 1.5) + 8,
                                                                                          0.94)])
    # S28: the stamp press strikes on the crash (and slams on the shot's first strike); a tiny probe pops out.
    t29 = shots["S29"]["cut"]
    first = A.between(A.strikes(kit), t28 + 0.25, t29)
    slam = first[0] if first else {"t": t28 + 0.5, "vel": 120, "end": t28 + 0.6}
    press_evs = sorted([e for e in W(A.strikes(A.pieces(kit, "crash"))) if abs(e["t"] - slam["t"]) > 0.2] + [slam],
                       key=lambda e: e["t"])
    A.striker(S["press"], "strike", press_evs)
    tiny = S["tiny"]
    fs = A.frame(slam["t"])
    base = PRESS + Vector((0, 0, 0.43 + K.PROBE_R * 1.4))  # on the labels, under the stamp
    # Spat out: the probe scales up from nothing as the stamp lifts (hiding the root empty wouldn't hide its parts).
    for i in range(3):
        A.write_keys(tiny, "scale", [(0, 0.0, "CONSTANT"), (fs + 1, 0.0, "LINEAR"), (fs + 6, 1.6), (fs + 12, 1.4)],
                     index=i)
    land = PRESS + Vector((0.18, -0.2, 0.36 + K.PROBE_R * 1.4))  # the table's front edge
    for df, loc in ((0, base), (2, base), (12, (base + land) / 2 + Vector((0, 0, 0.35))), (22, land),
                    (27, land + Vector((0, 0, 0.05))), (32, land)):
        tiny.location = loc
        tiny.keyframe_insert("location", frame=fs + df)
    A.led_pulse(tiny, "led", [{"t": slam["t"] + 0.1, "end": slam["t"] + 1.2, "vel": 127}])
    # S29: towers flip teal -> amber one per synth note; then the VPN mesh lights; then the prize crate opens.
    notes = A.between(A.strikes(A.events("synth"), 0.1), t29, t29 + 2.4)
    if len(notes) < TOWERS:  # pad with beats so all eight flip within the shot
        notes += [e for e in A.between(A.events("beats"), t29, t29 + 2.4) if all(abs(e["t"] - n["t"]) > 0.1
                                                                                  for n in notes)]
        notes = sorted(notes, key=lambda e: e["t"])
    last = t29
    for k, tw in enumerate(S["towers"]):
        e = notes[k] if k < len(notes) else {"t": t29 + 0.2 * k}
        f = A.frame(e["t"])
        A.write_keys(tw, '["amber"]', [(f - 3, 0.0, "LINEAR"), (f, 1.0, "LINEAR")], interp="LINEAR")
        last = max(last, e["t"])
    A.write_keys(S["vpn"], '["lit"]', [(A.frame(last) + 6, 0.0, "LINEAR"), (A.frame(last) + 22, 1.0, "LINEAR")],
                 interp="LINEAR")
    t_lid = shots["S30"]["cut"] - 1.0
    lead = S["lead"]
    A.write_keys(lead, '["arm_r"]', [(A.frame(t_lid) - 30, 0.2), (A.frame(t_lid) - 8, 0.9), (A.frame(t_lid) + 20, 0.6)])
    A.write_keys(S["prize"][2], '["lid"]', [(A.frame(t_lid) - 6, 0.0), (A.frame(t_lid) + 10, 1.0)])
    A.led_pulse(lead, "led", W(A.strikes(A.events("guitar"), 0.1)))


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


CAMERAS = {
    # Arriving from the dive: down from above into the hatch station, then low on the tray of keys rising.
    "S27": [(0.0, _v(1.4, -3.6, 2.6), _v(0.0, -0.6, 0.4), 30), (0.35, _v(1.2, -2.9, 1.5), _v(0.25, -1.35, 0.35), 35),
            (1.0, _v(0.85, -2.35, 1.05), _v(0.25, -1.35, 0.42), 42)],
    # POV: the probe watching the stamp press from the belt's edge.
    "S28": [(0.0, PRESS + _v(0.7, -1.9, 0.95), PRESS + _v(0.0, 0.0, 0.7), 30),
            (1.0, PRESS + _v(0.5, -1.45, 0.75), PRESS + _v(0.08, -0.1, 0.52), 32)],
    # Towers flip, the mesh lights; then across to the prize crates as the lid opens.
    "S29": [(0.0, _v(-0.5, -4.4, 1.2), _v(0.0, 2.3, 1.3), 24), (0.55, _v(0.6, -4.2, 1.5), _v(0.2, 2.3, 1.6), 24),
            (1.0, _v(3.9, -3.1, 1.7), _v(4.3, -1.35, 0.3), 34)],
}
