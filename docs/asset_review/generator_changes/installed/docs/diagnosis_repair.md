# Diagnosis, bounded repair and production replacement

The installed review interface adds **Diagnosis & repairs** to each asset. The
current integrated server is http://127.0.0.1:8742/. The normal launcher retains
its configured port; stop an existing instance before restarting it.

Review the retained concept, saved mesh and standardized front/side/back/
three-quarter, clay/textured/wireframe, detail and gameplay-distance images.
Open the animation evidence for rigged assets. Record mesh evidence before
asserting a geometric, UV or weight cause. Technical validation and visual
judgment are independent; no scalar quality score accepts a candidate.

Assign KEEP, POLISH, PARTIAL REBUILD, REGENERATE or REJECT. Describe asset-specific
criteria, confidence, exact source SHA, named regions and unresolved checks.
Good assets can stay KEEP without processing. Archive a failed candidate rather
than deleting its meshes, references, textures or manifest.

The structured JSON editor exposes supported plans and editable budgets. Defaults
are 2 automatic rounds, 1 actual saved assisted Blender pass and 360 seconds of
repair processing per asset. A failed fingerprint cannot repeat. Stop on a
plateau, regression or budget exhaustion. Paid regeneration is disabled.
Unattended model assistance is unavailable; an external assisted edit must save
actual mesh output and undergo the same evidence review.

## Supported operations

`GET /api/system` returns `repair_capabilities`, including actual local backend
availability and supported parameters. `PUT /api/assets/<id>/diagnosis` validates
the source hash, evidence files, plan and budget. Unknown operations/settings are
refused.

- `selective_smooth`: named object, explicit local bounds, protected regions,
  bounded iterations/factor/displacement; retain sharp features and boundaries.
- `normals_repair`: named mesh, justified by normal inspection.
- `material_adjust`: named material; supported unlinked roughness/metallic values.
- `simplify`: triangle target plus surface and sampled animation guards.
- `rebuild_parts`: curated static `timber_supports` or `fern_fronds`, preserving
  successful roof/balcony or crown regions.
- `assisted_blender`: actual saved candidate ID, one focused modification pass.
- `regenerate`: reviewed reference, available local backend and supported settings.
  TripoSR exposes `mc_resolution` and `texture_resolution`; TripoSG exposes
  `generation_seed`, `diffusion_steps`, `guidance_scale`, `shape_octree_depth`.
  Availability is checked before execution. Paid backends cannot be invoked here.

`POST /api/assets/<id>/repair` freezes the current plan and starts a bounded job.
Outputs have the same-camera before/after sheets, mesh audit, animation evidence,
Godot validation and time/cost receipt. An interrupted attempt preserves changed
output and restores its pre-attempt artifacts; the round still counts. Review is
required before another attempt.

## Compare and preserve

The comparison editor records improved defects, regressions, evidence and separate
silhouette, material, animation, integration, gameplay-distance, reference and
regression checks. `PUT /api/assets/<id>/attempts/<attempt>/review` accepts,
rejects or marks a plateau. Rejection archives output and restores the previous
selection. Never infer successful visual review from numerical success alone.

`POST /api/assets/<id>/versions/promote` requires an exact passed technical hash,
opened evidence and completed checks. It writes an immutable bundle containing
runtime GLB, lineage, retained editable/source files, PBR maps and review. A
temporary fallback must explicitly record its reason and incomplete reference
fidelity. `future_work` records unresolved artist tasks after runtime-safe fallback
acceptance, and the UI labels both its current and original generated status.

`POST /api/assets/<id>/game/apply` writes the reviewed immutable version to the
game's configured source binding. It preserves a hashed prior visual and mapping
history. Reapplying the same exact version is idempotent.
`POST /api/assets/<id>/game/rollback` restores the previous mapping immediately.
Archived candidates are disabled in selection and excluded from automatic export.
Ordinary export also requires production acceptance and completed diagnosis.

Loopback writes require `X-Forge-Request: 1`; browser Origin must be local.
Source files remain downloadable for inspection without production acceptance.

## Topology limits

Preserve/Simplify/Balanced/Retopology are optional processing modes. QuadriFlow runs
in a bounded Blender child process, projects onto the source, transfers skin and
rebakes supported PBR materials. Bidirectional surface, extrema, manifold and
sampled deformation checks can retain the original above-budget mesh. Linked or
mixed transparency and unsupported shaders stop before mutating target UVs or
materials. Automatic retopology cannot author anatomical joint loops, repair
incompatible anatomy or recover unseen texture detail.

Lossless GLB degenerate cleanup removes only proven zero-area indexed triangles.
It preserves original binary vertex/UV/weight/material/animation data, retains the
pre-cleanup export and refuses removal of an entire primitive. Both paths require
fresh renders after modification.

## Applied inventory and validation

The Ironfield project report is at
[D:/Games/Metin2Clone/docs/asset_review/README.md](D:/Games/Metin2Clone/docs/asset_review/README.md).
It records 110 reviewed bindings, two regional rebuilds (three exports), 54 marked
fallbacks, 61 archived candidates and the actual Godot integration/rollback checks.
Fifteen REGENERATE diagnoses remain future work; no new neural generation was
performed in that bounded repair review. Character anatomy, costumes and bridge
rails remain artist tasks. Whole-game cold performance and streaming hitches are
reported separately from the better warmed result.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd run build
```

The project also supplies `tools/forge_review_ui.py` for live Chrome checks and
`tools/forge_verify_reviewed.py` for the exact deployed versions and an actual
rollback/restore roundtrip. Do not run generation or browser work during FPS
measurement.
