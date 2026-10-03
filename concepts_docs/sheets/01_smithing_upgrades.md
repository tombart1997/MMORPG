# Smithing upgrades — +0 to +9

**Fixed:** all equipment supports +9; failed upgrades destroy the item; higher gear tiers are riskier. **Proposed:** the exact odds, prices and ingredients below.

![Weapon and armor tempering progression](../art/gear_upgrades.png)

## Success and failure rates

Each column is the destination upgrade. Failure chance is `100% − success chance`. Weapon, armor and accessory profiles use the same tier table.

| Gear tier / item level band | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T1 / 1–5 | 100% | 100% | 95% | 90% | 85% | 80% | 70% | 60% | 50% |
| T2 / 6–10 | 100% | 95% | 90% | 85% | 75% | 65% | 55% | 45% | 35% |
| T3 / 11–15 | 100% | 95% | 85% | 80% | 70% | 60% | 50% | 35% | 25% |
| T4 / 16–20 | 98% | 92% | 83% | 78% | 68% | 58% | 45% | 30% | 20% |
| T5 / 21+ | 95% | 90% | 82% | 75% | 65% | 55% | 40% | 25% | 15% |

Tier is an item property derived from its intended level band, not the player's level, rarity colour, or current + value. Rare and ordinary equipment in the same band use the same risk profile. The [equipment catalogue](../tables/equipment_catalogue.csv) distinguishes current item level requirements from proposed tier assignments.

## Required loot and gold

`n` is the destination + level; `t` is the gear tier. Each attempt consumes Moss Shards × `n`, a matching tier trophy × `ceil(n / 3) × t`, the listed Tempered Ore and Wakeglass, plus gold. The exact trophy IDs are listed in [economy and crafting](11_economy_and_crafting.md) and expanded in each CSV row. This is one specific trophy type, not a choice of any item with that tier. Tempered Ore is a proposed new material.

| Destination | Base gold | Moss Shards | Tier-trophy count | Tempered Ore | Wakeglass Ember |
| --- | ---: | ---: | ---: | ---: | ---: |
| +1 | 15 | 1 | 1 × t | 0 | 0 |
| +2 | 30 | 2 | 1 × t | 0 | 0 |
| +3 | 55 | 3 | 1 × t | 0 | 0 |
| +4 | 95 | 4 | 2 × t | 1 | 0 |
| +5 | 150 | 5 | 2 × t | 1 | 0 |
| +6 | 230 | 6 | 2 × t | 2 | 0 |
| +7 | 350 | 7 | 3 × t | 2 | 1 |
| +8 | 520 | 8 | 3 × t | 3 | 2 |
| +9 | 760 | 9 | 3 × t | 3 | 3 |

Multiply base gold by T1 **1**, T2 **2**, T3 **4**, T4 **7**, T5 **11**. Exact expanded values, failure rates and accumulated risk are in [smithing_upgrades.csv](../tables/smithing_upgrades.csv).

Example: a T3 weapon at +6 attempting +7 costs **1,400 gold, 7 Moss Shards, 9 specified T3 trophies, 2 Tempered Ore and 1 Wakeglass**. Success is **50%**; failure is **50%** and destroys the weapon. Attempting the same transition on T5 costs 3,850 gold and 15 matching T5 trophies; success is 40%.

## Transaction and failure

1. The player selects one item at Smith Oren while outside combat. The screen shows item identity, current +, destination +, exact success and failure probabilities, resulting stats, and all ingredients.
2. The player confirms the displayed attempt. Missing costs, wrong item, distance changes or a changed inventory cancel without payment or a roll.
3. Gold and ingredients are consumed once. One roll determines the outcome.
4. Success preserves the item's identity, sockets and unrelated modifiers, then sets the new + value. Failure removes the complete item including attached modifications. Equipped items are unequipped atomically and their stats/visuals are removed.
5. Persist the outcome before allowing another attempt. A crash, save reload or duplicate click must not re-roll or spend twice. The outcome text names the lost item on failure.

No loss occurs from opening or cancelling the panel. A +9 item has no further quote. There is no downgrade or retention on a failed attempt. Quest progress only records a successful upgrade.

## Risk across the entire route

The probability that one +0 item survives to +9 is the product of all nine success probabilities. It is much smaller than the final step's probability. The workbook includes both route survival and expected fresh base items, so repeated destructive attempts can be evaluated before release. These are mathematical expectations, not guaranteed attempt counts.

Keep a viable replacement weapon available from town. Tune gold and ingredient supply against real farming time, especially for T4/T5. A failed rare item should remain a significant loss; avoid requiring a +9 item merely to access the next region.

## Implementation difference

The current `UpgradeService` supports profile-sized progression, retains failed items by default, and optionally consumes Wakeglass to guarantee success. Existing profiles have three steps. This sheet requests replacing those rules with nine steps and destruction; it does not claim the runtime has already changed.
