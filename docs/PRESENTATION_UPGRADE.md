# Horse, swords, loot, character and audio

The primitive horse, floating loot crystals and silent conversations were the main issues in this pass. The new assets are connected to existing item, mount, combat, dialogue and save systems. The established UI layout remains intact.

Open the [visual and audio review](screenshots/presentation-upgrade/review.html) for rendered close-ups, both mounted cuts, a recorded walkthrough and playable audio. These captures come from the production outdoor scene in Godot 4.7.2 Compatibility at 1280 × 720 on a GTX 1080.

## Assets and integration

- The original bay horse has continuous skin, shaped shoulders/haunches, articulated legs, hooves, muzzle, fitted tack and mane/tail strands. Its 23-bone rig supplies idle, walk, trot and canter cycles. Cadence follows ground speed, transitions blend, and hoof sounds follow animated contact events.
- Mounted cuts twist the pelvis, spine and chest, with a counter-rotating head and a closed sword path. IK keeps both boots in the moving stirrups and the left hand on the reins. The existing movement, collision, attack speed, two-hit knockback, ownership and dismount rules remain authoritative.
- Ten original forged blades have sharpened edges, recessed fullers, varied guards, leather bindings, fitted pommels and restrained inlays. They replace visual references for 18 existing sword items without changing item IDs or statistics. Regular and two-handed grips use the existing skeleton sockets.
- Dropped weapons instantiate the same scene as the equipped item and rest against the actual terrain. Currency uses instanced minted gold cash coins with thickness, square holes, raised rims and relief. Selection, labels, rarity beams, lifetime and collection rules remain in place.
- The preserved hero has warmer, lighter skin, clean-shaven cheek planes, a softened nose bridge, narrower eye sockets, dark brown eyes, fitted brows and black tied hair. Facial colors remain consistent across class wardrobe tints. Equipment and animation contracts are preserved.

## Audio

The shipped assets include two original region music loops, two ambience loops, six skill cues, varied recorded foley and 24 synthetic voice clips covering all ten NPCs. Conversations speak the displayed page; responses replace the current line. Shop NPCs greet the player, closing/switching panels stops speech, and dialogue lowers the music. Region travel crossfades music and ambience over two seconds. Sword swings, damage, walking, hooves, mount, equipment, coins and pickups use game events.

All runtime playback is offline. **F8** toggles sound and saves the preference. The mixer has separate Music, Ambience, Effects and Voice buses, a pool of 16 spatial effect players, and a 32 m distance limit.

Foley comes from [Kenney RPG Audio](https://kenney.nl/assets/rpg-audio) and [Impact Sounds](https://kenney.nl/assets/impact-sounds), which are CC0. Music, ambience and skill pulses are original procedural compositions. NPC lines were rendered during authoring using [edge-tts](https://github.com/rany2/edge-tts); these are synthetic voices. Credits and source licenses are in `game/assets/audio/CREDITS.txt`.

## Rendered review loop

Four substantial rendered passes preceded the final review capture:

1. Checked all new assets and real mounted attacks. Caught an unsupported Blender material mix exporting the horse white, insufficient facial definition, and uneven coin face shading.
2. Corrected the coat export, fitted facial details, flattened minted faces, and checked all ten blades together. The review exposed inappropriate color attributes affecting armor and overly prominent facial overlays.
3. Restricted facial vertex coloration to the skin material, kept neutral colors on tack, and replaced floating facial outlines with changes to the continuous head. Rechecked stirrup/rein contacts and dialogue transitions.
4. Refined skin tone and brow thickness, retained wardrobe colors, and checked clean close-ups alongside ordinary gameplay views. Recorded the actual renderer and audio output.

The mounted review measured **22° pelvis rotation**, **91° chest rotation**, **0.9 mm maximum stirrup error** and **4.9 mm maximum rein-hand error**. Two real attacks landed and produced swing, impact and hoof cues. The captured runtime mix peaked around **0.77**, below clipping. The review also exercises normal NPC panel opening, page changes, cancellation and music crossfades.

The full regression run passed **all 21 suites and 1,839 checks**, including routes, mounted knockback, inventory/save persistence, real combat, all six skills and the previous full-body motion checks. [Recorded suite results](screenshots/presentation-upgrade/regression_results.json) accompany the preview. The windowed presentation review separately passed playback and mix checks with no script or resource errors.

## Budgets and reproduction

| Asset/system | Budget |
| --- | --- |
| Horse | 40,376 triangles, one skin, 23 bones |
| Swords | 4,740–7,512 triangles per design, shared surfaces |
| Coin | 4,560 triangles, 3–14 MultiMesh instances per pile |
| Ground loot | Weapon culling at 36 m; coin piles at 28 m |
| Audio | About 4 MB including import descriptors and credits |

Editable sources are under `blender/mounts`, `blender/weapons` and `blender/characters`. Rebuild from the repository root:

```powershell
blender -b --factory-startup --python-exit-code 1 -P blender/scripts/build_trail_horse.py
blender -b --factory-startup --python-exit-code 1 -P blender/scripts/build_sword_suite.py
python tools/wire_sword_suite.py
blender -b blender/characters/warden_high.blend --python-exit-code 1 -P blender/scripts/update_hero_face.py
python tools/build_game_audio.py
game/.local/audio_env/Scripts/python tools/build_game_audio.py --voices
./tools/run.ps1 -Test -Suite presentation_upgrade -Windowed
./tools/run.ps1 -Test
```

Audio authoring requires NumPy/SciPy, ffmpeg and the Kenney source archives under `game/.local/audio_sources`; voice authoring additionally uses edge-tts. Rebuild tooling is optional for playing the shipped assets. Headless tests validate audio resources/events without running the audio decoder; the windowed review validates playback, ducking, crossfading and the recorded mix.
