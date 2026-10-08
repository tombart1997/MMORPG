# Ironfield — concept and design book

Open [index.html](index.html) to browse the complete illustrated book offline, or [Ironfield_Concepts.xlsx](Ironfield_Concepts.xlsx) for separate topic and balance tabs.

The concepts have also been reconstructed through the local 2D-to-3D generator and imported into the game. Open the [Godot model gallery](../docs/forge_rebuild/gallery.html) or [rebuild report](../docs/forge_rebuild/README.md) to inspect the resulting models and their remaining visual limitations.

Created 3 October 2026. This folder contains **17 topic sheets**, **12 original generated concept plates**, **37 illustrated mob entries**, **151 individual mob item-drop rows**, **45 smithing steps** across five gear tiers, **34 equipment entries**, and the **48 class skill designs**.

## Your fixed rules

- Every equipment item can reach +9; failed upgrades destroy the item and consume the attempt costs. Higher gear tiers have lower success rates.
- Weapons and armor gradually become shinier. +7 uses blue sparks, +8 red sparks, +9 violet sparks; tier affects intensity.
- Mob loot has individual item probabilities, reduced logarithmically by the combined player/mob level gap, in both directions.
- Each quarter of a level grants one VIT/STR/DEX/AGI point, giving four per completed level. Each level grants one skill point.
- Skill rank 17 becomes M. Fracture loot advances M1–M10 at costs of 1–10 items; M10 completes G, the maximum. M and G are two mastery tiers.

Exact odds, prices, ingredient quantities, stat effects, level cap and formula coefficients are **proposed tuning**. Current creature/loot facts are copied from runtime resources and marked separately. These documents do not implement the new gameplay rules.

## Topic sheets

| Sheet | Contents |
| --- | --- |
| [00 · Vision](sheets/00_game_vision.md) | Core loop, pillars, scope, fixed rules |
| [01 · Smithing](sheets/01_smithing_upgrades.md) | Success/failure rates, exact ingredients, gold, destruction and accumulated risk |
| [02 · Equipment](sheets/02_equipment_and_visuals.md) | Tiers, stats, material shine and sparks |
| [03 · Levels and stats](sheets/03_levels_and_stats.md) | XP curve, quarter milestones, four attributes and point budgets |
| [04 · Skill mastery](sheets/04_skills_and_mastery.md) | Rank 17, M1–M10, 55 Leaves per G skill, reset/persistence rules |
| [05 · Bestiary](sheets/05_mob_bestiary.md) | All mobs, appearance, level, tier, EXP, stats and every item roll |
| [06 · Loot scaling](sheets/06_loot_and_level_scaling.md) | Exact logarithmic formula, examples and reward scope |
| [07 · Fractures](sheets/07_fractures_and_spawn_points.md) | Waves, spawn-point destruction, mastery/material farming |
| [08 · World](sheets/08_world_and_regions.md) | Current regions, future regions, level bands and routes |
| [09 · Classes and combat](sheets/09_classes_and_combat.md) | Four classes, eight specializations, skill identities and encounter decisions |
| [10 · Quests and town](sheets/10_quests_and_town.md) | NPC services, current quests, proposed opening-session pacing |
| [11 · Economy and crafting](sheets/11_economy_and_crafting.md) | Trophy sources, conversions, crafting, shops and gold sinks |
| [12 · Mounts](sheets/12_mounts_and_travel.md) | Horse/rider proportions, tack, travel and model acceptance |
| [13 · UI](sheets/13_ui_and_feedback.md) | Allocation, mastery, smith risk, loot readability and accessibility |
| [14 · Art/audio](sheets/14_art_audio_and_production.md) | Style, materials, sound, rendering reviews and provenance |
| [15 · Endgame/online](sheets/15_endgame_and_online.md) | Boss routes and future party, trade, guild, PvP and persistence rules |

The [interactive bestiary](bestiary.html) has one mapped portrait per creature, family/search filters and a player-level input that calculates effective item probabilities. [art_gallery.html](art_gallery.html) shows the full-resolution plates. The [prompt set](art/prompts.json) preserves every final generation prompt; the [art review](art/ART_REVIEW.md) records visual inspection. Built-in image generation was used for all concept PNGs.

## Balance files and workbook

`tables/` contains UTF-8 CSVs, `design_rules.json` and a resource snapshot. Every CSV is available as a workbook tab. The workbook also includes the full topic sheets with embedded concept art. Its Smithing Table and Drop Calculator use formulas so editing probabilities or player/mob levels recalculates related risk/rates in Excel. Formula values recalculate when opened; the CSVs contain already computed values.

Workbook edits are standalone explorations and do not automatically change CSVs, Markdown or gameplay. To persist a chosen tuning change, update the source constants in `tools/build_balance.py`, review the corresponding prose and regenerate. Edit the authored Markdown sheets directly for prose changes.

## Rebuilding

Build dependencies are Python 3.12+, `openpyxl`, `Pillow` and `Markdown`. Browser verification additionally uses Playwright with the installed Chrome executable; no downloaded browser is required on this machine. Dependency names are listed in [requirements.txt](tools/requirements.txt).

From the project root:

```powershell
py concepts_docs/tools/build_balance.py
py concepts_docs/tools/build_bestiary.py
py concepts_docs/tools/build_presentations.py
py concepts_docs/tools/validate_concepts.py
```

`build_bestiary.py` regenerates only the bestiary Markdown from the snapshot. `build_presentations.py` rebuilds HTML and the workbook without changing authored topic prose. Refresh `project_snapshot.json` deliberately with `py concepts_docs/tools/snapshot_project.py` if runtime resources change; then review design differences before rebuilding. Rebuild scripts never write game resources.

For browser-only layout changes, use `py concepts_docs/tools/build_presentations.py --html-only`. Close the workbook in Excel before a full workbook rebuild; output replacement is atomic and preserves the previous valid file if writing fails.

Images are retained as original PNGs. All relative browser links require keeping this folder together. References to the current class design, art benchmark and previous horse review point into the surrounding project.

The added [quality and performance sheet](sheets/16_quality_performance.md) records the measured game budget, bounded repair process and the current complete replacement catalogue.

## Practical 3D reference views

Open [the production reference gallery](art/asset_turnarounds_v2/index.html) for 30 inspected sheets and their separate front, side, back, overhead and three-quarter inputs. The [multi-image generator report](../docs/full_asset_rebuild/README.md) records actual reconstruction, optimization and Godot results.
