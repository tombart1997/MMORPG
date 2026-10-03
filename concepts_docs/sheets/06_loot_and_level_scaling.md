# Loot tables and logarithmic level scaling

**Fixed:** player and monster levels combine to make far-separated levels yield almost no loot. **Proposed:** the exact symmetric logarithmic function below. Current resource probabilities are retained as equal-level base values.

## Per-item base chance

Every item has its own independent roll. Rates do not need to sum to 100%, and several different items can drop from one kill. Roll stack quantity uniformly over the listed minimum/maximum only after that item's roll succeeds. The [151-row drop table](../tables/mob_drops.csv) lists all ordinary item entries for the 37 unique current mobs.

Example at matching levels: Meadow Wolf can independently drop Meadow Wolf trophy at **22.5%**, Field Tonic at **4%**, its rare relic blade at **0.2%**, and its rare relic coat at **0.2%**. Those are current resource values, not generated illustrative numbers. Quantity and rates for every other enemy appear in the bestiary.

## Exact proposed formula

Let `P` be player level and `M` be mob level, both at least 1.

```text
gap       = abs(P - M)
tolerance = max(10, (P + M) / 2)
factor    = max(0, 1 - ln(1 + gap) / ln(1 + tolerance)) ^ 2
effective_chance = base_chance * factor
```

The combined mean level sets the tolerance; absolute level difference sets the penalty. The logarithm makes the first few level gaps matter, while the square drives the distant tail toward zero. Equal levels always give factor 1. Interchanging player and monster levels gives the same result. At or beyond the tolerance, factor is zero. This deliberately makes very large gaps produce no ordinary loot rather than rounding a tiny probability upward.

| Player / monster | Gap | Multiplier, approximately | 22.5% trophy becomes |
| --- | ---: | ---: | ---: |
| 5 / 5 | 0 | 1.000 | 22.50% |
| 5 / 4 | 1 | .505 | 11.37% |
| 10 / 8 | 2 | .294 | 6.61% |
| 20 / 18 | 2 | .401 | 9.02% |
| 20 / 15 | 5 | .149 | 3.35% |
| 20 / 10 | 10 | .018 | .411% |
| 25 / 5 | 20 | 0 | 0% |
| 5 / 25 | 20 | 0 | 0% |

The authoritative computed examples are [drop_scaling_examples.csv](../tables/drop_scaling_examples.csv). Keep full precision until the final roll. Round displayed percentages for readability without changing the probability.

## What scales

Scale ordinary mob item rolls, Fracture core rewards, repeatable direct camp-leader item rewards, and gold by this factor. A future 100%-base repeatable reward is still scaled; bypassing the drop-table code must not bypass the level rule. Gold uses the base uniform integer roll followed by multiplication; stochastic rounding preserves fractional expectation without imposing a one-gold floor.

One-time quest rewards, bought items and player trades are not random monster drops and are exempt. Defender kills use each defender's own level; the Fracture's core uses the Fracture's level. Ordinary kills must not roll the same core reward. Mastery Leaves use the Fracture factor, preventing level-50 players from farming level-7 spawn points at full efficiency.

XP is a separately listed reward. This loot function does not silently change the current EXP numbers. A later XP penalty or party XP rule needs its own tuning sheet and migration. No luck stat, paid drop boost or hidden pity is assumed here.

## Ownership and route implications

Offline play attributes a kill to the player. Future online play uses a fixed participation list captured by the encounter, personal rolls, and each recipient's level factor. Avoid last-hit ownership and proximity-only rewards. A high-level carry does not make a far-underlevel player eligible for full rewards against an oversized monster.

Expect similarly leveled hunting routes to outperform old low-level fields for item farming. For high-tier recipes, supply the required low-tier materials through current-band Fractures, a documented conversion recipe or trading. Do not force characters to obtain effectively zero-chance drops from obsolete mobs.

## Implementation difference

The current `DropTable.roll(rng)` only rolls its entry probabilities; it has no player/mob level arguments. The proposed scaling needs explicit encounter context and consistent treatment of gold and direct reward paths.
