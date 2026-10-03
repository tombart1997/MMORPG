# Endgame, bosses and future online play

**Proposed future scope.** The current project is offline; these systems require later implementation and balancing.

![Regional endgame direction](../art/world_cinderfall.png)

## Endgame at level 50

Continue improving chosen skills to G, assemble +9 equipment, complete harder farming circuits and craft distinct relics. Max level stops XP/stat rewards but does not remove item or mastery goals. +9 gear is aspirational; ordinary upgraded equipment must still support useful current-level farming.

Avoid endless increases to the equipment cap or a hidden mastery tier above G. New regions should add meaningful encounters, weapon identities and build choices while keeping +9/G rules legible. A future level-cap increase must grant exactly four new stat points and one skill point per new level rather than rescaling old earned budgets.

## Boss structure

| Boss tier | Encounter role | Reward direction |
| --- | --- | --- |
| T3 leaders, e.g. Moonfang / Slate Guardian | Short focused solo challenge | Distinct trophy and band relic rolls |
| T4 threats, e.g. Bloodfang / Silk Matron / Rift Sentinel | Prepared solo or small-party pressure | Rarer gear, stronger crafting supply |
| T5, e.g. Cairn Colossus / Ancient Warden | Regional climax, later group variants | High-tier construction material and unique relic forms |
| Future Crownless Warden | Level-50 route finale | Crown-band relic recipes and cosmetic achievement |

Current T values describe resource threat categories, not proof of online raid implementation. A group version must list separate HP, damage, mechanics, participation requirements and per-item rewards. Do not merely multiply solo boss HP until the encounter becomes a long stationary damage test.

Bosses need a recognisable windup, pressure that asks for movement, an opportunity to punish recovery, and a clearly bounded area. Terrain should not trap horses or ranged players behind invisible blockers. Resetting a boss grants no reward and cannot preserve partially rolled loot.

## Parties and personal loot

Proposed party size is four. Record meaningful participation through damage, healing and support events, with bounded anti-idle criteria. On completion, each eligible player receives personal item rolls using their own level gap. Another party member's level does not overwrite that factor. Shared encounter completion is recorded once; reward transactions are per eligible participant and idempotent.

Party XP sharing is undecided; the single-player EXP values in the current table are not a finished party formula. Define it separately before network implementation. Personal loot avoids last-hit competition while rare crafting ingredients can still support trade.

## Trade, guilds and PvP

Equipment and ordinary crafting ingredients can be traded through a confirmed two-sided offer. Show exact item, quantity, + level and gold. Lock changed offers until both players confirm again. Mastery skill records are character-bound; the first proposal keeps Mastery Leaves character-bound too, preserving the spawn-point progression loop.

Guilds can offer shared objectives, route events and cosmetic standards. No guild bonus should multiply smithing success into a guaranteed high-tier outcome. Guild storage needs explicit permissions and a transaction log before use.

PvP is opt-in in marked areas with safe town boundaries. Begin with normalized sparring and a separately reviewed damage/control rule set. Do not enable unrestricted item theft or destruction on ordinary player death; the agreed destruction mechanic belongs to deliberate smithing attempts.

## Persistence authority

A future server owns XP milestones, skill points, inventory, gold, upgrade rolls, mastery learning, encounter completion and reward ownership. Clients request an action and display the recorded result. Transaction identifiers prevent retries from repeating spending or granting rewards. The offline save format should preserve stable item/skill IDs to make later migration possible.

Implement in this order: fixed progression and smithing rules; reliable single-player persistence; complete encounter/reward context; explicit party rules; then authoritative networking and trade. Art and design approval cannot establish that online authority or economy security has been implemented.
