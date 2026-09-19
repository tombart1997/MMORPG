# Ironfield - Briarwood March

A small offline Godot 4.7.2 fantasy action RPG foundation. The default scene is an outdoor zone with committed melee sequences, three enemy camps, group respawning, XP/levels, gold, stackable loot, consumable healing, and player revival. All visuals are original Godot primitives; no downloads, third-party dependencies, or copyrighted game assets. Blender remains available but adds no value for these simple placeholders.

## Launch and environment

Verified tools: Godot 4.7.2.stable.official.ed1daf0bf, Blender 5.2.2 LTS, Git 2.37.0.windows.1.

From the repository root in PowerShell:

```powershell
./tools/run.ps1                         # Play Briarwood March
./tools/run.ps1 -Editor                 # Open Godot editor
./tools/run.ps1 -Test                   # All three headless integration suites
./tools/run.ps1 -Test -Suite zone_loop  # Only the outdoor gameplay loop
./tools/run.ps1 -Test -Suite zone_loop -Windowed # Rendered loop and screenshots
```

The launcher redirects process-local APPDATA/LOCALAPPDATA and Godot logs to `game/.local/`, restoring the environment afterward. It changes no system settings. Importing `game/project.godot` directly and pressing F5 also works, but a normal Godot launch uses normal OS cache paths.

Progress is currently **session-only**. Death preserves XP/inventory; closing or restarting the game does not. The original arena remains in `scenes/arena.tscn` for focused regressions and may be run with F6 from the editor.

## Controls and gameplay

| Input | Behavior |
| --- | --- |
| WASD | Camera-relative movement when not committed to melee |
| Mouse | Orbit camera; camera yaw aims a new attack |
| Left click | Start a sword swing; click during recovery to buffer the next swing |
| Wheel | Camera distance, 3-10 meters |
| E | Gather all unclaimed loot within 2.3 meters |
| Q | Use one field tonic for up to 45 HP when movement is unlocked |
| Escape / click | Release / recapture cursor; recapture does not attack |
| R while dead | Revive at the starting waystone, retaining progression and inventory |
| F3 | Toggle the debug attack cone (off by default in the zone) |

Follow the dirt path from Waystone Refuge to Briar Crossing, then the branches toward Old Pine Hollow and The Broken Cairn. Their groups contain 3, 4, and 5 mosslings. Striking a member alerts its group. Ordinary hits flash but do not cancel an enemy's committed attack. Amber torso color signals windup, red signals active frames, and weapon/bone motion follows the phase.

Each kill gives 25 XP immediately. A visible bundle contains 4-8 gold and either a moss shard or a field tonic. E collects nearby bundles atomically; shards are collectible inventory items with no crafting use yet. Players start with two tonics. The HUD shows health, XP, level, currency, item counts, camp status, attack phase/sequence, hits, and kills.

Level 2 requires 80 XP; later thresholds increase by 40 each level. Excess XP carries over. Leveling adds 20 maximum HP and restores health. Waystone Refuge heals 18 HP/second when no pack has a target and the player is not attacking. Death allows R revival without a penalty in this milestone.

Fully defeated camps respawn after 18 seconds, postponed while a player is within 6 meters of the camp center. Corpses are removed when the new group spawns. Uncollected loot expires after 90 seconds. Groups stop pursuit if the player dies or moves more than 13 meters from their camp; living enemies return home. Enemy damage already taken is retained on return. Individual dead members do not respawn until their whole group is cleared.

## Melee commitment and sequencing

Normal movement is locked by `MeleeCombat.movement_locked()` throughout windup, active, and the configured recovery portion. All current attacks unlock at the end of recovery. This is specifically a melee-component rule, not a global actor movement restriction; future bow/ranged combat should use its own policy.

`AttackData` authors `lunge_distance`, `lunge_start`, and `lunge_duration` in meters/seconds. Combat integrates the displacement window and supplies velocity in the facing direction captured at attack start. Controllers combine permitted locomotion with combat motion and call `move_and_slide`; lunges collide with bodies/world instead of teleporting. This is root-motion-like simulation, not motion extracted from animation.

