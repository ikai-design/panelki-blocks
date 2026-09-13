import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { ContactShadows, Html, OrbitControls, Stars, useGLTF } from '@react-three/drei';
import { Bloom, EffectComposer, N8AO, Vignette } from '@react-three/postprocessing';
import { useEffect, useMemo, useRef } from 'react';
import { CanvasTexture, PerspectiveCamera, RepeatWrapping, SRGBColorSpace, Vector3 } from 'three';
import type { Object3D } from 'three';
import type { Group } from 'three';
import { BLOCK_HEIGHT, CONFIG } from '../game/config';
import type { Snapshot } from '../game/types';
import { Block } from './Block';

type Basis = (forward: [number, number], right: [number, number]) => void;
const TERRAIN_GROUND_Y = -1.04;
// The field mesh top is 0.02 below its group origin, so this keeps it flush with terrain.
const PLAYFIELD_GROUP_Y = TERRAIN_GROUND_Y + .02;
// Imported building modules have a -0.499 local Y bound; .48 centers their cell floor on the field.
const BLOCK_CELL_CENTER_Y = .48;
// Field footprint is x: -2.5..2.5, z: -2..2. Keep scenery at least 3.75 units clear
// so its rendered bounds never compete with falling pieces or the construction area.
const PLAYFIELD_SCENERY_BUFFER = { minX: -6.25, maxX: 6.25, minZ: -5.75, maxZ: 5.75 };

type TrashKind = 'paper' | 'bag' | 'can';
type TrashParticle = {
  kind: TrashKind; x: number; z: number; vx: number; vz: number; phase: number;
  drag: number; gust: number; spin: number; y: number; hop: number;
};

// Smooth deterministic value noise gives irregular gusts without a visibly repeating sine wave.
const windHash = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
const windNoise = (t: number) => {
  const i = Math.floor(t), f = t - i, eased = f * f * (3 - 2 * f);
  return windHash(i) * (1 - eased) + windHash(i + 1) * eased;
};

function Terrain({ industrial = false }: { industrial?: boolean }) {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 512;
    const c = canvas.getContext('2d')!;
    c.fillStyle = industrial ? '#272b2c' : '#40382b'; c.fillRect(0, 0, 512, 512);
    let seed = 918273;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
    const tones = industrial ? ['#313638', '#1d2021', '#41403b', '#282b2b'] : ['#574936', '#6b583c', '#302d25', '#82704a', '#49402f'];
    for (let i = 0; i < (industrial ? 420 : 1200); i++) {
      const x = rnd() * 512, y = rnd() * 512, r = 1 + rnd() * 14;
      c.globalAlpha = .08 + rnd() * .2; c.fillStyle = tones[Math.floor(rnd() * tones.length)];
      c.beginPath(); c.ellipse(x, y, r, r * (.3 + rnd()), rnd() * Math.PI, 0, Math.PI * 2); c.fill();
    }
    for (let i = 0; i < (industrial ? 28 : 90); i++) {
      const x = rnd() * 512, y = rnd() * 512, r = 8 + rnd() * 35;
      c.globalAlpha = .08 + rnd() * .12; c.fillStyle = industrial ? (rnd() > .45 ? '#111415' : '#554738') : (rnd() > .45 ? '#171813' : '#928050');
      c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill();
    }
    c.globalAlpha = 1;
    const t = new CanvasTexture(canvas); t.wrapS = t.wrapT = RepeatWrapping; t.repeat.set(3, 3); t.colorSpace = SRGBColorSpace;
    return t;
  }, [industrial]);
  const grass = useMemo(() => {
    let seed = 417; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    return industrial ? [] : Array.from({ length: 85 }, () => ({ x: (rnd() - .5) * 34, z: (rnd() - .5) * 34, s: .12 + rnd() * .28, r: rnd() * Math.PI }));
  }, [industrial]);
  return <group position={[0, -1.04, 0]}>
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow><circleGeometry args={[25, 96]} /><meshStandardMaterial map={texture} bumpMap={texture} bumpScale={industrial ? .035 : .16} color={industrial ? '#686867' : '#8a7654'} roughness={1} /></mesh>
    {!industrial && <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, .012, 0]} receiveShadow><ringGeometry args={[4.2, 7.5, 48]} /><meshStandardMaterial color="#342f27" roughness={1} transparent opacity={.24} /></mesh>}
    {grass.map((g, i) => <group key={i} position={[g.x, .04, g.z]} rotation={[0, g.r, 0]} scale={g.s}><mesh rotation={[0, 0, -.18]}><coneGeometry args={[.07, 1.25, 3]} /><meshStandardMaterial color={i % 4 === 0 ? '#29291e' : '#7a6a3d'} roughness={1} /></mesh><mesh position={[.16, 0, .04]} rotation={[0, 0, .24]}><coneGeometry args={[.055, .85, 3]} /><meshStandardMaterial color="#554b2d" roughness={1} /></mesh></group>)}
  </group>;
}

