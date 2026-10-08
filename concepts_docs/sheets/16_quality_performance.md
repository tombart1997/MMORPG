# Asset quality, repair and performance

![Horse, town services and equipment concept](../art/town_mounts.png)

This sheet defines the production review loop. The concept is the visual target;
an export passing numerical checks is still subject to an opened image review.

## Review every saved asset

Compare the original concept with front, side, back and three-quarter views,
clay, textured, wireframe, defining-feature close-ups and the normal camera distance.
For a rigged asset inspect every clip. Four samples per clip help identify large
deformation errors; continuous motion and unusual blends remain separate checks.

| Status | Action |
| --- | --- |
| KEEP | Retain a result that reads correctly in the game. |
| POLISH | Repair a named local surface, material or feature. |
| PARTIAL REBUILD | Remodel a specific structure while preserving successful regions. |
| REGENERATE | Prepare consistent neutral references and use supported local settings. |
| REJECT | Archive the candidate and retain a better version or marked fallback. |

Inspect mesh coordinates, UVs, normals and weights before assigning a cause.
Do not confuse intentional holes, rocky skin or floating wisp ribbons with defects.
Do not use a single quality score to override independent visual checks.

## Bounded repair budget

Default to two automatic rounds, one actual assisted Blender pass and 360 seconds
of repair-job processing per asset. These limits are editable in the Forge review
interface. Failed approaches must change before retrying. Stop on a plateau,
regression or budget limit. Paid regeneration stays disabled.

Use selective smoothing only with explicit protected regions. Repair normals
before remodeling a shading defect. Rebuild distorted posts and ladders as clean
timber geometry. Rebuild fused fern fronds as separated, batched leaflets.

Automatic QuadriFlow is available for surface retopology with projection, UV/PBR
rebaking and skin transfer. It does not create artist-authored joint loops or
repair a body whose anatomy disagrees with its skeleton. Surface guards use
2% maximum and 1% 95th-percentile error relative to source extent, with sampled
animation guards. Unsupported shaders or textured transparency retain the source.

## Current hardware budget

The current target is 60 FPS at 1920 × 1080 on the tested GTX 1080 (8 GB),
i7-5820K and 16 GB RAM, using Godot's Compatibility renderer. These are measured
local targets, not a guarantee for other computers.

| Real game case | Median frame | 95th percentile | Frames over 16.67 ms |
| --- | ---: | ---: | ---: |
| Original dense combat, 159 active actors | 25.42 ms | 61.51 ms | 78.73% |
| Complete replacement baseline, 34 active enemies | 8.179 ms | 16.153 ms | 3.86% |
| Complete replacement settlement | 5.640 ms | 11.699 ms | See raw profile |
| Complete replacement wilderness | 4.855 ms | 8.921 ms | See raw profile |
| Complete replacement mounted travel | 6.089 ms | 13.640 ms | 2.13% |
| Standalone travel after background model prefetch | 8.308 ms | 15.863 ms | 2.99% |
| Final dense combat, 34 active enemies | 7.555 ms | 15.253 ms | 2.67% |
| Final mounted travel | 6.482 ms | 12.984 ms | 1.39% |

The full final profile and real game screenshots are linked in the current repair report.
These results use actual wall-clock frames at 1920 by 1080, Compatibility rendering,
uncapped frame rate, saves disabled, two seconds warmup and eight seconds sampling.
GPU generation, Blender and other Godot jobs are stopped during measurement.
Median timing does not guarantee every frame reaches 60 FPS.

All 153 authored camps remain. Residency wakes at 44 m and sleeps at 58 m;
ordinary expanded packs contain three members and elites one. Model prefetch starts
at 68 m without spawning actors or advancing encounters. Completed background loads
are collected into a shared cache. Survivors, damage, deaths, respawns and rewards
survive streaming. Nearby combat retains full simulation; navigation shares a
bounded queue and distant animation samples run less often.

Travel crossed about 87 m with 100% mounted samples and no navigation failure.
Diagnosis traced 100-170 ms cold travel hitches to synchronous creature loading.
Background model prefetch reduced the standalone worst measured frame to 48.716 ms.
The final full profile reached a 34.302 ms worst travel frame after completed-load
collection was added. Brief hitches remain, and synchronous world initialization
took 12.744 seconds.
The evidence preserves both normal percentiles and worst frames.

Ordinary final creatures use roughly 12,000-18,000 triangles; the final hero uses
23,983 and horse 13,852 triangles. Higher budgets
are retained only when reductions visibly damage important shape or clothing.
Surface limits are calibrated together with encounter density, materials, lighting,
streaming and the actual camera; there is no universal triangle count.

## Versioned acceptance

Import candidates in isolation and inspect materials, scale, pivot, rig, clips,
attachments and actual game composition. Keep new source meshes, concepts,
textures, editable scenes and a manifest tied to model and rendered-image hashes.
Visual review is recorded independently of automatic numerical checks.

The current runtime catalogue contains **111 replacement exports**, with editable
sources, four-angle Godot sheets and sampled animation sheets for rigged models.
Thirty practical turnaround subjects condition shared reconstructions; species,
service and tier variants explicitly disclose their shared bases. Thin swords,
equipment pivots, fused lower legs, vegetation, bridge rails and other failed
sections use clean remodeling. Previous game model geometry was deleted after
replacement and validation, as requested. Current mappings contain no provisional
fallback entries. Earlier 54-fallback reports describe a superseded stage.

Automatic retopology still does not author clean anatomical deformation loops.
Transferred skinning has residual local stretching in extreme poses; close-up faces,
hands and painted lighting remain coarser than the reference. The fracture cage is
an intentionally simplified open interpretation. These limits are recorded alongside
opened evidence instead of claiming concept-exact reconstruction.

See the [current catalogue and repair report](../../docs/full_asset_rebuild/README.md),
[all installed models in Godot](../../docs/full_asset_rebuild/gallery.html), and
[30 practical reference sheets](../art/asset_turnarounds_v2/index.html).
