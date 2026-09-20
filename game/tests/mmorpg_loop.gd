extends "res://tests/combat_smoke.gd"
var world: Node3D
var player: ActorBody
var hud: ZoneHUD

func find_item(id: StringName) -> int:
	for i in player.inventory.slots.size():
		if player.inventory.slots[i] and player.inventory.slots[i].id == id: return i
	return -1

func approach(node: Node3D, kind: StringName, limit: int = 1800) -> void:
	player.world_interaction.command({"kind": kind, "target": node, "position": node.global_position})
	for i in limit:
		await frames(1)
		if player.ui_open or not is_instance_valid(node) or node.is_queued_for_deletion(): break
		if node is ActorBody and not node.health.is_alive(): break
		if player.world_interaction.target == null: break

func travel(point: Vector3, limit: int = 2200) -> void:
	player.world_interaction.command({"kind": &"terrain", "position": point, "normal": Vector3.UP})
	for i in limit:
		await frames(1)
		if not player.navigation.active: break

func capture(name: String) -> void:
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/" + name + ".png")

func mouse(point: Vector2, pressed: bool) -> void:
	var hover := InputEventMouseMotion.new()
	hover.position = point
	Input.parse_input_event(hover.xformed_by(root.get_final_transform()))
	await frames(2)
	var event := InputEventMouseButton.new()
	event.position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = pressed
	Input.parse_input_event(event.xformed_by(root.get_final_transform()))
	await frames(2)

func drag_between(from: Control, to: Control) -> void:
	await frames(3)
	var start := from.get_global_rect().get_center()
	var finish := to.get_global_rect().get_center()
	await mouse(start, true)
	for i in 8:
		var motion := InputEventMouseMotion.new()
		motion.position = start.lerp(finish, (i + 1) / 8.0)
		motion.relative = (finish - start) / 8
		motion.button_mask = MOUSE_BUTTON_MASK_LEFT
		Input.parse_input_event(motion.xformed_by(root.get_final_transform()))
		await frames(2)
	await mouse(finish, false)