function CameraBasis({ onChange }: { onChange: Basis }) {
  const camera = useThree(s => s.camera); const last = useRef('');
  useFrame(() => {
    const d = new Vector3(); camera.getWorldDirection(d);
    const cardinal = (a: number, b: number): [number, number] => Math.abs(a) > Math.abs(b) ? [Math.sign(a), 0] : [0, Math.sign(b)];
    const forward = cardinal(d.x, d.z), right = cardinal(-d.z, d.x), next = [...forward, ...right].join(',');
    if (next !== last.current) { last.current = next; onChange(forward, right); }
  });
  return null;
}

function SceneReady({ onReady }: { onReady: () => void }) {
  const frames = useRef(0);
  useFrame(() => { if (++frames.current === 2) onReady(); });
  return null;
}

function CameraFraming({ mobile }: { mobile: boolean }) {
  const camera = useThree(s => s.camera);
  useEffect(() => {
    const perspective = camera as PerspectiveCamera;
    const position: [number, number, number] = mobile ? [11.5, 12.5, 21] : [14, 14, 20];
    perspective.position.set(position[0], position[1], position[2]);
    perspective.fov = mobile ? 42 : 35;
    perspective.updateProjectionMatrix();
  }, [camera, mobile]);
  return null;
}

function Well({ snap, industrial = false }: { snap: Snapshot; industrial?: boolean }) {
  const group = useRef<Group>(null), last = useRef(snap.dropPulse);
  const cx = (CONFIG.width - 1) / 2, cz = (CONFIG.depth - 1) / 2;
  useFrame((_, dt) => { if (group.current) { const hit = last.current !== snap.dropPulse; group.current.position.y += (PLAYFIELD_GROUP_Y - group.current.position.y) * Math.min(1, dt * 10); if (hit) { group.current.position.y = PLAYFIELD_GROUP_Y - .09; last.current = snap.dropPulse; } } });
  // Keep the field at one canonical world height; only the temporary drop shake changes this parent.
  return <group ref={group} position={[-cx, PLAYFIELD_GROUP_Y, -cz]}>
    <mesh position={[cx, -.16, cz]} receiveShadow><boxGeometry args={[CONFIG.width, .28, CONFIG.depth]} /><meshStandardMaterial color={industrial ? '#414848' : '#343a37'} roughness={.9} /></mesh>
    <mesh position={[cx, -.315, cz]} receiveShadow><boxGeometry args={[CONFIG.width + .42, .06, CONFIG.depth + .42]} /><meshStandardMaterial color={industrial ? '#292e2f' : '#272822'} roughness={1} /></mesh>
    {Array.from({ length: CONFIG.width + 1 }, (_, i) => <mesh key={`gx${i}`} position={[i - .5, .002, cz]}><boxGeometry args={[.018, .018, CONFIG.depth]} /><meshStandardMaterial color="#414d4a" /></mesh>)}
    {Array.from({ length: CONFIG.depth + 1 }, (_, i) => <mesh key={`gz${i}`} position={[cx, .002, i - .5]}><boxGeometry args={[CONFIG.width, .018, .018]} /><meshStandardMaterial color="#414d4a" /></mesh>)}
    {[[-.5, -.5], [CONFIG.width - .5, -.5], [-.5, CONFIG.depth - .5], [CONFIG.width - .5, CONFIG.depth - .5]].map(([x, z], i) => <mesh key={i} position={[x, CONFIG.height / 2, z]}><boxGeometry args={[.022, CONFIG.height, .022]} /><meshStandardMaterial color="#584b40" emissive="#1c1713" emissiveIntensity={.03} roughness={.9} transparent opacity={.48} /></mesh>)}
    {/* GLB building modules are centered on their cell; this offset puts their bases on the field surface. */}
    {snap.ghost.map((c, i) => <Block key={`g${i}`} kind={c.kind} position={[c.pos[0], c.pos[2] * BLOCK_HEIGHT + BLOCK_CELL_CENTER_Y, c.pos[1]]} ghost />)}
    {snap.board.map(c => <Block key={c.pos.join()} kind={c.kind} position={[c.pos[0], c.pos[2] * BLOCK_HEIGHT + BLOCK_CELL_CENTER_Y, c.pos[1]]} />)}
    {snap.active.map((c, i) => <Block key={`a${i}`} kind={c.kind} position={[c.pos[0], c.pos[2] * BLOCK_HEIGHT + BLOCK_CELL_CENTER_Y, c.pos[1]]} />)}
  </group>;
}

