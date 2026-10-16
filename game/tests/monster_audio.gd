extends SceneTree
var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, description: String) -> void:
	if condition: print("PASS: ", description)
	else:
		failures += 1
		push_error("FAIL: " + description)

func frames(count: int) -> void:
	for i in count:
		await physics_frame
		await process_frame

func count_event(cue: StringName) -> int:
	return int(IronfieldAudio.instance.events.get(cue, 0))

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	current_scene = world
	for specimen in ["grey_wolf", "bristle_boar", "young"]:
		var data := load("res://data/enemies/%s.tres" % specimen) as EnemyData
		var mob := ActorBody.new()
		mob.enemy_definition = data
		mob.weapon = data.attack
		mob.visual_scene = data.visual
		mob.faction = &"enemies"
		world.add_child(mob)
		mob.visual.apply_variant(data)
		await frames(2)
		var family := String(data.family)
		for event in ["hurt", "attack", "death"]:
			var choices: Array = IronfieldAudio.instance.cues.get(StringName(family + "_" + event), [])
			check(choices.size() == 3, family + " has three " + event + " variations")
			for stream: AudioStream in choices:
				check(stream != null and stream.get_length() > .2 and stream.get_length() < 1.6, family + " imports a short, valid " + event + " recording")
		var hurt := StringName(family + "_hurt")
		var attack := StringName(family + "_attack")
		var death := StringName(family + "_death")
		var baseline := count_event(hurt)
		mob.health.apply_damage(0, null)
		check(count_event(hurt) == baseline, family + " rejected damage stays silent")
		mob.health.apply_damage(2, null)
		check(count_event(hurt) == baseline + 1, family + " accepted damage cries immediately")
		mob.health.apply_damage(2, null)
		check(count_event(hurt) == baseline + 1, family + " rapid hits cannot stack pain cries")
		await frames(14)
		mob.health.apply_damage(2, null)
		check(count_event(hurt) == baseline + 2, family + " pain voice recovers after cooldown")
		var attacks_before := count_event(attack)
		var generic_before := count_event(&"combat_cry")
		var swings_before := count_event(&"swing")
		check(mob.combat.request_attack(), family + " starts real combat attack")
		await frames(45)
		check(count_event(attack) == attacks_before + 1, family + " active strike emits exactly one species attack voice")
		check(count_event(&"combat_cry") == generic_before and count_event(&"swing") == swings_before, family + " attack avoids generic sword cries")
		mob.combat.cancel()
		attacks_before = count_event(attack)
		mob.combat.request_attack()
		mob.combat.cancel()
		await frames(30)
		check(count_event(attack) == attacks_before, family + " cancelled windup has no attack cry")
		world.set_meta("reference_audio", false)
		baseline = count_event(hurt)
		mob.health.apply_damage(2, null)
		check(count_event(hurt) == baseline, family + " respects scene audio suppression")
		world.set_meta("reference_audio", true)
		await frames(14)
		baseline = count_event(hurt)
		var deaths_before := count_event(death)
		mob.health.apply_damage(1000, null)
		mob.health.apply_damage(1000, null)
		check(count_event(death) == deaths_before + 1 and count_event(hurt) == baseline, family + " lethal hit emits one death cry without pain stacking")
		mob.queue_free()
		await frames(2)
	world.queue_free()
	await frames(2)
	print("MONSTER_AUDIO_RESULT failures=", failures)
	quit(0 if failures == 0 else 1)
