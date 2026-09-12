"""Pure Python rules; coordinates are integer (x, depth, height) cells."""
import random

CONFIG = {
    'width': 4, 'depth': 3, 'height': 12,
    'fall_seconds': 1.1, 'speed_factor': .82, 'minimum_seconds': .12,
    'layers_per_level': 4, 'layer_points': 100,
    'colors': [( .64,.69,.62,1), (.40,.64,.57,1), (.78,.65,.39,1),
               (.69,.43,.43,1), (.39,.53,.65,1)],
}
NAMES = ['Khrushchovka tower', 'Yugoslav slab', 'Courtyard block',
         'Five-story prefab', 'Brutalist high-rise']
SHAPES = [((0,0,0),(0,0,1),(0,0,2),(0,0,3)),
          ((0,0,0),(1,0,0),(2,0,0),(2,0,1)),
          ((0,0,0),(1,0,0),(0,1,0),(1,1,0)),
          ((0,0,0),(1,0,0),(1,0,1),(2,0,1)),
          ((0,0,0),(1,0,0),(2,0,0),(1,0,1))]

class Game:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.restart()

    def restart(self):
        self.board = {}
        self.score = self.layers = 0
        self.over = self.paused = False
        self.bag = []
        self.next_kind = self.pick()
        self.spawn()

    @property
    def level(self): return 1 + self.layers // CONFIG['layers_per_level']

    @property
    def interval(self):
        return max(CONFIG['minimum_seconds'], CONFIG['fall_seconds'] * CONFIG['speed_factor'] ** (self.level-1))

    def pick(self):
        if not self.bag:
            self.bag = list(range(len(SHAPES)))
            self.rng.shuffle(self.bag)
        return self.bag.pop()

    def cells(self, shape=None, pos=None):
        return [tuple(a+b for a,b in zip(c, self.pos if pos is None else pos))
                for c in (self.shape if shape is None else shape)]

    def valid(self, shape=None, pos=None):
        return all(0 <= x < CONFIG['width'] and 0 <= y < CONFIG['depth']
                   and 0 <= z < CONFIG['height'] and (x,y,z) not in self.board
                   for x,y,z in self.cells(shape, pos))

    def spawn(self):
        self.kind = self.next_kind
        self.next_kind = self.pick()
        self.shape = SHAPES[self.kind]
        self.pos = ((CONFIG['width'] - 1 - max(c[0] for c in self.shape)) // 2,
                    1, CONFIG['height'] - 1 - max(c[2] for c in self.shape))
        self.over = not self.valid()

    def move(self, x=0, y=0, z=0):
        if self.over or self.paused: return False
        p = tuple(a+b for a,b in zip(self.pos,(x,y,z)))
        if not self.valid(pos=p): return False
        self.pos = p
        return True

    def rotate(self, axis):
        if self.over or self.paused: return False
        transforms = {'X': lambda x,y,z:(x,-z,y), 'Y': lambda x,y,z:(z,y,-x),
                      'Z': lambda x,y,z:(-y,x,z)}
        s = [transforms[axis](*c) for c in self.shape]
        lo = [min(c[i] for c in s) for i in range(3)]
        s = [tuple(c[i]-lo[i] for i in range(3)) for c in s]
        # Small wall kicks, but no upward kicks or passage through locked cells.
        for dx,dy,dz in [(0,0,0),(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(-2,0,0),(0,-2,0)]:
            p = (self.pos[0]+dx,self.pos[1]+dy,self.pos[2]+dz)
            if self.valid(s,p):
                self.shape, self.pos = s,p
                return True
        return False

    def ghost(self):
        p = self.pos
        while self.valid(pos=(p[0],p[1],p[2]-1)):
            p = (p[0],p[1],p[2]-1)
        return self.cells(pos=p)

    def clear_layers(self):
        full = [z for z in range(CONFIG['height']) if all((x,y,z) in self.board
                for x in range(CONFIG['width']) for y in range(CONFIG['depth']))]
        self.board = {(x,y,z-sum(f<z for f in full)):k
                      for (x,y,z),k in self.board.items() if z not in full}
        self.score += CONFIG['layer_points'] * len(full)**2 * self.level
        self.layers += len(full)
        return len(full)

    def lock(self):
        for cell in self.cells(): self.board[cell] = self.kind
        self.clear_layers()
        self.spawn()

    def tick(self):
        if self.over or self.paused: return
        if not self.move(z=-1): self.lock()

    def drop(self):
        if self.over or self.paused: return
        while self.move(z=-1): self.score += 2
        self.lock()
