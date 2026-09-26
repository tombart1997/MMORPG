# Ironfield - Briarwood March

A small offline Godot 4.7.2 classic PC MMORPG prototype. Waystone Refuge connects four NPCs, introductory quests, merchant/Smith services and a winding route through three enemy bands. Persistent cursor navigation, selective loot, drag/drop inventory, equipment, upgrades and local persistence remain integrated. The playable class is **Ironvow / Turnwarden**, with six active skills, timed defensive counterplay and relevant basic sword attacks. The complete future roster (four classes, eight specializations, 48 skill concepts) is in [CLASS_DESIGN.md](CLASS_DESIGN.md). Only Turnwarden is implemented or selectable. All assets are original project assets, including the existing Blender character pipeline.

## Launch and environment

Verified tools: Godot 4.7.2.stable.official.ed1daf0bf, Blender 5.2.2 LTS, Git 2.37.0.windows.1.

From the repository root in PowerShell:

```powershell
./tools/run.ps1                         # Play Briarwood March
./tools/run.ps1 -Editor                 # Open Godot editor
./tools/run.ps1 -Test                   # All eight headless integration suites
./tools/run.ps1 -Test -Suite zone_loop  # Only the outdoor gameplay loop
./tools/run.ps1 -Test -Suite zone_loop -Windowed # Rendered loop and screenshots
```

The launcher redirects process-local APPDATA/LOCALAPPDATA and Godot logs to `game/.local/`, restoring the environment afterward. It changes no system settings. Importing `game/project.godot` directly and pressing F5 also works, but a normal Godot launch uses normal OS cache paths.

Progress saves locally, automatically every 30 seconds and on normal window close. F5 saves; F9 loads at the waystone. Launch automatically loads the latest valid snapshot. Death and revival preserve progression. The original arena remains in `scenes/arena.tscn` for focused regressions and may be run with F6 from the editor.

## Controls and gameplay

| Input | Behavior |
| --- | --- |
| WASD | Camera-relative movement when not committed to melee |
| Right mouse drag | Orbit camera while keeping the cursor visible |
| Left click | Navigate terrain; approach/interact with NPC or individual loot; select/approach/attack enemy |
| Space | Basic sword attack; press during recovery to buffer the next combo swing |
| 1-6 / action-bar buttons | Activate the six skills; Heelturn and Standard then require a ground click |
| Wheel | Camera distance, 4-13 meters |
| E | Talk to the nearest eligible NPC; otherwise pick up one nearest loot entry |
| Q | Use one field tonic for up to 45 HP when movement is unlocked |
| Escape | Cancel skill placement or movement intent; close active UI |
| R while dead | Revive at the starting waystone, retaining progression and inventory |
| I | Inventory/equipment/stats; drag to move/equip, Shift-drag to split; selection actions remain |
| J | Quest journal |
| F6 | Developer/reference selection: Turnwarden at the refuge; reselecting never resets cooldowns |
| F5 / F9 | Save / load local progression |
| F3 | Toggle debug attack cone, encounter status and combat diagnostics |

Visit Mara in Waystone Refuge, then follow the gate road to Briar Crossing (3 young mosslings), west to Old Pine Hollow (4 grown mosslings), and deeper east to The Broken Cairn (5 ironbacks). Striking a member alerts its group. Ordinary hits flash but do not cancel an enemy's committed attack. Amber torso color signals windup, red signals active frames, and weapon/bone motion follows the phase.

Kills give XP immediately and a separate visible gold pouches and difficulty-specific item entries. Young mosslings give 20 XP and 4-6 gold; grown mosslings give 25 XP and 6-8 gold; ironbacks give 40 XP and 9-12 gold. Only the Old Pine Hollow leader guarantees a Briarsteel Edge. See the economy tables below for drops and merchant prices. Click a chosen entry to approach and collect it; E takes only the nearest. Shards are inventory materials used by quests and the Smith. Players start with two tonics. The normal HUD shows HP, XP/level, gold, tonics and controls. Inventory contains 24 slots, tooltips, six equipment slots and calculated stats. Encounter/combat diagnostics appear only with F3.

Level 2 requires 80 XP; later thresholds increase by 40 each level. Excess XP carries over. Leveling adds 20 maximum HP and 2 Attack, and restores health. The sanctuary heals 18 HP/second when no pack has a target and the player is not attacking. Death allows R revival without a penalty in this milestone.

Fully defeated camps respawn after 18 seconds, postponed while a player is within 6 meters of the camp center. Corpses are removed when the new group spawns. Uncollected loot expires after 90 seconds. Groups stop pursuit and cancel committed attacks if the player dies, enters sanctuary, or exceeds the camp leash; living enemies return home. Enemy damage already taken is retained on return. Individual dead members do not respawn until their whole group is cleared.

## Melee commitment and sequencing

Normal movement is locked by `MeleeCombat.movement_locked()` throughout windup, active, and the configured recovery portion. All current attacks unlock at the end of recovery. This is specifically a melee-component rule, not a global actor movement restriction; future bow/ranged combat should use its own policy.

`AttackData` authors `lunge_distance`, `lunge_start`, and `lunge_duration` in meters/seconds. Combat integrates the displacement window and supplies velocity in the facing direction captured at attack start. Controllers combine permitted locomotion with combat motion and call `move_and_slide`; lunges collide with bodies/world instead of teleporting. This is root-motion-like simulation, not motion extracted from animation.

