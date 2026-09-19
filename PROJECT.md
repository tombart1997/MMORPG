# Ironfield combat prototype

First playable offline 3D action RPG slice, using native Godot primitives. No external assets, dependencies, copyrighted game files, multiplayer, or Blender processing.

## Environment and launch

Verified: Godot **4.7.2.stable.official.ed1daf0bf**, Blender **5.2.2 LTS**, Git **2.37.0.windows.1**. Initial workspace contained empty source folders, no Godot project. Git checkpoint `9e0635b` preserves the initial files.

From the repository root in PowerShell:

```powershell
./tools/run.ps1          # Play
./tools/run.ps1 -Editor  # Editor
./tools/run.ps1 -Test    # Import and run integration checks
./tools/run.ps1 -Test -Windowed # Also verify mouse capture and save .local/arena.png
```

The launcher redirects per-process Windows cache paths to `game/.local/`; generated files remain inside this workspace. Alternatively import `game/project.godot` or run `godot --path game` (normal Godot launches use OS cache paths). The launcher does not change system settings.

## Controls

| Input | Action |
| --- | --- |
| WASD | Camera-relative movement |
| Mouse | Orbit third-person camera |
| Left mouse | One sword swing per press, aimed along camera yaw |
| Wheel | Zoom from 3 to 10 meters |
| Escape | Release cursor |
| Click after Escape | Capture cursor |
| R | Restart encounter, including after death or victory |
| F3 | Toggle floor combat cone |

Approach the six red raiders and strike to alert the pack. Three sword hits kill a raider; sweeps can hit several. Move between swings to avoid enemy windups. Player has 160 HP. White flash and squash show damage, amber shows windup, and red shows active attacks. HUD reports HP, pack status, phase, and hits. Dead actors fall over and stop blocking others.

Movement turns toward travel. Attacks snap facing to camera yaw and lock it through recovery, while movement slows. Camera orbit remains independent. Enemy attack facing also locks, allowing players to evade telegraphed strikes.

## Structure

```text
game/                      Godot project
  scenes/arena.tscn         Entry scene
  data/attacks/             AttackData resources
  scripts/actors/           Actor composition and placeholder visuals
  scripts/components/      Reusable health/damage component
  scripts/combat/           Attack data, phase machine, cone visualization
  scripts/player/          Input/movement and camera
  scripts/ai/              Enemy brain and encounter aggro group
  scripts/world/           Arena composition, geometry, input defaults
  scripts/ui/              Combat HUD
  tests/                   Dependency-free integration tests
  .godot/                  Generated imports (ignored)
  .local/                  Logs and editor caches (ignored)
assets/                    Reserved original source art
blender/                   Reserved editable Blender sources
docs/                      Future design notes
tools/run.ps1              Workspace-local launcher
```

Future runtime art belongs under `game/assets/`, original art under root `assets/` or `blender/`. Track .blend source and Godot .uid files; ignore .godot, logs, Blender backups, and temporary renders.

## Architecture

`arena.gd` is the composition root: it creates geometry, actors, group, controllers, and HUD. Procedural actor assembly can move to PackedScenes later without changing combat logic.

`ActorBody` owns health, combat, and placeholder presentation. Controllers own movement decisions and call `move_and_slide` in physics ticks. Feet are at local Y=0, forward is -Z, Y is up, distances are meters, times are seconds.

`PlayerController` converts input into movement and attack requests. `ThirdPersonCamera` follows independently of actor rotation with a SpringArm3D sphere probe to prevent clipping through static geometry.

`AttackData` defines damage, phase timings, reach, full cone angle, vertical tolerance, and movement multiplier. Sword: 25 damage, 0.18/0.16/0.30 seconds, 2.8 m, 115 degrees. Claw: 8 damage, 0.55/0.12/0.85 seconds, 1.65 m, 85 degrees. Tune `.tres` resources, not controllers.

`MeleeCombat` runs IDLE → WINDUP → ACTIVE → RECOVERY → IDLE. Only active ticks test opposing living actor centers against distance, height, and forward dot product. Static-world ray checks prevent attacks through walls. All qualifying targets are damaged, with a per-swing instance-ID set preventing repeats. Detection is a cone, not blade collision. Requests during a swing are rejected; no combo or input buffer yet.

`HealthComponent.apply_damage` is the damage entry point; it clamps damage, rejects post-death hits, and emits damaged/changed/died. Presentation reacts via signals. Death cancels combat and disables actor collisions. Enemy hits trigger brief stagger and cancel their current attack.

`AggroGroup` holds explicit pack membership and a shared target. Striking any member alerts all, even on lethal damage. `EnemyBrain` pursues directly with light separation, stops at melee range, and uses the same combat component as the player. Dead targets stop pursuit. No pathfinding, leash, or timed respawn is implemented; the arena has an open interior.

Collision layers: **1 static world**, **2 actors**. Bodies collide with both. Camera and melee occlusion queries use layer 1 only. Faction groups `players` and `enemies` select targets; encounter membership remains separate.

## Conventions and future systems

GDScript; snake_case files/functions, PascalCase classes, typed interfaces where useful. Store tuning in resources and mutable state in components. Do not mutate shared attack resources per swing. Signals report events; direct calls issue commands. Avoid global singletons without a concrete need.

This is a local simulation, not network ready. Controller requests → combat resolution → health application provide future authority boundaries. Multiplayer will require server-owned validation, stable network actor IDs, replication, and a latency policy. Instance IDs are only local deduplication keys. Skills/weapons can add resources, stats can supply derived damage, animations can follow phase signals, and loot can subscribe to death. These later systems are not implemented.

## Verification

Validated on 2026-09-19: **29 headless checks and 32 windowed checks passed**, with zero gameplay/script errors. The initial rendered arena screenshot was inspected. Windowed run used an NVIDIA GeForce GTX 1080 via OpenGL 3.3 compatibility. Interactive combat feel and balance still need human playtesting.

`./tools/run.ps1 -Test` exercises real scene/physics behavior: six spawns, movement and floor collision, camera input, attack phases, cleave, per-swing deduplication, cone exclusions, repeated swings, wall occlusion, group aggro, pursuit, enemy damage, death, and encounter reset. Failed checks produce a nonzero exit. Manual play additionally checks camera feel, cursor capture/release, R restart, F3, and visual readability.

Windowed tests use the OpenGL compatibility renderer and also check Escape/click capture and the left-click attack input path. Headless tests exercise camera look math because that display driver cannot capture a cursor. The restricted environment may emit `Failed to read the root certificate store` at engine startup; the offline gameplay tests still run. Windowed execution outside that restriction completed without that message. No network access is required.
