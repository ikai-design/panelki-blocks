import {useGLTF} from '@react-three/drei';import {useMemo} from 'react';import {Box3,Vector3} from 'three';import type {Mesh,Object3D} from 'three';import {BLOCK_HEIGHT,PALETTE} from '../game/config';

const ASSETS=['khrushchovka','yugoslav-slab','courtyard','five-story','brutalist'];

export function Block({kind,position,ghost=false}:{kind:number;position:[number,number,number];ghost?:boolean}){
  const {scene}=useGLTF(`/assets/buildings/${ASSETS[kind]}.glb`);
  const {model,visualScaleY,visualOffsetY}=useMemo(()=>{
    const model=scene.clone(true);
    model.traverse((o:Object3D)=>{if('castShadow'in o){(o as Mesh).castShadow=!ghost;(o as Mesh).receiveShadow=true}});
    const bounds=new Box3().setFromObject(model),size=bounds.getSize(new Vector3()),center=bounds.getCenter(new Vector3());
    // Normalize only the imported visual on Y. The logical cell and horizontal silhouette stay unchanged.
    const visualScaleY=BLOCK_HEIGHT/size.y;
    return {model,visualScaleY,visualOffsetY:-center.y*visualScaleY};
  },[scene,ghost]);
  if(ghost)return <mesh position={position}><boxGeometry args={[.84,BLOCK_HEIGHT,.84]}/><meshBasicMaterial color={PALETTE[kind]} transparent opacity={.1}/></mesh>;
  return <group position={position}><primitive object={model} position={[0,visualOffsetY,0]} scale={[1,visualScaleY,1]}/></group>;
}
