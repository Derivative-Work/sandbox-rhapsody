"""Prop meshes for sets A and B (C5 placeholder pass: the human, set D, "are you sure you went through all of the
assets for placeholders"; scenes/blender/prop_audit.py found these props still one or two primitives).

Each builder returns a mesh at real size (no object scaling, so bevels stay round), with its bevels applied in the
mesh rather than as modifiers: hundreds of objects share one mesh (`inst`), as the B warehouse's ~1,300 crates do.
Parts are bevelled boxes, cylinders and tori merged into one bmesh, each with a material slot index.
"""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import sr_kit as K


# ---------------------------------------------------------------- mesh parts

def _merge(dst, src, mat):
    vmap = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        nf = dst.faces.new([vmap[v] for v in f.verts])
        nf.material_index = mat
        nf.smooth = f.smooth


def _place(t, center, rot):
    if rot:
        bmesh.ops.rotate(t, verts=t.verts, cent=Vector((0, 0, 0)), matrix=Euler(rot).to_matrix())
    bmesh.ops.translate(t, vec=Vector(center), verts=t.verts)


def box(bm, center, size, bevel=0.0, segs=2, mat=0, rot=None, top=(1.0, 1.0), bottom=(1.0, 1.0)):
    """A box `size` (x, y, z) at `center`, its edges bevelled by `bevel` (rounded faces smooth, flat faces flat);
    `top`/`bottom` scale the top or bottom face (a taper)."""
    t = bmesh.new()
    bmesh.ops.create_cube(t, size=1.0)
    for v in t.verts:
        sx, sy = top if v.co.z > 0 else bottom
        v.co = Vector((v.co.x * size[0] * sx, v.co.y * size[1] * sy, v.co.z * size[2]))
    if bevel > 0:
        r = bmesh.ops.bevel(t, geom=list(t.edges), offset=bevel, offset_type="OFFSET", segments=segs, profile=0.5,
                            affect="EDGES", clamp_overlap=True)
        for f in r["faces"]:
            f.smooth = True
    _place(t, center, rot)
    _merge(bm, t, mat)
    t.free()


def cyl(bm, center, r, depth, segs=24, mat=0, rot=None, r2=None, smooth=True, bevel=0.0):
    """A cylinder (or a cone, with `r2`) along Z, then rotated by `rot`."""
    t = bmesh.new()
    bmesh.ops.create_cone(t, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    if bevel > 0:
        rims = [e for e in t.edges if any(len(f.verts) > 4 for f in e.link_faces)]
        res = bmesh.ops.bevel(t, geom=rims, offset=bevel, offset_type="OFFSET", segments=2, profile=0.5,
                              affect="EDGES", clamp_overlap=True)
        for f in res["faces"]:
            f.smooth = True
    for f in t.faces:
        if len(f.verts) == 4 and smooth:
            f.smooth = True
    _place(t, center, rot)
    _merge(bm, t, mat)
    t.free()


def torus(bm, center, R, r, mat=0, rot=None, segs=(48, 12), keep=None, scale=(1, 1, 1)):
    """A torus in the XY plane (then `scale`, `rot`); `keep(angle)` drops the part of the ring it rejects (a C)."""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=segs[0], minor_segments=segs[1])
    o = bpy.context.active_object
    t = bmesh.new()
    t.from_mesh(o.data)
    me = o.data
    bpy.data.objects.remove(o)
    bpy.data.meshes.remove(me)
    if keep is not None:
        bmesh.ops.delete(t, geom=[v for v in t.verts if not keep(math.atan2(v.co.y, v.co.x))], context="VERTS")
    for v in t.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    for f in t.faces:
        f.smooth = True
    _place(t, center, rot)
    _merge(bm, t, mat)
    t.free()


