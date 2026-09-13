"""Build the restrained Factory Dusk coffee-kiosk and luxury-SUV vignette."""
import bpy
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "assets", "environment", "factory-dusk")
BLEND_PATH = os.path.join(ROOT, "blender", "factory-dusk-vignette.blend")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)


def material(name, color, metallic=0.0, roughness=0.8, emission=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.2
    return mat


PAINT = material("Kiosk_Painted_Metal", (0.30, 0.31, 0.28), metallic=0.25, roughness=0.68)
DARK = material("Vignette_Dark_Glass", (0.025, 0.035, 0.035), metallic=0.05, roughness=0.3)
WARM = material("Kiosk_Warm_Practical", (0.35, 0.20, 0.08), roughness=0.55, emission=(1.0, 0.43, 0.12))
WOOD = material("Kiosk_Dark_Wood", (0.18, 0.12, 0.075), roughness=0.9)
BODY = material("SUV_Off_Black_Body", (0.045, 0.052, 0.05), metallic=0.45, roughness=0.42)
RUBBER = material("SUV_Rubber", (0.012, 0.014, 0.014), roughness=0.92)
METAL = material("SUV_Muted_Metal", (0.18, 0.19, 0.18), metallic=0.65, roughness=0.5)


def clear_collection(name):
    collection = bpy.data.collections.get(name)
    if collection:
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def cube(collection, name, location, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = move_to(bpy.context.object, collection)
    obj.name = name
    obj.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("Restrained edge bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(mat)
    return obj


def cylinder(collection, name, location, radius, depth, mat, rotation=(math.pi / 2, 0, 0), vertices=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = move_to(bpy.context.object, collection)
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def root_for(collection, name):
    root = bpy.data.objects.new(name, None)
    collection.objects.link(root)
    for obj in collection.objects:
        if obj != root:
            obj.parent = root
    return root


def export_collection(collection, root, filename):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in collection.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(OUT_DIR, filename), export_format="GLB",
        use_selection=True, export_yup=True, export_apply=True,
        export_materials="EXPORT", export_cameras=False, export_lights=False,
    )


def metrics(collection):
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    return {
        "meshes": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(len(poly.vertices) - 2 for obj in meshes for poly in obj.data.polygons),
        "materials": len({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}),
    }


# Compact prefab kiosk: intentionally cleaner than its industrial surroundings.
kiosk = clear_collection("Factory_Dusk_Coffee_Kiosk")
cube(kiosk, "Kiosk_Shell", (0, 0, 1.15), (2.75, 1.8, 2.3), PAINT, .06)
cube(kiosk, "Kiosk_Roof", (0, 0, 2.38), (3.05, 2.05, .16), DARK, .05)
cube(kiosk, "Service_Window", (0, -.916, 1.42), (1.62, .045, .82), DARK)
cube(kiosk, "Warm_Window_Glow", (0, -.943, 1.42), (1.38, .025, .58), WARM)
cube(kiosk, "Service_Counter", (0, -1.08, .91), (2.0, .34, .14), WOOD, .035)
cube(kiosk, "Slim_Canopy", (0, -1.16, 2.02), (2.25, .72, .12), PAINT, .035)
cube(kiosk, "Blank_Menu_Board", (1.0, -.95, 1.48), (.38, .04, .65), WOOD, .02)
cube(kiosk, "Warm_Light_Strip", (0, -1.19, 1.96), (1.25, .035, .055), WARM)
kiosk_root = root_for(kiosk, "Coffee_Kiosk_Root")
export_collection(kiosk, kiosk_root, "coffee-kiosk.glb")


# One heavy, status-coded, G-Class-inspired silhouette; no detailed interior.
suv = clear_collection("Factory_Dusk_Luxury_SUV")
cube(suv, "SUV_Lower_Body", (0, 0, .72), (3.7, 1.7, .72), BODY, .12)
cube(suv, "SUV_Cabin", (-.25, 0, 1.30), (2.55, 1.62, .82), BODY, .1)
cube(suv, "SUV_Hood", (1.42, 0, 1.04), (.88, 1.62, .38), BODY, .06)
cube(suv, "SUV_Windscreen", (.57, 0, 1.48), (.08, 1.48, .52), DARK, .02)
cube(suv, "SUV_Side_Windows_Left", (-.4, -.825, 1.42), (1.55, .035, .48), DARK, .015)
cube(suv, "SUV_Side_Windows_Right", (-.4, .825, 1.42), (1.55, .035, .48), DARK, .015)
cube(suv, "SUV_Grille", (1.875, 0, .93), (.035, 1.15, .34), METAL, .02)
cube(suv, "SUV_Rear_Spare", (-1.88, 0, 1.03), (.18, .72, .72), RUBBER, .04)
for x in (-1.17, 1.17):
    for y in (-.88, .88):
        cylinder(suv, f"Wheel_{x}_{y}", (x, y, .48), .38, .22, RUBBER)
        cylinder(suv, f"WheelHub_{x}_{y}", (x, y * 1.01, .48), .17, .235, METAL)
for y in (-.5, .5):
    cube(suv, f"Headlamp_{y}", (1.9, y, 1.08), (.04, .28, .18), WARM, .02)
suv_root = root_for(suv, "Luxury_SUV_Root")
export_collection(suv, suv_root, "luxury-suv.glb")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print({
    "kiosk": metrics(kiosk), "suv": metrics(suv),
    "kiosk_glb": os.path.join(OUT_DIR, "coffee-kiosk.glb"),
    "suv_glb": os.path.join(OUT_DIR, "luxury-suv.glb"),
    "blend": BLEND_PATH,
})
