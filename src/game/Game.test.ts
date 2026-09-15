import {describe,it,expect,vi} from 'vitest';import {CLEAR_TIMING,Game} from './Game';import {ACTIVE_HEIGHT,CONFIG,SHAPES,SPAWN_BUFFER} from './config';
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
    const pos:[number,number,number]=[Math.floor((CONFIG.width-1-maxX)/2),1,ACTIVE_HEIGHT-1-maxZ];
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

describe('active movement and collision invariants',()=>{
  it('keeps the full empty-board horizontal range for every piece family',()=>{
    SHAPES.forEach(shape=>{
      const game=new Game();game.start();game.shape=shape.map(c=>[...c] as [number,number,number]);game.pos=[0,0,8];
      const maxX=Math.max(...shape.map(c=>c[0]));
      while(game.move([1,0,0])){}
      expect(game.pos[0]).toBe(CONFIG.width-1-maxX);
      const maxY=Math.max(...shape.map(c=>c[1]));
      game.pos=[0,0,8];
      while(game.move([0,1,0])){}
      expect(game.pos[1]).toBe(CONFIG.depth-1-maxY);
    });
  });

  it('allows a piece to travel above a tall central stack at multiple heights',()=>{
    [0,2,4,6,8].forEach(height=>{
      const game=new Game();game.start();game.shape=[[0,0,0]];game.pos=[0,1,11];
      for(let z=0;z<height;z++)game.board.set(`2,1,${z}`,{pos:[2,1,z],kind:0});
      while(game.move([1,0,0])){}
      expect(game.pos[0]).toBe(CONFIG.width-1);
    });
  });

  it('keeps lateral reach unchanged at different active heights above the same board',()=>{
    [6,8,10].forEach(activeZ=>{
      const game=new Game();game.start();game.shape=[[0,0,0]];game.pos=[0,1,activeZ];
      for(let z=0;z<5;z++)game.board.set(`2,1,${z}`,{pos:[2,1,z],kind:0});
      while(game.move([1,0,0])){}
      expect(game.pos[0]).toBe(CONFIG.width-1);
    });
  });

  it('rejects only a true same-Z overlap or a board-boundary violation',()=>{
    const game=new Game();game.start();game.shape=[[0,0,0]];game.pos=[1,1,8];
    game.board.set('2,1,8',{pos:[2,1,8],kind:0});
    expect(game.move([1,0,0])).toBe(false);
    expect(game.pos).toEqual([1,1,8]);
    game.board.clear();game.pos=[0,1,8];
    expect(game.move([-1,0,0])).toBe(false);
    game.pos=[CONFIG.width-1,1,8];
    expect(game.move([1,0,0])).toBe(false);
  });

  it('uses the rotated logical footprint for movement bounds',()=>{
    const axes=['X','Y','Z'] as const;
    axes.forEach(axis=>{
      const game=new Game();game.start();game.shape=SHAPES[0].map(c=>[...c] as [number,number,number]);game.pos=[0,0,8];
      expect(game.rotate(axis)).toBe(true);
      const cells=game.cells();
      expect(cells.every(([x,y,z])=>x>=0&&x<CONFIG.width&&y>=0&&y<CONFIG.depth&&z>=0&&z<CONFIG.height)).toBe(true);
      const maxX=Math.max(...game.shape.map(c=>c[0]));
      while(game.move([1,0,0])){}
      expect(game.pos[0]).toBe(CONFIG.width-1-maxX);
    });
  });

  it('preserves hard-drop landing after lateral movement',()=>{
    const game=new Game();game.start();game.shape=[[0,0,0]];game.pos=[0,1,8];
    game.board.set('2,1,0',{pos:[2,1,0],kind:0});
    expect(game.move([1,0,0])).toBe(true);expect(game.move([1,0,0])).toBe(true);
    game.drop();
    expect(game.board.get('2,1,1')?.pos).toEqual([2,1,1]);
    expect(game.phase).toBe('playing');
  });
});

describe('hidden spawn maneuver buffer',()=>{
  it('spawns above a tall visible stack when buffer space remains',()=>{
    const game=new Game();game.start();
    for(let z=0;z<CONFIG.height-1;z++)game.board.set(`2,1,${z}`,{pos:[2,1,z],kind:0});
    game.nextKind=0;
    (game as unknown as {spawn:()=>void}).spawn();
    expect(game.phase).toBe('playing');
    expect(game.cells().some(([, , z])=>z>=CONFIG.height)).toBe(true);
    expect(Math.min(...game.cells().map(([, , z])=>z))).toBe(ACTIVE_HEIGHT-1-3);
  });

  it('allows movement across the full footprint while a piece is in the buffer',()=>{
    const game=new Game();game.start();game.shape=[[0,0,0]];game.pos=[0,1,ACTIVE_HEIGHT-1];
    while(game.move([1,0,0])){}
    expect(game.pos[0]).toBe(CONFIG.width-1);
  });

  it('keeps the ghost inside the visible build volume after a buffer drop',()=>{
    const game=new Game();game.start();game.shape=[[0,0,0]];game.pos=[2,1,ACTIVE_HEIGHT-1];
    game.board.set('2,1,0',{pos:[2,1,0],kind:0});
    expect(game.ghost()).toEqual([[2,1,1]]);
    game.drop();
    expect(game.board.get('2,1,1')?.pos).toEqual([2,1,1]);
    expect(game.score).toBe(20);
  });

  it('allows X/Y/Z rotation while the active piece occupies buffer rows',()=>{
    (['X','Y','Z'] as const).forEach(axis=>{
      const game=new Game();game.start();game.shape=[[0,0,0],[0,0,1],[0,0,2],[0,0,3]];game.pos=[0,0,11];
      expect(game.cells().some(([, , z])=>z>=CONFIG.height)).toBe(true);
      expect(game.rotate(axis)).toBe(true);
      expect(game.cells().every(([x,y,z])=>x>=0&&x<CONFIG.width&&y>=0&&y<CONFIG.depth&&z>=0&&z<ACTIVE_HEIGHT)).toBe(true);
    });
  });

  it('locks pieces at or below the visible ceiling but games over above it',()=>{
    const valid=new Game();valid.start();valid.shape=[[0,0,0]];valid.pos=[0,0,CONFIG.height-1];valid.board.set('0,0,10',{pos:[0,0,10],kind:0});valid.drop();
    expect(valid.phase).toBe('playing');expect(valid.board.get('0,0,11')?.pos).toEqual([0,0,11]);
    const blocked=new Game();blocked.start();blocked.shape=[[0,0,0],[0,0,1]];blocked.pos=[2,1,CONFIG.height];
    blocked.board.set('2,1,11',{pos:[2,1,11],kind:0});blocked.drop();
    expect(blocked.phase).toBe('gameover');expect(blocked.board.has('2,1,12')).toBe(false);
  });

  it('keeps the clear plane at the original 5 by 4 size',()=>{
    expect(CONFIG.width*CONFIG.depth).toBe(20);
  });
});
