extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(12)
	var player: ActorBody = world.player
	var hud: ZoneHUD
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	check(world.camps.size() == 33, "First map contains 33 distinct encounters")
	check(world.settlement.npcs.size() == 9, "Expanded village has nine service NPCs")
	check(player.map_state.region.bounds == ZoneTerrain.BOUNDS, "Map and terrain share expanded bounds")
	var levels := {}
	var ids := {}
	var nav_map := player.get_world_3d().navigation_map
	for npc: WorldNPC in world.settlement.npcs:
		var path := NavigationServer3D.map_get_path(nav_map, ZoneTerrain.START, npc.global_position, true)
		check(SafeArea.protects(npc) and not path.is_empty() and path[-1].distance_to(npc.global_position) < 2, "%s is reachable in the safe village" % npc.data.id)
	for camp: EnemyCamp in world.camps:
		var data := camp.enemy_data
		ids[data.id] = true
		levels[data.level] = true
		check(camp.pack.members.size() >= 3 if data.tier <= 2 else camp.pack.members.size() == 1, "%s tier grouping" % data.id)
		var kinds := {}
		for entry in data.drops.entries:
			kinds[entry.item.item_type] = true
			if entry.item.item_type in ["weapon","armor"]:
				check(entry.chance <= .004, "%s equipment is rare" % data.id)
		check(kinds.has_all(["weapon","armor","consumable","material"]) and data.gold_min > 0, "%s complete loot table" % data.id)
		var path := NavigationServer3D.map_get_path(nav_map, ZoneTerrain.START, camp.global_position, true)
		check(not path.is_empty() and path[-1].distance_to(camp.global_position) < 2, "%s reachable from village" % data.id)
	check(ids.size() == 33 and levels.size() == 25, "Unique types span every level from 1 through 25")
	check(player.progression.xp_required() == 600 and PlayerProgression.requirement_for(25) == 25080, "Slower quadratic XP curve")
	# Real specialist transaction, including rejection without consuming anything.
	var crafter: WorldNPC = world.settlement.npcs[8]
	player.global_position = crafter.global_position + Vector3(1,0,0)
	await frames(3)
	var offer: ShopOffer = crafter.data.shop.offers[0]
	var service := MerchantService.new()
	player.inventory.gold = 2000
	check(not service.buy(crafter,player,0,1).is_empty() and player.inventory.gold == 2000, "Craft rejects missing species materials atomically")
	for id in offer.ingredients: player.inventory.add_item(ItemCatalog.get_item(StringName(id)),int(offer.ingredients[id]))
	check(service.buy(crafter,player,0,1).is_empty() and player.inventory.count(offer.item.id) == 1 and player.inventory.gold == 2000-offer.price, "Craft consumes materials and gold and grants equipment")
	for id in offer.ingredients: check(player.inventory.count(StringName(id)) == 0, "Craft consumed required material")
	# Solo elite acquires and actually runs at a nearby unprovoking player.
	var elite: EnemyCamp = world.camps[12]
	var foe: ActorBody = elite.pack.members[0]
	player.global_position = elite.global_position + Vector3(0,0,6)
	await frames(3)
	var distance := foe.global_position.distance_to(player.global_position)
	await frames(25)
	check(elite.enemy_data.tier >= 3 and elite.pack.target == player and foe.global_position.distance_to(player.global_position) < distance-1, "Solo elite proactively runs toward player")
	world.respawn_player()
	await frames(5)
	check(not elite.pack.has_target(), "Sanctuary clears elite pursuit")
	player.mounts.owned.assign([&"trail_horse"])
	player.mounts.selected = &"trail_horse"
	player.mounts.combat_lock = 0
	check(player.mounts.toggle(), "Owned mount summons")
	# Isolate one durable foe while retaining its actual brain and physics push.
	var camp: EnemyCamp = world.camps[3]
	foe = camp.pack.members[0]
	player.global_position = foe.global_position + Vector3(0,0,1.8)
	player.rotation.y = 0
	for member in camp.pack.members:
		if member != foe: member.global_position += Vector3(7,0,-5)
	foe.health.maximum = 1000
	foe.health.current = 1000
	await frames(3)
	check(not camp.pack.has_target(), "Tier one group waits until provoked")
	var initial_hp := foe.health.current
	# Synthetic physical Space verifies the actual gameplay binding.
	var key := InputEventKey.new()
	key.physical_keycode = KEY_SPACE
	key.pressed = true
	Input.parse_input_event(key)
	await frames(1)
	check(player.combat.is_attacking() and player.mounts.mounted and is_equal_approx(player.combat.swing_speed, player.stats.value(&"attack_speed")*1.35), "Space attacks from mount at 35 percent faster speed")
	# Toggle the new auto mode off, then finish this committed strike.
	key.pressed = false
	Input.parse_input_event(key)
	await frames(1)
	key.pressed = true
	Input.parse_input_event(key)
	await frames(1)
	key.pressed = false
	Input.parse_input_event(key)
	while player.combat.is_attacking(): await frames(1)
	check(foe.health.current < initial_hp and camp.pack.target == player, "Mounted strike damages and alerts whole group")
	check(hud.target_hp.visible and hud.target_hp.size.x >= 400 and hud.target_label.text.contains("Lv.1"), "Combat automatically displays large top-center target health")
	var before_second := foe.health.current
	player.combat.request_attack()
	for i in 60:
		await frames(1)
		if foe.health.current < before_second: break
	await frames(14)
	check(foe.health.current < before_second and foe.global_position.distance_to(player.global_position) > player.combat.attack.reach, "Second consecutive mounted hit knocks foe beyond melee range")
	check(player.mounts.mounted, "Taking damage during mounted combat keeps rider mounted")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/expansion_combat.png")
	world.respawn_player()
	await frames(5)
	player.progression.award_xp(500)
	var save := ProgressionSave.new()
	save.path = "user://first_map_expansion_test.json"
	check(save.save_player(player), "Save accepts XP above the old level-one threshold")
	player.progression.xp = 0
	check(save.load_player(player) and player.progression.xp == 500 and player.progression.level == 1, "New slower progression round-trips through save validation")
	if DisplayServer.get_name() != "headless":
		player.position = Vector3(0,0,40)
		await frames(10)
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/expansion_village.png")
	world.queue_free()
	await frames(2)
	print("First-map expansion complete: %d failures" % failures)
	quit(1 if failures else 0)
