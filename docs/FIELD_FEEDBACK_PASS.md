# Field creatures, mounted combat and rewards

The October 2 feedback pass addresses creature readability, Young Mossling visibility,
mounted sword motion, Briarwake reinforcements, inventory trophy icons and common loot volume.

## Rendered review

Open [the review gallery](screenshots/field-feedback/review.html) for the production-scene
screenshots, four mounted cuts with short/long swords, and the new horse call.
The test harness hides HUD/nameplates for creature closeups; inventory shots use the real UI.
No UI layout or gameplay actor collision envelope was changed.

Baseline Young Mosslings were present in a fresh scene. The review now visits every one
of their seven authored camps, including camps unloaded at startup, and verifies their
actors are visible and standing on terrain. Fresh saplings have lighter green bark and
a slightly rounder head. Their stable `young` gameplay/quest ID is retained, and the
legacy `young.tres` definition is restored alongside the current filename.

## Changes

- Shared creature surfaces neutralize the baked green albedo before applying species
  colors. Texture grain and normal maps remain; fur has dorsal/underside markings,
  chitin has a restrained sheen, stone/bark are rougher, and wisps retain luminous color.
  Red wolves are rust, blue wolves slate blue, grey wolves grey, frost wolves pale.
  Other wolves, boars, spiders, stone guardians and wisps have individual palettes.
  Bandit clothes receive distinct palettes while skin, eyes and armor retain their surfaces.
- The mount cue is an actual [horse vocal recorded by Joseph SARDIN](https://bigsoundbank.com/little-neighing-call-6-s1217.html),
  released as CC0. Its 1.64-second nicker is normalized/faded offline. Existing hoof cues
  are retained, and the vocal plays at its original pitch.
- Mounted cuts form backward circles in diagonal planes outside alternating sides of
  the horse. Hips, spine and shoulders shift with the cut. The hand path accounts for
  cross-body reach, the socket offset and pommel length, transferring through a forward
  raised guard. Final IK runs after pose transitions; reins and stirrups remain constrained.
  Mounting and equipment swaps immediately apply the safe mounted guard.
- Briarwake has 1,800 HP and four waves at 100%, 80%, 55% and 30% health: 6 young,
  6 young, 8 grown and 4 ironbacks. Each receives a 0.65-second warning. Damage can
  reach the following phase boundary but cannot kill the root before pending waves
  release. Encounter formations preserve their exact authored counts, including elites.
  Population remains capped at 24; defenders grant no extra loot. Abandonment, sanctuary,
  reset, survivor combat, cooldown and completion rewards keep their existing rules.
- All 35 crafting materials have individual vector icons. Teeth, tusks, silk, stone cores,
  insignia, essence, bark, sap and plates use recognizable silhouettes and species colors.
- Common trophy chance is 22.5% instead of 45%; ordinary tonic chance is 4% instead
  of 8%. Young shard chance is 45% instead of guaranteed; grown shard chance is 35%
  instead of 80%. Root common bundles shrink to 1–2 shards at 80% and one tonic at
  25%. Rare gear, gold, quest rewards and guaranteed camp rewards keep their rules.
  The existing three-shard introductory objective remains; common shards now require
  additional hunting when rolls are unlucky.

## Verification

`tools/run.ps1 -Test` includes the new `field_feedback_review` suite. Test processes
now write separate logs so an open game cannot contaminate their results.
All 22 suites passed after the pass, including the live farming fight, mounted combat,
quest/forge UI, inventory, save/load, traversal and the new feedback regressions.

The rendered loop was repeated across four substantial passes. The second pass added
full blade/pommel checks and caught chest interference that tip-only checks missed.
The final short/long sword review recorded zero horse or rider envelope intersections.
These are conservative presentation checks, not new physical sword colliders.

The real level-6 farming fight released all four waves and ended with the player alive,
16 defenders still fighting, and 163 damage received. Burst-damage tests separately
verify all 24 defenders materialize before root destruction and completion pays once.

10,000 seeded rolls per table produced mean item quantities of 0.717 young, 0.627 grown,
0.266 red wolf and 1.636 root, versus previous expected quantities 1.534, 1.334, 0.535
and 6.187 respectively. These measurements exclude coins and leader rewards.

Rebuild icons with `python tools/build_trophy_icons.py`; explicit common-drop settings
are reproducible with `python tools/tune_field_drops.py`. Audio source attribution and
the horse download/processing recipe are in `game/assets/audio/CREDITS.txt` and
`tools/build_game_audio.py`.
