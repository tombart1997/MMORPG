# Ironfield — Briarwake art benchmark

## Locked scope and diagnosis

One clearing and its western/southern forest approach, centered on (-8, -49), with an approximately 24 m art footprint and a shallow background tree belt. No new encounters or gameplay. Existing gameplay, saves, rig names, animation clips, socket origins and crowd scheduling remain authoritative. Existing uncommitted work is retained. No automatic commit.

The inspected captures show bare green terrain, stacked cone trees, rounded unstructured rocks, cylindrical Fracture ribs, toy-like smooth characters and oversized instructional HUD panels. Flat materials and uniform spacing amplify these problems. Traveler is still the default profile despite the available V2 source. The current environment has no authored import pipeline; it constructs primitives at runtime. Mossling already exports as one skin: preserve that improvement.

## Art plan, before implementation

The **Amber Scar**: an old road opens into a damp, slate-backed grove. Three bent deciduous tree silhouettes create a dark foreground arch and uneven background canopy. Broken roots and low fern banks define walkable earth. Cool olive/jade vegetation and gray blue stone surround a single warm amber focal point. Density increases at the edges, never across the encounter floor. The approach partially hides the core behind a trunk and a slate shoulder; moving into the clearing reveals split, inward-curling wooden ribs around a suspended fractured heart.

1. Preserve Turnwarden V2's base rig and clips. Replace its most visible rounded shoulder/boot/coat forms with constructed plates, shaped cloth and a strong rear silhouette; retain its separate sword and equipment socket. Use distinguishable skin, hair, oxblood cloth, leather, brushed steel and tarnished brass.
2. Author one Mossling: hunched root anatomy, broad bark face with recessed amber eyes, forked grasping claws, split feet, and asymmetric shelf fungus/leaf growth. Export one skin, with a small shared material palette.
3. Author seven split Fracture ribs with eroded edges, branching ground roots, interior amber shards and visible depth. Presentation follows existing health/activation/death state; collapse ribs outward and scatter restrained embers.
4. A reusable kit: three branching trees, three fractured slate rocks, two shrubs, fern, grass/sedge, fallen trunk and a broken roadside memorial. Authored mesh shapes and original procedural color/roughness/normal textures; no downloaded art. Repeated small foliage uses MultiMesh, with limited shadows.
5. Blend traveled soil, forest duff, low grass, exposed stone and an irregular corrupted scar in the existing ground material. Add local roots, stones and plants without replacing terrain collision or navigation.
6. Cool ambient fill, warm directional light, readable shadows and modest distance fog. Compact HP/XP and skill bar, target presentation, and optional F3 instructions.
7. Capture and inspect the real third-person camera before and after. Iterate on the three most visible remaining weaknesses. Run all gameplay suites and the existing 10/20/40/80 crowd harness; record actual frame/counter measurements and asset budgets.

## Production expectations

Low polygon count is not permission to ship visible construction primitives. Editable source may contain many pieces; runtime characters must consolidate by material and skin. Textures belong to a reproducible original source pipeline. Roughness and normals communicate material; tiny geometry hidden at gameplay distance has low priority. Foliage must frame characters without hiding attacks. Amber marks supernatural activity, not every prop. Large opaque effects and permanent debug text are not part of the visual target.

Reference-quality status, measured budgets, captures and remaining limitations will be recorded after rendered review, not inferred from successful generation.

## Implemented art and source ownership

The clearing is roughly 20 m across, with a western approach and a shallow tree belt extending to about 24 m from the existing encounter center. `BriarwakeGrove` contains fixed tree/rock placements and bounded understory beds. The original terrain height function, collision mesh and encounter remain in use. A local ground shader adds a traveled southern footpath, brown duff, green banks, exposed stone and the irregular dark scar. Ferns, sedge, shrubs, leaf litter and pebbles use one MultiMesh per imported surface group; small vegetation does not cast shadows.

`blender/scripts/build_benchmark.py` is the original source generator. Editable meshes live in `blender/benchmark/`; runtime props live in `game/assets/benchmark/`, with characters continuing to use `game/assets/characters/`. The archived generators and original character sources remain useful for comparing the starting point. `build_turnwarden_v2.py` still owns the base humanoid construction and animation contract; the benchmark generator reuses it and changes visible armor, boots, coat, back and material treatment. The player profile now actually selects V2. Its sword remains separately equipped and its visible blade matches the existing 1.08 m tip marker.

Build all art with `./tools/build_art.ps1`, or use `-Asset forest`, `briarwake`, `briarling` or `turnwarden_v2`. These commands regenerate source, so use `./tools/build_assets.ps1 -Asset <name>` to export a hand-edited benchmark `.blend` without regenerating it. This launcher prefers benchmark source over the archived character source. The no-argument asset builder now rebuilds the benchmark rather than overwriting it with the old creature. Export joins editable pieces, retains weights and NLA tracks, and records production statistics. Godot imports named skins, generated LODs and shadow meshes; animated profiles use 60 Hz import sampling.

