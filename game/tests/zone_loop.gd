extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(5)
	var player: ActorBody = world.player
	check(world.camps.size() == FirstMapContent.POINTS.size()+3 and world.camps[0].count + world.camps[1].count + world.camps[2].count == 12,
		"Expanded zone preserves original twelve mosslings and all authored camps")
	check(player.visual.skeleton.find_bone("Hand.R") >= 0 and player.visual.skeleton.find_bone("Shin.L") >= 0,
		"Imported humanoid skeleton has hand and leg chains")
	check(player.visual.sockets[&"WeaponSocket"].get_node_or_null("Equipment") != null,
		"Weapon attached through replaceable equipment socket")
	check(player.visual.sockets[&"ArmorSocket"].get_node_or_null("Equipment") != null,
		"Armor attached independently of gameplay")
	check(world.camps[0].pack.members[0].visual.creature, "Enemies use separate creature visual scene")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/zone.png")
	Input.action_press("move_forward")
	await frames(100)
	Input.action_release("move_forward")
	check(player.position.z < 3.1 and absf(player.position.y) < 0.1,
		"Walk from waystone along terrain path toward first camp")
	check(player.visual.animation_player.has_animation("run"), "Visual adapter provides locomotion animation")
	var camp: EnemyCamp = world.camps[0]
	camp.respawn_delay = 0.3
	player.position = camp.position + Vector3(0, 0, 2.1)
	player.rotation.y = 0
	var health_before := player.health.current
	var swing_count := 0
	while camp.pack.living_count() > 0 and player.health.is_alive() and swing_count < 7:
		player.combat.request_attack()
		await frames(5)
		check(player.visual.state == &"windup", "Visual follows gameplay windup")
		while player.combat.is_attacking():
			await frames(1)
		swing_count += 1
	check(camp.pack.living_count() == 0, "Real melee sequences can clear first group")
	check(player.health.current < health_before, "Camp deals damage during real melee exchange")
	check(player.progression.kills == 3 and player.progression.xp == 60,
		"Each real combat kill awards XP exactly once")
	var drop_count := get_nodes_in_group("loot").size()
	var coin_bundles := 0
	for bundle: LootPickup in get_nodes_in_group("loot"):
		if bundle.coins > 0: coin_bundles += 1
	check(coin_bundles == 3 and drop_count >= 3, "Each enemy drops coins; materials roll independently instead of flooding every kill")
	if camp.pack.living_count() != 0:
		quit(1)
		return
	var xp_before := player.progression.xp
	camp.pack.members[0].health.apply_damage(500, player)
	check(player.progression.xp == xp_before and get_nodes_in_group("loot").size() == drop_count,
		"Corpse damage cannot duplicate XP or drops")
	var drop: LootPickup = get_nodes_in_group("loot")[0]
	var saved_position := player.position
	player.position = ZoneTerrain.START
	check(not drop.collect(player), "Pickup requires actual proximity")
	player.position = saved_position
	player.global_position = drop.global_position
	check(drop.collect(player) and not drop.collect(player), "Drop collected exactly once")
	await frames(2)
	var gather := InputEventKey.new()
	gather.physical_keycode = KEY_E
	gather.pressed = true
	for bundle in get_nodes_in_group("loot"):
		player.global_position = bundle.global_position
		world._unhandled_input(gather)
	await frames(2)
	check(player.inventory.gold >= 32 and player.inventory.gold <= 38 and player.inventory.count(&"moss_shard") <= 3,
		"E gathers nearby individual entries into gold and stackable inventory")
	player.health.apply_damage(50, camp.pack.members[0])
	var wounded := player.health.current
	var tonics := player.inventory.count(&"field_tonic")
	var drink := InputEventKey.new()
	drink.physical_keycode = KEY_Q
	drink.pressed = true
	world._unhandled_input(drink)
	check(player.health.current == minf(player.health.maximum, wounded + 45)
		and player.inventory.count(&"field_tonic") == tonics - 1, "Tonic heals and removes one item")
	player.position = camp.position
	await frames(30)
	check(camp.generation == 1, "Respawn waits while player occupies cleared camp")
	player.position = ZoneTerrain.START
	await frames(25)
	check(camp.generation == 2 and camp.pack.living_count() == 3,
		"Group respawns after timer and player departure")
	check(player.progression.xp == xp_before, "Respawning itself awards nothing")
	var second: EnemyCamp = world.camps[1]
	player.position = second.pack.members[0].global_position + Vector3(0, 0, 2.1)
	player.rotation.y = 0
	player.combat.cancel()
	swing_count = 0
	while second.pack.living_count() > 0 and player.health.is_alive() and swing_count < 8:
		for member in second.pack.members:
			if member.health.is_alive():
				player.global_position = member.global_position + Vector3(0, 0, 2.1)
				player.rotation.y = 0
				break
		player.combat.request_attack()
		while player.combat.is_attacking():
			await frames(1)
		swing_count += 1
	check(second.pack.living_count() == 0, "Player can fight a second independent camp")
	if second.pack.living_count() != 0:
		quit(1)
		return
	check(player.progression.level == 1 and player.progression.xp == 160,
		"Two introductory groups no longer award an immediate level")
	player.progression.award_xp(player.progression.xp_required()-player.progression.xp)
	check(player.health.maximum == 180, "Level increases maximum health")
	var saved_gold := player.inventory.gold
	var saved_xp := player.progression.xp
	player.health.apply_damage(1000, second.pack.members[0])
	check(not player.health.is_alive(), "Zone player can die")
	var nearby: LootPickup = get_nodes_in_group("loot")[0]
	player.global_position = nearby.global_position
	check(not nearby.collect(player), "Dead player cannot pick up drops")
	var event := InputEventKey.new()
	event.physical_keycode = KEY_R
	event.pressed = true
	world._unhandled_input(event)
	await frames(3)
	check(player.health.current == 180 and player.position.distance_to(ZoneTerrain.START) < 0.2,
		"R revives player at waystone")
	check(player.inventory.gold == saved_gold and player.progression.xp == saved_xp,
		"Revival preserves progression and inventory")
	check(player.visual.state != &"death" and player.collision_layer == 2,
		"Revival restores visual state and actor collision")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/zone_after.png")
	world.queue_free()
	await frames(2)
	print("Zone loop complete: %d failures" % failures)
	quit(1 if failures else 0)
