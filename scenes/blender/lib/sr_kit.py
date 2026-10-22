"""Shared kit (brief, "Sets → Shared kit"): Python-built assets reused in every set.

Everything here is procedural and deterministic: no random calls, so a rebuild gives the same geometry. Colors come
from config/look.json (written from style/style_spec.md), never hard-coded in a set.

Units are metres. Rigs expose a few named custom properties that the note-driven animation library (step 7) keys:
  probe:  "led" (0–1 LED intensity), "arm_l" / "arm_r" (0–1 reach)
  blade:  "vent" (0 = louvres closed, 1 = open)
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
LOOK = json.loads((ROOT / "config" / "look.json").read_text())


# ---------------------------------------------------------------- colour and materials

def lin(hexstr, a=1.0):
    """sRGB hex -> linear RGBA, as Blender's colour sockets expect."""
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    h = hexstr.lstrip("#")
    return (ch(int(h[0:2], 16)), ch(int(h[2:4], 16)), ch(int(h[4:6], 16)), a)


def col(role):
    return lin(LOOK["palette"][role])


def _principled(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"]


def mat_plastic(name, role, rough=None):
    """Glossy plastic: the Animusic default surface (spec, 'Materials')."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Roughness"].default_value = LOOK["materials"]["plastic_roughness"] if rough is None else rough
    b.inputs["Coat Weight"].default_value = LOOK["materials"]["plastic_coat"]
    b.inputs["Coat Roughness"].default_value = 0.03
    return m


def mat_chrome(name, role="chrome"):
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = LOOK["materials"]["chrome_roughness"]
    return m


def mat_metal(name, role, rough):
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    return m


def mat_glass(name, role="glass", rough=0.0, tint=0.94, reflect=0.7):
    """Thin clear glass: a Fresnel mix of a tinted transparent and a sharp glossy reflection, blended.

    Tried and rejected (log, step 3): raytraced refraction (Eevee refracts one layer only; the cube's panes stack, so
    it breaks), and dithered transparency (grain, darkens and smears what's behind). Blended panes reflect the sphere
    probe, so the probe resolution is raised in setup_render."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    c = col(role)
    tr.inputs["Color"].default_value = (c[0] * tint, c[1] * tint, c[2] * tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = rough
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = reflect
    mix = nt.nodes.new("ShaderNodeMixShader")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(fr.outputs[0], k.inputs[0])
    nt.links.new(k.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs[0])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


def mat_acrylic(name, role, alpha=0.35, emit=0.0):
    """Translucent tinted acrylic, optionally glowing from inside (LED housings, pellets)."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Emission Color"].default_value = col(role)
    b.inputs["Emission Strength"].default_value = emit
    m.surface_render_method = "BLENDED"
    return m


def mat_emission(name, role, strength, prop_owner=None, prop=None):
    """Emitter whose strength can be driven by a custom property on `prop_owner` (0–1 scales `strength`)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = col(role)
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    if prop_owner is not None:
        fc = e.inputs["Strength"].driver_add("default_value")
        d = fc.driver
        d.type = "SCRIPTED"
        v = d.variables.new()
        v.name = "x"
        v.targets[0].id_type = "OBJECT"
        v.targets[0].id = prop_owner
        v.targets[0].data_path = f'["{prop}"]'
        d.expression = f"{strength} * (0.04 + 0.96 * x)"
    return m


def mat_mirror_floor(name="floor"):
    """Black mirror floor (spec, 'Background'): near-black, low roughness, reflections fade with distance."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col("floor")
    b.inputs["Roughness"].default_value = LOOK["materials"]["floor_roughness"]
    b.inputs["Specular IOR Level"].default_value = 0.5
    return m


# ---------------------------------------------------------------- helpers

def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_obj(name, mesh_op, mat=None, parent=None, **kw):
    mesh_op(**kw)
    o = bpy.context.active_object
    o.name = name
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def bevel(o, width, segments=3):
    md = o.modifiers.new("bevel", "BEVEL")
    md.width = width
    md.segments = segments
    md.limit_method = "ANGLE"
    return o


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    link(e)
    if parent:
        e.parent = parent
    return e


def prop(o, key, value, lo=0.0, hi=1.0):
    o[key] = value
    o.id_properties_ui(key).update(min=lo, max=hi)


def drive(target, path, index, owner, key, expr):
    """target.path[index] = expr(x), x = owner[key]."""
    fc = target.driver_add(path, index) if index is not None else target.driver_add(path)
    d = fc.driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "x"
    v.targets[0].id_type = "OBJECT"
    v.targets[0].id = owner
    v.targets[0].data_path = f'["{key}"]'
    d.expression = expr


# ---------------------------------------------------------------- render setup

def setup_render(scene, width, height, samples):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.fps = LOOK["fps"]
    ee = scene.eevee
    ee.taa_render_samples = samples
    ee.use_raytracing = True
    ee.ray_tracing_options.resolution_scale = "1"
    ee.ray_tracing_options.screen_trace_quality = 1.0
    ee.use_shadows = True
    ee.fast_gi_method = "GLOBAL_ILLUMINATION"
    ee.gi_cubemap_resolution = "2048"  # sharp reflections in blended glass (see mat_glass)
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = LOOK["agx_look"]
    scene.view_settings.exposure = LOOK["exposure"]
    scene.world = void_world()
    return scene


def void_world():
    """The surround (spec, 'Background'): not black. A vertical gradient from the floor-level horizon glow up to a
    deep violet-black zenith, with a sparse, faint starfield. Seen mostly in reflections and behind machines."""
    world = bpy.data.worlds.new("void")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = col("horizon")
    ramp.color_ramp.elements[1].position = 0.35
    ramp.color_ramp.elements[1].color = col("void")
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    # Stars: thresholded fine Voronoi distance, only above the horizon. Deterministic (procedural, no seed).
    vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
    vor2.inputs["Scale"].default_value = 220.0
    nt.links.new(tc.outputs["Generated"], vor2.inputs["Vector"])
    star = nt.nodes.new("ShaderNodeMath")
    star.operation = "LESS_THAN"
    star.inputs[1].default_value = 0.06
    nt.links.new(vor2.outputs["Distance"], star.inputs[0])
    above = nt.nodes.new("ShaderNodeMath")
    above.operation = "GREATER_THAN"
    above.inputs[1].default_value = 0.08
    nt.links.new(sep.outputs["Z"], above.inputs[0])
    # Only ~12% of cells get a star, at a random brightness, so the field doesn't read as a grid.
    sepc = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vor2.outputs["Color"], sepc.inputs[0])
    keep = nt.nodes.new("ShaderNodeMath")
    keep.operation = "GREATER_THAN"
    keep.inputs[1].default_value = 0.88
    nt.links.new(sepc.outputs["Red"], keep.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    nt.links.new(star.outputs[0], m1.inputs[0])
    nt.links.new(keep.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    nt.links.new(m1.outputs[0], m2.inputs[0])
    nt.links.new(sepc.outputs["Green"], m2.inputs[1])
    mask = nt.nodes.new("ShaderNodeMath")
    mask.operation = "MULTIPLY"
    nt.links.new(m2.outputs[0], mask.inputs[0])
    nt.links.new(above.outputs[0], mask.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = LOOK["stars"]
    nt.links.new(mask.outputs[0], gain.inputs[0])
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs["Factor"].default_value = 1.0
    nt.links.new(ramp.outputs[0], add.inputs["A"])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        nt.links.new(gain.outputs[0], comb.inputs[k])
    nt.links.new(comb.outputs[0], add.inputs["B"])
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(add.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], o.inputs[0])
    return world


def reflection_cards(center=(0, 0, 0.6), radius=7.0):
    """Large soft emissive cards that the camera never sees directly (ray visibility off) but chrome, glass and the
    floor reflect: Animusic's chrome reads because it mirrors bright shapes, not the dark surround."""
    out = []
    c = Vector(center)
    for name, d, role, strength, size in (("card_warm", (-0.7, -0.6, 0.5), "key", 2.5, (6, 3)),
                                          ("card_cool", (0.8, 0.5, 0.35), "fill", 1.6, (8, 2)),
                                          ("card_top", (0.0, 0.0, 1.0), "rim", 1.2, (5, 5))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=c + Vector(d).normalized() * radius)
        o = bpy.context.active_object
        o.name = name
        o.scale = (size[0], size[1], 1)
        o.rotation_euler = (c - o.location).to_track_quat("Z", "Y").to_euler()
        o.data.materials.append(mat_emission(name, role, strength))
        o.visible_camera = False
        o.visible_shadow = False
        out.append(o)
    return out


def reflection_probe(center=(0, 0, 0.6), radius=3.0):
    """Sphere light probe: lets Eevee's chrome and glass reflect what's off screen (the cards, lights, the set)."""
    bpy.ops.object.lightprobe_add(type="SPHERE", location=center)
    o = bpy.context.active_object
    o.data.influence_distance = radius
    return o


def area_light(name, loc, target, power, size, role="key", shape="RECTANGLE", size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.shape = shape
    ld.size = size
    ld.size_y = size_y or size
    ld.color = col(role)[:3]
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def studio_lights(center=(0, 0, 0.6), radius=6.0, scale=1.0):
    """Soft key from front-left above, strong cool rim pair from behind, faint fill (spec, 'Lighting')."""
    L = LOOK["lights"]
    c = Vector(center)
    out = [
        area_light("key", c + Vector((-0.55, -0.8, 0.75)) * radius, c, L["key"] * scale, radius * 0.5, "key"),
        area_light("fill", c + Vector((0.9, -0.5, 0.2)) * radius, c, L["fill"] * scale, radius * 0.6, "fill"),
        area_light("rim_l", c + Vector((-0.8, 0.9, 0.45)) * radius, c, L["rim"] * scale, radius * 0.18, "rim",
                   size_y=radius * 0.6),
        area_light("rim_r", c + Vector((0.85, 0.85, 0.5)) * radius, c, L["rim"] * scale, radius * 0.18, "rim",
                   size_y=radius * 0.6),
    ]
    return out


def floor(size=200.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = "floor"
    o.data.materials.append(mat_mirror_floor())
    return o


def camera(name, loc, target, lens=35.0, dof_fstop=None, focus=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.01, 500
    o = link(bpy.data.objects.new(name, cd))
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if dof_fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = dof_fstop
        cd.dof.focus_distance = focus or (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = o
    return o


# ---------------------------------------------------------------- probe rig

PROBE_R = 0.034  # tennis-ball size (brief, "The agents")


def probe(name="probe", loc=(0, 0, 0), led_role="amber", led=1.0, scale=1.0):
    """Polished sphere, one lens, one status LED, two thin manipulator arms. Faces -Y (lens forward)."""
    r = PROBE_R
    root = empty(name, loc)
    root.scale = (scale,) * 3
    prop(root, "led", led)
    prop(root, "arm_l", 0.2)
    prop(root, "arm_r", 0.2)

    shell = mesh_obj(f"{name}.shell", bpy.ops.mesh.primitive_uv_sphere_add, mat_chrome(f"{name}.chrome", "probe"),
                     root, radius=r, segments=48, ring_count=24, location=(0, 0, 0))
    smooth(shell)
    # Lens: a dark glass bulge in a chrome bezel, facing -Y.
    bezel = mesh_obj(f"{name}.bezel", bpy.ops.mesh.primitive_torus_add, mat_chrome(f"{name}.bezel", "chrome"), root,
                     major_radius=r * 0.42, minor_radius=r * 0.07, location=(0, -r * 0.9, r * 0.05),
                     rotation=(math.pi / 2, 0, 0))
    smooth(bezel)
    lens = mesh_obj(f"{name}.lens", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.lens", "lens", 0.02),
                    root, radius=r * 0.4, segments=32, ring_count=16, location=(0, -r * 0.78, r * 0.05))
    lens.scale = (1, 0.55, 1)
    smooth(lens)
    iris = mesh_obj(f"{name}.iris", bpy.ops.mesh.primitive_circle_add, mat_emission(f"{name}.iris", led_role, 6.0, root, "led"),
                    root, radius=r * 0.16, vertices=32, fill_type="NGON", location=(0, -r * 1.0, r * 0.05),
                    rotation=(math.pi / 2, 0, 0))
    # Status LED on top, in a small acrylic dome.
    ledo = mesh_obj(f"{name}.led", bpy.ops.mesh.primitive_uv_sphere_add,
                    mat_emission(f"{name}.led", led_role, 40.0, root, "led"), root, radius=r * 0.13, segments=16,
                    ring_count=8, location=(0, -r * 0.1, r * 0.97))
    smooth(ledo)
    # Arms: two-segment thin chrome rods from the equator, with a tiny pincer.
    for side, sx in (("l", -1), ("r", 1)):
        shoulder = empty(f"{name}.shoulder_{side}", (sx * r * 0.92, 0, -r * 0.1), root)
        upper = mesh_obj(f"{name}.upper_{side}", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.arm", "chrome"),
                         shoulder, radius=r * 0.045, depth=r * 1.1, vertices=12, location=(0, 0, -r * 0.55))
        elbow = empty(f"{name}.elbow_{side}", (0, 0, -r * 1.1), shoulder)
        fore = mesh_obj(f"{name}.fore_{side}", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.arm", "chrome"),
                        elbow, radius=r * 0.035, depth=r * 0.9, vertices=12, location=(0, 0, -r * 0.45))
        joint = mesh_obj(f"{name}.joint_{side}", bpy.ops.mesh.primitive_uv_sphere_add, mat_chrome(f"{name}.arm", "chrome"),
                         elbow, radius=r * 0.07, segments=12, ring_count=8, location=(0, 0, 0))
        for k in (-1, 1):
            f = mesh_obj(f"{name}.finger_{side}{k}", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.arm", "chrome"),
                         elbow, size=1, location=(k * r * 0.05, 0, -r * 0.95))
            f.scale = (r * 0.025, r * 0.05, r * 0.16)
        # Reach 0 = arm folded along the body, 1 = stretched forward.
        drive(shoulder, "rotation_euler", 0, root, f"arm_{side}", "-0.25 - 1.25 * x")
        drive(shoulder, "rotation_euler", 1, root, f"arm_{side}", f"{sx} * (0.35 - 0.2 * x)")
        drive(elbow, "rotation_euler", 0, root, f"arm_{side}", "-1.1 + 0.95 * x")
    return root


# ---------------------------------------------------------------- server blade

def blade(name="blade", loc=(0, 0, 0), rot_z=0.0, width=0.48, height=0.09, depth=0.62, slats=9):
    """A 2U server blade: glossy pale chassis, chrome handles, a louvred front grille whose slats open with "vent",
    and a row of status LEDs. Front faces -Y."""
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    prop(root, "vent", 0.0)
    prop(root, "led", 0.5)

    body = mesh_obj(f"{name}.body", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.body", "lab"), root,
                    size=1, location=(0, 0, height / 2))
    body.scale = (width, depth, height)
    bevel(body, 0.006)
    # Chrome face plate, a recessed dark grille well in it, the glow behind, the louvres in front.
    face = mesh_obj(f"{name}.face", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.face", "chrome"), root,
                    size=1, location=(0, -depth / 2 - 0.002, height / 2))
    face.scale = (width * 0.98, 0.004, height * 0.94)
    bevel(face, 0.002, 2)
    gw, gh = width * 0.74, height * 0.8
    well = mesh_obj(f"{name}.well", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.well", "shadow", 0.4), root,
                    size=1, location=(-width * 0.07, -depth / 2 - 0.0035, height / 2))
    well.scale = (gw, 0.004, gh)
    glow = mesh_obj(f"{name}.glow", bpy.ops.mesh.primitive_plane_add,
                    mat_emission(f"{name}.glow", "lab_glow", 4.0, root, "vent"), root, size=1,
                    location=(-width * 0.07, -depth / 2 - 0.006, height / 2), rotation=(math.pi / 2, 0, 0))
    glow.scale = (gw * 0.97, gh * 0.9, 1)
    slat_h = gh / slats
    for i in range(slats):
        z = height / 2 - gh / 2 + slat_h * (i + 0.5)
        pivot = empty(f"{name}.slat_pivot{i}", (-width * 0.07, -depth / 2 - 0.009, z), root)
        s = mesh_obj(f"{name}.slat{i}", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.slat", "lab", 0.1), pivot,
                     size=1, location=(0, 0, 0))
        s.scale = (gw, slat_h * 0.98, 0.002)
        s.rotation_euler = (math.pi / 2, 0, 0)
        # vent 0: slats vertical (closed); 1: rotated 70° (open, the glow shows through).
        drive(pivot, "rotation_euler", 0, root, "vent", "1.22 * x")
    # Handles.
    for sx in (-1, 1):
        h = mesh_obj(f"{name}.handle{sx}", bpy.ops.mesh.primitive_torus_add, mat_chrome(f"{name}.handle", "chrome"), root,
                     major_radius=height * 0.28, minor_radius=0.004, location=(sx * width * 0.46, -depth / 2 - 0.009,
                                                                               height / 2),
                     rotation=(0, math.pi / 2, 0))
        h.scale = (1, 0.5, 1)
    # Status LEDs right of the grille.
    for i in range(3):
        mesh_obj(f"{name}.ledrow{i}", bpy.ops.mesh.primitive_uv_sphere_add,
                 mat_emission(f"{name}.ledrow{i}", "amber" if i == 0 else "lab_glow", 12.0, root, "led"), root,
                 radius=0.0045, segments=12, ring_count=6,
                 location=(width * 0.36 + i * 0.016, -depth / 2 - 0.005, height * 0.5))
    return root


# ---------------------------------------------------------------- the sandbox cube

def glass_cube(name="sandbox", size=2.0, loc=(0, 0, 0)):
    """Glass cube with thin chrome edge frame, standing on the floor. Returns the root empty."""
    root = empty(name, loc)
    glass = mat_glass(f"{name}.glass")
    half = size / 2
    panes = {"front": ((0, -half, half), (math.pi / 2, 0, 0)), "back": ((0, half, half), (math.pi / 2, 0, 0)),
             "left": ((-half, 0, half), (math.pi / 2, 0, math.pi / 2)),
             "right": ((half, 0, half), (math.pi / 2, 0, math.pi / 2)), "top": ((0, 0, size), (0, 0, 0))}
    for side, (p, r) in panes.items():
        mesh_obj(f"{name}.pane_{side}", bpy.ops.mesh.primitive_plane_add, glass, root, size=size, location=p,
                 rotation=r)
    # Edge frame: 12 thin chrome bars.
    t = 0.018
    half = size / 2
    edges = []
    for a in (-1, 1):
        for b in (-1, 1):
            edges += [((0, a * half, half + b * half), (size + t, t, t)),
                      ((a * half, 0, half + b * half), (t, size + t, t)),
                      ((a * half, b * half, half), (t, t, size + t))]
    for i, (p, s) in enumerate(edges):
        e = mesh_obj(f"{name}.edge{i}", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.edge", "chrome"), root,
                     size=1, location=p)
        e.scale = s
        bevel(e, t * 0.3, 2)
    return root