func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(8)
	player = world.player
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Cursor remains visible during ordinary gameplay")
	check(NavigationServer3D.map_get_iteration_id(player.get_world_3d().navigation_map) > 0, "World collision baked into synchronized Godot navigation")
	await capture("mouse_settlement")
	var camera := player.world_interaction.camera
	var point := camera.unproject_position(Vector3(0, 0, 7))
	check(WorldPicker.pick(camera, point).get("kind") == &"terrain", "Camera ray resolves visible road as terrain")
	await mouse(point, true)
	await mouse(point, false)
	check(player.navigation.active, "Real viewport terrain click starts navigation")
	player.world_interaction.cancel()
	await mouse(Vector2(80, 80), true)
	await mouse(Vector2(80, 80), false)
	check(not player.navigation.active and not player.combat.is_attacking(), "HUD click cannot reach world movement or combat")
	await travel(Vector3(0, 0, 7))
	check(player.position.distance_to(Vector3(0, 0, 7)) < 0.7, "Terrain travel follows navigation and stops naturally")
	# Route across a building must bend around physical geometry.
	player.position = Vector3(-9, 0, 9)
	player.navigation.command(Vector3(-2, 0, 9))
	check(player.navigation.path.size() > 2, "Navigation produces a detour around a settlement building")
	for i in 900:
		await frames(1)
		if not player.navigation.active: break
	check(player.position.distance_to(Vector3(-2, 0, 9)) < 0.8, "Player physically follows obstacle detour without teleporting")
	player.navigation.command(Vector3(0, 0, 4))
	Input.action_press("move_back")
	await frames(3)
	Input.action_release("move_back")
	check(not player.navigation.active, "Keyboard locomotion cancels click destination")
	var warden: WorldNPC = world.settlement.npcs[1]
	var mara: WorldNPC = world.settlement.npcs[0]
	var smith: WorldNPC = world.settlement.npcs[3]
	point = camera.unproject_position(warden.global_position + Vector3.UP)
	check(WorldPicker.pick(camera, point).get("target") == warden, "Camera ray resolves NPC proxy")
	await mouse(point, true)
	await mouse(point, false)
	for i in 400:
		await frames(1)
		if player.ui_open: break
	check(hud.town_panel.visible and warden.can_interact(player), "Click intent approaches NPC and opens dialogue in range")
	check(player.quests.accept(&"welcome", warden), "Introductory quest accepted from its giver")
	player.ui_session.close()
	await approach(mara, &"npc")
	check(hud.town_panel.shop_box.visible, "Merchant uses the same approach interaction")
	player.ui_session.close()
	await approach(warden, &"npc")
	check(player.quests.ready(QuestCatalog.all()[&"welcome"]), "Talk objective advances through NPC interaction")
	check(player.quests.claim(&"welcome", warden).is_empty(), "Introductory quest turns in exactly once")
	var gold := player.inventory.gold
	check(not player.quests.claim(&"welcome", warden).is_empty() and player.inventory.gold == gold, "Repeated quest reward rejected")
	check(player.quests.accept(&"briar_watch", warden), "Prerequisite unlocks hunting quest")
	player.ui_session.close()
	# The winding route is traversed, not teleported, during the actual quest hunt.
	await travel(ZoneTerrain.CAMPS[0] + Vector3(0, 0, 3))
	check(player.position.distance_to(ZoneTerrain.CAMPS[0]) < 4, "Travel unfolds through road bends to first hunting territory")
	var camp: EnemyCamp = world.camps[0]
	for enemy in camp.pack.members:
		if enemy.health.is_alive(): await approach(enemy, &"enemy", 700)
	check(camp.pack.living_count() == 0 and player.health.is_alive(), "Selected enemy focus drives real melee while cleaving the group")
	if not player.health.is_alive(): quit(1); return
	check(player.progression.kills == 3, "Enemy deaths award progression once")
	player.world_interaction.cancel()
	check(get_nodes_in_group("loot").size() >= 6, "Deaths create individually selectable gold and item entries")
	await capture("individual_loot")
	var coin_count := 0
	for loot in get_nodes_in_group("loot"):
		if loot.item == null: coin_count += 1
		elif loot.item.id == &"moss_shard": await approach(loot, &"loot")
	check(player.inventory.count(&"moss_shard") == 3, "Chosen material entries approach and enter inventory individually")
	check(get_nodes_in_group("loot").filter(func(loot): return loot.item == null).size() == coin_count, "Unselected gold remains on ground")
	# Return by navigation; collected materials feed the hunting quest then the forge.
	await approach(warden, &"npc", 2400)
	check(player.quests.ready(QuestCatalog.all()[&"briar_watch"]), "Kill and collection objectives become ready for return")
	check(player.quests.claim(&"briar_watch", warden).is_empty(), "Hunting turn-in consumes materials and grants rewards")
	check(player.quests.accept(&"first_temper", warden), "Smith introduction unlocks after hunting")
	player.ui_session.close()
	await approach(smith, &"npc")
	check(hud.smith_panel.visible, "Clicking Smith approaches and opens forge")
	var bag := player.inventory
	check(player.equipment.unequip(&"weapon"), "Equipment can move back to bag before forging")
	var index := find_item(&"wayfarer_blade")
	var instance := bag.slots[index]
	var payload := {"player": player, "index": index, "equipment": &"", "stack": instance, "quantity": 1}
	check(hud.smith_panel.drop._can_drop_data(Vector2.ZERO, payload), "Smith anvil accepts eligible dragged equipment")
	await drag_between(hud.smith_panel.bag_buttons[index], hud.smith_panel.drop)
	check(hud.smith_panel.details.text.contains("100%") and hud.smith_panel.details.text.contains("15 gold"), "Upgrade confirmation shows authored chance and cost")
	await capture("smith_upgrade")
	gold = bag.gold
	hud.smith_panel.attempt()
	check(instance.upgrade_level() == 1 and bag.gold == gold - 15, "Confirmed upgrade changes instance level and charges exactly once")
	check(player.equipment.equip(index) and player.stats.value(&"attack") == 29, "Upgraded sword bonuses enter authoritative calculated Attack")
	check(player.quests.claim(&"first_temper", smith).is_empty(), "Successful upgrade completes Smith quest")
	# Failure is deterministic in this test, but production uses the service RNG.
	player.equipment.unequip(&"weapon")
	index = find_item(&"wayfarer_blade")
	instance = bag.slots[index]
	bag.add_item(ItemCatalog.get_item(&"moss_shard"), 5)
	var probe := RandomNumberGenerator.new()
	var failure_seed := 0
	for seed_value in 100:
		probe.seed = seed_value
		if probe.randf() >= 0.8: failure_seed = seed_value; break
	hud.smith_panel.service.rng.seed = failure_seed
	gold = bag.gold
	var material_count := bag.count(&"moss_shard")
	var failed := hud.smith_panel.service.attempt(player, smith, index, instance)
	check(not failed.get("success", true) and instance.upgrade_level() == 1 and bag.gold == gold - 30 and bag.count(&"moss_shard") == material_count - 2, "Failed upgrade spends authored costs and retains item and level")
	bag.gold = 0
	check(hud.smith_panel.service.attempt(player, smith, index, instance).has("error") and instance.upgrade_level() == 1, "Insufficient funds cannot alter equipment")
	bag.gold = gold - 30
	instance.properties["upgrade"] = 3
	check(hud.smith_panel.service.quote(instance).is_empty(), "Upgrade cap comes from profile step count")
	instance.properties["upgrade"] = 1
	player.equipment.equip(index)
	player.ui_session.close()
	# Inventory drag/drop services preserve references, split/merge stacks and reject stale payloads.
	hud.inventory_panel.set_open(true)
	bag.add_item(ItemCatalog.get_item(&"moss_shard"), 9)
	var source := find_item(&"moss_shard")
	var destination := bag.slots.find(null)
	var stack := bag.slots[source]
	check(bag.move_slot(source, destination, stack, 4) and bag.slots[destination].quantity == 4, "Stack drag can split a chosen quantity")
	var split := bag.slots[destination]
	check(bag.move_slot(destination, source, split) and bag.slots[destination] == null, "Compatible stack drag merges without loss")
	check(not bag.move_slot(destination, source, split), "Stale drag payload rejected")
	var equipment_button: ItemSlot = hud.inventory_panel.gear_buttons[&"weapon"]
	var gear_payload := {"player": player, "index": -1, "equipment": &"weapon", "stack": player.equipment.slots[&"weapon"], "quantity": 1}
	var slot: ItemSlot = hud.inventory_panel.bag_buttons[destination]
	slot._drop_data(Vector2.ZERO, gear_payload)
	check(player.equipment.slots[&"weapon"] == null and bag.slots[destination] == instance, "Dragging equipped item to bag preserves upgraded instance")
	payload = {"player": player, "index": destination, "equipment": &"", "stack": instance, "quantity": 1}
	equipment_button._drop_data(Vector2.ZERO, payload)
	check(player.equipment.slots[&"weapon"] == instance, "Dragging weapon onto equipment slot equips the same instance")
	var invalid: ItemSlot = hud.inventory_panel.gear_buttons[&"head"]
	check(not invalid._can_drop_data(Vector2.ZERO, payload), "Wrong equipment slot rejects drop")
	await drag_between(equipment_button, slot)
	check(player.equipment.slots[&"weapon"] == null and bag.slots[destination] == instance, "Native GUI drag unequips without loss")
	await drag_between(slot, equipment_button)
	check(player.equipment.slots[&"weapon"] == instance and not player.navigation.active and not player.combat.is_attacking(), "Native GUI equip drag never reaches world controls")
	await capture("inventory_drag")
	var item_count := bag.count(&"cairn_cap")
	while bag.slots.has(null): bag.add_item(ItemCatalog.get_item(&"cairn_cap"))
	var loot := LootPickup.new()
	loot.item = ItemCatalog.get_item(&"marchguard_sword")
	world.add_child(loot)
	loot.global_position = player.global_position + Vector3(0.5, 0, 0)
	check(not loot.collect(player) and not loot.claimed, "Full inventory leaves the selected ground item intact")
	bag.remove_count(&"cairn_cap", bag.count(&"cairn_cap") - item_count)
	check(loot.collect(player), "Individual pickup succeeds after capacity is freed")
	await frames(2)
	# Versioned persistence includes quests and instance upgrades, with v1 migration.
	var save := ProgressionSave.new()
	save.path = "user://mouse_test.json"
	check(save.save_player(player), "Save includes upgrade and quest progression")
	instance.properties.clear()
	player.quests.states.clear()
	var loaded := save.load_player(player)
	check(loaded and player.equipment.slots[&"weapon"].upgrade_level() == 1 and player.quests.status(&"first_temper") == "completed", "Reload restores upgraded gear and completed quests")
	check(player.stats.value(&"attack") == 29, "Reload recalculates upgraded stats")
	var legacy: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(save.path))
	legacy["version"] = 1
	legacy.erase("quests")
	check(save.apply_snapshot(player, legacy) and player.quests.states.is_empty(), "Version 1 saves migrate without quest state")
	check(save.load_player(player), "Current version can restore after migration test")
	DirAccess.remove_absolute(save.path)
	DirAccess.remove_absolute(save.path + ".bak")
	world.queue_free()
	await frames(3)
	print("Mouse-driven MMORPG loop complete: %d failures" % failures)
	quit(1 if failures else 0)