| Attack | Damage | Windup / active / recovery | Forward distance |
| --- | --- | --- | --- |
| Sword sweep | 25 | 0.18 / 0.16 / 0.30 s | 0.35 m |
| Returning cut | 25 | 0.15 / 0.16 / 0.28 s | 0.28 m |
| Heavy sweep | 35 | 0.25 / 0.18 / 0.38 s | 0.55 m |
| Enemy claw | 8 | 0.32 / 0.12 / 0.85 s | 0.30 m |

One Space press in recovery can buffer one follow-up. A new attack within 0.65 seconds of idle advances the three-step sequence; waiting longer or canceling resets it. Early windup/active presses are not buffered. Facing stays fixed during an attack and its buffered follow-up; between attacks, movement or selected-enemy focus establishes facing. Automatic focus refaces between committed swings.

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
    items/                    ItemData resources: swords, armor, tonic and moss shard
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
  tests/                      Six native SceneTree integration suites
  .godot/                     Ignored imports/cache
  .local/                     Ignored logs/editor data/screenshots
assets/                       Original source art (reserved)
blender/                      Editable .blend sources (reserved)
docs/                         Additional design notes (reserved)
tools/run.ps1                 Workspace-local launcher and test runner
```

`outdoor_zone.gd` composes terrain, lighting, player components, three camps, HUD, and the small session loop. `ZoneTerrain` builds a deterministic colored triangle mesh with collision, flat branching paths and camp clearings, gentle hills, trees, rocks, boundary stones, and a campfire landmark. Godot clockwise winding is required for the terrain's front-facing collision. Props are kept away from camp clearings and paths.

`ActorBody` owns its CharacterBody3D, health, melee component, and one replaceable `ActorVisual` scene. It has no input or AI decisions and no bone/mesh logic. `PlayerController` and `EnemyBrain` own movement decisions. `AggroGroup` owns target/member relationships, separately from `EnemyCamp`, which owns spawning, reward creation, corpse cleanup, and group respawn timing.

`HealthComponent.apply_damage` remains the single damage entry point. It rejects dead targets and hostile damage involving sanctuary, applies Defense, clamps damage, and emits damaged/changed/died. `heal` cannot resurrect actors. The zone explicitly revives the player and restores collision. All reward logic subscribes to death; repeat damage to a corpse cannot pay rewards again.

`PlayerProgression` owns XP, levels and kill count. `CharacterStats` calculates base + level + equipment contributions and synchronizes HealthComponent. `PlayerInventory` owns slot state and gold; `PlayerEquipment` owns equipped instances. `LootPickup` validates life, proximity, duplicate claim and capacity for the selected item before transfer. `DropTable` resources author independent item rolls. Details and extension instructions follow below.

## Replaceable character and enemy visuals

The humanoid and mossling PackedScenes use an `ActorVisual` adapter with `present(...)`, `react_to_hit()`, and `equip_visual(slot, scene)` methods. Gameplay feeds health, velocity, and combat state to this adapter, without addressing specific bones or animation assets.

The current adapter loads the existing imported skinned models and animation libraries through CharacterVisualProfile. It samples attack clips against gameplay phases, layers hit reactions, and maps BoneAttachment3D sockets from the profile. Item equipment uses the same socket interface and leaves the working rig and combo animations intact.

Named attachment points include WeaponSocket, OffhandSocket, ArmorSocket, HeadSocket, and boot sockets. Sword and chest armor are independent scenes; replacing one equipment child leaves the body and gameplay intact. To integrate a future humanoid or creature, replace the visual scene/adapter internals with an imported rig and mapped clips while keeping this interface. The skeleton, sockets, and animations may differ per creature; gameplay does not depend on them. Armor can later replace skinned mesh parts inside the adapter. Root motion should continue to be validated/applied by combat rather than making rendering authoritative.

## Conventions and future boundaries

GDScript, snake_case files/functions, PascalCase classes. Local -Z is forward, Y is up, feet at Y=0, distances in meters, timings in seconds. Keep tuning in resources and runtime state in components. Shared attack resources must not be mutated per swing. Direct calls issue commands, signals report events. Avoid global singletons without a concrete need.

Collision layers: 1 = static world, 2 = actors. Actors collide with both; camera and melee occlusion queries use only static world. Scene groups `players` and `enemies` identify factions; `loot` identifies pickups; AggroGroup membership defines an encounter.

Runtime art belongs under `game/assets/`; original art belongs under root `assets/` or `blender/`. Track Godot .uid files and .blend source. Ignore .godot, .local, temporary renders, backups, and logs.

This remains an offline simulation. Future multiplayer needs server-owned movement, attack validation, rewards and pickup validation, stable replicated IDs, and a latency policy. Local instance IDs only deduplicate hits. Navigation mesh, ranged combat, crafting, quests, trading and networking remain future work. AI uses direct pursuit and light separation; camp paths/clearings are open, and complex obstacle routing remains future work.

## Verification

The test runner imports once, rejects script import errors, runs the selected suites, and returns nonzero on failed checks or runtime script errors. Suite logs are retained under `.local/`.

- `combat_smoke`: retained arena checks movement/camera, attack timing, cleave, deduplication, exclusions, walls, aggro, enemy damage, death, and arena reset. It also checks persistent cursor, RMB orbit and Space input.
- `melee_commitment`: held retreat cannot defeat movement lock; exact authored forward motion; buffered combo steps; timeout reset; movement recovery; closest enemy lands a timed hit during commitment; uncommitted retreat avoids damage.
- `zone_loop`: outdoor traversal/collision, visual rig/equipment contract, two real combat encounters, XP and level growth, death reward uniqueness, pickup proximity/claim behavior, inventory, tonic use, group respawn safety, player death/revival, and preservation of session progression.

Headless combat and melee suites passed after the visual refactor. The outdoor loop passed headless and windowed, and `game/.local/zone.png` was visually inspected. Native windowed execution used OpenGL 3.3 compatibility on the GTX 1080. Sandbox startup may report inability to read the OS certificate store; this offline prototype does not use certificates/networking, and the unrestricted windowed run did not report it.

Checkpoints: `94b5df8` first playable slice; `9276e0c` verified melee correction before the outdoor/visual architecture work. Further combat balance and visual polish are intentionally deferred to playtesting.


## RPG progression architecture

The scene remains the composition root; no autoload manager or UI-owned state was introduced. Components are attached to the existing ActorBody only for the RPG player, preserving the arena and enemy combat behavior.

| Owner | Responsibility |
| --- | --- |
| PlayerProgression | Level, remainder XP, kill count; level_gained and changed signals |
| CharacterStats | Base, progression_bonus, equipment_bonus and calculated dictionaries, keyed by stable stat names |
| HealthComponent | Authoritative mutable current HP, synchronized maximum, physical damage/healing/death |
| ItemData | Shared immutable authored definition in data/items/*.tres |
| ItemCatalog | Resolves stable item IDs to resources; rejects duplicate IDs |
| ItemStack | Runtime ID, quantity and reserved properties dictionary; separate from shared resources |
| PlayerInventory | 24 slots of ItemStack or null; stack insertion, capacity, consumption, discard, gold |
| PlayerEquipment | Six slots of ItemStack or null; validated swap/unequip, visuals, attack-set selection |
| DropEntry / DropTable | Item resource, chance, inclusive minimum/maximum quantity; independent rolls |
| ProgressionSave | Versioned snapshot serialization, validation and backup recovery |
| InventoryPanel / ZoneHUD | Presentation, input routing and component commands |

Current formulas are intentionally simple:

- HP maximum = 160 + 20 * (level - 1) + equipment max_hp.
- Attack = 15 + 2 * (level - 1) + equipment attack. Starter sword adds 10.
- Swing damage = authored AttackData.damage * calculated Attack / 25. Thus the starter retains the existing 25/25/35 combo; Briarsteel Edge gives 33/33/46.2 at level 1.
- Incoming physical damage = max(1, raw damage - Defense), clamped to remaining HP.
- Movement speed starts at 5.5 m/s. Attack speed starts at 1.0 and is clamped to 0.2-4.0; it advances actual combat phases and lunge time, with animation sampling following those phases.
- Damage and speed are captured at swing start. Equipment cannot change during attacks or while dead. Shared AttackData resources are never modified.
- Equipment HP changes preserve absolute current HP, clamping when maximum falls. They never heal or resurrect. Level-up retains the previous full-heal behavior. Revival restores the calculated maximum.

Additional numeric stat keys can be added to base/modifier dictionaries without changing inventory, equipment or save structures. Future combat effects still need explicit consumers for criticals, resistance, life steal, etc.; those effects are not silently implemented by adding a key.

Equipment slots are weapon, head, chest, hands, legs and feet. Weapon and chest have visible attachments; head/hands/legs/feet currently provide gameplay slots without extra armor meshes. Empty weapon removes the sword and disables sword attacks. Weapon-family metadata, per-item attack sets, level requirements and reserved properties provide extension points for later class restrictions and other weapons; bows, dual wielding and specializations are not implemented.

The inventory opens with I and blocks player movement/attack initiation; the world continues running. Select a bag slot for details and Use/Equip, or an equipment slot for Unequip. Hover either for a tooltip. Swapping equipment uses the vacated inventory slot, so it works with a full bag. Unequip requires an empty slot. A full bag leaves the selected item on the ground; gold is a separate pouch that needs no bag slot; free space with consumables or the two-click Discard stack action. Ground entries retain their 90-second lifetime. Currency never consumes bag capacity.

### Adding items and equipment

1. Create an ItemData resource under game/data/items with a unique permanent id, display_name, description, item_type and value. Optional icon is a Texture2D; original category SVGs under assets/icons supply current inventory/shop icons.
2. Materials/consumables specify stackable and maximum_stack. A healing consumable supplies healing. Other use effects should be explicit gameplay commands, not UI code.
3. Equipment must be non-stackable, have one supported equipment_slot and a modifiers dictionary such as {"attack": 18.0} or {"defense": 3.0, "max_hp": 25.0}.
4. A sword supplies visual (PackedScene with its grip at the socket origin), weapon_family and an ordered attacks array of AttackData. New sword scenes reuse the original mesh with modest size variants. Do not modify the imported rig to change weapons.
5. Add a DropEntry referencing the item to data/drops/mossling.tres or a new DropTable, then assign that table to the camp. Chance is 0-1, quantity is inclusive. EnemyData.leader_reward is an optional authored guaranteed item for member zero; unconfigured legacy camps retain their direct resource fields for regression fixtures.
6. Keep resource IDs stable after release. Renaming/removing IDs requires a save migration. rarity, required_level and properties are reserved/simple metadata, not an affix system.

Test content: Wayfarer Blade (+10 Attack), Briarsteel Edge (+18), Cairnwarden Sword (+25 and +0.1 Attack speed), Traveler's Vest (starter visual), Briarhide Coat (+3 Defense, +25 HP), Cairn Cap (+1 Defense), Pathrunner Boots (+1 Defense, +0.5 movement), Field tonic and Moss shard. Mara sells a small fixed selection; Smith upgrading is implemented; crafting and random affixes remain excluded.

### Local persistence

Save schema version 3 stores level, remainder XP, kills, gold, current HP, a fixed inventory array, and equipment keyed by slot. Stack records are {id, quantity, properties}; empty slots are null. Version 2 added quest state. Version 3 adds class/specialization IDs, skill ranks and cooldown remainders; v1/v2 migrate to the reference kit. Resource paths and calculated stats are not serialized. Loading resolves IDs and recalculates using current definitions.

The file is user://progression.json (with .tmp and .bak siblings). With tools/run.ps1 this is under game/.local/roaming/IronfieldPrototype/. Direct editor launches use the regular Godot user data directory instead. Tests use rpg_test.json and disable normal autosave/autoload so they do not touch player progression.

Writes flush a temporary file, rotate the previous snapshot to backup, then rename the temporary file. Loading validates the entire snapshot before applying any changes, including IDs, stack limits, equipment slots, level requirements and numeric ranges; malformed primary files fall back to the backup. Unsupported versions are rejected. Versions 1 and 2 are accepted with default missing progression fields; future changes require explicit migrations. If existing saves cannot load, automatic saving is disabled for that session to preserve them; restore a valid backup or move the invalid files aside before starting a new save.

Launch and F9 return to the waystone; living saved HP is retained, while a dead snapshot revives. World camps, ground loot and positions are deliberately not persisted. F5 saves, F9 reloads, and normal play autosaves every 30 seconds and on window close. This is an offline foundation, not secure/server persistence.

### RPG verification

`./tools/run.ps1 -Test -Suite rpg_progression` covers stacking/overflow, full item pickup and currency, consumption, equipment swaps in a full bag, unequip, socket scene changes, HP clamping, Attack/Defense effects on real damage, attack-speed phase timing, movement speed, reward rolls, death/revival, save/load into a fresh composition, corrupt backup recovery and UI commands. Windowed mode captures `.local/rpg_inventory.png` and `.local/rpg_tooltip.png` and exercises mouse selection.

The previous combat/zone/character and RPG suites remain in the regression runner alongside settlement_loop, mmorpg_loop and skill_combat. The runner now rejects engine errors as well as script errors, except the known sandbox-only OS certificate-store warning. No system software or third-party assets were installed.


## Settlement, NPC and dialogue architecture

`Settlement` composes three low-poly buildings, a market canopy/counter, fences, road links, a hunting gate, signs and NPC placements. Physical collision belongs to buildings and gate posts; sanctuary rules do not rely on invisible walls. The existing terrain flattens the settlement footprint and excludes random trees/rocks there. Mara Fen sells supplies, Warden Elric explains the hunting route, Keeper Sella explains refuge/respawn, and Smith Oren upgrades equipment.

`NPCData` resources in data/npcs contain permanent id, display name, role, interaction range, facing policy, clothing color, dialogue pages and an optional ShopData. `WorldNPC` supplies the reusable world presentation and range/line-of-sight validation. NPCs are not combat actors and cannot become pack targets. Role routes merchant and Smith services; future trainers/storage can use the same interaction boundary.

`InteractionService` resolves E independently of the player controller. Eligible NPCs have precedence over loot. The nearest NPC wins, with its stable ID breaking equal-distance ties; an NPC behind static geometry is ineligible. Without an eligible NPC, E collects only the nearest eligible individual entry. Interaction requires life and no committed attack. NPCs turn toward nearby players.

`DialoguePage` resources contain text and a small response array. Each response supports text, next page index, action (talk/shop/close), and optional min_level. `DialogueSession` holds the current NPC/player/page and filters eligible responses. It validates choices and range without depending on UI. This gives progression-conditioned dialogue a starting point while avoiding a large quest or branching framework. Dialogue page position is session state and is not saved.

To add an NPC, create an NPCData resource with a unique id, author a few DialoguePage subresources, optionally reference a ShopData, then place a WorldNPC with that resource. Position and role are not encoded in player input code. To extend dialogue conditions, add explicit predicates to DialogueSession.options using authoritative progression state; do not evaluate UI text or execute arbitrary resource strings.

## Merchant transactions and UI

`ShopData` owns a stable shop ID, title and ordered ShopOffer resources. Each offer references ItemData and supplies its purchase price. Supplies are unlimited in this milestone, so merchant stock does not add transient save state. Player inventory has the existing fixed capacity.

`MerchantService.buy` validates NPC/range/line of sight, life, attack state, offer, quantity, gold and capacity before committing. It uses the authored offer price and the existing inventory insertion operation. `sell` validates the exact selected ItemStack still occupies the expected slot, verifies quantity, removes items and grants ItemData.value per unit. Equipped items must first be unequipped. Commands return a result message; UI never sets balances or prices. A per-inventory transaction guard prevents signal callbacks from reentering a partially completed trade. Repeating a sale on a removed/replaced stack cannot grant more gold. Purchases support 1-99 stackable units; non-stackable purchases are presented as one at a time. Partial stack sales are supported.

`TownPanel` renders dialogue and shop views. Merchant and bag lists show original category icons, names, unit prices and tooltips. Selection shows item description/modifiers and the difference from currently equipped gear via reusable `EquipmentComparison`; Buy/Sell displays the total quantity-adjusted price. Failures stay visible in the panel. Mara opens directly to trading, with Talk available for her dialogue.

`UISession` owns the single active modal: inventory, dialogue/shop, Smith or journal. I switches to inventory or closes it; Escape closes the active modal. Modal transitions clear pending attack input, preserve the visible cursor and consume the triggering event. Outside-panel clicks cannot reach the camera or combat. Death or leaving NPC interaction range closes NPC UI. The world continues simulating while a panel is open. F5/F9 still save/load; loading returns to town and closes the modal.

## Early economy and equipment curve

New characters start with 20 gold, the Wayfarer Blade, Traveler's Vest and two Field tonics. Existing saves retain their actual balances and gear; the starting grant is not reapplied on death or load. Two complete weak-group hunts supply at least another 24 gold, enough to buy the first 40-gold sword without requiring lucky item drops. Selling materials and spare gear speeds later purchases. Merchant resale values are below purchase prices; no shop arbitrage is intended.

| Merchant item | Purchase | Sell per item | Contribution |
| --- | ---: | ---: | --- |
| Marchguard Sword | 40 | 9 | +14 Attack |
| Quilted Jack | 30 | 7 | +1 Defense, +10 Max HP |
| Cairn Cap | 28 | 12 | +1 Defense |
| Pathrunner Boots | 50 | 12 | +1 Defense, +0.5 movement |
| Field tonic | 6 | 1 | Restore up to 45 HP |

Other sell values: starter sword 3, starter vest 2, Moss shard 1, Briarsteel Edge 12, Briarhide Coat 12, Cairnwarden Sword 22. Selling a stack pays quantity times its unit value. Gold remains currency outside bag slots. ItemData.value controls sell prices; ShopOffer.price controls buying independently.

At level 1, the sword curve is Wayfarer Blade (25 total Attack), merchant Marchguard Sword (29), dropped Briarsteel Edge (33), then Cairnwarden Sword (40 and 1.1x attack speed). The same 25/25/35 authored combo coefficients apply throughout. Every level adds 2 Attack, independent of gear. Armor progresses from the starter vest, through Quilted Jack, to Briarhide Coat (+3 Defense and +25 Max HP). With the existing subtractive Defense formula, early armor has a visible effect without making the stronger group harmless.

| Territory / band | Group size | HP each | Raw hit | XP each | Gold each |
| --- | ---: | ---: | ---: | ---: | ---: |
| Briar Crossing / Young Mossling | 3 | 60 | 6 | 20 | 4-6 |
| Old Pine Hollow / Mossling | 4 | 75 | 8 | 25 | 6-8 |
| Broken Cairn / Cairn Ironback | 5 | 110 | 11 | 40 | 9-12 |

`EnemyData` resources configure health, AttackData, visual scene/scale, movement speed, XP, gold range, DropTable and optional leader reward. All variants use the same ActorBody, EnemyBrain, AggroGroup and EnemyCamp implementations. Young mosslings are smaller; ironbacks are larger and carry an original dark ridge attached to the existing rig's ArmorSocket. Their attachment animates with the body, including death. No imported animation or AI implementation was copied.

| Drop table | Independent item chances (quantity 1) | Guaranteed leader item |
| --- | --- | --- |
| young | Moss shard 100%, Field tonic 25% | None |
| grown | Moss shard 80%, Field tonic 30%, Briarsteel Edge 18%, Briarhide Coat 18% | Briarsteel Edge |
| ironback | Moss shard 80%, Field tonic 40%, Cairnwarden Sword 22%, Briarhide Coat 28% | None |

Every death produces a gold pouch and one separate labeled pickup per item roll. Gold is deliberately selectable, not automatically absorbed. Difficulty-specific pools deliberately avoid large quantities of junk. The older mossling.tres table remains available as a deterministic regression fixture, but live camps use the three band resources. Prices, drops and EnemyData are tuning data, not scattered UI constants. This is an early offline economy, not a final MMO balance model.

## Sanctuary and recovery

`SafeArea` is a reusable spatial rule component. Waystone Refuge uses a radius of 11 meters around (0, 0, 15); the gate/road indicate the transition to hunting territory. EnemyCamp refuses to spawn inside sanctuary. AggroGroup rejects protected targets, and camps disengage when a target enters sanctuary or either the target or a pursuing member exceeds the authored leash. Disengage clears targets and cancels every committed swing; living enemies return home through the existing controller. HealthComponent also rejects hostile damage to or from sanctuary, covering same-frame/late hits and preventing safe-area attacks on enemies.

Death invokes the existing centralized recovery path: all camp targets/swings clear, modal UI closes, and R restores the player at the refuge with calculated maximum HP, collision and combat state reset. Items, equipment, gold and XP are retained. F9 uses the same safe relocation path. A later penalty policy can attach to this death/recovery boundary; no harsh loss is applied now. World camps and loose drops are still not persisted.

## Settlement verification

Run `./tools/run.ps1 -Test -Suite settlement_loop`, or add `-Windowed` for rendered captures. The complete test starts fresh in town, talks to the warden, visits Mara, rejects an unaffordable purchase, clears weak groups with real combat, gathers rewards, returns to sell, buys/equips a sword, verifies real damage, clears the middle band, equips its drop, and tests strong enemy damage and sanctuary retreat. It also checks quantity transactions, stale sale rejection, capacity, safe death/respawn and disk save/load after trading. Existing combat, melee commitment, zone, imported-character and RPG tests remain included in `-Test`.

Rendered captures are under game/.local: settlement.png, dialogue.png, shop.png and ironbacks.png. Tests disable normal persistence and use settlement_test.json for isolated save checks. No system software or copyrighted assets were added. Original UI icons are SVG source files under game/assets/icons.


## Persistent cursor, navigation and interaction

`WorldClickable` is a shared Area3D proxy for NPCs, enemies and loot on layer 4; static geometry is layer 1, actor bodies layer 2. `WorldPicker` resolves visible loot labels first (nearest screen label), then the closest static/proxy ray hit. Labels are separated in screen space; each still refers to its actual ground item. Static LOS blocks interaction through buildings.

`WorldInteraction` owns a replaceable intent and selected enemy. Terrain intent delegates to `PlayerNavigation`; NPC/loot intent repaths toward a validated interaction distance; enemy focus approaches and requests ordinary cleaving melee. Selection is not single-target damage authority. Death/despawn, manual movement and opening a modal cancel obsolete intent. RMB orbits without capture. NPCs retain the optional E-key range/LOS service.

`ZoneNavigation` bakes existing static collision into a Godot navigation region (0.5m actor radius, 2m clearance). The static map is synchronized once before path queries. `PlayerNavigation` requests paths, rejects inaccessible endpoints, follows waypoints and abandons stalled travel. Controllers still move physical bodies with `move_and_slide`. Hills, trees, buildings and ridge gaps participate in navigation; characters never teleport along paths. The route bends from refuge to camps at (14,-24), (-25,-50), (26,-82) in X/Z. The prior milestone supplied this layout; class work does not expand it.

`UISession` owns modal input. UI Controls consume pointer events before `_unhandled_input` reaches world selection; skill-bar clicks use the same rule. Skill placement receives only an unhandled world click, so clicking a tooltip, item slot, action bar or HUD cannot place an area or move the player. Numeric skill requests validate modal state independently.

## Inventory drag/drop, Smith and quests

`ItemSlot` uses Godot native drag payloads containing player, source slot, exact ItemStack reference and quantity. `PlayerInventory.move_slot` owns split/merge/swap mutations; `PlayerEquipment.to_inventory` owns equipment-to-bag swaps. Stale references and invalid destinations reject without deleting items. Shift-drag moves half a stack. Instance properties, including upgrade level, move with the item.

`UpgradeProfile` resources author cumulative step bonuses, gold/material costs, probabilities and failure policy. `UpgradeService` checks the Smith, range, current instance, resources and maximum before charging. Oren's panel accepts dragged unequipped gear; selection only prepares a quote, and an explicit confirmation performs the attempt. Current +1/+2/+3 attempts cost 15/30/55 gold and 1/2/3 Moss shards at 100/80/60 percent. Sword steps add 2/3/4 Attack; armor steps add 1 Defense and 3 HP each. Failure spends costs but retains both item and level. Optional downgrade policy exists; destruction is not implemented. Extend the authored steps to raise the cap. `ItemStack.modifiers()` is the single source combining item definition with instance upgrade bonuses; equipment, comparisons and skill scaling use it.

`QuestData`, `QuestCatalog` and `PlayerQuests` separate stable definitions from per-player status/counts. The three quests are A Place on the Road (talk to Mara and return), Briar Watch (three young Mosslings plus three carried shards, then return), and First Temper (meet Oren and successfully upgrade). Quest turn-in validates NPC/range/prerequisites, preflights reward space and consumes collection items atomically. Completed quests cannot reward twice. Kill, talk, collect, return and upgrade objectives share typed event/count handling. Collection progress reads the current bag. NPC indicators are [!] available, [...] involved, [?] ready. J shows objectives/rewards. Save state is keyed by quest ID, not UI labels. Add a resource and catalog entry for future quests; preserve objective ordering or migrate saved counts.

## Class and skill architecture

Read [CLASS_DESIGN.md](CLASS_DESIGN.md) before adding a class: it specifies inheritance, identity, all six skills per specialization, geometry/timing, interactions and intended PvP counterplay. Seven future specializations are documentation only.

- `CharacterClassData` defines the base identity and weapon policy. `SpecializationData` references its base and exactly six `SkillData` resources. The current authored pair is ironvow/turnwarden. New games and old-save migration receive this complete kit; F6 is a refuge-only developer selection command and never grants cooldown resets.
- `SkillData` contains permanent ID, targeting model, effect shape, geometry, windup/recovery/cooldown, animation, icon/color, rank limits/scaling and an ordered array of effect resources. Data lives under `game/data/skills`. Resources assign script before exported properties. Maximum rank is currently 1; the rank scaling field is a future extension, not an implemented progression tree.
- `PlayerSkills` validates ownership, life, UI, weapon, current action and cooldown, then creates `SkillContext`. That context snapshots Attack/rank, chosen target, direction, ground point and optional Answer consumption. It owns windup/execution/recovery, bounded physical skill motion and cooldowns. Failed validation spends nothing; accepted commitment starts cooldown and spends Answer immediately. There is no skill input queue.
- `SkillTargeting` provides common range/LOS/navigation checks and single/arc/circle/self/none target gathering. Input policy (selected/facing/self/ground/direction) is separate from shape, so selecting an enemy does not remove area hits. Ground skills arm a preview and wait for a world click. Manual movement, a basic-attack command or Escape cancels placement. Directional travel requires continuous navigable ground and uses collision. Current out-of-range skills reject with feedback; basic enemy focus retains its existing autoapproach.
- `SkillEffect` subclasses execute damage, status, movement or persistent-area commands. Adding another effect means a small explicit handler and data, not an ability-ID switch in input/UI. `SkillArea` owns finite periodic zones. There is no arbitrary expression/script interpreter, network layer, or generic implementation of every future roster mechanic.
- `CombatStatuses` is present on all actors. Hostile statuses use the same life/sanctuary boundary and can alert packs. Health applies Defense first, then the strongest guard/shelter reduction. Controllers apply strongest slow to ordinary locomotion and consume bounded push motion through physics. Basic melee reads Open at actual hit time. Existing health/death/reward signals still own kill credit, quests, loot and XP.
- `ActorVisual` samples imported skill clips from authoritative phase progress; animations never apply damage or move the body. `SkillVFX` draws thin ground arcs/rings, `StatusVisual` shows guard/Answer/Open/slow, and persistent Standard has a small pennant. Effects leave enemies visible. `SkillBar` is presentation and request routing only: six clickable buttons, 1-6, cooldown text/dimming, placement state, brief feedback and tooltips.

### Turnwarden rules and usage

| Key | Skill | Main decision |
| --- | --- | --- |
| 1 | Riving Stroke | Select a close enemy; open the narrow front for four seconds of stronger basics |
| 2 | Held Line | Face the anticipated claw and guard one frontal hit during a 1.2s window |
| 3 | Heelturn | Click nearby ground to step out of pressure, leaving a short slow patch |
| 4 | Gate Sweep | Cash out Open on a wide front; Answer adds outward push |
| 5 | Standard of Ash | Click ground to establish a five-second defensive/slow area |
| 6 | Due Return | Commit to one selected enemy; Answer increases damage and heals only on hit |

A successful guard reduces one frontal hit by 60% and gives one five-second Answer. Gate Sweep and Due Return consume it at commitment, including on miss. Other skills leave it available. Standard reduces damage by 20%; it does not multiply with guard. Basic attacks exploit Open for 25% additional raw damage. Sweep consumes Open for its authored bonus. Ordinary incoming damage does not cancel a cast. Skills and basics cannot overlap. Changing selection during windup cannot redirect an accepted skill; single-target death/escape/obstruction misses, while an already aimed arc retains its geometry and may hit other foes. Movement input resumes after commitment. Skill requests stop automatic melee intent but retain selection: click the enemy or press Space to resume basics.

Statuses are bounded, nonstacking entries by effect ID. Reapplication uses the greater remaining duration and strength. Slows from different IDs use the strongest; guard/shelter likewise use the strongest reduction. A Standard refreshes short aura statuses only while in range and LOS. Leaving it loses the benefit within .25s. Death/load clear transient statuses, casts and owned areas. No stuns, immunity windows or escalating passive damage meter are implemented.

At Attack 25, Riving deals 22.5 raw; basic Open hit 31.25; Sweep 25 or 35 versus Open; Return 32.5 or 45 with Answer (15 healing on a damaging hit). Gear and level change these through final Attack. Attack speed affects basics, not skill cooldowns/windups. Timed guard and area placement are useful even with starter gear; stronger gear remains relevant. The live regression records damage taken before level-up healing so a full end-of-fight HP bar does not hide actual enemy pressure.

### Skill persistence and extension

Version 3 adds `skills: {class, specialization, ranks, cooldowns}`. Class/spec IDs and known rank bounds are validated before changing any gameplay state. Cooldown remainders are saved and restored; they do not tick while the application is closed. This prevents F9 or respawn from freely resetting the kit. Answer, guard, Open, current casts and ground areas are transient and are never persisted. Versions 1/2 without skill data migrate to the complete reference specialization; existing item/quest/currency progress is retained. Future specialization data needs an explicit catalog and migrations before making more pairs selectable.

To add an implemented skill, author its SkillData and effects, provide an imported animation and original icon, then include it in an implemented six-slot specialization. Use existing target models/shapes first; add a shared range/shape policy only when a new mechanic needs it. New stats need an explicit consumer; a dictionary key alone does not implement elemental damage or healing power. Skill rank expansion must author and test actual rank curves, update maximum_rank and define migration behavior. There is no rank purchase interface in this milestone.

### Animation source and verification

`blender/scripts/add_skill_animations.py` opens the existing traveler.blend and adds/replaces only skill_guard, skill_step, skill_plant and skill_riposte. It preserves prior meshes and locomotion/basic/hit/death clips, then exports traveler.glb and the manifest through the existing builder. The full builder also generates these clips. Run `blender --background --factory-startup --python-exit-code 1 --python blender/scripts/add_skill_animations.py` from the repository root to rebuild only the skill clips. Reuse attack_01 for Riving and attack_03 for Sweep. Godot samples each signature animation at the same .30 execution marker used by the original combat pipeline.

`./tools/run.ps1 -Test` runs eight suites. `-Suite skill_combat` verifies all six effects, animation contracts, mouse/hotkey activation, ground-click routing, cooldown/commitment rejection, selected-target snapshot, missing/dead/out-of-range targets, Open/basic damage, guard direction, Answer damage/healing, stacking/expiry, physical movement, death/respawn, validated save migration, Smith scaling and live weak/strong encounters. `-Suite mmorpg_loop` preserves the road/NPC/quest/selective-loot/Smith/native-drag/save playthrough. Other suites cover original combat, commitment, zone, imported character, RPG and merchant behavior. Add `-Windowed` for rendered captures under game/.local/turnwarden_*.png. Test snapshots use isolated filenames and never overwrite ordinary progression.json.

### Class/skill milestone architecture review (2026-09-20)

The roster and implementation passed a focused review with constraints; this section is the handoff for the next class session. The 48 concepts have distinct purposes and the eight specialization identities are viable. The primary design risks are setup taxes and upkeep loops in Redmarch, Knotbinder, Hearthwright and Briarchanter. Their independent skills must remain useful enough that their central mechanic creates choices rather than a mandatory opener and rotation. `CLASS_DESIGN.md` records the identity and cross-kit guardrails.

Turnwarden is a sound reference for the currently implemented domain. Riving keeps basics relevant; Held Line creates a hostile-action response; Heelturn and Standard work independently; Answer presents a real choice between group control and a single-target counter. Commit timing, misses, cooldowns, target snapshots, obstacles, death and equipment changes have predictable rules. Use those properties as conventions. Do not copy Turnwarden's concrete state fields to kits with fundamentally different execution lifecycles.

The following changes are required before a second specialization becomes selectable:

- Replace `PlayerSkills.REFERENCE` and reference-only save validation with a small catalog of implemented class/specialization resources. The catalog must validate stable class/spec pairing, six unique skill IDs, weapon policy, ranks and cooldown keys before mutating state. Add explicit version migration when the selection format changes.
- Make `SkillBar` rebuild its six buttons when specialization changes. It currently builds once, and its Answer prompt is Turnwarden-specific even though the title now comes from data. Specialization-owned opportunity presentation should supply future prompts.
- Keep targeting policy, target affiliation/object kind, effect geometry and execution lifecycle separate. `SkillTargeting` currently supports hostile `ActorBody` targets and immediate single/arc/circle/self/none resolution. Do not grow that one shape enum to represent allies, destructible anchors, projectiles, channels and delayed impacts.
- Introduce a structured damage request/result before a kit or encounter needs physical/elemental types, penetration, crits, blockability, shields, invulnerability, PvP coefficients or boss rules. `HealthComponent.apply_damage(amount, source)` cannot express them, and Held Line currently filters every hostile actor hit rather than authored physical damage.
- Replace or front `CombatStatuses` with authored status definitions before status variety expands. Definitions will need polarity/category, source and stack key, periodic behavior, attribution, cleanse rules, resistance/immunity and boss/PvP crowd-control policy. The current greater-duration/greater-strength ID dictionary remains suitable for Turnwarden's bounded Open, guard, Answer, shelter and slows.
- Move shared movement away from fields owned by `PlayerSkills` when another kit needs dashes, pulls or knockback. The replacement needs collision-validated endpoints, interruption policy and an authoritative motion result. Preserve the current rule that gameplay moves the body; animation only presents it.
- Add authored execution events or timing markers when a skill needs multiple hits, a projectile release or a channel tick. The universal normalized `.30` animation sample is presentation for this melee kit and must not become authoritative gameplay timing.

Other limitations should be addressed only when their trigger appears. `SkillDamageEffect` and `SkillStatusEffect` currently execute in order but cannot condition a later effect on hit/miss/invulnerability. `SkillArea` scans hostile actors each physics frame and hard-codes shelter/slow payloads; this is acceptable for two small zones, but multiple persistent objects need overlap/tick scheduling, data-owned payloads, ownership caps, destruction and lifetime rules. `StatusVisual` and the generic ring/flash presenter enumerate current states; add a presenter registry when another kit needs new readable state rather than putting gameplay authority in VFX. `SkillContext` snapshots final Attack and rank, which is correct for Turnwarden, but later scaling stats must be explicit and a future server must reconstruct and validate context from commands instead of trusting a client snapshot.

One contained defect was corrected during review: basic melee no longer names the Turnwarden `open` status. It asks the target status policy to modify incoming basic damage. Skill tooltips now take their equipment requirement from data, and the skill-bar title uses the selected specialization. These changes remove current boundary leaks without introducing a broad framework. Turnwarden-only Answer consumption and bonus/heal/push fields remain intentionally documented debt; replace them with bounded conditions or specialization-owned effects before copying them into another kit.

The focused test is strong integration coverage for the implemented domain: it drives real UI input and gameplay, verifies all six skills, commitment conflicts, animation windup, range/LOS/obstacles, target death and retargeting, actual damage/healing/control/movement, area expiry, death/respawn, gear scaling, save migration and live encounters. Its resource checks also require six unique stable IDs and valid basic timing/geometry/rank data. Gaps are intentional until their systems exist: projectiles, channels, delayed effects, friendly/destructible targets, damage types, status immunity/resistance, boss rules and PvP. Before expanding those domains, add unit-level policy tests in addition to the live suite. Also add exact cooldown expiry, invalid rank/cooldown variants, sanctuary skill rejection, post-commit LOS/range rules, overlapping source/refresh behavior and area ownership-cap tests when touching those paths. The rendered captures confirm clips are selected; pose readability still requires manual inspection. Extract shared fixtures from the inherited `mmorpg_loop` test before the focused suite becomes substantially larger.
