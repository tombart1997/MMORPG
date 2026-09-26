# Ironfield field-farming contract

**PLAYER POWER SHOULD CHANGE HOW THE PLAYER FARMS THE WORLD, NOT MERELY INCREASE DAMAGE NUMBERS.**

Progression should let the player return to the same ground with fewer swings per pack, more simultaneous attackers survived, fewer recovery stops and better routes. There are no enemy-count unlocks. Attack, Defense, HP, attack cadence, cleave geometry and deliberate skill use produce the change. Mounts may later change travel and attack policies; encounter activation depends on damage and proximity, never on WASD, walking speed or a particular animation.

## Reference: Briarwake Fracture

A natural wound has forced seven splintered root ribs around a suspended amber heart. Its branching silhouette and amber light distinguish it from ordinary rocks and trees. The original procedural model is authored in `fracture_visual.gd`; it has no imported third-party assets. The ribs spread and the heart brightens as health falls, hits pulse the core, and destruction drops the ribs around a brief outward ring. Ground circles warn where defenders will emerge.

The reference lies at (-8, 0, -49), east of Old Pine Hollow. A small path branches from the hollow, loops through the fracture clearing and rejoins the southern road. Existing ridges conceal it from town. The three ordinary enemy bands remain, so the player chooses between circling back, clearing nearby packs, or continuing toward the Broken Cairn. This is an addition inside the existing terrain bounds.

| Trigger | Pressure |
| --- | --- |
| First damage | Three young Mosslings |
| 72% health | Five young Mosslings |
| 38% health | Seven grown Mosslings |
| 12% health | Two ironbacks |
| Destruction | Reward scatter; surviving defenders remain dangerous |

The core has 950 HP. Each wave warns for 1.2 seconds and selects separated points on navigable ground roughly seven meters away, at least 3.5 meters from the player. Positions are rechecked at release. A player standing on a warning denies that spawn location; an entirely blocked wave retries. Thresholds queue in order, with a cap of 24 live defenders. No invulnerability gate forces a powerful player to wait: destroying the core cancels unreleased waves. This is a deliberate clear-speed reward.

Death, sanctuary or leaving the 22-meter encounter radius ends pursuit. An unfinished attempt resets after 12 seconds without a valid nearby opponent. The core heals, warnings disappear and surviving adds are removed. Defender corpses clear after five seconds. Adds yield no independent XP/items; all fracture reward value belongs to completion, preventing endless first-wave reset farming. Ordinary packs retain their existing rewards and respawns. The core reappears after 180 seconds of running game time, delayed while the player is within ten meters.

## Small reward chase

Independent rolls on completion: Wakeglass Ember 18%, Wakecleaver 5.5%, Rootward Jack 7.5%. An encounter can drop none, one or several rares. There is no hidden pity counter or forced rare in normal play. Every completion gives 28-42 gold, 3-6 Moss shards, 1-2 tonics and 100 XP.

- **Wakeglass Ember:** optionally consumes one at the existing Smith to guarantee a normally uncertain upgrade. Gold and ordinary materials still cost the same. It cannot be used on a 100% step, beyond the cap, with missing materials, or after a stale inventory selection. This is a durable crafting-cost decision through an existing service, not a new crafting system.
- **Wakecleaver:** level-four sword with +34 Attack and +0.16 attack speed. Uses the established sword visual, attack sequence and upgrades. Actual basic/skill damage reads the same calculated Attack.
- **Rootward Jack:** level-four chest armor with +8 Defense and +70 HP. Uses the established armor attachment and upgrade path. Defense reduces each incoming hit, making larger young-Mossling pulls survivable without immunity.

Rare ground items have a cyan label, narrow translucent beam and five-minute lifetime. Common entries remain quiet and last 90 seconds. One 10 Hz layout pass prioritizes rare labels and bounds common labels; entries whose labels are hidden remain physically clickable and available through nearby pickup. Label selection uses the displayed label position. There is no audio pipeline in this prototype, so this milestone adds no sound dependency.

## State and authority

`FractureData` and `FractureWave` author thresholds, enemy references, counts, warning delay, HP, radius, leash, cap, rewards and timers. `WorldFracture` owns one runtime attempt, warning queue and defender camps. It delegates every hit to the existing ActorBody/Health/Melee/Skill interfaces. Its stationary ActorBody is a bounded compatibility adapter for this encounter, not a new universal boss/destructible-target system. Push and slow do not move the core. New damage types, boss immunity, projectiles and PvP remain outside this contract.

