import { useProgress } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';

const PIECES = [
  { x: 68, y: 108, width: 48, height: 25, tone: 'slab' },
  { x: 119, y: 108, width: 47, height: 25, tone: 'tower' },
  { x: 95, y: 80, width: 48, height: 26, tone: 'courtyard' },
  { x: 145, y: 82, width: 43, height: 24, tone: 'prefab' },
  { x: 119, y: 52, width: 47, height: 26, tone: 'brutalist' },
] as const;

const statusFor = (progress: number) => {
  if (progress < 18) return 'Surveying courtyard...';
  if (progress < 36) return 'Pouring concrete...';
  if (progress < 54) return 'Placing first block...';
  if (progress < 76) return 'Stacking the neighbourhood...';
  if (progress < 93) return 'Waking the district...';
  return 'Almost ready...';
};

function MiniPiece({ piece, index, settled, falling }: { piece: typeof PIECES[number]; index: number; settled: boolean; falling: boolean }) {
  const x = piece.x, y = piece.y, w = piece.width, h = piece.height, side = 13;
  const state = settled ? ' is-settled' : falling ? ' is-dropping' : '';
  const style = { '--piece-delay': `${index * 45}ms` } as CSSProperties;
  return <g className={`mini-stack__piece mini-stack__piece--${piece.tone}${state}`} style={style}>
    <polygon className="mini-stack__roof" points={`${x},${y} ${x + w},${y} ${x + w + side},${y - 8} ${x + side},${y - 8}`} />
    <path className="mini-stack__front" d={`M${x},${y}H${x + w}V${y + h}H${x}Z`} />
    <path className="mini-stack__side" d={`M${x + w},${y}L${x + w + side},${y - 8}V${y + h - 8}L${x + w},${y + h}Z`} />
    {[.22, .56, .82].map((offset, window) => <rect key={window} className={`mini-stack__window ${window !== 1 ? 'mini-stack__window--lit' : ''}`} x={x + w * offset - 3} y={y + 8} width="5" height="7" rx=".6" />)}
    <rect className="mini-stack__window" x={x + 8} y={y + 8} width="5" height="7" rx=".6" />
  </g>;
}

function MiniStack({ progress, completed }: { progress: number; completed: boolean }) {
  const settledCount = completed ? PIECES.length : Math.min(PIECES.length - 1, Math.floor(progress / 20));
  return <div className={`mini-stack${completed ? ' is-complete' : ''}`} aria-hidden="true">
    <svg viewBox="0 0 260 160" role="presentation">
      <ellipse className="mini-stack__ground" cx="130" cy="139" rx="67" ry="10" />
      {PIECES.map((piece, index) => <MiniPiece key={piece.tone} piece={piece} index={index} settled={completed || index < settledCount} falling={!completed && index === settledCount} />)}
    </svg>
  </div>;
}

export function LoadingScreen({ sceneReady, onReveal }: { sceneReady: boolean; onReveal: () => void }) {
  const { active, progress: assetProgress, loaded, total } = useProgress();
  const [staged, setStaged] = useState(4);
  const [leaving, setLeaving] = useState(false);
  const [mounted, setMounted] = useState(true);
  const [artworkReady, setArtworkReady] = useState(false);
  const [completedStack, setCompletedStack] = useState(false);
  const startedAt = useRef(performance.now());
  const ready = artworkReady && sceneReady && !active && (total === 0 || loaded >= total);
  const presentationReady = ready && staged >= 92;

  useEffect(() => {
    const image = new Image();
    image.onload = () => setArtworkReady(true);
    image.onerror = () => setArtworkReady(true);
    image.src = '/assets/loading/panelki-loading-bg.webp';
    if (image.complete) setArtworkReady(true);
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => setStaged(value => {
      if (value >= 92) return value;
      // Five slow milestones give every miniature building time to land before the next appears.
      const elapsed = performance.now() - startedAt.current;
      return Math.min(92, 4 + elapsed / 5600 * 88);
    }), 80);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (!presentationReady) return;
    // Let the last mini building settle, then hold the finished skyline briefly before reveal.
    const completeTimer = window.setTimeout(() => setCompletedStack(true), 90);
    const leaveTimer = window.setTimeout(() => { onReveal(); setLeaving(true); }, 470);
    const unmountTimer = window.setTimeout(() => setMounted(false), 820);
    return () => { window.clearTimeout(completeTimer); window.clearTimeout(leaveTimer); window.clearTimeout(unmountTimer); };
  }, [onReveal, presentationReady]);

  const displayProgress = useMemo(() => {
    if (presentationReady) return 100;
    const real = total > 0 ? assetProgress : 0;
    // Asset loading can complete in a single browser tick. Allow it to lead slightly,
    // but never enough to skip a building's landing animation.
    return Math.round(Math.min(94, Math.max(staged, Math.min(real, staged + 7))));
  }, [assetProgress, presentationReady, staged, total]);

  if (!mounted) return null;
  return <section className={`loading-screen${leaving ? ' is-leaving' : ''}`} aria-label="Loading Panelki Blocks" aria-busy={!ready}>
    <div className="loading-screen__shade" />
    <div className="loading-screen__content">
      <div className="loading-screen__brand"><h1>Panelki Blocks</h1><p>Build a kinder skyline.</p></div>
      <MiniStack progress={displayProgress} completed={completedStack} />
      <div className="loading-screen__progress">
        <div className="loading-screen__status" aria-live="polite"><span>{statusFor(displayProgress)}</span><b>{displayProgress}%</b></div>
        <div className="loading-screen__track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={displayProgress}><i style={{ transform: `scaleX(${displayProgress / 100})` }} /></div>
      </div>
    </div>
  </section>;
}
