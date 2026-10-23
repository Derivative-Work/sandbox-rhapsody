"""Prop geometry for sets F and G (C5 placeholder pass: the human found props still built as one or two primitives).

Each prop is one mesh assembled in bmesh from bevelled boxes, cylinders and frames, with a material slot per part,
shaded smooth with sharp edges by angle, so a bevel catches light like a moulded or machined edge. Repeated copies
(crates, legs, pilasters) share one mesh.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import sr_kit as K


class Builder:
    """Parts added to one bmesh; `mats` are the material slots, a part's `m` is its slot index."""

    def __init__(self, mats):
        self.bm = bmesh.new()
        self.mats = mats

    def _tag(self, faces, m):
        for f in faces:
            f.material_index = m

    def box(self, c, size, bev=0.0, m=0, seg=2, rot=None):
        """A box centred at `c`, `size` full extents, edges bevelled by `bev`; `rot` a Matrix (3x3) about its centre."""
        bm = self.bm
        mat = Matrix.Translation(Vector(c)) @ (rot.to_4x4() if rot else Matrix()) @ Matrix.Diagonal((*size, 1.0))
        res = bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
        verts = res["verts"]
        self._tag({f for v in verts for f in v.link_faces}, m)
        if bev > 0:
            edges = list({e for v in verts for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=min(bev, min(size) * 0.45), segments=seg, profile=0.5,
                            affect="EDGES", clamp_overlap=True, material=m)

    def cyl(self, c, r, depth, axis="Z", segs=32, m=0, r2=None):
        """A capped cylinder (a cone if `r2`) centred at `c` along `axis`."""
        rot = {"Z": Matrix(), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                                    radius2=r if r2 is None else r2, depth=depth,
                                    matrix=Matrix.Translation(Vector(c)) @ rot)
        self._tag({f for v in res["verts"] for f in v.link_faces}, m)

    def prism(self, pts, z0, z1, m=0, at=(0, 0, 0)):
        """A flat outline (2D points, counter-clockwise in XY) extruded from z0 to z1, offset by `at`."""
        bm, (ax, ay, az) = self.bm, at
        bot = [bm.verts.new((x + ax, y + ay, z0 + az)) for x, y in pts]
        top = [bm.verts.new((x + ax, y + ay, z1 + az)) for x, y in pts]
        n = len(pts)
        faces = [bm.faces.new(bot[::-1]), bm.faces.new(top)]
        faces += [bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i])) for i in range(n)]
        self._tag(faces, m)

    def frame(self, c, outer, inner, height, m=0, bev=0.0):
        """A rectangular ring (a band round a box, a lip): outer and inner (w, d) at height `height`."""
        (ow, od), (iw, idp) = outer, inner
        t_x, t_y = (ow - iw) / 2, (od - idp) / 2
        cx, cy, cz = c
        self.box((cx, cy - od / 2 + t_y / 2, cz), (ow, t_y, height), bev, m)
        self.box((cx, cy + od / 2 - t_y / 2, cz), (ow, t_y, height), bev, m)
        self.box((cx - ow / 2 + t_x / 2, cy, cz), (t_x, idp, height), bev, m)
        self.box((cx + ow / 2 - t_x / 2, cy, cz), (t_x, idp, height), bev, m)

    def mesh(self, name, sharp=0.6):
        me = bpy.data.meshes.new(name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        self.bm.to_mesh(me)
        self.bm.free()
        for mt in self.mats:
            me.materials.append(mt)
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=sharp)
        return me


def place(name, me, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    """An object using mesh `me` (shared), at `loc` under `parent`."""
    o = K.link(bpy.data.objects.new(name, me))
    o.location, o.rotation_euler = loc, rot
    if parent:
        o.parent = parent
    return o
