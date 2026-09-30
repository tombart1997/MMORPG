# Briarwood expansion

The playable terrain grew from 110 × 130 to 240 × 362 metres (6.1 times the area). Eleven village buildings, four market stalls and nine NPCs connect through broad lanes. The original four services remain; Darin sells weapons, Hessa armor, Sera potions, Bram mount bridles and Ilyra crafts relic equipment. All 33 hunting camps connect to the village navigation mesh. The map includes the new roads and six discoverable hunting districts.

Thirty new monster definitions join the three original mossling varieties. Every level from 1 to 25 is represented. Wolves, boars, spiders, bandits, wisps and stonekin use shared prototype silhouettes with distinct palettes, sizes and stats; these are not thirty bespoke production meshes. The machine-readable [catalogue](game/data/first_map_catalogue.json) lists every new monster's stats, location, population, XP, gold and loot chances.

Tier 1 spawns three monsters, tier 2 four (the original ironback camp retains five). They alert as a group when attacked. Tiers 3–5 spawn alone, acquire visible players within 10–13 metres and run at 4.6–5.2 m/s. They respect sanctuary, terrain and a 20-metre encounter leash. Higher tiers increase HP, damage, defense and size. Ordinary expansion camps respawn after 45 seconds; elites after 210–270 seconds, once the player leaves. The original mossling route remains the introductory hunt.

Each species drops gold and can drop potions, weapon, armor and its own crafting material. New rare equipment has a **0.2–0.4% chance per item per kill**, with independent rolls. Species materials have a 45% drop chance; potions 8%. Original mosslings also retain quest moss shards. The old guaranteed camp-leader weapon was removed, and fracture equipment now drops at 0.3–0.4%. Ilyra's recipes require 25–45 species materials plus gold, giving a deterministic equipment path alongside rare drops. Shops provide ordinary equipment in five level bands.

XP per level is `600 + 180*(level-1) + 35*(level-1)^2`: level 1 requires 600 XP and level 25 requires 25,080. This supersedes earlier fast first-hour pacing notes. Existing saves are retained and validated against the new curve.

The top-center horizontal target bar shows name, level, tier and numerical HP. It follows selection or recent combat. Mounted Space attacks multiply attack speed by 1.35. Two consecutive successful swings against the same living target within 1.5 seconds apply physical knockback beyond melee reach in open ground; walls can obstruct it. A miss or expired chain resets the sequence. Taking damage preserves riding, but death, conversation and skills dismount. Summoning still requires ownership and being out of combat.

Validation: `./tools/run.ps1 -Test`; rendered expansion check: `./tools/run.ps1 -Test -Suite first_map_expansion -Windowed`. The expansion suite checks every camp's navigation, levels, tiers, loot rates, crafting transactions, elite pursuit, sanctuary, actual Space input, mounted knockback and HUD. Screenshots go to `game/.local/expansion_combat.png` and `expansion_village.png`. Tests disable normal save persistence.

To regenerate authored expansion resources, run `python tools/author_first_map.py`, then `python tools/finish_expansion_data.py`. The latter preserves the original quest material IDs while updating original encounter loot.
