# Asset diagnosis and controlled replacement

Reviewed on 4 October 2026 against the saved game inventory. Open the
[offline evidence gallery](gallery.html), [spreadsheet](inventory.csv), or
[complete structured report](report.json). The running Forge interface is
[http://127.0.0.1:8742/](http://127.0.0.1:8742/); select **Diagnosis & repairs**.
The gallery's live links open the corresponding asset directly.

## Results

| Original generated diagnosis | Assets | Result |
| --- | ---: | --- |
| KEEP | 12 | Retained. No unnecessary geometry edits. |
| POLISH | 40 | Retained with explicit local defects. Wolf smoothing plateaued. |
| PARTIAL REBUILD | 43 | Three exports from two regional rebuilds; 39 bindings use saved fallbacks; bridge remains flagged. |
| REGENERATE | 15 | Saved fallbacks selected; no neural regeneration performed in this review. |
| REJECT | 0 | No entire asset record discarded. Unacceptable individual candidates archived. |

There are **57 deployed immutable versions: 3 repaired exports and 54 temporary
fallback mappings**. Two source repairs produce the tower, fern and derived fern
exports. The current selection totals 69 KEEP, 40 POLISH and 1 PARTIAL REBUILD.
KEEP on a fallback approves its runtime safety and sampled appearance; its
incomplete concept fidelity remains explicit. Original diagnoses remain in this
report and saved manifest history.

**61 candidates are archived and excluded from selection and automatic export**:
54 failed generated presentations plus 7 failed repair outputs. Source meshes,
concepts, textures, editable files, references and original manifests are retained.
No gameplay entity, authored camp, service, collider or reward definition was
deleted because its visual failed. The original generation parents of fallback
assets already remain pending production acceptance, so their export gate also
prevents bypassing the reviewed replacement.

Ten bounded repair attempts ran: 3 automatic and 7 actual saved assisted Blender
passes across eight representative assets. Two were accepted, six rejected, one
plateaued and one interrupted/failed. Repair-job receipts total **313.55 seconds
and 0 generation credits**. This is processing recorded by the repair jobs,
excluding diagnosis rendering, reference preparation, image inspection and earlier
generation work. Earlier costs remain in their original receipts.

## Representative repairs

| Asset | Mesh diagnosis and action | Opened result |
| --- | --- | --- |
| Armored ironhide boar | Saved coordinates and weights confirm limb/anatomy mismatch. A focused weight-transfer pass preserved the hide. | Rejected: moving underside worsened. Original retained in archive; stable blacktusk anatomy selected as a marked fallback. Unique armor needs artist work. |
| Meadow wolf | Small noisy torso surface; protected head and paws; bounded 9 mm local smoothing. | Plateau: little improvement in defining features. Original remains POLISH. |
| Wooden watchtower | Distorted supports and indistinct ladder; preserve roof/balcony, rebuild only supports/braces/rungs. | First protruding-post pass rejected. Corrected 3,852-triangle, one-mesh export accepted: four posts, stone feet, braces and 14 readable rungs. |
| Fern | Fused opaque fronds; preserve crown, rebuild separated joined leaflets. | First sparse yellow pass rejected. Corrected 2,719-triangle, one-mesh export accepted: 12 fronds and 16 leaflet pairs. |

Additional focused horse, rider and red/grey wolf passes were rejected or failed
because they did not resolve the sampled anatomy defects without regressions.
Their outputs, notes and before/after images are retained in the interface.

## Evidence and validation

All 110 saved bindings received mesh inspection and standardized opened Godot
sheets: front, side, back, three-quarter, clay, textured, wireframe, detail and
gameplay-distance views. Every rigged clip sheet was opened with four samples per
clip. Every distinct saved fallback presentation was rendered and opened again.
When identical source bytes are reused, that evidence reuse is recorded by SHA.

Numerical validation remains separate from these visual decisions:

- [Initial isolated contracts](isolated_contracts.json): 110 bindings.
- [Exact replacement contracts](staged_contracts.json): 57 versioned candidates.
- [Actual world, services, rigs and equipment](integration/contracts.json).
- [Source retention, hashes, archive gates and actual rollback roundtrip](deployment_verification.json).
- [Gameplay suites](../forge_rebuild/gameplay_validation.json), including combat,
  streaming, routes, mount, services, farming and first-map progression.
- [Live Chrome interface checks](ui/report.json): editable budgets, unsupported
  operations refused, loaded comparisons, rejected history, fallback labels,
  archive selection disabled and asset deep links.

Horse, rider and mounted views were inspected separately and together inside
Godot. The saved previous coherent horse/rider are used as explicit fallbacks;
the attempted generated hoof/weight repairs did not earn production acceptance.
The mounted saddle and pose retain the existing animation/attachment contracts:
23 horse bones, four gaits, foot socket error 6.683 mm and rein socket error
0.665 mm. See [the nine opened views and metrics](../screenshots/horse-reference/godot/reviewed_staged_clean/metrics.json).
Those socket measurements certify attachment alignment, not exact reference style.

Whole-game measurements and their cold-start limitations are documented in
[performance evidence](../asset_optimization/README.md). The actual mounted route
was 86.22 m, with 100% mounted samples and no navigation failure. Opened final
screenshots also verify camera clearance for both scattered and authored grove
trees.
The [post-deployment receipt](post_deployment_validation.json) preserves the final
timing and density configuration without changing historical accepted versions.

## Implemented production loop

Forge now stores asset-specific criteria, confidence, named defects, exact source
hashes, evidence and supported repair plans. No arbitrary quality score accepts
an asset. Capability discovery rejects invented operations/settings.

Default budgets are **2 automatic rounds, 1 actual assisted Blender pass and
360 seconds per asset**, editable in the UI. Failed fingerprints cannot repeat;
a changed approach and prior review are required. Interruption preserves the
changed output, restores the previous artifacts and consumes the recorded round.
Paid regeneration stays disabled. Unattended model assistance is unavailable and
does not fabricate a successful manual edit.

Supported operations include protected local smoothing, named normals/material
repair, guarded simplification, curated static timber/fern rebuilding, saved
assisted Blender output and discovered available local regeneration settings.
Automatic QuadriFlow retopology has surface/animation guards, skin transfer and
PBR rebaking for supported materials. It cannot author anatomical joint loops.
Texture-linked or mixed alpha is rejected before any target UV/material mutation.

Promotion requires an exact validated GLB hash, opened evidence and independent
silhouette, materials, animation, integration, gameplay-distance and regression
checks. Temporary fallback promotion additionally requires an explicit reason
and records failed reference fidelity. Versioned bundles include lineage and
retained source/PBR/editable artifacts. The game maps to
`res://assets/reviewed/<asset>/<version>/runtime.glb` with a hashed previous visual
for immediate rollback. Reapplying the same version is idempotent.

## Remaining art work

The bridge needs rope/rail remodeling. Forty retained POLISH assets need local
fur, face, material, blade or surface refinement; deliberate wisp openings and
thin sword edges were not treated as accidental holes. Fifteen generation-fidelity
failures remain candidates for improved consistent references and future local
generation, rather than claimed successful regeneration.

Fifty-four fallback mappings still need unique, concept-faithful replacements.
Priority work is anatomy matched to quadruped and spider skeletons, explicit hero
coat/sleeve separation, NPC faces/costumes, species-specific armor and materials,
and foliage beyond the accepted fern. Small coat tints do not recover unique
species anatomy. Four sampled frames per clip cannot rule out every blend or
continuous deformation issue. Those limitations appear per asset in the UI and
report; the rejected meshes remain available for remodeling.

## Reproduce

From `D:\Games\Metin2Clone`:

```powershell
py -3.12 tools/forge_review_report.py
py -3.12 tools/forge_verify_reviewed.py
py -3.12 tools/forge_review_ui.py
py -3.12 tools/forge_validate_godot.py optimization_contracts remaster_streaming first_map_expansion combat_smoke route_mount zone_loop
Godot_console.exe --rendering-method gl_compatibility --path game --script res://tests/asset_balance_profile.gd -- --label=local_review
```

The verification script exercises and restores the actual tower mapping. Run
performance measurements alone. Use `--dense-only` for the immediate combat
stress case and `--cpu-profile` for opt-in nested CPU timings; do not compare
instrumented timing to final FPS. Saves are disabled in these fixtures.

To restart the current API after stopping its existing instance:

```powershell
Set-Location C:\Users\Tom\Documents\2D_to_3D
.\.venv\Scripts\python.exe -m uvicorn forge.api:app --host 127.0.0.1 --port 8742
```

The normal launcher retains its usual port. Generator changes are installed in
that directory; [the saved patch package](generator_changes/manifest.json)
records modified/new files and backups. The [concept library](../../concepts_docs/index.html)
contains 17 topic sheets, concept plates, mob/drop tables and the 29-tab workbook.
