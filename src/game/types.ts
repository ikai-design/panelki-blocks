export type Vec3=[number,number,number];
export type Axis='X'|'Y'|'Z';
export type Phase='title'|'playing'|'paused'|'clearing'|'gameover';
export type Cell={pos:Vec3;kind:number};
export type NearLayer={z:number;filled:number;holes:Vec3[]};
export type ClearEvent={id:number;stage:'anticipation'|'removal'|'collapse';planes:number[];points:number;collapseFrom:Record<string,number>};
export type ClearReward={id:number;planes:number;points:number;z:number};
export type Snapshot={phase:Phase;board:Cell[];active:Cell[];ghost:Cell[];kind:number;nextKind:number;score:number;level:number;layers:number;clearPulse:number;dropPulse:number;nearLayer:NearLayer|null;clearEvent:ClearEvent|null;clearReward:ClearReward|null};
