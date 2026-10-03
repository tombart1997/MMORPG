# Ironfield world visual pass

## Audit before changes

The active project uses Godot's Compatibility renderer. Existing local character,
creature, progression and painted UI changes are retained. No reference attachments
were supplied in this turn; the target is the user's described classic MMORPG art
direction and the project's existing painted palette.

- **Terrain:** Briarwood is a single unindexed 2 m grid. Its elevation is almost
  entirely distance from roads/camps, making flat floors and repetitive berms.
  Cinderfall is a plane with raised colored disks and rectangular glowing strips.
- **Assets:** Briarwood's regular boulder rows use scaled low-resolution spheres.
  General trees have cylindrical branches and seven spherical crown lobes. The
  Amber Scar has an existing authored Blender kit, confined to one encounter.
  Cinderfall scatters five-sided cones and has spherical boundary rocks.
- **Materials:** Briarwood already has a reusable painted atlas and six terrain
  layers. This is useful foundation, but repeated high-frequency detail and smooth
  primitive silhouettes dominate. Cinderfall uses nearly all flat colors.
- **Composition:** Random scatter, straight rock rows and repeated boundaries
  expose the generation rules. Camp clearings and current roads must remain usable.
  Labels currently do more orientation work than physical landmarks.
- **Lighting:** Warm sun and color ambient light exist. The Amber Scar overwrites
  global light/fog every frame, even when the camera is outside the grove. Trees
  cast huge opaque lobe shadows. Compatibility does not provide screen-space AO.
- **Camera:** A 60-degree third-person camera supports orbit and zoom. Close canopy
  clearance already uses pixel dithering. Preserve controls and readable combat.
- **Actors:** Existing rigged Jade creatures and hero assets are substantially
  stronger than the surroundings. Retain their rigs, clips, sockets and combat
  timing. Improve pack variation only in presentation, and ground actors visually.
- **Performance:** Existing camp streaming and animation throttling are valuable.
  General scenery uses 24 m MultiMesh chunks, but rocks use individual nodes and
  terrain lacks chunk culling. Preserve streaming, shared materials and navigation.

## Review workflow

`game/tests/world_visual_review.gd` captures the actual rendered game at fixed
settlement, first hunting ground, outer route, Amber Scar and Cinderfall viewpoints.
It disables persistence, uses the production scenes, and measures uncapped wall
frame times. Run with Godot's normal renderer, never headless for visual review.
Each pass is inspected before deciding the next three corrections.

Review notes and final validation results are appended as passes finish.

## Rendered iterations

Every row below corresponds to a real Godot run, followed by inspection of the
captured images. The six production viewpoints were retained across passes. For
Cinderfall, the camera's foot position follows the new terrain height.

| Pass | Three weaknesses found in the rendered result | Corrections made next |
|---|---|---|
| Baseline | Rounded rock walls; spherical tree crowns; flat, untextured Cinderfall | Authored slate rocks, branching leaf-spray trees and an editable reusable kit |
| 1 | Large rocks occlude combat; stone is too pale; regular object rows remain obvious | Camera clearance, painted stone response, terrain shoulders and irregular ridge groups |
| 2 | Atmosphere washes Cinderfall pink; new elevations invalidate one review pose; landscape lacks orienting vertical forms | Cooler haze/fill, terrain-aware review camera, shrines/ruins/watchtowers and mountain belts |
| 3 | Outer cliffs repeat like a palisade; outpost tent reads as flat boards; actors need softer contact | Broader shelf cliffs with irregular spacing, sagged Blender canvas, shared soft contact shadows |
| 4 | Sparse perimeter reveals sky below terrain; the first hunt needs a physical focal point; a navigation shortcut runs into wolves | Foothill skirt and matching terrain border, roadside shrine, slate shoulder separating lane and clearing |
| 5/final | Camera clearance needs to remain reliable; additional detail must keep its LODs; slope contact needs alignment | Larger basin rocks receive convex collisions, imported LODs are retained, contact shadows align to the actual floor normal |

The final assets replace general tree, rock, shrub, fern, grass, deadwood and tent
presentation. Small existing camp details and the already authored Amber Scar kit
remain. Settlement services, camp definitions, loot tables, character rigs,
animation timings, controls, progression, saves and painted UI retain their owners.
The sun direction is now stable when crossing the grove instead of rotating with
the camera's proximity. Cinderfall item drops follow terrain height.

## Assets and rendering

`blender/scripts/build_world_kit.py` rebuilds 17 assets in `blender/world_kit/` and
`game/assets/world_kit/`. These are original mesh constructions using existing
project texture art. Trees have bent trunks, flared roots, asymmetric limbs and
individual leaf sprays. Stone has broken faces, split shelves and talus. The kit
also includes two cliff formations, a broken arch, a shrine and a timber watchtower.

