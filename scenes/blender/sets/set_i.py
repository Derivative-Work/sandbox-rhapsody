"""Set I, Cold Storage (brief, "Sets → I"; outro and coda). Grey-box for the C4 animatic.

Contents, as the brief lists them:
- inside the freezer: frosted pale walls, one work light hanging over the middle, rows of sleeping probes on shelves
  along both side walls (LEDs breathing low with the backing vocals);
- the music box from set A on a crate, the only instrument left, playing the piano's top line;
- the lead probe beside it, amber LED singing with the vocal; its right arm is folded over the flag it held all along
  (S60 opens it);
- the frost wall (S61): frost on the back wall traces the map of everything it reached -- four regions, eleven nodes,
  the corporate VPN -- word by word, then melts;
- the split-flap scoreboard: clacks through its digits on the piano notes and lands on 0 at each "zero";
- the sleeping machines of the coda (S64b, as sung): two mallet pads, a grader turnstile, a rack of blades and the
  floor ring, frosted over until the band returns; they shake the frost off and play the coda, then everything powers
  down one by one, the lead probe last: its amber LED fades on the SIGTERM (S65; the CRT collapse is an edit effect).
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import sr_anim as A
import sr_kit as K

WALL_Y, SIDE_X = 3.0, 3.6
SHELF_Z = (0.3, 0.8, 1.3)
PER_ROW = 10
BOARD = Vector((-1.6, WALL_Y - 0.06, 1.45))
MAP = Vector((1.0, WALL_Y - 0.03, 1.3))
LEAD_CRATE = 0.09  # the lead stands on a low crate: its folded hand (and the flag) would sit below the floor
LEAD = Vector((0.42, -0.32, LEAD_CRATE + K.PROBE_R * 2.0))
CELLS = 3
GLYPHS = "0123456789 "


def _box(name, mat, parent, loc, scale, bev=0.0):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc)
    o.scale = scale
    if bev:
        K.bevel(o, bev, 2)
    return o


def _drive_vars(target, path, expr, index=None, **vars_):
    """target[path] = expr over several custom-property variables: name=(owner object, property)."""
    fc = target.driver_add(path) if index is None else target.driver_add(path, index)
    d = fc.driver
    d.type = "SCRIPTED"
    for n, (owner, key) in vars_.items():
        v = d.variables.new()
        v.name, v.targets[0].id_type, v.targets[0].id, v.targets[0].data_path = n, "OBJECT", owner, f'["{key}"]'
    d.expression = expr


def _flag(name, parent, loc, size, mat_pole, mat_flag, rot=(math.pi / 2, 0, 0), grip=0.5):
    """A small flag on a pole along its local +Y; `grip` = where along the pole the root (the hand) holds it."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = rot
    _box(f"{name}.pole", mat_pole, root, (0, size * (0.5 - grip), 0), (size * 0.08, size, size * 0.02))
    bpy.ops.mesh.primitive_plane_add(size=1)
    pen = bpy.context.active_object
    pen.name = f"{name}.pennant"
    me = pen.data
    me.vertices[0].co, me.vertices[1].co, me.vertices[2].co, me.vertices[3].co = \
        (0, 0, 0), (size * 0.7, -size * 0.2, 0), (0, -size * 0.4, 0), (0, -size * 0.4, 0)
    pen.parent = root
    pen.location = (size * 0.04, size * (1.0 - grip), 0.002)
    pen.data.materials.append(mat_flag)
    return root


