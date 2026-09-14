import { useEffect, useState } from 'react';
import { NAMES } from '../game/config';
import type { Snapshot } from '../game/types';

export type Stage = 'courtyard' | 'industrial' | 'sanatorium';

export function Hud({ snap, onPause, onRestart }: { snap: Snapshot; onPause: () => void; onRestart: () => void }) {
  const showBrand = snap.phase === 'title' || snap.phase === 'playing' || snap.phase === 'clearing';
  const showStats = snap.phase === 'playing' || snap.phase === 'clearing';
  const showActions = snap.phase === 'playing';
  if (!showBrand && !showStats) return null;
  return <>
    <div className="hud-topbar">
      {showBrand && <header className="brand"><span className="brand__mark" aria-label="PB">PB</span><div><h1>Panelki Blocks</h1><p>Build a kinder skyline.</p></div></header>}
      {showStats && <aside className="stats"><div className="score"><span>Score</span><strong>{String(snap.score).padStart(6, '0')}</strong></div><div className="pair"><p><span>Level</span><b>{String(snap.level).padStart(2, '0')}</b></p><p><span>Layers</span><b>{String(snap.layers).padStart(2, '0')}</b></p></div><div className="next"><div className="next__copy"><span>Up next</span><strong>{NAMES[snap.nextKind]}</strong></div><i /></div></aside>}
      {showActions && <nav className="actions"><button onClick={onPause} aria-label="Pause game"><span className="actions__label">Pause</span><span className="actions__icon" aria-hidden="true"><i /><i /></span><kbd>P</kbd></button><button className="quiet" onClick={onRestart}>Restart <kbd>R</kbd></button></nav>}
    </div>
  </>;
}

export function StageSelector({ stage, onChange, disabled = false }: { stage: Stage; onChange: (stage: Stage) => void; disabled?: boolean }) {
  return <div className={`stage-field${disabled ? ' is-switching' : ''}`}><nav className="stage-selector" aria-label="Choose environment" aria-busy={disabled}><button disabled={disabled} className={stage === 'courtyard' ? 'is-active' : ''} aria-pressed={stage === 'courtyard'} onClick={() => onChange('courtyard')}>Courtyard</button><button disabled={disabled} className={stage === 'industrial' ? 'is-active' : ''} aria-pressed={stage === 'industrial'} onClick={() => onChange('industrial')}>Factory Dusk</button><button disabled={disabled} className={stage === 'sanatorium' ? 'is-active' : ''} aria-pressed={stage === 'sanatorium'} onClick={() => onChange('sanatorium')}>Sanatorium</button></nav></div>;
}

export function TouchControls({ act }: { act: (a: string) => void }) {
  return <div className="touch" aria-label="Touch controls"><div className="touch__movement" aria-label="Move piece"><button aria-label="Move left" onPointerDown={() => act('left')}>←</button><button aria-label="Move forward" onPointerDown={() => act('forward')}>↑</button><button aria-label="Move back" onPointerDown={() => act('back')}>↓</button><button aria-label="Move right" onPointerDown={() => act('right')}>→</button></div><div className="touch__rotation" aria-label="Rotate piece"><button aria-label="Rotate X" onPointerDown={() => act('x')}>X</button><button aria-label="Rotate Y" onPointerDown={() => act('y')}>Y</button><button aria-label="Rotate Z" onPointerDown={() => act('z')}>Z</button></div><button className="drop" aria-label="Drop piece" onPointerDown={() => act('drop')}>DROP</button></div>;
}

type OverlayProps = {
  phase: Snapshot['phase']; onStart: () => void; onRestart: () => void; stage: Stage;
  score: number; layers: number;
  stageTransitioning: boolean; onStageChange: (stage: Stage) => void; onStageRestart: (stage: Stage) => void;
};

export function Overlay({ phase, onStart, onRestart, stage, score, layers, stageTransitioning, onStageChange, onStageRestart }: OverlayProps) {
  const [view, setView] = useState<'main' | 'stage'>('main');
  const [pendingStage, setPendingStage] = useState<Stage>(stage);
  useEffect(() => { if (phase !== 'paused' && phase !== 'gameover') setView('main'); setPendingStage(stage); }, [phase, stage]);
  if (phase === 'playing' || phase === 'clearing') return null;

  if ((phase === 'paused' || phase === 'gameover') && view === 'stage') {
    const stageName = pendingStage === 'industrial' ? 'Factory Dusk' : pendingStage === 'sanatorium' ? 'Sanatorium' : 'Courtyard';
    return <section className="overlay overlay--paused overlay--stage-change">
      <p className="stamp">Change stage</p><h2>Choose a district.</h2>
      <p>Changing stage will restart your current run.</p>
      <StageSelector stage={pendingStage} onChange={setPendingStage} />
      <div className="overlay__secondary-actions"><button className="quiet" onClick={() => setView('main')}>Cancel</button><button onClick={() => onStageRestart(pendingStage)}>Restart in {stageName}</button></div>
    </section>;
  }

  const isPaused = phase === 'paused';
  const isGameOver = phase === 'gameover';
  return <section className={`overlay overlay--${phase}`}>
    <h2>{phase === 'title' ? 'Build a kinder skyline.' : isPaused ? 'Take a little break.' : 'Your district is full.'}</h2>
    <p>{phase === 'title' ? 'Stack homes, clear layers, make room for more people.' : isGameOver ? "Good planning. Start a fresh neighbourhood when you're ready." : 'Everything will stay exactly where you left it.'}</p>
    {phase === 'title' && <StageSelector stage={stage} onChange={onStageChange} disabled={stageTransitioning} />}
    {isGameOver && <div className="result-summary"><div><span>Score</span><strong>{String(score).padStart(6, '0')}</strong></div><div><span>Layers</span><strong>{String(layers).padStart(2, '0')}</strong></div></div>}
    <button onClick={onStart}>{isPaused ? 'Continue' : phase === 'gameover' ? 'Start again' : 'Start building'}</button>
    {isPaused && <div className="overlay__secondary-actions"><button className="quiet" onClick={onRestart}>Restart run</button><button className="quiet" onClick={() => setView('stage')}>Change stage</button></div>}
    {isGameOver && <div className="overlay__secondary-actions overlay__secondary-actions--single"><button className="quiet" onClick={() => setView('stage')}>Change stage</button></div>}
  </section>;
}
