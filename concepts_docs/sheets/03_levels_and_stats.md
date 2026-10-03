# Levels and VIT / STR / DEX / AGI

**Fixed:** one assignable stat point at each quarter of a level and one skill point per level. **Proposed:** a level cap of 50, starting values, stat formulas and caps.

## XP and quarter awards

Keep the current curve as the first balance baseline:

`XP needed at level L = 600 + 180 × (L − 1) + 35 × (L − 1)²`.

For level 1, the thresholds are **150, 300, 450 and 600 XP**. Each threshold grants one stat point. At 600 XP, grant the fourth stat point, advance to level 2, carry remaining XP forward and grant the level's skill point in one saved transaction. The new level's 0% threshold does not award another stat point.

| Moment | Stat points gained | Skill points gained |
| --- | ---: | ---: |
| New level-1 character | 0 | 1 starting point, proposed |
| Level progress reaches 25% | 1 | 0 |
| Progress reaches 50% | 1 | 0 |
| Progress reaches 75% | 1 | 0 |
| Progress reaches 100%; level advances | 1 | 1 |

At arrival at level L, stat points earned are `4 × (L − 1)` and skill points earned are `L`, including the proposed starting point. A level-10 character therefore has **36** earned stat points and **10** skill points; level 50 has **196** and **50**. Spent and unspent points must sum to those totals. XP stops advancing at the cap, with no repeatable max-level quarter rewards.

If a kill grants enough XP to cross several thresholds or levels, award all crossed milestones exactly once. Store level, current XP, milestone state, earned/unspent budgets and allocations. Death, saving, reconnecting or resetting stats must not create new awards. Use integer thresholds rounded upward; the [progression table](../tables/level_progression.csv) lists them through level 50.

## Separate roles for four stats

All four start at **10**. Effects below apply to allocated points above 10. Proposed individual cap is **100**. Equipment bonuses are a separate layer and do not spend the allocation budget.

| Stat | Role | Proposed contribution per allocated point |
| --- | --- | --- |
| VIT | Endurance | +15 maximum HP; +0.10 Defense |
| STR | Physical power | +1.20 physical Attack |
| DEX | Precision and ability technique | +0.35% skill potency; +0.08 percentage points critical chance |
| AGI | Mobility and cadence | +0.12% movement speed; +0.10% basic attack speed; +0.05 percentage points evasion |

Base critical chance 5%, cap 30%; evasion starts at 0%, cap 20%. Stat/gear movement bonuses cap at +25%, basic attack cadence bonuses at +40%; explicit temporary ability buffs remain separately bounded. Evasion, if implemented, only applies to direct monster basic attacks; it does not erase floor hazards or hide attack geometry. PvP must use a separately reviewed rule set.

DEX controls technique, while AGI controls speed. Keep these names distinct in the character screen. Spell classes use weapon/focus power plus skill potency; they should not require an extra undocumented INT stat.

Example: allocate +10 VIT and +5 STR. Relative to the base character, gain 150 HP, 1 Defense and 6 Attack. Moving those points into DEX exchanges that power for ability potency/precision; it must not apply both sets of bonuses.

## Level bonuses and resets

The prototype currently automatically grants +20 HP and +2 Attack per level. Proposed stat allocation replaces that automatic layer rather than silently adding it on top. Equipment and any explicitly listed class base values still apply. Increasing maximum HP preserves current absolute HP unless an explicit level-up heal is specified; it cannot resurrect a dead character.

Proposed reset: Keeper Sella offers a gold-funded full stat reset, returning spent allocation points while preserving earned totals. Cost `100 × level` gold, once per visit, outside combat. It does not reset level, XP, gear or mastery. Skill resets return only basic skill points; mastery-leaf investment stays attached to its learned skill. See [mastery](04_skills_and_mastery.md).
