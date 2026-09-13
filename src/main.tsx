import { StrictMode, useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import { createRoot } from 'react-dom/client';
import { Game } from './game/Game';
import { GameScene } from './rendering/Scene';
import { Hud, Overlay, TouchControls } from './ui/Hud';
import type { Stage } from './ui/Hud';
import { LoadingScreen } from './ui/LoadingScreen';
import './styles.css';
import './edge-ui.css';

function App() {
  const game = useMemo(() => new Game(), []);
  const theme = useMemo(() => new URLSearchParams(window.location.search).get('theme') === 'industrial' ? 'industrial' as const : 'courtyard' as const, []);
  const snap = useSyncExternalStore(game.subscribe, game.snapshot);
  const [rotationHintDismissed, setRotationHintDismissed] = useState(false);
  const [sceneReady, setSceneReady] = useState(false);
  const [gameVisible, setGameVisible] = useState(false);
  const dismissRotationHint = useCallback(() => setRotationHintDismissed(true), []);
  const markSceneReady = useCallback(() => setSceneReady(true), []);
  const revealGame = useCallback(() => setGameVisible(true), []);
  const changeStage = useCallback((next: Stage) => {
    const url = new URL(window.location.href);
    if (next === 'industrial') url.searchParams.set('theme', 'industrial'); else url.searchParams.delete('theme');
    window.location.assign(url);
  }, []);
  const view = useRef({ forward: [0, -1] as [number, number], right: [1, 0] as [number, number] });
  const onViewBasis = useCallback((forward: [number, number], right: [number, number]) => { view.current = { forward, right }; }, []);
  const act = useCallback((action: string) => {
    if (action === 'drop') game.drop();
    else if (action === 'pause') game.togglePause();
    else if (action === 'restart') game.restart();
    else if (action === 'x' || action === 'y' || action === 'z') {
      // Renderer maps game [x,y,z] to world [x,z,y], so keep the button labels on world axes.
      const worldAxis: Record<string, 'X' | 'Y' | 'Z'> = { x: 'X', y: 'Z', z: 'Y' };
      if (game.rotate(worldAxis[action])) setRotationHintDismissed(true);
    }
    else {
      const { forward, right } = view.current;
      const moves: Record<string, [number, number, number]> = {
        left: [-right[0], -right[1], 0], right: [right[0], right[1], 0],
        forward: [forward[0], forward[1], 0], back: [-forward[0], -forward[1], 0], down: [0, 0, -1],
      };
      game.move(moves[action]);
    }
  }, [game]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const codeMap: Record<string, string> = { KeyX: 'x', KeyY: 'y', KeyZ: 'z', KeyP: 'pause', KeyR: 'restart', KeyS: 'down' };
      const map: Record<string, string> = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'forward', ArrowDown: 'back', ' ': 'drop', x: 'x', X: 'x', y: 'y', Y: 'y', z: 'z', Z: 'z', p: 'pause', P: 'pause', r: 'restart', R: 'restart', s: 'down', S: 'down' };
      const action = map[e.key] ?? codeMap[e.code];
      if (action || ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', ' '].includes(e.key)) e.preventDefault();
      if (action) act(action);
    };
    addEventListener('keydown', onKey); return () => removeEventListener('keydown', onKey);
  }, [act]);
  useEffect(() => { if (snap.phase !== 'playing') return; const id = setInterval(() => game.tick(), game.interval * 1000); return () => clearInterval(id); }, [game, snap.phase, snap.level]);
  useEffect(() => { if (snap.clearPulse) { document.body.classList.add('cleared'); setTimeout(() => document.body.classList.remove('cleared'), 350); } }, [snap.clearPulse]);
  useEffect(() => {
    let timer = 0; const edge = 150;
    const onMove = (e: PointerEvent) => { const near = e.clientX < edge || e.clientX > innerWidth - edge || e.clientY < edge || e.clientY > innerHeight - edge; document.body.classList.toggle('edge-active', near); clearTimeout(timer); if (near) timer = window.setTimeout(() => document.body.classList.remove('edge-active'), 1400); };
    addEventListener('pointermove', onMove, { passive: true }); return () => { removeEventListener('pointermove', onMove); clearTimeout(timer); document.body.classList.remove('edge-active'); };
  }, []);
  const start = () => snap.phase === 'paused' ? game.togglePause() : game.start();
  return <main className={`phase-${snap.phase} theme-${theme}`}><div className={`game-surface${gameVisible?' is-visible':''}`} aria-hidden={!gameVisible}><GameScene snap={snap} onViewBasis={onViewBasis} showRotationHint={gameVisible&&snap.phase === 'playing' && !rotationHintDismissed} onDismissRotationHint={dismissRotationHint} theme={theme} onReady={markSceneReady} /></div>{gameVisible&&<><div className="grain" /><Hud snap={snap} onPause={() => act('pause')} onRestart={() => act('restart')} />{snap.phase!=='title'&&<div className="caption"><span>5 × 4 × 12</span><p>Drag to orbit · Scroll to zoom<br />Arrows follow the camera.</p></div>}<TouchControls act={act} /><Overlay phase={snap.phase} onStart={start} stage={theme} onStageChange={changeStage} /></>}<LoadingScreen sceneReady={sceneReady} onReveal={revealGame} /></main>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