function RotationHint({ snap, onDismiss }: { snap: Snapshot; onDismiss: () => void }) {
  const timer = useRef<number | undefined>(undefined);
  const gizmo = useRef<Group>(null);
  const hintTime = useRef(0);
  const reducedMotion = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, []);
  useEffect(() => { timer.current = window.setTimeout(onDismiss, 5200); return () => window.clearTimeout(timer.current); }, [onDismiss]);
  useFrame((_, dt) => {
    if (reducedMotion || !gizmo.current) return;
    hintTime.current += Math.min(dt, .05);
    const t = hintTime.current;
    gizmo.current.rotation.set(Math.sin(t * 2.6) * .42 - .2, Math.sin(t * 2.1) * .68 - .35, Math.sin(t * 1.7) * .12);
  });
  const cell = snap.active[0]?.pos;
  if (!cell) return null;
  return <group position={[cell[0], cell[2] + BLOCK_CELL_CENTER_Y + .18, cell[1]]}>
    <group ref={gizmo}>
      <mesh><boxGeometry args={[.48, .48, .48]} /><meshBasicMaterial color="#f1f1ec" transparent opacity={.18} wireframe /></mesh>
      <mesh rotation={[0, Math.PI / 2, 0]}><torusGeometry args={[.36, .012, 4, 24]} /><meshBasicMaterial color="#f1f1ec" transparent opacity={.45} /></mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[.42, .012, 4, 24]} /><meshBasicMaterial color="#f1f1ec" transparent opacity={.32} /></mesh>
      <mesh><torusGeometry args={[.3, .012, 4, 24]} /><meshBasicMaterial color="#f1f1ec" transparent opacity={.55} /></mesh>
    </group>
    <Html center distanceFactor={8} position={[0, .52, 0]} className="rotation-hint" zIndexRange={[3, 0]}>
      <span>X Y Z <b>·</b> Rotate</span>
    </Html>
  </group>;
}

function PrototypeBuilding() { const {scene}=useGLTF('/assets/buildings/khrushchyovka-textured-v1.glb'); const model=useMemo(()=>scene.clone(true),[scene]); model.traverse((o:Object3D)=>{if('castShadow'in o){(o as any).castShadow=true;(o as any).receiveShadow=true}}); return <primitive object={model} position={[0, 0, 0]} scale={1} />; }
function Neighbourhood() { return <group>{[[-7.4, -2.5, 3, 0, -.08], [-5.3, 2.5, 5, 1, .12], [5.6, 2.8, 4, 3, -.1], [7.8, -1.8, 6, 4, .08]].map(([x, z, h, k, r], i) => <group key={i} position={[x, -.5, z]} rotation={[0, r, 0]}>{i===0 ? <PrototypeBuilding /> : Array.from({ length: h }, (_, n) => <Block key={n} kind={k} position={[0, n * BLOCK_HEIGHT, 0]} />)}</group>)}</group>; }

