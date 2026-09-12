# Verification

Tested on 2026-09-11 with Node 25, Vite 7, Python 3 and Blender 5.2 LTS.

- `npm test`: 3 TypeScript game-engine tests passed, including drop/lock, pause/restart and repeated in-bounds play.
- `npm run build`: TypeScript compilation and Vite production build passed.
- Browser: title state rendered, all five GLBs loaded, Receive Keys started the game, keyboard movement/rotation/drop worked, score changed from 000000 to 000022, and no console warnings or errors were recorded.
- Camera: constrained orbit rotation and wheel/pinch zoom are enabled without camera panning; the browser board is 5 × 4 × 12.
- Alignment: the rectangular grid is drawn at exact half-cell boundaries, blocks render at integer cell centres, and the four vertical posts sit on the outer corners.
- Navigation: horizontal arrow/touch movement is quantized to the current camera-facing axes and was checked after orbiting the view.
- Environment: Blender-generated dead-tree and playground GLBs load and render around the playfield.
- Responsive browser viewport: compact HUD and all eight touch controls rendered without page scrolling.
- Blender export: five modules exported successfully, totaling 252 KB.
- Original Python rules: 9 tests passed, including spawn, collision, all-axis rotation, obstruction, ghost, layer compaction, score/speed, pause, game over, restart and randomized invariants.
- Original Blender operator integration: launch, input dispatch, pause, drop, linked meshes, restart, clear, game over and exit passed.

Known limits: the game is intentionally silent. The production JavaScript bundle is 1.36 MB before gzip because Three.js, React Three Fiber and post-processing ship together. Desktop and mobile visual layouts were inspected in the local in-app browser; physical-device touch performance has not been measured.
