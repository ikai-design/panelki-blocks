import {ACTIVE_HEIGHT,CONFIG,SHAPES} from './config';
import type {Axis,Cell,ClearEvent,ClearReward,NearLayer,Phase,Snapshot,Vec3} from './types';
const key=([x,y,z]:Vec3)=>`${x},${y},${z}`;
export const CLEAR_TIMING={anticipation:130,removal:250,collapse:190,reward:850} as const;
export class Game {
  board=new Map<string,Cell>(); score=0; layers=0; phase:Phase='title'; bag:number[]=[];
  kind=0; nextKind=0; shape:Vec3[]=SHAPES[0]; pos:Vec3=[0,1,8]; clearPulse=0; dropPulse=0;
  clearEvent:ClearEvent|null=null; clearReward:ClearReward|null=null;
  private clearTimers:ReturnType<typeof setTimeout>[]=[]; private clearId=0;
  private listeners=new Set<()=>void>(); private cached?:Snapshot;
  constructor(){this.nextKind=this.pick();this.spawn();}
  subscribe=(fn:()=>void)=>{this.listeners.add(fn);return()=>this.listeners.delete(fn)};
  private emit(){this.cached=undefined;this.listeners.forEach(fn=>fn())}
  snapshot=()=>this.cached??(this.cached={phase:this.phase,board:[...this.board.values()],active:this.phase==='gameover'||this.phase==='clearing'?[]:this.cells().map(pos=>({pos,kind:this.kind})),ghost:this.phase==='gameover'||this.phase==='clearing'?[]:this.ghost().map(pos=>({pos,kind:this.kind})),kind:this.kind,nextKind:this.nextKind,score:this.score,level:this.level,layers:this.layers,clearPulse:this.clearPulse,dropPulse:this.dropPulse,nearLayer:this.nearLayer(),clearEvent:this.clearEvent,clearReward:this.clearReward});
  get level(){return 1+Math.floor(this.layers/CONFIG.layersPerLevel)}
  get interval(){return Math.max(CONFIG.minimumSeconds,CONFIG.fallSeconds*CONFIG.speedFactor**(this.level-1))}
  private pick(){if(!this.bag.length)this.bag=[0,1,2,3,4].sort(()=>Math.random()-.5);return this.bag.pop()!}
  start(){this.restart();this.phase='playing';this.emit()}
  restart(){this.clearTimers.forEach(clearTimeout);this.clearTimers=[];this.clearEvent=this.clearReward=null;this.board.clear();this.score=this.layers=this.clearPulse=this.dropPulse=0;this.bag=[];this.nextKind=this.pick();this.phase='playing';this.spawn();this.emit()}
  togglePause(){if(this.phase==='playing')this.phase='paused';else if(this.phase==='paused')this.phase='playing';this.emit()}
  private spawn(){this.kind=this.nextKind;this.nextKind=this.pick();this.shape=SHAPES[this.kind].map(v=>[...v] as Vec3);const maxX=Math.max(...this.shape.map(c=>c[0])),maxZ=Math.max(...this.shape.map(c=>c[2]));this.pos=[Math.floor((CONFIG.width-1-maxX)/2),1,ACTIVE_HEIGHT-1-maxZ];if(!this.valid())this.phase='gameover'}
  cells(shape=this.shape,pos=this.pos){return shape.map(c=>c.map((n,i)=>n+pos[i]) as Vec3)}
  valid(shape=this.shape,pos=this.pos){return this.cells(shape,pos).every(([x,y,z])=>x>=0&&x<CONFIG.width&&y>=0&&y<CONFIG.depth&&z>=0&&z<ACTIVE_HEIGHT&&!this.board.has(key([x,y,z])))}
  move([dx,dy,dz]:Vec3){if(this.phase!=='playing')return false;const p:Vec3=[this.pos[0]+dx,this.pos[1]+dy,this.pos[2]+dz];if(!this.valid(this.shape,p))return false;this.pos=p;this.emit();return true}
  rotate(axis:Axis){if(this.phase!=='playing')return false;const fn={X:([x,y,z]:Vec3):Vec3=>[x,-z,y],Y:([x,y,z]:Vec3):Vec3=>[z,y,-x],Z:([x,y,z]:Vec3):Vec3=>[-y,x,z]}[axis];let s=this.shape.map(fn);const lo:[number,number,number]=[0,1,2].map(i=>Math.min(...s.map(c=>c[i]))) as Vec3;s=s.map(c=>c.map((v,i)=>v-lo[i]) as Vec3);for(const [dx,dy,dz] of [[0,0,0],[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1],[-2,0,0],[0,-2,0],[0,0,-2]] as Vec3[]){const p:Vec3=[this.pos[0]+dx,this.pos[1]+dy,this.pos[2]+dz];if(this.valid(s,p)){this.shape=s;this.pos=p;this.emit();return true}}return false}
  ghost(){let p=[...this.pos] as Vec3;while(this.valid(this.shape,[p[0],p[1],p[2]-1]))p=[p[0],p[1],p[2]-1];const cells=this.cells(this.shape,p);return cells.every(([, , z])=>z<CONFIG.height)?cells:[]}
  tick(){if(this.phase!=='playing')return;if(!this.move([0,0,-1]))this.lock()}
  drop(){if(this.phase!=='playing')return;let n=0,bufferSteps=0;while(true){const inBuffer=this.cells().some(([, , z])=>z>=CONFIG.height);if(!this.move([0,0,-1]))break;n++;if(inBuffer)bufferSteps++}this.score+=Math.max(0,n-bufferSteps)*2;this.dropPulse++;this.lock()}
  private occupiedAt(z:number){let filled=0;const holes:Vec3[]=[];for(let x=0;x<CONFIG.width;x++)for(let y=0;y<CONFIG.depth;y++){const cell:Vec3=[x,y,z];if(this.board.has(key(cell)))filled++;else holes.push(cell)}return {filled,holes}}
  private fullLayers(){const full:number[]=[];for(let z=0;z<CONFIG.height;z++)if(this.occupiedAt(z).filled===CONFIG.width*CONFIG.depth)full.push(z);return full}
  private nearLayer():NearLayer|null{if(this.phase==='clearing'||this.phase==='gameover')return null;let best:NearLayer|null=null;for(let z=0;z<CONFIG.height;z++){const {filled,holes}=this.occupiedAt(z);if(filled>=Math.ceil(CONFIG.width*CONFIG.depth*.8)&&filled<CONFIG.width*CONFIG.depth&&(!best||filled>best.filled))best={z,filled,holes}}return best}
  private schedule(fn:()=>void,delay:number){this.clearTimers.push(setTimeout(fn,delay))}
  private lock(){const cells=this.cells();if(cells.some(([, , z])=>z>=CONFIG.height)){this.phase='gameover';this.emit();return}cells.forEach(pos=>this.board.set(key(pos),{pos,kind:this.kind}));const full=this.fullLayers();if(full.length)this.beginClear(full);else{this.spawn();this.emit()}}
  private beginClear(full:number[]){
    const id=++this.clearId,points=CONFIG.layerPoints*full.length**2*this.level;
    const collapseFrom:Record<string,number>={};
    const collapsed=new Map<string,Cell>();
    this.board.forEach(c=>{if(!full.includes(c.pos[2])){const pos:Vec3=[c.pos[0],c.pos[1],c.pos[2]-full.filter(f=>f<c.pos[2]).length];collapsed.set(key(pos),{...c,pos});if(pos[2]!==c.pos[2])collapseFrom[key(pos)]=c.pos[2]}});
    this.phase='clearing';
    this.clearEvent={id,stage:'anticipation',planes:full,points,collapseFrom};
    this.clearReward={id,planes:full.length,points,z:full[Math.floor(full.length/2)]};
    this.emit();
    this.schedule(()=>{this.clearEvent={...this.clearEvent!,stage:'removal'};this.emit()},CLEAR_TIMING.anticipation);
    this.schedule(()=>{
      this.board=collapsed;this.score+=points;this.layers+=full.length;this.clearPulse++;
      this.clearEvent={...this.clearEvent!,stage:'collapse'};this.emit();
    },CLEAR_TIMING.anticipation+CLEAR_TIMING.removal);
    this.schedule(()=>{this.clearEvent=null;this.phase='playing';this.spawn();this.emit()},CLEAR_TIMING.anticipation+CLEAR_TIMING.removal+CLEAR_TIMING.collapse);
    this.schedule(()=>{if(this.clearReward?.id===id){this.clearReward=null;this.emit()}},CLEAR_TIMING.reward);
  }
}