| Attack | Damage | Windup / active / recovery | Forward distance |
| --- | --- | --- | --- |
| Sword sweep | 25 | 0.18 / 0.16 / 0.30 s | 0.35 m |
| Returning cut | 25 | 0.15 / 0.16 / 0.28 s | 0.28 m |
| Heavy sweep | 35 | 0.25 / 0.18 / 0.38 s | 0.55 m |
| Enemy claw | 8 | 0.32 / 0.12 / 0.85 s | 0.30 m |

One click in recovery can buffer one follow-up. A new attack within 0.65 seconds of idle advances the three-step sequence; waiting longer or canceling resets it. Early windup/active clicks are not buffered. Facing stays fixed during an attack and its buffered follow-up; between attacks, the next unbuffered click can aim again using camera yaw.

The existing cone hit resolver remains: 2.8 m / 115 degrees for all sword steps, 1.95 m / 85 degrees for claws. Active ticks check living opposing actor centers against distance, height tolerance, and forward dot product. Static geometry blocks hits via a ray. Every valid target can be hit, but only once per swing. No guaranteed damage, magnet targeting, or client-side damage shortcuts are added.

Enemy speed is 3.2 m/s. Enemies begin a strike within 1.65 m, lock facing, and perform the same phased detection with a small lunge. Ordinary damage causes only a short pause when not already attacking; it cannot repeatedly cancel an enemy windup. Tests verify that a close enemy can hit a retreat-held but committed player, while an uncommitted retreat still avoids the telegraph.

## Architecture and directory structure

```text
game/
  project.godot
  scenes/
    outdoor_zone.tscn         Default composition root
    arena.tscn                Retained regression arena
    visuals/                  Humanoid, mossling, sword, armor scenes
  data/
    attacks/                  Shared immutable AttackData resources
    items/                    ItemData resources: tonic and moss shard
  scripts/
    actors/                   ActorBody: physics body and component assembly
    components/               HealthComponent: damage, healing, death signals
    combat/                   MeleeCombat, AttackData, debug cone
    player/                   Input/movement controller and spring-arm camera
    ai/                       EnemyBrain and AggroGroup
    visuals/                  ActorVisual presentation adapter and placeholder rig
    rpg/                      Progression, inventory, item data, loot pickup
    world/                    Zone composition, terrain/props, camp spawning, arena
    ui/                       Zone HUD and retained arena combat HUD
  tests/                      Three native SceneTree integration suites
  .godot/                     Ignored imports/cache
  .local/                     Ignored logs/editor data/screenshots
assets/                       Original source art (reserved)
blender/                      Editable .blend sources (reserved)
docs/                         Additional design notes (reserved)
tools/run.ps1                 Workspace-local launcher and test runner
```

`outdoor_zone.gd` composes terrain, lighting, player components, three camps, HUD, and the small session loop. `ZoneTerrain` builds a deterministic colored triangle mesh with collision, flat branching paths and camp clearings, gentle hills, trees, rocks, boundary stones, and a campfire landmark. Godot clockwise winding is required for the terrain's front-facing collision. Props are kept away from camp clearings and paths.

`ActorBody` owns its CharacterBody3D, health, melee component, and one replaceable `ActorVisual` scene. It has no input or AI decisions and no bone/mesh logic. `PlayerController` and `EnemyBrain` own movement decisions. `AggroGroup` owns target/member relationships, separately from `EnemyCamp`, which owns spawning, reward creation, corpse cleanup, and group respawn timing.

`HealthComponent.apply_damage` remains the single damage entry point. It rejects dead targets, clamps damage, and emits damaged/changed/died. `heal` cannot resurrect actors. The zone explicitly revives the player and restores collision. All reward logic subscribes to death; repeat damage to a corpse cannot pay rewards again.