def _cymbal(name, loc, r, height, hat=False):
    """A cymbal machine on a stand (grey-box). Crash: a brass disc tilted on its stand; "bell" (sr_anim.bell) rocks
    it. Hi-hat: two discs; "strike" (sr_anim.striker) drops the top disc onto the bottom one (0 open, -1 lifted,
    1 closed). "flash" (sr_anim.hit_flash) lights the rim on every hit."""
    root = K.empty(name, loc)
    K.prop(root, "flash", 0.0)
    K.prop(root, "strike" if hat else "bell", 0.0, lo=-1.0, hi=1.0)
    chrome = K.mat_chrome(f"{name}.stand")
    brass = K.mat_plastic(f"{name}.brass", "brass", 0.25)
    K.mesh_obj(f"{name}.stand", bpy.ops.mesh.primitive_cylinder_add, chrome, root, radius=0.012, depth=height,
               location=(0, 0, height / 2))
    K.mesh_obj(f"{name}.foot", bpy.ops.mesh.primitive_cylinder_add, chrome, root, radius=0.12, depth=0.012,
               location=(0, 0, 0.006))
    rim_m = K.mat_emission(f"{name}.rim", "amber", 50.0, root, "flash", floor=0.0)

    def disc(nm, parent, z, flip=False):
        d = K.mesh_obj(nm, bpy.ops.mesh.primitive_cone_add, brass, parent, radius1=r, radius2=r * 0.18,
                       depth=r * 0.14, vertices=48, location=(0, 0, z), rotation=(math.pi if flip else 0, 0, 0))
        K.smooth(d)
        K.mesh_obj(f"{nm}.rim", bpy.ops.mesh.primitive_torus_add, rim_m, parent, major_radius=r,
                   minor_radius=0.006, location=(0, 0, z - (r * 0.07 if not flip else -r * 0.07)))
        return d

    piv = K.empty(f"{name}.pivot", (0, 0, height), root)
    if hat:
        disc(f"{name}.bottom", root, height - 0.026, flip=True)
        K.drive(piv, "location", 2, root, "strike", f"{height} + 0.06 * (1 - max(x, 0)) - 0.05 * min(x, 0)")
        disc(f"{name}.top", piv, 0.0)
    else:
        piv.rotation_euler = (0.2, 0, 0)
        K.drive(piv, "rotation_euler", 0, root, "bell", "0.2 + 0.35 * x")
        disc(f"{name}.disc", piv, 0.0)
    return root


def _curve(name, pts, bevel, mat, parent, cyclic=False):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = bevel
    cd.bevel_resolution = 3
    sp = cd.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = cyclic
    cd.materials.append(mat)
    o = K.link(bpy.data.objects.new(name, cd))
    o.parent = parent
    return o


