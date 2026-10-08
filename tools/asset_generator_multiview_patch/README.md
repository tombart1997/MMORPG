# Ironfield Asset Forge

A working local image-to-3D workbench: concept references → TRELLIS combined views, TripoSR or TripoSG → Blender → interactive review → GLB/glTF → Godot 4.7 validation. Paid generation is disabled.

## Combined images, tested on this machine

TRELLIS now consumes 2–6 separately prepared and reviewed images into **one shared mesh**. The native `multidiffusion` mode combines every view at every sampling step; `stochastic` cycles views faster. This is shared-latent conditioning, not calibrated photogrammetry. TripoSR and TripoSG remain single-image backends.

Open [the practical turnaround gallery](D:/Games/Metin2Clone/concepts_docs/art/asset_turnarounds_v2/index.html) for 30 inspected sets, or the current development preview at **http://127.0.0.1:8743**. Restarting `Launch.cmd` loads installed changes on the normal configured port. Do not run simultaneous generation jobs from separate preview servers.

1. In **References**, prepare individual front, side, back, opposite-side and/or overhead images. Use the same asset and neutral pose; keep anatomy and thin details fully visible. Mark source concept separately. A contact sheet itself is not a set of individual model inputs.
2. Assign 2–6 distinct angle images under **Combined reference views**, save the set, open its images and record consistency notes. Approve after inspection. Inconsistent panels should be omitted or corrected.
3. In **Workbench**, choose **TRELLIS · combined views**, an approved generation input set, conditioning mode, steps and guidance. The queued job freezes exact image hashes and configuration. Changed pixels cannot silently enter an existing job.
4. Optional **Project reviewed orthographic color details** defaults off. Inspect the generated forward axis first: native inference does not guarantee that its front matches Godot -Z. Projection uses foreground masks, normals and visibility; perspective views require camera calibration and are excluded. Check seams and eye alignment; uncovered surfaces keep native colors. The horse test rejected misregistered projection and retained its native coat, using processing `source_rotation_degrees: [0,0,90]` to correct the forward axis in Blender coordinates.
5. Process the candidate within its triangle budget. When simplifying vertex-painted surfaces, the pipeline now bakes the high-detail color field into a UV atlas with Godot color-space matching. Shape guards retain input geometry if the reduction is unsafe. Inspect the exported result in Godot before acceptance; rigs and animation are separate work.

Run `powershell -ExecutionPolicy Bypass -File scripts/setup_trellis.ps1` for the isolated Python 3.11 environment, pinned MIT model and upstream code. The Windows/Pascal port uses native spconv kernels and exact chunked PyTorch attention; no fake generation or substitute attention. Setup alone does not mark the backend available: a full real multi-image inference and export check must pass.

Measured four-view boar: 25 steps, seed 42, combined conditioning, 632.08 seconds and 6692.2 MiB peak CUDA allocation. The 523,056-triangle source reduced to 17,983 exported triangles with a 1024px base-color atlas. See [actual renders, comparisons and runtime limits](D:/Games/Metin2Clone/docs/multiview_pipeline/README.md). More images do not automatically improve every shape: the matched 12-step single/three-view boars had similar geometry. Surface fidelity, rigging and PBR authoring still need inspection.

Expensive inference retains a hash-checked native checkpoint. A failed projection can resume from the same mesh and masks; changing inputs, geometry adapter or conditioning settings invalidates it. Originals and earlier candidates stay available.

The application and local model are installed in this workspace. Open **http://127.0.0.1:8740** while the server is running. Double-click `Launch.cmd` to start it again.

The quality follow-up installed **TripoSG** and tested the same sword reference. Its clay geometry preserves the compact guard and blade edges better than TripoSR. Choose **TripoSG · local geometry** in the Generation backend selector; the current local sword includes this candidate and the earlier TripoSR outputs. TripoSG is geometry only: textures, UVs and physical material maps must be prepared separately. The measured full application run took about four minutes and peaked at 4.76 GiB of PyTorch-allocated GPU memory. Detailed ornament and inferred hidden surfaces still require review. See [the comparison](data/evidence/reconstruction_comparison.html).

## Reproducible setup

Tested on Windows 10, Python 3.12, Node 24.15, Blender 5.2.2 LTS and Godot 4.7.2. Hardware: GTX 1080 8 GB, i7-5820K, 15.91 GiB physical RAM. The CUDA kernel probe checks the GPU rather than assuming every CUDA wheel supports Pascal.

```powershell
cd C:\Users\Tom\Documents\2D_to_3D
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_triposg.ps1
.\Launch.cmd
```

