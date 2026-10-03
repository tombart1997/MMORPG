extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(4)
	world.set_physics_process(false)
	var player: ActorBody = world.player
	for actor in get_nodes_in_group("players") + get_nodes_in_group("enemies"):
		for child in actor.get_children():
			if child is PlayerController or child is EnemyBrain: child.set_physics_process(false)
	var bag := player.inventory
	var equipment := player.equipment
	var shard := ItemCatalog.get_item(&"moss_shard")
	check(bag.add_item(shard, 45) and bag.count(shard.id) == 45, "Stack overflow splits into bounded slots")
	check(bag.slots[1].quantity == 20 and bag.slots[3].quantity == 5, "Stack sizes respect authored maximum")
	var enemy: ActorBody = world.camps[0].pack.members[0]
	enemy.health.current = 75
	enemy.health.maximum = 75
	# Keep this focused item-stat regression deterministic; reward bands are tested separately.
	world.camps[0].drop_table = load("res://data/drops/mossling.tres")
	world.camps[0].leader_reward = ItemCatalog.get_item(&"briarsteel_edge")
	player.position = Vector3(0, 0, 2)
	player.rotation.y = 0
	enemy.global_position = Vector3(0, 0, 0)
	player.combat.request_attack()
	while player.combat.is_attacking(): await frames(1)
	var starter_damage := 75.0 - enemy.health.current
	check(starter_damage == 25, "Starter equipment preserves actual melee damage")
	player.combat.cancel()
	bag.add_item(ItemCatalog.get_item(&"briarsteel_edge"))
	var sword_slot := find_item(bag, &"briarsteel_edge")
	check(equipment.equip(sword_slot), "Equip sword through inventory command")
	check(player.stats.value(&"attack") == 33, "Base and weapon attack compose authoritatively")
	check(player.visual.sockets[&"WeaponSocket"].get_node("Equipment").scene_file_path == ItemCatalog.get_item(&"briarsteel_edge").visual.resource_path, "Equipped item selects its authored weapon scene on rig socket")
	enemy.health.current = 75
	player.position = Vector3(0, 0, 2)
	enemy.global_position = Vector3(0, 0, 0)
	player.combat.request_attack()
	check(not equipment.unequip(&"weapon"), "Cannot replace attack set mid-swing")
	while player.combat.is_attacking(): await frames(1)
	check(75 - enemy.health.current == 33, "Better sword changes real cone-hit damage")
	player.combat.cancel()
	bag.add_item(ItemCatalog.get_item(&"briarhide_coat"))
	player.health.current = 100
	check(equipment.equip(find_item(bag, &"briarhide_coat")), "Equip armor")
	check(player.health.maximum == 185 and player.health.current == 100, "Max HP increase preserves current HP")
	player.health.apply_damage(8, enemy)
	check(player.health.current == 95, "Armor defense reduces incoming physical damage")
	player.health.current = 180
	check(equipment.unequip(&"chest") and player.health.current == 160, "Removing HP equipment clamps current HP")
	player.health.current = 100
	player.health.apply_damage(8, enemy)
	check(player.health.current == 92, "Removing defense changes actual damage")
	var tonic_count := bag.count(&"field_tonic")
	check(bag.use_item(ItemCatalog.get_item(&"field_tonic"), player.health) and player.health.current == 137 and bag.count(&"field_tonic") == tonic_count - 1, "Consumable heals and decrements stack")
	player.health.current = player.health.maximum
	check(not bag.use_item(ItemCatalog.get_item(&"field_tonic"), player.health), "Full-health use does not waste tonic")
	# Deterministic authored drop table boundaries and actual enemy reward hook.
	var table := DropTable.new()
	var entry := DropEntry.new()
	entry.item = shard
	entry.minimum = 2
	entry.maximum = 4
	table.entries.append(entry)
	var never := DropEntry.new()
	never.item = shard
	never.chance = 0
	table.entries.append(never)
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	for i in 20:
		var rolled := table.roll(rng)
		check(rolled.size() == 1 and rolled[0].quantity >= 2 and rolled[0].quantity <= 4, "Drop chance and quantity bounds")
	enemy.health.apply_damage(1000, player)
	var drop: LootPickup = get_nodes_in_group("loot")[0]
	player.global_position = drop.global_position
	var before_gold := bag.gold
	check(drop.collect(player) and not drop.collect(player), "Actual Mossling reward enters bag exactly once")
	for entry_drop in get_nodes_in_group("loot"):
		if entry_drop.claimed: continue
		player.global_position = entry_drop.global_position
		entry_drop.collect(player)
	check(bag.gold > before_gold and bag.count(&"briarsteel_edge") >= 1, "Reward includes currency and guaranteed first-camp upgrade")
	await frames(2)
	while bag.slots.has(null): bag.add_item(ItemCatalog.get_item(&"cairn_cap"))
	var full_drop := LootPickup.new()
	full_drop.item = ItemCatalog.get_item(&"cairnwarden_sword")
	full_drop.coins = 10
	world.add_child(full_drop)
	full_drop.global_position = player.global_position
	before_gold = bag.gold
	check(not full_drop.collect(player) and not full_drop.claimed and bag.gold == before_gold, "Full bag leaves complete bundle and gold unclaimed")
	check(not equipment.unequip(&"weapon"), "Full inventory safely rejects unequip")
	sword_slot = find_item(bag, &"wayfarer_blade")
	check(equipment.equip(sword_slot), "Full bag supports equipment swap in the vacated slot")
	bag.slots[23] = null
	check(full_drop.collect(player), "Pickup succeeds after capacity is freed")
	await frames(2)
	player.combat.cancel()
	check(equipment.equip(find_item(bag, &"cairnwarden_sword")), "Fast sword can equip")
	player.combat.request_attack()
	check(is_equal_approx(player.combat.swing_speed, 1.1), "Attack speed snapshots from equipment")
	player.combat.set_physics_process(false)
	player.combat._physics_process(0.1)
	check(is_equal_approx(player.combat.phase_elapsed, 0.11), "Attack speed advances actual combat phase timing")
	player.combat.cancel()
	player.combat.set_physics_process(true)
	equipment.equip(find_item(bag, &"wayfarer_blade"))
	bag.slots[23] = ItemStack.new(&"pathrunner_boots")
	equipment.equip(23)
	check(is_equal_approx(player.stats.value(&"movement_speed"), 6.0), "Boots recalculate movement speed")
	var controller: PlayerController
	for child in player.get_children():
		if child is PlayerController: controller = child
	Input.action_press("move_forward")
	controller._physics_process(1.0 / 60.0)
	Input.action_release("move_forward")
	check(is_equal_approx(Vector2(player.velocity.x, player.velocity.z).length(), 6.0), "Controller uses calculated movement speed")
	# Versioned round trip, properties, validation and backup recovery.
	var persistence := ProgressionSave.new()
	persistence.path = "user://rpg_test.json"
	bag.slots[0].properties = {"test_marker": "retained"}
	player.progression.award_xp(player.progression.xp_required())
	var saved_gold := bag.gold
	check(persistence.save_player(player), "Save complete progression snapshot")
	bag.gold = 0
	player.progression.level = 1
	check(persistence.load_player(player) and bag.gold == saved_gold and player.progression.level == 2, "Load restores currency and level")
	check(bag.slots[0].properties.get("test_marker") == "retained" and equipment.slots[&"weapon"].id == &"wayfarer_blade", "Load preserves instances and equipped items")
	check(not persistence.apply_snapshot(player, {"version": 999}) and bag.gold == saved_gold, "Unsupported snapshot rejected without state mutation")
	var fresh := ActorBody.new()
	world.add_child(fresh)
	fresh.progression = PlayerProgression.new()
	fresh.add_child(fresh.progression)
	fresh.inventory = PlayerInventory.new()
	fresh.add_child(fresh.inventory)
	fresh.equipment = PlayerEquipment.new()
	fresh.equipment.actor = fresh
	fresh.add_child(fresh.equipment)
	fresh.stats = CharacterStats.new()
	fresh.stats.actor = fresh
	fresh.add_child(fresh.stats)
	check(persistence.load_player(fresh) and fresh.inventory.gold == saved_gold and fresh.equipment.slots[&"feet"].id == &"pathrunner_boots", "Fresh character composition restores saved equipment and progression")
	fresh.queue_free()
	await frames(2)
	check(persistence.save_player(player), "Second save retains backup")
	var file := FileAccess.open(persistence.path, FileAccess.WRITE)
	file.store_string("broken json")
	file.close()
	check(persistence.load_player(player), "Corrupt primary recovers validated backup")
	player.health.apply_damage(10000, null)
	check(not equipment.equip(0) and not bag.use_slot(0, player.health), "Dead player cannot equip or consume")
	player.stats.recalculate()
	check(player.health.current == 0, "Stat recalculation cannot resurrect")
	world.respawn_player()
	check(player.health.current == player.health.maximum and bag.gold == saved_gold, "Respawn retains inventory and calculated stats")
	bag.slots[23] = null
	check(equipment.unequip(&"weapon"), "Unequip weapon")
	check(player.visual.sockets[&"WeaponSocket"].get_node_or_null("Equipment") == null and not player.combat.request_attack(), "Empty weapon slot removes visual and disables sword attacks")
	check(equipment.equip(23), "Re-equip restores sword")
	var hud: ZoneHUD
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	var ui := hud.inventory_panel
	var key := InputEventKey.new()
	key.physical_keycode = KEY_I
	key.pressed = true
	Input.parse_input_event(key)
	await frames(2)
	check(ui.visible and player.ui_open and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "I opens inventory and releases cursor")
	if DisplayServer.get_name() == "headless":
		ui.select_slot(find_item(bag, &"cairn_cap"))
	var button := ui.bag_buttons[find_item(bag, &"cairn_cap")]
	var mouse := InputEventMouseButton.new()
	mouse.position = button.get_global_rect().get_center()
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.pressed = true
	Input.parse_input_event(mouse)
	mouse = mouse.duplicate()
	mouse.pressed = false
	Input.parse_input_event(mouse)
	await frames(2)
	check(ui.details.text.contains("Cairn Cap") and ui.action.text == "Equip", "Inventory selection displays details and equipment action")
	check(ui.bag_buttons[0].tooltip_text.contains("Restores") and ui.gear_buttons[&"weapon"].tooltip_text.contains("Attack"), "Bag and equipment expose authored tooltips")
	ui.action.pressed.emit()
	check(equipment.slots[&"head"] != null, "UI equip button invokes gameplay equipment")
	ui.select_slot(0)
	player.health.current = 50
	var before_use := bag.count(&"field_tonic")
	ui.action.pressed.emit()
	check(player.health.current == 95 and bag.count(&"field_tonic") == before_use - 1, "UI Use button consumes and heals")
	ui.select_slot(find_item(bag, &"cairn_cap"))
	var discard_index := ui.selected
	ui.discard.pressed.emit()
	check(bag.slots[discard_index] != null, "Discard requires explicit second click")
	ui.discard.pressed.emit()
	check(bag.slots[discard_index] == null, "Confirmed discard frees capacity")
	ui.select_gear(&"head")
	check(ui.action.text == "Unequip", "Equipment UI offers unequip")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/rpg_inventory.png")
		var hover := InputEventMouseMotion.new()
		hover.position = ui.gear_buttons[&"weapon"].get_global_rect().get_center()
		Input.parse_input_event(hover)
		await frames(60)
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/rpg_tooltip.png")
	Input.parse_input_event(key)
	await frames(2)
	check(not ui.visible and not player.ui_open, "I closes inventory")
	DirAccess.remove_absolute(persistence.path)
	DirAccess.remove_absolute(persistence.path + ".bak")
	world.queue_free()
	await frames(2)
	print("RPG progression complete: %d failures" % failures)
	quit(1 if failures else 0)

func find_item(bag: PlayerInventory, id: StringName) -> int:
	for i in bag.slots.size():
		if bag.slots[i] and bag.slots[i].id == id: return i
	return -1
