"""Set B's rotary phone from a third-party model (human, C4 v4: "see if you can find a CC asset to replace it").

Source: "Rotary Phone" by lobstor (https://sketchfab.com/patrickcauty), CC BY 4.0,
https://sketchfab.com/3d-models/rotary-phone-09f3f6bd3c914283924caf0754e0d00a, downloaded by the human (R4) to
assets/models/rotary_phone_src/ (license.txt there). Credit it in the end card.

The model is one mesh of 122 loose parts in centimetres. This splits it by where each part sits:
- the cord (every coil, out past the body's sides) is dropped: set B models its own, which can stretch and swing;
- the handset: the long grip and the two end cups (parts above the cradle, behind the dial), with the cord's sleeve;
- the finger wheel (the largest part, the dial's holed disc), so set B can turn it to dial;
- the body: everything else, including the cradle posts and the cord's grommet on the side of the base.
It is mirrored in X, so the cord leaves the base on the right (the open side at the end of the shelf), scaled to
WIDTH across, and stood with the base's footprint centred on the origin. Set B's "alarm" red replaces the baked
texture. The wheel's origin is its centre with local Z along its axis. Cord anchors (body: the grommet; handset: the
sleeve) are stored as custom properties in each object's local coordinates.

Usage: blender -b --factory-startup --python scripts/phone_prep.py  ->  assets/models/rotary_phone.blend
"""
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

SRC = "assets/models/rotary_phone_src/scene.gltf"
OUT = "assets/models/rotary_phone.blend"
WIDTH = 0.24  # metres across the base (the grey-box phone's width)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = src
src.select_set(True)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o.type == "EMPTY"]:
    bpy.data.objects.remove(o)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.separate(type="LOOSE")
bpy.ops.object.mode_set(mode="OBJECT")


def bounds(o):
    co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    return Vector(co.min(0)), Vector(co.max(0))


groups = {"cord": [], "handset": [], "wheel": [], "body": []}
anchors = {}
parts = [o for o in bpy.data.objects if o.type == "MESH"]
largest = max(parts, key=lambda o: len(o.data.vertices))
for o in parts:
    lo, hi = bounds(o)
    c = (lo + hi) / 2
    if lo.x < -81 or hi.x > 79 or (hi.x < -54 and hi.z < 20):  # coils; the cord's run outside the base (x -52.7)
        k = "cord"
    elif o is largest:
        k = "wheel"
    elif lo.y >= 23.5 and lo.z >= 28.0 and (hi.x - lo.x > 60 or abs(c.x) > 30):
        k = "handset"
    else:
        k = "body"
    groups[k].append(o)
    if k == "handset" and lo.x < -79:  # the cord's sleeve on the handset's end
        anchors["handset"] = Vector((lo.x, c.y, c.z))
    if k == "body" and hi.x < -45 and lo.x > -54 and c.z < 12:  # the grommet in the base's side
        anchors["body"] = Vector((lo.x, c.y, c.z))
assert set(anchors) == {"body", "handset"}, anchors
for o in groups["cord"]:
    bpy.data.objects.remove(o)

# Footprint, scale and mirror, from the body's bounds.
body_lo = Vector(np.min([bounds(o)[0] for o in groups["body"]], axis=0))
body_hi = Vector(np.max([bounds(o)[1] for o in groups["body"]], axis=0))
s = WIDTH / (body_hi.x - body_lo.x)
centre = Vector(((body_lo.x + body_hi.x) / 2, (body_lo.y + body_hi.y) / 2, body_lo.z))
to_set = Matrix.Diagonal((-s, s, s, 1.0)) @ Matrix.Translation(-centre)  # mirrored in X
for k in anchors:
    anchors[k] = to_set @ anchors[k]

mat = bpy.data.materials.new("phone_red")  # replaced by set B's own material on load
out = {}
for k in ("body", "handset", "wheel"):
    objs = groups[k]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = f"phone_{k}"
    o.data.transform(to_set)
    o.data.flip_normals()  # the mirror turned every face inside out
    o.data.materials.clear()
    o.data.materials.append(mat)
    out[k] = o

# Origins: body at its footprint centre (already); handset at its centre; wheel at its centre, local Z on its axis.
hs = out["handset"]
lo, hi = bounds(hs)
c = (lo + hi) / 2
hs.data.transform(Matrix.Translation(-c))
hs.location = c
wh = out["wheel"]
co = np.array([v.co for v in wh.data.vertices])
mid = co.mean(0)
_, _, vt = np.linalg.svd(co - mid)
n = Vector(vt[2])
if n.z < 0:
    n = -n
rot = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
wh.data.transform(rot.inverted() @ Matrix.Translation(-Vector(mid)))
wh.matrix_world = Matrix.Translation(Vector(mid)) @ rot
wh.parent = out["body"]
hs["cord_anchor"] = list(anchors["handset"] - hs.location)
out["body"]["cord_anchor"] = list(anchors["body"])
for o in out.values():
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    for p in o.data.polygons:
        p.use_smooth = True
print("PHONE", {k: len(v.data.vertices) for k, v in out.items()}, "scale", round(s, 6),
      "anchors", {k: [round(x, 4) for x in v] for k, v in anchors.items()},
      "handset at", [round(x, 4) for x in hs.location], "wheel axis", [round(x, 3) for x in n])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