def build():
    K.floor()
    out = {}
    frost = K.mat_plastic("frost_wall", "lab", 0.75)
    frost_shell = K.mat_acrylic("frost_shell", "glass", alpha=0.75, emit=0.15)
    dark = K.mat_plastic("i_dark", "lab_dark", 0.3)
    chrome = K.mat_chrome("i_chrome")

    # The freezer: back and side walls, pale and rough with frost; a ceiling so the work light is the only light.
    _box("wall_back", frost, None, (0, WALL_Y + 0.05, 1.6), (2 * SIDE_X + 0.2, 0.1, 3.2))
    for sx in (-1, 1):
        _box(f"wall_side{sx}", frost, None, (sx * (SIDE_X + 0.05), 0.0, 1.6), (0.1, 2 * WALL_Y + 0.2, 3.2))
    _box("ceiling", dark, None, (0, 0, 3.25), (2 * SIDE_X + 0.2, 2 * WALL_Y + 0.2, 0.1))
    _box("frost_floor", K.mat_plastic("frost_floor", "horizon", 0.5), None, (0, 0.4, 0.004), (4.4, 4.2, 0.008))
    # One work light, hanging over the music box: cord, shade, bulb.
    _box("lamp.cord", dark, None, (0, 0, 2.85), (0.01, 0.01, 0.75))
    K.mesh_obj("lamp.shade", bpy.ops.mesh.primitive_cone_add, K.mat_metal("shade", "chrome", 0.3), None, radius1=0.22,
               radius2=0.05, depth=0.18, location=(0, 0, 2.4))
    K.mesh_obj("lamp.bulb", bpy.ops.mesh.primitive_uv_sphere_add, K.mat_emission("bulb", "key", 30.0), None,
               radius=0.05, location=(0, 0, 2.3))

    room = K.empty("room")
    for k, v in (("breath", 0.0), ("awake", 0.0)):
        K.prop(room, k, v)
    for r in range(6):
        K.prop(room, f"row{r}", 0.0)
    out["room"] = room

    # Rows of sleeping probes on shelves along both side walls, facing in. LED = power x max(breathing, awake + row
    # pulse): set per probe by a driver.
    sleepers = []
    for side, sx in enumerate((-1, 1)):
        for tier, z in enumerate(SHELF_Z):
            x = sx * (SIDE_X - 0.25)
            _box(f"shelf{side}_{tier}", K.mat_metal("shelf", "chrome", 0.25), None, (x, 0.75, z - 0.012),
                 (0.4, 4.0, 0.024))
            for k in range(PER_ROW):
                p = K.probe(f"sleeper{side}_{tier}_{k}", (x, -1.0 + 0.38 * k, z + K.PROBE_R * 2), led_role="lab_glow",
                            led=0.1, scale=2.0)
                p.rotation_euler = (0, 0, -sx * math.pi / 2)
                K.prop(p, "power", 1.0)
                _drive_vars(p, '["led"]', "p * max(0.3 * b, 0.4 * a + 0.6 * w)", p=(p, "power"), b=(room, "breath"),
                            a=(room, "awake"), w=(room, f"row{side * 3 + tier}"))
                sleepers.append(p)
    out["sleepers"] = sleepers

    # The music box on a crate in the middle, under the light.
    _box("mb_crate", K.mat_plastic("mb_crate", "lab", 0.3), None, (0, 0, 0.13), (0.42, 0.34, 0.26), 0.01)
    mb = K.music_box("musicbox", (0, 0, 0.26), scale=2.4)
    bpy.data.objects["musicbox.axle"].animation_data.drivers[0].driver.expression = "0.5236 * x"  # 1/12 turn a note
    out["musicbox"] = mb
    # The lead probe beside it on a low crate, holding the flag in its folded right arm.
    _box("lead_crate", K.mat_plastic("lead_crate", "lab", 0.3), None, (LEAD.x, LEAD.y + 0.02, LEAD_CRATE / 2),
         (0.17, 0.13, LEAD_CRATE), 0.008)
    lead = K.probe("lead", LEAD, led=0.6, scale=2.0)
    lead.rotation_euler = (0, 0, math.radians(-25))
    lead["arm_r"] = 0.0
    # The held flag stands upright in its hand at every arm pose: its root counter-rotates the shoulder, elbow and the
    # singing tilt (all about local X), so the pole never swings down through the floor (human, C4 v2: "the ending
    # flag is clipping through the floor"). Held near the pole's foot; furled against the pole until the arm opens.
    fl = _flag("held_flag", bpy.data.objects["lead.elbow_r"], (0, 0, -K.PROBE_R * 1.0), 0.1, chrome,
               K.mat_plastic("flag", "amber", 0.3), rot=(0, 0, 0), grip=0.12)
    _drive_vars(fl, "rotation_euler", "1.5708 + 1.35 + 0.3 * a + 0.16 * s", index=0, a=(lead, "arm_r"), s=(lead, "sing"))
    pen = bpy.data.objects["held_flag.pennant"]
    for ax in (0, 1):
        _drive_vars(pen, "scale", "0.12 + 0.88 * a", index=ax, a=(lead, "arm_r"))
    out["lead"] = lead

    # The sleeping machines of the coda, each under a frost shell ("frost{k}" objects, shaken off on waking).
    machines = {}
    machines["kick"] = K.mallet_pad("kick_pad", (-1.0, 0.75, 0), rot_z=math.radians(20), pad_role="lab_dark",
                                    pad_r=0.16, arm_len=0.4, glow_role="alarm")
    machines["snare"] = K.mallet_pad("snare_pad", (1.0, 0.75, 0), rot_z=math.radians(-20), pad_role="lab_dark",
                                     pad_r=0.12, glow_role="amber")
    machines["grader"] = K.turnstile("grader", (1.9, 1.7, 0), rot_z=math.radians(-30))
    blades = []
    for k in range(4):
        blades.append(K.blade(f"blade{k}", (-2.0 + 0.36 * k, 1.9, 0.0), width=0.3, height=0.062, depth=0.22))
    _box("blade_plinth", dark, None, (-1.46, 1.9, -0.0), (1.5, 0.3, 0.01))
    machines["blades"] = blades
    # The rest of the kit for the coda (human, C4 v2: "add more drums there too"): two toms behind the music box,
    # a hi-hat by the snare, a crash by the kick.
    machines["toms"] = [K.mallet_pad(f"tom{k}", (x, 1.3, 0), rot_z=math.radians(rz), pad_role="lab_dark", pad_r=pr,
                                     arm_len=0.36, glow_role="lab_glow")
                        for k, (x, rz, pr) in enumerate(((-0.42, 12, 0.15), (0.42, -12, 0.13)))]
    machines["hats"] = _cymbal("hats", (1.6, 0.25, 0), 0.17, 0.62, hat=True)
    machines["crash"] = _cymbal("crash", (-1.65, 0.3, 0), 0.26, 0.85)
    out["machines"] = machines
    out["floor_ring"] = K.floor_ring("floor_ring", radius=1.45)
    shells = []
    for k, (loc, sc) in enumerate((((-1.0, 0.85, 0.2), (0.45, 0.6, 0.42)), ((1.0, 0.85, 0.2), (0.4, 0.55, 0.42)),
                                   ((1.9, 1.7, 0.5), (0.55, 0.55, 1.05)), ((-1.46, 1.9, 0.07), (1.5, 0.32, 0.15)),
                                   ((-0.42, 1.4, 0.2), (0.42, 0.55, 0.42)), ((0.42, 1.4, 0.2), (0.4, 0.55, 0.42)),
                                   ((1.6, 0.25, 0.36), (0.42, 0.42, 0.74)), ((-1.65, 0.3, 0.5), (0.62, 0.62, 1.0)))):
        shells.append(_box(f"frost{k}", frost_shell, None, loc, sc, 0.03))
    out["shells"] = shells

    # The frost wall map: regions, nodes, links and the VPN mesh, all glowing pale with "glow" on its root.
    fm = K.empty("frost_map", MAP)
    K.prop(fm, "glow", 1.0)
    ice = K.mat_emission("frost_map", "rim", 6.0, fm, "glow")
    regions, nodes, links = [], [], []
    centers = [Vector((-0.75, 0, 0.25)), Vector((-0.1, 0, -0.35)), Vector((0.55, 0, 0.3)), Vector((1.0, 0, -0.3))]
    for r, c in enumerate(centers):
        pts = [c + Vector((math.cos(a) * 0.32 * (1 + 0.15 * math.sin(3 * a + r)), 0, math.sin(a) * 0.24))
               for a in [k * math.tau / 10 for k in range(10)]]
        o = _curve(f"region{r}", pts + pts[:1], 0.012, ice, fm)  # open (closed by repeating the start): a cyclic
        # spline ignores the bevel factors, so it couldn't trace itself
        o.data.bevel_factor_end = 0.0
        regions.append(o)
    node_pts = []
    for k in range(11):
        c = centers[k % 4]
        a = k * 2.399
        p = c + Vector((math.cos(a) * 0.17, -0.01, math.sin(a) * 0.12))
        node_pts.append(p)
        n = K.mesh_obj(f"fnode{k}", bpy.ops.mesh.primitive_uv_sphere_add, ice, fm, radius=0.035, location=p)
        n.scale = (0, 0, 0)
        nodes.append(n)
    for k in range(10):
        a, b = node_pts[k], node_pts[k + 1]
        o = _curve(f"flink{k}", [a, (a + b) / 2 + Vector((0, -0.01, 0.12)), b], 0.006, ice, fm)
        o.data.bevel_factor_end = 0.0
        links.append(o)
    vpn = []
    for k, (i, j) in enumerate(((0, 2), (1, 3), (0, 3), (2, 1))):
        a, b = centers[i], centers[j]
        o = _curve(f"fvpn{k}", [a, (a + b) / 2 + Vector((0, -0.01, 0.55)), b], 0.009, ice, fm)
        o.data.bevel_factor_end = 0.0
        vpn.append(o)
    out["frost_map"] = dict(root=fm, regions=regions, nodes=nodes, links=links, vpn=vpn)

    # The split-flap scoreboard on the back wall: SCORE over three flap cells.
    board = K.empty("scoreboard", BOARD)
    _box("board.back", dark, board, (0, 0, 0), (0.95, 0.06, 0.62), 0.01)
    K.text("board.label", "SCORE", 0.12, K.mat_plastic("board_ink", "paper", 0.4), loc=(0, -0.035, 0.2),
           rot=(math.pi / 2, 0, 0), parent=board)
    cells = []
    glyph_m = K.mat_plastic("glyph", "paper", 0.4)
    cell_m = K.mat_plastic("cell", "shadow", 0.3)
    for c in range(CELLS):
        x = -0.28 + 0.28 * c
        _box(f"cell{c}", cell_m, board, (x, -0.04, -0.07), (0.24, 0.02, 0.34))
        glyphs = []
        for g in GLYPHS:
            t = K.text(f"cell{c}.g{g if g != ' ' else 'blank'}", g, 0.3, glyph_m, loc=(x, -0.052, -0.07),
                       rot=(math.pi / 2, 0, 0), parent=board)
            glyphs.append(t)
        hinge = K.empty(f"cell{c}.hinge", (x, -0.056, -0.07), board)
        _box(f"cell{c}.flap", cell_m, hinge, (0, 0, 0.085), (0.235, 0.004, 0.165)).hide_render = True  # shown only
        # while it falls (see _board_keys)
        _box(f"cell{c}.seam", K.mat_plastic("seam", "lab_dark", 0.4), board, (x, -0.06, -0.07), (0.24, 0.003, 0.006))
        cells.append(dict(glyphs=glyphs, hinge=hinge))
    out["board"] = cells
    return out


