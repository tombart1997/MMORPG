extends "res://tests/combat_smoke.gd"
## Imported mesh/rig contracts and sampled poses, plus real combat timing checks.
var capture_index: int = 0

func capture(title: String) -> void:
	await frames(2)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/character_%02d_%s.png" % [capture_index, title])
	capture_index += 1

func pose(actor: ActorBody, velocity: Vector3 = Vector3.ZERO, delta: float = 0.2) -> void:
	actor.visual.present(velocity, actor.combat, actor.health, actor.title, delta)

func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(5)
	world.set_physics_process(false)
	var player: ActorBody = world.player
	var enemy: ActorBody = world.camps[0].pack.members[0]
	for child in world.get_children():
		if child is CanvasLayer: child.hide()
	for actor in get_nodes_in_group("players") + get_nodes_in_group("enemies"):
		actor.set_process(false)
		actor.combat.set_physics_process(false)
		for child in actor.get_children():
			if child is PlayerController:
				child.set_physics_process(false)
				child.rig.set_process(false)
			if child is EnemyBrain:
				child.set_physics_process(false)
		if actor != player and actor != enemy: actor.hide()
	player.position = Vector3(-0.9, 0, 8)
	enemy.global_position = Vector3(1.1, 0, 8)
	player.rotation.y = 0
	enemy.rotation.y = 0
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.position = Vector3(3.1, 2.1, 4.3)
	camera.look_at(Vector3(0, 0.95, 8))
	camera.fov = 47
	camera.current = true
	var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/manifest.json"))
	for actor in [player, enemy]:
		var visual: ActorVisual = actor.visual
		var asset: String = "briarling" if visual.creature else "warden_high"
		check(visual.skeleton.get_bone_count() == manifest.assets[asset].bones.size(), asset + " rig matches exported contract")
		var skins := 0
		for mesh in visual.model.find_children("*", "MeshInstance3D", true, false):
			if mesh.skin != null: skins += 1
		check(skins > 0, asset + " uses actual skinned imported meshes")
		for clip in manifest.assets[asset].clips:
			check(visual.animation_player.has_animation(clip), asset + " imports " + clip)
			check(absf(visual.animation_player.get_animation(clip).length - float(manifest.assets[asset].clips[clip])) < .001,
				asset + " preserves duration of " + clip)
	pose(player)
	pose(enemy)
	await capture("idle")
	var equipment: Node3D = player.visual.sockets[&"WeaponSocket"].get_node("Equipment")
	var grip: Marker3D = equipment.get_node("Grip")
	var tip: Marker3D = equipment.get_node("Tip")
	var hand_index := player.visual.skeleton.find_bone("Hand.R")
	var hand := player.visual.skeleton.global_transform * player.visual.skeleton.get_bone_global_pose(hand_index)
	check(grip.global_position.distance_to(hand.origin) < .12, "Sword grip sits inside the animated hand")
	check(absf(grip.global_position.distance_to(tip.global_position) - 1.08) < .01, "Separate weapon keeps its authored scale")
	var shin := player.visual.skeleton.find_bone("Shin.L")
	pose(player, Vector3(0, 0, -5.5), .13)
	pose(enemy, Vector3(0, 0, -3.2), .13)
	var initial_pose := player.visual.skeleton.get_bone_pose_rotation(shin)
	await capture("run_a")
	pose(player, Vector3(0, 0, -5.5), .23)
	pose(enemy, Vector3(0, 0, -3.2), .23)
	check(initial_pose.angle_to(player.visual.skeleton.get_bone_pose_rotation(shin)) > .1, "Run animates the skinned leg chain")
	await capture("run_b")
	pose(player)
	pose(enemy)
	check(player.visual.state == &"idle", "Run transitions back to idle")
	var tips: Array[Vector3] = []
	for attack in player.attack_sequence:
		player.combat.attack = attack
		player.combat.swing_serial += 1
		player.combat.phase = MeleeCombat.Phase.WINDUP
		player.combat.phase_elapsed = attack.windup * .8
		pose(player)
		await capture(String(attack.animation_clip) + "_windup")
		var before := tip.global_position
		player.combat.phase = MeleeCombat.Phase.ACTIVE
		player.combat.phase_elapsed = attack.active * .5
		pose(player)
		await capture(String(attack.animation_clip) + "_active")
		check(player.visual.sampled_clip == attack.animation_clip, "Combo selects " + attack.animation_clip)
		check(absf(player.visual.sampled_time - .425) < .001, "Active phase maps to authored swing interval")
		check(before.distance_to(tip.global_position) > .25, "Sword traverses visible swing for " + attack.animation_clip)
		tips.append(tip.global_position)
		player.combat.phase = MeleeCombat.Phase.RECOVERY
		player.combat.phase_elapsed = attack.recovery * .6
		pose(player)
		await capture(String(attack.animation_clip) + "_recovery")
	check(tips[0].distance_to(tips[1]) > .15 and tips[1].distance_to(tips[2]) > .15, "Three attack clips have distinct poses")
	# Different frame deltas must sample the same combat pose, not advance a second clock.
	player.combat.phase = MeleeCombat.Phase.ACTIVE
	player.combat.phase_elapsed = .06
	pose(player, Vector3.ZERO, 1.0 / 30)
	var sample := player.visual.sampled_time
	pose(player, Vector3.ZERO, 1.0 / 144)
	check(is_equal_approx(sample, player.visual.sampled_time), "Attack sampling is independent of rendering frame rate")
	var chest := player.visual.skeleton.find_bone("Chest")
	var normal_chest := player.visual.skeleton.get_bone_pose_rotation(chest)
	player.visual.react_to_hit()
	pose(player, Vector3.ZERO, .12)
	check(player.visual.hit_weight > 0 and normal_chest.angle_to(player.visual.skeleton.get_bone_pose_rotation(chest)) > .01,
		"Imported hit reaction layers over committed attack")
	check(player.visual.sampled_clip == player.combat.attack.animation_clip, "Hit reaction does not replace attack playback")
	await capture("player_hit")
	enemy.combat.phase = MeleeCombat.Phase.WINDUP
	enemy.combat.phase_elapsed = enemy.weapon.windup * .85
	pose(enemy)
	await capture("enemy_windup")
	enemy.combat.phase = MeleeCombat.Phase.ACTIVE
	enemy.combat.phase_elapsed = enemy.weapon.active * .5
	pose(enemy)
	check(absf(enemy.visual.sampled_time - .425) < .001, "Enemy timing samples same authored active markers")
	await capture("enemy_active")
	enemy.combat.cancel()
	enemy.visual.react_to_hit()
	pose(enemy, Vector3.ZERO, .12)
	check(enemy.visual.hit_weight > 0, "Enemy has imported hit reaction")
	await capture("enemy_hit")
	# Real ticks still drive hits outside sanctuary; importing animations must not inject damage tracks.
	player.combat.cancel()
	player.combat.attack = player.weapon
	player.combat.sequence_index = -1
	player.position = Vector3(0, 0, 2)
	enemy.global_position = Vector3(0, 0, 0.3)
	enemy.health.current = 75
	player.set_process(true)
	player.combat.set_physics_process(true)
	player.combat.request_attack()
	await frames(5)
	check(enemy.health.current == 75 and player.visual.sampled_time < .30, "Visible windup remains harmless")
	await frames(9)
	check(enemy.health.current == 50 and player.visual.sampled_time >= .30 and player.visual.sampled_time <= .55,
		"Actual damage occurs while the visible animation is in active swing")
	await frames(9)
	check(enemy.health.current == 50 and player.visual.sampled_time >= .55,
		"Recovery pose cannot damage the target a second time")
	player.combat.set_physics_process(false)
	player.set_process(false)
	player.combat.cancel()
	player.position = Vector3(-.9, 0, 8)
	enemy.global_position = Vector3(1.1, 0, 8)
	player.health.apply_damage(1000, null)
	enemy.health.apply_damage(1000, null)
	pose(player, Vector3.ZERO, .4)
	pose(enemy, Vector3.ZERO, .4)
	await capture("death_fall")
	pose(player, Vector3.ZERO, 1.0)
	pose(enemy, Vector3.ZERO, 1.0)
	check(player.visual.sampled_clip == &"death" and is_equal_approx(player.visual.sampled_time, 1.2), "Death reaches final pose")
	var fallen := player.visual.skeleton.get_bone_pose_rotation(0)
	pose(player, Vector3.ZERO, 2.0)
	check(fallen.is_equal_approx(player.visual.skeleton.get_bone_pose_rotation(0)), "Corpse holds death pose without looping")
	await capture("death_held")
	world.respawn_player()
	pose(player)
	check(player.visual.state == &"idle" and player.visual.hit_weight == 0, "Revival clears death and reaction state")
	player.visual.equip_visual(&"WeaponSocket", null)
	check(player.visual.sockets[&"WeaponSocket"].get_node_or_null("Equipment") == null, "Weapon can be removed without editing character mesh")
	player.visual.equip_visual(&"WeaponSocket", load("res://scenes/visuals/iron_sword.tscn"))
	check(player.visual.sockets[&"WeaponSocket"].get_node_or_null("Equipment") != null, "Weapon can be re-equipped through same socket")
	world.queue_free()
	await frames(2)
	print("Character pipeline complete: %d failures" % failures)
	quit(1 if failures else 0)
