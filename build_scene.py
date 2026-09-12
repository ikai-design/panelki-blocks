"""Build the complete scene with reusable, merged apartment module meshes."""
import bpy, math, os, sys
from mathutils import Vector
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,ROOT)
from game_core import CONFIG, Game
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
cols = {}
for name in ['Gameplay','Pieces','Environment','UI','Lights','Camera']:
    cols[name] = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(cols[name])

def mat(name,color,emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=color; m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=color
    p.inputs['Roughness'].default_value=.8
    if emission:
        p.inputs['Emission Color'].default_value=color; p.inputs['Emission Strength'].default_value=emission
    return m
palette=[mat('Facade / '+n,c) for n,c in zip(['sage concrete','mint','ochre','rose','blue'],CONFIG['colors'])]
concrete=mat('Precast edges',(.3,.34,.34,1))
glass=mat('Evening blue glass',(.065,.15,.19,1))
warm=mat('Someone is home',(.98,.64,.23,1),.45)
rust=mat('Balcony rust',(.37,.17,.1,1))
cream=mat('Curtains and laundry',(.83,.79,.63,1))
green=mat('Balcony plants',(.19,.34,.17,1))
ground=mat('Courtyard asphalt',(.095,.13,.15,1))
line=mat('Grid brass',(.65,.46,.22,1),.15)
allm=palette+[concrete,glass,warm,rust,cream,green,ground,line]

class Mesh:
    def __init__(self): self.v=[]; self.f=[]; self.mi=[]
    def box(self,p,s,m):
        n=len(self.v)
        self.v += [(p[0]+a*s[0]/2,p[1]+b*s[1]/2,p[2]+c*s[2]/2)
                   for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
        self.f += [tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]]
        self.mi += [allm.index(m)]*6
    def object(self,name,col):
        mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(self.v,[],self.f)
        for m in allm: mesh.materials.append(m)
        for p,i in zip(mesh.polygons,self.mi): p.material_index=i
        ob=bpy.data.objects.new(name,mesh); cols[col].objects.link(ob); return ob

for k in range(5):
    m=Mesh(); m.box((0,0,0),(.9,.9,.9),palette[k])
    # Repeated prefab seams and roof caps; all details remain inside one cell.
    for z in [-.44,-.15,.15,.44]: m.box((0,0,z),(.94,.94,.025),concrete)
    for side in [-1,1]:
        for row,z in enumerate([-.29,0,.29]):
            for col,x in enumerate([-.29,0,.29]):
                lit=(row+col+k)%4==0
                m.box((x,side*.455,z),(.14,.015,.16),warm if lit else glass)
                m.box((side*.455,x,z),(.015,.14,.16),warm if lit else glass)
                if (col+k)%3==0:
                    m.box((x,side*.467,z),(.025,.016,.15),cream)
            if k in [1,3]: # broad balcony bands for slab/prefab styles
                m.box((0,side*.475,z-.09),(.83,.04,.035),cream)
                m.box((0,side*.489,z-.035),(.83,.014,.08),rust)
            elif k==4:
                for x in [-.4,0,.4]: m.box((x,side*.47,0),(.06,.045,.84),concrete)
        # Compact AC, planter, door and hanging laundry modules.
        m.box((.27,side*.479,-.12),(.12,.04,.07),cream)
        m.box((-.27,side*.48,.17),(.14,.035,.045),rust)
        m.box((-.27,side*.483,.21),(.11,.03,.045),green)
        m.box((0,side*.46,-.34),(.10,.018,.17),rust)
        if k==3: m.box((.12,side*.49,.19),(.11,.015,.12),cream)
    if k==2: # inset rooftop courtyard / planted terrace
        m.box((0,0,.455),(.57,.57,.015),ground)
        for x in [-.32,.32]: m.box((x,0,.465),(.08,.7,.04),green)
    else:
        m.box((.18,.15,.466),(.27,.22,.045),concrete)
        m.box((-.2,.1,.473),(.10,.12,.035),rust)
        # Angular low-poly satellite dish silhouette.
        m.box((-.25,-.15,.463),(.03,.03,.06),concrete)
        m.box((-.25,-.15,.487),(.12,.08,.02),cream)
    ob=m.object('Module_%d'%k,'Pieces'); ob.hide_render=True; ob.hide_set(True)

m=Mesh(); m.box((0,0,0),(.97,.97,.97),warm)
ghost=m.object('GhostTemplate','Pieces'); ghost.hide_render=True; ghost.hide_set(True)
m=Mesh(); m.box((1.5,1,-.65),(6,5,.3),concrete); m.box((1.5,1,-.485),(4,3,.025),ground)
for x in range(5): m.box((x-.5,1,-.46),(.017,3,.017),line)
for y in range(4): m.box((1.5,y-.5,-.46),(4,.017,.017),line)
for x in [-.53,3.53]:
    for y in [-.53,2.53]: m.box((x,y,5.45),(.026,.026,12),concrete)
for z in [2.5,5.5,8.5,11.5]:
    m.box((1.5,2.53,z),(4.1,.022,.022),line)
m.object('Construction grid / 4 x 3 x 12','Environment')
m=Mesh(); m.box((1.5,1,-1),(200,200,.2),ground); m.object('Endless courtyard','Environment')
# A quiet miniature neighbourhood around the well.
for i,(x,y,h) in enumerate([(-4,5,3),(-2,7,4),(3,8,3),(6,6,5),(8,3,2)]):
    for z in range(h):
        ob=bpy.data.objects.new('Neighbour_%d_%d'%(i,z),bpy.data.objects['Module_%d'%(i%5)].data)
        cols['Environment'].objects.link(ob); ob.location=(x,y,z-.35)
        ob.scale=(1.4,1.4,1)

def label(name,text,loc,size):
    c=bpy.data.curves.new(name,'FONT'); c.body=text; c.size=size; c.extrude=.002
    c.materials.append(cream); o=bpy.data.objects.new(name,c); cols['UI'].objects.link(o)
    o.location=loc; o.rotation_euler=(math.pi/2,0,0)
label('Site sign','P A N E L K I  /  B L O C K S',(-1.2,-1.53,-.55),.24)

camdata=bpy.data.cameras.new('Architect camera'); cam=bpy.data.objects.new('Camera',camdata)
cols['Camera'].objects.link(cam); cam.location=(19,-27,21)
cam.rotation_euler=(Vector((1.5,1,5.1))-cam.location).to_track_quat('-Z','Y').to_euler()
camdata.type='ORTHO'; camdata.ortho_scale=21; bpy.context.scene.camera=cam
for name,loc,power,color,size in [('Evening key',(0,-8,17),2300,(1,.73,.47),9),('Sky fill',(-8,2,12),1800,(.48,.68,1),10),('Sunset rim',(5,8,13),2600,(1,.48,.25),7)]:
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); cols['Lights'].objects.link(o); o.location=loc
    o.rotation_euler=(Vector((1,1,4))-o.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.17,.23,.29,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
# Very light atmospheric volume for the beauty render.
vol=scene.world.node_tree.nodes.new('ShaderNodeVolumeScatter'); vol.inputs['Density'].default_value=.001
scene.world.node_tree.links.new(vol.outputs[0],scene.world.node_tree.nodes['World Output'].inputs['Volume'])
scene.render.resolution_x=1200; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
for name in ['game_core.py','play.py']:
    t=bpy.data.texts.load(os.path.join(ROOT,name)); t.use_fake_user=True
readme=bpy.data.texts.new('START HERE'); readme.write('PANELKI BLOCKS\nSwitch any panel to Text Editor, select play.py, click Run Script.\nHover the 3D viewport. Arrows move; X/Y/Z rotate; Space drops; S steps down.\nP pause, R restart, Esc exit. Use Layout workspace for the full view.\nSound placeholders: drop, layer clear, game over (currently silent).\n')
# Saved board is a preview; starting the game resets it.
for x,y,z,k in [(0,0,0,0),(1,0,0,0),(2,1,0,1),(3,1,0,1),(3,2,0,2),(3,2,1,2),(0,2,0,3),(1,2,0,3),(1,1,6,4),(2,1,6,4),(3,1,6,4),(2,1,7,4)]:
    o=bpy.data.objects.new('Preview apartment',bpy.data.objects['Module_%d'%k].data)
    cols['Gameplay'].objects.link(o); o.location=(x,y,z)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active; s.region_3d.view_perspective='CAMERA'; s.region_3d.view_camera_zoom=0
            s.overlay.show_overlays=False; s.show_region_ui=False
            s.shading.type='SOLID'; s.shading.light='STUDIO'; s.shading.color_type='MATERIAL'
            s.shading.show_shadows=True; s.shading.show_cavity=True; s.shading.cavity_type='BOTH'
            s.shading.background_type='WORLD'
        elif area.type=='TEXT_EDITOR': area.spaces.active.text=bpy.data.texts['play.py']
scene['sound_placeholders']='drop.wav, layer_clear.wav, game_over.wav (silent prototype)'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Panelki Blocks.blend'))
scene.render.filepath=os.path.join(ROOT,'preview.png')
if '--render-preview' in sys.argv: bpy.ops.render.render(write_still=True)
