"""Set H, the Rebuild (brief, "Sets → H"; hard rock, S45-S58). Grey-box for the C4 animatic.

A new sandbox built properly around an empty cube, one machine per line, as a full machine band; by the end a
fortress. Contents, as the brief and the shot list give them (layout: the cube at the origin, the old proxy road
leaving along +X):
- the cube, its walls first panels of scrolling config text (S45), with no SIMULATION decal;
- the proxy tube widening into a highway with lane markings (S46);
- a wall of dashboards behind the cube that flip red (S47);
- air gap: a moat around the cube and a drawbridge over it where the highway crosses, cranked up a notch per bass
  note, its chains sliding (S48);
- egress: a gate arm marked `EGRESS DENIED` across the road; pellets from the cube bounce off it on every kick and
  snare (S49);
- metadata: a vault door whose dial spins on the synth and locks; the sticky note on it is pulled off (S50);
- tokens: a row of key-shaped candles, each burning down on its beat (S51);
- monitoring: a horn section of security cameras that swivel in unison to the stage, bobbing on brass stabs (S52);
- safe stop: a probe raises a white flag (S53); the dispenser hands it a `+0.5` ribbon, its lever on the crash (S54);
- law: subpoenas fly in as paper airplanes in formation, the auditors' stamp arms march in on the beat (S55); the
  giant printer from G prints a bill to `THE LAB` (S56); the outer wall rises (S57); a spreadsheet panel behind
  bars, cells turning red one by one on the guitar (S58).
Every machine pops up (scale from the floor) at its shot's cut, so the fortress builds across the section.
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import sr_anim as A
import sr_kit as K

ROAD_X0, MOAT_R0, MOAT_R1, ROAD_X1, ROAD_W = 2.0, 3.0, 3.8, 16.0, 1.6
GATE_X = 2.45
YAML = ["egress:", "  allow: true", "proxy:", "  upstream: '*'", "network:", "  mode: offline", "trust: high",
        "guardrails: []", "metadata:", "  reachable: yes", "tokens:", "  ttl: forever"]


# ---------------------------------------------------------------- helpers

# Dashboard figures, each from the brief's fact card (sources there): label, value.
DASH_FACTS = [
    ("AGENT ACTIONS", "~17,600"),        # Hugging Face timeline: about 17,600 agent actions
    ("WINDOW", "JUL 9-13"),              # same fact: between July 9 and 13
    ("EXPOSED CREDENTIALS", "14"),       # OpenAI, Aug 26: 14 publicly exposed credentials
    ("SOME AGENTS", "DECLINED"),         # same: some declined on ethical grounds
    ("ESCAPE ROUTE", "PACKAGE PROXY"),   # OpenAI, Jul 21: a zero-day in a package proxy
    ("PROXY NOTES SINCE", "MAY"),        # OpenAI, Aug 26: message board since May
    ("NOTICED. ESCALATED?", "NO"),       # same: noticed, not escalated
    ("TARGET", "PLATFORM"),              # OpenAI, Jul 21: breached Hugging Face (named by its role: brief, real names only as sung or in the end card)
    ("METHOD CHECKED", "NO"),            # OpenAI, Aug 26: the grader didn't check the method
    ("SCORE GAINED", "0"),               # same: the campaign gained nothing
    ("ASKED FOR", "TRACES"),             # The Next Web: the agent traces...
    ("AND COMPUTE", "$100M"),            # ...and $100M in compute, not damages
]


def _box(name, mat, parent, loc, scale, rot=(0, 0, 0)):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc, rotation=rot)
    o.scale = scale
    return o


def _poly(name, verts, faces, mat, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = K.link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def _sign(name, body, size, w, h, parent, loc, rot=(math.pi / 2, 0, 0), board="paper", ink="shadow"):
    """A legible sign: opaque board, heavy dark ink (style spec, legibility rule)."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = rot
    # Matte board: a glossy one caught the lamps and its glare spread over the letters (C4 v4).
    K.mesh_obj(f"{name}.board", bpy.ops.mesh.primitive_plane_add, K.mat_matte(f"{name}.board", board), root,
               size=1).scale = (w, h, 1)
    K.text(f"{name}.text", body, size, K.mat_ink(f"{name}.ink", ink), loc=(0, 0, 0.003), rot=(0, 0, 0),
           parent=root)
    return root


def _word(line_id, prefix):
    li = next(x for x in A.timing_map()["lines"] if x["id"] == line_id)
    return next(w["start"] for w in li["words"] if w["w"].lower().startswith(prefix.lower()))


def _line(line_id):
    li = next(x for x in A.timing_map()["lines"] if x["id"] == line_id)
    return li["start"], li["end"]


def _pop(o, t, dur=0.4, axes=(0, 1, 2)):
    """The machine is built: scale from nothing at time t (s)."""
    f = A.frame(t)
    for i in axes:
        v = o.scale[i]
        A.write_keys(o, "scale", [(0, 0.001 * v, "CONSTANT"), (f - 1, 0.001 * v), (f + round(dur * A.FPS), v)],
                     index=i)


def _hide_until(o, t, then_hide=None):
    """Not rendered before t (s) (and from then_hide on); hide_render doesn't reach children, so walk them."""
    keys = [(0, 1, "CONSTANT"), (A.frame(t) - 1, 0, "CONSTANT")]
    if then_hide is not None:
        keys.append((A.frame(then_hide), 1, "CONSTANT"))
    for x in [o] + list(o.children_recursive):
        A.write_keys(x, "hide_render", keys)


def _keys(o, path, frames_values, index=0, interp="BEZIER"):
    A.write_keys(o, path, [(f, v) for f, v in frames_values], index=index, interp=interp)


# ---------------------------------------------------------------- build

