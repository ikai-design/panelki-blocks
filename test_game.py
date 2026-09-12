import unittest
from game_core import Game, CONFIG, SHAPES

class RulesTests(unittest.TestCase):
    def test_spawn_all_types(self):
        for k in range(5):
            g=Game(0); g.next_kind=k; g.spawn()
            self.assertTrue(g.valid()); self.assertEqual(len(set(g.cells())),4)
    def test_movement_walls_and_collision(self):
        g=Game(1); g.shape=SHAPES[2]; g.pos=(1,1,3)
        self.assertTrue(g.move(x=-1)); self.assertFalse(g.move(x=-1))
        g.board[(2,1,3)]=0; self.assertFalse(g.move(x=1))
        self.assertFalse(g.move(y=2)); self.assertFalse(g.move(z=-4))
    def test_rotation_all_axes_four_turns(self):
        for shape in SHAPES:
            for axis in 'XYZ':
                g=Game(0); g.shape=shape; g.pos=(0,0,4)
                # A 4-long tower cannot fit along the 3-deep axis.
                if shape==SHAPES[0] and axis=='X':
                    self.assertFalse(g.rotate(axis)); continue
                for _ in range(4): self.assertTrue(g.rotate(axis))
                self.assertEqual(set(g.shape),set(shape)); self.assertTrue(g.valid())
    def test_rotation_obstruction(self):
        g=Game(0); g.shape=SHAPES[0]; g.pos=(0,0,0)
        g.board={(x,y,z):1 for x in range(4) for y in range(3) for z in range(5) if (x,y,z) not in g.cells()}
        before=g.cells(); self.assertFalse(g.rotate('Y')); self.assertEqual(g.cells(),before)
    def test_ghost_drop_lock(self):
        g=Game(0); ghost=set(g.ghost()); self.assertEqual(min(z for x,y,z in ghost),0)
        g.drop(); self.assertTrue(ghost.issubset(g.board)); self.assertGreater(g.score,0)
    def test_layer_compaction_score_speed(self):
        g=Game(0); initial=g.interval
        g.board={(x,y,z):0 for x in range(4) for y in range(3) for z in range(4)}
        g.board[(1,1,5)]=2
        self.assertEqual(g.clear_layers(),4); self.assertEqual(g.board,{(1,1,1):2})
        self.assertEqual(g.score,1600); self.assertEqual(g.level,2); self.assertLess(g.interval,initial)
    def test_tick_locks_and_clears(self):
        g=Game(0); g.shape=SHAPES[2]; g.pos=(0,0,0); g.kind=2
        g.board={(x,y,0):0 for x in range(4) for y in range(3) if (x,y,0) not in g.cells()}
        g.tick(); self.assertEqual(g.layers,1); self.assertEqual(g.score,100); self.assertFalse(g.board)
    def test_pause_gameover_restart(self):
        g=Game(0); before=g.cells(); g.paused=True
        g.tick(); g.drop(); g.move(x=1); g.rotate('Y'); self.assertEqual(before,g.cells())
        g.paused=False; g.board={(x,y,z):0 for x in range(4) for y in range(3) for z in range(12)}
        g.spawn(); self.assertTrue(g.over); g.tick(); self.assertEqual(len(g.board),144)
        g.restart(); self.assertFalse(g.over); self.assertFalse(g.paused); self.assertFalse(g.board)
        self.assertEqual((g.score,g.layers,g.level),(0,0,1)); self.assertTrue(g.valid())
    def test_random_play_invariants(self):
        for seed in range(20):
            g=Game(seed)
            for _ in range(100):
                if g.over: break
                g.rotate(g.rng.choice('XYZ')); g.move(x=g.rng.choice([-1,0,1])); g.move(y=g.rng.choice([-1,0,1]))
                self.assertTrue(g.valid()); g.drop()
                self.assertTrue(all(0<=x<4 and 0<=y<3 and 0<=z<12 for x,y,z in g.board))

if __name__=='__main__': unittest.main(verbosity=2)
