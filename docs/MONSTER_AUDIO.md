Wolves, boars and mosslings now have separate hurt, attack and death voices,
with three recordings per event (27 clips). Every existing enemy resource in
these three families inherits the voice automatically. Weapon contact effects
still accompany the creature's reaction.

Wolf reactions use edited canine whines, yelps and growls. Boars combine
performed grunts with original nasal pain squeals. Mosslings combine a rough,
dark throat with recorded wood creaks, snapping twigs and a hollow reflection.
Sources and licenses are in `game/assets/audio/monsters/CREDITS.txt`.

Attack voices trigger once when a strike enters its active phase, including a
miss; a cancelled windup stays silent. Accepted nonlethal damage triggers the
hurt voice with a 0.18-second cooldown. Lethal damage triggers the death voice
alone. Voices use the existing spatial Effects mixer, distance limit and mute
setting. Streams are shared across creatures and play offline.

Rebuild the clips with `python tools/build_monster_audio.py --download`
(numpy, scipy and ffmpeg required). The download flag fetches missing CC0
authoring sources into the ignored project cache; shipped Ogg files need no
Python or network connection.

Run the integration checks with:

```powershell
godot --headless --path game --fixed-fps 60 --script res://tests/monster_audio.gd
```

The checks cover imported stream lengths, real health events, rapid hits,
strike timing, cancelled attacks, scene suppression, and lethal hits. The same
suite can run without `--headless` to exercise normal audio playback.

Build and launch the Windows Release executable with:

```powershell
./tools/run_release.ps1
```

Use `-BuildOnly` to export without opening the game. Install the matching
stable Godot export templates through the editor first. The launcher also
accepts a cached template at
`.local/godot_release/templates/windows_release_x86_64.exe`. Release uses
`--export-release`, stores the executable and PCK under the ignored
`game/builds/windows-release` directory, shares the existing project-local
saves, and writes runtime logs to `game/.local/release-game.log`.
