extends SceneTree
var failures: int = 0

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, description: String) -> void:
	if condition:
		print("PASS: ", description)
	else:
		failures += 1
		push_error("FAIL: " + description)

func frames(count: int) -> void:
	for i in range(count):
		await physics_frame
		await process_frame

func _run() -> void:
	var scene: PackedScene = load("res://scenes/arena.tscn")
	var world = scene.instantiate()
	root.add_child(world)
	current_scene = world
	await frames(3)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/arena.png")
	var player: ActorBody = world.player
	var pack: AggroGroup = world.pack
	var controller: PlayerController
	for child in player.get_children():
		if child is PlayerController:
			controller = child
	check(pack.members.size() == 6, "Six enemies spawn")
	check(not pack.has_target(), "Pack starts idle")
	var origin := player.position
	Input.action_press("move_forward")
	await frames(20)
	Input.action_release("move_forward")
	check(player.position.z < origin.z - 1.0, "W moves player forward through physics")
	check(absf(player.position.y) < 0.05, "Player stands on arena floor")
	var motion := InputEventMouseMotion.new()
	motion.relative = Vector2(100, 30)
	if DisplayServer.get_name() == "headless":
		controller.rig.apply_look_delta(motion.relative)
	else:
		controller.rig._unhandled_input(motion)
	check(controller.rig.yaw < -0.2 and controller.rig.pitch < -0.3, "Camera look controls yaw and pitch")
	if DisplayServer.get_name() != "headless":
		var escape := InputEventKey.new()
		escape.physical_keycode = KEY_ESCAPE
		escape.pressed = true
		Input.parse_input_event(escape)
		await frames(2)
		check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Escape releases cursor")
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		Input.parse_input_event(click)
		await frames(2)
		check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and not player.combat.is_attacking(),
			"Recapture click does not attack")
		click = click.duplicate()
		click.pressed = false
		Input.parse_input_event(click)
		await frames(2)
		click = click.duplicate()
		click.pressed = true
		Input.parse_input_event(click)
		await frames(2)
		check(player.combat.is_attacking(), "Captured left click requests sword attack")
		click = click.duplicate()
		click.pressed = false
		Input.parse_input_event(click)
		await frames(42)
	controller.set_physics_process(false)
	for enemy in pack.members:
		for child in enemy.get_children():
			if child is EnemyBrain:
				child.set_physics_process(false)
	player.position = Vector3.ZERO
	player.rotation = Vector3.ZERO
	var positions := [Vector3(-0.8, 0, -1.8), Vector3(0, 0, -2),
		Vector3(0.8, 0, -1.8), Vector3(0, 0, 2), Vector3(2, 0, 0), Vector3(0, 0, -5)]
	for i in range(6):
		pack.members[i].position = positions[i]
	check(player.combat.request_attack(), "Idle actor accepts attack")
	check(not player.combat.request_attack(), "Overlapping attacks rejected")
	await frames(5)
	check(player.combat.phase == MeleeCombat.Phase.WINDUP, "Distinct windup")
	check(pack.members[0].health.current == 75, "Windup deals no damage")
	await frames(9)
	check(player.combat.phase == MeleeCombat.Phase.ACTIVE, "Distinct active phase")
	check(player.combat.swing_hits == 3, "One swing hits three enemies")
	check(pack.members[0].health.current == 50, "Expected damage")
	check(pack.has_target(), "Damage alerts entire pack")
	await frames(9)
	check(player.combat.phase == MeleeCombat.Phase.RECOVERY, "Distinct recovery")
	check(pack.members[0].health.current == 50, "No duplicate damage in active frames")
	check(pack.members[3].health.current == 75 and pack.members[4].health.current == 75
		and pack.members[5].health.current == 75, "Behind, side and distant targets excluded")
	check(not player.combat.request_attack(), "Recovery prevents attacks")
	await frames(20)
	check(player.combat.phase == MeleeCombat.Phase.IDLE, "Recovery returns to idle")
	player.combat.request_attack()
	await frames(42)
	check(pack.members[0].health.current == 25, "New swing resets hit tracking")
	world._box(Vector3(0, 1, -1), Vector3(4, 2, 0.2), Color.GRAY)
	await frames(2)
	player.combat.request_attack()
	await frames(42)
	check(player.combat.swing_hits == 0, "Walls block melee")
	world.get_child(world.get_child_count() - 1).queue_free()
	await frames(2)
	var distant: ActorBody = pack.members[5]
	var previous_distance := distant.position.distance_to(player.position)
	for enemy in pack.members:
		for child in enemy.get_children():
			if child is EnemyBrain:
				child.set_physics_process(true)
	await frames(180)
	check(distant.position.distance_to(player.position) < previous_distance - 1,
		"Unstruck group member approaches after aggro")
	check(player.health.current < player.health.maximum, "Enemies attack and damage player")
	pack.members[0].health.apply_damage(1000, player)
	check(not pack.members[0].health.is_alive(), "Lethal damage kills enemy")
	check(pack.members[0].collision_layer == 0, "Corpses stop blocking actors")
	check(not pack.members[0].combat.request_attack(), "Dead enemies cannot attack")
	player.health.apply_damage(1000, pack.members[1])
	check(not pack.has_target(), "Pack stops targeting dead player")
	check(not player.combat.request_attack(), "Dead player cannot attack")
	check(not player.health.apply_damage(1, pack.members[1]), "Dead health rejects damage")
	var restart := InputEventKey.new()
	restart.physical_keycode = KEY_R
	restart.pressed = true
	world._unhandled_input(restart)
	await frames(3)
	var fresh = current_scene
	check(fresh.player.health.current == 160 and fresh.pack.living_count() == 6
		and not fresh.pack.has_target(), "Fresh encounter resets health and pack")
	fresh.queue_free()
	await frames(2)
	print("Combat integration complete: %d failures" % failures)
	quit(1 if failures else 0)
