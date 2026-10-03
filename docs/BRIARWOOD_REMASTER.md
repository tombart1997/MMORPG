# Briarwood March remaster and performance

The existing layout, settlement locations, roads, navigation obstacles, spawn definitions, progression, grouped aggression and ornate UI are preserved. A painted six-material terrain blend, organic camp spurs, clustered ground cover, three shared tree silhouettes, constructed timber/plaster/tile buildings and species-specific camp dressing replace the broad flat surfaces and cone trees. The subsequent [character pass](NPC_CHARACTER_PASS.md) brings the village inhabitants into that direction.

## Measured bottleneck

The original expanded map eagerly instantiated 910 combat actors and 30,548 scene nodes. Procedural enemy presentation rewrote materials on individual mesh parts every frame, even when those enemies contributed little to the view. Its many separate mesh submissions also created substantial render/shadow cost.

At the same wilderness position, freezing enemy nodes reduced median wall-frame time from 254.80 ms to 52.45 ms. Turning directional shadows off with enemies running reduced it to 187.89 ms. These ablations identify enemy simulation/presentation and its rendering workload as the main cost; shadows alone do not explain the slowdown. Freezing removes AI, movement, animation and material updates together, so these figures must not be read as an isolated measurement of AI or navigation.

The fix addresses that workload directly:

- Within 30 m, enemies retain full combat AI, navigation, movement and animation. An engaged group stays in this tier regardless of distance.
- Medium actors use .2 s idle AI/presentation intervals and omit dynamic mesh shadows. Combat and pending statuses retain full updates.
- Camps wake within 68 m and unload beyond 84 m. Hysteresis and staggered .2 s checks avoid rapid repeated loading. Far camps retain lightweight authored spawn state.
- Partial health and killed member slots survive unloading. Unloading is blocked by targets, committed attacks, status effects and knockback. Rewards and respawn generation remain authoritative.
- Enemy primitive meshes and base materials are shared. Windup/hit overlays change only on state transitions instead of mutating every part every frame.
- Ground cover and trees use shared MultiMeshes in 24 m chunks, with visibility ranges. Small dressing does not cast shadows. Painted material detail carries most of the added visual work.
- Nearby tree surfaces dither away from the camera, clearing the larger canopy silhouettes without adding gameplay/navigation colliders.

## Benchmark method

`game/tests/remaster_profile.gd` runs real uncapped rendering, rather than synthetic fixed-FPS timing. It disables vsync, locks the player/camera and 1280 x 720 viewport, warms each view for two seconds plus 45 frames, then samples at least 180 frames and five seconds. It saves UI-visible and UI-hidden images plus JSON. The hardware was NVIDIA GTX 1080, Godot 4.7.2 Compatibility/OpenGL renderer. Other desktop activity can affect uncapped wall timings.

The pre-remaster build is preserved at `refs/checkpoints/briarwood-remaster-start` and in `.codex/remaster-baseline`. Its matching settlement/wilderness measurements were captured before implementation. Baseline ablations were subsequently repeated from that checkpoint. Raw results and the final comparison are in [performance/comparison.json](performance/comparison.json).

| View | Before median / p95 | Final median / p95 | Resident enemies before / final | Draw calls before / final |
|---|---:|---:|---:|---:|
| Settlement | 259.75 / 345.23 ms | 12.08 / 20.18 ms | 910 / 68 | 11,681 / 1,503 |
| Wilderness | 254.80 / 321.70 ms | 14.99 / 20.59 ms | 910 / 117 | 10,816 / 1,036 |

The intermediate environment build, before the NPC pass, measured 8.54 ms in town and 8.64 ms in the wilderness. The final scene uses fewer draw calls and nodes than that intermediate scene; rendered GPU time is about 2.3 ms. It also corrects an additional camera-distance throttle so near/engaged enemies follow the full animation tier, adding animation work compared with that intermediate build. These desktop runs are not an isolated measurement of NPC art cost. Engine process/physics/render monitors can overlap or update less frequently; they are retained in JSON but must not be added together as a frame-time breakdown.

The sustained six-district controller route visited 143 of the 153 authored spawn groups, peaked at 267 resident enemies, reached every destination on the normal movement path and released distant populations on returning home. All 910 potential enemies remain defined; nearby groups can still participate in combat.

Reproduce the final measurements with:

```powershell
& 'C:/Program Files/Godot/Godot_console.exe' --path game --resolution 1280x720 --script res://tests/remaster_profile.gd -- --label=review
```

Use `--ablations-only` after the user-argument separator to run only frozen-enemy and shadow checks. Headless or `--fixed-fps` runs are appropriate for regression tests, not FPS measurement.

## Visual review and validation

| Scene | Before | Final |
|---|---|---|
| Settlement, UI hidden | [Before](screenshots/before-settlement.png) | [Final](screenshots/settlement.png) |
| Wilderness, UI hidden | [Before](screenshots/before-wilderness.png) | [Final](screenshots/wilderness.png) |
| Characters in the remastered settlement | [Prototype inhabitants](screenshots/before-characters.png) | [Shared character kit](screenshots/settlement.png) |

Additional actual-world reviews: [Sella](screenshots/sella.png), [Oren](screenshots/oren.png), [player](screenshots/player.png), [fire](screenshots/fire.png), [crossing composition](screenshots/crossing.png), [UI-visible settlement](screenshots/settlement-ui.png) and [UI-visible wilderness](screenshots/wilderness-ui.png). Close face views are also saved alongside these images. The review corrected tinting that obscured clothing layers, Oren's initial beard silhouette, flame layers that hid their bright cores, roof winding and camera obstruction by the new canopy.

Passing regression suites cover melee, skills, character rig/timing, streaming state, normal and mounted travel, NPC dialogue, merchant trading, inventory/equipment, farming, save/load, sanctuary respawn, expanded spawn/loot progression, second-region travel and UI bounds. New streaming, traversal and NPC review checks are available through `tools/run.ps1 -Test -Suite ...` and included in the `all` suite. Gameplay tests and rendered art review are separate: a technical pass alone was not treated as visual approval.

The shared atlases, asset locations and exact built-in image-generation prompts are documented in [GENERATED_ART.md](GENERATED_ART.md).
