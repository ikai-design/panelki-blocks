"""Build and export the Factory Dusk Chernobyl-inspired landmark."""

import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "public", "assets", "environment", "factory-dusk")
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "chernobyl-station.glb")
OUTPUT_BLEND = os.path.join(ROOT, "blender", "chernobyl-station.blend")
COLLECTION_NAME = "Chernobyl_Station_Landmark"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)


def make_material(name, color, roughness, metallic=0.0, emission=None, emission_strength=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return material


def link_only_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def box(collection, name, location, dimensions, material, bevel=0.0, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Restrained bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    link_only_to_collection(obj, collection)
    return obj


def pipe(collection, name, start, end, radius, material, vertices=8):
    a, b = Vector(start), Vector(end)
    direction = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


def arch_shell(collection, material):
    """Create a broad, segmented, shallow confinement arch with no interior detail."""
    cx, cy, base = 3.2, -1.9, 0.12
    outer_x, outer_z = 4.0, 4.55
    inner_x, inner_z = 3.55, 4.08
    half_depth = 1.85
    segments = 12
    vertices = []
    faces = []
    for segment in range(segments):
        a0 = math.pi - segment * math.pi / segments
        a1 = math.pi - (segment + 1) * math.pi / segments
        ring = []
        for y in (cy - half_depth, cy + half_depth):
            ring.extend([
                (cx + math.cos(a0) * outer_x, y, base + math.sin(a0) * outer_z),
                (cx + math.cos(a1) * outer_x, y, base + math.sin(a1) * outer_z),
                (cx + math.cos(a1) * inner_x, y, base + math.sin(a1) * inner_z),
                (cx + math.cos(a0) * inner_x, y, base + math.sin(a0) * inner_z),
            ])
        offset = len(vertices)
        vertices.extend(ring)
        faces.extend([
            (offset, offset + 1, offset + 2, offset + 3),
            (offset + 4, offset + 7, offset + 6, offset + 5),
            (offset, offset + 4, offset + 5, offset + 1),
            (offset + 1, offset + 5, offset + 6, offset + 2),
            (offset + 2, offset + 6, offset + 7, offset + 3),
            (offset + 3, offset + 7, offset + 4, offset),
        ])
    mesh = bpy.data.meshes.new("Confinement_Arch_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("New_Safe_Confinement_Arch", mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def join_by_material(collection, root):
    """Collapse repeated modules to one mesh per material for predictable draw calls."""
    material_groups = {}
    for obj in [item for item in collection.objects if item.type == "MESH"]:
        key = obj.data.materials[0].name if obj.data.materials else "Unassigned"
        material_groups.setdefault(key, []).append(obj)
    for material_name, objects in material_groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        merged = bpy.context.object
        merged.name = material_name.replace(" ", "_")
        merged.parent = root


# Replace only this authored collection so reruns remain deterministic.
old_collection = bpy.data.collections.get(COLLECTION_NAME)
if old_collection:
    for old_object in list(old_collection.objects):
        bpy.data.objects.remove(old_object, do_unlink=True)
    bpy.data.collections.remove(old_collection)

collection = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(collection)
root = bpy.data.objects.new("Chernobyl_Station_Root", None)
collection.objects.link(root)

concrete = make_material("Station Concrete", (0.25, 0.28, 0.29), 0.94)
dark_metal = make_material("Station Dark Metal", (0.08, 0.10, 0.11), 0.78, 0.32)
arch_metal = make_material("Confinement Cold Metal", (0.43, 0.49, 0.51), 0.72, 0.38)
rust = make_material("Station Muted Rust", (0.30, 0.15, 0.09), 0.90, 0.10)
warm = make_material("Station Dim Amber", (0.20, 0.11, 0.045), 0.62, emission=(0.78, 0.30, 0.08), emission_strength=1.1)

# Monumental horizontal turbine hall and stepped reactor masses.
box(collection, "Turbine_Hall", (-2.6, 0.45, 1.55), (12.6, 3.7, 3.1), concrete, 0.05)
box(collection, "Turbine_Hall_Roof", (-2.6, 0.45, 3.16), (12.95, 3.95, 0.13), dark_metal)
box(collection, "Lower_Service_Wing", (-5.1, -1.0, 0.75), (7.1, 1.15, 1.5), dark_metal, 0.035)
box(collection, "Reactor_Block", (3.25, 0.35, 2.35), (5.4, 4.1, 4.7), concrete, 0.055)
box(collection, "Reactor_Upper_Mass", (2.8, 0.45, 4.45), (3.3, 3.15, 1.05), dark_metal, 0.04)
box(collection, "Roof_Utility_A", (-0.9, 0.7, 3.7), (2.4, 1.5, 0.95), dark_metal, 0.035)
box(collection, "Roof_Utility_B", (-4.7, 0.5, 3.55), (1.6, 1.4, 0.72), dark_metal, 0.03)

# The cold arch is the strongest identification cue at gameplay distance.
arch_shell(collection, arch_metal)
for x in (0.1, 1.7, 3.2, 4.7, 6.3):
    box(collection, "Arch_Panel_Seam", (x, -3.765, 2.1 if x not in (0.1, 6.3) else 1.25), (0.055, 0.025, 1.35), dark_metal)

# One tapered stack with restrained oxidation bands.
pipe(collection, "Ventilation_Stack", (-7.4, 0.5, 0.05), (-7.4, 0.5, 8.1), 0.48, concrete, 12)
for z in (2.2, 5.5, 7.7):
    pipe(collection, "Stack_Rust_Band", (-7.4, 0.5, z), (-7.4, 0.5, z + 0.24), 0.51, rust, 12)
pipe(collection, "Stack_Cap", (-7.4, 0.5, 8.05), (-7.4, 0.5, 8.28), 0.57, dark_metal, 12)

# A simple service gantry and two pipe runs add depth without dense machinery.
for x in (-5.7, -3.8, -1.9):
    pipe(collection, "Gantry_Leg", (x, -2.1, 0.1), (x, -2.1, 2.05), 0.07, dark_metal)
pipe(collection, "Gantry_Top", (-5.9, -2.1, 2.05), (-1.7, -2.1, 2.05), 0.08, dark_metal)
pipe(collection, "Service_Pipe_A", (-6.0, -2.15, 1.55), (-1.6, -2.15, 1.55), 0.12, rust)
pipe(collection, "Service_Pipe_B", (-6.0, -2.15, 1.18), (-1.6, -2.15, 1.18), 0.09, arch_metal)

# Sparse warm rectangles read as distant occupied control rooms, not light sources.
for x, z in [(-5.5, 1.45), (-4.5, 1.45), (-3.3, 2.25), (-2.2, 2.25), (-0.8, 1.45), (0.2, 1.45)]:
    box(collection, "Dim_Window", (x, -1.415, z), (0.48, 0.035, 0.28), warm)
for x in (-6.8, -7.4, -8.0):
    box(collection, "Stack_Base_Light", (x, -1.42, 0.55), (0.22, 0.03, 0.22), warm)

# Apply transforms and merge by material before export.
for obj in list(collection.objects):
    if obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj.select_set(False)
join_by_material(collection, root)

# Validate outward normals on every exported mesh.
for obj in [item for item in collection.objects if item.type == "MESH"]:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)

bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for obj in collection.objects:
    if obj.type == "MESH":
        obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_materials="EXPORT",
    export_cameras=False,
    export_lights=False,
)

triangles = sum(len(poly.vertices) - 2 for obj in collection.objects if obj.type == "MESH" for poly in obj.data.polygons)
vertices = sum(len(obj.data.vertices) for obj in collection.objects if obj.type == "MESH")
meshes = sum(1 for obj in collection.objects if obj.type == "MESH")
print({"glb": OUTPUT_GLB, "blend": OUTPUT_BLEND, "triangles": triangles, "vertices": vertices, "meshes": meshes, "materials": len({mat.name for obj in collection.objects if obj.type == 'MESH' for mat in obj.data.materials if mat})})
