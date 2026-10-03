# Horse and rider reference pass

The supplied riding-horse image guided a dark bay coat, black lower legs,
a sloping neck, a substantial barrel, fine lower limbs, and an upright seated
rider. The previous mount's tall neck, angular leg construction and flat saddle
pad were replaced. The player's existing identity, equipment and animation rig
remain the basis of the rider.

The connected horse mesh and diffuse texture come from **8tibGames**, licensed
CC0: https://opengameart.org/content/horse. The original archive, Blender source,
texture and license provenance are in `blender/reference/horse/`.

The horse adaptation adds subdivision, corrected metre scale and orientation,
skin weights, a fitted bridle, reins, eyes, black points, dark hooves, flowing
mane and tail, a curved pad, shaped leather saddle and D-shaped stirrups. The
export has 37,424 triangles, nine material surfaces, one skin and 23 bones.
Idle, walk, trot and canter retain the existing runtime animation names.

The rider was reviewed separately in front, side and three-quarter renders.
Shoulder shells and boots were reduced, skin and roughness were adjusted, and
the robe received a shorter riding split and revised thigh weights. The seat
and stirrups were then fitted to the rider. The rider's origin is raised 0.65 m;
the saddle seat is at 1.535 m. The resting sword hand sits lower beside the
body, the left hand follows the rein grip, and both ankles follow the animated
stirrups. The existing 18-bone rider rig and sixteen combat/skill clips survive.

Every requested view was rendered and opened for visual inspection. Iteration
found and corrected a source object transform error, floating bridle details,
an oversized mane, harsh tail bends, overextended robe weights and a Godot
material import that dropped vertex tint. `horse_import.gd` enables the exported
vertex shading when the GLB is imported. The coat was also checked under the
production outdoor illumination and tuned to retain its brown color.

## Final images

- Godot horse: [front](screenshots/horse-reference/godot/final/horse_front.png),
  [side](screenshots/horse-reference/godot/final/horse_side.png),
  [three-quarter](screenshots/horse-reference/godot/final/horse_threequarter.png).
- Godot rider: [front](screenshots/horse-reference/godot/final/rider_front.png),
  [side](screenshots/horse-reference/godot/final/rider_side.png),
  [three-quarter](screenshots/horse-reference/godot/final/rider_threequarter.png).
- Godot mounted pose: [front](screenshots/horse-reference/godot/final/mounted_front.png),
  [side](screenshots/horse-reference/godot/final/mounted_side.png),
  [three-quarter](screenshots/horse-reference/godot/final/mounted_threequarter.png).
- Production outdoor scene: [close view](screenshots/horse-reference/production_close.png),
  [canter](screenshots/horse-reference/production_canter.png).

The neutral Godot stage uses the shipped GLB and the actual `ActorVisual` mounted
pose. Its fixture sets ownership directly for visual review. The separate route
and production presentation suites exercise normal purchasing, mounting,
navigation, attacks, dismounting and persistence.

## Validation

- `horse_reference_review`: imported textures, vertex shading, rig and all four
  clips; idle ankle error 0.0067 m and rein grip error 0.0007 m.
- `presentation_upgrade`: actual outdoor canter and both mounted cuts; maximum
  ankle error 0.0107 m and rein grip error 0.0014 m; real hits and hoof audio.
- `character_motion`: all six sword clips, planted contacts, two-handed grips,
  moving skills, sockets and equipment replacement.
- `route_mount`: purchase, ownership, 17 waypoints, mounting camera height,
  obstacle detour, saves, combat lockout, death and revival. Zero failures.
- `git diff --check`: passed.

## Rebuild and review

From the repository root:

```powershell
blender -b --factory-startup --python-exit-code 1 -P blender/scripts/refine_riding_hero.py
blender -b --factory-startup --python-exit-code 1 -P blender/scripts/build_trail_horse.py
Godot_console --headless --path game --editor --import --quit
Godot_console --path game --script res://tests/horse_reference_review.gd -- --label final
blender -b blender/mounts/trail_horse.blend --python-exit-code 1 -P blender/scripts/review_mount_asset.py -- horse_final
```

The rider refinement rebuilds from the preserved original
`blender/reference/rider/warden_riding_base.blend`, so repeat runs do not apply
proportion changes cumulatively. Editable output is saved to
`blender/characters/warden_high.blend` and `blender/mounts/trail_horse.blend`.
