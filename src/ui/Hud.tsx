import { useEffect, useState } from 'react';
import { NAMES } from '../game/config';
import type { Snapshot } from '../game/types';

export type Stage = 'courtyard' | 'industrial';

export function Hud({ snap, onPause, onRestart }: { snap: Snapshot; onPause: () => void; onRestart: () => void }) {
  const preStart = snap.phase === 'title';
  return <>
    <div className="hud-topbar">
      <header className="brand"><span className="brand__mark">PN</span><div><h1>Panelki Blocks</h1><p>Build a kinder skyline.</p></div></header>
      {!preStart && <aside className="stats"><div className="score"><span>Score</span><strong>{String(snap.score).padStart(6, '0')}</strong></div><div className="pair"><p><span>Level</span><b>{String(snap.level).padStart(2, '0')}</b></p><p><span>Layers</span><b>{String(snap.layers).padStart(2, '0')}</b></p></div><div className="next"><div className="next__copy"><span>Up next</span><strong>{NAMES[snap.nextKind]}</strong></div><i /></div></aside>}
    </div>
    {!preStart && <nav className="actions"><button onClick={onPause}>{snap.phase === 'paused' ? 'Resume' : 'Pause'} <kbd>P</kbd></button><button className="quiet" onClick={onRestart}>Restart <kbd>R</kbd></button></nav>}
  </>;
}

export function StageSelector({ stage, onChange, disabled = false }: { stage: Stage; onChange: (stage: Stage) => void; disabled?: boolean }) {
  return <div className={`stage-field${disabled ? ' is-switching' : ''}`}><span className="stage-field__label">Stage</span><nav className="stage-selector" aria-label="Choose environment" aria-busy={disabled}><button disabled={disabled} className={stage === 'courtyard' ? 'is-active' : ''} aria-pressed={stage === 'courtyard'} onClick={() => onChange('courtyard')}>Courtyard</button><button disabled={disabled} className={stage === 'industrial' ? 'is-active' : ''} aria-pressed={stage === 'industrial'} onClick={() => onChange('industrial')}>Factory Dusk</button></nav></div>;
}

export function TouchControls({ act }: { act: (a: string) => void }) {
  return <div className="touch" aria-label="Touch controls"><div className="touch__movement" aria-label="Move piece"><button aria-label="Move left" onPointerDown={() => act('left')}>←</button><button aria-label="Move forward" onPointerDown={() => act('forward')}>↑</button><button aria-label="Move back" onPointerDown={() => act('back')}>↓</button><button aria-label="Move right" onPointerDown={() => act('right')}>→</button></div><div className="touch__rotation" aria-label="Rotate piece"><button aria-label="Rotate X" onPointerDown={() => act('x')}>X</button><button aria-label="Rotate Y" onPointerDown={() => act('y')}>Y</button><button aria-label="Rotate Z" onPointerDown={() => act('z')}>Z</button></div><button className="drop" aria-label="Drop piece" onPointerDown={() => act('drop')}>DROP</button></div>;
}

type OverlayProps = {
  phase: Snapshot['phase']; onStart: () => void; onRestart: () => void; stage: Stage;
  stageTransitioning: boolean; onStageChange: (stage: Stage) => void; onStageRestart: (stage: Stage) => void;
};

export function Overlay({ phase, onStart, onRestart, stage, stageTransitioning, onStageChange, onStageRestart }: OverlayProps) {
  const [view, setView] = useState<'main' | 'stage'>('main');
  const [pendingStage, setPendingStage] = useState<Stage>(stage);
  useEffect(() => { if (phase !== 'paused') setView('main'); setPendingStage(stage); }, [phase, stage]);
  if (phase === 'playing') return null;

  if (phase === 'paused' && view === 'stage') {
    const stageName = pendingStage === 'industrial' ? 'Factory Dusk' : 'Courtyard';
    return <section className="overlay overlay--paused overlay--stage-change">
      <p className="stamp">Change stage</p><h2>Choose a district.</h2>
      <p>Changing stage will restart your current run.</p>
      <StageSelector stage={pendingStage} onChange={setPendingStage} />
      <div className="overlay__secondary-actions"><button className="quiet" onClick={() => setView('main')}>Cancel</button><button onClick={() => onStageRestart(pendingStage)}>Restart in {stageName}</button></div>
    </section>;
  }

  const isPaused = phase === 'paused';
  return <section className={`overlay overlay--${phase}`}>
    <p className="stamp">Panelki neighbourhood plan</p>
    <h2>{phase === 'title' ? 'A brighter block starts here.' : isPaused ? 'Take a little break.' : 'Your district is full.'}</h2>
    <p>{phase === 'title' ? 'Stack homes, clear layers, and make room for one more neighbour.' : phase === 'gameover' ? 'Good planning. Start a fresh neighbourhood whenever you are ready.' : 'Everything will stay exactly where you left it.'}</p>
    {phase === 'title' && <StageSelector stage={stage} onChange={onStageChange} disabled={stageTransitioning} />}
    <button onClick={onStart}>{isPaused ? 'Continue' : phase === 'gameover' ? 'Start again' : 'Start building'}</button>
    {isPaused && <div className="overlay__secondary-actions"><button className="quiet" onClick={onRestart}>Restart run</button><button className="quiet" onClick={() => setView('stage')}>Change stage</button></div>}
    {phase !== 'title' && <div className="keys"><span><kbd>Arrows</kbd> move · <kbd>X Y Z</kbd> rotate · <kbd>Drag / scroll</kbd> view</span></div>}
  </section>;
}
