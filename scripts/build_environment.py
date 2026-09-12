"""Build and export a dead tree and a worn Eastern European playground."""
import bpy, math, os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out=os.path.join(root,'public','assets','environment');os.makedirs(out,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def mat(name,color,metal=0,rough=.8):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.metallic=metal;m.roughness=rough;return m
bark=mat('Charred bark',(.075,.055,.038));wood=mat('Weathered wood',(.25,.16,.08));rust=mat('Flaking rust',(.35,.12,.045),.65);blue=mat('Faded blue paint',(.10,.24,.29),.5);sand=mat('Dirty sand',(.38,.30,.18));rubber=mat('Old black rubber',(.025,.025,.022));

def cyl(name,a,b,r,material,verts=7):
    mid=(Vector(a)+Vector(b))/2;d=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r*1.12,radius2=r*.72,depth=d.length,location=mid)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(material);return o
def box(name,loc,scale,material,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def export_selected(name,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(out,name+'.glb'),use_selection=True,export_format='GLB',export_apply=True,export_yup=True,export_materials='EXPORT',export_cameras=False,export_lights=False)

# Crooked, nearly dead tree with a few blackened branch forks.
tree=[]
segments=[((0,0,0),(0.08,0,1.8),.23),((.08,0,1.8),(-.15,.02,3.35),.18),((-.15,.02,3.35),(.08,-.04,4.7),.12),
          ((-.03,0,2.25),(-1.0,.05,3.15),.105),((-1,.05,3.15),(-1.55,.02,3.72),.07),((-1,.05,3.15),(-1.55,.12,2.88),.055),
          ((-.1,0,3.05),(.9,.08,3.75),.09),((.9,.08,3.75),(1.42,.04,4.35),.055),((.9,.08,3.75),(1.45,.18,3.55),.05),
          ((.02,0,4.05),(-.62,-.05,4.75),.065),((-.62,-.05,4.75),(-.83,.1,5.25),.04)]
for i,(a,b,r) in enumerate(segments):tree.append(cyl('Dead_branch_%02d'%i,a,b,r,bark))
for i,(x,y) in enumerate([(-.16,-.1),(.18,.03),(0,.2)]):tree.append(cyl('Root_%02d'%i,(0,0,.12),(x*3,y*3,0),.1,bark))
export_selected('dead-tree',tree)

# Playground: sandbox, climbing frame, slide, swing and discarded tire.
play=[]
for x,y,sx,sy in [(0,-1.45,1.8,.08),(0,1.45,1.8,.08),(-1.72,0,.08,1.45),(1.72,0,.08,1.45)]:play.append(box('Sandbox_edge',(x,y,.12),(sx,sy,.12),wood))
play.append(box('Dirty_sand',(0,0,.02),(1.62,1.34,.035),sand))
# Climbing bars / tiny jungle gym.
for x in [-1.05,-.35,.35,1.05]:
    play.append(cyl('Climb_post',(x,-.7,.15),(x,-.7,1.65),.035,blue,8))
for z in [.45,.85,1.25,1.65]:play.append(cyl('Climb_rail',(-1.05,-.7,z),(1.05,-.7,z),.025,rust,8))
# Slide platform and slanted chute.
for x in [-.75,.75]:play.append(cyl('Slide_leg',(x,.4,.1),(x,.4,1.25),.045,rust,8))
play.append(box('Slide_platform',(0,.4,1.22),(.82,.48,.07),wood))
play.append(box('Slide_chute',(0,1.22,.69),(.55,1.05,.045),blue,(-.48,0,0)))
for x in [-.56,.56]:play.append(cyl('Slide_side',(x,.58,1.25),(x,1.73,.12),.03,rust,8))
# Swing frame and seat.
for x in [-1.25,1.25]:
    play.append(cyl('Swing_frame',(x,-2.0,.05),(x*.72,-2,2.25),.055,rust,8))
play.append(cyl('Swing_top',(-.9,-2,2.25),(.9,-2,2.25),.055,rust,8))
for x in [-.27,.27]:play.append(cyl('Swing_chain',(x,-2,2.2),(x,-2,.72),.012,rust,7))
play.append(box('Swing_seat',(0,-2,.65),(.42,.18,.045),wood))
# Half-buried tire.
bpy.ops.mesh.primitive_torus_add(major_radius=.42,minor_radius=.105,major_segments=12,minor_segments=6,location=(2.15,.7,.25),rotation=(math.pi/2,0,.22));t=bpy.context.object;t.name='Half_buried_tire';t.data.materials.append(rubber);play.append(t)
export_selected('playground',play)
print('EXPORTED environment:',out)
