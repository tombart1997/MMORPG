# Practical references and combined-image asset generation

The existing Forge at `C:\Users\Tom\Documents\2D_to_3D` now supports reviewed sets of 2–6 individual views and native TRELLIS conditioning of one shared 3D mesh. Eight production reference sheets were generated from the project concepts, opened and inspected. Boar and horse prototypes were reconstructed with real inference, optimized, rendered from four angles and inspected inside Godot. This is a tested generator improvement with representative prototypes, not a new production rebuild of every game model.

Open the [reference gallery](../../concepts_docs/art/asset_turnarounds_v2/index.html), [current Forge preview](http://127.0.0.1:8743/?asset=9bd5513739b9), [final Godot render sheet](evidence/boar_corrected_runtime.png) or [in-game mesh-load test](evidence/asset_balance_multiview_game_grounded25_dense_combat.png).

## Practical interpretation of the concepts

| Asset | Selected generation views | Inspection and correction |
| --- | --- | --- |
| Ironhide boar | Front, left, back, three-quarter, right | Stocky body, four separated legs, paired tusks and dorsal reeds. Opposite flank added after inspecting incomplete color coverage. |
| Bay horse | Front, left, back, three-quarter | Removed invented white facial blaze and exaggerated muscles. Plain bay face, black mane, tail and lower legs. Horse and rider remain separate. |
| Ironvow warrior | Front, left, back, three-quarter | Neutral A-pose, empty hands, separated feet; consistent lamellar armor and sash. Back costume details are inferred. |
| Meadow wolf | Front, left, back, three-quarter | Consistent lupine proportions, cream chest and inner legs, amber eyes and neutral stance. |
| Watchtower | Front, right, three-quarter | Rear panel omitted because it loses the ladder. Structural straightness still needs mesh inspection. |
| Fern | Front, overhead | Other panels repeat the front too closely; excluded. Thin leaves may need clean cards instead of solid neural geometry. |
| Reed spider | Front, left, overhead, three-quarter | Eight walking legs distinct from palps; overhead rotated so the nose points up. Check hidden leg attachments in the mesh. |
| Blacksmith | Front, right, back, three-quarter | Corrected mislabeled side and three-quarter views. Neutral limbs and empty hands; tools remain independent. |

Each set archives its original concept authority, exact prompt, whole sheet, deterministic individual crops, input hashes, angle labels and inspection notes in [catalog.json](../../concepts_docs/art/asset_turnarounds_v2/catalog.json). Approval here records consistency of **input images**, not acceptance of the resulting mesh. Generated unseen surfaces are design interpretations, not measured evidence.

## What changed in Forge

- **Actual combined inference:** Microsoft's native `run_multi_image` combines predictions into one sparse structure and structured latent. `multidiffusion` uses every image at every sampling step; `stochastic` cycles conditions across steps. It does not generate independent meshes and average them. This inference wrapper is not calibrated photogrammetry and cannot reconcile contradictory references automatically.
- **Windows GTX 1080 support:** isolated Python 3.11, PyTorch 2.5.1 CUDA 11.8, native Pascal-compatible spconv kernels, exact chunked PyTorch SDPA and model-stage CPU offloading. Numerical tests check full-key attention equivalence and separation of sparse batches. No inference mocks or replacement geometry were used for the measured candidates.
- **Reference controls:** assign each angle once, save and review a set, select it in Workbench, choose conditioning mode, steps and guidance. Duplicate images, duplicate angles, foreign references, changed pixels and unapproved sets are rejected. Jobs and resumes freeze the configuration and exact image hashes.
- **Material transfer:** optional orthographic projection uses foreground masks, normals and BVH visibility. It accounts for Blender's Z-up import transform and glTF/Godot Y-up world axes. Perspective images condition shape but are excluded from approximate color projection. Native colors remain where no usable reference covers the surface.
- **Godot export:** explicit normals, one `COLOR_0` layer and a documented `-vcol` material hint fix unshaded/white imports. Simplification of vertex-painted surfaces now bakes the high-detail field into a UV atlas instead of discarding it. Baking matches Godot's sRGB vertex-color interpretation, including Blender copied material names, and removes redundant vertex layers to avoid double tinting.
- **Resumable expensive stages:** a hash-checked native checkpoint retains the mesh and masks if later projection fails. Changed images, conditioning settings or geometry adapter invalidate it. Completed outputs, original code copies and earlier candidates remain available.

TripoSR and TripoSG still accept one image. Their selectors disable combined-view controls. Paid generation remains disabled. TRELLIS generates geometry and native base color; it does not provide a production rig, calibrated cameras, complete PBR maps or guaranteed clean deformation topology.

## Measured reconstruction and visual findings

GTX 1080 8 GB, i7-5820K, approximately 16 GB RAM; Blender 5.2.2 LTS and Godot 4.7.2. Same boar, pinned model, seed 42 and guidance 5:

| Native inference | Steps per stage | Shape inputs | Source triangles | Time | Peak PyTorch CUDA allocation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Single image | 12 | 1 | 533,740 | 162.45 s | 6,643.1 MiB |
| Combined images | 12 | 3 | 506,750 | 291.19 s | 6,637.5 MiB |
| Full Forge combined job | 25 | 4 | 523,056 | 632.08 s | 6,692.2 MiB |
| Horse, native stochastic shared conditioning | 25 | 4 | 322,916 | 221.30 s | 6,218.3 MiB |

The matched [single](evidence/boar_single.png) and [three-view](evidence/boar_multi.png) geometry looks similar. These tests establish genuine combined-input execution; they do not establish a universal quality advantage over TRELLIS single-image inference. The four-view candidate preserves recognizable tusks, four legs, ears and dorsal reeds better than the [current game fallback](evidence/boar_current_game.png), but does not reproduce the fine plates of the concept as geometry.

The [native full-resolution output](evidence/boar_four_native.png) had muddy surface color. Direct vertex-color simplification then blurred it further. Inspection led to orthographic color projection and a baked 1024px atlas. A further material correction added the reviewed opposite-side image without rerunning or changing geometry. **The measured geometry used four input images; the final color repair additionally uses the right-side reference.** Future generation from the selected five-view set consumes all five images. [Provenance](evidence/all_sides_provenance.json) records that distinction.

Final exported candidate: **17,983 triangles**, one material, one embedded base-color texture, UV0 and normals; no skeleton or clips. The reduction's sampled maximum surface distance was 0.179% of the object diagonal, p95 0.0745%, bounds drift 0.0343%, and nonmanifold-edge count zero. These shape checks do not measure artwork fidelity. Godot imported the exact output successfully with automatic import LOD generation disabled. The [optimization report](evidence/final_optimization.json) and [technical validation](evidence/final_godot_technical.json) retain the actual results.

The final [front, side, back and three-quarter sheet](evidence/boar_corrected_runtime.png) was opened after export. Body outline and tusks survive reduction; texture detail is visible at normal inspection scale. Remaining defects include soft eye/muzzle detail, uneven plate coverage, approximate texture registration and small spike/underbody artifacts. The 11m tile uses native reconstruction scale rather than a production creature height; the in-game fixture explicitly scales it by 1.8 and places its feet on terrain. This is not a rigged, animation-approved replacement.

## Runtime evidence and practical quality budget

The final 25-instance Godot validation grid at 960×640 measured 0.559 ms average and 0.701 ms p95 over 180 frames after warm-up, with 449,803 average rendered primitives. This small static grid is not a whole-game FPS prediction.

The real outdoor level was also measured at **1920×1080**, uncapped Compatibility rendering, with **34 active actors and 153 authored camps**. A separate test adds 25 static candidate meshes while the existing AI/combat remains active; it does not replace creatures or add their animation cost. Cold baseline: 11.967 ms median, 25.36 ms p95, 3.852 ms GPU. Warm baseline: 10.089 ms median, 25.672 ms p95, 3.816 ms GPU. The initial additional-mesh run: 9.361 ms median, 22.499 ms p95, 4.208 ms GPU. Faster total timing in that run is run-to-run/warm-up variation, not an optimization claim. The final grounded fixture measured **10.349 ms median, 24.835 ms p95 and 4.220 ms GPU**, with 21.15% of samples exceeding 16.67 ms. [Its report](evidence/asset_balance_multiview_game_grounded25.json) and [screenshot](evidence/asset_balance_multiview_game_grounded25_dense_combat.png) show the actual test.

The mesh load has modest measured GPU cost on this machine; existing combat frame spikes still exceed the 16.67 ms budget. CPU/AI/physics behavior and eventual skinning need separate profiling. No extra density reduction or retopology was justified by this static asset test. Start creature studies near **18k triangles and a 1024px atlas**, retain source meshes and compare silhouettes before moving budgets higher. This is a measured starting point for this boar, not a verified budget for every species, rig or environment asset.

The boar prototype is imported under `game/review_assets/multiview_ironhide_boar`. Gameplay model mappings and saves are unchanged. The existing `ActorVisual` requires a species skeleton and idle/run/attack/hit/death clips, so directly installing this static candidate as a creature would break its contract. Human and other prepared sets are ready as generator inputs; their new meshes were not generated or animation-approved in this pass.

The horse is a second actual four-input reconstruction, using native stochastic view cycling. It reduced to **17,995 exported triangles** with a 1024px atlas. Its generated forward axis initially pointed +X, so automatic projection put mane/tail colors across the body. That [projected coat](evidence/horse_projected.png) was rejected after opening the Godot renders. The final [horse prototype](evidence/horse_runtime.png) keeps native colors and uses the existing processing orientation control, `source_rotation_degrees: [0, 0, 90]` in Blender coordinates, to face Godot -Z. **Reference projection now defaults off and requires orientation inspection before opting in.** This regression is a concrete limitation of uncalibrated multi-image generation, not something additional resolution fixes. The final 25-copy grid measured 0.639 ms average and 0.718 ms p95; import passed with no errors. The horse is imported under `game/review_assets/multiview_bay_horse`; soft eye/muzzle detail, a pale forelock stripe, ribbon-like tail, species rig, hoof/gait review, saddle and mounted rider still need work before it can replace the working mount. [Its diagnosis](evidence/horse_diagnosis.json) records those limitations against the exact runtime hash.

## Checks and reproducibility

- 33 Forge tests pass, including real API crop rotation, approval/hash gates, one combined backend call, frozen resumes, changed-input rejection and native-checkpoint integrity.
- Six TRELLIS/Blender checks cover exact attention, real glTF normals/material/color export, actual orthographic projection in Y-up coordinates, untouched unseen colors, and a real simplification/bake preserving the intended color without multiplying it twice.
- Browser validation passes with no page errors: approved thumbnails, backend switching, conditioning controls, optional projection and omitted panels. Production JavaScript build passes.
- Full real CUDA sparse-convolution probe, four actual native reconstructions, Godot imports, rendered four-angle sheets and whole-game mesh-load tests were completed. Technical validity remains separate from visual acceptance.

The [source patch bundle](../../tools/asset_generator_multiview_patch/manifest.json) contains reviewable copies of the installed generator changes. Its `Install.ps1` verifies hashes and backs up existing code before copying files into an existing Forge installation. Weights and upstream dependencies remain in the isolated generator environment rather than the game repository. Run `scripts/setup_trellis.ps1` there, restart Forge, then use **References → save/review a set → Workbench → TRELLIS → Generate → Process → Godot**. The normal launcher uses its configured port; the development preview is on 8743.

Pinned upstream code: `442aa1e1afb9014e80681d3bf604e8d728a86ee7`; model revision: `25e0d31ffbebe4b5a97464dd851910efc3002d96`. [Microsoft TRELLIS source](https://github.com/microsoft/TRELLIS), [official model](https://huggingface.co/microsoft/TRELLIS-image-large), [spconv source](https://github.com/traveller59/spconv), and [Godot material import hints](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/node_type_customization.html) document the underlying capabilities and import behavior. Code/model use MIT licenses; FlexiCubes uses Apache 2.0. No paid 3D generation services were called; image-tool usage is separate from backend service credits.
