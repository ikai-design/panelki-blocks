# Panelki Blocks

Playable browser-based 3D falling-block game about improbable housing and very probable shortages. Blender supplies the modular apartment assets; React, TypeScript and React Three Fiber run the game independently in the browser.

## Run

```bash
npm install
npm run dev
```

Open the local URL printed by Vite. Create a production build with `npm run build`, then inspect it with `npm run preview`.

The default URL renders the residential courtyard. Append `?theme=industrial` to render the alternative **Factory Dusk** environment with the same gameplay, camera and UI.

## Controls

| Input | Action |
| --- | --- |
| Arrow keys | Move across the 5 × 4 floor relative to the current camera view |
| X / Y / Z | Rotate around each world axis |
| Space | Hard drop |
| S | Soft step down |
| P | Pause / resume |
| R | Restart |
| Mouse drag / touch drag | Rotate the camera |
| Scroll / pinch | Zoom the camera |

Touch controls appear on narrow screens. The game is intentionally silent and contains no audio controls.

## Architecture

- `src/game/` — grid rules, pieces, collision, layer compaction, scoring and state machine.
- `src/rendering/` — Three.js scene, GLB instances, ghost blocks, lights, shadows and post-processing.
- `src/ui/` — title, pause, game-over states, HUD and touch controls.
- `public/assets/buildings/` — five standalone GLB façade modules, 252 KB total.
- `scripts/export_assets.py` — repeatable Blender-to-GLB export.
- `Panelki Blocks.blend` — editable source models and the original Blender prototype.

The five fictional building families are Khrushchovka tower, Yugoslav slab, courtyard block, five-story prefab and brutalist high-rise. Each GLB uses reusable geometry and embedded materials for concrete panels, windows, lit rooms, curtains, balcony bands, plants, AC units and roof objects. Gameplay collision remains an integer cell, so façade detail never changes the rules.

The ground is generated procedurally in the browser from a seeded canvas texture, with dirt, ash, burned-grass patches, bump variation and sparse low-poly dry grass. It needs no downloaded texture or Blender export.

`public/assets/facade-atlas.svg` is a lightweight texture-atlas source for future baked variants. The current GLBs use material-separated geometry because it preserves the small stylized details at a lower total asset size than a set of normal/roughness textures. KTX2 would add tooling and runtime weight without benefiting these 252 KB assets.

## Rebuild assets

```bash
npm run export-assets
npm run build-environment
npm run build-industrial-theme
```

This expects Blender at `/Applications/Blender.app`; set `BLENDER_BIN` to another executable when needed. The web build has no Blender runtime dependency.

`build-environment` procedurally models and exports the dead tree and abandoned playground GLBs. The playground includes a sandbox, climbing frame, slide, swing and half-buried tire.

`build-industrial-theme` uses Blender to rebuild the separate Factory Dusk GLB: asphalt apron, sparse chain-link fence, service warehouse, transformer cabinet, exposed conduits, two industrial lamps, weeds and one distant smokestack.

## Test

```bash
npm test
npm run build
python3 test_game.py
/Applications/Blender.app/Contents/MacOS/Blender --background "Panelki Blocks.blend" --python test_blender.py
```

## Production checklist

- [x] Independent browser runtime and static production bundle
- [x] Five optimized GLB asset families
- [x] Keyboard and touch input
- [x] Title, playing, paused and game-over states
- [x] Ghost, hard drop, scoring, levels and next-piece preview
- [x] Evening lighting, fog, AO, bloom, shadows and landing feedback
- [x] Silent interface with no audio controls
- [x] Responsive HUD and mobile controls
- [x] Browser and rule verification without console errors
- [ ] Optional GLB meshopt/Draco delivery after profiling on the deployment host
- [ ] Deployment target and analytics, intentionally left unspecified

The Vite build currently reports a 1.36 MB JavaScript entry (about 413 KB gzip), mostly Three.js and post-processing. This is acceptable for the prototype; route-level splitting would matter once the game gains menus or additional scenes.
