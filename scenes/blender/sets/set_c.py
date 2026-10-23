"""Set C, the Street (brief, "Sets → C"): the open web outside the warehouse. Grey-box for C4.

Contents, as the brief lists them:
- a night street of magenta-lit kiosks: paste boards, request-capture mailboxes and file-drop lockers, seven a
  side; each kiosk's door unlocks and swings open on its note in S14 ("open", plus a lock flash);
- the fourteen keys: fourteen brass keys on the pavement down the middle of the street; the lead probe picks up one
  per piano note in S13 and hangs it on a ring under itself (the HUD counts 1/14 -> 14/14);
- the rented launchpad: a floating platform past the end of the street, another company's property, with a
  generic `RENTED` plate; in S24 the probe lands on it and a camp of crates drops into place, one per kick/snare;
- a floor ring on the launchpad (bass).
Deterministic: placement is arithmetic, never random.
"""
import math

import bpy
from mathutils import Vector

import sr_anim as A
import sr_kit as K

N_KEYS = 14
KIOSK_W, KIOSK_D, KIOSK_H = 1.1, 0.9, 2.1
KIOSK_X, KIOSK_Y0, KIOSK_DY = 2.1, 0.6, 1.75
PAD = Vector((0.0, 15.5, 1.1))
PAD_R = 1.6
SIGNS = ["PASTE BOARD", "REQUESTS", "FILE DROP", "MAIL", "PASTE BOARD", "UPLOADS", "OPEN 24/7"]