The 256 px tiling color/roughness/normal resources are generated from seeded periodic noise fields. Bark uses lengthwise branch UVs; slate uses planar projections and worn bevels. Cloth has fine weave and high roughness; leather is matte with granular variation; steel is cooler and smoother; brass is warmer. Faces and hair retain V2's simpler materials because tiny added detail did not justify more geometry at the gameplay camera. No texture or mesh was downloaded. Godot also extracts embedded GLB image resources beside the imports.

## Runtime budgets discovered

These are full-detail exported triangle counts, not LOD or visible-frame counts. Godot can split a mesh into several draws by surface and shadow pass. One skin does not mean one draw.

| Asset | Triangles | Surfaces | Meshes / skins |
| --- | ---: | ---: | ---: |
| Turnwarden V2 | 4,604 | 10 | 1 / 1 |
| Separate sword | 550 | 5 | 1 / 0 |
| Equipped chest harness | 164 | 2 | 1 / 0 |
| Mossling | 4,320 | 5 | 1 / 1 |
| Briarwake | 5,490 | 17 | 10 / 0 |
| Each of three trees | 18,010 | 2 | 1 / 0 |
| Three slate rocks | 540–846 | 2 | 1 / 0 each |
| Two shrubs | 912 / 1,368 | 2 | 1 / 0 each |
| Fern / sedge / leaf litter | 648 / 92 / 48 | 1 | 1 / 0 each |
| Fallen wood | 606 | 1 | 1 / 0 |

Mossling's 69 editable pieces become one five-surface skin. Its existing 18 bones and five clips are retained. V2's 59 editable pieces likewise become one skin; all eleven clips, socket bones and phase markers are retained. Briarwake intentionally keeps seven two-surface ribs and three single-surface core slivers so damage and outward collapse do not require skinning. These are discovered budgets, not universal maximums. A better 15k creature is welcome if its submitted representation remains sensible.

## Lighting, VFX and HUD contract

The benchmark blends cool ambient/fog and a warm oblique key as the camera enters the grove. An unshadowed cool fill keeps armor and creature anatomy readable. The renderer remains GL Compatibility, with 4x MSAA and a 4096 directional shadow atlas. Fog provides distance separation; geometry and light define the nearby scene. Amber is reserved for the Fracture and encounter activity. Its dormant/active light levels, health-based rib opening, impact chips and root-pivot collapse all follow existing gameplay signals.

Impacts, creature death and defender arrival use brief instanced shard bursts, capped at twelve live bursts scene-wide. Sword trails follow the animated equipment tip during active time and vanish after the short stroke. Skill flashes retain thin geometric outlines and now fade. Rare loot has a restrained beam, a brief arrival effect and a priority label; forced rare creation exists only in the screenshot fixture. Loot layout/click targets remain owned by the existing system.

HP and XP use a compact upper-left panel. Target name/health has a small separate hierarchy; skill names and descriptions live in tooltips while six icons, hotkeys, cooldowns and opportunity feedback remain visible. F3 exposes development instructions and encounter diagnostics. World district labels no longer scale into giant instructions near the camera.

## Rendered review and reference status

The captures come from the shipped outdoor world and `ThirdPersonCamera`, not a Blender render or a separate cinematic camera. The final view uses the ordinary 8 m zoom, 60-degree FOV, yaw -0.38 and pitch -0.42. The fixture activates the existing first wave and positions its three real defenders for repeatability; it disables their steering during the still capture. Persistence is disabled in tests. This is a composed gameplay-camera still, not a claim that it records an unassisted fight.

Visual review found and corrected: crowns above the camera, repetitive grid-like texture fields, stiff branch gestures, over-dark character silhouettes, an occluding foreground tree, overexposed amber, giant district text, and ribs collapsing around the wrong pivot. The final lighting faces the player side of the clearing, branches have authored smooth centerlines and lengthwise grain, and the approach reveals the core through layered vegetation.

Use the Mossling, fern/slate kit, layered V2 shoulders and Fracture silhouette as the new **benchmark references**, rather than using the earlier primitive models as style rules. They establish a repeatable direction at gameplay distance. The tree crowns still expose procedural repetition, some floor transitions remain soft, and close-up faces/armor are not a finished commercial character-art standard. Background regions beyond this clearing still contain explicit placeholder cones and rounded rocks. Do not extend this scene's approval to those regions or advertise the whole project as production-quality. A successful export or passing test does not resolve this remaining art judgment.
