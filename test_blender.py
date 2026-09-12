"""Exercise the actual Blender operator, scene updates and keyboard dispatch."""
import bpy, os
from types import SimpleNamespace
root=os.path.dirname(os.path.abspath(__file__))
# Read the external script so this also checks the newest version before rebuild.
with open(os.path.join(root,'play.py')) as f: exec(compile(f.read(),'play.py','exec'))
op=bpy.app.driver_namespace['panelki_operator']
def key(name): return op.modal(bpy.context,SimpleNamespace(type=name,value='PRESS'))
assert len(bpy.data.collections['Gameplay'].objects)==8
key('P'); assert op.game.paused
old=op.game.cells(); key('SPACE'); assert op.game.cells()==old
key('P'); assert not op.game.paused
key('X'); key('Y'); key('Z'); assert op.game.valid()
key('LEFT_ARROW'); key('RIGHT_ARROW'); key('UP_ARROW'); key('DOWN_ARROW'); assert op.game.valid()
key('SPACE'); assert len(op.game.board)==4
assert len(bpy.data.collections['Gameplay'].objects)==12
key('R'); assert len(op.game.board)==0 and op.game.score==0
op.game.shape=rules['SHAPES'][2]; op.game.pos=(0,0,0)
op.game.board={(x,y,0):0 for x in range(4) for y in range(3) if (x,y,0) not in op.game.cells()}
key('S'); assert op.game.layers==1 and op.game.score==100
op.game.board={(x,y,z):0 for x in range(4) for y in range(3) for z in range(12)}
op.game.spawn(); key('X'); assert op.game.over
assert len(bpy.data.collections['Gameplay'].objects)==144
key('R'); assert not op.game.over
key('ESC'); assert not bpy.app.driver_namespace['panelki_running']
assert set(['Gameplay','Pieces','Environment','UI','Lights','Camera']).issubset(bpy.data.collections.keys())
print('BLENDER INTEGRATION: PASS — launch, input, pause, drop, restart, clear, game over, exit, linked meshes')
