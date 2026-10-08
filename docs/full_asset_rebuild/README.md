# Complete multi-view asset rebuild

The game now uses 111 new runtime GLBs in `game/assets/generated`: the hero and horse, 37 enemy variants, ten NPC bodies, eleven swords, five equipment models and 46 world models. Every export has an editable source in `blender/multiview_rebuild`. The previous runtime model folders and previous Blender model geometry were deleted after replacement, import and gameplay validation.

Open [the complete Godot gallery](gallery.html), [30 practical reference sheets](../../concepts_docs/art/asset_turnarounds_v2/index.html), [final horse/rider/saddle angles](../screenshots/horse-reference/godot/final_multiview/final_contact.png), or [the machine-readable catalogue](catalogue.json). The gallery links every model to its source, concept authority, four-angle render, animation sheet where applicable, and SHA-256. Shared reconstruction lineage is explicit: 111 exports do **not** mean 111 independent neural generations.

## The retained generation approach

Asset Forge at `C:\Users\Tom\Documents\2D_to_3D` accepts reviewed sets of two to six consistent images and calls Microsoft's native TRELLIS `run_multi_image`. All selected views condition one shared reconstruction. The original concept is translated into a neutral isolated sheet, split into individual images and visually checked before generation. Repeated or inconsistent panels are excluded. Hidden surfaces remain inferred design choices; this is not calibrated photogrammetry.

Thirty base subjects were reconstructed across this work, with a second pine generation after diagnosis showed foreground segmentation was deleting its canopy. Common body plans supply explicit species, tier, coat and stature variants. The new swords, armor and small crafted props use clean editable construction where neural output could not produce reliable thin blades, equipment pivots or joinery. No previous model surface is reused. Previous rig names, animation actions and sparse point/weight guides retain gameplay compatibility; the binding templates contain no previous mesh faces or textures.

The Forge source changes are preserved in [the installable source patch](../../tools/asset_generator_multiview_patch/manifest.json). Install them into an existing Forge checkout with `./tools/asset_generator_multiview_patch/Install.ps1`. Its SHA checks and code backups preserve the existing installation. Model weights and Python environments remain local and are not committed. [The earlier controlled experiment](../multiview_pipeline/README.md) documents native execution, attention tests and the limits of the initial quality comparison.

Production settings on this machine are native mesh/color output, stochastic combined conditioning, 25 steps, guidance 5, seed 42, exact chunked SDPA with 256-query chunks, Pascal-compatible native spconv and CPU stage offloading. Background preparation respects meaningful alpha and uses a studio-border mask for white-background sheets instead of deleting leaves with a generic foreground model. Generation queues record the actual jobs and sources in this folder.

## Repairs established by opened renders

- The hero and NPCs were fitted to new body proportions, with separate warrior, smith, keeper and stablemaster reconstruction sources. Stablemaster facing was corrected. Detached NPC bars, floor shells and stray fragments were removed. Long clothing weights were smoothed across legs and torso. Opened attack clips revealed that A-pose reposing moved wrists inside the hand-region cutoff: the cutoff was corrected, upper sleeves were bound to their shoulder/elbow chains, and a game test now verifies that visible hand vertices follow both wrist bones.
- Stonekin shoulder, elbow, hand and head joints were moved to match the reconstructed anatomy. Added rounded back plates were rejected after rear-view inspection. Some local stretching remains in extreme poses; this is transferred skinning rather than artist-authored joint retopology.
- The boar retains its new reconstructed head, tusks, coat and dorsal shape. Fused lower legs and hooves were completely remodeled and rebound. The horse retains its new bay body, head and mane; the thin white tail and fused lower legs were replaced with clean black volume, separate leg chains and hooves.
- The saddle was reconstructed separately and oriented/fitted to the new horse. New bridle, bit and reins follow the horse rig. Final mounted review measured foot-to-stirrup error below 7 mm and hand-to-rein error below 1 mm. Rider, horse and mounted front/side/three-quarter images were opened.
- The pine foreground mask was repaired and reconstruction repeated. An 8,000-triangle candidate failed the shape guard; the 11,996-triangle candidate passed with 1.09% sampled maximum surface error and 0.43% 95th-percentile error. Broad pine silhouettes follow the practical East Asian forest reference.
- Fern and grass were completely remodeled as separated leaflets/blades. Dead tree and bridge were rebuilt after their neural candidates produced exterior shells, detached posts and broken rails. Ground litter now consists of separate curled fallen leaves.
- The fracture keeps reconstructed roots while its fused upper cage becomes seven open bark ribs around a visible emissive core. Its clean cage is a simplified interpretation of the organic concept. Existing wave, damage, collapse and reward contracts remain intact.
- Bandit cuff loops were replaced with clean sleeves/bracers and fitted reconstructed hands. Constant material albedo now survives variant tinting, keeping new cloth/leather brown rather than white.
- Swords have actual blade cross-sections, a recessed fuller, wraps, metal, jade/brass detail and socket-space pivots. Armor, coin aperture, house, tower, shrine and tent were reviewed separately and in game. Vertex albedo is explicitly enabled by the Godot post-import script; copied packed textures are replaced with fresh image storage when authoring tinted variants.

