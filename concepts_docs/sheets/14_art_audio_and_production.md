# Art direction, audio and production acceptance

![Player class material and silhouette direction](../art/classes_four.png)

## Shared visual language

Grounded stylized proportions, Korean-inspired frontier clothing and structures, weathered useful objects, and clear constructed materials. Palette: muted jade/olive vegetation, ochre grass, blue-grey slate, warm skin, dark leather, brass, steel and a restrained oxblood sash/banner accent.

Large forms carry identity: branching trees, hunched root creatures, layered stone guardians and fitted lamellar. Avoid recognizable stacks of construction primitives, perfectly repeated foliage crowns, identical rounded shoulders and glowing balls without a physical core.

Amber marks Fracture activity. Class effects can use distinct narrow hues; upgraded equipment follows the fixed +7 blue / +8 red / +9 violet sparks. Environment glow must not overwhelm attack warnings or high-tier equipment effects.

## Asset acceptance

| Asset | Required review |
| --- | --- |
| Humanoid | Front/side/three-quarter proportions, face, hand grip, armor fit, cloth movement |
| Creature | Anatomically legible limbs, distinct tier silhouette, readable windup, grounded contact |
| Horse and mounted rider | Separate anatomy review, tack fit, feet/reins contact, idle/walk/canter inspection |
| Equipment | Same identity at all + levels, correct material shine and ordered sparks |
| Environment kit | Gameplay-camera readability, natural clustering, collision and route clearances |
| Fracture | Dormant/active/damaged/destroyed states, open warning floor, readable reward scatter |

Open and inspect actual rendered images. Inspect exported assets with materials inside Godot. A successful export does not demonstrate good proportions, and an AI concept plate is not a shipped model. Keep editable Blender sources, reproducible exports and import manifests.

## Rendering and performance

The current prototype uses Godot's GL Compatibility renderer. Design effects that remain readable there rather than assuming a different rendering feature set. Consolidate runtime characters sensibly by material and skin; repeated foliage should use instancing. Particle counts, light counts and shadow costs need scene-level limits.

Review actual crowds at 10/20/40/80 enemies and ordinary camera distance. Reduce effects density under load without changing attack timing, hit logic or upgrade identity. Avoid assigning a universal polygon limit from one model; record triangles, surfaces, draws, materials and the observed frame cost.

## Audio direction

| Source | Character |
| --- | --- |
| Foot/hoof contact | Distinct earth, timber and slate; restrained per-step variation |
| Steel hit / guard | Short metal/body contact matched to real hit events |
| Fracture wave / collapse | Root creak or stone strain, clear warning cue, brief falling-rib sound |
| Smith success / failure | Tempered ringing versus a short fractured impact, with outcome text |
| Mastery learned | Small page/rune cue, no lengthy fanfare on every spend |
| Region ambience | Wind, leaves, forge work, reeds or distant basin cracks; leave room for attack tells |

Music supports the region with sparse acoustic/percussive themes and limited encounter intensification. Do not cover important warnings with a constant loud loop. Maintain separate volume controls.

## Concept-art provenance

All PNG concept plates in this folder were generated with the built-in image generation tool for this project. Exact prompts are preserved in [prompts.json](../art/prompts.json). They are illustrations of design intent, not photographs, model renders or copies of free downloadable runtime assets.

The existing horse asset's separate free-source attribution remains in the project's [horse license record](../../blender/reference/horse/LICENSE.md). Retain the license and source for every externally acquired model, texture, sound or font. The concept-art creation here does not alter those asset records.

See [ART_REVIEW.md](../art/ART_REVIEW.md) for plate-level inspection and [existing art benchmark](../../ART_DIRECTION.md) for current implementation limitations.
