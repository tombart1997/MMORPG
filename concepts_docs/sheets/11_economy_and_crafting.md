# Economy, ingredients and crafting

![Mastery and smithing materials](../art/fractures_mastery.png)

Gold comes from hunting, explicit quest rewards and selling unwanted loot. It leaves the economy through supplies, replacement gear, smithing, crafting and optional resets/travel. Destructive smithing also removes equipment, while successful mastery learning removes Leaves.

## Exact trophy ingredients by gear tier

For this first proposal every item in one gear tier uses the same specified trophy. Later family-specific recipes can vary that input, but cannot accept arbitrary trophies without a documented recipe change.

| Gear tier | Required trophy / item ID | Primary current drop source |
| --- | --- | --- |
| T1 | Meadow Wolf trophy / `meadow_wolf_trophy` | Meadow Wolf, level 1 |
| T2 | Grey Wolf trophy / `grey_wolf_trophy` | Grey Wolf, level 6 |
| T3 | Blacktusk trophy / `blacktusk_trophy` | Blacktusk, level 11 |
| T4 | Ironhide Boar trophy / `ironhide_boar_trophy` | Ironhide Boar, level 16 |
| T5 | Obsidian Boar trophy / `obsidian_boar_trophy` | Obsidian Boar, level 21 |

Use the actual item display names and base rates in [mob_drops.csv](../tables/mob_drops.csv); the table above names the enemy origin. The [smithing table](../tables/smithing_upgrades.csv) gives the count for every tier/+ step. All ingredients, including required trophy IDs, are expanded there.

## Materials and acquisition

| Material | Role | Proposed acquisition |
| --- | --- | --- |
| Moss Shard | Common ingredient at every + step | Existing Mossling/core drops; keep on all higher-band Fractures at 80%, quantity 1–2 |
| Tier trophy | Gear-band ingredient | Existing matching mob loot; current-band Fracture material rolls and conversion provide later access |
| Tempered Ore, new | +4–+9 construction input | Fracture chance 35/45/55/65% by core band, quantity 1; optional paid conversion |
| Wakeglass Ember | +7–+9 input | Current Briarwake base 18%; stronger Fractures 22/28/35%; no guaranteed upgrade |
| Mastery Leaf, new | M1–M10 learning | Destroyed core only; distinct from Wave drops and Wakeglass |

Proposed extra core material rolls: each core independently offers all listed tier trophies at **60% each**, quantity **1–3**, for tiers up to its own tier. Briarwake offers T1–T2; Cairnwake T1–T3; Ashwake T1–T4; Crownwake T1–T5. Each of these rolls receives the core's level multiplier. This keeps older recipes supplyable through current-band farming without bypassing the level-gap rule. See [fracture_materials.csv](../tables/fracture_materials.csv).

## Crafting proposals

| Recipe at Ilyra / Oren | Inputs | Output / certainty |
| --- | --- | --- |
| Tempered Ore conversion | 10 Moss Shards + 150 gold | 1 Ore, guaranteed |
| Trophy conversion | 3 trophies from the next higher gear tier + 50 gold | 1 specified trophy of the adjacent lower tier, guaranteed |
| Band relic construction | 20 specified band trophies + 5 Ore + 2 Wakeglass + 1,000 × tier gold | One chosen existing-band relic at +0, guaranteed |

Crafting does not copy the input weapon or carry its + level onto a new item. The output is a fresh item. Craft inputs are consumed atomically only when the requested output can be granted. Rare world drops remain a faster lucky route, while crafting provides a measurable long-term alternative.

## Supply and shop rules

Merchants always supply a viable ordinary weapon and armor for the player's unlocked hunting band. Recipes and prices are explicit. Sellback is below buy price and below material crafting cost, so buying/crafting/selling cannot print gold. Mastery Leaves have no NPC purchase path in this proposal; they retain the Fracture-farming requirement.

Existing Trail Bridle price is **240 gold**, and existing horse speed is **8.8 m/s**. Other merchant prices remain current resource values until a separate tuned shop table is approved. Do not pretend the proposed crafting recipes are already present in the merchant resources.

## Balance measurements

Track gold earned per minute, potion spending, ingredient yield, replacement cost, smithing cost per surviving + level and Leaves per core clear. Evaluate equal-level rates first, then realistic route level differences. The product of destructive success rates is central: a 15% final step does not mean a fresh T5 +9 item takes only seven base items.

Future player trade can redistribute ingredients and replacements. It must preserve item identity and mastery ownership; skill-learning records are character progression, not tradeable equipment properties.