Guarded simplification checks sampled bidirectional surface error, bounds and nonmanifold edges before baking albedo/normal atlases. QuadriFlow is available as a bounded fallback with projection and rebaking. It does not automatically draw production deformation loops. Thin vegetation, badly fused anatomy and structural parts instead receive named clean remodeling. Numerical pass reports are not substitutes for visual inspection; [visual_review.json](visual_review.json) records the opened final exports independently.

## Rebuild and review

```powershell
# Export all current editable sources, apply import settings and refresh hashes.
./tools/build_assets.ps1
# Or export one named model.
./tools/build_assets.ps1 -Asset wayfarer

# Import the game and run its ordinary gates.
./tools/run.ps1 -Test
# All 25 asset/gameplay suites, with per-suite reports and isolated test saves.
python tools/validate_multiview_game.py

# Actual imported materials, four angles, clay/wire, details and clip samples.
python tools/render_full_rebuild.py warrior bay_horse --runtime
python tools/render_full_rebuild.py meadow_wolf --runtime --group mobs
python tools/build_full_rebuild_gallery.py

# A new reviewed Forge generation; serial GPU execution and resumable jobs.
python tools/rebuild_multiview_batch.py --keys warrior --report generation_queue.json
python tools/prepare_full_rebuild.py warrior
python tools/bind_full_rebuild.py warrior
```

Reconstruction and preparation do not deploy a new candidate automatically. After binding, inspect exported views and animation, repair the named problem, then export/update mappings deliberately. `build_multiview_variants.py`, `build_multiview_equipment.py`, `build_multiview_armor.py` and `build_multiview_mount_tack.py` preserve the corresponding authored rebuild recipes. `build_art.ps1` now routes to the current catalogue rather than regenerating retired assets.

## Actual game verification and performance

[gameplay_checks.json](gameplay_checks.json) contains 25 passing suites and 2,767 passing checks with affected asset, world, streaming and integration gates rerun after material, foliage and skinning corrections. These checks exercise real collision, navigation, services, separate equipment, combat, mounting, 153 authored camps, fracture waves/rewards, imported rigs/materials and all manifest hashes. Rendered world and worn equipment captures accompany the isolated asset sheets.

Measured hardware: GTX 1080 8 GB, i7-5820K, 16 GB RAM. Godot 4.7.2 Compatibility, uncapped/vsync disabled, 1920 x 1080, saves disabled, two seconds warmup and eight seconds of real frame samples per scenario. No generation, Blender repair or other Godot test runs alongside the timed profile. Timing uses consecutive process-frame wall-clock intervals, not stale process/physics monitor values.

| Final full replacement profile | Active enemies | Median | 95th percentile | Frames over 16.67 ms | Worst frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| Settlement | 10 | 4.846 ms | 10.123 ms | 0.00% | 15.565 ms |
| Wilderness | 22 | 4.804 ms | 9.769 ms | 0.07% | 17.215 ms |
| Dense authored combat | 34 | 7.555 ms | 15.253 ms | 2.67% | 24.308 ms |
| Mounted travel | about 28 | 6.482 ms | 12.984 ms | 1.39% | 34.302 ms |

The final travel run crossed 86.95 m with 100% mounted samples and no navigation failure. GPU timing averages 3.12 ms in dense combat and 4.08 ms during travel. Consecutive wall-clock frame samples above are authoritative: accumulated Godot process/physics monitor values can be stale and are not used as FPS measurements. Synchronous world initialization took 12.744 seconds.

Before background prefetch, the full replacement baseline reached a 169.854 ms travel frame, and repeated travel reached 97.433 ms. Instrumented diagnosis traced 47-94 ms nested spans to first-use creature scene loading during camp materialization. Dormant camps now prefetch their models at 68 m, before the 44 m wake boundary. Completed loads enter a shared cache without spawning actors or advancing encounter state. The streaming suite checks that behavior. The final normal profile exits without uncollected-resource warnings. Its 34.302 ms maximum still represents a brief hitch; percentile results do not guarantee a locked 60 FPS.

See [the final raw measurements](performance/asset_balance_full_rebuild_final.json), [settlement](performance/asset_balance_full_rebuild_final_settlement.png), [dense combat](performance/asset_balance_full_rebuild_final_dense_combat.png), and [actual mounted travel](performance/asset_balance_full_rebuild_final_mounted_travel.png). These three final game captures were opened and inspected. Baseline, standalone travel, initial prefetch and instrumented diagnosis measurements are retained beside them for comparison.

The current quality/density balance keeps the reduced ordinary expanded packs at three members and solo elites at one. All authored encounter locations, survivors, deaths, rewards and services remain. Camps wake at 44 m and sleep at 58 m, distant simulation/animation is throttled, navigation requests are bounded and distant shadows/near-camera foliage are managed. No further population reduction was needed after profiling the new library. Stronger assets remain within the measured normal-frame budget, with first-use streaming hitches reduced through background loading and remaining outliers documented.

Older `asset_review`, `forge_rebuild` and `asset_optimization` reports preserve diagnosis/history; their deleted model directories and provisional fallback counts describe previous stages. The current runtime namespace, hashes, editable export manifest and final catalogue are authoritative.
