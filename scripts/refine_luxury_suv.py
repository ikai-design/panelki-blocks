"""One-pass silhouette refinement of the Factory Dusk luxury SUV."""
import bpy
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "assets", "environment", "factory-dusk", "luxury-suv.glb")
BLEND = os.path.join(ROOT, "blender", "factory-dusk-vignette.blend")


def mat(name, color, metallic=0.0, roughness=0.8, emission=None):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = 1.6
    return material


BODY = mat("SUV_Deep_Olive_Body", (.075, .085, .068), .38, .48)
GLASS = mat("SUV_Smoked_Glass", (.018, .027, .028), .08, .24)
RUBBER = mat("SUV_Rubber_Trim", (.012, .014, .013), 0, .9)
METAL = mat("SUV_Dark_Metal", (.14, .15, .14), .55, .55)
LIGHT = mat("SUV_Warm_Lamps", (.32, .19, .075), 0, .48, (1.0, .43, .13))


collection = bpy.data.collections.get("Factory_Dusk_Luxury_SUV")
if collection:
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    collection = bpy.data.collections.new("Factory_Dusk_Luxury_SUV")
    bpy.context.scene.collection.children.link(collection)


def move(obj):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def cube(name, location, size, material, bevel=0.0, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = move(bpy.context.object)
    obj.name = name
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("Low-poly edge bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    return obj


def cylinder(name, location, radius, depth, material, rotation, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = move(bpy.context.object)
    obj.name = name
    obj.data.materials.append(material)
    return obj


def side_window(name, x, side, width):
    return cube(name, (x, side, 1.48), (width, .035, .48), GLASS, .012)


# Strong three-volume silhouette with a higher roof and more distinct hood.
cube("SUV_Main_Body", (0, 0, .78), (3.82, 1.72, .7), BODY, .1)
cube("SUV_Cabin", (-.32, 0, 1.39), (2.58, 1.62, .92), BODY, .065)
cube("SUV_Roof_Cap", (-.34, 0, 1.9), (2.72, 1.69, .12), BODY, .045)
cube("SUV_Hood", (1.42, 0, 1.12), (.92, 1.62, .35), BODY, .055, (0, -.035, 0))

# Windshield gains a believable rake; side glazing is split by visible pillars.
cube("SUV_Windscreen", (.55, 0, 1.52), (.065, 1.48, .57), GLASS, .018, (0, -.16, 0))
for side in (-.825, .825):
    side_window(f"Front_Window_{side}", .12, side, .78)
    side_window(f"Rear_Window_{side}", -.78, side, .72)
    cube(f"B_Pillar_{side}", (-.35, side, 1.49), (.115, .05, .58), RUBBER, .01)
    cube(f"Door_Seam_Front_{side}", (.52, side * 1.002, .94), (.025, .025, .62), RUBBER)
    cube(f"Door_Seam_Rear_{side}", (-1.12, side * 1.002, .94), (.025, .025, .62), RUBBER)
    cube(f"Side_Mirror_{side}", (.67, side * 1.12, 1.43), (.28, .22, .18), BODY, .035)

# Larger wheels and simple squared fender brows improve stance at gameplay distance.
for x in (-1.2, 1.22):
    for side in (-.9, .9):
        cylinder(f"Wheel_{x}_{side}", (x, side, .51), .43, .24, RUBBER, (math.pi / 2, 0, 0))
        cylinder(f"Wheel_Hub_{x}_{side}", (x, side * 1.008, .51), .2, .255, METAL, (math.pi / 2, 0, 0), 10)
        cube(f"Fender_Brow_{x}_{side}", (x, side * .99, .83), (.96, .12, .18), BODY, .035)

# Layered front and rear details replace the previous flat plates.
cube("SUV_Front_Bumper", (1.94, 0, .65), (.18, 1.78, .22), RUBBER, .045)
cube("SUV_Grille_Frame", (1.945, 0, 1.05), (.06, 1.1, .38), METAL, .025)
for side in (-.5, .5):
    cylinder(f"Round_Headlamp_{side}", (1.99, side, 1.18), .15, .07, LIGHT, (0, math.pi / 2, 0), 10)
cube("SUV_Rear_Bumper", (-1.96, 0, .64), (.16, 1.76, .2), RUBBER, .04)
cylinder("SUV_Rear_Spare_Wheel", (-2.02, 0, 1.12), .43, .2, RUBBER, (0, math.pi / 2, 0), 12)
cylinder("SUV_Rear_Spare_Hub", (-2.14, 0, 1.12), .18, .06, METAL, (0, math.pi / 2, 0), 10)

root = bpy.data.objects.new("Luxury_SUV_Root", None)
collection.objects.link(root)
for obj in collection.objects:
    if obj != root:
        obj.parent = root

bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for obj in collection.objects:
    if obj.type == "MESH":
        obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_materials="EXPORT", export_cameras=False, export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

meshes = [obj for obj in collection.objects if obj.type == "MESH"]
print({
    "glb": OUT,
    "blend": BLEND,
    "meshes": len(meshes),
    "vertices": sum(len(obj.data.vertices) for obj in meshes),
    "triangles": sum(len(poly.vertices) - 2 for obj in meshes for poly in obj.data.polygons),
    "materials": len({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}),
})
