# Briar Crossing character pass

The prototype cylinder-and-box residents now use a modular, skinned townfolk kit. Keeper Sella has indigo keeper robes, an ivory stole, jade seal, prayer beads, talisman and pinned hair bun. Smith Oren has a broader build, rolled linen sleeves, exposed forearms, worn leather apron, pockets, hammer, tongs and a short beard. Both have profession-specific idle clips. All nine village residents and the Cinderfall scout use the same foundation.

The terrain, building locations, navigation, progression, dialogue and ornate UI remain established. A roof winding defect found in the review was corrected. The bright sphere campfire became curved layered flame cutouts, grain, shader-driven movement, a small unshadowed flickering light and seven smoke particles.

## Reuse the kit

`blender/scripts/build_townfolk.py` builds `blender/characters/townfolk_kit.blend` and `game/assets/characters/townfolk_kit.glb`. It reuses the existing humanoid bone definition in `build_characters.py`: 18 bones, metre scale, Godot forward -Z, unchanged hand/foot/chest/head names. Existing NPC gameplay stays on `WorldNPC`; `TownfolkVisual` handles presentation.

The kit contains two body bases, two independently selectable heads, three hairstyles, tunic/robe/apron garments, and five profession accessory modules. Hands have palms, thumbs and fingers; limbs have weighted elbows and knees; the head has a continuous jaw/cheek/nose surface, fitted eyes and brows. Clothes, skin and metal have painted grain and vertex shading. Each module has one material slot. The runtime atlas is external and shared; the GLB does not embed another copy. The editable blend retains textured, individually editable source parts.

Create a `NPCAppearance` resource and assign it to `NPCData.appearance`. Choose `body`, `face`, `hair`, `clothing`, `accessories`, `skin_tint`, `cloth_override`, `stature` and `idle`. Optional `weapon` and `offhand` scenes use the existing animated equipment grip contract. `TownfolkVisual.equip_visual(slot, scene)` also supports replacement/removal at runtime. Existing NPC data receives role presets automatically.

Residents share imported mesh resources. Unselected modules are removed from instances. Sella uses 10,264 triangles across five modules; Oren uses 7,504 across five. The entire optional library has 21,106 triangles; that entire library is not rendered for each resident. Meshes cull at 65 m. Idle sampling runs at 20 Hz within 16 m and 5 Hz farther away; it stops past the visibility range. There is no per-frame material creation.

Rebuild with the installed Blender executable:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/build_townfolk.py
& 'C:/Program Files/Godot/Godot_console.exe' --headless --path game --editor --import --quit
```

The live Blender MCP connection was unavailable, so creation/export used the installed Blender executable. Visual approval used rendered gameplay screenshots in Godot, including full figures, faces, player comparison and fire.

## Names and player

Resident names use 19 px text at .005 world pixel size, with smaller 13 px professions. Professions fade before 9 m; ordinary names fade before 16 m; quest-marked names retain a 20 m range. Updates are throttled to .15 s, labels respect depth, and quest indicators preserve their existing text. The former .216 m name glyph height is now .095 m.

The player remains on `warden_high.glb` and its existing animations, skills, equipment and sockets. `HumanoidPaint` gives its armor shared painted scratch textures, rougher metal and restrained specular response. Class tinting remains compatible and repeatable. No attack durations, active markers, damage timing or movement behavior changed.

## Recovery and validation

Full-workspace recovery snapshots include the pre-existing uncommitted work and untracked assets, without changing the user's Git index:

- `refs/checkpoints/briarwood-remaster-start` (`e7ab323`): before environment/performance work.
- `refs/checkpoints/character-quality-start` (`061329a`): remastered environment before NPC work.

Passing checks cover combat timing, melee commitment, streaming health/deaths/statuses/respawn, imported player animations and grips, skills, inventory/equipment, village dialogue and trading, save/load, sanctuary death/respawn, mounted route traversal, dense-map traversal, expanded spawn/loot progression, mouse interaction, farming, Cinderfall travel and painted UI bounds. `townfolk_review.gd` checks modular skins, rig/idle compatibility, labels, idle deformation and optional weapon grips while producing art-review images.

Tests referencing the former fixed 33-camp population now check the current authored spawn definitions. Tests that retain a distant enemy pointer now reacquire the resident actor after returning. The existing compact target bar expectation was updated to its established width. The Mossling resource rename also had a broken drop-table reference; it now uses the existing `young.tres` drop table.

See [performance measurements and screenshots](BRIARWOOD_REMASTER.md) and [generated texture prompts](GENERATED_ART.md).
