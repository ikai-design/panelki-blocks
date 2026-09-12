import {CONFIG,SHAPES} from './config';
import type {Axis,Cell,Phase,Snapshot,Vec3} from './types';
const key=([x,y,z]:Vec3)=>`${x},${y},${z}`;
export class Game {
  board=new Map<string,Cell>(); score=0; layers=0; phase:Phase='title'; bag:number[]=[];
  kind=0; nextKind=0; shape:Vec3[]=SHAPES[0]; pos:Vec3=[0,1,8]; clearPulse=0; dropPulse=0;
  private listeners=new Set<()=>void>(); private cached?:Snapshot;
  constructor(){this.nextKind=this.pick();this.spawn();}
  subscribe=(fn:()=>void)=>{this.listeners.add(fn);return()=>this.listeners.delete(fn)};
  private emit(){this.cached=undefined;this.listeners.forEach(fn=>fn())}
  snapshot=()=>this.cached??(this.cached={phase:this.phase,board:[...this.board.values()],active:this.phase==='gameover'?[]:this.cells().map(pos=>({pos,kind:this.kind})),ghost:this.phase==='gameover'?[]:this.ghost().map(pos=>({pos,kind:this.kind})),kind:this.kind,nextKind:this.nextKind,score:this.score,level:this.level,layers:this.layers,clearPulse:this.clearPulse,dropPulse:this.dropPulse});
  get level(){return 1+Math.floor(this.layers/CONFIG.layersPerLevel)}
  get interval(){return Math.max(CONFIG.minimumSeconds,CONFIG.fallSeconds*CONFIG.speedFactor**(this.level-1))}
  private pick(){if(!this.bag.length)this.bag=[0,1,2,3,4].sort(()=>Math.random()-.5);return this.bag.pop()!}
  start(){this.restart();this.phase='playing';this.emit()}
  restart(){this.board.clear();this.score=this.layers=this.clearPulse=this.dropPulse=0;this.bag=[];this.nextKind=this.pick();this.phase='playing';this.spawn();this.emit()}
  togglePause(){if(this.phase==='playing')this.phase='paused';else if(this.phase==='paused')this.phase='playing';this.emit()}
  private spawn(){this.kind=this.nextKind;this.nextKind=this.pick();this.shape=SHAPES[this.kind].map(v=>[...v] as Vec3);const maxX=Math.max(...this.shape.map(c=>c[0])),maxZ=Math.max(...this.shape.map(c=>c[2]));this.pos=[Math.floor((CONFIG.width-1-maxX)/2),1,CONFIG.height-1-maxZ];if(!this.valid())this.phase='gameover'}
  cells(shape=this.shape,pos=this.pos){return shape.map(c=>c.map((n,i)=>n+pos[i]) as Vec3)}
  valid(shape=this.shape,pos=this.pos){return this.cells(shape,pos).every(([x,y,z])=>x>=0&&x<CONFIG.width&&y>=0&&y<CONFIG.depth&&z>=0&&z<CONFIG.height&&!this.board.has(key([x,y,z])))}
  move([dx,dy,dz]:Vec3){if(this.phase!=='playing')return false;const p:Vec3=[this.pos[0]+dx,this.pos[1]+dy,this.pos[2]+dz];if(!this.valid(this.shape,p))return false;this.pos=p;this.emit();return true}
  rotate(axis:Axis){if(this.phase!=='playing')return false;const fn={X:([x,y,z]:Vec3):Vec3=>[x,-z,y],Y:([x,y,z]:Vec3):Vec3=>[z,y,-x],Z:([x,y,z]:Vec3):Vec3=>[-y,x,z]}[axis];let s=this.shape.map(fn);const lo:[number,number,number]=[0,1,2].map(i=>Math.min(...s.map(c=>c[i]))) as Vec3;s=s.map(c=>c.map((v,i)=>v-lo[i]) as Vec3);for(const [dx,dy,dz] of [[0,0,0],[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1],[-2,0,0],[0,-2,0],[0,0,-2]] as Vec3[]){const p:Vec3=[this.pos[0]+dx,this.pos[1]+dy,this.pos[2]+dz];if(this.valid(s,p)){this.shape=s;this.pos=p;this.emit();return true}}return false}
  ghost(){let p=[...this.pos] as Vec3;while(this.valid(this.shape,[p[0],p[1],p[2]-1]))p=[p[0],p[1],p[2]-1];return this.cells(this.shape,p)}
  tick(){if(this.phase!=='playing')return;if(!this.move([0,0,-1]))this.lock()}
  drop(){if(this.phase!=='playing')return;let n=0;while(this.move([0,0,-1]))n++;this.score+=n*2;this.dropPulse++;this.lock()}
  private lock(){this.cells().forEach(pos=>this.board.set(key(pos),{pos,kind:this.kind}));this.clearLayers();this.spawn();this.emit()}
  private clearLayers(){const full:number[]=[];for(let z=0;z<CONFIG.height;z++)if(Array.from({length:CONFIG.width*CONFIG.depth},(_,i)=>this.board.has(key([i%CONFIG.width,Math.floor(i/CONFIG.width),z]))).every(Boolean))full.push(z);if(!full.length)return;const next=new Map<string,Cell>();this.board.forEach(c=>{if(!full.includes(c.pos[2])){const pos:[number,number,number]=[c.pos[0],c.pos[1],c.pos[2]-full.filter(f=>f<c.pos[2]).length];next.set(key(pos),{...c,pos})}});this.board=next;this.score+=CONFIG.layerPoints*full.length**2*this.level;this.layers+=full.length;this.clearPulse++}
}
