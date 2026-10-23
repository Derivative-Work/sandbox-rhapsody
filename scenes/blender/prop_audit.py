"""Placeholder audit: every prop of a set on its own, framed to fill the shot, so its modelling can be judged up close
(human, C5 set D: "the pager also looks very boxy. are you sure you went through all of the assets for
placeholders"; the earlier pass looked at whole-set stills, where small props hide).

A prop is a top-level object and everything parented under it; a top-level object spanning more than BIG metres
with children is split into its children instead. Props whose names differ only by a trailing index (drawer3,
drawer4, ...) are rendered once. Each still has its own neutral key, fill and rim, on a dark grey ground. Alongside
it, audit.tsv lists each prop's size and its bare boxes (8-vertex meshes with no bevel) and flat-shaded meshes:
the marks of placeholder geometry. Props a set keeps hidden until animated (scale 0) are listed, not rendered.

Usage: blender -b --factory-startup --python scenes/blender/prop_audit.py -- SET [--out renders/audit]
       -> <out>/set_<SET>/<prop>.png, <out>/set_<SET>/audit.tsv
"""
import importlib
import math
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scenes/blender/lib"), str(ROOT / "scenes/blender/sets")]
import sr_kit as K  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
SET = args[0].upper()
OUT = Path(args[args.index("--out") + 1] if "--out" in args else ROOT / "renders/audit") / f"set_{SET}"
OUT.mkdir(parents=True, exist_ok=True)
BIG = 6.0
RENDERABLE = {"MESH", "CURVE", "FONT", "SURFACE", "META"}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, 640, 480, 16)
importlib.import_module(f"set_{SET.lower()}").build()
K.smooth_by_angle()  # as animatic.py renders it
bpy.context.view_layer.update()
for o in bpy.data.objects:  # the set's own lights and cameras play no part
    if o.type in {"LIGHT", "CAMERA"}:
        o.hide_render = True
world = bpy.data.worlds.new("audit") if scene.world is None else scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.03, 0.03, 0.035, 1)
    bg.inputs[1].default_value = 1.0
scene.world = world


def subtree(o):
    out = [o]
    for c in o.children:
        out += subtree(c)
    return out


def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type in RENDERABLE for c in o.bound_box]
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def props():
    todo = [o for o in bpy.data.objects if o.parent is None]
    out = []
    while todo:
        o = todo.pop()
        objs = subtree(o)
        bb = bbox(objs)
        if bb is None:
            continue
        if (bb[1] - bb[0]).length > BIG and o.children and any(c.type in RENDERABLE or c.children for c in o.children):
            if o.type in RENDERABLE:
                out.append((o, [o]))
            todo += list(o.children)
            continue
        out.append((o, objs))
    return out


def stem(name):
    return re.sub(r"([._-]?\d+)+$", "", name)


seen = {}
for o, objs in sorted(props(), key=lambda p: p[0].name):
    seen.setdefault(stem(o.name), []).append((o, objs))

key = bpy.data.lights.new("audit_key", "AREA")
fill = bpy.data.lights.new("audit_fill", "AREA")
rim = bpy.data.lights.new("audit_rim", "AREA")
lights = [K.link(bpy.data.objects.new(f"audit_{n}", d)) for n, d in (("key", key), ("fill", fill), ("rim", rim))]
cd = bpy.data.cameras.new("audit_cam")
cd.lens, cd.clip_start, cd.clip_end = 50, 0.001, 1000
cam = K.link(bpy.data.objects.new("audit_cam", cd))
scene.camera = cam
everything = [o for o in bpy.data.objects if o.type in RENDERABLE]
rows = ["prop\tcount\tsize_m\tmeshes\tbare_boxes\tflat_shaded\tnote"]
for name, group in seen.items():
    o, objs = group[0]
    mine = [x for x in objs if x.type in RENDERABLE]
    bb = bbox(objs)
    size = bb[1] - bb[0]
    meshes = [x for x in mine if x.type == "MESH"]
    bare = [x.name for x in meshes if len(x.data.vertices) == 8 and not any(m.type == "BEVEL" for m in x.modifiers)]
    flat = [x.name for x in meshes if x.data.polygons and not any(p.use_smooth for p in x.data.polygons)
            and len(x.data.vertices) > 8]
    note = ""
    if max(size) < 1e-4 or all(max(x.matrix_world.to_scale()) < 1e-6 for x in mine):
        note = "hidden until animated"
    rows.append(f"{name}\t{len(group)}\t{size.x:.3f}x{size.y:.3f}x{size.z:.3f}\t{len(meshes)}\t{len(bare)}\t{len(flat)}\t"
                f"{note}")
    if note:
        continue
    for x in everything:
        x.hide_render = x not in mine
    c = (bb[0] + bb[1]) / 2
    r = max(size.length / 2, 0.01)
    d = r / math.tan(math.atan(18 / cd.lens) * 0.75) * 1.05
    view = Vector((-0.55, -1.0, 0.6)).normalized()
    cam.location = c + view * d
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    for lo, (v, power, size_k) in zip(lights, (((-1.0, -0.8, 1.0), 900, 1.2), ((1.0, -0.6, 0.3), 300, 1.5),
                                                ((0.4, 1.0, 0.8), 700, 0.6))):
        lo.location = c + Vector(v).normalized() * d
        lo.rotation_euler = (c - lo.location).to_track_quat("-Z", "Y").to_euler()
        lo.data.energy = power * (d / 3.0) ** 2
        lo.data.size = r * size_k * 2
    scene.render.filepath = str(OUT / f"{name}.png")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
(OUT / "audit.tsv").write_text("\n".join(rows) + "\n")
print("AUDIT", SET, len(seen), "props")
