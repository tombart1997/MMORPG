# Painted bronze UI

The UI uses a 1280×720 reference canvas with Godot's existing `canvas_items` stretch mode. It scales proportionally at 1080p and 1440p. Gameplay services retain authority over all commands.

`game/scripts/ui/theme/painted_theme.gd` owns the shared theme, nine-patch window frames, small recessed controls, section rules and aligned value fields. `PaintedArt` handles noninteractive portrait/flame layers. `WindowChrome.install()` supplies the serif title strip, close, collapse and constrained dragging. New windows should use these components rather than define independent colors and borders.

The full frame uses original painted cloud hooks and dragon claws. Corners remain fixed while edges and the grainy center tile to fit. Small controls use narrow strips from the same atlas so corner ornament does not overwhelm a 44px slot. Surface grain and scratches are baked into the artwork; there is no animated noise or particle fire. Portrait and ornament shaders provide the circular mask and black-background key. The minimap reuses the ring with its fire colors muted to bronze. A separate item atlas replaces the common placeholder icons at presentation time; bespoke weapon artwork retains its identity.

The HUD, inventory, shop/dialogue, forge, quest journal, map, login and combat sandbox share the theme. The action bar uses six painted ability tiles, real cooldown labels and illustrated active-state flames. System/Combat tabs filter a bounded local event history; they do not imply network chat. HP and XP use real values. The prototype has no mana or attribute-allocation system, so no fictional values or nonfunctional allocation buttons are added. The portrait is a shared illustration, not a generated likeness of each saved character.

Existing single-modal session behavior is retained. Window dragging and collapsing are visual operations; opening inventory, dialogue or a map still blocks world commands as before. Item commands, stack splitting, equipment drops, consumable assignment, purchases and forge confirmation continue through their existing handlers.

Assets and the exact generation prompts are documented in [PAINTED_UI_PROMPTS.md](PAINTED_UI_PROMPTS.md). All runtime assets are inside `game/assets/ui`; no files are loaded from a user's Codex directory.

Validation:

```powershell
godot --headless --path game --editor --import --quit
godot --path game --fixed-fps 60 --script res://tests/painted_ui.gd
godot --headless --path game --fixed-fps 60 --script res://tests/mmorpg_loop.gd
godot --headless --path game --fixed-fps 60 --script res://tests/skill_combat.gd
```

The rendered UI test writes HUD/inventory screenshots at 720p, 1080p and 1440p plus utility-window previews under `game/.local/`. It checks canvas bounds, title dragging and live HP. Run with a display for screenshots; headless mode checks behavior without captures.
