"""Build a UV-mapped, glTF-safe PBR prototype from the production Khrushchovka GLB.

The production asset is read-only. Generated PNG authoring maps are kept beside the
project assets for inspection, and Blender embeds them into the prototype GLB.
"""

import math
import os
import struct
import zlib
from array import array
from binascii import crc32

import bpy


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "public", "assets", "buildings", "khrushchovka.glb")
OUTPUT = os.path.join(ROOT, "public", "assets", "buildings", "khrushchyovka-textured-v1.glb")
TEXTURE_DIR = os.path.join(ROOT, "public", "assets", "textures", "khrushchovka-v1")
SIZE = 512


def save_rgba(name, pixels, color_space):
    """Save an authoring PNG and return the Blender image used by the material."""
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    path = os.path.join(TEXTURE_DIR, f"{name}.png")

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc32(kind + data) & 0xFFFFFFFF)

    rows = []
    for y in range(SIZE):
        start = y * SIZE * 4
        row = bytes(max(0, min(255, round(value * 255))) for value in pixels[start:start + SIZE * 4])
        rows.append(b"\x00" + row)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as file:
        file.write(png)

    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = color_space
    print("MAP", name, "range", round(min(pixels), 3), round(max(pixels), 3), "bytes", len(png))
    return image


def make_maps():
    """Author restrained, low-frequency maps that stay readable at game distance."""
    base = array("f")
    rough = array("f")
    height = [0.0] * (SIZE * SIZE)
    emissive = array("f")

    for y in range(SIZE):
        for x in range(SIZE):
            broad = math.sin(x * 0.031) * 0.45 + math.sin(y * 0.024 + 1.3) * 0.35
            broad += math.sin((x + y) * 0.012) * 0.2
            seam = min(x % 128, y % 128, 128 - (x % 128), 128 - (y % 128)) < 3
            stain = max(0.0, math.sin(x * 0.009 - y * 0.014)) * 0.025
            variation = broad * 0.022 - stain - (0.045 if seam else 0.0)
            base.extend((0.56 + variation, 0.55 + variation * 0.92, 0.50 + variation * 0.76, 1.0))
            r = max(0.64, min(0.9, 0.76 + broad * 0.035 + (0.08 if seam else 0.0)))
            rough.extend((r, r, r, 1.0))
            height[y * SIZE + x] = broad * 0.012 - (0.025 if seam else 0.0)

            u = (x + 0.5) / SIZE - 0.5
            v = (y + 0.5) / SIZE - 0.5
            falloff = max(0.38, 1.0 - (u * u * 1.2 + v * v * 1.6))
            emissive.extend((1.0 * falloff, 0.46 * falloff, 0.16 * falloff, 1.0))

    normal = array("f")
    for y in range(SIZE):
        for x in range(SIZE):
            left = height[y * SIZE + max(0, x - 1)]
            right = height[y * SIZE + min(SIZE - 1, x + 1)]
            down = height[max(0, y - 1) * SIZE + x]
            up = height[min(SIZE - 1, y + 1) * SIZE + x]
            nx, ny, nz = (left - right) * 2.2, (down - up) * 2.2, 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            normal.extend((nx / length * 0.5 + 0.5, ny / length * 0.5 + 0.5, nz / length * 0.5 + 0.5, 1.0))

    return {
        "base": save_rgba("concrete-basecolor", base, "sRGB"),
        "rough": save_rgba("concrete-roughness", rough, "Non-Color"),
        "normal": save_rgba("concrete-normal", normal, "Non-Color"),
        "emissive": save_rgba("window-emissive", emissive, "sRGB"),
    }


