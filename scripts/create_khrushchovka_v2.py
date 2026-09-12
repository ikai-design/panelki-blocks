"""Create one lightweight façade experiment from the stable Khrushchovka GLB.

This deliberately works from the exported GLB instead of opening the source .blend,
because headless inspection of the original file has been unstable. The production
asset is never overwritten.
"""
import bpy, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, 'public/assets/buildings/khrushchovka.glb')
dst = os.path.join(ROOT, 'public/assets/buildings/khrushchovka-v2.glb')
# Never let Blender's default cube/camera/light contaminate the exported prototype.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
root = bpy.context.selected_objects[0] if bpy.context.selected_objects else None
if root is None:
    raise RuntimeError('Could not import source GLB')

# Add only a few broad façade bands in the imported Blender local space.
# Blender's imported GLTF axes are X=width, Y=depth, Z=height.
mat = bpy.data.materials.new('V2_PanelSeam'); mat.diffuse_color = (0.12, 0.14, 0.14, 1)
for y in (-0.34, 0.0, 0.34):
    bpy.ops.mesh.primitive_cube_add(location=(0, -0.44, y), scale=(0.42, 0.018, 0.018))
    seam = bpy.context.object; seam.name = f'V2_PanelSeam_{y:.2f}'; seam.data.materials.append(mat)

# Simple parapet adds a readable roof silhouette.
roofmat = bpy.data.materials.new('V2_RoofMetal'); roofmat.diffuse_color = (0.16, 0.18, 0.17, 1); roofmat.roughness = .82
bpy.ops.mesh.primitive_cube_add(location=(0, 0, .5), scale=(.43, .43, .018))
roof = bpy.context.object; roof.name = 'V2_RoofParapet'; roof.data.materials.append(roofmat)

bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' or obj == root: obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=dst, use_selection=True, export_format='GLB', export_apply=True, export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False)
print('EXPORTED', dst)
