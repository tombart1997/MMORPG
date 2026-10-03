# Town services, NPCs and quest structure

![Smith Oren, Keeper Sella and Bram, alongside the mounted hero](../art/town_mounts.png)

## Town roles

| Current NPC | Service / identity | Target design role |
| --- | --- | --- |
| Keeper Sella | Waystone keeper | Arrival, return point, stat/skill reset and region guidance |
| Mara Fen | Refuge merchant | Starter supplies and accessible replacement gear |
| Warden Elric | Road warden | First hunting quest, road safety, regional threat story |
| Smith Oren | Smith | Nine-step upgrades, exact risk quotes and Fracture introduction |
| Darin | Weapon merchant | Ordinary weapons for each unlocked hunting band |
| Hessa | Armor merchant | Ordinary armor for each unlocked band |
| Sera | Apothecary | Consumables and recovery preparation |
| Ilyra | Relic crafting merchant | Trophy-based rare crafting and conversions |
| Bram | Stable merchant | Trail Bridle and horse preparation |
| Scout Vela | Basin scout | Cinderfall quests, outpost guidance and basin progression |

Keep services physically distinguishable through tools and clothing. Oren has a leather apron and hammer; Sella uses slate/jade robes and an old lantern; Bram carries tack. Town interiors and signs should indicate service roles with familiar symbols rather than floating implementation text.

## Existing opening quest chain

| Existing quest | Action taught | Design update |
| --- | --- | --- |
| A Place on the Road | Meet Mara and learn preparation services | Teach bag and affordable replacement equipment |
| Briar at the Gate | Hunt Young Mosslings and collect three shards | Show first quarter-level point; hunting also works without a quest |
| A Steadier Edge | Successfully upgrade one equipment item | Explain destructive failure before any uncertain attempt |
| A Heart Beneath the Roots | Discover and destroy Briarwake, return to Oren | Introduce distinct Wakeglass and Mastery Leaf purposes |
| Through the Veil | Enter Cinderfall and hunt Ember Hounds | Teach next-region level matching |
| Shattered Web | Defeat four Glass Spiders | Require a readable mixed-threat hunt |
| Heart of the Rift | Defeat the Rift Sentinel | End the basin introduction with a boss tell |

Current quest rewards are one-time grants and exempt from random-drop level scaling. Any guaranteed tutorial equipment or ingredient must be named in the quest resource. Do not secretly guarantee ordinary repeatable loot through a quest flag.

## First-session target — proposed

First 10 minutes: meet keeper/merchant, try basic attacks, kill a short pack and see a quarter-level award. Next 10–20 minutes: allocate a stat point, select a first ability, buy a useful upgrade and finish a short hunting route. Next 20–40 minutes: meet Oren, try a T1 +1 upgrade, learn +9 risk visually, and discover Briarwake's warning rings. Later preparation leads to the first successful core destruction and mastery-loot explanation.

These are pacing targets rather than guarantees from the current XP curve. Measure them in a fresh save with ordinary drops and no debug gear; tune encounter density and travel distance if the quarter reward arrives too late.

## Quest design rules

One quest introduces one primary mechanic. Avoid mandatory rare-drop objectives with extremely long tails. Discovery objectives activate once, kill counts use real death events, and upgrade quests only count success. A quest can recommend a route without making ordinary hunting dependent on accepting it.

Future regional chains pair one social problem with a visible world threat: reopen fen crossings, recover shrine records, protect ridge roads and investigate the Crownless Warden. Repeatable bounties offer gold or supplies with explicit completion limits; they cannot bypass mastery loot rules through unlimited guaranteed Leaves.