`EnemyCamp` accepts authored spawn positions and independent switches for rewards/respawn/corpse cleanup. Wave mobs remain ordinary Godot entities, with the same EnemyData, AggroGroup, animations and combat commitments. `FarmingState` owns the reference location and save adapter, while the zone connects notices to the HUD. UI never creates rewards or advances encounter phases.

Version 4 stores cooldown, completion count and outstanding fracture ground loot in the same snapshot as inventory and currencies. Loading validates everything before mutation, removes current world pickups, restores saved fracture pickups and resets unfinished attempts without paying rewards. Destroyed cores retain their saved cooldown. Claimed loot is already in the saved bag and is absent from saved ground loot. Cooldowns and ground lifetimes do not advance offline. Versions 1-3 migrate to a dormant fracture. Ordinary ground drops remain transient and are cleared on load; ordinary camps retain their previous session rules.

This is one persistent location. Before adding multiple locations, replace the single-location save envelope with stable location-ID entries and a version migration. Do not save scene paths or transient instance IDs. Later variants can reuse the data/effect boundaries; do not add a generic encounter scripting language.

## Mass-enemy strategy

`EnemyCrowd` builds a scene-owned 1.5-meter spatial grid at 10 Hz. Staggered steering queries local cells across pack boundaries. Ordinary mobs occupy collision layer 8 and collide with world/player layers 1/2; the player mask includes 8. Mob-mob spacing comes from bounded steering instead of many physical body contacts. Dense overlaps defer new attack starts, but an accepted attack still commits and cannot be canceled by ordinary hits. Death removes body and click-proxy collision immediately.

AI uses direct movement with staggered 0.6-0.72 second LOS/path refresh when terrain obstructs pursuit. Navigation does not query once per enemy per frame. Resting grounded enemies skip redundant movement; distant nonattacking animations sample at 5 Hz, while nearby combat stays full-rate. Only the selected or nearest foe receives a normal nameplate; core labels and status VFX remain distinct. Existing ground skills refresh their short auras at 10 Hz rather than raycasting every physics frame.

The exporter joins the Mossling's 32 authored mesh pieces into one five-surface skin only for runtime export. Vertex counts, triangles, weights, skeleton and clips are preserved; the `.blend` remains editable as separate pieces. `./tools/build_assets.ps1 -Asset briarling` reproduces the optimized runtime asset. This was justified by measured draw-call growth, not a cosmetic remodel.

Pooling was not introduced: the normal encounter spawns at most seven enemies per release, and timing work identified ongoing contact/render costs rather than allocation as the primary problem. The stress harness excludes initial spawn/import time, so it is not evidence that spawning 80 actors in one frame is cheap. Larger waves should be spread over frames before raising the cap.

## Verification and future limits

`./tools/run.ps1 -Test` includes `farming_loop` alongside all previous suites. The farming test follows the road, fights a real ordinary pack, fights the four-wave reference with real skills, verifies survivor pressure, reward uniqueness, full inventory, rare selection, Smith catalyst use, actual rare-sword scaling, corpse cleanup, escape/death/reset, respawn and persistence. Forced rare creation is confined to tests; there is no debug drop shortcut in normal play.

`./tools/run.ps1 -Test -Suite farming_stress` exercises 10/20/40/80 active enemies and 60 ground entries including three rares. Add `-Windowed` for the rendered run and captures in `game/.local/farming_*.png`. It measures median/p95 wall time across 180 fixed-step frame waits, reports Godot counters, checks distinct occupied positions, and isolates frozen-animation versus hidden-mesh costs at 40 mobs. The fixed-FPS harness, warm-up and camera placement are part of the measurement; reported timings are not hardware-independent FPS guarantees. Performance observations are recorded in PROJECT.md.

Remaining boundaries: no network authority, crowd avoidance server, mount controller, boss control policy or automatic idle farming. Very dense steering still has a local quadratic worst case; imported rigs and per-hit VFX still cost per visible actor/hit. Candidate broad-phase for melee/skills and distant AI scheduling should follow new profiling, not be added speculatively. Stress-test both appearance and commitment timing whenever changing those paths.
