# Fractures — spawn points and mastery farming

![Fracture states and reward objects](../art/fractures_mastery.png)

A Fracture is a destructible source of enemy reinforcements. The player attacks its core while managing the defenders it releases. Destroying the core rewards materials and the proposed Mastery Leaf; surviving defenders remain alive and dangerous.

## Current Briarwake encounter

The current resource uses **1,800 HP**, 180-second respawn, a population cap of 24 and four health-triggered waves. It releases **6 Young Mosslings at first damage**, **6 at 80% HP**, **8 Grown Mosslings at 55%**, and **4 Ironbacks at 30%**. Wave warning is **0.65 seconds**. These resource values supersede older text that described a 950-HP core and smaller waves.

Warnings select navigable, separated ground near the encounter and visibly mark the release positions. Blocked locations retry; duplicate damage events cannot release the same wave twice. Strong damage can destroy the core without a forced invulnerability gate. Cancel queued releases on destruction but do not remove already spawned defenders.

## Proposed spawn-point progression

| Fracture | Level | Gear band | HP | Base EXP | Mastery Leaf base chance / quantity | Respawn |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| Briarwake | 7 | T2 | 1,800 | 100 | 40% / 1 | 180s |
| Cairnwake | 15 | T3 | 6,000 | 300 | 50% / 1 | 240s |
| Ashwake | 24 | T4 | 14,000 | 700 | 60% / 1–2 | 300s |
| Crownwake | 40 | T5 | 36,000 | 1,800 | 65% / 1–2 | 360s |

Only Briarwake currently has a Fracture resource. Its proposed level is 7; an explicit level field needs implementation for loot scaling. Cairnwake, Ashwake and Crownwake are new targets. Their exact gold/material chances are in [fractures.csv](../tables/fractures.csv).

Leaf rates are equal-level base probabilities. At equal level, Briarwake gives an expected **0.4 Leaves per clear**, so 55 Leaves for one complete G skill average **137.5 core destructions**. Ashwake averages .6 × 1.5 = .9 Leaves, or approximately 61.1 clears. These expectations ignore travel, competition, failed fights and level-gap penalties. Tune against actual route time rather than counting only the respawn timer.

## Core rewards

Current Briarwake has independent base rolls for Wakeglass Ember **18%**, Wakecleaver **0.3%**, Rootward Jack **0.4%**, Moss Shard **80%** with quantity 1–2, and Field Tonic **25%**. Add the proposed Mastery Leaf **40%** and Tempered Ore **35%** as independent core rolls. Proposed higher-band cores retain Moss Shards so all nine-step recipes remain farmable near the player's level.

Wakeglass becomes an ordinary required ingredient for +7–+9. It does not guarantee smithing success. Mastery Leaves are a separate material and cannot substitute for Wakeglass. Ordinary wave enemies keep their own regular drop tables, but never drop the core's Mastery Leaves merely because they spawned from a Fracture.

## Visual and sound states

Dormant: seven closed splintered ribs, suspended amber heart, dim scar. Active: a clearer amber core and short impact chips. Each wave uses low ground warning rings and a root-crack cue. Damaged: ribs spread, core becomes visible without flooding the screen. Destroyed: ribs fall outward, a brief restrained ring releases, items remain readable on the ground.

Cairnwake uses slate ribs, Ashwake black glass and ember seams, Crownwake weathered stone/root forms with a cold violet heart. Shape and silhouette identify the tier before colour is visible. The illustrated plate is a design reference; exact rib count and spawn markers remain production constraints.

## Route, reset and online rules

Place Fractures off the main road with two approach angles and an open fighting floor. Nearby regular packs make a useful circuit during respawn. Abandonment resets the core and thresholds without granting rewards or turning remaining defenders into an infinite spawn loop. Record destruction once before rolling rewards. Future groups receive personal eligible rewards; the same core cannot be destroyed separately for every participant.
