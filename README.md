# Ironfield - Briarwood March

A Godot 4.7.2 classic PC MMORPG prototype with a persistent cursor, navigable outdoor zone, quests, selective loot, equipment, Smith upgrades and local saves.

Run `./tools/run.ps1`, or open `game/project.godot` and press F5.

The first map now covers 240 × 362 metres, with a larger village, nine NPCs and 33 monster types spanning levels 1–25 and tiers 1–5. Tiers 1–2 travel in groups; tiers 3–5 are aggressive solo encounters. Specialist shops sell weapons, armor, potions and mounts, and craft equipment from species-specific materials. See [MAP_EXPANSION.md](MAP_EXPANSION.md) for balance and loot details.

**H** mounts an unlocked horse. **Space** attacks while riding at 35% faster speed; two consecutive hits knock the target out of melee range. A bridle requires level 3 and 240 gold. **M** opens the expanded map.

Play as **Ironvow / Turnwarden** with six mobile, single-press skills: **1 Thunder Cleave** (lightning arc), **2 Spirit Edge** (green blade, +45% basic damage and +30% attack speed for 6s), **3 Flashstep** (5m dash and +80% movement speed for 4s), **4 Bladestorm** (orbiting sword, repeated area hits), **5 Phoenix Ring** (damaging fire field and shelter), and **6 Sunbreaker** (heavy radiant cleave, knockback and healing). Skills take over basic attacks immediately and buffer one follow-up. WASD and click travel continue during casts; selected targets stay selected while strafing.

- **Left click:** travel, interact, select/approach enemies or pick up chosen loot.
- **Right drag / wheel:** orbit / zoom. **WASD:** move. **Space:** toggle continuous sword combos; press again or Esc to stop. Movement and menus stop autoattacking.
- **1-6 or skill buttons:** six active skills, cast on one press while moving. Flashstep follows movement direction; Phoenix Ring erupts at your feet.
- **I:** inventory/equipment; drag items, Shift-drag half a stack. **J:** quests.
- **E:** nearest interaction. **Q:** tonic. **R:** revive when dead.
- **F5 / F9:** save / load. Autosave and save-on-close remain enabled. **F3:** debug. **F6:** reference specialization selection at the refuge.

Visit Warden Elric for the introductory quests, Mara for trade and Smith Oren for upgrades. New and migrated characters receive the complete reference specialization; the character creator offers all four class identities with separate local saves and a rotatable preview. The other three identities currently share Turnwarden combat; their unique skill kits remain design-only.

`./tools/run.ps1 -Test` runs twelve gameplay suites. Add `-Suite first_map_expansion -Windowed` to watch the expansion checks, or `-Suite skill_combat -Windowed` for specialization checks. See [PROJECT.md](PROJECT.md) for implementation and extension instructions, and [CLASS_DESIGN.md](CLASS_DESIGN.md) for the full original four-class, eight-specialization roster and all 48 skill concepts.

The **Amber Scar** art benchmark surrounds the existing Briarwake Fracture. Follow the branch east from Old Pine Hollow. `./tools/run.ps1 -Test -Windowed -Suite art_benchmark` captures its approach, real gameplay camera, damage, collapse and reward presentation. `./tools/build_art.ps1` rebuilds the original art; `./tools/build_assets.ps1 -Asset briarling` re-exports the editable creature source. Read [ART_DIRECTION.md](ART_DIRECTION.md) for the visual contract, asset budgets, review and measurements.

Recent combat and world updates: the third strike is an overhead cleave (0.70s versus 0.64s for the opening cut). Mounted attacks alternate two close left/right cuts along a figure-eight path with rider lean. Wilderness tier 1/2 packs contain 6/8 monsters; introductory mossling camps retain their onboarding balance. Packs select individual members to wander briefly within their home area every 3-6 seconds. The full map stays centered and separates town service labels from landmarks.

`./tools/run.ps1 -Test -Suite combat_creation_review -Windowed` checks creation, saves, automatic combos, mount alternation, pack density and map bounds, and captures visual review images in `game/.local/review_*.png`.
