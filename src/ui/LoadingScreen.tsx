import { useProgress } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState } from 'react';

const statusFor = (progress: number) => {
  if (progress < 24) return 'Preparing neighbourhood...';
  if (progress < 48) return 'Loading buildings...';
  if (progress < 70) return 'Waking the district...';
  if (progress < 91) return 'Placing concrete...';
  return 'Almost ready...';
};

export function LoadingScreen({ sceneReady }: { sceneReady: boolean }) {
  const { active, progress: assetProgress, loaded, total } = useProgress();
  const [staged, setStaged] = useState(4);
  const [leaving, setLeaving] = useState(false);
  const [mounted, setMounted] = useState(true);
  const startedAt = useRef(performance.now());
  const ready = sceneReady && !active && (total === 0 || loaded >= total);

  useEffect(() => {
    const id = window.setInterval(() => setStaged(value => {
      if (value >= 92) return value;
      const increment = value < 45 ? 3.4 : value < 74 ? 1.7 : .65;
      return Math.min(92, value + increment);
    }), 120);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const minimumRemaining = Math.max(0, 1800 - (performance.now() - startedAt.current));
    const leaveTimer = window.setTimeout(() => setLeaving(true), minimumRemaining);
    const unmountTimer = window.setTimeout(() => setMounted(false), minimumRemaining + 650);
    return () => { window.clearTimeout(leaveTimer); window.clearTimeout(unmountTimer); };
  }, [ready]);

  const displayProgress = useMemo(() => {
    if (ready) return 100;
    const real = total > 0 ? assetProgress : 0;
    return Math.round(Math.min(94, Math.max(staged, real)));
  }, [assetProgress, ready, staged, total]);

  if (!mounted) return null;
  return <section className={`loading-screen${leaving ? ' is-leaving' : ''}`} aria-label="Loading Panelki Blocks" aria-busy={!ready}>
    <div className="loading-screen__shade" />
    <div className="loading-screen__content">
      <div className="loading-screen__brand">
        <div><h1>Panelki Blocks</h1><p>Build a kinder skyline.</p></div>
      </div>
      <div className="loading-screen__progress">
        <div className="loading-screen__status" aria-live="polite"><span>{statusFor(displayProgress)}</span><b>{displayProgress}%</b></div>
        <div className="loading-screen__track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={displayProgress}>
          <i style={{ transform: `scaleX(${displayProgress / 100})` }} />
        </div>
      </div>
    </div>
  </section>;
}
