export type Vec3=[number,number,number];
export type Axis='X'|'Y'|'Z';
export type Phase='title'|'playing'|'paused'|'gameover';
export type Cell={pos:Vec3;kind:number};
export type Snapshot={phase:Phase;board:Cell[];active:Cell[];ghost:Cell[];kind:number;nextKind:number;score:number;level:number;layers:number;clearPulse:number;dropPulse:number};