def lights(S):
    """One work light over the music box, a cold faint fill: a freezer."""
    K.area_light("work", (0, 0, 2.25), (0, 0, 0), 180, 0.35, "key", shape="DISK")
    K.studio_lights(center=(0, 0.6, 0.8), radius=5.0, scale=0.12)


# ---------------------------------------------------------------- animation (config/instrument_map.json, set I)

def _digits(v):
    """Three cells for value v (None = blank), no leading zeros."""
    s = f"{v:>3d}" if v is not None else "   "
    return [GLYPHS.index(ch) for ch in s]


def _board_keys(S, changes):
    """changes = [(frame, value)], value shown from that frame; each change drops the cell's flap."""
    for c, cell in enumerate(S["board"]):
        shown = [(f, _digits(v)[c]) for f, v in changes]
        for gi, g in enumerate(cell["glyphs"]):
            A.write_keys(g, "hide_render", [(f, 0 if d == gi else 1, "CONSTANT") for f, d in shown],
                         interp="CONSTANT")
        keys, last = [], -100
        for f, _ in changes[1:]:
            if f - last < 4:
                continue
            keys += [(f - 3, 0.0, "LINEAR"), (f, -math.pi, "CONSTANT"), (f + 1, 0.0, "CONSTANT")]
            last = f
        if keys:
            A.write_keys(cell["hinge"], "rotation_euler", [(0, 0.0, "CONSTANT")] + keys, index=0)
            vis = [(0, 1, "CONSTANT")]
            for k in range(0, len(keys), 3):
                vis += [(keys[k][0], 0, "CONSTANT"), (keys[k + 1][0] + 1, 1, "CONSTANT")]
            A.write_keys(cell["hinge"].children[0], "hide_render", vis, interp="CONSTANT")