Python dependencies and npm dependencies are locked. The model uses an isolated `.backends/venv`, PyTorch 2.5.1 + CUDA 12.4, and the upstream TripoSR repository at `107cefdc244c39106fa830359024f6a2f1c78871`. Model weights are pinned to Hugging Face revision `5b521936b01fbe1890f6f9baed0254ab6351c04a`; DINO architecture configuration is pinned separately. Initial setup downloads PyTorch and inference dependencies. First generation downloads model weights and U²-Net background-removal weights; subsequent runs use the local cache. No model subscription or API key is required.

Blender and Godot must be installed separately. They are discovered on PATH. Overrides:

```powershell
$env:BLENDER_PATH = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$env:GODOT_PATH = 'C:\Program Files\Godot\Godot_console.exe'
$env:CONCEPT_GALLERY = 'D:\Games\Metin2Clone\concepts_docs\art_gallery.html'
$env:FORGE_DATA = 'C:\Users\Tom\Documents\2D_to_3D\data'
.\scripts\launch.ps1
```

Use Python 3.12 explicitly; the system's `python` command currently resolves to Python 3.8. The backend installer avoids compiling a CUDA extension on Windows: scikit-image extracts the neural density isosurface on CPU. This still reconstructs the asset from the real pretrained model; it does not build a procedural substitute.

For offline inference after all weights have been downloaded, set `HF_HUB_OFFLINE=1`. Reference images and assets remain on disk. U²-Net checks its own cached weights in `%USERPROFILE%\.u2net`.

TripoSG uses its own dependency overrides in `.backends/triposg-venv` and shares the existing Pascal-compatible PyTorch base read-only. Source is pinned to `fc5c40990181e2a756c4e0b1c2f4d6b5202faf8c`; weights to `2c1c516d22d58db486a058d98d31bb6177344e06` (about 8 GB download). The adapter offloads image encoder/transformer/VAE components to CPU when unused, uses FP16 math attention and 1,024-point decoder chunks, and extracts the real neural field using upstream CPU marching cubes. It does not require Flash Attention, BF16, BRIA RMBG weights or a new CUDA extension. The actual final shape latent is checkpointed before extraction.

On a fresh setup, verify a full TripoSG generation before enabling the adapter:

```powershell
.\.backends\triposg-venv\Scripts\python.exe backends/triposg/runner.py --image path/to/reference.png --output data/experiments/triposg_test --steps 50 --depth 9
```

Successful inference writes `data/triposg_probe.json`; imports alone do not enable an untested backend. In the UI's Pipeline settings, `generation_seed`, `diffusion_steps`, `guidance_scale` and `shape_octree_depth` control TripoSG. TripoSR does not support generation seeds and ignores those diffusion-specific parameters. Both adapters use the same bounded job budget. Increasing extraction resolution samples the field more densely; it does not guarantee recovered engraving. TripoSG texture rebaking is disabled because it has no learned color field.

## Producing an asset

1. Create an asset and choose an editable static prop, equipment, humanoid, creature or environment preset.
2. Upload a PNG/JPEG or select a plate from the configured gallery. Originals are copied unchanged. Drag a crop rectangle at original pixel resolution. Flat-color background masking is available; inspect its thin edges. Local reconstruction uses U²-Net if the input is opaque.
3. Save the design contract: silhouette, proportions, face, costume layers, palette, material character, distinctive details and uncertain hidden surfaces. Additional views are retained. TripoSR consumes one primary view. An uploaded generated turnaround requires an explicit consistency review before it can become primary authority.
4. Click **Reconstruct locally**, or import an existing GLB, Blender file, FBX or OBJ. Imported candidates are explicitly labeled and retain their provenance. Prefer self-contained GLB; uploaded OBJ/FBX files with external textures need those textures embedded beforehand.
5. Run **Process in Blender**. This preserves `source.blend` and `source.glb`, produces `editable.blend` and `runtime.glb`, packs textures, records geometry/UV/weight issues, and optionally exports separate collision, LODs, effect components and glTF files. Repairs, normal recalculation and LOD generation are opt-in. Choose Preserve, Simplify, Balanced or Retopology. Simplify reduces triangles while retaining source UVs/materials; Balanced uses guarded simplification for skinned meshes and automatic quad remeshing for static meshes. Retopology attempts QuadriFlow on either kind, projects the new surface and skin weights, and rebakes material maps. Failed surface/deformation checks retain the source or fall back to simplification. Automatic retopology does not author joint loops or repair anatomy.
6. Inspect textured, clay, wireframe and normal views. Orbit, zoom, display the skeleton, play actual imported animation clips, and compare candidates. Capture evidence or render a 12-view turntable. Geometry statistics are measured from the loaded mesh.
7. Run **Validate in Godot**. The application creates a separate project, imports the GLBs, checks skeletons and clips, captures close-up/gameplay images and animation previews, and measures a 25-instance grid. Godot's automatic LOD generation and mesh compression are disabled for this test. Reports include rendered primitive/draw-call counters, hardware, warm-up and sampling conditions.
8. Record concrete defects and complete the visual checklist. Technical success never accepts an asset. Unresolved defects require a written human override to accept. Download the accepted bundle, or download individual review artifacts before acceptance.

