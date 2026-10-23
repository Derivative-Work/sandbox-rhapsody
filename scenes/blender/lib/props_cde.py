"""Modelling helpers for sets C, D and E's props (C5 placeholder pass; human, set D: the pager "looks very boxy").

- box(): a bevelled block whose size is baked into the mesh before the bevel, so every edge gets the same round
  (a bevel on a scaled cube is squashed by the scale: the old pager's 8 mm bevel came out under 1 mm deep);
- lathe(): a turned part (bell, beacon dome, horn, lamp shade) spun from a (radius, z) profile;
- floor_with_hole(): the set's mirror floor with a round hole cut in it (set E's portal).
Shared mesh data: pass `share` to reuse one mesh across repeated copies.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import sr_kit as K

_MESHES = {}


def _obj(name, mesh, mat, parent, loc, rot):
    o = bpy.data.objects.new(name, mesh)
    K.link(o)
    if mat is not None and not mesh.materials:
        mesh.materials.append(mat)
    o.location, o.rotation_euler = loc, rot
    if parent:
        o.parent = parent
    return o


def _finish(o, bev, segments):
    if bev:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width, md.segments, md.limit_method = bev, segments, "ANGLE"
        md.harden_normals = True
        K.smooth(o)
    return o


def box(name, mat, parent, loc, dims, bev=0.0, rot=(0, 0, 0), segments=3, share=None):
    """A block `dims` (x, y, z) metres centred at `loc`, edges rounded by `bev` metres."""
    key = share and ("box", share)
    mesh = _MESHES.get(key) if key else None
    if mesh is None:
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector(dims), verts=bm.verts)
        bm.to_mesh(mesh)
        bm.free()
        if key:
            _MESHES[key] = mesh
    return _finish(_obj(name, mesh, mat, parent, loc, rot), bev, segments)


def lathe(name, mat, parent, loc, profile, rot=(0, 0, 0), steps=48, smooth=True, share=None):
    """A solid of revolution about local Z: `profile` is [(radius, z), ...] from one end to the other."""
    key = share and ("lathe", share)
    mesh = _MESHES.get(key) if key else None
    if mesh is None:
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        vs = [bm.verts.new((r, 0.0, z)) for r, z in profile]
        es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
        bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), dvec=(0, 0, 0), angle=math.tau,
                       steps=steps, use_merge=True)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        if key:
            _MESHES[key] = mesh
    o = _obj(name, mesh, mat, parent, loc, rot)
    if smooth:
        K.smooth(o)
    return o


def cyl(name, mat, parent, loc, r, depth, rot=(0, 0, 0), verts=32, bev=0.0, share=None):
    """A cylinder along local Z, optionally with rounded rims."""
    key = share and ("cyl", share)
    mesh = _MESHES.get(key) if key else None
    if mesh is None:
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
        bm.to_mesh(mesh)
        bm.free()
        if key:
            _MESHES[key] = mesh
    o = _obj(name, mesh, mat, parent, loc, rot)
    if bev:
        return _finish(o, bev, 3)
    K.smooth(o)
    o.data.polygons.foreach_set("use_smooth", [len(p.vertices) == 4 for p in o.data.polygons])
    return o


def floor_with_hole(floor, center, radius, segments=96):
    """Replace the floor plane's mesh by the same square with a round hole at `center` (a quad ring from the hole's
    edge out to the square's border, so the mirror floor is unchanged everywhere else)."""
    half = max(floor.dimensions.x, floor.dimensions.y) / 2
    bm = bmesh.new()
    inner, outer = [], []
    for k in range(segments):
        a = math.tau * k / segments
        d = Vector((math.cos(a), math.sin(a), 0.0))
        inner.append(bm.verts.new(Vector(center) + d * radius))
        s = half / max(abs(d.x), abs(d.y))  # out along the same angle to the square's edge
        p = d * s
        outer.append(bm.verts.new((max(-half, min(half, p.x)), max(-half, min(half, p.y)), 0.0)))
    for k in range(segments):
        j = (k + 1) % segments
        bm.faces.new((inner[k], inner[j], outer[j], outer[k]))
    # segments is a multiple of 8, so the 45-degree rays land on the square's corners: the outline stays square.
    assert segments % 8 == 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    mats = list(floor.data.materials)
    mesh = bpy.data.meshes.new("floor_holed")
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    floor.data = mesh
    floor.location = (0, 0, 0)
    floor.scale = (1, 1, 1)
    return floor


def shift_mesh(o, offset):
    """Move an object's mesh within its own frame (keeps the object's origin, so rigs are untouched)."""
    o.data.transform(Matrix.Translation(Vector(offset)))


def rod(name, mat, parent, p0, p1, r, verts=12, share=None):
    """A round bar from p0 to p1 (parent space)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = cyl(name, mat, parent, (p0 + p1) / 2, r, d.length, verts=verts, share=share)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o