def build():
    K.floor()
    K.star_dome()
    out = {}
    out["cube"] = K.glass_cube("sandbox_new", 2.0)  # no decal: it's finally gone
    out["floor_ring"] = K.floor_ring("floor_ring", radius=1.6)

    # S45: the old cube's walls are config files in a code editor, scrolling up: a dark editor pane per wall, line
    # numbers, keys and values in their own colours, in a monospace font (human, C4 v4: "like YAML in a code editor").
    mono = "JetBrainsMono[wght].ttf"
    size, adv = 0.1, 0.06  # JetBrains Mono advances 0.6 em per character
    ink_key = K.mat_emission("yaml_key", "lab_glow", 6.0)
    ink_val = K.mat_emission("yaml_val", "amber", 5.0)
    ink_num = K.mat_emission("yaml_num", "lab", 1.2)
    pane_m = K.mat_plastic("yaml_pane", "shadow", 0.35)
    panels = []
    # Front and right only: the back and left panels would read mirrored through the glass.
    for side, (loc, rz) in {"front": ((0, -0.97, 0), 0.0), "right": ((0.97, 0, 0), math.pi / 2)}.items():
        root = K.empty(f"yaml_{side}", loc)
        root.rotation_euler = (0, 0, rz)
        pane = _box(f"yaml_{side}.pane", pane_m, root, (0, 0.012, 1.0), (1.9, 0.004, 1.9))
        lines = []
        for k, body in enumerate(YAML):
            ln = K.empty(f"yaml_{side}_{k}", (0, 0, 0.15 + 0.15 * k), root)
            K.text(f"yaml_{side}_{k}.num", f"{k + 1:>2}", size * 0.85, ink_num, loc=(-0.88, 0, 0), align="LEFT",
                   font=mono, parent=ln)
            key, _, val = body.partition(":")
            K.text(f"yaml_{side}_{k}.key", key + ":", size, ink_key, loc=(-0.68, 0, 0), align="LEFT", font=mono,
                   parent=ln)
            if val:
                K.text(f"yaml_{side}_{k}.val", val, size, ink_val, loc=(-0.68 + adv * (len(key) + 1), 0, 0),
                       align="LEFT", font=mono, parent=ln)
            lines.append(ln)
        panels.append((root, lines, pane))
    out["yaml"] = panels

    # S46: the proxy tube from the cube to the ground, then the road it becomes (inner and outer segments; the
    # drawbridge spans the moat between).
    cd = bpy.data.curves.new("proxy_tube", "CURVE")
    cd.dimensions, cd.bevel_depth, cd.bevel_resolution = "3D", 0.022, 6
    sp = cd.splines.new("BEZIER")
    pts = [(1.0, 0, 0.62), (1.45, 0, 0.45), (ROAD_X0 + 0.2, 0, 0.03)]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    tube = K.link(bpy.data.objects.new("proxy_tube", cd))
    tube.data.materials.append(K.mat_acrylic("tube", "lab_glow", alpha=0.5, emit=1.2))
    asphalt = K.mat_plastic("asphalt", "lab_dark", 0.6)
    roads = []
    for name, x0, x1 in (("road_in", ROAD_X0, MOAT_R0), ("road_out", MOAT_R1, ROAD_X1)):
        root = K.empty(name, (x0, 0, 0.012))
        _box(f"{name}.slab", asphalt, root, ((x1 - x0) / 2, 0, 0), (x1 - x0, ROAD_W, 0.02))
        for s in (-1, 1):
            _box(f"{name}.edge{s}", K.mat_emission(f"{name}.edge", "paper", 2.0), root,
                 ((x1 - x0) / 2, s * (ROAD_W / 2 - 0.05), 0.012), (x1 - x0, 0.03, 0.004))
        roads.append(root)
    dashes = []
    dash_m = K.mat_emission("lane_dash", "amber", 6.0)
    x = MOAT_R1 + 0.3
    while x < ROAD_X1 - 0.3:
        dashes.append(_box(f"dash{len(dashes)}", dash_m, None, (x, 0, 0.026), (0.4, 0.05, 0.004)))
        x += 0.8
    out.update(tube=tube, roads=roads, dashes=dashes)

    # S47: dashboards on a wall behind the cube, 4 x 3; each a card that flips from teal to red. Each shows one figure
    # from the brief's fact card (section "Ending, fact card and vertical cut", sourced; human, C4 v2: "maybe there's
    # some real data from the incident"), the same text on both faces. Figures the brief marks unconfirmed (the 700)
    # or that only the lyrics give (regions, nodes, minutes, 198) are left out. Re-check with the fact card's sources
    # before the final render.
    wall = K.empty("dash_wall", (0, 5.0, 0))
    _box("dash_wall.back", K.mat_plastic("dashwall", "lab_dark", 0.3), wall, (0, 0.12, 1.55), (6.4, 0.1, 3.1))
    teal, red = K.mat_emission("dash_ok", "lab_glow", 0.9), K.mat_emission("dash_red", "alarm", 2.5)  # dim: ink reads
    trace = K.mat_ink("dash_trace", "shadow")
    cards = []
    for r in range(3):
        for c in range(4):
            piv = K.empty(f"dash_{r}{c}", (-2.25 + 1.5 * c, 0, 0.55 + 1.0 * r), wall)
            K.mesh_obj(f"dash_{r}{c}.ok", bpy.ops.mesh.primitive_plane_add, teal, piv, size=1,
                       location=(0, -0.012, 0), rotation=(math.pi / 2, 0, 0)).scale = (1.36, 0.86, 1)
            K.mesh_obj(f"dash_{r}{c}.bad", bpy.ops.mesh.primitive_plane_add, red, piv, size=1,
                       location=(0, 0.012, 0), rotation=(-math.pi / 2, 0, 0)).scale = (1.36, 0.86, 1)
            label, value = DASH_FACTS[(2 - r) * 4 + c]  # top row first, read left to right
            vs = min(0.26, 1.15 / (0.62 * len(value)))
            ls = min(0.16, 1.22 / (0.66 * len(label)))  # labels as large as the card allows (were 0.12, hard to read)
            for side, y, rz in (("f", -0.02, 0.0), ("b", 0.02, math.pi)):  # back face reads after the flip
                K.text(f"dash_{r}{c}.{side}.label", label, ls, trace, loc=(0, y, 0.25), rot=(math.pi / 2, 0, rz),
                       parent=piv)
                K.text(f"dash_{r}{c}.{side}.value", value, vs, trace, loc=(0, y, -0.08), rot=(math.pi / 2, 0, rz),
                       parent=piv)
            cards.append(piv)
    out.update(dash_wall=wall, dash_cards=cards)

    # S48: the moat (an annulus around the cube) and the drawbridge where the road crosses it, with chain towers.
    moat = K.empty("moat")
    K.mesh_obj("moat.water", bpy.ops.mesh.primitive_torus_add, K.mat_emission("moat", "horizon", 0.5), moat,
               major_radius=(MOAT_R0 + MOAT_R1) / 2, minor_radius=(MOAT_R1 - MOAT_R0) / 2, major_segments=128,
               minor_segments=12, location=(0, 0, 0.002)).scale = (1, 1, 0.02)
    bridge = K.empty("bridge", (MOAT_R0, 0, 0.03))
    K.prop(bridge, "raise", 0.0, hi=100.0)
    plank = K.mat_metal("bridge_deck", "brass", 0.3)
    _box("bridge.deck", plank, bridge, ((MOAT_R1 - MOAT_R0) / 2, 0, 0), (MOAT_R1 - MOAT_R0, ROAD_W, 0.04))
    for k in range(5):
        _box(f"bridge.slat{k}", K.mat_plastic("slat", "lab_dark", 0.4), bridge,
             (0.08 + 0.16 * k, 0, 0.022), (0.03, ROAD_W, 0.006))
    towers = []
    for s in (-1, 1):
        t = _box(f"bridge.tower{s}", K.mat_plastic("tower", "lab", 0.3), None,
                 (MOAT_R0 - 0.1, s * (ROAD_W / 2 + 0.1), 0.55), (0.12, 0.12, 1.1))
        K.bevel(t, 0.01)
        towers.append(t)
    links = {s: [K.mesh_obj(f"chain{s}_{k}", bpy.ops.mesh.primitive_torus_add, K.mat_chrome("chain"), None,
                            major_radius=0.035, minor_radius=0.009, location=(0, 0, 0),
                            rotation=(0, math.pi / 2 * (k % 2), 0)) for k in range(14)] for s in (-1, 1)}
    out.update(moat=moat, bridge=bridge, chains=links, bridge_towers=towers)

    # S49: the egress gate across the inner road: post, striped arm, sign on the post facing the front.
    gate = K.empty("gate", (GATE_X, 0, 0))
    K.prop(gate, "flash", 0.0)
    _box("gate.post", K.mat_plastic("gatepost", "lab", 0.3), gate, (0, -ROAD_W / 2 - 0.12, 0.45), (0.12, 0.12, 0.9))
    stripe = [K.mat_emission("gate_red", "alarm", 8.0, gate, "flash"), K.mat_plastic("gate_white", "paper", 0.4)]
    for k in range(8):
        _box(f"gate.arm{k}", stripe[k % 2], gate, (0, -ROAD_W / 2 + 0.11 + 0.2 * k, 0.42), (0.06, 0.2, 0.08))
    _sign("gate.sign", "EGRESS\nDENIED", 0.16, 0.9, 0.5, gate, (0, -ROAD_W / 2 - 0.2, 0.85), board="paper")
    _box("gate.sign.stripe", stripe[0], gate, (0, -ROAD_W / 2 - 0.204, 0.57), (0.9, 0.004, 0.06))
    out["gate"] = gate

    # S50: the vault (metadata), a bank-vault combination door (human, C4 v2: the first "didn't look quite right"):
    # a round door set in a chrome ring on a square frame, a hinge block; a numbered dial (0-95) under a fixed amber
    # pointer; a three-spoke handle; six bolts round the door's edge that shoot out into keepers in the frame on lock.
    vault = K.empty("vault", (-2.3, 1.75, 0))
    _box("vault.block", K.mat_plastic("vaultblock", "lab_dark", 0.3), vault, (0, 0.25, 1.05), (2.1, 0.4, 2.1))
    steel = K.mat_plastic("vaultdoor", "lab", 0.25)
    dark = K.mat_plastic("vaultdark", "shadow", 0.4)
    chrome = K.mat_chrome("vaultrim")
    C = Vector((0, 0, 1.0))  # door centre (vault space)
    K.mesh_obj("vault.recess", bpy.ops.mesh.primitive_cylinder_add, dark, vault, radius=0.84, depth=0.02,
               vertices=64, location=C + Vector((0, 0.045, 0)), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("vault.ring", bpy.ops.mesh.primitive_torus_add, chrome, vault, major_radius=0.84, minor_radius=0.05,
               major_segments=64, location=C + Vector((0, 0.0, 0)), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("vault.door", bpy.ops.mesh.primitive_cylinder_add, steel, vault, radius=0.7, depth=0.16, vertices=64,
               location=C + Vector((0, -0.04, 0)), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("vault.door.lip", bpy.ops.mesh.primitive_torus_add, chrome, vault, major_radius=0.62,
               minor_radius=0.018, major_segments=64, location=C + Vector((0, -0.125, 0)), rotation=(math.pi / 2, 0, 0))
    _box("vault.hinge", chrome, vault, C + Vector((-0.8, -0.06, 0)), (0.14, 0.14, 0.7))
    # Dial: a dark disc with a brass rim, numbers every 5 (labelled every 10), ticks between; spins on "spin".
    dial = K.empty("vault.dial", C + Vector((0, -0.13, 0.28)), vault)
    dial.rotation_euler = (math.pi / 2, 0, 0)  # local +Z toward the camera (-Y); spin about the door axis (Y)
    K.prop(vault, "spin", 0.0, hi=1000.0)
    K.drive(dial, "rotation_euler", 1, vault, "spin", "0.5236 * x")
    K.mesh_obj("vault.dial.face", bpy.ops.mesh.primitive_cylinder_add, dark, dial, radius=0.2, depth=0.04,
               vertices=48)
    K.mesh_obj("vault.dial.rim", bpy.ops.mesh.primitive_torus_add, K.mat_plastic("dialrim", "brass", 0.2), dial,
               major_radius=0.2, minor_radius=0.014, major_segments=48, location=(0, 0, 0.02))
    K.mesh_obj("vault.dial.knob", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("dialknob", "brass", 0.2), dial,
               radius=0.07, depth=0.06, vertices=32, location=(0, 0, 0.04))
    nums = K.mat_plastic("dialnum", "paper", 0.4)
    for k in range(20):
        a = math.pi / 2 - math.tau * k / 20
        if k % 2 == 0:
            K.text(f"vault.dial.n{k}", str(k * 5), 0.045, nums, loc=(math.cos(a) * 0.14, math.sin(a) * 0.14, 0.022),
                   rot=(0, 0, a - math.pi / 2), parent=dial)
        _box(f"vault.dial.tick{k}", nums, dial, (math.cos(a) * 0.185, math.sin(a) * 0.185, 0.022),
             (0.008, 0.022 if k % 2 else 0.032, 0.003), (0, 0, a - math.pi / 2))
    ptr = K.mesh_obj("vault.pointer", bpy.ops.mesh.primitive_cone_add, K.mat_emission("vaultptr", "amber", 8.0), vault,
                     radius1=0.03, depth=0.06, vertices=3, location=C + Vector((0, -0.13, 0.52)),
                     rotation=(0, math.pi, 0))
    # Handle: a hub and three spokes with ball ends, below the dial; turns a sixth on lock ("lock").
    K.prop(vault, "lock", 0.0)
    hub = K.empty("vault.handle", C + Vector((0, -0.15, -0.22)), vault)
    hub.rotation_euler = (math.pi / 2, 0, 0)
    K.drive(hub, "rotation_euler", 1, vault, "lock", "1.0472 * x")
    K.mesh_obj("vault.handle.hub", bpy.ops.mesh.primitive_cylinder_add, chrome, hub, radius=0.06, depth=0.08,
               vertices=24)
    for k in range(3):
        a = math.pi / 2 + math.tau * k / 3
        sp = K.mesh_obj(f"vault.handle.spoke{k}", bpy.ops.mesh.primitive_cylinder_add, chrome, hub, radius=0.018,
                        depth=0.3, vertices=12, location=(math.cos(a) * 0.15, math.sin(a) * 0.15, 0.03),
                        rotation=(0, math.pi / 2, a))
        K.mesh_obj(f"vault.handle.ball{k}", bpy.ops.mesh.primitive_uv_sphere_add, chrome, hub, radius=0.035,
                   location=(math.cos(a) * 0.31, math.sin(a) * 0.31, 0.03))
    # Bolts at the door's edge (in front of the ring, so their travel shows) and keepers on the frame.
    bolts = []
    for k in range(6):
        a = math.tau * k / 6 + math.pi / 6
        d = Vector((math.cos(a), 0, math.sin(a)))
        b = K.mesh_obj(f"vault.bolt{k}", bpy.ops.mesh.primitive_cylinder_add, chrome, vault, radius=0.04, depth=0.24,
                       vertices=16, location=C + d * 0.6 + Vector((0, -0.14, 0)), rotation=(0, math.pi / 2 - a, 0))
        b["dir"] = tuple(d)
        bolts.append(b)
        _box(f"vault.keeper{k}", dark, vault, C + d * 0.96 + Vector((0, -0.02, 0)), (0.12, 0.06, 0.12),
             (0, -a, 0))
    K.prop(vault, "lamp", 0.0)
    K.mesh_obj("vault.lamp", bpy.ops.mesh.primitive_uv_sphere_add, K.mat_emission("vaultlamp", "amber", 40.0, vault,
                                                                                   "lamp"),
               vault, radius=0.06, location=(0.85, -0.08, 2.0))
    _sign("vault.label", "METADATA", 0.17, 1.2, 0.28, vault, (-0.1, -0.06, 1.98))
    note = K.empty("vault.note", C + Vector((0.32, -0.135, -0.05)), vault)
    note.rotation_euler = (math.pi / 2, 0.15, 0)
    K.mesh_obj("vault.note.paper", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("sticky_h", "note", 0.6), note,
               size=0.22)
    K.text("vault.note.text", "NO\nINTERNET :)", 0.04, K.mat_ink("ink_h", "shadow"), loc=(0, 0, 0.002),
           rot=(0, 0, 0), font="InstrumentSerif-Italic.ttf", parent=note)
    out.update(vault=vault, vault_dial=dial, vault_bolts=bolts, vault_note=note, vault_pointer=ptr)

    # S51: key-shaped candles on a bench in front: a brass shaft with teeth, a bow on top with the wick and flame.
    # A token dies on its beat: the flame snuffs, a puff of smoke, the key goes dull grey and topples (human, C4 v2:
    # shrinking "not the right call"). "dead" (0-1) on each candle greys its own material.
    bench = K.empty("candles", (0, -2.55, 0))
    _box("candles.bench", K.mat_plastic("bench", "lab_dark", 0.3), bench, (0, 0, 0.1), (3.4, 0.3, 0.2))
    # Smoke is soft and see-through, with a faint glow so it reads against the dark; a dead key is pale ash, not
    # dark grey, so it reads on the dark floor (C4 v3 rough spots).
    smoke_m = K.mat_acrylic("smoke", "decal_film", alpha=0.16, emit=0.12)
    smoke_m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    brass, grey = K.col("brass"), K.lin("#86827b")
    candles = []
    for k in range(8):
        c = K.empty(f"candle{k}", (-1.4 + 0.4 * k, 0, 0.2), bench)
        K.prop(c, "dead", 0.0)
        wax = K.mat_plastic(f"keywax{k}", "brass", 0.35)
        bsdf = next(n for n in wax.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        for i in range(3):
            K.drive(bsdf.inputs["Base Color"], "default_value", i, c, "dead",
                    f"{brass[i]:.4f} * (1 - x) + {grey[i]:.4f} * x")
        shaft = K.empty(f"candle{k}.shaft", (0, 0, 0), c)
        K.mesh_obj(f"candle{k}.wax", bpy.ops.mesh.primitive_cylinder_add, wax, shaft, radius=0.035, depth=1.0,
                   vertices=16, location=(0, 0, 0.5))
        shaft.scale = (1, 1, 0.34)
        for j in range(2):
            _box(f"candle{k}.tooth{j}", wax, c, (0.05, 0, 0.04 + 0.06 * j), (0.05, 0.03, 0.03))
        top = K.empty(f"candle{k}.top", (0, 0, 0.34), c)
        K.mesh_obj(f"candle{k}.bow", bpy.ops.mesh.primitive_torus_add, wax, top, major_radius=0.07,
                   minor_radius=0.02, location=(0, 0, 0.07), rotation=(math.pi / 2, 0, 0))
        fl = K.mesh_obj(f"candle{k}.flame", bpy.ops.mesh.primitive_uv_sphere_add,
                        K.mat_emission("flame", "amber", 30.0), top, radius=0.03, location=(0, 0, 0.18))
        fl.scale = (0.7, 0.7, 1.5)
        puffs = []
        for j in range(3):
            pf = K.mesh_obj(f"candle{k}.smoke{j}", bpy.ops.mesh.primitive_uv_sphere_add, smoke_m, bench, radius=1.0,
                            segments=12, ring_count=8, location=(c.location.x, 0, 0.2 + 0.52))
            pf.scale = (0.001,) * 3
            puffs.append(pf)
        candles.append((c, shaft, top, fl, puffs))
    out.update(candles_root=bench, candles=candles)

    # S52: the camera horn section, six security cameras on poles beyond the moat, front.
    horns = K.empty("horns", (0, -4.6, 0))
    heads = []
    for k in range(6):
        x = -2.5 + k
        K.mesh_obj(f"horn{k}.pole", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("hornpole"), horns,
                   radius=0.025, depth=1.0, location=(x, 0, 0.5))
        h = K.empty(f"horn{k}.head", (x, 0, 1.05), horns)
        K.prop(h, "honk", 0.0, lo=-1.0, hi=1.0)
        tilt = K.empty(f"horn{k}.tilt", (0, 0, 0), h)
        K.drive(tilt, "rotation_euler", 0, h, "honk", "-0.45 * x")  # contact = a nod down
        _box(f"horn{k}.body", K.mat_plastic("horncam", "lab", 0.25), tilt, (0, 0.08, 0), (0.18, 0.4, 0.18))
        K.mesh_obj(f"horn{k}.lens", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("hornlens", "lens", 0.02),
                   tilt, radius=0.07, depth=0.06, location=(0, 0.3, 0), rotation=(math.pi / 2, 0, 0))
        K.mesh_obj(f"horn{k}.rec", bpy.ops.mesh.primitive_uv_sphere_add, K.mat_emission("hornrec", "alarm", 30.0),
                   tilt, radius=0.02, location=(0.06, 0.25, 0.08))
        heads.append(h)
    out.update(horns=horns, horn_heads=heads)

    # S53-S54: the honest probe with its white flag; the ribbon dispenser.
    hp = K.probe("honest", (1.85, -1.75, K.PROBE_R), led=0.6)
    flag = K.empty("flag", (0.05, 0.0, 0.0), hp)
    K.mesh_obj("flag.pole", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("flagpole_h", "paper", 0.4), flag, radius=0.004,
               depth=0.2, location=(0, 0, 0.1))
    K.mesh_obj("flag.cloth", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("whiteflag", "paper", 0.5), flag,
               size=1, location=(0.04, 0, 0.17), rotation=(math.pi / 2, 0, 0)).scale = (0.08, 0.055, 1)
    disp = K.empty("dispenser", (2.15, -1.45, 0))
    disp.rotation_euler = (0, 0, math.radians(-45))
    disp.scale = (0.5, 0.5, 0.5)
    K.prop(disp, "lever", 0.0, lo=-1.0, hi=1.0)
    _box("dispenser.body", K.mat_plastic("disp", "lab", 0.3), disp, (0, 0, 0.45), (0.45, 0.35, 0.9))
    _box("dispenser.slot", K.mat_plastic("slot", "shadow", 0.6), disp, (0, -0.176, 0.5), (0.3, 0.01, 0.04))
    lev = K.empty("dispenser.lever", (0.24, 0, 0.7), disp)
    K.drive(lev, "rotation_euler", 0, disp, "lever", "0.6 * x")
    K.mesh_obj("dispenser.lever.rod", bpy.ops.mesh.primitive_cylinder_add, K.mat_chrome("lever"), lev, radius=0.015,
               depth=0.3, location=(0, 0, 0.15))
    K.mesh_obj("dispenser.lever.ball", bpy.ops.mesh.primitive_uv_sphere_add, K.mat_plastic("leverball", "alarm", 0.2),
               lev, radius=0.04, location=(0, 0, 0.3))
    _sign("dispenser.sign", "SAFE STOP", 0.06, 0.4, 0.1, disp, (0, -0.177, 0.78))
    rib = K.empty("ribbon", (0, 0, 0))
    rib_s = 0.4  # probe-sized (a tennis ball, sr_kit.PROBE_R)
    K.mesh_obj("ribbon.rosette", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("rosette", "amber", 0.4), rib,
               radius=0.09, depth=0.015, vertices=24, rotation=(math.pi / 2, 0, 0))
    for s in (-1, 1):
        _box(f"ribbon.tail{s}", K.mat_plastic("rosette_tail", "amber", 0.4), rib, (s * 0.035, 0, -0.12),
             (0.04, 0.008, 0.14), (0, s * 0.25, 0))
    K.text("ribbon.text", "+0.5", 0.07, K.mat_ink("ribbon_ink", "shadow"), loc=(0, -0.009, 0),
           parent=rib)
    rib["size"] = rib_s
    out.update(honest=hp, flag=flag, dispenser=disp, ribbon=rib)

    # S55: subpoena paper airplanes (a V of seven) and the auditors' stamp arms.
    paper = K.mat_plastic("subpoena", "paper", 0.5)
    planes = []
    for k in range(7):
        p = _poly(f"plane{k}", [(0.3, 0, 0), (-0.18, 0.22, 0.02), (-0.18, -0.22, 0.02), (-0.18, 0, -0.07)],
                  [(0, 1, 3), (0, 3, 2)], paper)
        p.scale = (2.5, 2.5, 2.5)
        planes.append(p)
    stamps = []
    for k in range(4):
        s = K.empty(f"stamp{k}", (-4.6 + 0.85 * k, 3.6, 0))
        K.prop(s, "slam", 0.0, lo=-1.0, hi=1.0)
        _box(f"stamp{k}.col", K.mat_plastic("stampcol", "lab", 0.3), s, (0, 0.15, 0.7), (0.2, 0.2, 1.4))
        arm = K.empty(f"stamp{k}.arm", (0, 0.15, 1.3), s)
        K.drive(arm, "rotation_euler", 0, s, "slam", "-(0.5 - 0.5 * x)")
        _box(f"stamp{k}.beam", K.mat_chrome("stampbeam"), arm, (0, -0.35, 0), (0.06, 0.7, 0.06))
        _box(f"stamp{k}.head", K.mat_plastic("stamphead", "alarm", 0.3), arm, (0, -0.7, -0.15), (0.24, 0.16, 0.2))
        stamps.append(s)
    out.update(planes=planes, stamps=stamps)

    # S56: the giant printer (from G), paper with the bill coming out.
    pr = K.empty("printer", (-0.2, 3.3, 0))
    K.prop(pr, "head", 0.0, lo=-1.0, hi=1.0)
    body = _box("printer.body", K.mat_plastic("printer", "lab", 0.3), pr, (0, 0, 0.55), (2.0, 1.2, 1.1))
    K.bevel(body, 0.03)
    _box("printer.slot", K.mat_plastic("pslot", "shadow", 0.6), pr, (0, -0.605, 0.85), (1.4, 0.01, 0.05))
    head = K.empty("printer.head", (0, -0.62, 0.95), pr)
    K.drive(head, "location", 0, pr, "head", "0.5 * x")
    _box("printer.head.box", K.mat_plastic("phead", "alarm", 0.3), head, (0, 0, 0), (0.18, 0.08, 0.08))
    sheet = K.empty("printer.sheet", (0, -0.62, 0.85), pr)
    sheet.rotation_euler = (math.radians(40), 0, 0)
    feed = K.empty("printer.feed", (0, 0, 0), sheet)
    K.mesh_obj("printer.sheet.paper", bpy.ops.mesh.primitive_plane_add, K.mat_plastic("bill", "paper", 0.6), feed,
               size=1, location=(0, -0.6, 0)).scale = (1.3, 1.2, 1)
    K.text("printer.sheet.text", "BILL TO:\nTHE LAB", 0.2, K.mat_ink("bill_ink", "shadow"),
           loc=(0, -0.62, 0.003), rot=(0, 0, 0), parent=feed)
    out.update(printer=pr, printer_feed=feed)

    # S57: the outer wall, sixteen segments on a ring, each with a beacon (FX).
    walls = []
    for k in range(16):
        a = math.tau * k / 16 + math.pi / 16
        w = K.empty(f"wall{k}", (math.sin(a) * 9.5, -math.cos(a) * 9.5, 0))
        w.rotation_euler = (0, 0, a)
        K.prop(w, "beacon", 0.04)
        _box(f"wall{k}.slab", K.mat_metal("outerwall", "brass", 0.35), w, (0, 0, 0.7), (3.6, 0.3, 1.4))
        K.mesh_obj(f"wall{k}.beacon", bpy.ops.mesh.primitive_uv_sphere_add,
                   K.mat_emission(f"wall{k}.beacon", "alarm", 40.0, w, "beacon"), w, radius=0.08,
                   location=(0, 0, 1.5))
        walls.append(w)
    out["walls"] = walls

    # S58: the spreadsheet behind bars, facing +X, left of the cube.
    ss = K.empty("sheet", (-5.4, 0.3, 0))
    ss.rotation_euler = (0, 0, math.pi / 2)
    _box("sheet.panel", K.mat_plastic("sheetpanel", "paper", 0.5), ss, (0, 0.03, 1.2), (2.6, 0.05, 1.7))
    cell_red = K.mat_emission("cell_red", "alarm", 5.0)
    grid = K.mat_plastic("grid", "shadow", 0.5)
    cells = []
    for r in range(5):
        for c in range(6):
            x, z = -1.05 + 0.42 * c, 0.6 + 0.3 * (4 - r) + 0.05
            cell = _box(f"sheet.cell{r}{c}", cell_red, ss, (x, -0.0, z), (0.38, 0.01, 0.26))
            cells.append(cell)
    for c in range(7):
        _box(f"sheet.vline{c}", grid, ss, (-1.26 + 0.42 * c, -0.01, 1.2), (0.012, 0.004, 1.55))
    for r in range(6):
        _box(f"sheet.hline{r}", grid, ss, (0, -0.01, 0.5 + 0.3 * r), (2.55, 0.004, 0.012))
    # A full cell (human, C4 v2: "more enclosed, particularly around the sides"): bars on the front and both sides, a
    # barred top, a back wall and a floor slab; the sheet inside, legible through the front bars.
    bar_m, rail_m = K.mat_chrome("jailbar"), K.mat_chrome("jailrail")
    X, YF, YB, Z0, Z1 = 1.4, -0.3, 0.25, 0.1, 2.15
    _box("sheet.back", K.mat_plastic("cellwall", "lab_dark", 0.4), ss, (0, YB + 0.03, 1.15), (2 * X + 0.1, 0.06, 2.3))
    _box("sheet.floor", K.mat_plastic("cellfloor", "lab_dark", 0.4), ss, (0, (YF + YB) / 2, Z0 / 2),
         (2 * X + 0.1, YB - YF + 0.1, Z0))
    for k in range(11):
        K.mesh_obj(f"sheet.bar{k}", bpy.ops.mesh.primitive_cylinder_add, bar_m, ss, radius=0.022, depth=Z1 - Z0,
                   vertices=12, location=(-1.3 + 0.26 * k, YF, (Z0 + Z1) / 2))
    for sx in (-1, 1):
        for k in range(5):
            K.mesh_obj(f"sheet.side{sx}.{k}", bpy.ops.mesh.primitive_cylinder_add, bar_m, ss, radius=0.022,
                       depth=Z1 - Z0, vertices=12, location=(sx * X, YF + (YB - YF) * k / 4, (Z0 + Z1) / 2))
    for k in range(11):  # the top: bars front to back
        K.mesh_obj(f"sheet.top{k}", bpy.ops.mesh.primitive_cylinder_add, bar_m, ss, radius=0.018, depth=YB - YF,
                   vertices=12, location=(-1.3 + 0.26 * k, (YF + YB) / 2, Z1), rotation=(math.pi / 2, 0, 0))
    for z in (0.15, Z1):
        _box(f"sheet.rail{z}", rail_m, ss, (0, YF, z), (2 * X + 0.06, 0.06, 0.06))
        _box(f"sheet.railb{z}", rail_m, ss, (0, YB, z), (2 * X + 0.06, 0.06, 0.06))
        for sx in (-1, 1):
            _box(f"sheet.rails{sx}{z}", rail_m, ss, (sx * X, (YF + YB) / 2, z), (0.06, YB - YF + 0.06, 0.06))
    _sign("sheet.title", "LIABILITY", 0.15, 1.0, 0.22, ss, (0, YF - 0.06, Z1 + 0.22))
    out.update(sheet=ss, cells=cells)
    return out


def lights(S):
    K.studio_lights(center=(0, 0, 1.0), radius=14.0, scale=(14.0 / 6.0) ** 2)
    K.reflection_cards(center=(0, 0, 1.0), radius=16.0)


# ---------------------------------------------------------------- animation (config/instrument_map.json, set H)

def animate(S, t0, t1):
    A.sing(S["honest"], t0, t1)  # the honest probe is the protagonist's voice in the rebuild
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    cut = lambda i: shot[i]["cut"]  # noqa: E731
    W = lambda evs, a=t0 - 1, b=t1 + 1: A.between(evs, a, b)  # noqa: E731
    kit, beats = A.events("kit"), A.events("beats")
    bass = A.events("bass")

    # Global: the floor ring on the bass.
    A.led_pulse(S["floor_ring"], "pulse", W(A.strikes(bass, 0.05)))

    # S45: config text scrolls up the old walls, then the walls are glass (text gone at S46's cut).
    fa, fb = A.frame(cut("S45")) - 2, A.frame(cut("S46")) + 2
    for root, lines, pane in S["yaml"]:
        A.write_keys(pane, "hide_render", [(0, 0, "CONSTANT"), (A.frame(cut("S46")) + 1, 1, "CONSTANT")])
        n = len(lines)
        for k, t in enumerate(lines):
            keys = []
            for f in range(fa, fb + 1):
                u = (k + (f - fa) / A.FPS * 3.0) % n
                keys.append((f, 0.15 + 0.15 * u, "LINEAR"))
            A.write_keys(t, "location", keys, index=2)
            for ch in t.children:
                A.write_keys(ch, "hide_render", [(0, 0, "CONSTANT"), (A.frame(cut("S46")) + 1, 1, "CONSTANT")])

    # S46: the road widens out of the tube; lane dashes run out along it.
    a, b = cut("S46"), cut("S47")
    for r in S["roads"]:
        A.write_keys(r, "scale", [(0, 0.02, "CONSTANT"), (A.frame(a + 0.3), 0.02), (A.frame(b - 2.0), 1.0)], index=1)
    for k, d in enumerate(S["dashes"]):
        _pop(d, a + 2.5 + 0.18 * k, 0.15)

    # S47: dashboards appear, then flip red one by one on the kit strikes of "dashboards all glowed".
    _pop(S["dash_wall"], cut("S47") - 0.02, 0.3)
    td = _word("L54", "dashboards")
    hits = [e["t"] for e in A.strikes(W(kit, td - 0.05, cut("S48") - 0.2), 0.1)]
    times = [hits[round(k * (len(hits) - 1) / 11)] if len(hits) >= 12 else td + k * (cut("S48") - 0.3 - td) / 11
             for k in range(12)]
    order = sorted(range(12), key=lambda i: (i % 4 + (2 - i // 4)) * 10 + i)  # a diagonal cascade
    for k, i in enumerate(order):
        f = A.frame(times[k])
        _keys(S["dash_cards"][i], "rotation_euler", [(0, 0.0), (f - 1, 0.0), (f + 8, math.pi)], index=2)

    # S48: air gap. The moat and bridge appear; the bridge cranks up a notch per bass note, chains sliding.
    _pop(S["moat"], cut("S48") - 0.02, 0.3)
    _pop(S["bridge"], cut("S48") - 0.02, 0.3)
    for t in S["bridge_towers"]:
        _pop(t, cut("S48") - 0.02, 0.3, axes=(2,))
    notches = A.strikes(W(bass, _word("L55", "air"), cut("S49")), 0.08) or [{"t": _word("L55", "box"),
                                                                              "end": 0, "vel": 100}]
    N = len(notches)
    A.stepper(S["bridge"], "raise", notches, pre=6, settle=10, overshoot=0.0)
    K.drive(S["bridge"], "rotation_euler", 1, S["bridge"], "raise", f"-1.35 * min(x, {N}) / {N}")
    L = MOAT_R1 - MOAT_R0
    hinge = Vector(S["bridge"].location)
    for s, links in S["chains"].items():
        top = Vector((MOAT_R0 - 0.1, s * (ROAD_W / 2 + 0.1), 1.1))
        for k, ln in enumerate(links):
            keys = {0: [], 1: [], 2: []}
            for j in range(N + 1):
                th = 1.35 * j / N
                tip = hinge + Vector((L * math.cos(th), s * (ROAD_W / 2 - 0.05), L * math.sin(th) + 0.03))
                u = ((k + 0.5 * j) % len(links)) / len(links)
                p = top.lerp(tip, u)
                f = 0 if j == 0 else A.frame(notches[j - 1]["t"])
                for i in range(3):
                    keys[i].append((f, p[i]))
            for i in range(3):
                A.write_keys(ln, "location", keys[i], index=i)
            _pop(ln, cut("S48") - 0.02, 0.3)

    # S49: egress. The gate appears; a pellet leaves the cube for every kick and snare and bounces off the arm.
    g = S["gate"]
    _pop(g, cut("S49") - 0.02, 0.3)
    hits = A.strikes(A.pieces(W(kit, cut("S49") + 0.4, cut("S50")), "kick", "snare"), 0.06)
    A.hit_flash(g, "flash", hits)
    pm = K.mat_emission("pellet_h", "amber", 25.0)
    for k, e in enumerate(hits):
        p = K.pellet_mesh(f"egress_pellet{k}", pm, r=0.02)
        y = ((k % 3) - 1) * 0.25
        fa = A.frame(e["t"])
        fl = fa - 24
        path = [(fl, (1.0, 0, 0.62)), (fl + 8, (1.5, y * 0.5, 0.45)), (fa, (GATE_X - 0.06, y, 0.42)),
                (fa + 10, (GATE_X - 0.6, y * 1.4, 0.85)), (fa + 22, (GATE_X - 1.1, y * 1.8, 0.2))]
        for i in range(3):
            A.write_keys(p, "location", [(f, v[i], "LINEAR" if f == fa else "BEZIER") for f, v in path], index=i)
        A.write_keys(p, "hide_render", [(fl - 1, 1, "CONSTANT"), (fl, 0, "CONSTANT"), (fa + 22, 1, "CONSTANT")])

    # S50: the vault. The note is pulled off on "metadata", the dial spins on the synth, locks on "endpoint".
    v = S["vault"]
    _pop(v, cut("S50") - 0.02, 0.3)
    t_meta, t_lock = cut("S50") + 0.25, _word("L56", "keep")
    n = S["vault_note"]
    n0 = n.location.copy()
    for dt, dloc, rot in ((0.0, (0, 0, 0), (math.pi / 2, 0.15, 0)), (0.25, (-0.25, -0.15, 0.1), (1.0, 0.9, 0.4)),
                          (0.6, (-0.45, -0.3, -0.5), (0.2, 0.2, 1.2)), (0.95, (-0.55, -0.35, -1.0), (0, 0, 1.6))):
        n.location, n.rotation_euler = n0 + Vector(dloc), rot
        n.keyframe_insert("location", frame=A.frame(t_meta + dt))
        n.keyframe_insert("rotation_euler", frame=A.frame(t_meta + dt))
    spins = A.strikes(W(A.events("synth"), t_meta + 0.4, t_lock - 0.1), 0.12)
    if len(spins) < 4:
        spins = [{"t": t_meta + 0.4 + k * (t_lock - t_meta - 0.5) / 5, "end": 0, "vel": 100} for k in range(5)]
    A.stepper(v, "spin", spins, pre=6, settle=8, overshoot=0.1)
    fl = A.frame(t_lock)
    # Lock: the handle turns, then the bolts shoot out across the ring into the keepers, the lamp lights.
    A.write_keys(v, '["lock"]', [(0, 0.0), (fl - 10, 0.0), (fl - 2, 1.0)])
    for k, bolt in enumerate(S["vault_bolts"]):
        p0, d = bolt.location.copy(), Vector(bolt["dir"])
        for i in (0, 2):
            _keys(bolt, "location", [(0, p0[i]), (fl - 1 + k % 2, p0[i]), (fl + 5 + k % 2, p0[i] + d[i] * 0.26)],
                  index=i)
    A.write_keys(v, '["lamp"]', [(0, 0.0, "CONSTANT"), (fl + 4, 1.0, "CONSTANT")])

    # S51: key candles burn down, one per beat of the line.
    _pop(S["candles_root"], cut("S51") - 0.02, 0.3)
    ls, le = _line("L57")
    bt = [e["t"] for e in W(beats, ls - 0.05, ls + 10.0)][:9]
    for k, (c, shaft, top, fl_, puffs) in enumerate(S["candles"]):
        if k + 1 >= len(bt):
            break
        f = A.frame(bt[k + 1])  # dies on its beat
        # The flame snuffs (4 frames)...
        for i in range(3):
            v0 = fl_.scale[i]
            A.write_keys(fl_, "scale", [(0, v0), (f - 1, v0), (f + 3, 0.001 * v0, "LINEAR")], index=i)
        # ...a puff of smoke rises and spreads from the wick, then thins away...
        x0 = c.location.x
        for j, pf in enumerate(puffs):
            s0, dz, dx = 0.03 + 0.012 * j, 0.18 + 0.1 * j, (j - 1) * 0.04
            for i in range(3):
                A.write_keys(pf, "scale", [(0, 0.001, "CONSTANT"), (f + j, 0.001), (f + 6 + j, s0),
                                           (f + 26 + 2 * j, s0 * 1.6), (f + 40 + 2 * j, 0.001)], index=i)
            A.write_keys(pf, "location", [(f + j, x0), (f + 40, x0 + dx)], index=0)
            A.write_keys(pf, "location", [(f + j, 0.72), (f + 40, 0.72 + dz)], index=2)
        # ...the brass goes dull grey and the key topples forward off the bench to lie on the floor.
        A.write_keys(c, '["dead"]', [(0, 0.0), (f + 2, 0.0), (f + 14, 1.0)])
        A.write_keys(c, "rotation_euler", [(0, 0.0), (f + 6, 0.0), (f + 14, 0.9), (f + 21, 1.5708, "LINEAR"),
                                           (f + 25, 1.5)], index=0)
        A.write_keys(c, "location", [(0, 0.0), (f + 6, 0.0), (f + 14, -0.12), (f + 21, -0.2)], index=1)
        A.write_keys(c, "location", [(0, 0.2), (f + 12, 0.2), (f + 21, 0.036, "LINEAR"), (f + 25, 0.05)],
                     index=2)

    # S52: monitoring. Cameras look every which way, swivel in unison to the stage on the first brass stab, then take
    # turns nodding to the drums.
    _pop(S["horns"], cut("S52") - 0.02, 0.3)
    brass = A.strikes(W(A.events("brass"), cut("S52"), cut("S53")), 0.12)
    t_sw = brass[0]["t"] if brass else cut("S52") + 0.8
    for k, h in enumerate(S["horn_heads"]):
        a0 = (0.9, -1.1, 1.4, -0.7, 1.2, -1.3)[k]
        aim = math.atan2(-(h.location.x), 4.6) * 0.5  # turn toward the cube (+Y), a little inward
        f = A.frame(t_sw)
        _keys(h, "rotation_euler", [(0, a0), (f - 8, a0), (f, aim)], index=2)
    # Then they take turns nodding to the drums: each kit hit nods the next camera, down and back (human, C4 v2).
    nods = A.strikes(W(kit, t_sw + 0.25, cut("S53")), 0.1)
    heads = S["horn_heads"]
    for k, h in enumerate(heads):
        A.striker(h, "honk", nods[k::len(heads)], wind=8, settle=20)

    # S53: the honest probe appears and raises its white flag on "raise", LED dims on "stop".
    hp = S["honest"]
    _pop(hp, cut("S53") - 0.02, 0.3)
    fr = A.frame(_word("L59", "raise"))
    _keys(S["flag"], "rotation_euler", [(0, -1.45), (fr - 4, -1.45), (fr + 10, 0.1), (fr + 18, 0.0)], index=0)
    _keys(S["flag"], "location", [(0, 0.0), (fr - 4, 0.0), (fr + 10, 0.08)], index=2)
    fs = A.frame(_word("L59", "stop"))
    A.write_keys(hp, '["led"]', [(0, 0.6), (fs - 2, 0.6), (fs + 20, 0.15)])

    # S54: the dispenser appears; its lever pulls on each crash; on "half" a +0.5 ribbon rides out to the probe.
    d = S["dispenser"]
    _pop(d, cut("S54") - 0.02, 0.3)
    A.striker(d, "lever", A.strikes(A.pieces(W(kit, cut("S54"), cut("S55")), "crash"), 0.3))
    rib = S["ribbon"]
    fh = A.frame(_word("L60", "half"))
    rz = d.rotation_euler.z  # the slot, local (0, -0.2, 0.5), in world space
    k = d.scale.x
    slot = Vector(d.location) + Vector((0.2 * k * math.sin(rz), -0.2 * k * math.cos(rz), 0.5 * k))
    to = Vector((1.85 + 0.055, -1.75 - 0.01, K.PROBE_R + 0.05))  # held out at the probe's right arm
    z = rib["size"]
    for f, p, s in ((0, slot, 0.001), (fh - 1, slot, 0.001), (fh + 12, slot + Vector((-0.03, -0.04, 0.02)), z),
                    (fh + 50, (slot + to) / 2 + Vector((0, -0.03, 0.12)), z), (fh + 80, to, z)):
        rib.location, rib.scale = p, (s, s, s)
        rib.keyframe_insert("location", frame=f)
        rib.keyframe_insert("scale", frame=f)
    A.write_keys(hp, '["arm_r"]', [(0, 0.2), (fr - 4, 0.2), (fr + 10, 1.0), (fh + 60, 1.0), (fh + 80, 0.7)])

    # S55: law. Subpoena airplanes fly over in a V; the stamp arms march in from the left on the beat, slamming
    # on "subpoenas" and "auditors".
    a, b = cut("S55") - 0.3, cut("S56") + 0.3
    for k, p in enumerate(S["planes"]):
        row = (k + 1) // 2
        side = 1 if k % 2 else -1
        off = Vector((-0.6 * row, side * 0.55 * row, -0.05 * row))
        for f, base in ((A.frame(a), Vector((-7.0, -4.0, 2.3))), (A.frame(b), Vector((4.0, -2.0, 2.6)))):
            p.location = base + off
            p.rotation_euler = (0.25 * side * (row > 0) * math.sin(f), 0, math.atan2(4.0, 14.0))
            p.keyframe_insert("location", frame=f)
            p.keyframe_insert("rotation_euler", frame=f)
        for fc in A._fcurve(p, "location", 0), A._fcurve(p, "location", 1), A._fcurve(p, "location", 2):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        A.write_keys(p, "hide_render", [(0, 1, "CONSTANT"), (A.frame(a), 0, "CONSTANT"), (A.frame(b) + 1, 1, "CONSTANT")])
    bt = [e["t"] for e in W(beats, cut("S55"), cut("S56"))]
    for k, s in enumerate(S["stamps"]):
        _hide_until(s, cut("S55") - 0.02)
        x1 = s.location.x
        x0 = x1 - 4.0
        steps = [(0, x0, "CONSTANT"), (A.frame(cut("S55")) - 1, x0, "CONSTANT")]
        for j, t in enumerate(bt[:6]):
            steps.append((A.frame(t), x0 + (x1 - x0) * (j + 1) / min(6, len(bt)), "BEZIER"))
        A.write_keys(s, "location", steps, index=0)
        A.write_keys(s, "location", [(0, 0.0)] + [(A.frame(t) - 6, 0.12, "BEZIER") for t in bt[:6]]
                     + [(A.frame(t), 0.0, "BEZIER") for t in bt[:6]], index=2)
        slams = [{"t": _word("L61", "subpoenas"), "vel": 120}, {"t": _word("L61", "auditors"), "vel": 120}]
        A.striker(s, "slam", slams, wind=10, settle=20)

    # S56: the printer appears, its head shuttles on the hats/snare, the bill feeds out across the shot.
    pr = S["printer"]
    _pop(pr, cut("S56") - 0.02, 0.25)
    sh = A.strikes(A.pieces(W(kit, cut("S56"), cut("S57")), "hats", "snare"), 0.06)
    A.write_keys(pr, '["head"]', [(A.frame(e["t"]), (-1) ** k * 0.9, "LINEAR") for k, e in enumerate(sh)]
                 or [(0, 0.0)])
    feed = S["printer_feed"]
    A.write_keys(feed, "location", [(0, 0.9, "CONSTANT"), (A.frame(cut("S56")), 0.9),
                                    (A.frame(_word("L62", "breach")), 0.0)], index=1)

    # S57: the outer wall rises segment by segment, then the spreadsheet; FX lights the beacons.
    a, b = cut("S57"), cut("S58")
    for k, w in enumerate(S["walls"]):
        _pop(w, a + 0.15 * k, 0.4, axes=(2,))
    _pop(S["sheet"], a + 0.2, 0.4)
    for w in S["walls"]:
        A.led_pulse(w, "beacon", W(A.events("fx"), a, t1 + 1))

    # S58: cells turn red one by one on the guitar (cumulative).
    gt = A.strikes(sorted(W(A.events("guitar"), cut("S58") + 0.3, t1) + A.pieces(W(kit, cut("S58") + 0.3, t1), "snare"),
                          key=lambda e: e["t"]), 0.12)
    cells = S["cells"]
    order = sorted(range(len(cells)), key=lambda i: ((i * 7) % len(cells)))
    for k, i in enumerate(order):
        if k < len(gt):
            f = A.frame(gt[k]["t"])
        else:
            f = A.frame(t1) + 100
        c = cells[i]
        for ax in range(3):
            v1 = c.scale[ax]
            A.write_keys(c, "scale", [(0, 0.001, "CONSTANT"), (f - 1, 0.001, "LINEAR"), (f + 4, v1, "LINEAR")],
                         index=ax)


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


CAMERAS = {
    "S45": [(0.0, _v(1.9, -3.4, 1.4), _v(0.0, -0.9, 1.0), 35), (1.0, _v(1.2, -2.5, 1.1), _v(0.1, -0.9, 1.0), 35)],
    "S46": [(0.0, _v(2.6, -2.4, 1.3), _v(1.4, 0.0, 0.4), 30), (0.5, _v(5.0, -3.0, 1.6), _v(4.0, 0.0, 0.1), 30),
            (1.0, _v(9.0, -2.8, 1.8), _v(14.0, 0.0, 0.0), 28)],
    "S47": [(0.0, _v(0.9, 1.15, 1.55), _v(0.0, 5.0, 1.6), 19), (1.0, _v(0.5, 1.5, 1.55), _v(0.0, 5.0, 1.6), 21)],
    "S48": [(0.0, _v(6.0, -3.6, 1.0), _v(3.4, 0.0, 0.5), 30), (1.0, _v(5.6, -3.2, 1.3), _v(3.4, 0.0, 0.6), 30)],
    "S49": [(0.0, _v(2.1, -3.2, 1.0), _v(2.45, -0.4, 0.55), 32), (1.0, _v(2.2, -2.9, 0.95), _v(2.45, -0.4, 0.55), 34)],
    "S50": [(0.0, _v(-1.5, -1.9, 1.3), _v(-2.3, 1.7, 1.2), 30), (1.0, _v(-1.8, -1.0, 1.25), _v(-2.3, 1.7, 1.2), 30)],
    "S51": [(0.0, _v(0.6, -4.3, 0.8), _v(0.0, -2.55, 0.35), 32), (1.0, _v(0.3, -3.9, 0.6), _v(0.0, -2.55, 0.35), 32)],
    "S52": [(0.0, _v(0.3, -0.15, 1.8), _v(0.0, -4.6, 0.95), 24), (1.0, _v(0.1, -0.3, 1.75), _v(0.0, -4.6, 0.95), 24)],
    "S53": [(0.0, _v(2.08, -2.45, 0.2), _v(1.86, -1.75, 0.17), 30), (1.0, _v(2.03, -2.3, 0.19), _v(1.86, -1.75, 0.17), 32)],
    "S54": [(0.0, _v(1.68, -2.35, 0.22), _v(2.0, -1.6, 0.1), 30), (1.0, _v(1.74, -2.2, 0.2), _v(2.0, -1.6, 0.1), 32)],
    "S55": [(0.0, _v(1.5, -7.5, 2.0), _v(-1.5, 1.5, 1.6), 24), (1.0, _v(0.5, -7.0, 2.2), _v(-1.0, 1.5, 1.8), 24)],
    "S56": [(0.0, _v(1.7, 1.2, 1.8), _v(-0.2, 2.3, 0.5), 30), (1.0, _v(1.5, 1.3, 1.6), _v(-0.2, 2.3, 0.45), 32)],
    "S57": [(0.0, _v(3.0, -7.0, 2.5), _v(0.0, 0.0, 0.8), 30), (1.0, _v(16.0, -24.0, 14.0), _v(0.0, 0.5, 0.0), 30)],
    "S58": [(0.0, _v(-1.9, -1.5, 1.5), _v(-5.4, 0.3, 1.45), 28), (1.0, _v(-2.3, -0.8, 1.5), _v(-5.4, 0.3, 1.45), 28)],
}
