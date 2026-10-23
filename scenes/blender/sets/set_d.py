"""Set D, the SOC (brief, "Sets → D"): a security operations room with no one in it. C5: modelled.

Contents, as the brief lists them:
- a wall of alarm bells and siren horns, which are the drum kit: bells swing on snare and hats ("bell"), sirens
  flare on crash and toms ("glow", beacons turning);
- the counter: a large mechanical odometer over the wall that rolls to 17,600 by the end of "seventeen thousand
  moves" ("count"; real carries: the upper wheels click over whole digits);
- one empty chair, one desk with dark monitors, one pager on the desk: it buzzes across the desk on the kick
  ("walk" counts kicks, "buzz" shakes it) and falls off the edge on "you missed them all";
- red lights down the hall (a corridor on the left, its lamps pulsing on the beat); the floor ring (bass).
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import props_cde as P
import sr_anim as A
import sr_kit as K

WALL_Y = 2.0
DESK = Vector((0.2, 0.0, 0.76))     # desk-top centre
DESK_W = 1.7
PAGER0 = Vector((-0.3, -0.05, 0.0))  # pager start, relative to the desk top
ODO = Vector((0.0, WALL_Y - 0.12, 3.05))
ODO_R, ODO_PITCH = 0.36, 0.3
N_BELLS, N_SIRENS = 8, 4


def _odometer(out):
    """Five digit wheels behind a dark faceplate with one window, a comma between thousands and hundreds."""
    root = K.empty("odometer", ODO)
    K.prop(root, "count", 0.0, lo=0.0, hi=100000.0)
    face = K.mat_plastic("odo_face", "lab_dark", 0.6)
    ink = K.mat_plastic("odo_ink", "paper", 0.4)
    drum = K.mat_plastic("odo_drum", "shadow", 0.5)
    n = 5
    w = n * ODO_PITCH + 0.4
    for k, (x, z, sx, sz) in enumerate(((0, 0.34, w, 0.4), (0, -0.34, w, 0.4), (-w / 2 + 0.1, 0, 0.2, 0.3),
                                         (w / 2 - 0.1, 0, 0.2, 0.3))):
        o = K.mesh_obj(f"odometer.face{k}", bpy.ops.mesh.primitive_cube_add, face, root, size=1,
                       location=(x, -ODO_R - 0.04, z))
        o.scale = (sx, 0.04, sz)
        K.bevel(o, 0.012)
    back = K.mesh_obj("odometer.back", bpy.ops.mesh.primitive_cube_add, face, root, size=1, location=(0, 0.1, 0))
    back.scale = (w, 0.06, 1.1)
    K.bevel(back, 0.02)
    bolt = K.mat_chrome("odo_bolt")
    for bx in (-1, 1):  # chrome bolts at the faceplate's corners, and a chrome rim round the window
        for bz in (-1, 1):
            K.mesh_obj(f"odometer.bolt{bx}{bz}", bpy.ops.mesh.primitive_uv_sphere_add, bolt, root, radius=0.025,
                       location=(bx * (w / 2 - 0.06), -ODO_R - 0.065, bz * 0.46)).scale = (1, 0.5, 1)
    for k, (z, sx, sz) in enumerate(((0.15, w - 0.4, 0.012), (-0.15, w - 0.4, 0.012))):
        K.mesh_obj(f"odometer.rim{k}", bpy.ops.mesh.primitive_cube_add, bolt, root, size=1,
                   location=(0, -ODO_R - 0.062, z)).scale = (sx, 0.012, sz)
    for i in range(n):  # i = 0 is the units wheel (rightmost)
        x = (n - 1) / 2 * ODO_PITCH - i * ODO_PITCH - (0.06 if i >= 3 else 0.0)
        wheel = K.empty(f"odometer.wheel{i}", (x, 0, 0), root)
        # A tenth of a turn per digit, to 8 places: at 0.6283 the units wheel ends 17,600 half a digit off.
        expr = "-0.62831853 * x" if i == 0 else f"-0.62831853 * floor(x / {10 ** i})"
        K.drive(wheel, "rotation_euler", 0, root, "count", expr)
        K.mesh_obj(f"odometer.drum{i}", bpy.ops.mesh.primitive_cylinder_add, drum, wheel, radius=ODO_R - 0.01,
                   depth=ODO_PITCH * 0.86, vertices=40, rotation=(0, math.pi / 2, 0))
        for d in range(10):
            piv = K.empty(f"odometer.piv{i}_{d}", (0, 0, 0), wheel)
            piv.rotation_euler = (d * 0.62831853, 0, 0)
            K.text(f"odometer.d{i}_{d}", str(d), 0.24, ink, loc=(0, -ODO_R - 0.002, 0), parent=piv
                   ).data.offset = 0.004
        if i < 4:  # dividers
            K.mesh_obj(f"odometer.div{i}", bpy.ops.mesh.primitive_cube_add, face, root, size=1,
                       location=(x - ODO_PITCH / 2 - (0.03 if i == 2 else 0), -ODO_R - 0.04, 0)
                       ).scale = (0.03 if i != 2 else 0.09, 0.04, 0.3)
    comma_x = (n - 1) / 2 * ODO_PITCH - 2.5 * ODO_PITCH - 0.03
    K.text("odometer.comma", ",", 0.3, ink, loc=(comma_x, -ODO_R - 0.065, -0.07), parent=root).data.offset = 0.004
    out["odometer"] = root


BELL_PROFILE = [(0.0, 0.0), (0.05, 0.0), (0.085, -0.012), (0.11, -0.04), (0.124, -0.09), (0.134, -0.16),
                (0.158, -0.22), (0.198, -0.27), (0.224, -0.298), (0.229, -0.312), (0.218, -0.318), (0.19, -0.292),
                (0.15, -0.242), (0.12, -0.172), (0.108, -0.092), (0.088, -0.045), (0.0, -0.032)]
HORN_PROFILE = [(0.035, 0.0), (0.045, 0.06), (0.07, 0.16), (0.11, 0.25), (0.165, 0.3), (0.175, 0.31), (0.17, 0.316),
                (0.155, 0.305), (0.1, 0.255), (0.062, 0.165), (0.038, 0.065), (0.025, 0.0)]
DOME_PROFILE = [(0.0, 0.27), (0.04, 0.265), (0.08, 0.245), (0.105, 0.21), (0.116, 0.16), (0.118, 0.07), (0.0, 0.07)]


def _bell(i, loc, mats):
    """An alarm bell on a wall bracket: a turned brass bell (open mouth, flared lip, crown) hung from a yoke on a
    hinge, its clapper swinging with it; a bracket arm and a screwed wall plate behind ("bell" swings it)."""
    root = K.empty(f"bell{i}", loc)
    K.prop(root, "bell", 0.0, lo=-1.0, hi=1.0)
    P.box(f"bell{i}.plate", mats["dark"], root, (0, 0.235, 0.12), (0.16, 0.02, 0.22), bev=0.006, share="bell_plate")
    for sz in (-1, 1):
        P.cyl(f"bell{i}.screw{sz}", mats["chrome"], root, (0, 0.222, 0.12 + sz * 0.08), 0.01, 0.008,
              rot=(math.pi / 2, 0, 0), verts=16, share="bell_screw")
    P.box(f"bell{i}.bracket", mats["chrome"], root, (0, 0.11, 0.12), (0.045, 0.24, 0.045), bev=0.01,
          share="bell_bracket")
    hinge = K.empty(f"bell{i}.hinge", (0, -0.02, 0.12), root)
    K.drive(hinge, "rotation_euler", 0, root, "bell", "0.6 * x")
    P.cyl(f"bell{i}.pin", mats["chrome"], hinge, (0, 0, 0), 0.016, 0.09, rot=(0, math.pi / 2, 0), verts=20,
          share="bell_pin")
    P.box(f"bell{i}.yoke", mats["brass"], hinge, (0, 0, 0.0), (0.12, 0.04, 0.035), bev=0.008, share="bell_yoke")
    P.lathe(f"bell{i}.dome", mats["brass"], hinge, (0, 0, -0.02), BELL_PROFILE, steps=56, share="bell")
    P.lathe(f"bell{i}.rim", mats["brass"], hinge, (0, 0, -0.02), [(0.0, 0.012), (0.03, 0.012), (0.035, 0.0),
                                                                   (0.03, -0.006), (0.0, -0.006)], share="bell_crown")
    P.cyl(f"bell{i}.rod", mats["chrome"], hinge, (0, 0, -0.14), 0.006, 0.2, verts=12, share="bell_rod")
    K.smooth(K.mesh_obj(f"bell{i}.clapper", bpy.ops.mesh.primitive_uv_sphere_add, mats["chrome"], hinge, radius=0.035,
                        segments=24, ring_count=12, location=(0, 0, -0.25)))
    return root


def _siren(i, loc, mats):
    """A rotating alarm beacon over a horn speaker, on a wall bracket: a stepped base, a tall red lens dome with a
    chrome cap and cage ribs (the dome glows with "glow"; the reflector turns inside), and a flared horn with its
    driver housing below."""
    root = K.empty(f"siren{i}", loc)
    K.prop(root, "glow", 0.05)
    P.box(f"siren{i}.bracket", mats["dark"], root, (0, 0.11, -0.1), (0.09, 0.22, 0.05), bev=0.01, share="siren_brk")
    P.box(f"siren{i}.wallplate", mats["dark"], root, (0, 0.21, -0.12), (0.2, 0.02, 0.36), bev=0.008,
          share="siren_plate")
    P.lathe(f"siren{i}.base", mats["dark"], root, (0, 0, 0), [(0.0, -0.05), (0.15, -0.05), (0.157, -0.042),
                                                              (0.157, 0.03), (0.14, 0.05), (0.125, 0.05),
                                                              (0.125, 0.07), (0.0, 0.07)], share="siren_base")
    spin = K.empty(f"siren{i}.spin", (0, 0, 0.05), root)
    P.lathe(f"siren{i}.dome", K.mat_emission(f"siren{i}.dome", "alarm", 30.0, root, "glow"), root, (0, 0, 0),
            DOME_PROFILE, steps=48)
    P.lathe(f"siren{i}.cap", mats["chrome"], root, (0, 0, 0.262), [(0.0, 0.03), (0.03, 0.028), (0.045, 0.012),
                                                                   (0.05, 0.0), (0.0, 0.0)], share="siren_cap")
    for r in range(6):  # cage ribs over the lens
        a = r * math.tau / 6
        P.box(f"siren{i}.rib{r}", mats["chrome"], root, (math.cos(a) * 0.121, math.sin(a) * 0.121, 0.165),
                    (0.006, 0.006, 0.19), bev=0.002, rot=(0, 0, a), share="siren_rib")
    P.lathe(f"siren{i}.band", mats["chrome"], root, (0, 0, 0.07), [(0.12, 0.0), (0.128, 0.004), (0.128, 0.018),
                                                                   (0.12, 0.022)], share="siren_band")
    K.mesh_obj(f"siren{i}.mirror", bpy.ops.mesh.primitive_cube_add, mats["chrome"], spin, size=1,
               location=(0, 0, 0.07)).scale = (0.18, 0.012, 0.09)
    P.box(f"siren{i}.stalk", mats["dark"], root, (0, 0.0, -0.14), (0.045, 0.045, 0.18), bev=0.008, share="siren_stalk")
    P.cyl(f"siren{i}.driver", mats["dark"], root, (0, 0.06, -0.25), 0.065, 0.11, rot=(math.pi / 2, 0, 0), verts=32,
          bev=0.01, share="siren_driver")
    P.lathe(f"siren{i}.horn", mats["chrome"], root, (0, 0.005, -0.25), HORN_PROFILE, rot=(math.pi / 2, 0, 0),
            steps=48, share="siren_horn")
    return root


def _box(name, mat, parent, loc, size, bev=0.0, rot=(0, 0, 0)):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc, rotation=rot)
    o.scale = size
    if bev:
        K.bevel(o, bev)
    return o


def _cyl(name, mat, parent, loc, r, depth, rot=(0, 0, 0), verts=24):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cylinder_add, mat, parent, radius=r, depth=depth, vertices=verts,
                   location=loc, rotation=rot)
    K.smooth(o)
    return o


def _desk(mats):
    """An operator's desk: a glossy top with rounded edges and a chrome front banding, on chrome tube legs with
    levelling glides, a back rail and a modesty panel; a drawer pedestal under the left end (the pager falls off the
    right end, between the legs) with inset drawer fronts on a toe kick and bar pulls on standoffs; two dark monitors
    on stands, flashing ALERT."""
    P.box("desk.top", mats["dark"], None, DESK - Vector((0, 0, 0.02)), (DESK_W, 0.8, 0.04), bev=0.008)
    P.box("desk.edge", mats["chrome"], None, DESK - Vector((0, 0.401, 0.02)), (DESK_W - 0.02, 0.006, 0.014), bev=0.002)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = DESK.x + sx * (DESK_W / 2 - 0.06), sy * 0.33
            P.cyl(f"desk.leg{sx}{sy}", mats["chrome"], None, (x, y, (DESK.z - 0.04) / 2), 0.022, DESK.z - 0.04,
                  share="desk_leg")
            P.lathe(f"desk.foot{sx}{sy}", mats["dark"], None, (x, y, 0.0), [(0.0, 0.0), (0.032, 0.0), (0.034, 0.004),
                                                                            (0.03, 0.012), (0.018, 0.016),
                                                                            (0.018, 0.03), (0.0, 0.03)],
                    share="desk_foot")
            P.box(f"desk.bracket{sx}{sy}", mats["chrome"], None, (x, y, DESK.z - 0.05), (0.07, 0.07, 0.02),
                  bev=0.004, share="desk_bracket")
    P.cyl("desk.rail", mats["chrome"], None, (DESK.x, 0.33, 0.18), 0.016, DESK_W - 0.12, rot=(0, math.pi / 2, 0))
    P.box("desk.modesty", mats["dark"], None, (DESK.x, 0.355, 0.5), (DESK_W - 0.16, 0.02, 0.38), bev=0.005)
    # Drawer pedestal, left end: a carcass on a recessed toe kick, three inset drawer fronts with bar pulls.
    px = DESK.x - DESK_W / 2 + 0.3
    P.box("desk.pedestal", mats["dark"], None, (px, -0.02, 0.39), (0.4, 0.66, 0.62), bev=0.006)
    P.box("desk.toe", mats["shadow"], None, (px, 0.0, 0.04), (0.37, 0.6, 0.08), bev=0.003)
    for k in range(3):
        z = 0.18 + 0.2 * k
        P.box(f"desk.drawer{k}", mats["dark"], None, (px, -0.355, z), (0.37, 0.012, 0.185), bev=0.004,
              share="desk_drawer")
        P.box(f"desk.handle{k}", mats["chrome"], None, (px, -0.381, z + 0.055), (0.14, 0.01, 0.012), bev=0.004,
              share="desk_handle")
        for hx in (-1, 1):
            P.cyl(f"desk.standoff{k}{hx}", mats["chrome"], None, (px + hx * 0.06, -0.368, z + 0.055), 0.004, 0.018,
                  rot=(math.pi / 2, 0, 0), verts=12, share="desk_standoff")
    screen = K.mat_emission("monitor_screen", "alarm", 0.6)
    bezel = K.mat_plastic("monitor_bezel", "shadow", 0.15)
    stand = K.mat_plastic("monitor_stand", "lab_dark", 0.3)
    for k, x in enumerate((-0.55, 0.0)):
        c = DESK + Vector((x, 0.25, 0.27))
        # The panel: a slim bezel with a raised lip round the glass, a chin with the power button and its LED.
        P.box(f"monitor{k}", bezel, None, c + Vector((0, 0.006, 0)), (0.52, 0.03, 0.34), bev=0.008, share="mon_panel")
        for j, (dx, dz, w, h) in enumerate(((0, 0.1535, 0.5, 0.017), (0, -0.1485, 0.5, 0.007), (-0.2425, 0, 0.015, 0.29),
                                            (0.2425, 0, 0.015, 0.29))):
            P.box(f"monitor{k}.lip{j}", bezel, None, c + Vector((dx, -0.011, dz)), (w, 0.006, h), bev=0.002)
        P.box(f"monitor{k}.back", bezel, None, c + Vector((0, 0.055, -0.01)), (0.34, 0.07, 0.22), bev=0.025,
              segments=4, share="mon_back")
        for v in range(5):  # vent slots on the back housing
            P.box(f"monitor{k}.vent{v}", K.mat_plastic("monitor_vent", "shadow", 0.6), None,
                  c + Vector((-0.1 + v * 0.05, 0.091, 0.05)), (0.03, 0.002, 0.09), bev=0.001, share="mon_vent")
        K.mesh_obj(f"monitor{k}.screen", bpy.ops.mesh.primitive_plane_add, screen, None, size=1,
                   location=c + Vector((0, -0.0105, 0)), rotation=(math.pi / 2, 0, 0)).scale = (0.47, 0.29, 1)
        K.text(f"monitor{k}.text", "ALERT", 0.07, K.mat_emission(f"monitor{k}.ink", "paper", 3.0),
               loc=c + Vector((0, -0.014, 0)))
        # The stand: a hinge barrel under the back housing, a flat arm, a rounded foot plate.
        P.cyl(f"monitor{k}.hinge", mats["chrome"], None, DESK + Vector((x, 0.31, 0.16)), 0.016, 0.07,
              rot=(0, math.pi / 2, 0), verts=24, share="mon_hinge")
        P.box(f"monitor{k}.neck", stand, None, DESK + Vector((x, 0.31, 0.085)), (0.055, 0.024, 0.15), bev=0.008,
              share="mon_neck")
        P.box(f"monitor{k}.foot", stand, None, DESK + Vector((x, 0.28, 0.007)), (0.24, 0.17, 0.014), bev=0.006,
              segments=4, share="mon_foot")
        K.mesh_obj(f"monitor{k}.led", bpy.ops.mesh.primitive_uv_sphere_add,
                   K.mat_emission(f"monitor{k}.led", "lab_glow", 12.0), None, radius=0.005,
                   location=c + Vector((0.23, -0.011, -0.155)))
        P.cyl(f"monitor{k}.button", mats["chrome"], None, c + Vector((0.205, -0.0115, -0.155)), 0.006, 0.004,
              rot=(math.pi / 2, 0, 0), verts=16, share="mon_button")


def _chair(mats):
    """The empty office chair, turned a little from the desk: a five-star base on casters, a gas column in a
    sleeve, a tilt plate, a padded seat and backrest on a chrome spine, two armrests."""
    chair = K.empty("chair", DESK + Vector((0.75, -0.75, -0.76)))
    chair.rotation_euler = (0, 0, math.radians(25))
    pad = K.mat_plastic("chair_seat", "lab_dark", 0.55)
    _cyl("chair.hub", mats["dark"], chair, (0, 0, 0.085), 0.05, 0.05)
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        c, s_ = math.cos(a), math.sin(a)
        _box(f"chair.foot{k}", mats["chrome"], chair, (c * 0.16, s_ * 0.16, 0.075), (0.3, 0.045, 0.028), bev=0.008,
             rot=(0, -0.08, a))
        _box(f"chair.fork{k}", mats["dark"], chair, (c * 0.3, s_ * 0.3, 0.05), (0.03, 0.03, 0.04))
        _cyl(f"chair.caster{k}", mats["dark"], chair, (c * 0.3, s_ * 0.3, 0.025), 0.025, 0.022, rot=(0, math.pi / 2, a))
    _cyl("chair.sleeve", mats["dark"], chair, (0, 0, 0.18), 0.032, 0.16)
    _cyl("chair.post", mats["chrome"], chair, (0, 0, 0.33), 0.022, 0.16)
    _box("chair.plate", mats["dark"], chair, (0, 0, 0.415), (0.24, 0.24, 0.03), bev=0.006)
    _box("chair.seat", pad, chair, (0, 0.01, 0.47), (0.5, 0.48, 0.08), bev=0.03)
    _box("chair.spine", mats["chrome"], chair, (0, -0.25, 0.56), (0.06, 0.02, 0.26), bev=0.006, rot=(-0.12, 0, 0))
    _box("chair.back", pad, chair, (0, -0.29, 0.88), (0.46, 0.07, 0.5), bev=0.03, rot=(-0.12, 0, 0))
    for sx in (-1, 1):
        _box(f"chair.arm_post{sx}", mats["chrome"], chair, (sx * 0.26, -0.02, 0.58), (0.025, 0.04, 0.2), bev=0.005)
        _box(f"chair.arm{sx}", pad, chair, (sx * 0.26, -0.01, 0.69), (0.07, 0.28, 0.035), bev=0.012)
    return chair


def build():
    K.floor()
    out = {}
    mats = {"chrome": K.mat_chrome("soc_chrome"), "brass": K.mat_metal("bell_brass", "brass", 0.06),
            "dark": K.mat_plastic("soc_dark", "lab_dark", 0.2),
            "shadow": K.mat_plastic("soc_shadow", "shadow", 0.5), "wall": K.mat_plastic("soc_wall", "lab_dark", 0.75)}
    K.mesh_obj("soc_wall", bpy.ops.mesh.primitive_cube_add, mats["wall"], None, size=1,
               location=(0, WALL_Y + 0.05, 1.9)).scale = (7.0, 0.1, 3.8)
    _odometer(out)
    # Bells in two rows across the wall, sirens at the ends and in the middle.
    bells = []
    for k in range(N_BELLS):
        x = -2.1 + (k % 4) * 1.4 + (0.7 if k >= 4 else 0)
        z = 2.0 if k < 4 else 1.35
        if k >= 4 and k % 4 == 3:
            x -= 2.8
        bells.append(_bell(k, (x - 0.35, WALL_Y - 0.25, z), mats))
    out["bells"] = bells
    sirens = []
    for k, (x, z) in enumerate(((-2.9, 2.5), (2.9, 2.5), (-1.2, 0.75), (1.6, 0.75))):
        s = _siren(k, (x, WALL_Y - 0.2, z), mats)
        s.rotation_euler = (math.radians(-12), 0, 0)
        sirens.append(s)
    out["sirens"] = sirens

    # The desk, its dark monitors, the empty chair, the pager.
    _desk(mats)
    desk = K.empty("desk")  # at the origin: one assembly for the desk and its monitors, transforms unchanged
    for o in list(bpy.data.objects):
        if o.parent is None and o is not desk and (o.name.startswith("desk.") or o.name.startswith("monitor")):
            o.parent = desk
    out["chair"] = _chair(mats)
    pager = K.empty("pager", DESK + PAGER0)
    K.prop(pager, "walk", 0.0, lo=0.0, hi=1000.0)
    K.prop(pager, "buzz", 0.0)
    slide = K.empty("pager.slide", (0, 0, 0), pager)
    out["pager_slide"] = slide
    shake = K.empty("pager.shake", (0, 0, 0), slide)
    K.drive(shake, "rotation_euler", 2, pager, "buzz", "0.25 * x * sin(frame * 2.7)")
    K.drive(shake, "location", 2, pager, "buzz", "0.006 * x * abs(sin(frame * 3.3))")
    # A 90s belt pager (human, C5: the old one "looks very boxy"; then "make it black with a green-ish monochrome
    # display so it's more obvious"): a rounded black body, a recessed grey bezel round the green LCD showing the page
    # (dimly lit at rest, its backlight flaring with "buzz"), three keys, a red alert LED, a lanyard eyelet, and a belt
    # clip underneath. The body keeps the old one's size and centre, so the walk and the fall are unchanged.
    dark = K.mat_plastic("pager_bezel", "lab_dark", 0.4)
    P.box("pager.body", K.mat_plastic("pager_body", "shadow", 0.45), shake, (0, 0, 0.02), (0.13, 0.08, 0.035),
          bev=0.011, segments=4)
    P.box("pager.bezel", dark, shake, (-0.012, 0, 0.0375), (0.094, 0.058, 0.004), bev=0.0018)
    K.mesh_obj("pager.screen", bpy.ops.mesh.primitive_plane_add,
               K.mat_emission("pager_screen", "lcd", 3.0, pager, "buzz", floor=0.3), shake, size=1,
               location=(-0.012, 0, 0.0397)).scale = (0.08, 0.045, 1)
    lcd = K.mat_ink("pager_lcd", "shadow")
    K.text("pager.msg", "ALERT 17600", 0.0105, lcd, loc=(-0.012, 0.007, 0.0399), rot=(0, 0, 0),
           font="JetBrainsMono-SemiBold-flat.ttf", parent=shake)
    K.text("pager.msg2", "CALL SOC NOW", 0.0095, lcd, loc=(-0.012, -0.009, 0.0399), rot=(0, 0, 0),
           font="JetBrainsMono-SemiBold-flat.ttf", parent=shake)
    for j, y in enumerate((-0.022, 0.0, 0.022)):
        P.lathe(f"pager.key{j}", dark, shake, (0.048, y, 0.0365), [(0.0, 0.0045), (0.0045, 0.0042), (0.0062, 0.002),
                                                                   (0.0065, 0.0), (0.0, 0.0)], steps=24,
                share="pager_key")
    K.smooth(K.mesh_obj("pager.led", bpy.ops.mesh.primitive_uv_sphere_add,
                        K.mat_emission("pager_led", "alarm", 40.0, pager, "buzz"), shake, radius=0.0035, segments=16,
                        ring_count=8, location=(0.05, 0.034, 0.0365)))
    P.cyl("pager.eyelet", dark, shake, (-0.068, 0.025, 0.02), 0.006, 0.012, rot=(0, math.pi / 2, 0), verts=16)
    P.box("pager.clip", K.mat_metal("pager_clip", "chrome", 0.3), shake, (0.005, 0, 0.0038), (0.085, 0.05, 0.0025),
          bev=0.001)
    for g in range(4):  # grip ridges along the near side
        P.box(f"pager.grip{g}", dark, shake, (-0.03 + g * 0.012, -0.0402, 0.02), (0.004, 0.002, 0.02), bev=0.0008,
              share="pager_grip")
    out["pager"] = pager

    # Red lights down the hall: a corridor wall on the left, lamps receding.
    K.mesh_obj("hall_wall", bpy.ops.mesh.primitive_cube_add, mats["wall"], None, size=1,
               location=(-3.6, -4.0, 1.5)).scale = (0.1, 12.0, 3.0)
    hall = K.empty("hall_lights")
    K.prop(hall, "glow", 0.2)
    red = K.mat_emission("hall_red", "alarm", 25.0, hall, "glow")
    # Caged bulkhead lamps on the corridor wall: a wall plate, a red glass dome glowing on the beat, a chrome cage.
    cage = K.mat_chrome("hall_cage")
    for k in range(8):
        lamp = K.empty(f"hall_lamp{k}", (-3.55, 1.0 - k * 1.5, 2.6))
        P.box(f"hall_lamp{k}.plate", mats["dark"], lamp, (0.01, 0, 0), (0.02, 0.2, 0.26), bev=0.006, share="hall_plate")
        P.lathe(f"hall_lamp{k}.base", mats["dark"], lamp, (0.02, 0, 0), [(0.0, 0.0), (0.095, 0.0), (0.095, 0.02),
                                                                          (0.085, 0.03), (0.0, 0.03)],
                rot=(0, math.pi / 2, 0), share="hall_base")
        P.lathe(f"hall_lamp{k}.glass", red, lamp, (0.045, 0, 0), [(0.0, 0.0), (0.075, 0.0), (0.078, 0.03),
                                                                  (0.072, 0.07), (0.055, 0.1), (0.03, 0.115),
                                                                  (0.0, 0.12)], rot=(0, math.pi / 2, 0),
                share="hall_glass")
        hoops = ((0.088, 0.065), (0.085, 0.105), (0.068, 0.145))
        for j, (r, x) in enumerate(hoops):  # cage hoops, clear of the glass
            K.smooth(K.mesh_obj(f"hall_lamp{k}.hoop{j}", bpy.ops.mesh.primitive_torus_add, cage, lamp,
                                major_radius=r, minor_radius=0.004, major_segments=48, minor_segments=8,
                                location=(x, 0, 0), rotation=(0, math.pi / 2, 0)))
        for j in range(4):  # cage bars from the first hoop to the last
            a = j * math.pi / 2 + math.pi / 4
            c, s_ = math.cos(a), math.sin(a)
            P.rod(f"hall_lamp{k}.bar{j}", cage, lamp, (hoops[0][1], c * hoops[0][0], s_ * hoops[0][0]),
                  (hoops[2][1], c * hoops[2][0], s_ * hoops[2][0]), 0.0035)
    out["hall"] = hall
    out["floor_ring"] = K.floor_ring("floor_ring_d", radius=1.6, loc=(0.2, -0.3, 0.001))
    return out


# ---------------------------------------------------------------- animation (config/instrument_map.json, set D)

def animate(S, t0, t1):
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    tm = A.timing_map()
    line = {ln["id"]: ln for ln in tm["lines"]}
    kit = A.events("kit")
    # Bells: snare and hats, round-robin; sirens: crash and toms.
    ring = W(A.strikes(A.pieces(kit, "snare", "hats"), 0.06))
    for k, b in enumerate(S["bells"]):
        A.bell(b, "bell", ring[k::len(S["bells"])], min_len=40, cycles_per_s=3.0)
    flare = W(A.strikes(A.pieces(kit, "crash", "toms"), 0.06))
    for k, s in enumerate(S["sirens"]):
        A.led_pulse(s, "glow", flare[k::2] if k < 2 else flare[1 - k % 2::2], floor=0.05)
        spin = bpy.data.objects[f"siren{k}.spin"]
        A.write_keys(spin, "rotation_euler", [(A.frame(t0 - 1), 0.0), (A.frame(t1 + 1), (t1 - t0 + 2) * 9.0)],
                     index=2, interp="LINEAR")
    # Hall lights on the beat; floor ring on the bass.
    A.led_pulse(S["hall"], "glow", W(A.events("beats")), floor=0.15)
    A.led_pulse(S["floor_ring"], "pulse", W(A.strikes(A.events("bass"), 0.05)))
    # The odometer rolls 0 -> 17,600 across "seventeen thousand moves," (decelerating onto the last digit).
    l27 = line["L27"]
    moves = next(w for w in l27["words"] if w["w"].lower().startswith("moves"))
    A.write_keys(S["odometer"], A.prop_path("count"), [(A.frame(l27["start"]), 0.0, "LINEAR"),
                                                       (A.frame(moves["end"]) - 20, 16900.0, "BEZIER"),
                                                       (A.frame(moves["end"]), 17600.0, "BEZIER")])
    # The pager buzzes across the desk on each kick and falls off the edge on "all." (end of "you missed them all").
    fall_w = next(w for w in l27["words"] if w["w"].lower().startswith("all"))
    t_fall = fall_w["start"]
    kicks = A.strikes(A.pieces(A.between(kit, t0 - 1, t_fall), "kick"), 0.08)
    A.stepper(S["pager"], "walk", kicks, pre=6, settle=10, overshoot=0.1)
    # Its screen keeps flashing on the floor (the kicks after the fall, until the shot ends).
    after = A.strikes(A.pieces(A.between(kit, t_fall + 0.7, t1 + 1), "kick"), 0.08)
    A.hit_flash(S["pager"], "buzz", kicks + after, length=24)
    edge = DESK_W / 2 - PAGER0.x + 0.02  # walk from the start to the desk's edge over all the kicks
    K.drive(S["pager_slide"], "location", 0, S["pager"], "walk", f"{edge / max(1, len(kicks)):.5f} * x")
    # The fall moves the root; the flip turns the slide, which carries the walked-off distance, so the pager turns
    # about itself (turning the root swung it in a 1 m circle through the floor, C4 v4).
    pg, sl = S["pager"], S["pager_slide"]
    p0 = pg.location.copy()
    for dt, d, rot in ((0.0, (0, 0, 0), (0, 0, 0)), (0.25, (0.08, -0.04, -0.2), (0, 1.6, 0.2)),
                       (0.5, (0.14, -0.08, -0.62), (0.2, 4.7, 0.5)), (0.6, (0.15, -0.09, -0.70), (0.1, 6.0, 0.5)),
                       (0.7, (0.15, -0.09, -0.761), (0.0, 6.283, 0.5))):  # one full flip, landing face up on the floor
                       # (its clip 1.5 mm above it; -0.74 left it hovering 2 cm, C5 placeholder pass)
        pg.location, sl.rotation_euler = p0 + Vector(d), rot
        pg.keyframe_insert("location", frame=A.frame(t_fall + dt))
        sl.keyframe_insert("rotation_euler", frame=A.frame(t_fall + dt))


def lights(S):
    K.studio_lights(center=(0, 0.5, 1.4), radius=6.5, scale=0.8)
    K.reflection_cards(center=(0, 0.5, 1.4), radius=7.0)
    K.area_light("alarm_wash", (0.0, -1.5, 3.8), (0.0, WALL_Y, 1.5), 900, 3.0, "alarm", specular=0.2)
    K.area_light("desk_lamp", DESK + Vector((-0.6, -0.6, 1.2)), DESK, 120, 0.6, "key", specular=0.3)


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


CAMERAS = {
    # The wall plays the drum part; push in past the empty chair to the buzzing pager.
    "S18": [(0.0, _v(-1.6, -4.2, 2.0), _v(0.0, WALL_Y, 1.7), 26), (0.55, _v(-1.4, -2.8, 1.6), _v(0.0, 0.6, 1.2), 28),
            (1.0, DESK + _v(-0.45, -1.0, 0.35), DESK + _v(0.2, 0.0, 0.0), 40)],
    # The odometer rolls to 17,600; down to the desk edge as the pager falls beside the chair.
    "S19": [(0.0, ODO + _v(0.1, -3.4, -0.5), ODO, 40), (0.55, ODO + _v(0.0, -3.1, -0.45), ODO, 42),
            (0.68, DESK + _v(2.1, -0.9, 0.45), DESK + _v(0.8, -0.15, -0.35), 32),
            (1.0, DESK + _v(2.0, -0.8, 0.3), DESK + _v(0.9, -0.2, -0.5), 34)],
}
