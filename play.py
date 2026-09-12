"""Run this embedded text in Blender, then hover the 3D viewport to play."""
import bpy, blf, time
from mathutils import Vector

# Loading the rules from the blend makes the game portable.
rules = {'__name__': 'panelki_rules'}
exec(bpy.data.texts['game_core.py'].as_string(), rules)
Game, CONFIG, NAMES = rules['Game'], rules['CONFIG'], rules['NAMES']

def redraw(game):
    col = bpy.data.collections['Gameplay']
    for ob in list(col.objects): bpy.data.objects.remove(ob, do_unlink=True)
    def cell(coords, kind, ghost=False):
        source = bpy.data.objects['GhostTemplate' if ghost else 'Module_%d' % kind]
        ob = bpy.data.objects.new(('Landing_' if ghost else 'Apartment_') + str(coords), source.data)
        col.objects.link(ob)
        ob.location = coords
        if ghost: ob.display_type = 'WIRE'
    for c,k in game.board.items(): cell(c,k)
    if not game.over:
        for c in game.ghost(): cell(c,game.kind,True)
        for c in game.cells(): cell(c,game.kind)

class PANELKI_OT_play(bpy.types.Operator):
    bl_idname = 'view3d.panelki_play'
    bl_label = 'Play Panelki Blocks'
    bl_description = 'Start the falling apartment puzzle; Esc exits'

    def hud(self):
        g = self.game
        lines = [('PANELKI / BLOCKS', 25, (1,.83,.48,1)),
                 ('A little concrete. A lot of neighbours.',14,(.8,.84,.83,1)),
                 ('%06d   /   LEVEL %02d   /   LAYERS %02d' % (g.score,g.level,g.layers),18,(1,1,1,1)),
                 ('Falling: '+NAMES[g.kind],14,(.82,.88,.84,1)),
                 ('Next: '+NAMES[g.next_kind],14,(.82,.88,.84,1)),
                 ('Arrows: move on ground   |   X / Y / Z: rotate',14,(.85,.88,.88,1)),
                 ('Space: drop   S: down   P: pause   R: restart   Esc: exit',14,(.85,.88,.88,1))]
        y = bpy.context.region.height - 44
        for text,size,color in lines:
            blf.size(0,size); blf.color(0,*color); blf.position(0,24,y,0); blf.draw(0,text)
            y -= 29
        if g.over or g.paused:
            blf.size(0,32); blf.color(0,1,.65,.4,1); blf.position(0,24,y-25,0)
            blf.draw(0,'NO VACANCIES — R TO REBUILD' if g.over else 'TEA BREAK — P TO RESUME')

    def execute(self, context):
        if bpy.app.driver_namespace.get('panelki_running'):
            self.report({'WARNING'}, 'Game already running. Esc in viewport first.')
            return {'CANCELLED'}
        self.area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'),None)
        if self.area is None:
            self.report({'ERROR'}, 'Open a 3D Viewport first.')
            return {'CANCELLED'}
        self.area.spaces.active.region_3d.view_perspective = 'CAMERA'
        self.game = Game()
        self.last = time.monotonic()
        redraw(self.game)
        self.handle = bpy.types.SpaceView3D.draw_handler_add(self.hud,(), 'WINDOW','POST_PIXEL')
        self.timer = context.window_manager.event_timer_add(.05,window=context.window)
        context.window_manager.modal_handler_add(self)
        bpy.app.driver_namespace['panelki_running'] = True
        bpy.app.driver_namespace['panelki_operator'] = self
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        dirty = False
        if event.type == 'ESC':
            context.window_manager.event_timer_remove(self.timer)
            bpy.types.SpaceView3D.draw_handler_remove(self.handle,'WINDOW')
            bpy.app.driver_namespace['panelki_running'] = False
            bpy.app.driver_namespace.pop('panelki_operator',None)
            self.area.tag_redraw()
            return {'CANCELLED'}
        if event.type == 'TIMER':
            now = time.monotonic()
            if now-self.last >= self.game.interval:
                self.game.tick(); self.last = now; dirty = True
        elif event.value == 'PRESS':
            g = self.game
            if event.type == 'R': g.restart(); self.last = time.monotonic()
            elif event.type == 'P': g.paused = not g.paused; self.last = time.monotonic()
            elif event.type in ('X','Y','Z'): g.rotate(event.type)
            elif event.type == 'LEFT_ARROW': g.move(x=-1)
            elif event.type == 'RIGHT_ARROW': g.move(x=1)
            elif event.type == 'UP_ARROW': g.move(y=1)
            elif event.type == 'DOWN_ARROW': g.move(y=-1)
            elif event.type == 'S': g.tick(); self.last = time.monotonic()
            elif event.type == 'SPACE': g.drop(); self.last = time.monotonic()
            else: return {'PASS_THROUGH'}
            dirty = True
        else: return {'PASS_THROUGH'}
        if dirty: redraw(self.game)
        self.area.tag_redraw()
        return {'RUNNING_MODAL'}

if not bpy.app.driver_namespace.get('panelki_running'):
    old = getattr(bpy.types,'PANELKI_OT_play',None)
    if old: bpy.utils.unregister_class(old)
    bpy.utils.register_class(PANELKI_OT_play)
    bpy.ops.view3d.panelki_play()