`PlayerProgression` owns XP, levels, and kill count. The zone listens for level-up to increase health. `PlayerInventory` owns gold and item stacks keyed by ItemData IDs. `LootPickup` checks life/proximity and a claimed flag before transferring its bundle, then frees itself. Current rewards are deterministic for easy testing. Inventory/loot do not equip gear yet.

## Replaceable character and enemy visuals

The humanoid and mossling PackedScenes use an `ActorVisual` adapter with `present(...)`, `react_to_hit()`, and `equip_visual(slot, scene)` methods. Gameplay feeds health, velocity, and combat state to this adapter, without addressing specific bones or animation assets.

The placeholder adapter builds a seven-bone Skeleton3D, rigid mesh parts attached using BoneAttachment3D, and an AnimationPlayer. It supplies idle, run, windup, active, recovery, and death clips; phase clips scale to the current attack's duration. These are deliberately simple rigid-part animations, not production skinned meshes.

Named attachment points include WeaponSocket, OffhandSocket, ArmorSocket, HeadSocket, and boot sockets. Sword and chest armor are independent scenes; replacing one equipment child leaves the body and gameplay intact. To integrate a future humanoid or creature, replace the visual scene/adapter internals with an imported rig and mapped clips while keeping this interface. The skeleton, sockets, and animations may differ per creature; gameplay does not depend on them. Armor can later replace skinned mesh parts inside the adapter. Root motion should continue to be validated/applied by combat rather than making rendering authoritative.

## Conventions and future boundaries

GDScript, snake_case files/functions, PascalCase classes. Local -Z is forward, Y is up, feet at Y=0, distances in meters, timings in seconds. Keep tuning in resources and runtime state in components. Shared attack resources must not be mutated per swing. Direct calls issue commands, signals report events. Avoid global singletons without a concrete need.

Collision layers: 1 = static world, 2 = actors. Actors collide with both; camera and melee occlusion queries use only static world. Scene groups `players` and `enemies` identify factions; `loot` identifies pickups; AggroGroup membership defines an encounter.

Runtime art belongs under `game/assets/`; original art belongs under root `assets/` or `blender/`. Track Godot .uid files and .blend source. Ignore .godot, .local, temporary renders, backups, and logs.

This remains an offline simulation. Future multiplayer needs server-owned movement, attack validation, rewards and pickup validation, stable replicated IDs, and a latency policy. Local instance IDs only deduplicate hits. No persistence, navigation mesh, ranged combat, equipment stats, crafting, quests, trading, networking, or production animations are implemented. AI uses direct pursuit and light separation; camp paths/clearings are open, and complex obstacle routing remains future work.

## Verification

The test runner imports once, rejects script import errors, runs the selected suites, and returns nonzero on failed checks or runtime script errors. Suite logs are retained under `.local/`.

- `combat_smoke`: retained arena checks movement/camera, attack timing, cleave, deduplication, exclusions, walls, aggro, enemy damage, death, and arena reset. Windowed mode also checks mouse recapture and actual left-click input.
- `melee_commitment`: held retreat cannot defeat movement lock; exact authored forward motion; buffered combo steps; timeout reset; movement recovery; closest enemy lands a timed hit during commitment; uncommitted retreat avoids damage.
- `zone_loop`: outdoor traversal/collision, visual rig/equipment contract, two real combat encounters, XP and level growth, death reward uniqueness, pickup proximity/claim behavior, inventory, tonic use, group respawn safety, player death/revival, and preservation of session progression.

Headless combat and melee suites passed after the visual refactor. The outdoor loop passed headless and windowed, and `game/.local/zone.png` was visually inspected. Native windowed execution used OpenGL 3.3 compatibility on the GTX 1080. Sandbox startup may report inability to read the OS certificate store; this offline prototype does not use certificates/networking, and the unrestricted windowed run did not report it.

Checkpoints: `94b5df8` first playable slice; `9276e0c` verified melee correction before the outdoor/visual architecture work. Further combat balance and visual polish are intentionally deferred to playtesting.