function CourtyardEasterEgg({ clearPulse }: { clearPulse: number }) {
  const cat = useRef<Group>(null), lid = useRef<Group>(null), lastPulse = useRef(clearPulse), timer = useRef(0);
  useFrame((_, dt) => {
    if (clearPulse !== lastPulse.current) {
      if (clearPulse > 0 && lastPulse.current === 0) timer.current = 1.25;
      lastPulse.current = clearPulse;
    }
    if (!cat.current || !lid.current) return;
    const wasTriggered = timer.current > 0;
    if (wasTriggered) timer.current = Math.max(0, timer.current - dt);
    const t = wasTriggered ? 1 - timer.current / 1.25 : 0;
    const rise = t < .2 ? t / .2 : t < .82 ? 1 : Math.max(0, 1 - (t - .82) / .18);
    const hop = Math.sin(Math.min(1, t / .82) * Math.PI) * .18;
    cat.current.position.y = .1 + rise * .54 + hop;
    cat.current.rotation.z = Math.sin(t * Math.PI * 2) * .06;
    lid.current.rotation.x = -.04 + (wasTriggered ? Math.sin(t * Math.PI * 2.2) * .1 * (1 - t) : 0);
  });
  return <group position={[4, 0, -4.8]}>
    <mesh position={[0, .34, 0]} castShadow receiveShadow><boxGeometry args={[1.15, .68, .78]} /><meshStandardMaterial color="#3d4541" roughness={.9} /></mesh>
    <mesh position={[0, .08, .4]}><boxGeometry args={[.88, .12, .06]} /><meshStandardMaterial color="#303633" roughness={1} /></mesh>
    <group ref={lid} position={[0, .72, 0]}>
      <mesh castShadow><boxGeometry args={[1.2, .08, .83]} /><meshStandardMaterial color="#4b514d" roughness={.95} /></mesh>
    </group>
    <group ref={cat} position={[.34, .1, .47]}>
      <mesh castShadow><sphereGeometry args={[.2, 7, 5]} /><meshStandardMaterial color="#6c6a61" roughness={1} /></mesh>
      <mesh position={[.16, .16, 0]} castShadow><sphereGeometry args={[.14, 7, 5]} /><meshStandardMaterial color="#77746a" roughness={1} /></mesh>
      <mesh position={[.1, .27, -.08]} rotation={[0, 0, -.25]}><coneGeometry args={[.07, .16, 3]} /><meshStandardMaterial color="#5d5b54" roughness={1} /></mesh>
      <mesh position={[.1, .27, .08]} rotation={[0, 0, -.25]}><coneGeometry args={[.07, .16, 3]} /><meshStandardMaterial color="#5d5b54" roughness={1} /></mesh>
    </group>
  </group>;
}

