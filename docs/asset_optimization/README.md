# Asset and game performance calibration

Measured locally in Godot 4.7.2 Compatibility at uncapped 1920 x 1080, on an
i7-5820K, GTX 1080 8 GB and 16 GB RAM. Each case has a two-second warm-up and
eight-second sample. Blender, browser checks and other builds run separately.
The benchmark loads the actual world, enables real combat/collision, disables
saves and traverses the actual mounted click-to-move route. Dense combat keeps
health replenished to sustain its stress load.

## Measured result

| Case | Actors | Median ms | P95 ms | P99 ms | Frames over 16.67 ms | Worst ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original dense combat | 159 | 25.42 | 61.51 | 75.55 | 78.73% | 90.74 |
| Final warmed dense combat | 34 | 8.93 | 15.17 | 18.46 | 2.75% | 24.32 |
| Final immediate combat stress | 34 | 12.99 | 24.47 | 31.73 | 29.51% | 35.71 |
| Final settlement | 10 | 6.46 | 14.28 | 15.98 | 0.58% | 19.33 |
| Final wilderness | 22 | 5.54 | 7.78 | 10.29 | 0% | 12.77 |
| Final mounted travel | 27.70 average | 7.42 | 13.75 | 19.56 | 1.77% | 55.42 |

The warmed route meets the 60 FPS budget for at least 95% of sampled frames.
**Immediate combat remains below the target for about 30% of frames.** The route
still has a 55 ms streaming hitch, and synchronous world/navigation initialization
takes about 9.4 seconds. These are unresolved CPU/startup issues. This calibration
improves playability substantially; it does not certify a locked 60 FPS game.

Mounted travel covered 86.22 m, remained mounted for 100% of samples and reported
no navigation failure. Final screenshots were opened, including the combat crowd
and the horse on the road. Near-camera foliage now fades for both WorldAssetKit
placements and the manually authored grove, preserving the horse view.

Raw measurements are retained:

- [Original raw baseline](../forge_rebuild/balance_baseline.log). Its numeric
  JSON was recovered from this unchanged log after a test-label mistake; the
  baseline image was overwritten by that intermediate test and is not claimed
  as original evidence.
- [Final full route](../asset_review/final_performance.log) and
  [immediate combat](../asset_review/cold_44.log).
- [Retained final JSON](final/asset_balance_reviewed_final.json),
  [cold JSON](final/asset_balance_reviewed_cold_44.json) and
  [opened mounted view](final/asset_balance_reviewed_final_mounted_travel.png).
- [Earlier 62-actor deployment](../asset_review/deployed_performance.log),
  [repeat](../asset_review/deployed_route_repeat.log) and
  [58-actor cold failure](../asset_review/cold_clean.log).
- [Three-member pack cold test](../asset_review/cold_three.log),
  [opt-in CPU sample](../asset_review/cold_cpu.log), and
  [instrumented full route](../asset_review/cpu_full.log).
- [Rejected four-worker experiment](../asset_review/workers_four.log): P95
  worsened from 24.47 to 29.12 ms. The project retains its default worker limit.

CPU instrumentation attributes nested costs to movement, brains, combat,
residency, animation and queued paths. Navigation was negligible in these samples;
the measurements do not identify one proven cause for all cold spikes. GPU time
stays about 3.4-4.7 ms, leaving rendering headroom. Godot's physics/process monitors
are sampled engine counters; do not sum them with nested function timings or
treat their averages as the isolated cost of a single physics tick.

## Selected tradeoffs

All 153 authored camps remain. Nearby camp residency wakes at 44 m and sleeps at
58 m, with hysteresis. Survivors, partial health, kills, respawn timers and reward
state survive unloading. Combat, statuses and knockback prevent unloading.
Ordinary expanded-map tier 1/2 packs contain three members; opening camps and
elites retain their authored sizes. Far unengaged simulation updates at 5 Hz;
nearby combat retains normal physics timing. Peripheral animation samples update
less often.

Pack steering uses a shared spatial snapshot, and navigation requests share a
queue limited to two queries and a one-millisecond post-query budget per tick.
One query may exceed that time budget; it cannot be preempted. Inventory health
updates touch only the relevant label, the event log repaints at 10 Hz, and hidden
debug text no longer rebuilds each frame. Collision capsules and melee timing
remain gameplay definitions independent of the visual mesh.

Twenty-nine ordinary reconstructed meshes were reduced from roughly 13-14k to a
12k target after opened Godot comparisons. The 8k wolf lost paw/fur detail; the
30k rider lost sleeve/coat detail, so the 41,998-triangle generated hero source
was retained. Rare generated creatures remain around 14k. Later visual review
replaced severe anatomy failures with 54 explicitly marked stable fallback
mappings; these earlier triangle targets describe retained generated assets,
not every final fallback. See [the adoption ledger](adopted_models.json) and
[subsequent asset decisions](../asset_review/report.json).

## Generator topology and material work

Installed optimization modes are Preserve, Simplify, Balanced and Retopology.
Reduction is optional. Bidirectional surface guards use 2% maximum and 1% P95
error relative to source extent, plus extrema, manifold and sampled deformation
checks. A failed candidate retains the source instead of forcing a damaged
triangle target. QuadriFlow runs in a bounded child Blender process; it does not
author joint loops or repair incompatible anatomy.

Successful remesh output projects onto the retained high surface, transfers skin
weights, creates UVs and rebakes supported base-color, metallic, roughness and
normal channels. Original actions and NLA export contracts remain available.
Unsupported shaders or linked/mixed transparency stop before changing target UVs
or materials. Source texture resolution is not presented as recovered detail.

The actual synthetic checker fixture reduced 3,968 to 2,496 triangles and rebaked
four PBR channels. Its Blender output and opened Godot material comparison are in
[the fixture evidence](views/material_transfer_fixture.png). It proves that
mechanism, not that every generated character earns acceptance.
[The real Blender alpha-preflight check](alpha_preflight.json) exited 0 and
confirmed UV, material and linked-alpha preservation on refusal.

A separate lossless GLB cleanup removes only proven zero-area indexed faces,
without changing vertices, UVs, weights, material slots or animation bytes. It
cleaned the retained horse and warden fallback copies; original files remain
untouched. Both cleaned outputs were rerendered and opened before deployment.

## Reproduce and continue calibration

From the game project, run separately:

```powershell
Godot_console.exe --rendering-method gl_compatibility --path game --script res://tests/asset_balance_profile.gd -- --label=local_final
Godot_console.exe --rendering-method gl_compatibility --path game --script res://tests/asset_balance_profile.gd -- --label=local_cold --dense-only
Godot_console.exe --rendering-method gl_compatibility --path game --script res://tests/asset_balance_profile.gd -- --label=local_cpu --dense-only --cpu-profile
```

JSON and screenshots are written under `game/.local/asset_balance_<label>*`.
Use unique labels. Open screenshots after any mesh/density change and rerun the
relevant combat/streaming/route contracts. Prioritize startup/streaming scheduling
and engine CPU profiling before lowering mesh quality further. Reassess the
worker experiment on another CPU rather than treating this machine's result as a
universal setting. The meaning of the tested worker setting is documented in
[Godot ProjectSettings](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html#class-projectsettings-property-threading-worker-pool-max-threads).
The foliage fade uses Godot's
[material distance fade](https://docs.godotengine.org/en/4.5/classes/class_basematerial3d.html#class-basematerial3d-property-distance-fade-mode).
