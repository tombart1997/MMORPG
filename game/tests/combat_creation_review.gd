extends "res://tests/combat_smoke.gd"

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.local/review_" + label + ".png")

func _run() -> void:
	var login = load("res://scenes/character_login.tscn").instantiate()
	login.roster_path = "user://creation_review_%d.cfg" % Time.get_ticks_usec()
	root.add_child(login)
	current_scene = login
	await frames(5)
	for i in range(4):
		login._select(i)
		check(login.heading.text == login.CLASSES[i], "Class carousel selects " + login.CLASSES[i])
	login._select(0)
	await capture("login")
	login.name_input.text = " "
	login._create()
	check(login.roster.is_empty(), "Empty character name is rejected")
	login._select(2)
	login.name_input.text = "Review Cinder"
	login._create()
	await frames(2)
	var world = current_scene
	world.persistence_enabled = false
	check(world.player.title == "Review Cinder" and world.player.get_meta("class_identity") == "Cinderhand", "Character creation enters world with selected name and class")
	check(world.persistence.path != "user://progression.json", "New character uses separate save from existing traveler")
	check(world.persistence.save_player(world.player), "New character saves successfully")
	world.player.title = "Changed"
	check(world.persistence.load_player(world.player) and world.player.title == "Review Cinder", "Name and class survive save/load")
	await frames(15)
	var player: ActorBody = world.player
	var controller: PlayerController
	for child in player.get_children():
		if child is PlayerController: controller = child
	await capture("village")
	player.ui_session.open_panel(player.ui_session.world_map)
	await frames(3)
	check(player.ui_session.world_map.get_viewport_rect().encloses(player.ui_session.world_map.get_global_rect()), "World map is fully visible inside viewport")
	await capture("map")
	player.ui_session.close()
	var key := InputEventKey.new()
	key.physical_keycode = KEY_SPACE
	key.pressed = true
	controller._unhandled_input(key)
	await frames(180)
	check(controller.auto_attack and player.combat.swing_serial >= 4, "One Space press continuously loops through full combos")
	controller._unhandled_input(key)
	var serial := player.combat.swing_serial
	await frames(60)
	check(not controller.auto_attack and player.combat.swing_serial == serial, "Second Space stops subsequent swings")
	var finish := load("res://data/attacks/player_finisher.tres") as AttackData
	check(is_equal_approx(finish.windup+finish.active+finish.recovery,.7), "Overhead finisher adds only 60ms over opening swing")
	player.combat.sequence_index = 1
	player.combat.idle_elapsed = 0
	player.combat.request_attack()
	await frames(12)
	await capture("overhead")
	await frames(9)
	await capture("overhead_impact")
	await frames(31)
	world.respawn_player()
	# Respawn places the actor 10 cm above the ground. Wait for the real
	# physics floor contact before exercising the normal mount restrictions.
	await frames(20)
	player.mounts.owned.assign([&"trail_horse"])
	player.mounts.selected = &"trail_horse"
	player.combat.cancel()
	player.mounts.combat_lock = 0
	check(player.mounts.unavailable().is_empty(), "Mount fixture is grounded and ready: " + player.mounts.unavailable())
	check(player.mounts.toggle(), "Horse mounts for animation review")
	controller.rig.yaw = -.65
	controller.rig.distance = 5
	for i in range(4):
		player.combat.idle_elapsed = 0
		player.combat.request_attack()
		check(player.combat.attack.display_name.begins_with("Mounted") and player.combat.sequence_index == i%2, "Horse alternates only two cuts")
		await frames(15)
		var equipment: Node3D = player.visual.sockets[&"WeaponSocket"].get_node("Equipment")
		var tip: Vector3 = player.to_local(equipment.get_node("Tip").global_position)
		check(tip.x < -.2 if i%2 == 0 else tip.x > .2, "Mounted blade reaches correct side of the saddle")
		await capture("horse_%d" % i)
		await frames(35)
	player.mounts.dismount()
	var camp: EnemyCamp = world.camps[3]
	check(camp.count >= 3 and camp.count <= 6, "Common packs preserve multiple enemies within the measured population budget")
	var moved := 0
	for member in camp.pack.members:
		for child in member.get_children():
			if child is EnemyBrain:
				check(member.global_position.distance_to(child.home) < 2.5, "Idle wandering remains confined")
				if member.global_position.distance_to(child.home) > .2: moved += 1
	check(moved < camp.count, "Pack does not wander in lockstep")
	player.global_position = camp.global_position + Vector3(0,.1,7)
	await frames(10)
	await capture("pack")
	print("Combat / creation review: %d failures" % failures)
	quit(1 if failures else 0)
