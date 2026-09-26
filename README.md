# Ironfield - Briarwood March

A Godot 4.7.2 classic PC MMORPG prototype with a persistent cursor, navigable outdoor zone, quests, selective loot, equipment, Smith upgrades and local saves.

Run `./tools/run.ps1`, or open `game/project.godot` and press F5.

Play as **Ironvow / Turnwarden**: open foes with Riving Stroke, exploit them with basic attacks, guard a frontal hit to earn an Answer, then spend it on a sweeping push or a healing counter. Heelturn and Standard add movement and area control.

- **Left click:** travel, interact, select/approach enemies or pick up chosen loot.
- **Right drag / wheel:** orbit / zoom. **WASD:** move. **Space:** basic sword combo.
- **1-6 or skill buttons:** six active skills. Skills 3 and 5 then need a ground click; Escape cancels placement.
- **I:** inventory/equipment; drag items, Shift-drag half a stack. **J:** quests.
- **E:** nearest interaction. **Q:** tonic. **R:** revive when dead.
- **F5 / F9:** save / load. Autosave and save-on-close remain enabled. **F3:** debug. **F6:** reference specialization selection at the refuge.

Visit Warden Elric for the introductory quests, Mara for trade and Smith Oren for upgrades. New and migrated characters receive the complete reference specialization; other classes are design-only.

`./tools/run.ps1 -Test` runs all nine gameplay suites. Add `-Suite skill_combat -Windowed` to watch the specialization checks. See [PROJECT.md](PROJECT.md) for implementation and extension instructions, and [CLASS_DESIGN.md](CLASS_DESIGN.md) for the full original four-class, eight-specialization roster and all 48 skill concepts.

The **Amber Scar** art benchmark surrounds the existing Briarwake Fracture. Follow the branch east from Old Pine Hollow. `./tools/run.ps1 -Test -Windowed -Suite art_benchmark` captures its approach, real gameplay camera, damage, collapse and reward presentation. `./tools/build_art.ps1` rebuilds the original art; `./tools/build_assets.ps1 -Asset briarling` re-exports the editable creature source. Read [ART_DIRECTION.md](ART_DIRECTION.md) for the visual contract, asset budgets, review and measurements.
