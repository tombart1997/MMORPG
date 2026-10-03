extends "res://tests/mmorpg_loop.gd"
var encounter: WorldFracture
var damage_taken: float = 0
func fight(victim: ActorBody, limit: int = 2400) -> void:
	player.world_interaction.command({"kind": &"enemy", "target": victim, "position": victim.global_position})
	for frame in limit:
		await frames(1)
		if not player.health.is_alive() or not is_instance_valid(victim) or not victim.health.is_alive(): break
		if frame % 60 == 0 and not player.skills.busy() and not player.combat.is_attacking():
			var nearby: ActorBody
			for foe: ActorBody in get_nodes_in_group("enemies"):
				if foe.health.is_alive() and foe.global_position.distance_to(player.global_position) < 2.7:
					nearby = foe
					break
			if nearby:
				for index in [0, 3, 1, 5]:
					if player.skills.request(player.skills.specialization.skills[index], nearby): break
		if not player.skills.busy() and player.world_interaction.target == null:
			player.world_interaction.command({"kind": &"enemy", "target": victim, "position": victim.global_position})
func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(10)
	player = world.player
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	encounter = player.farming.encounter
	encounter.rng.seed = 924
	check(encounter.body.health.is_alive() and not encounter.active, "Reference fracture begins dormant and attackable")
	check(not SkillTargeting.line_clear(player, player.position, encounter.global_position), "Terrain conceals the fracture from the refuge")
	# A developing farming loadout, using only real level and equipment rules.
	player.progression.level = 6
	player.equipment.slots[&"weapon"] = ItemStack.new(&"cairnwarden_sword")
	player.equipment.slots[&"chest"] = ItemStack.new(&"rootward_jack")
	player.equipment.refresh()
	player.health.heal(player.health.maximum)
	player.health.damaged.connect(func(amount, _source): damage_taken += amount)
	for point in [Vector3(0, 0, -4), Vector3(18, 0, -4), Vector3(18, 0, -20)]: await travel(point)
	check(player.position.distance_to(Vector3(18, 0, -20)) < 1, "Leave settlement and follow the actual road into hostile territory")
	await fight(world.camps[0].pack.members[0])
	check(world.camps[0].pack.living_count() < 3 and player.health.is_alive(), "Ordinary group pull resolves through real cleaves and skills")
	for point in [Vector3(14, 0, -32), Vector3(-6, 0, -32), Vector3(-25, 0, -43), Vector3(-19, 0, -49), Vector3(-8, 0, -46.9)]: await travel(point)
	check(player.position.distance_to(encounter.global_position) < 3, "Branching field route reaches the fracture")
	await capture("farming_discovery")
	await fight(encounter.body, 3600)
	print("FARMING live damage_taken=%.1f waves=%d living_defenders=%d HP=%.1f" % [damage_taken, encounter.next_wave, encounter.living_defenders(), player.health.current])
	check(not encounter.body.health.is_alive() and player.health.is_alive(), "Developing Turnwarden survives and destroys the fracture through real combat")
	check(encounter.next_wave >= 3 and encounter.living_defenders() > 0, "Damage escalates multiple waves; destruction leaves survivors dangerous")
	check(encounter.completions == 1 and encounter.remaining > 0, "Completion pays once and starts authored reappearance timer")
	var loot_count := get_nodes_in_group("loot").size()
	encounter.body.health.apply_damage(1000, player)
	check(get_nodes_in_group("loot").size() == loot_count, "Repeated corpse hits cannot duplicate rewards")
	await capture("farming_completion")
	# Surviving enemies and death/escape are independent from completion loot.
	player.position = ZoneTerrain.START
	await frames(10)
	for camp in encounter.defenders: check(not camp.pack.has_target(), "Sanctuary ends remaining defender pursuit")
	var rare := encounter.create_drop(ItemStack.new(&"wakeglass"), 0, 9)
	player.position = rare.global_position
	for i in PlayerInventory.CAPACITY: player.inventory.slots[i] = ItemStack.new(&"moss_shard", 20)
	check(not rare.collect(player) and not rare.claimed, "Full inventory leaves a rare reward on the ground")
	await frames(8)
	var camera := player.world_interaction.camera
	check(WorldPicker.pick(camera, camera.unproject_position(rare.label.global_position)).get("target") == rare, "Rare world label is a precise selectable click target")
	await capture("farming_rare")
	player.inventory.slots[0] = null
	check(rare.collect(player) and player.inventory.count(&"wakeglass") == 1, "Rare reward enters inventory once capacity is free")
	# Snapshot captures both carried reward and remaining ground loot.
	var save := ProgressionSave.new()
	save.path = "user://farming_test.json"
	var original_ground_rares := 0
	for drop: LootPickup in get_nodes_in_group("loot"):
		if not drop.claimed and drop.item and drop.item.id == &"wakeglass": original_ground_rares += drop.quantity
	check(save.save_player(player), "Save atomically stores encounter cooldown, outstanding loot and inventory")
	check(save.load_player(player), "Version 4 farming snapshot loads")
	await frames(3)
	check(player.inventory.count(&"wakeglass") == 1 and encounter.remaining > 0 and not encounter.body.health.is_alive(), "Reload retains the claimed rare and destroyed state without respawning rewards")
	var ground_rares := 0
	for drop: LootPickup in get_nodes_in_group("loot"):
		if drop.item and drop.item.id == &"wakeglass": ground_rares += drop.quantity
	check(ground_rares == original_ground_rares, "Claimed forced rare is not recreated on load; natural rolls are retained")
	var invalid: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(save.path))
	invalid.farming.cooldown = -1
	check(not save.apply_snapshot(player, invalid), "Invalid encounter state rejects the whole save before mutation")
	world.respawn_player()
	var smith: WorldNPC
	for npc: WorldNPC in get_nodes_in_group("npcs"):
		if npc.data.role == &"smith": smith = npc
	await approach(smith, &"npc")
	player.inventory.slots[1] = ItemStack.new(&"wayfarer_blade")
	var stack: ItemStack = player.inventory.slots[1]
	stack.properties["upgrade"] = 1
	player.inventory.gold = 1000
	var service := UpgradeService.new()
	hud.smith_panel.select_item(1, stack)
	hud.smith_panel.catalyst.button_pressed = true
	await capture("farming_smith_catalyst")
	hud.smith_panel.attempt()
	check(stack.upgrade_level() == 2 and player.inventory.count(&"wakeglass") == 0, "Smith UI consumes one Ember and guarantees an uncertain upgrade")
	check(not service.attempt(player, smith, 1, stack, true).get("success", false), "Missing catalyst cannot grant a second guaranteed upgrade")
	player.ui_session.close()
	# Deterministic lifecycle boundaries, separate from the live fight above.
	encounter.remaining = 0
	encounter.reset_attempt()
	await frames(3)
	player.position = encounter.global_position + Vector3(0, 0, 2)
	encounter.body.health.apply_damage(1, player)
	await frames(4)
	check(encounter.pending.size() == 6 and encounter.living_defenders() == 0, "Activation warns before spawning the first six defenders")
	for point in encounter.pending: check(point.distance_to(player.position) >= 3.5, "Spawn warning avoids the player")
	await frames(90)
	check(encounter.living_defenders() == 6, "First wave materializes after warning")
	var member: ActorBody = encounter.defenders[0].pack.members[0]
	member.health.apply_damage(10000, player)
	check(member.collision_layer == 0 and encounter.body.health.is_alive(), "Defender death removes collision without completing the fracture")
	await frames(310)
	check(not is_instance_valid(member), "Wave corpses clean up independently after five seconds")
	player.position = ZoneTerrain.START
	await frames(740)
	check(not encounter.active and encounter.body.health.current == encounter.body.health.maximum and encounter.defenders.is_empty(), "Running away resets an abandoned attempt without rewards")
	player.position = encounter.global_position + Vector3(0, 0, 2)
	encounter.body.health.apply_damage(1, player)
	player.health.apply_damage(100000, encounter.body)
	await frames(740)
	check(not encounter.active and encounter.defenders.is_empty(), "Player death cancels pending waves and resets abandoned encounter")
	world.respawn_player()
	encounter.remaining = 0.1
	encounter.body.health.current = 0
	await frames(10)
	check(encounter.body.health.is_alive(), "Elapsed cooldown reappears when the player is away")
	check(save.save_player(player) and save.load_player(player), "Continued farming and catalyst outcome survive another save/load")
	await frames(3)
	encounter.set_physics_process(false) # Isolate scaling; live waves tested above.
	encounter.body.health.damage_floor = 0 # Separate raw skill scaling from encounter phase gates.
	player.position = encounter.global_position + Vector3(0, 0, 2)
	player.equipment.slots[&"weapon"] = ItemStack.new(&"wayfarer_blade")
	player.equipment.refresh()
	var skill := player.skills.specialization.skills[0]
	player.skills.cooldowns.clear()
	var before := encounter.body.health.current
	player.skills.request(skill, encounter.body)
	await frames(50)
	var starter_damage := before - encounter.body.health.current
	player.inventory.slots[2] = ItemStack.new(&"wakecleaver")
	check(player.equipment.equip(2), "Rare sword equips through the ordinary inventory command")
	before = encounter.body.health.current
	player.skills.cooldowns.clear()
	player.skills.request(skill, encounter.body)
	await frames(50)
	var rare_damage := before - encounter.body.health.current
	check(rare_damage > starter_damage * 1.5, "Wakecleaver increases actual skill damage and farming throughput")
	print("FARMING scaling Riving starter=%.1f rare=%.1f" % [starter_damage, rare_damage])
	DirAccess.remove_absolute(save.path)
	DirAccess.remove_absolute(save.path + ".bak")
	print("Farming loop complete: %d failures" % failures)
	quit(1 if failures else 0)
