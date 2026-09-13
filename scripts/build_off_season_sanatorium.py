"""Build a browser-sized Off-Season Sanatorium kit in the connected Blender scene.

The script creates a separate scene, preserves the user's prior scene, exports five
GLBs with ground-level origins, and saves a reusable Blender source file.
"""

import bpy
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "assets", "environment", "off-season-sanatorium")
BLEND_PATH = os.path.join(ROOT, "blender", "off-season-sanatorium.blend")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)

scene = bpy.data.scenes.new("Off-Season Sanatorium")
bpy.context.window.scene = scene


def material(name, color, roughness=0.82, metalness=0.0, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metalness
    if emission:
        shader.inputs["Emission Color"].default_value = (*emission, 1)
        shader.inputs["Emission Strength"].default_value = 0.8
    return mat


CONCRETE = material("Sanatorium_Weathered_Concrete", (.43, .46, .45))
PLASTER = material("Sanatorium_Cream_Plaster", (.65, .64, .57))
AQUA = material("Sanatorium_Faded_Aqua", (.25, .43, .43))
GLASS = material("Sanatorium_Muted_Glass", (.08, .16, .19), .38)
METAL = material("Sanatorium_Painted_Metal", (.25, .31, .32), .68, .25)
PAVING = material("Sanatorium_Pale_Paving", (.47, .49, .46))
WOOD = material("Sanatorium_Dull_Wood", (.38, .31, .23))
WARM = material("Sanatorium_Warm_Interior", (.65, .48, .28), .55, 0, (.65, .4, .18))
DRY = material("Sanatorium_Dry_Planting", (.27, .30, .23))
POOL = material("Sanatorium_Empty_Pool", (.27, .48, .48))


def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


def move(obj, c, name, mat):
    obj.name = name
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    c.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def box(c, name, center, size, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(location=center)
    obj = move(bpy.context.object, c, name, mat)
    obj.scale = tuple(v / 2 for v in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Quiet edge", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cylinder(c, name, center, radius, depth, mat, vertices=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=center)
    return move(bpy.context.object, c, name, mat)


def beam(c, name, a, b, thickness, mat):
    start, end = __import__("mathutils").Vector(a), __import__("mathutils").Vector(b)
    mid = (start + end) / 2
    obj = box(c, name, mid, (thickness, thickness, (end - start).length), mat)
    obj.rotation_euler = (end - start).to_track_quat("Z", "Y").to_euler()
    return obj


def combine_by_material(c):
    """Merge matching materials to keep each GLB's draw calls modest."""
    for mat in (CONCRETE, PLASTER, AQUA, GLASS, METAL, PAVING, WOOD, WARM, DRY, POOL):
        meshes = [o for o in c.objects if o.type == "MESH" and o.active_material == mat]
        if len(meshes) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
        meshes[0].name = f"{c.name}_{mat.name}"


def export(c, name):
    combine_by_material(c)
    root = bpy.data.objects.new(f"{name}_Root", None)
    c.objects.link(root)
    for obj in list(c.objects):
        if obj != root and obj.type == "MESH":
            obj.parent = root
            obj.matrix_parent_inverse = root.matrix_world.inverted()
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in c.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    filepath = os.path.join(OUT_DIR, name + ".glb")
    bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True, export_materials="EXPORT",
                              export_cameras=False, export_lights=False)
    meshes = [o for o in c.objects if o.type == "MESH"]
    return {"file": os.path.basename(filepath), "bytes": os.path.getsize(filepath),
            "meshes": len(meshes), "triangles": sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons),
            "materials": len({o.active_material.name for o in meshes})}


# Broad central lobby, two long wings, and restrained terrace rhythm.
main = collection("Sanatorium_Main")
box(main, "East_wing", (3.65, .6, 2.1), (6.1, 3.3, 4.2), PLASTER)
box(main, "West_wing", (-3.65, .6, 2.1), (6.1, 3.3, 4.2), CONCRETE)
box(main, "Central_lobby", (0, -.42, 1.5), (2.1, 4.1, 3), CONCRETE)
box(main, "Lobby_glazing", (0, -2.49, 1.25), (1.86, .04, 2.25), GLASS)
box(main, "Lobby_warm_interior", (0, -2.465, 1.7), (1.4, .025, .54), WARM)
box(main, "Entrance_door", (0, -2.525, .76), (.75, .025, 1.3), METAL)
box(main, "Horizontal_roof", (0, .65, 4.34), (13.9, 3.7, .25), CONCRETE)
box(main, "Reception_roof", (0, -1.12, 3.14), (3.1, 3.2, .18), AQUA)
for x in (-1.05, 1.05):
    cylinder(main, "Canopy_column", (x, -2.7, 1.31), .09, 2.62, METAL)
for i in range(7):
    # A softly segmented modernist canopy is visible from the gameplay camera.
    x = -1.4 + i * .47
    depth = 1.85 + .32 * (1 - abs(x) / 1.4)
    box(main, "Curved_entry_canopy", (x, -2.7, 2.68), (.46, depth, .12), AQUA)
for wing_center in (-3.65, 3.65):
    for level in (1.15, 2.45, 3.75):
        box(main, "Terrace_slab", (wing_center, -1.17, level), (6.35, .65, .13), CONCRETE)
        box(main, "Terrace_rail", (wing_center, -1.5, level + .41), (6.13, .055, .05), METAL)
        for x_step in (-2.35, -.8, .8, 2.35):
            x = wing_center + x_step
            box(main, "Window", (x, -1.07, level - .36), (1.1, .045, .7), WARM if (int(x * 3 + level * 5) % 9 == 0) else GLASS)
            box(main, "Window_sill", (x, -1.12, level - .74), (1.2, .13, .06), PLASTER)
            box(main, "Rail_post", (x, -1.5, level + .2), (.045, .045, .42), METAL)
for x in (-6.65, -4.95, -3.3, -1.65, 1.65, 3.3, 4.95, 6.65):
    box(main, "Roof_parapet", (x, .6, 4.58), (.1, 3.5, .36), CONCRETE)
box(main, "Lobby_name_panel_blank", (0, -2.57, 2.88), (1.58, .035, .18), PLASTER)


# Drained pool: shallow painted bottom, four dry walls, coping and one ladder.
pool = collection("Sanatorium_Empty_Pool")
box(pool, "Pool_slab", (0, 0, .05), (4.9, 3.15, .10), PAVING)
box(pool, "Dry_aqua_floor", (0, 0, .105), (4.35, 2.6, .02), POOL)
for x in (-2.32, 2.32):
    box(pool, "Pool_side_wall", (x, 0, .31), (.22, 3.15, .52), AQUA)
for y in (-1.47, 1.47):
    box(pool, "Pool_end_wall", (0, y, .31), (4.48, .22, .52), AQUA)
for x in (-2.44, 2.44):
    box(pool, "Coping_long", (x, 0, .59), (.17, 3.3, .08), PLASTER)
for y in (-1.58, 1.58):
    box(pool, "Coping_short", (0, y, .59), (4.7, .17, .08), PLASTER)
for x in (-1.55, -1.15):
    beam(pool, "Ladder_rail", (x, -1.35, .23), (x, -1.35, .82), .035, METAL)
for z in (.23, .4, .57):
    box(pool, "Ladder_rung", (-1.35, -1.35, z), (.4, .055, .035), METAL)
box(pool, "Pool_drain", (.9, .4, .12), (.2, .2, .015), METAL)


# Two chairs, a low bench and a ping-pong table form one small recreation kit.
recreation = collection("Sanatorium_Recreation")
for offset in (-.82, .82):
    box(recreation, "Lounger_seat", (offset, 0, .39), (.65, 1.8, .1), PLASTER)
    back = box(recreation, "Lounger_back", (offset, -.64, .78), (.65, .9, .1), AQUA)
    back.rotation_euler.x = -.4
    for side in (-.25, .25):
        beam(recreation, "Lounger_leg", (offset + side, -.58, .35), (offset + side, -.58, .08), .04, METAL)
        beam(recreation, "Lounger_leg", (offset + side, .6, .35), (offset + side, .6, .08), .04, METAL)
box(recreation, "Ping_pong_surface", (3.8, 0, .77), (2.2, 1.15, .1), AQUA)
box(recreation, "Ping_pong_center_line", (3.8, 0, .825), (2.08, .025, .006), PLASTER)
box(recreation, "Ping_pong_net", (3.8, 0, .94), (.045, 1.15, .24), METAL)
for x in (2.95, 4.65):
    for y in (-.37, .37):
        beam(recreation, "Ping_pong_leg", (x, y, .72), (x, y, .08), .06, METAL)
box(recreation, "Bench_seat", (-3.2, 0, .48), (1.7, .48, .12), WOOD)
box(recreation, "Bench_back", (-3.2, .23, .84), (1.7, .1, .67), WOOD)
for x in (-3.85, -2.55):
    beam(recreation, "Bench_leg", (x, 0, .46), (x, 0, .07), .065, METAL)


# The single ironic accent: one open parasol, with nobody using the chairs.
parasol = collection("Sanatorium_Lonely_Parasol")
cylinder(parasol, "Parasol_pole", (0, 0, 1.3), .042, 2.6, METAL, 8)
cylinder(parasol, "Parasol_base", (0, 0, .045), .35, .09, CONCRETE, 10)
for i in range(10):
    a = i * math.tau / 10
    b = (i + 1) * math.tau / 10
    verts = [(0, 0, 2.7), (1.25 * math.cos(a), 1.25 * math.sin(a), 2.25),
             (1.25 * math.cos(b), 1.25 * math.sin(b), 2.25)]
    mesh = bpy.data.meshes.new("Parasol_canopy_panel")
    mesh.from_pydata(verts, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new("Parasol_canopy", mesh)
    parasol.objects.link(obj)
    obj.data.materials.append(PLASTER if i % 2 else AQUA)


# One small planting group: bare trunks, sparse poplar forms, quiet planters.
planting = collection("Sanatorium_Planting")
for i, x in enumerate((-2.1, 0, 2.15)):
    h = 3.2 + i * .38
    cylinder(planting, "Poplar_trunk", (x, 0, h / 2), .075, h, WOOD, 6)
    for side in (-1, 1):
        beam(planting, "Bare_branch", (x, 0, h * .65), (x + side * .28, .07, h * .91), .045, WOOD)
        beam(planting, "Bare_branch", (x, 0, h * .78), (x - side * .2, -.04, h * 1.03), .035, WOOD)
for x in (-3.1, 3.15):
    box(planting, "Planter", (x, -.8, .32), (.76, .76, .64), CONCRETE)
    box(planting, "Planter_soil", (x, -.8, .65), (.61, .61, .025), DRY)
    for dx in (-.18, 0, .17):
        beam(planting, "Dry_stem", (x + dx, -.8, .65), (x + dx + .06, -.8, .88), .02, DRY)


metrics = [export(c, name) for c, name in (
    (main, "sanatorium-main"), (pool, "empty-pool"),
    (recreation, "recreation"), (parasol, "lonely-parasol"),
    (planting, "planting"),
)]
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SANATORIUM_METRICS", json.dumps(metrics))