Humanoid/creature presets preserve an imported rig; automatic rig creation and retargeting are unavailable. Import a suitably rigged replacement candidate, or explicitly set `bypass_rigging` for a static use case. Creatures are never assigned a humanoid skeleton automatically. Neutral A-pose references must be supplied by the artist: this model cannot change the pose while guaranteeing identity.

The initial benchmark meshes are read-only copies of existing assets from `D:\Games\Metin2Clone`; those pre-existing assets were constructed procedurally in that project. They test this pipeline and are not represented as image-to-3D generation results. The separate **Sword / local reconstruction** asset is a real TripoSR result using the concept sword crop.

## Independent stages and recovery

One background worker prevents concurrent Blender/model work from exhausting this machine. Jobs persist in SQLite; each asset has an atomic JSON manifest. A restart marks unfinished jobs interrupted, and **Resume stage** uses the original input/settings snapshot. Completed source artifacts remain available. Failed local generation resumes its saved neural and geometry checkpoints. Blender/Godot stages rerun from their retained stage inputs. Processing a different material variant does not call the reconstruction model.

**Rebake texture atlas** reuses a locally generated candidate's scene-code and geometry checkpoints. It can change atlas resolution without rerunning neural reconstruction or surface extraction. It queries the original base-color field; it does not provide a new texture prompt, recover detail, or synthesize PBR maps. Both candidates are retained. Texture rebaking normalizes legacy candidates to the current +Y-up, -Z-front convention.

Generation is bounded to three new attempts per asset; subsequent attempts need a recorded reason. Recovery of a failed attempt does not count as a new candidate attempt. There are no automatic generation batches or paid retries. Cancellation terminates the current subprocess and keeps finished files. Each subprocess has a timeout; logs and checkpoints are linked in the interface.

`config/presets.json` is editable. The per-asset Pipeline editor exposes its stages and settings. Review stages are human gates. To replace a stage, import a new candidate and run the following supported stages. There is no arbitrary executable plugin editor in the UI.

Useful settings:

- `triangle_budget`: target enforced by successful reductions. Surface/deformation checks take priority: a rejected reduction can retain an above-budget source, explicitly reported for review.
- `optimization_mode`: `preserve`, `simplify`, `balanced`, or `retopology`. Existing assets without this setting default to Preserve. New presets select an appropriate guarded mode.
- `max_surface_error`: maximum bidirectional surface deviation divided by the source bounding-box diagonal; default 0.02, with a 95th-percentile limit of half that value. Skinned candidates are also compared with their retained source at three poses in each imported NLA clip. These numerical comparisons do not certify anatomy.
- `bake_normal_map`: bake source surface normals when replacing UVs. Quad remeshing automatically transfers existing linked normal detail. Base color, roughness, metallic and emission color are transferred without studio lighting. Constant opacity and culling are retained. Textured/mixed transparency, unsupported mixed shaders or varying emission strength retain the source.
- QuadriFlow runs in an isolated Blender worker with a 90-second deadline per mesh. A timeout selects the simplification fallback. Windows workers exit if their parent processing job is cancelled.
- `generate_lods` and `lod_ratios`: separate opt-in LOD exports; skinned meshes are skipped pending deformation-aware optimization.
- `repair_degenerate`: remove zero-area faces while preserving the original source and remaining weights.
- `recalculate_normals`: explicit derived-mesh normal correction.
- `texture_resolution`: 1024/2048/4096; Blender downsizes existing textures; topology replacement can bake new UV atlases at this size. Increasing resolution does not recover source detail.
- `source_rotation_degrees`: explicit Blender-space orientation correction; default `[0,0,0]`. New TripoSR output already uses +Y up, -Z front.
- `front_axis`: `-Z` or `+Z` for review framing; no geometry is changed by this setting.
- `material_variant`: `{ "roughness": 0.75, "emission": [0.03,0.05,0.1], "strength": 0.1 }`. Adjusts constants without discarding linked roughness maps or reconstructing geometry.
- `attachment`: `{ "name": "grip_socket", "location": [0,0,0] }` adds a named socket.
- `equipment_asset` / `weapon_attachment`: separate weapon asset ID and Godot bone/position/rotation convention; alignment still needs motion review.
- `separate_effects`: exports pre-existing objects named core/effect/glow/shard separately from structure. It does not infer semantic parts in a single generated mesh.

