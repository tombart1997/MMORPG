extends "res://tests/combat_smoke.gd"
var world: Node3D
var player: ActorBody
var hud: ZoneHUD

func find_item(id: StringName) -> int:
	for i in player.inventory.slots.size():
		if player.inventory.slots[i] and player.inventory.slots[i].id == id: return i
	return -1

func key(code: Key) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	Input.parse_input_event(event)

func capture(name: String) -> void:
	await frames(3)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/" + name + ".png")

func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(5)
	player = world.player
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	var bag := player.inventory
	var shop := hud.town_panel
	var merchant: WorldNPC = world.settlement.npcs[0]
	var warden: WorldNPC = world.settlement.npcs[1]
	var service := MerchantService.new()
	check(bag.gold == 20 and SafeArea.protects(player), "New traveler starts in settlement sanctuary with 20 gold")
	check(world.settlement.npcs.size() == 9 and merchant.data.shop.offers.size() == 6, "Settlement has nine NPCs and original supplies including mount bridle")
	await capture("settlement")
	var prohibited_camp := EnemyCamp.new()
	prohibited_camp.position = ZoneTerrain.START
	world.add_child(prohibited_camp)
	check(prohibited_camp.pack.living_count() == 0, "Sanctuary refuses hostile camp spawning")
	prohibited_camp.queue_free()
	player.position = warden.global_position + Vector3(0, 0, 1.3)
	await frames(3)
	check(world.interaction.nearest_npc() == warden, "Interaction selects nearest eligible NPC")
	var duplicate := WorldNPC.new()
	duplicate.data = warden.data.duplicate()
	duplicate.data.id = &"zz_warden"
	duplicate.position = warden.position
	world.settlement.add_child(duplicate)
	check(world.interaction.nearest_npc() == warden, "Equal-distance NPC interaction resolves by stable ID")
	duplicate.queue_free()
	key(KEY_E)
	await frames(2)
	check(shop.visible and shop.dialogue_box.visible and player.ui_open, "E opens NPC dialogue")
	check(shop.dialogue_text.text == warden.data.pages[0].text, "Dialogue shows authored opening page")
	shop.choose_response(0)
	check(shop.dialogue_text.text.contains("ironbacks") and shop.dialogue.options().size() == 1, "Dialogue pages and level-conditioned responses work")
	await capture("dialogue")
	key(KEY_ESCAPE)
	await frames(2)
	check(not shop.visible and not player.ui_open and not player.combat.is_attacking(), "Escape closes dialogue without an attack")
	if DisplayServer.get_name() != "headless":
		key(KEY_ESCAPE)
		await frames(2)
		await click_at(Vector2(1100, 650))
		check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE and not player.combat.is_attacking(), "Terrain click after dialogue preserves cursor without attacking")
	player.world_interaction.cancel()
	player.position = merchant.global_position + Vector3(1.0, 0, 0)
	await frames(3)
	key(KEY_E)
	await frames(2)
	check(shop.visible and shop.shop_box.visible, "Merchant interaction opens shop directly")
	shop.select_offer(0)
	if DisplayServer.get_name() != "headless":
		await click_at(shop.stock_list.get_global_rect().position + Vector2(90, 12))
	check(shop.info.text.contains("Attack +4.0"), "Shop compares merchant sword against equipped starter")
	var gold_before := bag.gold
	if DisplayServer.get_name() != "headless": await click_at(shop.trade.get_global_rect().get_center())
	else: shop.transact()
	check(not player.combat.is_attacking(), "Shop mouse clicks never initiate combat")
	check(bag.gold == gold_before and find_item(&"marchguard_sword") == -1 and shop.feedback.text.contains("Not enough gold"), "Insufficient gold rejects purchase without mutation")
	key(KEY_I)
	await frames(2)
	check(hud.inventory_panel.visible and not shop.visible and player.ui_open, "Inventory replaces shop without competing mouse capture")
	key(KEY_I)
	await frames(2)
	check(not player.ui_open and (DisplayServer.get_name() == "headless" or Input.mouse_mode == Input.MOUSE_MODE_VISIBLE), "Closing inventory returns to gameplay")
	# Complete first hunt using real movement/combat, then return and trade earned rewards.
	var camp: EnemyCamp = world.camps[0]
	player.position = camp.position + Vector3(0, 0, 2.1)
	player.rotation.y = 0
	var swings := 0
	while camp.pack.living_count() > 0 and player.health.is_alive() and swings < 8:
		player.combat.request_attack()
		while player.combat.is_attacking(): await frames(1)
		swings += 1
	check(camp.pack.living_count() == 0 and player.progression.xp == 60, "Starter gear can clear weak group through real combat")
	for drop in get_nodes_in_group("loot"):
		player.global_position = drop.global_position
		check(drop.collect(player), "Hunt reward picked up into inventory")
	await frames(2)
	check(bag.gold >= 32 and bag.gold <= 38, "Weak group pays authored gold range")
	player.position = merchant.global_position + Vector3(1, 0, 0)
	await frames(3)
	key(KEY_E)
	await frames(2)
	var shard_slot := find_item(&"moss_shard")
	if shard_slot >= 0:
		var stack := bag.slots[shard_slot]
		var amount := stack.quantity
		gold_before = bag.gold
		check(service.sell(merchant, player, shard_slot, stack, amount).is_empty() and bag.gold == gold_before + amount, "Merchant buys hunt materials for exact sell value")
		check(not service.sell(merchant, player, shard_slot, stack, amount).is_empty(), "Repeated sale cannot duplicate gold")
	# A second short hunt earns the rest of the first sword price.
	player.ui_session.close()
	player.position = ZoneTerrain.START
	camp.remaining = 0
	camp._physics_process(0.1)
	await frames(3)
	player.position = camp.position + Vector3(0, 0, 2.1)
	player.rotation.y = 0
	swings = 0
	while camp.pack.living_count() > 0 and player.health.is_alive() and swings < 8:
		player.combat.request_attack()
		while player.combat.is_attacking(): await frames(1)
		swings += 1
	check(camp.pack.living_count() == 0, "Second hunt repeats the earn-and-return loop")
	for drop in get_nodes_in_group("loot"):
		player.global_position = drop.global_position
		drop.collect(player)
	await frames(2)
	player.position = merchant.global_position + Vector3(1, 0, 0)
	await frames(3)
	key(KEY_E)
	await frames(2)
	shop.select_offer(0)
	gold_before = bag.gold
	shop.transact()
	check(bag.gold == gold_before - 40 and find_item(&"marchguard_sword") >= 0, "Earned gold buys merchant sword and adds actual inventory item")
	await capture("shop")
	key(KEY_I)
	await frames(2)
	var prior_attack := player.stats.value(&"attack")
	hud.inventory_panel.select_slot(find_item(&"marchguard_sword"))
	hud.inventory_panel.activate_selection()
	check(player.stats.value(&"attack") == prior_attack + 4, "Purchased sword equips through inventory and increases calculated Attack")
	key(KEY_I)
	await frames(2)
	# Combat against middle band confirms purchased upgrade and appropriate drops.
	var middle: EnemyCamp = world.camps[1]
	player.global_position = middle.global_position + Vector3(0,0,3)
	middle.update_residency()
	await frames(2)
	check(not middle.dormant and not middle.pack.members.is_empty(), "Approaching the middle camp activates its encounter")
	var target: ActorBody = middle.pack.members[0]
	var middle_visual_scale := target.visual.scale.x
	player.position = target.global_position + Vector3(0, 0, 2.1)
	player.rotation.y = 0
	player.health.current = player.health.maximum
	var hp_before := target.health.current
	player.combat.cancel()
	player.combat.request_attack()
	while player.combat.is_attacking(): await frames(1)
	check(hp_before - target.health.current == player.stats.value(&"attack"), "Purchased Attack affects actual cone-hit damage")
	swings = 0
	while middle.pack.living_count() > 0 and player.health.is_alive() and swings < 10:
		for member in middle.pack.members:
			if member.health.is_alive():
				player.global_position = member.global_position + Vector3(0, 0, 2.1)
				player.rotation.y = 0
				break
		player.combat.request_attack()
		while player.combat.is_attacking(): await frames(1)
		swings += 1
	check(middle.pack.living_count() == 0, "Upgraded traveler can clear middle-band group")
	for drop in get_nodes_in_group("loot"):
		player.global_position = drop.global_position
		drop.collect(player)
	await frames(2)
	check(middle.leader_reward == null, "Middle-band leader no longer guarantees rare equipment")
	player.combat.cancel()
	# Inject a rare result to test equipping without making a probabilistic assertion.
	bag.add_item(ItemCatalog.get_item(&"relic_blade_1"))
	check(player.equipment.equip(find_item(&"relic_blade_1")), "Rare upgrade equips through same architecture")
	var hard: EnemyCamp = world.camps[2]
	# Enter the deep camp's wake radius before inspecting its resident actors.
	player.position = hard.position + Vector3(0,0,2)
	await frames(30)
	check(hard.pack.members[0].health.maximum == 110 and hard.enemy_data.attack.damage == 11 and hard.enemy_data.xp == 40, "Deep band increases HP, damage and rewards modestly")
	check(hard.pack.members[0].visual.scale.x > middle_visual_scale and hard.pack.members[0].visual.sockets[&"ArmorSocket"].get_node_or_null("Equipment") != null, "Ironback visual communicates greater danger")
	check(hard.drop_table.entries.any(func(entry): return entry.item.item_type == "weapon" and entry.chance <= .004), "Ironback has rare weapon loot")
	check(camp.drop_table.entries.filter(func(entry): return entry.item.item_type == "weapon").all(func(entry): return entry.chance <= .004), "Weak enemies do not flood bags with progression weapons")
	# Retreat from a committed enemy into sanctuary must cancel pursuit and damage.
	player.position = hard.position + Vector3(0, 0, 2)
	hard.pack.target = player
	# Keep this actor resident during the sanctuary teleport. Streaming has its
	# own tests; unloading it would invalidate the combat assertions below.
	hard.streaming_enabled = false
	var hunter: ActorBody = hard.pack.members[0]
	# Observe the deep group's actual telegraphed damage before retreating.
	var damage_seen: Array[float] = []
	player.health.damaged.connect(func(amount, _source): damage_seen.append(amount))
	player.health.current = player.health.maximum
	await frames(90)
	check(damage_seen.any(func(amount): return is_equal_approx(amount, 11.0)), "Ironback attacks deal authored stronger damage in live combat")
	await capture("ironbacks")
	hunter.combat.request_attack()
	player.position = ZoneTerrain.START
	await frames(3)
	check(not hard.pack.has_target() and not hunter.combat.is_attacking(), "Entering sanctuary clears hostile pursuit and committed attacks")
	hp_before = player.health.current
	check(not player.health.apply_damage(11, hunter) and player.health.current == hp_before, "Sanctuary blocks late hostile damage")
	check(not hunter.health.apply_damage(30, player), "Sanctuary cannot be used to attack enemies without risk")
	# Buying stacks, selling part of a stack, and full capacity failures.
	player.position = merchant.global_position + Vector3(1, 0, 0)
	await frames(3)
	gold_before = bag.gold
	var tonics := bag.count(&"field_tonic")
	check(service.buy(merchant, player, 4, 2).is_empty() and bag.gold == gold_before - 12 and bag.count(&"field_tonic") == tonics + 2, "Stack purchase deducts quantity times unit price")
	var tonic_index := find_item(&"field_tonic")
	var tonic_stack := bag.slots[tonic_index]
	gold_before = bag.gold
	shop.open_npc(merchant)
	shop.select_sale(shop.bag_indices.find(tonic_index))
	shop.quantity.value = 1
	shop.transact()
	check(bag.gold == gold_before + 1 and tonic_stack.quantity >= 1, "Shop sale action removes partial stack and pays exact value")
	check(not service.buy(merchant, player, 4, -1).is_empty() and not service.sell(merchant, player, tonic_index, tonic_stack, 999).is_empty(), "Invalid transaction quantities rejected")
	while bag.slots.has(null): bag.add_item(ItemCatalog.get_item(&"moss_shard"), 20)
	gold_before = bag.gold
	# Capacity is checked with sufficient funds; restore this temporary test balance afterward.
	bag.gold = 100
	check(service.buy(merchant, player, 0, 1).contains("Inventory full") and bag.gold == 100, "Full inventory rejects purchase atomically")
	bag.gold = gold_before
	var full_stack := bag.slots[23]
	check(service.sell(merchant, player, 23, full_stack, full_stack.quantity).is_empty() and bag.slots[23] == null, "Selling frees a full inventory slot")
	# Persist actual traded/equipped state and verify safe death/respawn.
	var save := ProgressionSave.new()
	save.path = "user://settlement_test.json"
	var expected_gold := bag.gold
	var expected_weapon: StringName = player.equipment.slots[&"weapon"].id
	check(save.save_player(player), "Save after buying, selling and equipping")
	bag.gold = 0
	check(save.load_player(player) and bag.gold == expected_gold and player.equipment.slots[&"weapon"].id == expected_weapon, "Load restores trading outcomes and equipped upgrade")
	shop.open_npc(merchant)
	player.position = hard.position
	hard.update_residency()
	hunter = hard.pack.members[0]
	hard.pack.target = player
	player.health.apply_damage(10000, hunter)
	check(not player.health.is_alive() and not player.ui_open and not hard.pack.has_target(), "Death clears UI and combat targets")
	world.respawn_player()
	await frames(3)
	check(SafeArea.protects(player) and player.health.current == player.health.maximum and bag.gold == expected_gold, "Respawn is safe and preserves gold/items/progression")
	check(player.equipment.slots[&"weapon"].id == expected_weapon, "Death never deletes equipment")
	player.position = Vector3(25, 0, 0)
	check(not service.buy(merchant, player, 4, 1).is_empty(), "Remote merchant commands rejected")
	DirAccess.remove_absolute(save.path)
	DirAccess.remove_absolute(save.path + ".bak")
	world.queue_free()
	await frames(3)
	print("Settlement progression complete: %d failures" % failures)
	quit(1 if failures else 0)

func click_at(point: Vector2) -> void:
	var mouse := InputEventMouseButton.new()
	mouse.position = point
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.pressed = true
	Input.parse_input_event(mouse)
	mouse = mouse.duplicate()
	mouse.pressed = false
	Input.parse_input_event(mouse)
	await frames(2)