def animate(S, t0, t1):
    # The protagonist sings; the music box plays every piano note, the last chord ringing until the SIGTERM cuts it.
    A.sing(S["lead"], t0, t1)
    A.comb(S["musicbox"], A.between(A.events("piano"), t0 - 1, t1 + 1), cut_at=A.timing_map()["events"]["sigterm"])
    tm = A.timing_map()
    shots = {s["id"]: s for s in tm["shots"]}
    ev = tm["events"]
    f0, f1 = A.frame(t0 - 1), A.frame(t1 + 1)
    room = S["room"]
    piano = A.events("piano")
    coda0, coda1 = A.section("coda")
    final = ev["final_hits"]
    # The music box plays the piano's top line, a twelfth of a turn per note.
    A.stepper(S["musicbox"], "drum", A.between(A.top_line(A.pitch_range(piano, 60)), t0 - 1, t1 + 1), pre=4,
              settle=10, overshoot=0.0)
    # Sleepers breathe with the backing vocals; the coda wakes them ("awake"), rows flash on the kit, round robin.
    A.envelope_rig(room, "breath", A.envelope("backing_env") ** 1.5, f0, f1)
    A.write_keys(room, '["awake"]', [(A.frame(coda0) - 2, 0.0, "LINEAR"), (A.frame(coda0) + 20, 1.0, "LINEAR"),
                                     (A.frame(final + 1.0), 1.0, "LINEAR"), (A.frame(final + 3.0), 0.3, "LINEAR")])
    kit = A.between(A.strikes(A.events("kit"), 0.08), coda0, final + 0.5)
    for r in range(6):
        A.led_pulse(room, f"row{r}", kit[r::6])
    # Power down one by one after the final hits: the sleepers row by row toward the back, then the lead (S65).
    sl = S["sleepers"]
    off0, off1 = final + 1.5, ev["sigterm"] - 0.6
    order = sorted(range(len(sl)), key=lambda i: (-sl[i].location.y, sl[i].location.z))
    for n, i in enumerate(order):
        f = A.frame(off0 + (off1 - off0) * n / len(order))
        A.write_keys(sl[i], '["power"]', [(f, 1.0, "LINEAR"), (f + 6, 0.0, "LINEAR")], interp="LINEAR")
    # The lead probe sings (vocal envelope) and fades on the SIGTERM.
    lead = S["lead"]
    env = A.envelope("vocal_env")
    fs = A.frame(ev["sigterm"])
    keys = [(f, 0.45 + 0.55 * float(env[min(f, len(env) - 1)]), "LINEAR") for f in range(f0, min(f1, fs), 2)]
    keys += [(fs, 0.6, "LINEAR"), (fs + 4, 1.0, "LINEAR"), (fs + 30, 0.0, "LINEAR")]
    A.write_keys(lead, '["led"]', keys, interp="LINEAR")
    # S60: the lead opens its arm on "before": it was holding the flag all along.
    t_open = next(w["start"] for li in tm["lines"] if li["id"] == "L67" for w in li["words"] if w["w"].startswith("bef"))
    A.write_keys(lead, '["arm_r"]', [(0, 0.0), (A.frame(t_open) - 4, 0.0), (A.frame(t_open) + 26, 1.0)])
    # The coda machines: frost shells shake off as the band returns; they play the coda; they stop after the final hits.
    for k, sh in enumerate(S["shells"]):
        fw = A.frame(coda0) + 6 * k
        A.write_keys(sh, "location", [(fw - 6, sh.location.x), (fw - 3, sh.location.x + 0.02), (fw, sh.location.x - 0.02),
                                      (fw + 2, sh.location.x)], index=0)
        for ax in range(3):
            A.write_keys(sh, "scale", [(fw, sh.scale[ax]), (fw + 3, sh.scale[ax] * 1.08), (fw + 14, 0.0)], index=ax)
    M = S["machines"]
    kitc = A.between(A.events("kit"), coda0, final + 0.5)
    kicks, snares = A.strikes(A.pieces(kitc, "kick")), A.strikes(A.pieces(kitc, "snare"))
    A.striker(M["kick"], "strike", kicks)
    A.hit_flash(M["kick"], "flash", kicks)
    A.striker(M["snare"], "strike", snares)
    A.hit_flash(M["snare"], "flash", snares)
    A.stepper(M["grader"], "spin", snares)
    crashes = A.strikes(A.pieces(kitc, "crash"))
    A.bell(M["grader"], "bell", crashes)
    A.bell(M["crash"], "bell", crashes)
    A.hit_flash(M["crash"], "flash", crashes)
    hats = A.strikes(A.pieces(kitc, "hats"))
    A.striker(M["hats"], "strike", hats, wind=8, settle=16)
    A.hit_flash(M["hats"], "flash", hats)
    # Toms: one pitch in the drum events (GM 45), so the two toms take turns, hit by hit.
    toms = A.strikes(A.pieces(kitc, "toms"))
    for k, tom in enumerate(M["toms"]):
        A.striker(tom, "strike", toms[k::2])
        A.hit_flash(tom, "flash", toms[k::2])
    for k, b in enumerate(M["blades"]):
        env_b = A.envelope("vocal_env" if k % 2 else "backing_env") ** 2.0
        A.envelope_rig(b, "vent", env_b, A.frame(coda0), A.frame(final + 1.0))
        A.write_keys(b, '["led"]', [(A.frame(coda0) - 1, 0.05, "LINEAR"), (A.frame(coda0) + 10, 0.9, "LINEAR"),
                                    (A.frame(final + 1.5 + 0.4 * k), 0.9, "LINEAR"),
                                    (A.frame(final + 1.5 + 0.4 * k) + 8, 0.0, "LINEAR")], interp="LINEAR")
    bass = A.between(A.strikes(A.events("bass"), 0.05), coda0, final + 0.5)
    A.led_pulse(S["floor_ring"], "pulse", bass)
    # S61: the frost map traces word by word, then melts in the shot's last quarter.
    fm = S["frost_map"]
    words = {w["w"].lower().strip(".,"): w["start"] for li in tm["lines"] if li["id"] == "L69" for w in li["words"]}
    s61, s62 = shots["S61"]["cut"], shots["S62"]["cut"]
    t_reg = max(words["regions"], s61)
    for k, o in enumerate(fm["regions"]):
        ts = t_reg + 0.28 * k
        _grow(o.data, A.frame(ts), A.frame(ts + 0.5))
    for k, n in enumerate(fm["nodes"]):
        f = A.frame(words["eleven"] + (words["a"] - 0.2 - words["eleven"]) * k / 11)
        for ax in range(3):
            A.write_keys(n, "scale", [(0, 0.0, "CONSTANT"), (f, 0.0), (f + 5, 1.4), (f + 10, 1.0),
                                      (A.frame(s62 - 1.2), 1.0), (A.frame(s62 - 0.2), 0.0)], index=ax)
    for k, o in enumerate(fm["links"]):
        f = A.frame(words["eleven"] + 0.2 + (words["a"] - words["eleven"]) * k / 10)
        _grow(o.data, f, f + 12)
    for k, o in enumerate(fm["vpn"]):
        f = A.frame(words["corporate"] + 0.3 * k)
        _grow(o.data, f, f + 30)
    melt0 = s61 + 0.75 * (s62 - s61)
    for o in fm["regions"] + fm["links"] + fm["vpn"]:  # the lines thaw away from their starts
        o.data.bevel_factor_start = 0.0
        o.data.keyframe_insert("bevel_factor_start", frame=A.frame(melt0))
        o.data.bevel_factor_start = 1.0
        o.data.keyframe_insert("bevel_factor_start", frame=A.frame(s62 - 0.1))
    A.write_keys(fm["root"], '["glow"]', [(A.frame(melt0), 1.0, "LINEAR"), (A.frame(s62 - 0.1), 0.0, "LINEAR")],
                 interp="LINEAR")
    A.write_keys(fm["root"], "location", [(A.frame(melt0), MAP.z), (A.frame(s62), MAP.z - 0.12)], index=2)
    # The scoreboard: shows 0; clacks through digits on the piano notes of "and the score went up by..." and lands on
    # 0 on "zero"; again on "...zero"; and it jolts back to 0 on each "Zero" of the coda.
    zeros = [w["start"] for li in tm["lines"] if li["id"] in ("L71", "L72", "L73", "L74") for w in li["words"]]
    changes = [(0, 0)]
    clack_from = [shots["S62"]["cut"], shots["S64"]["cut"]]
    n = 0
    for z in zeros:
        lo = next((c for c in clack_from if c < z and z - c < 4.0), z - 0.6)
        notes = A.between(A.strikes(piano, 0.08), lo, z - 0.05)
        if not notes:
            notes = [{"t": z - 0.3}, {"t": z - 0.15}]
        for e in notes:
            n += 1
            changes.append((A.frame(e["t"]), (n * 389 + 127) % 1000))
        changes.append((A.frame(z), 0))
    _board_keys(S, sorted(changes))