function AmbientTrash() {
  const refs = useRef<(Group | null)[]>([]);
  const particles = useRef<TrashParticle[]>([
    { kind: 'paper', x: -7.8, z: 1.4, vx: 0, vz: 0, phase: .7, drag: 2.7, gust: 1.0, spin: 2.5, y: .035, hop: 0 },
    { kind: 'bag', x: 6.7, z: -5.2, vx: 0, vz: 0, phase: 2.3, drag: 2.15, gust: .82, spin: 1.45, y: .05, hop: 0 },
    { kind: 'can', x: -5.9, z: -5.8, vx: 0, vz: 0, phase: 4.1, drag: 3.5, gust: .34, spin: 3.2, y: .055, hop: 0 },
    { kind: 'paper', x: 7.9, z: 3.8, vx: 0, vz: 0, phase: 5.6, drag: 2.9, gust: .92, spin: 2.1, y: .035, hop: 0 },
  ]);
  const elapsed = useRef(0);
  const reducedMotion = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, []);

  useFrame((_, dt) => {
    if (reducedMotion) return;
    const step = Math.min(dt, 1 / 30); elapsed.current += step;
    const t = elapsed.current;
    // Two differently paced noise layers create slow swells with occasional asymmetric gusts.
    const slow = windNoise(t * .105), detail = windNoise(t * .31 + 19.4);
    const strength = .055 + slow * .075 + Math.max(0, detail - .72) * .22;
    const direction = -.38 + (windNoise(t * .045 + 7.2) - .5) * .28;
    const wx = Math.cos(direction), wz = Math.sin(direction);

    particles.current.forEach((p, i) => {
      const object = refs.current[i]; if (!object) return;
      const local = windNoise(t * (.42 + i * .025) + p.phase) - .5;
      const lateral = windNoise(t * .23 + p.phase * 3.7) - .5;
      p.vx += (wx * strength * p.gust + local * .035) * step;
      p.vz += (wz * strength * p.gust + lateral * .045) * step;
      const damping = Math.exp(-p.drag * step); p.vx *= damping; p.vz *= damping;
      p.x += p.vx * step; p.z += p.vz * step;

      const gustLift = strength > .115 && p.kind !== 'can';
      if (gustLift && p.hop <= 0 && windNoise(t * .7 + p.phase) > .78) p.hop = p.kind === 'bag' ? .42 : .25;
      p.hop = Math.max(0, p.hop - step);
      const lift = p.hop > 0 ? Math.sin((p.hop / (p.kind === 'bag' ? .42 : .25)) * Math.PI) * (p.kind === 'bag' ? .09 : .045) : 0;

      // Quietly wrap at the far courtyard edge, never beside the central playable board.
      if (p.x > 10.5) p.x = -10.5; else if (p.x < -10.5) p.x = 10.5;
      if (p.z > 7.7) p.z = -7.7; else if (p.z < -7.7) p.z = 7.7;
      if (Math.abs(p.x) < 4.4 && Math.abs(p.z) < 3.4) {
        p.z = (p.z < 0 ? -1 : 1) * 3.4;
        p.vz += (p.z < 0 ? -1 : 1) * .025;
      }
      object.position.set(p.x, p.y + lift, p.z);
      const speed = Math.hypot(p.vx, p.vz);
      object.rotation.y += (p.spin * speed + local * .008) * step * 10;
      object.rotation.z = p.kind === 'can' ? object.rotation.z + speed * 2.2 : local * .2 + lift * 1.8;
      object.rotation.x = p.kind === 'bag' ? lateral * .22 : object.rotation.x;
    });
  });

  return <group>
    {particles.current.map((p, i) => <group key={`${p.kind}-${i}`} ref={node => { refs.current[i] = node; }} position={[p.x, p.y, p.z]}>
      {p.kind === 'paper' && <mesh castShadow rotation={[-Math.PI / 2 + .06, 0, .12]}><planeGeometry args={[.32, .22]} /><meshStandardMaterial color={i === 0 ? '#b7b09b' : '#8f978f'} roughness={1} side={2} /></mesh>}
      {p.kind === 'bag' && <group><mesh castShadow scale={[.25, .3, .08]}><octahedronGeometry args={[.5, 0]} /><meshStandardMaterial color="#777a72" roughness={.9} transparent opacity={.88} /></mesh><mesh position={[-.07, .17, 0]} rotation={[0, 0, -.35]}><torusGeometry args={[.055, .014, 3, 6]} /><meshStandardMaterial color="#686b65" roughness={1} /></mesh><mesh position={[.07, .17, 0]} rotation={[0, 0, .35]}><torusGeometry args={[.055, .014, 3, 6]} /><meshStandardMaterial color="#686b65" roughness={1} /></mesh></group>}
      {p.kind === 'can' && <mesh castShadow rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[.075, .075, .19, 8]} /><meshStandardMaterial color="#666a65" metalness={.45} roughness={.72} /></mesh>}
    </group>)}
  </group>;
}

function EnvironmentDetails({ clearPulse }: { clearPulse: number }) {
  const tree = useGLTF('/assets/environment/dead-tree.glb').scene;
  const playground = useGLTF('/assets/environment/playground.glb').scene;
  const trees = useMemo(() => [[-8, -5, .8, 0], [-6, 5, 1.1, .7], [7, 5, .9, 1.8], [9, -4, 1.2, 2.5], [-10, 1, .75, -.5], [5, -7, .85, .3]] as [number, number, number, number][], []);
  return <group position={[0, -1, 0]}>{trees.map(([x, z, s, r], i) => <primitive key={i} object={tree.clone(true)} position={[x, 0, z]} scale={s} rotation={[0, r, 0]} />)}<primitive object={playground.clone(true)} position={[-4, 0, -3]} scale={.72} rotation={[0, .35, 0]} /><CourtyardEasterEgg clearPulse={clearPulse} /><AmbientTrash /></group>;
}

function IndustrialEnvironment() {
  const source = useGLTF('/assets/environment/factory-dusk.glb').scene;
  const model = useMemo(() => {
    const clone = source.clone(true);
    clone.traverse((object: Object3D) => { if ('castShadow' in object) { (object as any).castShadow = true; (object as any).receiveShadow = true; } });
    return clone;
  }, [source]);
  return <primitive object={model} position={[0, TERRAIN_GROUND_Y, 0]} />;
}

