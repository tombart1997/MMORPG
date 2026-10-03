extends "res://tests/combat_smoke.gd"
## Rendered review in the actual outdoor game, using its controller and normal camera.
## Godot --write-movie review.avi --fixed-fps 60 records every engine frame at real speed.
## --label names each iteration. --sun adds review in the open clearing.
var output := "res://.local/hero_review"
var controller: PlayerController
var player: ActorBody
var live_enemy := false

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output + "/" + label + ".png")

func _run() -> void:
	var arguments := OS.get_cmdline_user_args()
	live_enemy = "--live" in arguments
	var index := arguments.find("--label")
	if index >= 0 and index + 1 < arguments.size(): output += "/" + arguments[index+1]
	DirAccess.make_dir_recursive_absolute(output)
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(8)
	player = world.player
	for child in player.get_children():
		if child is PlayerController: controller = child
	# Existing low-tier clearing: real terrain, illumination, target, collision and hit resolver.
	var camp: EnemyCamp = world.camps[0]
	player.global_position = camp.global_position + (Vector3(4,.15,5) if "--sun" in arguments else Vector3(0,.15,2.1))
	player.rotation.y = 0
	player.health.maximum = 10000
	player.health.current = 10000
	await frames(6)
	var target: ActorBody = camp.pack.members[0]
	var target_brain: EnemyBrain
	for actor in get_nodes_in_group("enemies"):
		for child in actor.get_children():
			if child is EnemyBrain:
				child.set_physics_process(false)
				if actor == target: target_brain = child
		if actor != target:
			actor.hide()
			actor.remove_from_group("enemies")
			actor.collision_layer = 0
			actor.collision_mask = 0
	target.health.maximum = 10000
	target.health.current = 10000
	target.global_position = player.global_position + Vector3(0,0,-1.7)
	target.rotation.y = PI
	controller.rig.yaw = 0
	controller.rig.pitch = -.55
	controller.rig.distance = 8
	await frames(5)
	await capture("gameplay_idle")
	for weapon in ["wayfarer_blade", "wakecleaver", "rift_cleaver"]:
		player.equipment.slots[&"weapon"] = ItemStack.new(StringName(weapon))
		player.equipment.refresh()
		player.health.maximum = 10000
		player.health.current = 10000
		player.ui_session.close()
		player.navigation.cancel()
		player.world_interaction.cancel()
		target.global_position = player.global_position + Vector3(0,0,-1.7)
		target.combat.cancel()
		controller.rig.distance = 5
		controller.rig.yaw = 2.6
		await frames(12)
		check(player.visual.long_sword == (weapon != "wayfarer_blade"), weapon + " selects its weapon-length stance")
		check(player.visual.sampled_clip == (&"idle" if weapon == "wayfarer_blade" else &"longsword_idle"), weapon + " samples its authored idle guard")
		await capture(weapon + "_front")
		Input.action_press("move_forward")
		await frames(8)
		check(player.visual.sampled_clip == (&"run" if weapon == "wayfarer_blade" else &"longsword_run"), weapon + " carries its grip into real locomotion")
		await capture(weapon + "_run")
		Input.action_release("move_forward")
		await frames(4)
		player.rotation.y = 0
		target.global_position = player.global_position + Vector3(0,0,-1.7)
		controller.rig.yaw = 1.2
		await frames(6)
		await capture(weapon + "_side")
		controller.rig.distance = 8
		controller.rig.yaw = -.35
		await frames(6)
		await capture(weapon + "_gameplay")
		player.combat.sequence_index = -1
		player.combat.idle_elapsed = 2
		var origin := player.global_position
		var hits := player.combat.total_hits
		var last_serial := -1
		var last_phase := -1
		var previous_tip := Vector3.ZERO
		var maximum_step := 0.0
		var maximum_grip_gap := 0.0
		var probe := preload("res://tests/combat_visual_probe.gd").new()
		probe.actor = player
		world.add_child(probe)
		if live_enemy: target_brain.set_physics_process(true)
		controller.auto_attack = true
		for frame in range(150):
			await frames(1)
			var frame_image: Image
			if DisplayServer.get_name() != "headless" and (player.combat.swing_serial != last_serial or player.combat.phase != last_phase):
				await RenderingServer.frame_post_draw
				frame_image = root.get_texture().get_image()
			# Keep the target inside the real cone as collision-based authored lunges advance.
			if not live_enemy: target.global_position = player.global_position + Vector3(0,0,-1.7)
			var equipment: Node3D = player.visual.sockets[&"WeaponSocket"].get_node("Equipment")
			var tip: Vector3 = equipment.get_node("Tip").global_position
			if equipment.has_node("OffhandGrip"):
				var offhand: Node3D = player.visual.sockets[&"OffhandSocket"]
				maximum_grip_gap = maxf(maximum_grip_gap, offhand.global_position.distance_to(equipment.get_node("OffhandGrip").global_position))
			if frame > 0: maximum_step = maxf(maximum_step, previous_tip.distance_to(tip))
			previous_tip = tip
			if player.combat.swing_serial != last_serial or player.combat.phase != last_phase:
				last_serial = player.combat.swing_serial
				last_phase = player.combat.phase
				if player.combat.sequence_index >= 0 and player.combat.swing_serial < 20:
					if frame_image: frame_image.save_png(output + "/%s_cut%d_%s.png" % [weapon, player.combat.sequence_index+1, player.combat.phase_name()])
				if player.combat.phase == MeleeCombat.Phase.ACTIVE:
					print("BLADE ", weapon, " cut=", player.combat.sequence_index+1, " tip=", player.to_local(tip))
		controller.auto_attack = false
		await frames(50)
		target_brain.set_physics_process(false)
		target.combat.cancel()
		check(player.combat.total_hits >= hits + 3, weapon + " auto-attack lands three real hits")
		check(player.global_position.distance_to(origin) > .5, weapon + " preserves combat lunges")
		if weapon != "wayfarer_blade": check(maximum_grip_gap < .09, weapon + " keeps the offhand on the long grip across the combo (%.3fm)" % maximum_grip_gap)
		var report: Dictionary = probe.report(output + "/" + weapon + "_motion.csv")
		if not live_enemy:
			check(report.combo_step_m < .06, weapon + " joins successive cuts without a guard snap")
			check(report.max_step_m < .8, weapon + " distributes preparation and impact across visible frames")
			check(report.offhand_gap_m < .04, weapon + " maintains the authored grip in every render pose")
		print("PER_RENDER ",weapon," ",JSON.stringify(report))
		probe.queue_free()
		print("REVIEW ", weapon, " largest rendered tip step=", maximum_step, " serial=", player.combat.swing_serial, " hits=", player.combat.total_hits-hits, " auto=", controller.auto_attack, " hp=", player.health.current)
		player.combat.cancel()
		player.global_position = origin
	player.equipment.slots[&"weapon"] = ItemStack.new(&"briarsteel_edge")
	player.equipment.refresh()
	await frames(8)
	check(not player.visual.long_sword, "Slightly extended Briarsteel blade retains the regular sword stance")
	controller.rig.yaw = 2.7
	controller.rig.pitch = -.05
	controller.rig.distance = 4
	await frames(6)
	await capture("portrait_game")
	print("Hero combat review: %d failures" % failures)
	quit(1 if failures else 0)