## Evidence and validation

See [VALIDATION.md](VALIDATION.md) for the completed benchmark reports and concrete visual defects. All asset data lives under `data/assets/<id>/`:

```text
manifest.json                  provenance, references, candidates, review, hashes
references/                    untouched originals and prepared crops
imports/                       untouched imported source meshes
generated/<job>/               actual model outputs and neural/geometry checkpoints
processed/<job>/               Blender sources, exports, inspection, previews
godot/<job>/                   runnable engine project and measured evidence
logs/                          subprocess logs
requests/                      frozen Blender processing settings
```

Open a validation scene interactively:

```powershell
.\scripts\open_godot.ps1 -AssetId <id-from-manifest>
```

Right-drag orbits, the wheel zooms, and Space cycles imported clips. The interactive mode stays open; automatic benchmark mode exits after recording evidence.

Verify software:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd run build
py -3.12 scripts/browser_validation.py
```

The browser verification uses the installed Chrome and Playwright. Install `requirements-dev.txt` in a separate Python 3.12 development environment if needed. `scripts/seed_benchmarks.py` copies this user's references and existing meshes; `scripts/run_benchmarks.py` exercises the real stages against the running server. It leaves all assets pending human review. `scripts/collect_validation.py` verifies current hashes, imports, image dimensions and exported LOD counts, then rebuilds the evidence report. `scripts/record_benchmark_review.py` records the supplied advisory benchmark findings; do not run it after starting your own review because it replaces those benchmark review notes.

## Current limits

TripoSR is a practical compatible starting point, not a promise of concept-exact production assets. Fine ornament, thin sword guards, faces, layered clothing and hidden surfaces remain difficult. Its 512 px conditioning loses information even when the original is preserved. Base color can include painted lighting; no physical metallic/roughness/normal maps are invented.

Automatic guarded QuadriFlow retopology and projection/PBR transfer for supported materials are available; they do not produce artist-authored joint loops. General UV overlap detection, arbitrary shader/alpha baking, animation retargeting, autorigging, automatic anatomy repair and generative pose editing remain unavailable. Source UVs/materials/rigs are retained, and rejected reductions restore them. Background removal and part separation need review. Collision is a separate convex hull, which may be unsuitable for a concave environment piece. No vision-service API is configured; benchmark image inspection is recorded as advisory evidence.

The Meshy class retains the documented payload/capability contract as an optional disabled adapter. Its generation method rejects before making a request. This delivery does not claim a tested live Meshy integration. No keys are stored or used.

GLB validation checks binary/accessor bounds, finite geometry, degenerate triangles, authored normals, collapsed/missing UVs, missing external textures, weights, joint indices, inverse-bind counts and animation time ordering. It does not certify topology quality, internal visibility, deformation or watertightness. Visual acceptance is bound to the runtime hash. Source and runtime artifacts can be downloaded separately without labeling them production ready.

## Whole-game quality and performance calibration

The current integrated diagnosis/repair interface is available at **http://127.0.0.1:8742**. Older task instances were stopped. Restart the normal launcher to use its usual port. See [the installed diagnosis and replacement workflow](docs/diagnosis_repair.md).

The final Ironfield replacement library uses roughly 12,000-18,000 triangles for ordinary creatures, 23,983 for the hero and 13,852 for the horse. Shape guards retain higher budgets when reduction damages visible features. At 1920 x 1080 on this GTX 1080/i7-5820K, dense authored combat with 34 active enemies measured 7.555 ms median and 15.253 ms at the 95th percentile. This calibration combines actual assets, scene density, streaming and hardware; it is not a universal mesh budget.

See [the current whole-game measurements and opened Godot comparisons](D:/Games/Metin2Clone/docs/full_asset_rebuild/README.md). Each isolated optimization study retains its imported source, frozen settings, original generation lineage, Blender reports and runtime export in the library. Technical validation leaves visual acceptance pending.

The current Ironfield library contains 111 replacement exports with new editable sources. All previous game model geometry was removed after import and gameplay validation. Thirty practical reference sets condition shared native reconstructions; species and service variants disclose their shared body plans. Thin equipment, vegetation and failed structural regions use clean remodeling. No old surface geometry is reused. The [current catalogue and repair report](D:/Games/Metin2Clone/docs/full_asset_rebuild/README.md) links actual Godot views, provenance, tests and performance. Earlier 54-fallback reports describe a superseded stage. Surface retopology and transferred skinning still need visual deformation review; automatic optimization does not author anatomical joint loops.
