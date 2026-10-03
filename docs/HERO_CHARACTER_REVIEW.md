# Hero character and sword combat review

The player now uses a broad, heroic male silhouette with a stronger jaw, shorter fitted neck, shaped shoulder plates, a tapered forged breastplate, muscular upper sleeves, articulated knee shields and sabatons. Oxblood front and rear tassets, restrained gold trim and a fitted rear harness make the back readable from the gameplay camera. The editable source remains `blender/characters/warden_high.blend`; the single skinned runtime asset remains `game/assets/characters/warden_high.glb`.

Regular swords use a staggered one-handed guard with the free hand protecting the chest. Weapons at least 1.25 m long use separate two-handed idle, running and three-cut clips. A weapon scene may explicitly set `metadata/two_handed` to override the length classification. Wakecleaver/Cairnwarden has an extended handle and offhand marker. Ember Fang, Glass Sabre and Rift Cleaver now have continuous bevelled blades and long grips, with meshes grouped by material rather than stacked box parts.

The presentation adapter selects those clips; ItemData, equipment sockets, AttackData, damage, attack speed, hit cones, combo buffering, movement locks, authored lunges, skills and mounted attacks retain their existing contracts. The hero profile preserves its authored materials instead of replacing them with the townfolk atlas, and refits the equipped insignia to the deeper breastplate. Damage captions remain numeric hit feedback, with a smaller footprint and shorter rise so they leave the blade visible.

## Rendered iteration

1. Captured the original character and each attack in Godot. The neck was disproportionately long, the torso narrow, the shoulder plates looked like stacked pillows, and the material atlas gave the breastplate distracting surface noise. The original overhead correction failed the existing check: its blade tip was still above the head at the onset of damage.
2. Rendered the first broader body from the front, three-quarter, rear and portrait angles in Blender, then tested it in the outdoor Godot world. Changed the shoulders to plate shells and rebuilt all three attacks. All blade-contact checks passed. The rear render exposed a jagged lower neck cutoff and an underdeveloped back silhouette.
3. Fitted the neck into the collar, cleaned the swept hairline, added rear tassets and a harness, and shaped the knee and boot armor. Gameplay review exposed that the offhand could lose the grip on wide long-sword cuts. The shared handle path now stays within the reach of both arm chains before baking.
4. Recorded the actual outdoor game with Godot Movie Maker at 60 fps, including a normal 8 m camera, orbit views and an active enemy. Render-by-render measurements exposed overly sharp windup acceleration. Time-aware Hermite tangents and an earlier, more evenly distributed preparation reduced the maximum consecutive blade-tip displacement from 0.814 to 0.478 m for the regular sword, and from 1.027 to 0.635 m for the 1.6 m sword. These are measurements at 60 Hz under the existing attack timings, not frame-rate benchmarks. The largest guard discontinuity between cuts is now 1.7 cm; maximum offhand separation is 1.4 cm in the final clips. Oversized damage captions were also reduced after the recording showed them covering the swing.

The final silhouette, rear equipment, visible preparation, continuous recovery and two-handed contact are substantially stronger than the starting prototype. The character remains a stylized game asset; close-up hair and gloves are still simplified. The model is 280,448 full-detail triangles in one skin with 18 bones and 16 clips; this is a hero asset, not a crowd-character budget. Existing Godot LOD and shadow-mesh imports remain enabled.

## Evidence and checks

Local review artifacts are intentionally ignored by Git:

- `blender/renders/hero/hero_pass1_*.png`: first body pass.
- `blender/renders/hero/hero_pass2_*.png`: final source render angles.
- `game/.local/warden_idle.png`, `warden_portrait.png` and `warden_*.png`: final equipped Godot studio views and sampled cuts.
- `game/.local/hero_review/hero_combat_final.mp4`: real-speed recording of the final character fighting an active enemy in the actual outdoor game. Target and player HP are increased only by the review harness to keep the encounter available through all weapon changes.
- `game/.local/hero_review/final_motion_sheet.png`: consecutive frames from that recording.
- `game/.local/hero_review/final_contract/*_motion.csv`: every sampled render pose, combat phase, clock and blade position used for the final continuity checks.

All 16 pre-existing integration suites passed. After the final motion changes, the character pipeline, all three equipped blade-contact checks, the new weapon-length/continuity/grip suite and the rendered active-enemy review passed. Actual movement input verifies the distinct long-sword running clip, and a slightly extended Briarsteel blade still selects the regular guard. The new suite is included in `tools/run.ps1 -Test`.

```powershell
./tools/run.ps1 -Test -Suite hero_combat_review
./tools/run.ps1 -Test -Suite hero_combat_review -Windowed

# Record each engine frame; encode the resulting AVI with ffmpeg if desired.
Godot_console --path game --script res://tests/hero_combat_review.gd --fixed-fps 60 --write-movie .local/hero_review/review.avi -- --label review --live

# Rebuild from the original high-character generators and bundled anatomical reference.
blender --background --factory-startup --python blender/scripts/build_warden_hero.py -- --second
```

The source generator preserves the rig and original non-basic clips, exports the consolidated skin and updates the existing character manifest. An unmodified high-Warden `.blend` can also be supplied to the generator for quicker authoring. Do not pass an already refined hero back through the proportion pass.