def _grow(curve_data, fa, fb):
    curve_data.bevel_factor_end = 0.0
    curve_data.keyframe_insert("bevel_factor_end", frame=0)
    curve_data.keyframe_insert("bevel_factor_end", frame=fa)
    curve_data.bevel_factor_end = 1.0
    curve_data.keyframe_insert("bevel_factor_end", frame=fb)


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


_L = LEAD
CAMERAS = {
    # Frost, one work light, the music box playing: a slow push from the door to the box.
    "S59": [(0.0, _v(0.3, -4.6, 2.1), _v(0.0, 0.6, 0.7), 26), (1.0, _v(0.5, -1.35, 1.15), _v(0.2, -0.15, 0.22), 32)],
    # POV: looking down at its own folded arm, which opens on the flag.
    "S60": [(0.0, _L + _v(0.3, -0.85, 0.4), _L + _v(0.05, 0.0, 0.0), 40),
            (1.0, _L + _v(0.25, -0.6, 0.3), _L + _v(0.07, -0.05, 0.0), 42)],
    # The frost wall: the map traces itself, then melts.
    "S61": [(0.0, _v(1.0, -0.9, 1.25), MAP + _v(0.1, 0, 0), 30), (1.0, _v(1.0, 0.4, 1.3), MAP + _v(0.1, 0, 0), 32)],
    # The scoreboard clacks; lands on 0.
    "S62": [(0.0, _v(-1.3, 0.7, 1.35), BOARD, 35), (1.0, _v(-1.4, 1.1, 1.4), BOARD, 36)],
    "S63": [(0.0, _v(-1.5, 1.5, 1.45), BOARD, 40), (1.0, _v(-1.55, 1.75, 1.45), BOARD, 40)],
    # POV from the floor by the music box, up at the board (the reward meter is the HUD's).
    "S64": [(0.0, _L + _v(0.2, 0.0, 0.2), BOARD + _v(0, 0, -0.1), 26),
            (1.0, _L + _v(0.15, 0.2, 0.22), BOARD + _v(0, 0, -0.1), 28)],
    # The coda (human, C4 v2: "cuts closer to the instruments"): a setup per bar or two, every cut on a downbeat
    # (_coda_cuts below), then from the last chord (bar 186) the high view down on the comb with the singer.
    "S64b": None,
    "S65": [(0.0, _L + _v(0.12, -0.38, 0.14), _L + _v(0, 0, 0.03), 50),
            (1.0, _L + _v(0.1, -0.33, 0.12), _L + _v(0, 0, 0.03), 50)],
}


