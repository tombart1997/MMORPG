# Chinese fantasy character and creature pass

The hero and hostile creature families now use an original martial-fantasy art direction: ink lacquer, jade green, cinnabar silk, aged gold, cloud scrolls, crossed collars and layered lamellar armor. The male hero retains his broad shoulders, athletic taper and strong jaw. A fitted scalp, tied knot, jade hairpin, split robe and matching sword fittings establish his martial silhouette from both the front and the normal rear gameplay camera.

Field monsters use imported, animated skins rather than the former box/sphere assembly. Wolves have lean bodies, flowing cheek manes, whiskers and tail plumes; boars have heavier bodies, curling tusks and flank scales. Silk spiders have jointed tapered legs, petal carapace trim and an eye cluster. Stone guardians have carved masks, articulated fingers and plated skirts. Wisps are floating lantern souls with metal ribs and silk streamers. Mosslings were rebuilt as masked forest spirits with branching antlers, bark ridges and root claws. Ironbacks add a fitted carved leaf mantle. Existing bandit scenes share the new humanoid wardrobe.

Enemy IDs, names, level/tier data, colliders, speeds, damage, attack phases, rewards, targeting, streaming and equipment sockets are unchanged. The hero keeps all 16 clips, including distinct regular-sword and two-handed long-sword idle/run guards and three cuts per style. The regular blade preserves its 1.08 m grip/tip contract; long equipment retains its existing scale and offhand markers. Imported creature poses sample the same .30 active / .55 recovery markers as combat. Elite crowns are separate skinned surfaces, hidden on ordinary tiers. Shared species profiles and cached variant materials retain resource sharing across packs.

## Visual iteration

1. Rendered the first wardrobe from front, three-quarter, rear and portrait angles. The scalp looked helmet-like, the collar read as crossing straps and the silk border weighting did not match its panel. Rebuilt the scalp from the anatomical head surface, reduced the knot, shortened the inner collar and matched border/embroidery weights to the cloth.
2. Rendered every creature from front and rear. Corrected the studio's post-export pose evaluation, refitted floating hound eyes, swept back the spine mane and widened the guardian torso. Replaced the plain initial forest creature with a completely authored bark/mask/antler model. Added subtle baked grain/normal detail for fur, bark, stone and chitin.
3. Reviewed the equipped hero's three cuts in Godot. Replaced the regular sword with a jian-inspired blade and the long guards with continuous curved quillons. All three blade-contact checks still pass.
4. Ran a rendered review in the actual outdoor world, using the real player controller, enemy brains, collisions and hit resolver. Reviewed close orbit views and the normal 8 m, -.55 pitch gameplay camera. Corrected creature attack pitch so bites and lantern strikes lean into the target, and the carved guardians sweep their hands forward. The initial review harness lost its player after an equipment refresh restored ordinary HP; moved the review-only durability override after refresh. All eight reviewed types now both receive and deal real attack damage.
5. Recorded every engine frame with Godot Movie Maker at 60 fps: 1,385 frames / 23.08 seconds for the eight-enemy review. Extracted consecutive combat frames to inspect preparation, visible swing, hit response and recovery. Matched the new creatures' Godot import sampling to the authored 60 Hz clips, then repeated the rig/combat checks and native recording. The companion 743-frame hero recording checks both weapon styles with a live opponent and the normal camera.

These are stylized game assets, with simplified hair, fur and cloth rather than cinematic realism. Cloth is skinned to the existing hip/thigh rig, not physically simulated. The full-detail hero is 336,984 triangles in one skin; field creature assets use roughly 9–25 thousand triangles and at most two skins. Godot's imported mesh LODs remain enabled. Terrain, architecture and UI retain their existing art direction; this pass covers the requested character and monsters.

All 18 integration suites pass, including character import/rig contracts, real combat, progression, inventory/equipment, mounted combat, both regions, encounter streaming, dense-map traversal, townfolk, hero weapon-length/continuity checks and the new creature review. The equipped blade reaches forward at damage onset in all three cuts. The live hero recording measures at most 1.4 cm of offhand separation on the long grips.

## Review artifacts and rebuilding

Local images and recordings remain outside Git:

- `blender/renders/hero/jade_pass1_*.png` and `jade_pass2_*.png`: wardrobe iterations.
- `blender/renders/jade/*_front.png`, `*_rear.png`: creature source views.
- `game/.local/warden_idle.png`, `warden_portrait.png`, `warden_*_contact.png`: equipped native Godot views.
- `game/.local/jade_review/final/`: live enemy front, side, gameplay and impact captures.
- `game/.local/jade_review/jade_combat.mp4`: eight live encounters at gameplay speed.
- `game/.local/jade_review/guardian_motion.png`, `boar_motion.png`: consecutive 50 ms frames extracted from that recording.
- `game/.local/jade_review/jade_sword_stances.mp4`: regular and long-sword guards, locomotion and combat.

```powershell
./tools/build_jade_art.ps1                 # Rebuild editable sources and GLBs.
./tools/run.ps1 -Test                     # Gameplay, rig, equipment and visual contracts.
./tools/run.ps1 -Test -Suite jade_visual_review -Windowed
Godot_console --path game --script res://tests/jade_visual_review.gd --fixed-fps 60 --write-movie .local/jade_review/review.avi -- --label review
```

The hero builder reads the current editable `warden_high.blend` and replaces only its named wardrobe components, preserving the authored rig and choreography. The creature and equipment builders are deterministic from an empty Blender scene. The earlier character generators remain historical sources; use `build_jade_art.ps1` for this art pass.
