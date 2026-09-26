# Ironfield 0.1 readiness and playtest record

## Scope and audit, before implementation

This milestone combines the first-hour brief with its explicit map, action-bar and horse additions. Those additions supersede the pasted brief's older prohibition on mounts. The art benchmark and mass-mob work are retained; no additional specialization, region, crafting or network layer is planned.

The current game begins in Waystone Refuge, south of the first Mossling clearing called Briar Crossing. The fresh-start mouse-driven regression was run for this audit. The existing beginning requires Elric → Mara → Elric before the hunting introduction; six skills appear together; Q is a hard-coded tonic action; the HUD has no spatial map. Equipment, upgrades, rare rewards, encounter persistence and navigation already work. The art scene has been repeatedly captured and visually reviewed during the preceding milestone.

### Implementation plan

- Preserve the established paths and safe spawn. Present the arrival district as Briar Crossing / Waystone Refuge, distinguish the first hunting clearing, and replace the opening errand emphasis with concise field guidance.
- Reuse the three introductory quests and add one purposeful Fracture follow-up. Introduce equipment, a safe first upgrade and the rare-catalyst decision through rewards and dialogue; allow normal farming independently of quests.
- Add one small region definition and player discovery state. Maps show known settlements/NPCs, visited landmarks, facing and nearby observed Fracture state. They do not enumerate enemy packs or loot.
- Keep six data-driven specialization buttons. Add two inventory-backed consumable assignments and one utility assignment, with hotkeys, drag/drop validation and persistence.
- Add one data-defined horse, acquired using an existing inventory item from Mara. Mounting enlarges the actor's collision only after a clearance check, increases movement speed through the current controller, offsets the existing camera, and shows a simple original horse. Dismount before fighting/conversation; death and loading restore the unmounted state without losing ownership.
- Extend snapshot validation before any mutation, with migration from versions 1–4. Add focused state/UX/route tests, then run all regressions and record actual clear-time and foot/horse travel measurements.

## Validation constraint

Automatic approval review rejected the last requested rendered crowd rerun because the account usage limit was reached. Further graphical runs and Blender exports requiring escalation cannot currently be assumed available. Read-only inspection, code changes and headless gameplay checks can continue. Existing captures are evidence for the preceding art milestone, not evidence that new map/mount UI has been visually checked. Fresh-start automation must not be described as a human 45–60-minute playtest.

## Readiness categories

### BLOCKERS

- Implementation and validation in progress.
- Rendered review of the new 0.1 interface/horse and independent zero-explanation human playtests are pending.

### IMPORTANT POLISH

- Confirm first-hour pacing and encounter readability through actual fresh-start play.
- No existing audio infrastructure or original audio library was found in the inspected project; audio remains a production need.

### LATER CONTENT

- Additional classes/regions, multiplayer, crafting, a larger item catalog, mount species/equipment/breeding and mounted combat.
