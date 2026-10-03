# UI, readability and player feedback

The interface should let the player decide where to hunt, what to spend and what can be lost. Use compact slate/jade panels, brass edges, off-white type and restrained red danger accents. Keep the world and enemy silhouettes visible.

## Main HUD

| Element | Required information | Feedback |
| --- | --- | --- |
| Health | Current / maximum HP | Readable loss and heal, no full-screen flashes |
| XP bar | Current / required XP, level and 25/50/75% marks | One short notice per newly earned stat point |
| Skill bar | Six ability icons, key, cooldown and usable state | Small M/G badge and opportunity highlight |
| Target | Name, level, tier and HP | Elite symbol plus shape, not colour alone |
| Loot | Item name, quantity and rarity | Short arrival beam for rare gear; clean click target |
| Route guidance | Discovered district and recommended band | Optional indication when level gap strongly lowers rewards |

At 100% XP show a combined level-up/stat-point/skill-point notification. Large multi-level gains can group repeated notices while still granting each award. A notification is feedback, not the authority that grants the point.

## Character and skill sheets

Character panel shows VIT, STR, DEX and AGI individually, assigned/unspent points, base stats, gear bonuses and final derived values. A preview of the next allocation shows its exact effect. Stat reset displays gold cost and resulting refund before confirmation.

Skill panel shows basic rank, M progress, G completion, current and next potency, owned Leaves and next cost. Display M10 completion as **G — maximum**. A disabled button states the real missing requirement: basic rank, skill point, Leaf count, gold or combat state.

## Smithing panel

For a T3 +6 weapon attempting +7, show: **Success 50% / Failure 50%**, exact item name and current modifiers, 1,400 gold, 7 Moss Shards, 9 specified T3 trophies, 2 Ore and 1 Wakeglass. The final action reads **Attempt +7 upgrade**. Beside it show **Failure destroys this item and spends all listed costs** in readable text.

The player should never infer the destruction rule from a tooltip alone. Cancel is always free. While resolving, disable duplicate actions. Success and failure identify the resulting/lost item, and refresh both equipment and bag. The +9 panel says maximum reached.

## Bestiary and map

The bestiary exposes discovered creatures, their model portrait, level, tier, EXP, habitats and item base drop chances. If displaying effective rates, label the player's current level and show the applied multiplier. Do not label a 0.2% base rate as the effective probability when the levels differ.

The map distinguishes safe settlement, road, regular hunting band, camp leader, discovered Fracture and region gate. Reveal secret cores only after discovery. Hotkeys and map zoom must not steal attack input while panels are closed.

## Accessibility and interaction

Pair colour with a symbol/text for rarity, tier and + level. Blue/red/violet sparks remain visible upgrade cues, while icons and tooltips communicate the same values. Provide UI scaling, remappable keys, separate music/effects volume and a reduced-effects option. Maintain readable typography on bright parchment and dark combat scenes.

Technical diagnostics belong behind development controls such as F3. Item GUIDs, import details, bone names and error traces do not belong in ordinary player screens.
