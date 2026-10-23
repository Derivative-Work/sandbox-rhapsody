"""Small modelling helpers for sets H and I's props (C5 placeholder pass): bevelled blocks sized in the mesh rather
than the object's scale (so bevels stay round and an object can be popped by scale), lathe-turned parts, extruded
outlines, and copies that share mesh data."""
import math

import bmesh
import bpy
from mathutils import Matrix

import sr_kit as K


def _finish(o, bev, segs):
    if bev:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width, md.segments, md.limit_method, md.harden_normals = bev, segs, "ANGLE", True
    K.smooth(o)
    return o


def blk(name, mat, parent, loc, dims, bev=0.0, segs=3, rot=(0, 0, 0)):
    """A box `dims` (x, y, z metres) centred at `loc`, its size in the mesh (object scale 1), edges bevelled by `bev`."""
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc, rotation=rot)
    o.data.transform(Matrix.Diagonal((*dims, 1.0)))
    return _finish(o, bev, segs)


def cyl(name, mat, parent, loc, r, depth, rot=(0, 0, 0), verts=48, bev=0.0, segs=2):
    """A cylinder along its local Z (rotate it with `rot`), smooth-shaded, its rims bevelled by `bev`."""
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cylinder_add, mat, parent, radius=r, depth=depth, vertices=verts,
                   location=loc, rotation=rot)
    return _finish(o, bev, segs)


def lathe(name, mat, parent, loc, profile, segs=64, rot=(0, 0, 0)):
    """A surface of revolution about local Z through `profile` [(radius, z), ...], top to bottom or bottom to top;
    a radius of 0 closes the end to a point."""
    verts, faces = [], []
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            ring = []
            for k in range(segs):
                a = math.tau * k / segs
                ring.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), z))
            rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1 and len(rb) == 1:
            continue
        for k in range(segs):
            k1 = (k + 1) % segs
            if len(ra) == 1:
                faces.append((ra[0], rb[k], rb[k1]))
            elif len(rb) == 1:
                faces.append((ra[k], rb[0], ra[k1]))
            else:
                faces.append((ra[k], rb[k], rb[k1], ra[k1]))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    o = K.link(bpy.data.objects.new(name, me))
    o.location, o.rotation_euler = loc, rot
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return K.smooth(o)


def prism(name, mat, parent, loc, outline, depth, rot=(0, 0, 0), bev=0.0, segs=2):
    """A flat outline [(x, z), ...] (counter-clockwise, in the local XZ plane) extruded `depth` along local Y."""
    n = len(outline)
    verts = [(x, -depth / 2, z) for x, z in outline] + [(x, depth / 2, z) for x, z in outline]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = K.link(bpy.data.objects.new(name, me))
    o.location, o.rotation_euler = loc, rot
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return _finish(o, bev, segs)


def share(src, name, parent, loc=None, rot=None):
    """A copy of `src` that shares its mesh data (and keeps its modifiers), under `parent`."""
    o = src.copy()
    o.name = name
    K.link(o)
    o.parent = parent
    if loc is not None:
        o.location = loc
    if rot is not None:
        o.rotation_euler = rot
    return o


def share_tree(src_root, name, parent=None, loc=None, rot=None):
    """Copy an empty and every mesh under it (sharing their data) as `name`; children keep their local transforms.
    Children's names are re-prefixed from src_root.name to `name`."""
    root = src_root.copy()
    root.name = name
    K.link(root)
    root.parent = parent
    if loc is not None:
        root.location = loc
    if rot is not None:
        root.rotation_euler = rot

    def walk(s, d):
        for c in s.children:
            cc = c.copy()
            cc.name = c.name.replace(src_root.name, name, 1)
            K.link(cc)
            cc.parent = d
            cc.matrix_parent_inverse = c.matrix_parent_inverse.copy()
            walk(c, cc)
    walk(src_root, root)
    return root