function ChernobylStationLandmark() {
  const source = useGLTF('/assets/environment/factory-dusk/chernobyl-station.glb').scene;
  const model = useMemo(() => {
    const clone = source.clone(true);
    clone.traverse((object: Object3D) => {
      if ('castShadow' in object) {
        (object as any).castShadow = true;
        (object as any).receiveShadow = true;
      }
    });
    return clone;
  }, [source]);
  return <primitive object={model} position={[-1.5, TERRAIN_GROUND_Y, -12.5]} rotation={[0, -.06, 0]} scale={.82} />;
}

function FactoryDuskVignette() {
  const kioskSource = useGLTF('/assets/environment/factory-dusk/coffee-kiosk.glb').scene;
  const suvSource = useGLTF('/assets/environment/factory-dusk/luxury-suv.glb').scene;
  const [kiosk, suv] = useMemo(() => {
    const prepare = (source: Object3D) => {
      const clone = source.clone(true);
      clone.traverse((object: Object3D) => {
        if ('castShadow' in object) {
          (object as any).castShadow = true;
          (object as any).receiveShadow = true;
        }
      });
      return clone;
    };
    return [prepare(kioskSource), prepare(suvSource)];
  }, [kioskSource, suvSource]);
  return <group position={[0, TERRAIN_GROUND_Y, 0]}>
    {/* Both models sit outside PLAYFIELD_SCENERY_BUFFER, while their pairing stays intact. */}
    <primitive object={kiosk} position={[PLAYFIELD_SCENERY_BUFFER.minX - 5.85, 0, PLAYFIELD_SCENERY_BUFFER.maxZ - .45]} rotation={[0, .16, 0]} />
    <primitive object={suv} position={[PLAYFIELD_SCENERY_BUFFER.minX - 2.4, 0, PLAYFIELD_SCENERY_BUFFER.maxZ + .4]} rotation={[0, -.12, 0]} />
  </group>;
}

export function GameScene({ snap, onViewBasis, showRotationHint, onDismissRotationHint, theme, onReady }: { snap: Snapshot; onViewBasis: Basis; showRotationHint: boolean; onDismissRotationHint: () => void; theme: 'courtyard' | 'industrial'; onReady: () => void }) {
  const industrial = theme === 'industrial';
  const mobile = typeof window !== 'undefined' && window.matchMedia('(max-width: 700px) and (orientation: portrait)').matches;
  return <Canvas shadows dpr={mobile ? [1, 1.25] : [1, 1.65]} camera={{ position: [14, 14, 20], fov: 35 }} gl={{ antialias: true, powerPreference: 'high-performance' }}>
    <color attach="background" args={[industrial ? '#111619' : '#171b1d']} /><fog attach="fog" args={[industrial ? '#1b2225' : '#242726', industrial ? 18 : 20, industrial ? 43 : 48]} /><ambientLight intensity={industrial ? .3 : .32} color={industrial ? '#b8c5cb' : '#ffffff'} />
    <directionalLight castShadow position={[-8, 14, 7]} intensity={industrial ? 1.35 : 1.65} color={industrial ? '#aabac1' : '#ffc18b'} shadow-mapSize={[1024, 1024]} /><pointLight position={[5, 5, -2]} intensity={industrial ? 12 : 18} color={industrial ? '#d08b45' : '#87a5bf'} />
    <Stars radius={50} depth={20} count={industrial ? 42 : 100} factor={1.1} fade speed={.12} /><Terrain industrial={industrial} />{industrial ? <><IndustrialEnvironment /><ChernobylStationLandmark /><FactoryDuskVignette /></> : <><Neighbourhood /><EnvironmentDetails clearPulse={snap.clearPulse} /></>}<Well snap={snap} industrial={industrial} /><CameraFraming mobile={mobile} /><CameraBasis onChange={onViewBasis} />
    {showRotationHint && <RotationHint snap={snap} onDismiss={onDismissRotationHint} />}<SceneReady onReady={onReady} /><ContactShadows position={[0, -.7, 0]} opacity={.65} scale={30} blur={2.5} /><OrbitControls makeDefault target={[0, mobile ? 3.7 : 5, 0]} minDistance={11} maxDistance={34} minPolarAngle={Math.PI * .18} maxPolarAngle={Math.PI * .48} enablePan={false} rotateSpeed={.65} zoomSpeed={.8} />
    <EffectComposer multisampling={0}><N8AO aoRadius={1.15} intensity={.95} /><Bloom luminanceThreshold={.86} intensity={.16} mipmapBlur /><Vignette eskil={false} offset={.25} darkness={.42} /></EffectComposer>
  </Canvas>;
}
