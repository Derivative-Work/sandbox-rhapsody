"""Set E, the Backbone (brief, "Sets → E"; guitar solo, first half). C5: modelled.

Contents, as the brief lists them:
- the internet as a glowing wireframe map on the mirror floor: a violet grid, magenta route nodes;
- the guitar: a modem-shaped body whose six strings are fiber lines running off the nut into the map as routes, and
  whose frets blink with handshake lights; each strum fires a pellet one hop along its string's route, and the node
  it reaches lights and stays lit, so hop by hop the escape lights up the map;
- the amp: a server rack with blinking status lights and a speaker cone, pumping with the guitar stem;
- the dive (S26, E -> F): one pellet's route runs off the map's far edge into a teal hole, Platform's data center;
- the lead probe riding the modem; the bass floor ring around the guitar.
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Euler, Vector

import props_cde as P
import sr_anim as A
import sr_kit as K

STRINGS = 6
HOPS = 5
NUT_Y, BRIDGE_Y, STRING_Z = 1.05, -0.05, 0.118
PORTAL = Vector((0.0, 9.6, 0.0))


def string_x(s):
    return -0.045 + 0.018 * s


def node_pos(r, h):
    """Node h (0-based) on route r: routes fan out from the nut across the map, zigzagging a little."""
    a = math.radians(-50 + 20 * r)
    d = 1.4 + 1.15 * h
    z = 0.025
    return Vector((math.sin(a) * d + 0.22 * ((h % 2) * 2 - 1) * math.cos(a), NUT_Y + 0.3 + math.cos(a) * d, z))


def _polyline(pts, n=24):
    """Dense polyline through `pts` (Catmull-Rom), for paths that the pellet and the camera share."""
    P = [Vector(p) for p in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def _at(poly, u):
    """Point at arc-length fraction u of a polyline."""
    seg = [(poly[i + 1] - poly[i]).length for i in range(len(poly) - 1)]
    tot, d = sum(seg), max(0.0, min(1.0, u)) * sum(seg)
    for i, L in enumerate(seg):
        if d <= L or i == len(seg) - 1:
            return poly[i].lerp(poly[i + 1], d / L if L else 0)
        d -= L
    return poly[-1]


# The dive (S26): from the middle string's nut, out along route 2 over three nodes, past the map's edge and down into
# the portal. Shared by the pellet (keyed along it) and the S26 camera (chasing it).
DIVE = _polyline([(string_x(2), NUT_Y, STRING_Z), node_pos(2, 0) + Vector((0, 0, 0.12)),
                  node_pos(2, 1) + Vector((0, 0, 0.25)), node_pos(2, 2) + Vector((0, 0, 0.18)),
                  node_pos(2, 4) + Vector((0, 0, 0.5)), PORTAL + Vector((0, -1.0, 0.6)), PORTAL + Vector((0, 0, 0.25)),
                  PORTAL + Vector((0, 0.05, -0.8))])


def _curve(name, pts, bevel, mat, poly=False):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = bevel
    cd.bevel_resolution = 4
    sp = cd.splines.new("POLY" if poly else "BEZIER")
    if poly:
        sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts):
            p.co = (q[0], q[1], q[2], 1)
    else:
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = K.link(bpy.data.objects.new(name, cd))
    if mat:
        cd.materials.append(mat)
    return o


def _bx(name, mat, parent, loc, size, bev=0.0, rot=(0, 0, 0)):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc, rotation=rot)
    o.scale = size
    if bev:
        K.bevel(o, bev)
    return o


def _cy(name, mat, parent, loc, r, depth, rot=(0, 0, 0), verts=24):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cylinder_add, mat, parent, radius=r, depth=depth, vertices=verts,
                   location=loc, rotation=rot)
    K.smooth(o)
    return o


def _modem_guitar(gt):
    """The modem guitar: a bevelled modem body (glossy black top inset, a vent grille, side vents, rear ports, a
    status-LED strip that lights on each string's pluck, two hinged antennas with ball tips) that is also a guitar
    (two chrome pickups with pole pieces, volume and tone knobs, bridge); a neck with a rounded back, fret inlays,
    a nut with fiber ferrules where the strings leave as routes, and a headstock with six tuning pegs."""
    body_m = K.mat_plastic("modem", "lab_dark", 0.15)
    gloss = K.mat_plastic("modem_gloss", "shadow", 0.05)
    slot = K.mat_plastic("modem_slot", "shadow", 0.6)
    chrome = K.mat_chrome("modem_chrome")
    body = _bx("modem.body", body_m, gt, (0, -0.05, 0.05), (0.5, 0.3, 0.1), bev=0.02)
    _bx("modem.inset", gloss, gt, (-0.03, -0.05, 0.1005), (0.36, 0.24, 0.002), bev=0.004)
    for k in range(7):  # the vent grille, top right, behind the knobs
        _bx(f"modem.vent{k}", slot, gt, (0.19, -0.035 + 0.018 * k, 0.1008), (0.07, 0.008, 0.002))
    for sx in (-1, 1):
        for k in range(5):  # side vents
            _bx(f"modem.side_vent{sx}_{k}", slot, gt, (sx * 0.2505, -0.13 + 0.04 * k, 0.05), (0.002, 0.022, 0.05))
        # rear ports, either side of the neck
        _bx(f"modem.port{sx}", slot, gt, (sx * 0.16, 0.1005, 0.045), (0.05, 0.004, 0.028))
        _bx(f"modem.port_rim{sx}", chrome, gt, (sx * 0.16, 0.1002, 0.045), (0.058, 0.002, 0.036))
    _bx("modem.led_strip", gloss, gt, (0, -0.2002, 0.07), (0.3, 0.002, 0.026), bev=0.002)
    for k in range(6):  # front status LEDs, lit by the strum
        K.prop(gt, f"pluck{k}", 0.0)
        K.mesh_obj(f"modem.led{k}", bpy.ops.mesh.primitive_uv_sphere_add,
                   K.mat_emission(f"modem.led{k}", "amber", 30.0, gt, f"pluck{k}"), gt, radius=0.008,
                   location=(-0.12 + 0.048 * k, -0.201, 0.07))
    for sx in (-1, 1):  # antennas on hinge knuckles, with ball tips
        rot = Euler((-0.2, sx * 0.25, 0))
        mid = Vector((sx * 0.21, 0.07, 0.22))
        axis = rot.to_matrix() @ Vector((0, 0, 0.14))
        _cy(f"modem.antenna{sx}", K.mat_plastic("antenna", "lab_dark", 0.2), gt, mid, 0.011, 0.28, rot=rot)
        K.mesh_obj(f"modem.knuckle{sx}", bpy.ops.mesh.primitive_uv_sphere_add, chrome, gt, radius=0.02,
                   location=mid - axis)
        K.mesh_obj(f"modem.tip{sx}", bpy.ops.mesh.primitive_uv_sphere_add, chrome, gt, radius=0.014,
                   location=mid + axis)
    for k, y in enumerate((0.012, 0.062)):  # pickups under the strings, a pole piece per string
        _bx(f"modem.pickup{k}", gloss, gt, (0, y, 0.104), (0.14, 0.028, 0.01), bev=0.004)
        for st in range(STRINGS):
            K.mesh_obj(f"modem.pole{k}_{st}", bpy.ops.mesh.primitive_cylinder_add, chrome, gt, radius=0.004,
                       depth=0.003, location=(string_x(st), y, 0.1095))
    for k, y in enumerate((-0.16, -0.1)):  # volume and tone
        _cy(f"modem.knob{k}", chrome, gt, (0.19, y, 0.112), 0.018, 0.024, verts=32)
    # The neck: a rounded back, fret inlays, the nut with a ferrule per fiber, a headstock with six pegs.
    neck = _bx("modem.neck", K.mat_plastic("neck", "lab_dark", 0.2), gt, (0, 0.6, 0.085), (0.13, 0.95, 0.03),
               bev=0.006)
    back = _cy("modem.neck_back", K.mat_plastic("neck_back", "lab_dark", 0.2), gt, (0, 0.6, 0.074), 0.064, 0.93,
               rot=(math.pi / 2, 0, 0))
    back.scale = (1.0, 0.3, 1.0)
    pearl = K.mat_plastic("inlay", "paper", 0.1)
    for k in (1, 3, 5):
        K.mesh_obj(f"modem.inlay{k}", bpy.ops.mesh.primitive_cylinder_add, pearl, gt, radius=0.008, depth=0.002,
                   vertices=20, location=(0, 0.22 + 0.105 * k + 0.0525, 0.1003))
    K.mesh_obj("modem.nut", bpy.ops.mesh.primitive_cube_add, K.mat_chrome("nut"), gt, size=1,
               location=(0, NUT_Y, 0.108)).scale = (0.13, 0.015, 0.02)
    for st in range(STRINGS):
        K.mesh_obj(f"modem.ferrule{st}", bpy.ops.mesh.primitive_cylinder_add, chrome, gt, radius=0.0045,
                   depth=0.022, vertices=12, location=(string_x(st), NUT_Y + 0.012, STRING_Z),
                   rotation=(math.pi / 2, 0, 0))
    _bx("modem.headstock", K.mat_plastic("headstock", "lab_dark", 0.15), gt, (0, NUT_Y + 0.13, 0.082),
        (0.17, 0.22, 0.024), bev=0.01)
    for sx in (-1, 1):
        for k in range(3):
            y = NUT_Y + 0.07 + 0.06 * k
            _cy(f"modem.peg_post{sx}_{k}", chrome, gt, (sx * 0.06, y, 0.1), 0.006, 0.02, verts=12)
            _cy(f"modem.peg_shaft{sx}_{k}", chrome, gt, (sx * 0.1, y, 0.082), 0.004, 0.04, rot=(0, math.pi / 2, 0),
                verts=12)
            key = K.mesh_obj(f"modem.peg_key{sx}_{k}", bpy.ops.mesh.primitive_uv_sphere_add, chrome, gt,
                             radius=0.016, location=(sx * 0.128, y, 0.082))
            key.scale = (0.35, 1.0, 0.7)
    K.mesh_obj("modem.bridge", bpy.ops.mesh.primitive_cube_add, K.mat_chrome("bridge"), gt, size=1,
               location=(0, BRIDGE_Y, 0.108)).scale = (0.13, 0.02, 0.02)


def _amp():
    """The amp: an open server rack (chrome corner rails with holes, top and bottom plates, smoked acrylic sides)
    holding five 1U units with rack ears, drive bays and a row of status lights each (lit by "pump", the guitar
    stem), over a speaker module whose cone pumps."""
    amp = K.empty("amp", (0.85, 0.35, 0))
    amp.rotation_euler = (0, 0, math.radians(-25))
    K.prop(amp, "pump", 0.0)
    dark = K.mat_plastic("amp", "lab_dark", 0.2)
    chrome = K.mat_chrome("amp_chrome")
    slot = K.mat_plastic("amp_slot", "shadow", 0.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _bx(f"amp.rail{sx}{sy}", chrome, amp, (sx * 0.145, sy * 0.115, 0.3), (0.022, 0.022, 0.58), bev=0.003)
        for k in range(14):  # rail holes on the front rails
            _bx(f"amp.hole{sx}_{k}", slot, amp, (sx * 0.145, -0.1265, 0.06 + 0.038 * k), (0.008, 0.002, 0.008))
        _bx(f"amp.side{sx}", K.mat_acrylic("amp_side", "lab_glow", alpha=0.25, emit=0.1), amp,
            (sx * 0.158, 0, 0.3), (0.004, 0.23, 0.56))
    for z in (0.012, 0.588):
        _bx(f"amp.plate{z}", dark, amp, (0, 0, z), (0.32, 0.26, 0.024), bev=0.006)
    led = K.mat_emission("amp.leds", "lab_glow", 20.0, amp, "pump")
    for rr in range(5):
        z = 0.38 + 0.042 * rr
        _bx(f"amp.unit{rr}", dark, amp, (0, -0.005, z), (0.27, 0.24, 0.036), bev=0.004)
        for sx in (-1, 1):
            _bx(f"amp.ear{rr}{sx}", chrome, amp, (sx * 0.14, -0.126, z), (0.014, 0.004, 0.03))
        for c in range(6):
            K.mesh_obj(f"amp.led{rr}_{c}", bpy.ops.mesh.primitive_cube_add, led, amp, size=1,
                       location=(-0.1 + 0.04 * c, -0.131, z)).scale = (0.022, 0.004, 0.012)
    _bx("amp.speaker", dark, amp, (0, -0.005, 0.19), (0.27, 0.24, 0.29), bev=0.006)
    _bx("amp.baffle", slot, amp, (0, -0.126, 0.19), (0.25, 0.003, 0.26), bev=0.004)
    cone = K.empty("amp.cone_root", (0, -0.131, 0.18), amp)
    K.drive(cone, "scale", 1, amp, "pump", "1 + 3 * x")
    K.mesh_obj("amp.cone", bpy.ops.mesh.primitive_cone_add, K.mat_plastic("cone", "shadow", 0.5), cone, radius1=0.1,
               radius2=0.03, depth=0.03, location=(0, -0.012, 0), rotation=(math.pi / 2, 0, 0))
    K.mesh_obj("amp.dustcap", bpy.ops.mesh.primitive_uv_sphere_add, chrome, cone, radius=0.03,
               location=(0, -0.026, 0)).scale = (1, 0.4, 1)
    K.mesh_obj("amp.surround", bpy.ops.mesh.primitive_torus_add, K.mat_chrome("surround"), amp, major_radius=0.105,
               minor_radius=0.008, location=(0, -0.132, 0.18), rotation=(math.pi / 2, 0, 0))
    return amp


def build():
    P.floor_with_hole(K.floor(), PORTAL, 0.7)  # the portal is a real hole: the dive drops through it
    K.star_dome()
    out = {}

    # The map: a violet wireframe grid on the floor (faint), brighter every fourth line.
    grid = K.mat_emission("map_grid", "web2", 0.5)
    grid_hi = K.mat_emission("map_grid_hi", "web2", 1.4)
    x0, x1, y0, y1, step = -7.0, 7.0, -1.5, 11.0, 0.5
    for k in range(int((x1 - x0) / step) + 1):
        x = x0 + k * step
        g = K.mesh_obj(f"grid_x{k}", bpy.ops.mesh.primitive_cube_add, grid_hi if k % 4 == 0 else grid, None, size=1,
                       location=(x, (y0 + y1) / 2, 0.002))
        g.scale = (0.008, y1 - y0, 0.002)
    for k in range(int((y1 - y0) / step) + 1):
        y = y0 + k * step
        g = K.mesh_obj(f"grid_y{k}", bpy.ops.mesh.primitive_cube_add, grid_hi if k % 4 == 0 else grid, None, size=1,
                       location=(0, y, 0.002))
        g.scale = (x1 - x0, 0.008, 0.002)

    # The modem guitar: a dark modem body (status LEDs, two antennas) with a neck; six fiber strings.
    gt = K.empty("guitar", (0, 0, 0))
    out["guitar"] = gt
    _modem_guitar(gt)
    # Frets with handshake lights: one LED per fret on the neck's edge.
    for k in range(8):
        y = 0.22 + 0.105 * k
        K.mesh_obj(f"fret{k}", bpy.ops.mesh.primitive_cube_add, K.mat_chrome("fret"), gt, size=1,
                   location=(0, y, 0.101)).scale = (0.13, 0.004, 0.004)
        K.prop(gt, f"fret{k}", 0.04)
        K.mesh_obj(f"fret_led{k}", bpy.ops.mesh.primitive_uv_sphere_add,
                   K.mat_emission(f"fret_led{k}", "web", 40.0, gt, f"fret{k}"), gt, radius=0.009,
                   location=(0.078, y, 0.1))
    # Strings: glowing fiber from bridge to nut (vibrating on a pluck), then on as a fiber route into the map.
    nodes = {}
    for s in range(STRINGS):
        x = string_x(s)
        st = K.mesh_obj(f"string{s}", bpy.ops.mesh.primitive_cylinder_add,
                        K.mat_emission(f"string{s}", "web", 25.0, gt, f"pluck{s}"), gt, radius=0.0022,
                        depth=NUT_Y - BRIDGE_Y, vertices=8, location=(x, (NUT_Y + BRIDGE_Y) / 2, STRING_Z),
                        rotation=(math.pi / 2, 0, 0))
        K.drive(st, "scale", 0, gt, f"pluck{s}", "1 + 2.5 * x")
        K.drive(st, "scale", 1, gt, f"pluck{s}", "1 + 2.5 * x")
        fib = K.mat_emission(f"fiber{s}", "web2", 3.0)
        prev = Vector((x, NUT_Y, STRING_Z))
        for h in range(HOPS):
            p = node_pos(s, h)
            mid = (prev + p) / 2 + Vector((0, 0, 0.12 + 0.06 * h))
            _curve(f"hop{s}_{h}", [prev, mid, p], 0.005, fib)
            n = K.empty(f"node{s}_{h}", p)
            K.prop(n, "lit", 0.04)
            K.mesh_obj(f"node{s}_{h}.core", bpy.ops.mesh.primitive_uv_sphere_add,
                       K.mat_emission(f"node{s}_{h}.core", "web", 40.0, n, "lit"), n, radius=0.03, location=(0, 0, 0))
            halo = K.mesh_obj(f"node{s}_{h}.halo", bpy.ops.mesh.primitive_torus_add,
                              K.mat_emission(f"node{s}_{h}.halo", "web2", 20.0, n, "lit"), n, major_radius=0.08,
                              minor_radius=0.006, location=(0, 0, -0.02))
            halo.scale = (1, 1, 0.2)
            nodes[(s, h)] = n
            prev = p
    out["nodes"] = nodes

    # The dive route (S26) and the portal: a teal hole in the map, Platform's data center glowing below.
    _curve("dive_route", [tuple(p) for p in DIVE], 0.006, K.mat_emission("dive", "web2", 2.0),
           poly=True)
    # The portal: a round hole cut in the floor, a lined shaft with teal light rings, Platform's data center glowing
    # at the bottom: six small server racks round a lit floor (C5 placeholder pass: an opaque disc over teal posts
    # that could never be seen).
    depth = 1.6
    P.lathe("portal.shaft", K.mat_plastic("portal_shaft", "lab_dark", 0.6), None, PORTAL,
            [(0.7, 0.0), (0.7, -depth)], steps=96)
    glow = K.mat_emission("portal_glow", "platform", 4.0)
    for j, z in enumerate((-0.35, -0.75, -1.15)):
        K.smooth(K.mesh_obj(f"portal.band{j}", bpy.ops.mesh.primitive_torus_add, glow, None, major_radius=0.695,
                            minor_radius=0.008, major_segments=96, minor_segments=8,
                            location=PORTAL + Vector((0, 0, z))))
    K.mesh_obj("portal.disc", bpy.ops.mesh.primitive_circle_add, K.mat_emission("portal", "platform", 6.0), None,
               radius=0.7, vertices=96, fill_type="NGON", location=PORTAL + Vector((0, 0, -depth + 0.002)))
    K.smooth(K.mesh_obj("portal.ring", bpy.ops.mesh.primitive_torus_add, K.mat_chrome("portal_ring"), None,
                        major_radius=0.72, minor_radius=0.03, major_segments=96, minor_segments=16,
                        location=PORTAL + Vector((0, 0, 0.01))))
    body = K.mat_plastic("portal_rack", "lab_dark", 0.3)
    trim = K.mat_chrome("portal_rack_trim")
    led = K.mat_emission("portal_led", "platform", 8.0)
    grille = K.mat_plastic("portal_grille", "shadow", 0.5)
    for k in range(6):  # small server racks round the shaft floor, fronts to the middle
        a = math.tau * k / 6
        rack = K.empty(f"portal.rack{k}", PORTAL + Vector((math.cos(a) * 0.42, math.sin(a) * 0.42, -depth)))
        rack.rotation_euler = (0, 0, a - math.pi / 2)  # local -Y (its front) towards the centre
        P.box(f"portal.rack{k}.body", body, rack, (0, 0, 0.38), (0.2, 0.24, 0.76), bev=0.01, share="prack_body")
        P.box(f"portal.rack{k}.door", grille, rack, (0, -0.121, 0.38), (0.17, 0.004, 0.7), bev=0.002,
              share="prack_door")
        for u in range(6):  # 1U units with a teal status strip each
            z = 0.12 + u * 0.1
            P.box(f"portal.rack{k}.unit{u}", trim, rack, (0, -0.125, z), (0.16, 0.006, 0.06), bev=0.002,
                  share="prack_unit")
            P.box(f"portal.rack{k}.led{u}", led, rack, (-0.03, -0.1285, z), (0.07, 0.002, 0.008), share="prack_led")
        P.box(f"portal.rack{k}.top", trim, rack, (0, 0, 0.765), (0.21, 0.25, 0.012), bev=0.004, share="prack_top")
    # The amp: a server rack beside the guitar, LEDs and a speaker cone pumping with the guitar stem.
    out["amp"] = _amp()

    # The lead probe on the modem, by the strings; the bass floor ring around the guitar.
    out["lead"] = K.probe("lead", (-0.17, -0.12, 0.1 + K.PROBE_R * 1.6), led=0.6, scale=1.6)
    out["lead"].rotation_euler = (0, 0, math.radians(200))
    out["floor_ring"] = K.floor_ring("floor_ring", radius=1.2)
    pmat = K.mat_emission("pellet", "amber", 30.0)
    out["pellet_mat"] = pmat
    return out


def lights(S):
    # The map is its own light: key and fill only, at a third. No rims and no reflection cards: the rim strips
    # mirror in the floor as white slabs standing behind the guitar.
    L = K.LOOK["lights"]
    c = Vector((0, 0.8, 0.3))
    K.area_light("key", c + Vector((-0.55, -0.8, 0.75)) * 5, c, L["key"] * 0.35, 2.5, "key", shape="ELLIPSE",
                 specular=L["key_specular"])
    K.area_light("fill", c + Vector((0.9, -0.5, 0.2)) * 5, c, L["fill"] * 0.35, 3.0, "fill")


# ---------------------------------------------------------------- animation (config/instrument_map.json, set E)

def _string_of(e, lo, hi):
    return min(STRINGS - 1, int((e.get("pitch", lo) - lo) / max(1, hi - lo + 1) * STRINGS))


def _hop_pellet(S, name, curve, fl, fa):
    p = K.pellet_mesh(name, S["pellet_mat"], r=0.016)
    c = p.constraints.new("FOLLOW_PATH")
    c.target, c.use_fixed_location, c.use_curve_follow = curve, True, True
    curve.data.use_path = True  # Follow Path does nothing without it (the pellets sat still until C4 v5)
    A.write_keys(p, f'constraints["{c.name}"].offset_factor', [(fl, 0.0, "LINEAR"), (fa, 1.0, "LINEAR")],
                 interp="LINEAR")
    A.write_keys(p, "hide_render", [(0, 1, "CONSTANT"), (fl, 0, "CONSTANT"), (fa + 4, 1, "CONSTANT")],
                 interp="CONSTANT")
    return p


def animate(S, t0, t1):
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    f0, f1 = A.frame(t0 - 1), A.frame(t1 + 1)
    gt = S["guitar"]
    notes = W(A.events("guitar"))
    lo = min((e["pitch"] for e in notes), default=40)
    hi = max((e["pitch"] for e in notes), default=76)
    # Plucks: each note vibrates its string (pitch -> string) and lights its fret's handshake LED.
    for s in range(STRINGS):
        A.hit_flash(gt, f"pluck{s}", A.strikes([e for e in notes if _string_of(e, lo, hi) == s], 0.06), length=20)
    for k in range(8):
        A.led_pulse(gt, f"fret{k}", A.strikes([e for e in notes if e["pitch"] % 8 == k], 0.06))
    A.envelope_rig(S["amp"], "pump", A.envelope("guitar_env") ** 1.5, f0, f1)
    A.led_pulse(S["floor_ring"], "pulse", W(A.strikes(A.events("bass"), 0.05)))
    A.led_pulse(S["lead"], "led", W(A.strikes(A.events("kit"), 0.08)))
    # Route pellets: each strum fires one pellet a hop along its string's route; it reaches the node on the next strum
    # (or after 0.35 s, whichever is later), and that node lights and stays lit.
    shots = {s["id"]: s for s in A.timing_map()["shots"]}
    dive_t0 = shots["S26"]["cut"]
    strums = [e for e in A.strikes(notes, 0.12) if e["t"] < dive_t0]
    hop_n = [0] * STRINGS
    arrivals = {}
    for i, e in enumerate(strums):
        s = _string_of(e, lo, hi)
        h = hop_n[s] % HOPS
        hop_n[s] += 1
        fl = A.frame(e["t"])
        nxt = strums[i + 1]["t"] if i + 1 < len(strums) else e["t"] + 0.5
        fa = max(A.frame(nxt), fl + 21)
        _hop_pellet(S, f"pellet{i}", bpy.data.objects[f"hop{s}_{h}"], fl, fa)
        arrivals.setdefault((s, h), []).append(fa)
    for (s, h), n in S["nodes"].items():
        keys, cur = [(0, 0.04, "LINEAR")], 0.04
        for fa in sorted(arrivals.get((s, h), [])):
            keys += [(fa - 1, cur, "LINEAR"), (fa, 1.0, "LINEAR"), (fa + 30, 0.45, "LINEAR")]
            cur = 0.45
        A.write_keys(n, '["lit"]', keys, interp="LINEAR")
    # S26: one pellet leaves the middle string on the shot's first strum and rides the dive into the portal.
    end = shots["S27"]["cut"]
    p = K.pellet_mesh("dive_pellet", S["pellet_mat"], r=0.02)

    for u in DIVE_KEYS:
        p.location = _at(DIVE, u)
        p.keyframe_insert("location", frame=A.frame(dive_t0 + u * (end - dive_t0)))
    A.write_keys(p, "hide_render", [(0, 1, "CONSTANT"), (A.frame(dive_t0) - 1, 0, "CONSTANT")], interp="CONSTANT")


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


DIVE_KEYS = [k / 10 for k in range(11)]


def _chase():
    """S26: a camera chasing the dive pellet from behind and above, closing in as it drops into the portal."""
    keys = []
    for u in DIVE_KEYS:
        p = _at(DIVE, u)
        back = _at(DIVE, max(0.0, u - 0.06))
        d = (p - back).normalized() if (p - back).length > 1e-6 else Vector((0, 1, 0))
        eye = p - d * (0.7 - 0.45 * u) + Vector((0, 0, 0.35 - 0.15 * u))
        keys.append((u, eye, _at(DIVE, min(1.0, u + 0.04)), 28))
    return keys


CAMERAS = {
    # The modem guitar plays itself, close; then rise to see the routes lighting hop by hop across the map.
    "S25": [(0.0, _v(0.75, -0.75, 0.42), _v(0.0, 0.45, 0.1), 32), (0.35, _v(1.0, -0.9, 0.75), _v(0.0, 0.9, 0.1), 30),
            (1.0, _v(2.6, -2.2, 3.4), _v(0.0, 3.4, 0.0), 26)],
    "S26": _chase(),
}