def _coda_cuts():
    """S64b as cuts on the coda's downbeats: [(bar, eye, target, lens, eye_end, target_end, lens_end), ...]; each
    setup runs to the next one's bar. Bar numbers are the timing map's."""
    tm = A.timing_map()
    sh = {s["id"]: s for s in tm["shots"]}
    a, b = sh["S64b"]["cut"], sh["S65"]["cut"]
    bar = {x["n"]: x["start"] for x in tm["bars"]}
    L = LEAD
    plan = [  # bar, subject: (eye, target, lens) at the start -> at the end
        (174, (L + _v(-0.22, -0.5, 0.12), L + _v(0, 0, 0.03), 50), (L + _v(-0.18, -0.42, 0.1), L + _v(0, 0, 0.03), 55)),
        (175, (_v(-0.55, 0.05, 0.42), _v(-1.0, 0.8, 0.2), 40), (_v(-0.62, 0.15, 0.38), _v(-1.0, 0.8, 0.2), 44)),  # kick
        (176, (_v(0.0, 0.25, 0.85), _v(0.0, 1.3, 0.18), 22), (_v(0.08, 0.35, 0.8), _v(0.0, 1.3, 0.18), 24)),  # toms
        (177, (_v(-1.0, -0.35, 0.95), _v(-1.65, 0.3, 0.8), 40), (_v(-1.1, -0.25, 0.9), _v(-1.65, 0.3, 0.8), 44)),  # crash
        (178, (_v(1.05, -0.3, 0.78), _v(1.6, 0.25, 0.6), 45), (_v(1.15, -0.25, 0.74), _v(1.6, 0.25, 0.6), 48)),  # hats
        (179, (_v(0.0, -3.2, 1.8), _v(0.0, 0.8, 0.4), 24), (_v(0.6, -3.0, 1.7), _v(0.0, 0.8, 0.4), 24)),  # wide: all
        (180, (_v(0.6, 0.1, 0.45), _v(1.0, 0.8, 0.2), 40), (_v(0.66, 0.2, 0.42), _v(1.0, 0.8, 0.2), 44)),  # snare
        (181, (_v(0.0, 2.5, 0.9), _v(0.0, 0.6, 0.15), 28), (_v(0.25, 2.45, 0.85), _v(0.0, 0.6, 0.15), 28)),  # reverse
        (182, (_v(0.16, -0.58, 0.88), _v(0.0, -0.05, 0.45), 40), (_v(0.12, -0.5, 0.84), _v(0.0, -0.05, 0.45), 44)),  # comb
        (183, (_v(-0.4, 0.1, 0.42), _v(-0.75, 0.95, 0.2), 24), (_v(-0.36, 0.14, 0.4), _v(-0.75, 0.95, 0.2), 26)),  # final hits
        (184, (_v(2.4, -1.6, 1.3), _v(-0.5, 1.0, 0.6), 28), (_v(1.4, -1.5, 1.1), _v(-0.2, 0.6, 0.5), 30)),  # power-down
        (186, (_v(0.5, -1.35, 1.15), _v(0.2, -0.15, 0.24), 44), (_v(0.48, -1.2, 1.05), _v(0.21, -0.16, 0.24), 48)),
    ]
    u = lambda t: (t - a) / (b - a)  # noqa: E731
    segs = []
    for k, (n, (e0, t0, l0), (e1, t1, l1)) in enumerate(plan):
        ua = 0.0 if k == 0 else u(bar[n])
        ub = 1.0 if k + 1 == len(plan) else u(bar[plan[k + 1][0]]) - 1e-4
        segs.append([(ua, e0, t0, l0), (ub, e1, t1, l1)])
    return segs


CAMERAS["S64b"] = _coda_cuts()