def mesh(name, mats, *parts):
    """One mesh from parts: callables taking the bmesh (box/cyl/torus via lambda)."""
    bm = bmesh.new()
    for p in parts:
        p(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


def inst(name, me, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, mat=None, scale=(1, 1, 1)):
    """An object sharing mesh `me`; `mat` overrides its first slot for this object only."""
    o = K.link(bpy.data.objects.new(name, me))
    o.location, o.rotation_euler, o.scale = loc, rot, scale
    if mat is not None:
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = mat
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- set B: warehouse

def crate_mesh(name, w, d, h, body, dark, paper):
    """A stacking tote, front -Y, centred on the origin, w x d x h: rounded body, a lip round the top, side ribs, a
    dark hand-hole and a label holder with its card on the front, a dark foot."""
    fy = -d / 2
    return mesh(name, [body, dark, paper],
                lambda bm: box(bm, (0, 0, -0.004), (w - 0.016, d - 0.008, h - 0.03), 0.012, 3),
                lambda bm: box(bm, (0, 0, h / 2 - 0.016), (w, d, 0.028), 0.007, 2),
                lambda bm: box(bm, (0, 0, -h / 2 + 0.006), (w - 0.04, d - 0.04, 0.012), 0.004, 2, mat=1),
                *[(lambda sx, y: lambda bm: box(bm, (sx * (w / 2 - 0.006), y, -0.006), (0.008, 0.022, h - 0.05),
                                                  0.003, 2))(sx, y) for sx in (-1, 1) for y in (-d / 4, d / 4)],
                lambda bm: box(bm, (0, fy + 0.002, h / 2 - 0.052), (w * 0.3, 0.008, 0.022), 0.0095, 3, mat=1),
                lambda bm: box(bm, (0, fy + 0.001, -0.02), (w * 0.42, 0.008, 0.07), 0.004, 2, mat=1),
                lambda bm: box(bm, (0, fy - 0.003, -0.02), (w * 0.36, 0.002, 0.052), mat=2))


def drawer_mesh(name, w, d, h, body, dark):
    """A piano drawer, front -Y, bottom on the origin (it slides): the tote without its own label (the drawer's
    label is separate) and with its hand-hole low, flush enough that a pinned note lies over it."""
    fy = -d / 2
    return mesh(name, [body, dark],
                lambda bm: box(bm, (0, 0, h / 2 - 0.004), (w - 0.016, d - 0.004, h - 0.03), 0.012, 3),
                lambda bm: box(bm, (0, 0, h - 0.016), (w, d, 0.028), 0.007, 2),
                lambda bm: box(bm, (0, 0, 0.006), (w - 0.04, d - 0.04, 0.012), 0.004, 2, mat=1),
                *[(lambda sx, y: lambda bm: box(bm, (sx * (w / 2 - 0.006), y, h / 2 - 0.006),
                                                  (0.008, 0.022, h - 0.05), 0.003, 2))(sx, y)
                  for sx in (-1, 1) for y in (-d / 4, d / 4)],
                lambda bm: box(bm, (0, fy + 0.001, 0.06), (w * 0.34, 0.006, 0.022), 0.0095, 3, mat=1))


def label_mesh(name, dark, paper):
    """A drawer's label holder (a dark frame reaching back to the drawer face) with its white card."""
    return mesh(name, [dark, paper],
                lambda bm: box(bm, (0, 0.003, 0), (0.17, 0.01, 0.042), 0.002, 2),
                lambda bm: box(bm, (0, -0.0025, 0), (0.15, 0.002, 0.03), mat=1))


def upright_mesh(name, height, depth, steel, dark):
    """A shelving end frame, centred on the origin: two slotted posts (front and back), horizontal and diagonal
    braces between them, base plates."""
    py = depth / 2 - 0.015
    parts = []
    for y in (-py, py):
        parts.append(lambda bm, y=y: box(bm, (0, y, 0), (0.03, 0.03, height), 0.003, 2))
        parts.append(lambda bm, y=y: box(bm, (0, y, -height / 2 + 0.003), (0.06, 0.06, 0.006), 0.002, 2))
    n = int(height / 0.05)
    for k in range(1, n):  # the slots, on both posts' faces toward the aisle
        z = -height / 2 + k * 0.05
        for y in (-py, py):
            for s in (-1, 1):
                parts.append(lambda bm, z=z, y=y, s=s: box(bm, (0, y + s * 0.0155, z), (0.008, 0.001, 0.022), mat=1))
    step = 0.45
    k = 0
    z = -height / 2 + 0.15
    span = 2 * py
    diag = math.hypot(span, step)
    ang = math.atan2(step, span)
    while z + step < height / 2 - 0.1:
        parts.append(lambda bm, z=z: box(bm, (0, 0, z), (0.012, span, 0.014), 0.003, 2))
        s = 1 if k % 2 == 0 else -1
        parts.append(lambda bm, z=z, s=s: box(bm, (0, 0, z + step / 2), (0.01, diag, 0.012), 0.003, 2,
                                               rot=(s * ang, 0, 0)))
        z += step
        k += 1
    parts.append(lambda bm, z=z: box(bm, (0, 0, z), (0.012, span, 0.014), 0.003, 2))
    return mesh(name, [steel, dark], *parts)


def board_mesh(name, length, depth, steel, deck):
    """A shelf level, centred on the origin: a deck panel between front and back step beams."""
    py = depth / 2 - 0.015
    return mesh(name, [steel, deck],
                lambda bm: box(bm, (0, 0, 0.004), (length - 0.01, depth - 0.05, 0.012), 0.002, 1, mat=1),
                *[(lambda y: lambda bm: box(bm, (0, y, -0.012), (length, 0.03, 0.045), 0.004, 2))(y)
                  for y in (-py, py)])


def work_lens_mesh(name, lamp):
    """A work light's diffuser (2.2 m), rounded."""
    return mesh(name, [lamp], lambda bm: box(bm, (0, 0, 0), (2.2, 0.08, 0.03), 0.012, 3))


def work_hood_mesh(name, steel, body):
    """A work light's housing, centred on its old slab: a tapered reflector body, end caps, hanger tabs."""
    return mesh(name, [body, steel],
                lambda bm: box(bm, (0, 0, 0), (2.3, 0.18, 0.06), 0.008, 2, top=(1.0, 0.55)),
                *[(lambda sx: lambda bm: box(bm, (sx * 1.152, 0, 0.002), (0.016, 0.186, 0.066), 0.004, 2,
                                             mat=1))(sx) for sx in (-1, 1)],
                *[(lambda sx: lambda bm: box(bm, (sx * 0.95, 0, 0.04), (0.03, 0.012, 0.024), 0.003, 2,
                                             mat=1))(sx) for sx in (-1, 1)])


def wire_mesh(name, steel):
    """A hanging wire (2 m, centred) with a clip at its foot."""
    return mesh(name, [steel],
                lambda bm: cyl(bm, (0, 0, 0), 0.003, 2.0, 8),
                lambda bm: box(bm, (0, 0, -0.99), (0.014, 0.014, 0.022), 0.003, 2))


def phone_bracket_mesh(name, plate, steel):
    """The phone's wall bracket, centred on the old plate: the plate, a mounting plate bolted to the shelf's end
    upright, two arms and two diagonal struts under the plate's left half (the right edge, where the cord drapes and
    the handset hangs, stays clear)."""
    mx = -0.325  # the end upright's face (x 2.295), bracket-local
    a0, a1 = mx + 0.01, -0.12  # the arms, from the mounting plate to under the plate
    s0 = mx + 0.01
    strut, ang = math.hypot(-0.05 - s0, 0.155), math.atan2(0.155, -0.05 - s0)
    return mesh(name, [plate, steel],
                lambda bm: box(bm, (0, 0, 0), (0.34, 0.36, 0.03), 0.006, 3),
                lambda bm: box(bm, (mx + 0.005, -0.02, -0.08), (0.01, 0.3, 0.2), 0.003, 2),
                *[(lambda y: lambda bm: box(bm, ((a0 + a1) / 2, y, -0.03), (a1 - a0, 0.03, 0.03), 0.004, 2))(y)
                  for y in (-0.12, 0.08)],
                *[(lambda y: lambda bm: box(bm, ((s0 - 0.05) / 2, y, -0.0925), (strut, 0.024, 0.02), 0.004, 2,
                                            rot=(0, -ang, 0)))(y) for y in (-0.12, 0.08)],
                *[(lambda y, z: lambda bm: cyl(bm, (mx + 0.012, y, z), 0.008, 0.006, 16, mat=1,
                                               rot=(0, math.pi / 2, 0)))(y, z)
                  for y in (-0.13, 0.09) for z in (-0.03, -0.15)])


# ---------------------------------------------------------------- set A: sandbox and desk

def lockbox_meshes(case, brass):
    """The wall of 198's locked music box (the kit's footprint: 0.104 x 0.074, 0.075 tall, front -Y), as two shared
    meshes: the case (plinth, body, a rounded lid with a raised panel) and its brass (front band, corner guards, a
    hasp and a keyless padlock, back hinges)."""
    c = mesh("lockbox.case", [case],
             lambda bm: box(bm, (0, 0, 0.003), (0.104, 0.074, 0.006), 0.002, 2),
             lambda bm: box(bm, (0, 0, 0.033), (0.1, 0.07, 0.056), 0.003, 2),
             lambda bm: box(bm, (0, 0, 0.0675), (0.104, 0.074, 0.012), 0.004, 3),
             lambda bm: box(bm, (0, 0, 0.0745), (0.078, 0.05, 0.003), 0.0012, 2))
    b = mesh("lockbox.brass", [brass],
             lambda bm: box(bm, (0, -0.0356, 0.042), (0.102, 0.002, 0.008), 0.0006, 1),
             *[(lambda sx: lambda bm: box(bm, (sx * 0.0496, -0.0346, 0.033), (0.0035, 0.0035, 0.056), 0.0008,
                                          1))(sx) for sx in (-1, 1)],
             lambda bm: box(bm, (0, -0.0372, 0.057), (0.016, 0.0025, 0.02), 0.001, 2),
             lambda bm: box(bm, (0, -0.0405, 0.041), (0.014, 0.006, 0.012), 0.002, 2),
             lambda bm: torus(bm, (0, -0.0405, 0.047), 0.0048, 0.0011, rot=(math.pi / 2, 0, 0), segs=(24, 8),
                              keep=lambda a: a > -0.2),
             *[(lambda sx: lambda bm: cyl(bm, (sx * 0.03, 0.0365, 0.0625), 0.0025, 0.016, 12,
                                          rot=(0, math.pi / 2, 0)))(sx) for sx in (-1, 1)])
    return c, b


def locked_box(name, loc, rot_z, meshes):
    """One locked music box: a root with the shared case and brass (kit locked_box's name and placement)."""
    root = K.empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    inst(f"{name}.case", meshes[0], parent=root)
    inst(f"{name}.band", meshes[1], parent=root)
    return root


def wall_light_meshes(housing_m, lamp_proto):
    """A column light under the wall of 198: a lens (its emitter, per column) set in a dark channel with end caps."""
    lens = mesh("wall_light.lens", [lamp_proto], lambda bm: box(bm, (0, 0, 0.002), (0.108, 0.01, 0.008), 0.003, 2))
    housing = mesh("wall_light.housing", [housing_m],
                   lambda bm: box(bm, (0, 0, -0.002), (0.116, 0.018, 0.013), 0.003, 2),
                   *[(lambda sx: lambda bm: box(bm, (sx * 0.058, 0, -0.001), (0.006, 0.02, 0.016), 0.002,
                                                2))(sx) for sx in (-1, 1)])
    return lens, housing


def desk_leg_mesh(wood, metal):
    """A desk leg at the desk's scale (1.2 m square, 15.2 m), centred: tapered toward the floor, rounded edges, a
    metal glide."""
    return mesh("desk.leg", [wood, metal],
                lambda bm: box(bm, (0, 0, 0.1), (1.2, 1.2, 15.0), 0.08, 3, bottom=(0.72, 0.72)),
                lambda bm: cyl(bm, (0, 0, -7.5), 0.38, 0.2, 32, mat=1, bevel=0.04))


def pencil_meshes(yellow, brass, eraser, wood, graphite):
    """A pencil along its local Z (the old 7 m hex stick's length and radius): the painted hex body with softened
    edges, a ringed ferrule and eraser at the back; the sharpened tip (wood cone, graphite point) is its own mesh."""
    body = mesh("pencil", [yellow, brass, eraser],
                lambda bm: cyl(bm, (0, 0, 0.425), 0.16, 6.15, 6, smooth=False, bevel=0.012),
                lambda bm: cyl(bm, (0, 0, -2.9), 0.15, 0.5, 32, mat=1),
                *[(lambda z: lambda bm: torus(bm, (0, 0, z), 0.15, 0.008, mat=1, segs=(32, 8)))(z)
                  for z in (-2.75, -3.05)],
                lambda bm: cyl(bm, (0, 0, -3.33), 0.14, 0.36, 32, mat=2, bevel=0.05))
    tip = mesh("pencil.tip", [wood, graphite],
               lambda bm: cyl(bm, (0, 0, -0.075), 0.16, 0.55, 6, r2=0.046, smooth=False),
               lambda bm: cyl(bm, (0, 0, 0.275), 0.046, 0.15, 16, mat=1, r2=0.004))
    return body, tip


def wrench_mesh(steel):
    """A combination wrench lying flat (0.22 m): a ring end, a tapered shank, an open jaw."""
    return mesh("wrench", [steel],
                lambda bm: box(bm, (0, 0, 0), (0.15, 0.016, 0.007), 0.0025, 2),
                lambda bm: box(bm, (-0.068, 0, 0), (0.02, 0.022, 0.008), 0.003, 2),
                lambda bm: box(bm, (0.066, 0, 0), (0.02, 0.024, 0.008), 0.003, 2),
                lambda bm: torus(bm, (-0.09, 0, 0), 0.0155, 0.0055, scale=(1, 1, 0.75), segs=(40, 10)),
                lambda bm: torus(bm, (0.092, 0, 0), 0.0165, 0.006, scale=(1, 1, 0.75), segs=(40, 10),
                                 keep=lambda a: abs(a) > 0.75))


def guardrail_mesh(rail, dark):
    """A guardrail section lying on its side (0.9 m): two tubes, balusters between them, bolted end flanges."""
    return mesh("guardrail", [rail, dark],
                *[(lambda y: lambda bm: cyl(bm, (0, y, -0.008), 0.012, 0.88, 20, rot=(0, math.pi / 2, 0)))(y)
                  for y in (-0.032, 0.032)],
                *[(lambda x: lambda bm: cyl(bm, (x, 0, -0.008), 0.006, 0.064, 12, rot=(math.pi / 2, 0, 0)))(x)
                  for x in (-0.3, -0.1, 0.1, 0.3)],
                *[(lambda sx: lambda bm: box(bm, (sx * 0.444, 0, -0.005), (0.012, 0.09, 0.03), 0.003, 2))(sx)
                  for sx in (-1, 1)],
                *[(lambda sx, y: lambda bm: cyl(bm, (sx * 0.451, y, -0.005), 0.005, 0.004, 12, mat=1,
                                                rot=(0, math.pi / 2, 0)))(sx, y)
                  for sx in (-1, 1) for y in (-0.028, 0.028)])


def tray_mesh(body, dark, xs):
    """The flag tray (0.3 x 0.16 x 0.09): a rounded box with a dark inset top, a hole for each pole at `xs`
    (tray-local x), and feet."""
    return mesh("flag_tray", [body, dark],
                lambda bm: box(bm, (0, 0, 0.0), (0.3, 0.16, 0.084), 0.01, 3),
                lambda bm: box(bm, (0, 0, 0.0425), (0.27, 0.13, 0.004), 0.0015, 1, mat=1),
                *[(lambda x: lambda bm: cyl(bm, (x, 0, 0.045), 0.009, 0.002, 16, mat=1))(x) for x in xs],
                *[(lambda sx, sy: lambda bm: cyl(bm, (sx * 0.12, sy * 0.055, -0.044), 0.012, 0.006, 16,
                                                 mat=1))(sx, sy) for sx in (-1, 1) for sy in (-1, 1)])


def flag_pole_mesh(chrome):
    """A flag's pole (0.22 m, centred) with a ball finial."""
    return mesh("flag_pole", [chrome],
                lambda bm: cyl(bm, (0, 0, 0), 0.004, 0.22, 12),
                lambda bm: cyl(bm, (0, 0, 0.113), 0.0075, 0.008, 12, bevel=0.0035))


def flag_mesh(cloth):
    """A swallowtail pennant, 0.05 x 0.035, its hoist on the origin, in the XZ plane, rippled."""
    bm = bmesh.new()
    nx, nz = 10, 5
    grid = [[None] * (nz + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(nz + 1):
            u, w = i / nx, j / nz
            x = 0.05 * u
            if i == nx and 0 < j < nz:  # the swallowtail notch
                x -= 0.012 * (1 - abs(2 * w - 1))
            grid[i][j] = bm.verts.new((x, 0.004 * math.sin(u * math.pi * 2.2) * u, 0.035 * (w - 0.5)))
    for i in range(nx):
        for j in range(nz):
            f = bm.faces.new([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
            f.smooth = True
    me = bpy.data.meshes.new("flag")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(cloth)
    return me
