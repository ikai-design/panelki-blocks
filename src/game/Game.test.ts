import {describe,it,expect,vi} from 'vitest';import {CLEAR_TIMING,Game} from './Game';import {CONFIG,SHAPES} from './config';
describe('Panelki rules',()=>{it('starts and drops',()=>{const g=new Game();g.start();g.drop();expect(g.board.size).toBe(4);expect(g.score).toBeGreaterThan(0)});it('pauses and restarts',()=>{const g=new Game();g.start();g.togglePause();const a=JSON.stringify(g.pos);g.tick();expect(JSON.stringify(g.pos)).toBe(a);g.restart();expect(g.board.size).toBe(0)});it('keeps cells inside the well',()=>{for(let i=0;i<50;i++){const g=new Game();g.start();for(let n=0;n<40&&!['gameover'].includes(g.phase);n++){g.rotate('X');g.move([n%3-1,0,0]);g.drop()}expect([...g.board.values()].every(c=>c.pos.every((v,j)=>v>=0&&v<[CONFIG.width,CONFIG.depth,CONFIG.height][j]))).toBe(true)}})});

function fillLayer(game:Game,z:number,count:number){
  for(let i=0;i<count;i++){
    const pos:[number,number,number]=[i%CONFIG.width,Math.floor(i/CONFIG.width),z];
    game.board.set(pos.join(','),{pos,kind:0});
  }
}

describe('first clear loop',()=>{
  it('keeps ordinary placements immediate and preserves spawn-collision game over',()=>{
    const ordinary=new Game();ordinary.start();ordinary.drop();
    expect(ordinary.phase).toBe('playing');expect(ordinary.snapshot().active).toHaveLength(4);
    expect(ordinary.snapshot().clearEvent).toBeNull();
    const game=new Game();game.start();
    const shape=SHAPES[game.nextKind], maxX=Math.max(...shape.map(c=>c[0])),maxZ=Math.max(...shape.map(c=>c[2]));
    const pos:[number,number,number]=[Math.floor((CONFIG.width-1-maxX)/2),1,CONFIG.height-1-maxZ];
    game.board.set(pos.join(','),{pos,kind:0});game.drop();
    expect(game.phase).toBe('gameover');
    expect(game.snapshot().active).toHaveLength(0);
    game.restart();expect(game.phase).toBe('playing');expect(game.board.size).toBe(0);
  });
  it('cues only 16+ occupied cells and prioritizes the most complete layer',()=>{
    const game=new Game();game.start();fillLayer(game,0,15);
    expect(game.snapshot().nearLayer).toBeNull();
    fillLayer(game,0,16);game.move([1,0,0]);
    expect(game.snapshot().nearLayer?.holes).toHaveLength(4);
    fillLayer(game,1,19);game.move([-1,0,0]);
    expect(game.snapshot().nearLayer).toMatchObject({z:1,filled:19});
  });

  it('holds a full plane, ignores inputs, collapses, scores, and only then spawns',()=>{
    vi.useFakeTimers();
    try{
      const game=new Game();game.start();fillLayer(game,0,19);
      game.board.set('4,3,2',{pos:[4,3,2],kind:1});
      game.shape=[[0,0,0]];game.pos=[4,3,0];game.drop();
      expect(game.phase).toBe('clearing');
      expect(game.board.size).toBe(21);
      expect(game.snapshot().active).toHaveLength(0);
      expect(game.snapshot().clearEvent?.stage).toBe('anticipation');
      expect(game.snapshot().clearReward).toMatchObject({planes:1,points:100});
      expect(game.move([1,0,0])).toBe(false);
      expect(game.rotate('X')).toBe(false);
      const scoreBefore=game.score;game.drop();game.tick();game.togglePause();
      expect(game.score).toBe(scoreBefore);
      vi.advanceTimersByTime(CLEAR_TIMING.anticipation);
      expect(game.snapshot().clearEvent?.stage).toBe('removal');
      expect(game.board.size).toBe(21);
      vi.advanceTimersByTime(CLEAR_TIMING.removal);
      expect(game.snapshot().clearEvent?.stage).toBe('collapse');
      expect(game.board.size).toBe(1);
      expect(game.board.get('4,3,1')?.pos).toEqual([4,3,1]);
      expect(game.snapshot().clearEvent?.collapseFrom['4,3,1']).toBe(2);
      expect(game.score).toBe(scoreBefore+100);
      expect(game.layers).toBe(1);
      vi.advanceTimersByTime(CLEAR_TIMING.collapse);
      expect(game.phase).toBe('playing');
      expect(game.snapshot().active).toHaveLength(4);
      vi.advanceTimersByTime(CLEAR_TIMING.reward-CLEAR_TIMING.anticipation-CLEAR_TIMING.removal-CLEAR_TIMING.collapse);
      expect(game.snapshot().clearReward).toBeNull();
    }finally{vi.useRealTimers()}
  });

  it('keeps quadratic two-layer scoring and cancels a pending clear on restart',()=>{
    vi.useFakeTimers();
    try{
      const game=new Game();game.start();fillLayer(game,0,20);fillLayer(game,1,19);
      game.shape=[[0,0,0]];game.pos=[4,3,1];game.drop();
      expect(game.snapshot().clearReward).toMatchObject({planes:2,points:400});
      vi.advanceTimersByTime(CLEAR_TIMING.anticipation+CLEAR_TIMING.removal);
      expect(game.layers).toBe(2);expect(game.score).toBe(400);
      expect(game.board.size).toBe(0);
      game.restart();vi.runAllTimers();
      expect(game.phase).toBe('playing');expect(game.board.size).toBe(0);
      expect(game.score).toBe(0);expect(game.snapshot().clearEvent).toBeNull();
      expect(game.snapshot().clearReward).toBeNull();
    }finally{vi.useRealTimers()}
  });
});