def principled(name, base_color, roughness, metallic=0.0, emission=None, strength=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return material


def image_node(material, image, label, colorspace):
    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = node.label = label
    node.image = image
    node.image.colorspace_settings.name = colorspace
    return node


def concrete_material(maps):
    material = principled("PBR Concrete", (0.58, 0.57, 0.52), 0.76)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    base = image_node(material, maps["base"], "Base Color · sRGB", "sRGB")
    rough = image_node(material, maps["rough"], "Roughness · Non-Color", "Non-Color")
    normal = image_node(material, maps["normal"], "Normal · Non-Color", "Non-Color")
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.inputs["Strength"].default_value = 0.22
    links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(normal.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def emissive_material(name, maps, base_color, strength):
    material = principled(name, base_color, 0.42, emission=(1.0, 0.45, 0.15), strength=strength)
    node = image_node(material, maps["emissive"], "Emissive · sRGB", "sRGB")
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    material.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
    return material


def connected_polygon_groups(mesh, polygon_indices):
    """Return connected face islands so every window box gets one material state."""
    by_vertex = [[] for _ in mesh.vertices]
    for polygon_index in polygon_indices:
        polygon = mesh.polygons[polygon_index]
        for vertex in polygon.vertices:
            by_vertex[vertex].append(polygon.index)
    unseen = set(polygon_indices)
    groups = []
    while unseen:
        stack = [unseen.pop()]
        group = []
        while stack:
            index = stack.pop()
            group.append(index)
            neighbours = set()
            for vertex in mesh.polygons[index].vertices:
                neighbours.update(by_vertex[vertex])
            for neighbour in neighbours & unseen:
                unseen.remove(neighbour)
                stack.append(neighbour)
        groups.append(group)
    return groups


def add_uvs(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    obj.data.uv_layers.active.name = "UVMap"
    for polygon in obj.data.polygons:
        polygon.use_smooth = False


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SOURCE)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("No meshes imported from source GLB")

maps = make_maps()
concrete = concrete_material(maps)
glass = principled("Window · dark glass", (0.035, 0.055, 0.06), 0.28)
window_dim = emissive_material("Window · dim warm", maps, (0.18, 0.10, 0.045), 0.38)
window_bright = emissive_material("Window · bright warm", maps, (0.38, 0.19, 0.065), 0.9)
window_cool = principled("Window · muted cool", (0.055, 0.10, 0.12), 0.36, emission=(0.10, 0.18, 0.22), strength=0.28)
metal = principled("Metal · dark painted", (0.12, 0.13, 0.13), 0.58, metallic=0.42)
detail = principled("Detail · fabric", (0.66, 0.62, 0.50), 0.86)
plants = principled("Detail · plants", (0.22, 0.31, 0.20), 0.92)

for obj in meshes:
    original_names = [material.name if material else "" for material in obj.data.materials]
    original_by_polygon = [original_names[polygon.material_index] for polygon in obj.data.polygons]
    add_uvs(obj)
    obj.data.materials.clear()
    materials = (concrete, glass, window_dim, window_bright, window_cool, metal, detail, plants)
    for material in materials:
        obj.data.materials.append(material)

    lit_polygons = []
    for polygon, original in zip(obj.data.polygons, original_by_polygon):
        if original.startswith(("Facade", "Precast")):
            polygon.material_index = 0
        elif original.startswith("Evening blue glass"):
            polygon.material_index = 1
        elif original.startswith("Someone is home"):
            lit_polygons.append(polygon.index)
        elif original.startswith("Balcony rust"):
            polygon.material_index = 5
        elif original.startswith("Curtains"):
            polygon.material_index = 6
        else:
            polygon.material_index = 7

    for index, group in enumerate(connected_polygon_groups(obj.data, lit_polygons)):
        state = (2, 3, 2, 4, 2, 3)[index % 6]
        for polygon_index in group:
            obj.data.polygons[polygon_index].material_index = state
    obj.data.validate(clean_customdata=False)
    obj.data.update()

# Preserve the source transform contract: no object movement, no scaling, no rotation.
bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.export_scene.gltf(
    filepath=OUTPUT,
    use_selection=True,
    export_format="GLB",
    export_apply=False,
    export_yup=True,
    export_materials="EXPORT",
    export_cameras=False,
    export_lights=False,
)
print("EXPORTED", OUTPUT)
print("MESHES", len(meshes), "MATERIALS", len({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}))
print("UVS", [(obj.name, len(obj.data.uv_layers), len(obj.data.uv_layers.active.data)) for obj in meshes])
