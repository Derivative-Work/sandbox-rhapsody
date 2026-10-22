"""Set D, the SOC (brief, "Sets → D"): a security operations room with no one in it. Grey-box for C4.

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
        K.mesh_obj(f"odometer.face{k}", bpy.ops.mesh.primitive_cube_add, face, root, size=1,
                   location=(x, -ODO_R - 0.04, z)).scale = (sx, 0.04, sz)
    K.mesh_obj("odometer.back", bpy.ops.mesh.primitive_cube_add, face, root, size=1,
               location=(0, 0.1, 0)).scale = (w, 0.06, 1.1)
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


def _bell(i, loc, mats):
    root = K.empty(f"bell{i}", loc)
    K.prop(root, "bell", 0.0, lo=-1.0, hi=1.0)
    K.mesh_obj(f"bell{i}.bracket", bpy.ops.mesh.primitive_cube_add, mats["chrome"], root, size=1,
               location=(0, 0.1, 0.12)).scale = (0.04, 0.2, 0.04)
    hinge = K.empty(f"bell{i}.hinge", (0, -0.02, 0.12), root)
    K.drive(hinge, "rotation_euler", 0, root, "bell", "0.6 * x")
    b = K.mesh_obj(f"bell{i}.dome", bpy.ops.mesh.primitive_uv_sphere_add, mats["brass"], hinge, radius=0.22,
                   location=(0, 0, -0.06))
    b.scale = (1, 1, 0.75)
    K.smooth(b)
    K.mesh_obj(f"bell{i}.rim", bpy.ops.mesh.primitive_torus_add, mats["brass"], hinge, major_radius=0.215,
               minor_radius=0.015, location=(0, 0, -0.08))
    K.mesh_obj(f"bell{i}.clapper", bpy.ops.mesh.primitive_uv_sphere_add, mats["chrome"], root, radius=0.04,
               location=(0, -0.05, -0.12))
    return root


def _siren(i, loc, mats):
    root = K.empty(f"siren{i}", loc)
    K.prop(root, "glow", 0.05)
    K.mesh_obj(f"siren{i}.base", bpy.ops.mesh.primitive_cylinder_add, mats["dark"], root, radius=0.14, depth=0.1,
               location=(0, 0, 0))
    spin = K.empty(f"siren{i}.spin", (0, 0, 0.05), root)
    K.mesh_obj(f"siren{i}.dome", bpy.ops.mesh.primitive_uv_sphere_add,
               K.mat_emission(f"siren{i}.dome", "alarm", 30.0, root, "glow"), root, radius=0.12,
               location=(0, 0, 0.1))
    K.mesh_obj(f"siren{i}.mirror", bpy.ops.mesh.primitive_cube_add, mats["chrome"], spin, size=1,
               location=(0, 0, 0.07)).scale = (0.18, 0.012, 0.09)
    horn = K.mesh_obj(f"siren{i}.horn", bpy.ops.mesh.primitive_cone_add, mats["chrome"], root, radius1=0.16,
                      radius2=0.04, depth=0.3, location=(0, -0.12, -0.25), rotation=(math.pi / 2, 0, 0))
    K.smooth(horn)
    return root


def build():
    K.floor()
    out = {}
    mats = {"chrome": K.mat_chrome("soc_chrome"), "brass": K.mat_metal("bell_brass", "brass", 0.06),
            "dark": K.mat_plastic("soc_dark", "lab_dark", 0.2), "wall": K.mat_plastic("soc_wall", "lab_dark", 0.75)}
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
    K.mesh_obj("desk.top", bpy.ops.mesh.primitive_cube_add, mats["dark"], None, size=1,
               location=DESK - Vector((0, 0, 0.02))).scale = (DESK_W, 0.8, 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.mesh_obj(f"desk.leg{sx}{sy}", bpy.ops.mesh.primitive_cube_add, mats["chrome"], None, size=1,
                       location=DESK + Vector((sx * (DESK_W / 2 - 0.05), sy * 0.35, -0.39))).scale = (0.04, 0.04, 0.74)
    screen = K.mat_emission("monitor_screen", "alarm", 0.6)
    for k, x in enumerate((-0.55, 0.0)):
        K.mesh_obj(f"monitor{k}", bpy.ops.mesh.primitive_cube_add, mats["dark"], None, size=1,
                   location=DESK + Vector((x, 0.25, 0.25))).scale = (0.5, 0.04, 0.32)
        K.mesh_obj(f"monitor{k}.screen", bpy.ops.mesh.primitive_plane_add, screen, None, size=1,
                   location=DESK + Vector((x, 0.228, 0.25)), rotation=(math.pi / 2, 0, 0)).scale = (0.46, 0.28, 1)
        K.text(f"monitor{k}.text", "ALERT", 0.07, K.mat_emission(f"monitor{k}.ink", "paper", 3.0),
               loc=DESK + Vector((x, 0.224, 0.25)))
    chair = K.empty("chair", DESK + Vector((0.75, -0.75, -0.76)))
    chair.rotation_euler = (0, 0, math.radians(25))
    seat_m = K.mat_plastic("chair_seat", "lab", 0.3)
    K.mesh_obj("chair.seat", bpy.ops.mesh.primitive_cube_add, seat_m, chair, size=1,
               location=(0, 0, 0.48)).scale = (0.48, 0.46, 0.07)
    K.mesh_obj("chair.back", bpy.ops.mesh.primitive_cube_add, seat_m, chair, size=1,
               location=(0, -0.22, 0.82)).scale = (0.46, 0.06, 0.55)
    K.mesh_obj("chair.post", bpy.ops.mesh.primitive_cylinder_add, mats["chrome"], chair, radius=0.025, depth=0.42,
               location=(0, 0, 0.23))
    for k in range(5):
        a = k * math.tau / 5
        foot = K.mesh_obj(f"chair.foot{k}", bpy.ops.mesh.primitive_cube_add, mats["chrome"], chair, size=1,
                          location=(math.cos(a) * 0.15, math.sin(a) * 0.15, 0.04), rotation=(0, 0, a))
        foot.scale = (0.3, 0.03, 0.03)
    out["chair"] = chair
    pager = K.empty("pager", DESK + PAGER0)
    K.prop(pager, "walk", 0.0, lo=0.0, hi=1000.0)
    K.prop(pager, "buzz", 0.0)
    slide = K.empty("pager.slide", (0, 0, 0), pager)
    out["pager_slide"] = slide
    shake = K.empty("pager.shake", (0, 0, 0), slide)
    K.drive(shake, "rotation_euler", 2, pager, "buzz", "0.25 * x * sin(frame * 2.7)")
    K.drive(shake, "location", 2, pager, "buzz", "0.006 * x * abs(sin(frame * 3.3))")
    body = K.mesh_obj("pager.body", bpy.ops.mesh.primitive_cube_add, K.mat_plastic("pager_body", "lab", 0.2),
                      shake, size=1, location=(0, 0, 0.02))
    body.scale = (0.13, 0.08, 0.035)
    K.bevel(body, 0.008)
    K.mesh_obj("pager.screen", bpy.ops.mesh.primitive_plane_add,
               K.mat_emission("pager_screen", "alarm", 12.0, pager, "buzz"), shake, size=1,
               location=(-0.01, 0, 0.0376)).scale = (0.08, 0.045, 1)
    out["pager"] = pager

    # Red lights down the hall: a corridor wall on the left, lamps receding.
    K.mesh_obj("hall_wall", bpy.ops.mesh.primitive_cube_add, mats["wall"], None, size=1,
               location=(-3.6, -4.0, 1.5)).scale = (0.1, 12.0, 3.0)
    hall = K.empty("hall_lights")
    K.prop(hall, "glow", 0.2)
    red = K.mat_emission("hall_red", "alarm", 25.0, hall, "glow")
    for k in range(8):
        K.mesh_obj(f"hall_lamp{k}", bpy.ops.mesh.primitive_cube_add, red, None, size=1,
                   location=(-3.53, 1.0 - k * 1.5, 2.6)).scale = (0.04, 0.5, 0.08)
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
    pg = S["pager"]
    p0 = pg.location.copy()
    for dt, d, rot in ((0.0, (0, 0, 0), (0, 0, 0)), (0.25, (0.08, -0.04, -0.25), (0, 1.6, 0.2)),
                       (0.5, (0.14, -0.08, -0.74), (0.2, 5.6, 0.5)), (0.6, (0.15, -0.09, -0.70), (0.1, 6.1, 0.5)),
                       (0.7, (0.15, -0.09, -0.74), (0.0, 6.283, 0.5))):  # one full flip, landing face up
        pg.location, pg.rotation_euler = p0 + Vector(d), rot
        pg.keyframe_insert("location", frame=A.frame(t_fall + dt))
        pg.keyframe_insert("rotation_euler", frame=A.frame(t_fall + dt))


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
