# Full-body sword motion and skill attachments

The regular and long-sword combos now initiate the cut at the pelvis, unwind through
the spine and chest, transfer weight across bent knees, and return to a common
guard. The free arm counterbalances the regular blade. Both hands retain the
extended grip on long swords. Foot targets remain planted, with small boot pivots.
The overhead finisher adds a deeper compression and forward follow-through.

The editable Jade hero, materials and rig are preserved. Only the existing sword
clips were rebaked. Attack durations, active markers, lunges and damage remain
controlled by the existing gameplay resources. Thunder Cleave and Bladestorm use
the equipment-specific sword clips; Sunbreaker uses the authored overhead cut.
Moving skill casts retain their existing locomotion blend.

Manual animation sampling previously left BoneAttachment transforms behind the
skin until a later skeleton update. ActorVisual now synchronizes the sockets after
transition blending, recoil and mounted posing. Blade trails and effects derive
world positions directly from that final skeleton pose. Skill spectacles update
after actor presentation, so movement and turns affect the same rendered frame.

- Thunder originates from the animated blade; Sunbreaker connects the blade to its
  ground impact. Their attack footprints retain the original placement and reach.
- Spirit Edge wraps the actual equipped blade rather than a fixed caster offset.
- Bladestorm launches an echo of the equipped mesh from the grip. Its orbit follows
  the chest and stays visibly connected to the animated blade. The echo shares mesh
  resources and has no duplicate skeleton or gameplay components.
- Flashstep streaks follow the independently animated feet. Phoenix Ring's initial
  channel comes from the hand; its persistent ground field stays at its cast site.
- Non-cutting buff/dash gestures no longer generate broad sword-trail fans. Trails
  fade across their short history. Effects expire on death, buff removal or timeout.

## Rendered review and checks

The actual outdoor scene was run on Godot 4.7.2's Compatibility renderer.
Reviewed authored windup, impact and recovery poses, normal auto-attacks
with three swords, and all six skills while strafing. Images are under
`screenshots/character-motion`; [review.html](screenshots/character-motion/review.html)
switches between phases and skill views. These are engine captures, not Blender
previews.

The 41-sample checks across each of six sword clips measure:

| Motion | Horizontal cuts | Overhead finisher |
|---|---:|---:|
| Pelvis rotation range | 34 degrees | 17 degrees |
| Shoulder rotation range | 97 degrees | 53 degrees |
| Pelvis weight shift | 16 cm | 16 cm |
| Maximum foot-position drift | 3.1 mm | 2.2 mm |
| Maximum authored long-grip gap | 6.4 mm | 9.3 mm |

The moving, rendered skill checks reported zero blade/chest anchor disagreement
after presentation and less than 0.01 mm equipment-position disagreement. The live
three-sword combo review passed real hit, lunge, recovery continuity and grip
checks. The regression suite also exercises removing/replacing a weapon after
Bladestorm's cast recovery while its area remains active.

Rebake on the existing editable hero:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b blender/characters/warden_high.blend --python-exit-code 1 -P blender/scripts/update_hero_motion.py
```

Run rendered checks with `./tools/run.ps1 -Test -Windowed -Suite character_motion`.
For continuous real combat, use `-Suite hero_combat_review -Windowed`. Both are
included in the complete regression run.

Final validation: the complete twenty-suite run passed with zero failures,
including the moving skill attachment and in-flight equipment replacement checks.