def _key(name, mat, loc=(0, 0, 0), rot_z=0.0, parent=None, s=1.0):
    """A brass key ~10 cm long lying flat along +X: bow ring, shaft, bit."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = (0, 0, rot_z)
    root.scale = (s, s, s)
    K.mesh_obj(f"{name}.bow", bpy.ops.mesh.primitive_torus_add, mat, root, major_radius=0.018, minor_radius=0.006,
               location=(-0.04, 0, 0.006))
    K.mesh_obj(f"{name}.shaft", bpy.ops.mesh.primitive_cylinder_add, mat, root, radius=0.005, depth=0.07, vertices=10,
               location=(0.0, 0, 0.006), rotation=(0, math.pi / 2, 0))
    K.mesh_obj(f"{name}.bit", bpy.ops.mesh.primitive_cube_add, mat, root, size=1,
               location=(0.028, -0.01, 0.006)).scale = (0.014, 0.02, 0.006)
    return root


def _box(name, mat, parent, loc, size, bev=0.0):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc)
    o.scale = size
    if bev:
        K.bevel(o, bev, 2)
    return o


KINDS = {"PASTE BOARD": "board", "REQUESTS": "mailbox", "MAIL": "mailbox", "FILE DROP": "lockers",
         "UPLOADS": "lockers", "OPEN 24/7": "booth"}


def _kiosk(i, side, y, mats):
    """A kiosk facing the street; local front is -Y. "open" (0-1) swings its door out; "flash" lights its lock.
    One of four kinds by its sign (brief, Sets -> C): a pastebin noticeboard, a request-capture mailbox, a bank of
    file-drop lockers, an all-night booth. Each is a recessed cabinet (a lit cavity behind the door, with what it
    holds), on a plinth, under a roof cap, with a framed glowing sign."""
    name = f"kiosk{i}"
    label = SIGNS[i % len(SIGNS)]
    kind = KINDS[label]
    W, D, H = KIOSK_W, KIOSK_D, KIOSK_H
    root = K.empty(name, (side * KIOSK_X, y, 0))
    root.rotation_euler = (0, 0, -side * math.pi / 2)  # front (-Y local) toward the street
    K.prop(root, "open", 0.0)
    K.prop(root, "flash", 0.0)
    body, trim = mats["body"], mats["trim"]
    # Cabinet: a back block, and a front frame (jambs, lintel, sill) around the door opening (x +-0.45, z 0.2-1.7).
    _box(f"{name}.plinth", mats["dark"], root, (0, D / 2, 0.05), (W + 0.08, D + 0.08, 0.1), 0.01)
    _box(f"{name}.body", body, root, (0, (0.12 + D) / 2, H / 2 + 0.05), (W, D - 0.12, H - 0.1), 0.02)
    for sx in (-1, 1):
        _box(f"{name}.jamb{sx}", body, root, (sx * (W / 2 - 0.05), 0.06, H / 2 + 0.05), (0.1, 0.12, H - 0.1), 0.01)
    _box(f"{name}.lintel", body, root, (0, 0.06, (1.7 + H) / 2 + 0.025), (W - 0.2, 0.12, H - 1.65), 0.01)
    _box(f"{name}.sill", body, root, (0, 0.06, 0.15), (W - 0.2, 0.12, 0.1), 0.01)
    # Lit cavity behind the door, with what this kind holds.
    _box(f"{name}.inside", mats["inside"], root, (0, 0.118, 0.95), (0.9, 0.004, 1.5))
    for k in range(3):
        _box(f"{name}.shelf{k}", trim, root, (0, 0.09, 0.55 + 0.45 * k), (0.88, 0.06, 0.012))
        for j in range(3 if kind != "booth" else 1):
            if kind == "lockers":  # parcels
                _box(f"{name}.parcel{k}{j}", mats["copper"], root, (-0.27 + 0.27 * j, 0.09, 0.62 + 0.45 * k),
                     (0.2, 0.05, 0.13), 0.005)
            elif kind == "mailbox":  # stacks of envelopes
                _box(f"{name}.env{k}{j}", mats["paper"], root, (-0.27 + 0.27 * j, 0.09, 0.59 + 0.45 * k),
                     (0.22, 0.05, 0.07))
            elif kind == "board":  # stacks of pasted pages
                _box(f"{name}.stack{k}{j}", mats["paper"], root, (-0.27 + 0.27 * j, 0.09, 0.6 + 0.45 * k),
                     (0.18, 0.05, 0.1))
    if kind == "booth":  # a terminal glowing at the back
        _box(f"{name}.terminal", mats["web"], root, (0, 0.1, 1.15), (0.36, 0.02, 0.24))
    # Roof cap (a rounded hood on a mailbox), and the sign in a chrome frame above.
    if kind == "mailbox":
        hood = K.mesh_obj(f"{name}.hood", bpy.ops.mesh.primitive_cylinder_add, body, root, radius=W / 2 + 0.04,
                          depth=D + 0.1, vertices=32, location=(0, D / 2, H), rotation=(math.pi / 2, 0, 0))
        hood.scale = (1, 0.35, 1)
        K.smooth(hood)
    else:
        _box(f"{name}.roof", mats["dark"], root, (0, D / 2 - 0.03, H + 0.03), (W + 0.14, D + 0.16, 0.06), 0.015)
    sign_z = H + (0.36 if kind == "mailbox" else 0.27)  # clear of the mailbox hood
    _box(f"{name}.sign", mats["sign_back"], root, (0, -0.03, sign_z), (W, 0.06, 0.32), 0.01)
    for sz in (-1, 1):
        _box(f"{name}.sign_trim{sz}", trim, root, (0, -0.065, sign_z + sz * 0.165), (W + 0.02, 0.012, 0.02))
    t = K.text(f"{name}.sign_text", label, 0.15, mats["web"] if i % 2 else mats["web2"], loc=(0, -0.065, sign_z),
               parent=root)
    t.data.offset = 0.004
    # Side louvres on both flanks.
    for sx in (-1, 1):
        for k in range(5):
            _box(f"{name}.louvre{sx}{k}", mats["dark"], root, (sx * (W / 2 + 0.006), D * 0.55, 1.45 + 0.07 * k),
                 (0.012, D * 0.5, 0.025))
    # The door on its hinge (rig unchanged): a panel with an inset, a chrome pull, the brass lock and its light.
    hinge = K.empty(f"{name}.hinge", (-W * 0.4, -0.012, 0.2), root)
    K.drive(hinge, "rotation_euler", 2, root, "open", "-1.75 * x")
    _box(f"{name}.door", mats["door"], hinge, (W * 0.4, 0, 0.75), (W * 0.8, 0.03, 1.5), 0.008)
    _box(f"{name}.inset", mats["inset"], hinge, (W * 0.4, -0.017, 0.75), (W * 0.66, 0.006, 1.32), 0.004)
    _box(f"{name}.pull", trim, hinge, (W * 0.72, -0.04, 0.6), (0.025, 0.025, 0.3), 0.006)
    K.mesh_obj(f"{name}.lock", bpy.ops.mesh.primitive_cylinder_add, mats["brass"], hinge, radius=0.03, depth=0.02,
               location=(W * 0.72, -0.025, 0.8), rotation=(math.pi / 2, 0, 0))
    _box(f"{name}.keyhole", mats["dark"], hinge, (W * 0.72, -0.036, 0.8), (0.006, 0.004, 0.022))
    K.mesh_obj(f"{name}.lock_light", bpy.ops.mesh.primitive_uv_sphere_add,
               K.mat_emission(f"{name}.lock_light", "amber", 50.0, root, "flash"), hinge, radius=0.018,
               location=(W * 0.72, -0.03, 0.88))
    if kind == "board":  # a pinboard on the door, pages pinned to it; more pages pasted on the street-side flank
        _box(f"{name}.cork", mats["cork"], hinge, (W * 0.4, -0.024, 1.0), (W * 0.62, 0.008, 0.7))
        for k in range(5):
            x, z = W * 0.4 + (-0.2 + 0.1 * k), 1.0 + (0.18 if k % 2 else -0.12)
            _box(f"{name}.page{k}", mats["paper"], hinge, (x, -0.03, z), (0.13, 0.004, 0.17))
            K.mesh_obj(f"{name}.pin{k}", bpy.ops.mesh.primitive_uv_sphere_add, mats["pin"], hinge, radius=0.01,
                       location=(x, -0.036, z + 0.07))
        for k in range(4):
            _box(f"{name}.paste{k}", mats["paper"], root, (W / 2 + 0.004, 0.2 + (k % 2) * 0.32, 0.9 + (k // 2) * 0.4),
                 (0.006, 0.26, 0.3))
    elif kind == "mailbox":  # a letter slot with a chrome lip, and a red flag on the flank
        _box(f"{name}.slot", mats["dark"], hinge, (W * 0.4, -0.026, 1.35), (0.4, 0.008, 0.035))
        _box(f"{name}.lip", trim, hinge, (W * 0.4, -0.032, 1.38), (0.44, 0.012, 0.015))
        flag = K.empty(f"{name}.flag", (W / 2 + 0.03, 0.4, 1.3), root)
        flag.rotation_euler = (0.9, 0, 0)  # up: requests waiting
        _box(f"{name}.flag_arm", trim, flag, (0, 0, 0.18), (0.012, 0.025, 0.36))
        _box(f"{name}.flag_tab", mats["pin"], flag, (0, -0.06, 0.32), (0.014, 0.12, 0.08))
    elif kind == "lockers":  # louvred locker door with a number plate; a bank of small lockers on the flank
        for k in range(6):
            _box(f"{name}.vent{k}", mats["dark"], hinge, (W * 0.4, -0.024, 1.35 + 0.05 * k), (0.4, 0.006, 0.018))
        _box(f"{name}.number", mats["paper"], hinge, (W * 0.4, -0.024, 1.15), (0.14, 0.006, 0.07))
        for r in range(3):
            for c in range(2):
                y0, z0 = 0.27 + 0.36 * c, 0.45 + 0.5 * r
                _box(f"{name}.cubby{r}{c}", mats["inset"], root, (W / 2 + 0.008, y0, z0), (0.012, 0.32, 0.44), 0.004)
                _box(f"{name}.cubby_pull{r}{c}", trim, root, (W / 2 + 0.02, y0 - 0.1, z0), (0.012, 0.02, 0.1))
    elif kind == "booth":  # a window in the door, and an awning over the front
        _box(f"{name}.window", mats["glass"], hinge, (W * 0.4, -0.026, 1.25), (W * 0.6, 0.008, 0.5))
        aw = K.empty(f"{name}.awning", (0, -0.05, H - 0.02), root)
        aw.rotation_euler = (0.35, 0, 0)  # sloping down toward the street
        for k in range(5):  # stripes, alternating
            _box(f"{name}.awning{k}", mats["web_dark"] if k % 2 else mats["door"], aw,
                 (-W / 2 + W * (k + 0.5) / 5, -0.25, 0), (W / 5, 0.5, 0.02))
    return root


def build():
    K.floor()
    K.star_dome()
    out = {}
    mats = {"body": K.mat_plastic("kiosk_body", "lab_dark", 0.2), "door": K.mat_plastic("kiosk_door", "web2", 0.15),
            "inside": K.mat_emission("kiosk_inside", "key", 2.5), "brass": K.mat_metal("kiosk_brass", "brass", 0.15),
            "sign_back": K.mat_plastic("sign_back", "shadow", 0.4), "web": K.mat_emission("sign_web", "web", 6.0),
            "web2": K.mat_emission("sign_web2", "web", 4.0), "paper": K.mat_matte("paste", "paper"),
            "trim": K.mat_chrome("kiosk_trim"), "dark": K.mat_plastic("kiosk_dark", "shadow", 0.3),
            "inset": K.mat_plastic("kiosk_inset", "web", 0.2), "cork": K.mat_matte("kiosk_cork", "copper"),
            "pin": K.mat_plastic("kiosk_pin", "alarm", 0.2), "copper": K.mat_plastic("kiosk_parcel", "copper", 0.4),
            "glass": K.mat_acrylic("kiosk_glass", "web2", alpha=0.35, emit=0.6),
            "web_dark": K.mat_plastic("kiosk_awning", "shadow", 0.3)}
    kiosks = []
    for k in range(7):
        for side in (-1, 1):
            kiosks.append(_kiosk(len(kiosks), side, KIOSK_Y0 + k * KIOSK_DY + (0.4 if side > 0 else 0), mats))
    out["kiosks"] = kiosks  # near to far, alternating sides
    # Kerbs and a centre line, so it reads as a street.
    kerb = K.mat_plastic("kerb", "lab_dark", 0.3)
    for side in (-1, 1):
        K.mesh_obj(f"kerb{side}", bpy.ops.mesh.primitive_cube_add, kerb, None, size=1,
                   location=(side * 1.55, 6.5, 0.04)).scale = (0.12, 16.0, 0.08)
    line = K.mat_emission("centre_line", "web", 1.5)
    for k in range(9):
        K.mesh_obj(f"centre{k}", bpy.ops.mesh.primitive_cube_add, line, None, size=1,
                   location=(0.75, -1.0 + k * 1.7, 0.003)).scale = (0.05, 0.7, 0.004)
    # Street lamps: magenta glow heads on chrome posts.
    lamp = K.mat_emission("street_lamp", "web", 20.0)
    post_m = K.mat_plastic("lamp_post", "lab_dark", 0.5)
    for k, (x, y) in enumerate(((-1.45, 2.4), (1.45, 5.9), (-1.45, 9.4), (1.45, 12.9))):
        K.mesh_obj(f"lamp_post{k}", bpy.ops.mesh.primitive_cylinder_add, post_m, None, radius=0.025, depth=3.0,
                   location=(x, y, 1.5))
        K.mesh_obj(f"lamp_head{k}", bpy.ops.mesh.primitive_uv_sphere_add, lamp, None, radius=0.09,
                   location=(x, y, 3.05))

    # The fourteen keys, down the middle of the street (a fixed zig-zag).
    brass = K.mat_metal("key_brass", "brass", 0.12)
    keys = []
    for k in range(N_KEYS):
        x = 0.22 * math.sin(k * 2.1)
        y = 0.4 + k * 0.28
        keys.append(_key(f"key{k}", brass, (x, y, 0.0), rot_z=k * 1.3, s=1.6))
    out["keys"] = keys
    # The lead probe with a key ring hanging under it; ring keys appear as they're picked up.
    p = K.probe("lead_c", (keys[0].location.x, keys[0].location.y - 0.6, 0.16), led=0.7)
    out["lead"] = p
    ring = K.empty("key_ring", (0, 0, -K.PROBE_R - 0.02), p)
    K.mesh_obj("key_ring.loop", bpy.ops.mesh.primitive_torus_add, K.mat_chrome("key_ring"), ring, major_radius=0.012,
               minor_radius=0.002)
    held = []
    for k in range(N_KEYS):
        a = math.radians(-70 + 140 * k / (N_KEYS - 1))
        h = _key(f"held{k}", brass, (0, 0, 0), parent=ring, s=0.6)
        h.rotation_euler = (0, a + math.pi / 2, math.pi / 2)  # hang down, fanned
        h.location = (math.sin(a) * 0.01, 0, -0.01)
        h.scale = (0, 0, 0)
        held.append(h)
    out["held"] = held

    # The rented launchpad, floating past the end of the street.
    # A saucer: a bevelled deck on a tapering hull with a glowing keel, a chrome rim, landing markings, four thruster
    # nacelles, beacon posts round the edge, and a rental plate on two posts at the front (C5).
    pad = K.empty("launchpad", PAD)
    hull_m, chrome = K.mat_plastic("pad_hull", "lab_dark", 0.25), K.mat_chrome("pad_chrome")
    deck = K.mesh_obj("launchpad.deck", bpy.ops.mesh.primitive_cylinder_add, K.mat_plastic("pad_deck", "lab", 0.2),
                      pad, radius=PAD_R, depth=0.12, vertices=64, location=(0, 0, -0.06))
    K.bevel(deck, 0.02, 3)
    K.mesh_obj("launchpad.rim", bpy.ops.mesh.primitive_torus_add, chrome, pad, major_radius=PAD_R,
               minor_radius=0.035, major_segments=96, location=(0, 0, -0.04))
    hull = K.mesh_obj("launchpad.hull", bpy.ops.mesh.primitive_cone_add, hull_m, pad, radius1=0.5,
                      radius2=PAD_R * 0.96, depth=0.5, vertices=64, location=(0, 0, -0.37))
    K.smooth(hull)
    K.mesh_obj("launchpad.keel", bpy.ops.mesh.primitive_cylinder_add, K.mat_emission("pad_keel", "lab_glow", 6.0),
               pad, radius=0.42, depth=0.04, vertices=48, location=(0, 0, -0.63))
    paint = K.mat_matte("pad_paint", "paper")
    K.mesh_obj("launchpad.stripe", bpy.ops.mesh.primitive_torus_add, paint, pad, major_radius=PAD_R - 0.12,
               minor_radius=0.02, major_segments=96, location=(0, 0, 0.0)).scale = (1, 1, 0.2)
    for k in range(16):  # a dashed landing circle
        a = k * math.tau / 16
        _box(f"launchpad.dash{k}", paint, pad, (math.cos(a) * 0.95, math.sin(a) * 0.95, 0.002), (0.05, 0.22, 0.004)
             ).rotation_euler = (0, 0, a)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = math.cos(a) * 1.05, math.sin(a) * 1.05
        nac = K.mesh_obj(f"launchpad.nacelle{k}", bpy.ops.mesh.primitive_cylinder_add, chrome, pad, radius=0.15,
                         depth=0.32, vertices=32, location=(x, y, -0.28))
        K.smooth(nac)
        K.mesh_obj(f"launchpad.thruster{k}", bpy.ops.mesh.primitive_cone_add, K.mat_emission(f"thr{k}", "lab_glow", 8),
                   pad, radius1=0.16, radius2=0.11, depth=0.12, location=(x, y, -0.49))
    for k in range(10):  # beacon posts round the rim, the front left open for the plate
        a = math.radians(-60 + 24 * k)
        x, y = math.sin(a) * (PAD_R - 0.08), math.cos(a) * (PAD_R - 0.08)
        K.mesh_obj(f"launchpad.post{k}", bpy.ops.mesh.primitive_cylinder_add, chrome, pad, radius=0.015, depth=0.3,
                   vertices=12, location=(x, y, 0.15))
        K.mesh_obj(f"launchpad.beacon{k}", bpy.ops.mesh.primitive_uv_sphere_add,
                   K.mat_emission("pad_beacon", "rim", 10.0), pad, radius=0.025, location=(x, y, 0.31))
    # The rental plate: generic, someone else's.
    for sx in (-1, 1):
        K.mesh_obj(f"rented.post{sx}", bpy.ops.mesh.primitive_cylinder_add, chrome, pad, radius=0.02, depth=0.8,
                   location=(sx * 0.42, -PAD_R + 0.15, 0.4))
    _box("rented.frame", chrome, pad, (0.0, -PAD_R + 0.135, 0.74), (0.9, 0.025, 0.36), 0.006)
    _box("rented.plate", K.mat_matte("rented_plate", "decal_film"), pad, (0.0, -PAD_R + 0.12, 0.74), (0.84, 0.03, 0.3))
    K.text("rented.text", "RENTED", 0.17, K.mat_ink("rented_ink", "shadow"), loc=(0.0, -PAD_R + 0.1, 0.77),
           parent=pad).data.offset = 0.006
    K.text("rented.small", "LEASED UNIT  ·  NOT YOURS", 0.035, K.mat_ink("rented_ink2", "shadow"),
           loc=(0.0, -PAD_R + 0.1, 0.65), parent=pad)
    out["pad"] = pad
    out["floor_ring"] = K.floor_ring("floor_ring_c", radius=PAD_R - 0.2, loc=PAD + Vector((0, 0, 0.002)))
    # Camp crates (placed by animate(): they drop in on the kit).
    crate_m = K.mat_plastic("camp_crate", "copper", 0.3)
    strap_m = K.mat_chrome("camp_strap")
    crates = []
    slots = [(x, y, 0) for y in (-0.3, 0.0, 0.3) for x in (-0.3, 0.0, 0.3)]
    slots += [(x, y, 1) for y in (-0.15, 0.15) for x in (-0.15, 0.15)]
    slots += [(0.0, 0.0, 2)]
    slots += [(0.75, 0.55, 0), (0.75, 0.25, 0), (-0.75, 0.55, 0), (-0.75, 0.25, 0), (0.75, 0.4, 1)]
    for k, (x, y, z) in enumerate(slots):
        c = K.mesh_obj(f"camp{k}", bpy.ops.mesh.primitive_cube_add, crate_m, None, size=0.28,
                       location=PAD + Vector((x, y + 0.3, 0.14 + z * 0.28)))
        K.bevel(c, 0.01, 2)
        for sz in (-1, 1):  # two chrome straps round each crate
            _box(f"camp{k}.strap{sz}", strap_m, c, (0, sz * 0.07, 0), (0.29, 0.02, 0.29))
        crates.append(c)
    out["crates"] = crates
    return out


# ---------------------------------------------------------------- animation (config/instrument_map.json, set C)

def pickup_events():
    """The 14 notes the keys are picked up on, all inside S13 so the HUD runs 1/14 -> 14/14 in the shot (C4 v3: it
    opened on 2/14). Only 12 piano notes fall inside the shot, so the widest gaps between them take the guitar strike
    nearest their middle until there are 14."""
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    a, b = shot["S13"]["cut"], shot["S14"]["cut"]
    evs = A.strikes(A.between(A.events("piano"), a + 0.03, b), 0.05)
    guitar = A.strikes(A.between(A.events("guitar"), a + 0.03, b), 0.05)
    while len(evs) < N_KEYS:
        gaps = [(evs[k + 1]["t"] - evs[k]["t"], k) for k in range(len(evs) - 1)]
        _, k = max(gaps)
        mid = (evs[k]["t"] + evs[k + 1]["t"]) / 2
        g = min((e for e in guitar if evs[k]["t"] + 0.1 < e["t"] < evs[k + 1]["t"] - 0.1),
                key=lambda e: abs(e["t"] - mid))
        evs.insert(k + 1, g)
    return evs[:N_KEYS]


def door_events():
    """The 14 kiosk unlocks: guitar strikes inside "and every one worked fine.", 14 spread evenly over them."""
    g = A.strikes(A.in_line(A.events("guitar"), "and every one"), 0.05)
    if len(g) <= N_KEYS:
        return g
    return [g[round(i * (len(g) - 1) / (N_KEYS - 1))] for i in range(N_KEYS)]


def animate(S, t0, t1):
    A.sing(S["lead"], t0, t1)  # the protagonist sings
    W = lambda evs: A.between(evs, t0 - 1, t1 + 1)  # noqa: E731
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    # S13: the probe walks the keys, one pickup per note.
    pick = pickup_events()
    p = S["lead"]
    t13 = shot["S13"]["cut"]
    p.location = S["keys"][0].location + Vector((0, -0.7, 0.18))
    p.keyframe_insert("location", frame=A.frame(pick[0]["t"] - 0.8))
    arm = []
    for k, e in enumerate(pick):
        kl = S["keys"][k].location
        f = A.frame(e["t"])
        p.location = kl + Vector((0, -0.05, 0.12))
        p.keyframe_insert("location", frame=f)
        arm += [(f - 6, 0.2), (f, 1.0, "LINEAR"), (f + 8, 0.3)]
        # The key leaves the ground into the probe's hand, then appears on the ring.
        key = S["keys"][k]
        A.write_keys(key, "location", [(f - 6, kl.z), (f, kl.z + 0.06, "LINEAR")], index=2)
        for ax in range(3):
            A.write_keys(key, "scale", [(f, 1.6, "CONSTANT"), (f + 1, 0.0, "CONSTANT")], index=ax)
        for ax in range(3):
            A.write_keys(S["held"][k], "scale", [(f, 0.0, "CONSTANT"), (f + 1, 0.6, "LINEAR"), (f + 6, 0.6)], index=ax)
    A.write_keys(p, A.prop_path("arm_r"), A._merge([[k] for k in arm]))
    # After the last key: up and away down the street (S14 opens on the kiosks).
    last = S["keys"][-1].location
    p.location = last + Vector((0, 0.6, 0.6))
    p.keyframe_insert("location", frame=A.frame(pick[-1]["t"] + 1.0))
    # S14: kiosk doors unlock in sequence, near to far.
    for k, (kio, e) in enumerate(zip(S["kiosks"], door_events())):
        f = A.frame(e["t"])
        A.write_keys(kio, A.prop_path("open"), [(f, 0.0), (f + 10, 1.08), (f + 22, 1.0)])
        A.hit_flash(kio, "flash", [e], length=30)
    # S24: the probe flies to the launchpad and lands; the camp drops in, one crate per kick/snare.
    t24 = shot["S24"]["cut"]
    for t, loc in ((t24 - 0.2, PAD + Vector((0.4, -4.0, 0.9))), (t24 + 1.4, PAD + Vector((0.6, -0.9, 0.5))),
                   (t24 + 2.0, PAD + Vector((0.6, -0.9, K.PROBE_R)))):
        p.location = loc
        p.keyframe_insert("location", frame=A.frame(t))
    hits = A.strikes(A.pieces(A.between(A.events("kit"), t24 + 1.0, shot["S24"]["cut"] + 7.0), "kick", "snare"), 0.08)
    for c, e in zip(S["crates"], hits):
        f = A.frame(e["t"])
        z = c.location.z
        A.write_keys(c, "location", [(0, z + 3.0, "CONSTANT"), (f - 16, z + 3.0, "BEZIER"), (f, z, "LINEAR"),
                                     (f + 4, z + 0.03), (f + 8, z)], index=2)
        A.write_keys(c, "hide_render", [(0, 1, "CONSTANT"), (f - 16, 0, "CONSTANT")], interp="CONSTANT")
    # The probe directs each drop with its arm.
    A.striker(p, "arm_l", hits, wind=10, settle=20)
    for c in S["crates"][len(hits):]:  # more slots than hits: the rest stay away
        c.hide_render = True
    A.envelope_rig(p, "led", A.envelope("vocal_env") ** 2.0, A.frame(t0 - 1), A.frame(t1 + 1), gain=0.6, offset=0.3)
    A.led_pulse(S["floor_ring"], "pulse", W(A.strikes(A.events("bass"), 0.05)))


def lights(S):
    K.studio_lights(center=(0, 6.0, 1.0), radius=9.0, scale=0.7)
    K.reflection_cards(center=(0, 6.0, 1.0), radius=10.0)
    for k, y in enumerate((1.0, 5.0, 9.0, 13.0)):  # magenta street glow
        K.area_light(f"street{k}", (0.0, y, 3.0), (0.0, y, 0.0), 700, 2.5, "web", specular=0.2)
    K.area_light("keys_key", (-1.2, 1.0, 2.2), (0.0, 2.2, 0.0), 500, 1.5, "key", specular=0.0)
    K.area_light("pad_key", PAD + Vector((-2.0, -3.0, 3.0)), PAD, 900, 2.0, "key", specular=0.4)


# ---------------------------------------------------------------- cameras (u = fraction of the shot; eye, target, lens)

def _v(*a):
    return Vector(a)


CAMERAS = {
    # Low, beside the probe as it walks the keys up the street (keys set by _resolve from the pickups).
    "S13": [],
    # Down the street from above: fourteen doors swing open in sequence, near to far.
    "S14": [(0.0, _v(0.0, -2.4, 3.4), _v(0.0, 6.0, 0.6), 24), (1.0, _v(0.0, -1.2, 3.2), _v(0.0, 7.0, 0.6), 24)],
    # The probe reaches the rented launchpad; the camp drops in.
    "S24": [(0.0, PAD + _v(0.3, -5.4, 1.4), PAD + _v(0.4, -2.0, 0.5), 30),
            (0.3, PAD + _v(0.5, -3.2, 1.2), PAD + _v(0.5, -0.7, 0.2), 32),
            (1.0, PAD + _v(1.2, -2.0, 0.75), PAD + _v(0.25, -0.2, 0.25), 35)],
}


def _resolve():
    """S13's camera rides beside the probe: a key every third pickup (the probe's path, from the events)."""
    tm = A.timing_map()
    shot = {s["id"]: s for s in tm["shots"]}
    a, b = shot["S13"]["cut"], shot["S14"]["cut"]
    pick = pickup_events()
    keys = []
    for k in list(range(0, N_KEYS, 3)) + [N_KEYS - 1]:
        u = min(1.0, max(0.0, (pick[k]["t"] - a) / (b - a)))
        x = 0.22 * math.sin(k * 2.1)
        y = 0.4 + k * 0.28
        keys.append((u, _v(x + 0.55, y - 0.75, 0.38), _v(x, y + 0.15, 0.08), 38))
    keys[0] = (0.0,) + keys[0][1:]
    keys[-1] = (1.0,) + keys[-1][1:]
    CAMERAS["S13"] = keys


_resolve()