- Each runtime asset has one mesh, usually one or two material surfaces; shrine has four.
- Trees use 4,698 triangles, rocks 318, ferns 574, grass 26, the broken arch 810,
  shrine 280, watchtower 504 and tent 308. Full budgets are in the kit manifest.
- Imported mesh LODs and shadow meshes survive the runtime cache. Materials are
  shared, and repeated scenery remains in 24 m MultiMesh chunks.
- Terrain now uses indexed 24 m chunks, shared border samples and smooth matching
  normals, with independent frustum culling and actual collision/navigation baking.
- Distant mountain belts have no collision or shadows. Tiny dressing has no dynamic
  shadows. Existing camp residency and animation throttling are retained.
- Compatibility renderer is retained. Soft mesh contact shadows supplement real
  directional shadows without depending on unavailable screen-space AO.

## Before/after evidence

Open [the comparison viewer](screenshots/visual-pass/review.html) to move the divider
between baseline and final screenshots, or choose an intermediate pass.

| Production view | Baseline | Final |
|---|---|---|
| Briar Crossing | [Image](screenshots/visual-pass/baseline_settlement.png) | [Image](screenshots/visual-pass/final_settlement.png) |
| First hunt | [Image](screenshots/visual-pass/baseline_verge.png) | [Image](screenshots/visual-pass/final_verge.png) |
| Outer route | [Image](screenshots/visual-pass/baseline_route.png) | [Image](screenshots/visual-pass/final_route.png) |
| Amber Scar | [Image](screenshots/visual-pass/baseline_amber.png) | [Image](screenshots/visual-pass/final_amber.png) |
| Cinderfall outpost | [Image](screenshots/visual-pass/baseline_outpost.png) | [Image](screenshots/visual-pass/final_outpost.png) |
| Cinderfall basin | [Image](screenshots/visual-pass/baseline_basin.png) | [Image](screenshots/visual-pass/final_basin.png) |

## Measurements

Godot 4.7.2, NVIDIA GTX 1080, Compatibility renderer, 1280 x 720, vsync disabled,
uncapped wall-frame samples: 60 warmup frames followed by 120 measured frames per
view. Production AI, animation and UI remain active. Samples are short desktop
measurements, not controlled GPU-only benchmarks; random enemy wandering can vary.

| View | Before median / p95 | Final median / p95 | Resident enemies |
|---|---:|---:|---:|
| Settlement | 8.37 / 10.98 ms | 8.64 / 13.01 ms | 68 |
| First hunt | 8.14 / 10.86 ms | 8.26 / 10.64 ms | 117 |
| Outer route | 20.49 / 34.94 ms | 16.20 / 22.35 ms | 203 |
| Amber Scar | 15.89 / 22.95 ms | 12.07 / 16.99 ms | 175 |
| Outpost | 4.73 / 6.08 ms | 4.59 / 5.73 ms | 19 |
| Basin | 4.38 / 5.41 ms | 4.57 / 5.25 ms | 19 |

More detailed geometry and longer-range shadows increase Briarwood draw calls.
The busiest reviewed route remains around 62 FPS median; the 95th-percentile frame
time is about 22 ms. Outdoor startup increased from 5.79 to 6.64 seconds due to
terrain sampling/baking. Basin startup decreased from 1.52 to 0.73 seconds after
consolidating the primitive objects. These timings include synchronous startup.

Rebuild assets:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/build_world_kit.py
```

Capture and measure actual rendering:

```powershell
& 'C:/Program Files/Godot/Godot_console.exe' --path game --resolution 1280x720 --script res://tests/world_visual_review.gd -- --label=review
```

Run regression checks with `./tools/run.ps1 -Test`. `-Suite world_landscape`
specifically checks existing floors, normal Cinderfall controller travel, reachable
encounters and grounded rewards.

## Final validation

The complete twenty-suite regression run passed after the landscape and character
motion changes. This includes real melee/skill damage, progression and persistence,
mounted travel, both regions, streaming, extended traversal, hero/creature review,
grounded rewards and the new character attachment checks. Extended traversal
visited 144 groups with a peak of 275 resident actors and no failures.

The traversal review found a new shortcut through an idle wolf after opening up
the hills. A narrow slate shoulder now keeps the navigation route around that
clearing without moving the encounter or blocking the main road. Existing camp,
settlement and fracture floors stay level. Cinderfall click travel and every
encounter's accessibility were checked against the new terrain and collision.

The added player request is covered in [CHARACTER_MOTION_PASS.md](CHARACTER_MOTION_PASS.md):
full-body sword choreography, synchronized equipment sockets and skill effects
connected to the current blade, chest and foot poses. Gameplay timings and the
painted UI remain intact.
