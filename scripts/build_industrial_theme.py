"""Create the compact Factory Dusk environment kit and export it as one web GLB."""
import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "public", "assets", "environment", "factory-dusk.glb")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, color, roughness=.86, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


concrete = material("Industrial concrete", (.17, .18, .17), .96)
asphalt = material("Stained asphalt", (.095, .105, .105), .98)
metal = material("Faded galvanized metal", (.19, .22, .22), .72, .35)
rust = material("Muted oxidation", (.27, .12, .065), .91, .12)
dark = material("Warehouse charcoal", (.075, .085, .085), .94)
amber = material("Industrial amber", (.23, .12, .045), .58, 0, (.95, .42, .12), 1.35)
weed = material("Dead weeds", (.19, .17, .105), 1)


def box(name, location, dimensions, mat, rotation=(0, 0, 0), bevel=0):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Small edge bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
    return obj


def pipe(name, start, end, radius, mat, vertices=8):
    a, b = Vector(start), Vector(end)
    direction = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return obj


# A thin asphalt apron visually connects the playfield to the yard without raising it.
box("Asphalt apron", (0, 0, -.055), (14.5, 12.5, .1), asphalt)
for x, y, sx, sy in [(-4.8, 1.4, 2.1, .045), (4.2, -2.1, 1.7, .035), (1.3, 4.7, 2.8, .035)]:
    box("Concrete repair strip", (x, y, .008), (sx, sy, .018), concrete, rotation=(0, 0, -.18))

# Two restrained fence runs: frames plus only a few diagonals to read as chain-link at game distance.
for panel_index, (px, py, angle) in enumerate([(-6.8, 5.6, 0), (7.0, 4.9, 0)]):
    for dx in (-2.6, 0, 2.6):
        pipe(f"Fence {panel_index} post", (px + dx, py, 0), (px + dx, py, 2.15), .055, metal)
    pipe(f"Fence {panel_index} top", (px - 2.6, py, 2.05), (px + 2.6, py, 2.05), .045, metal)
    pipe(f"Fence {panel_index} lower", (px - 2.6, py, .18), (px + 2.6, py, .18), .035, metal)
    for dx in (-2.2, -.9, .4, 1.7):
        pipe(f"Fence {panel_index} mesh", (px + dx, py, .2), (px + dx + 1.2, py, 2.02), .012, metal, 5)

# Low service building at the rear edge.
box("Service warehouse", (-7.8, 2.1, 1.35), (5.6, 3.1, 2.7), dark, bevel=.035)
box("Warehouse roof", (-7.8, 2.1, 2.76), (5.9, 3.35, .12), metal)
box("Loading door", (-6.55, .52, 1.05), (2.2, .08, 2.1), metal)
for x in (-8.8, -7.6):
    box("Warehouse window", (x, .50, 1.75), (.7, .06, .42), amber)

# Transformer cabinet, readable silhouette with restrained rust and vents.
box("Transformer cabinet", (6.7, 2.5, 1.05), (1.65, 1.05, 2.1), metal, bevel=.045)
box("Transformer plinth", (6.7, 2.5, .10), (1.9, 1.25, .2), concrete)
for z in (.72, 1.0, 1.28):
    box("Transformer vent", (6.7, 1.95, z), (.92, .035, .055), dark)
box("Transformer rust patch", (7.45, 2.1, .55), (.035, .28, .52), rust)

# Small pipe rack on the opposite side, kept below the visual height of the field.
for x in (-5.2, -4.25):
    pipe("Pipe rack leg", (x, -4.9, 0), (x, -4.9, 1.25), .075, rust)
for z in (.68, 1.08):
    pipe("Service conduit", (-5.65, -4.9, z), (-3.75, -4.9, z), .105, metal)

# Two economical industrial lamps with emissive fixtures, not exported point lights.
for i, (x, y) in enumerate([(-6.0, -2.8), (6.0, -3.8)]):
    pipe(f"Lamp {i} pole", (x, y, 0), (x, y, 4.2), .09, metal)
    pipe(f"Lamp {i} arm", (x, y, 4.15), (x + .55, y, 4.15), .06, metal)
    box(f"Lamp {i} fixture", (x + .62, y, 4.08), (.42, .32, .16), dark)
    box(f"Lamp {i} glow", (x + .62, y - .17, 4.02), (.28, .025, .08), amber)

# One distant silhouette provides industrial identity without becoming a hero prop.
pipe("Distant smokestack", (10.5, 7.8, 0), (10.5, 7.8, 7.8), .55, concrete, 12)
pipe("Smokestack rim", (10.5, 7.8, 7.65), (10.5, 7.8, 7.95), .67, rust, 12)

# Sparse weed clumps, deliberately limited to six.
for i, (x, y, s) in enumerate([(-3.8, 5.1, .6), (3.9, 5.2, .45), (8.1, -.8, .55), (-8.6, -3.8, .5), (5.1, -5.2, .42), (-5.7, 3.9, .36)]):
    for j, tilt in enumerate((-.22, .08, .29)):
        pipe(f"Weed {i}-{j}", (x, y, 0), (x + tilt * s, y + (j - 1) * .12, .7 * s), .018, weed, 5)

# Export all authored objects in one predictable root scene.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUTPUT,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_materials="EXPORT",
    export_cameras=False,
    export_lights=False,
)
print("EXPORTED", OUTPUT)
print("OBJECTS", len(bpy.context.scene.objects), "MATERIALS", len(bpy.data.materials))
