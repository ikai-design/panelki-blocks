import type {Vec3} from './types';
export const CONFIG={width:5,depth:4,height:12,fallSeconds:1.1,speedFactor:.82,minimumSeconds:.12,layersPerLevel:4,layerPoints:100};
// Settled construction remains 12 layers tall; the extra rows are active-piece maneuver space only.
export const SPAWN_BUFFER=3;
export const ACTIVE_HEIGHT=CONFIG.height+SPAWN_BUFFER;
// Rendering contract: every logical vertical layer occupies exactly one world unit.
export const BLOCK_HEIGHT=1;
export const NAMES=['Khrushchovka tower','Yugoslav slab','Courtyard block','Five-story prefab','Brutalist high-rise'];
export const SHAPES:Vec3[][]=[[[0,0,0],[0,0,1],[0,0,2],[0,0,3]],[[0,0,0],[1,0,0],[2,0,0],[2,0,1]],[[0,0,0],[1,0,0],[0,1,0],[1,1,0]],[[0,0,0],[1,0,0],[1,0,1],[2,0,1]],[[0,0,0],[1,0,0],[2,0,0],[1,0,1]]];
export const PALETTE=['#8e9a89','#5d9886','#b29458','#a76364','#526e89'];
