"""Export the five linked gameplay modules as small standalone GLBs."""
import bpy,os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out=os.path.join(root,'public','assets','buildings');os.makedirs(out,exist_ok=True)
names=['khrushchovka','yugoslav-slab','courtyard','five-story','brutalist']
for i,name in enumerate(names):
    bpy.ops.object.select_all(action='DESELECT');src=bpy.data.objects[f'Module_{i}'];src.hide_set(False);src.hide_render=False;src.select_set(True);bpy.context.view_layer.objects.active=src
    bpy.ops.export_scene.gltf(filepath=os.path.join(out,name+'.glb'),use_selection=True,export_format='GLB',export_apply=True,export_yup=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
    src.hide_set(True);src.hide_render=True
print('EXPORTED',len(names),'building modules to',out)
