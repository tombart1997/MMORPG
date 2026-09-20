extends "res://tests/mmorpg_loop.gd"
var kit: PlayerSkills
var abilities: Array[SkillData]
var controller: PlayerController
var target: ActorBody
var second: ActorBody
var used: Dictionary = {}
var damage_taken: float = 0
func settle() -> void:
	for i in 100:
		await frames(1)
		if not kit.busy() and not player.combat.is_attacking(): return
func cast(index: int, victim: ActorBody = null, point: Vector3 = Vector3.ZERO) -> bool:
	var accepted := kit.request(abilities[index], victim, point)
	if accepted:
		await frames(6)
		check(player.visual.sampled_clip == abilities[index].animation, abilities[index].display_name + " samples its authored skill pose")
		await capture("turnwarden_pose_%d" % index)
		await settle()
	return accepted
func fresh_world() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(8)
	player = world.player
	kit = player.skills
	abilities = kit.specialization.skills
	for child in player.get_children():
		if child is PlayerController: controller = child
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	player.health.damaged.connect(func(amount, _source): damage_taken += amount)
	kit.resolved.connect(func(context): used[String(context.skill.id)] = true)
func _run() -> void:
	await fresh_world()
	check(abilities.size() == 6 and kit.specialization.class_id == &"ironvow", "One complete six-skill specialization selected; no unfinished kits")
	for skill in abilities:
		check(skill.icon != null and player.visual.animation_player.has_animation(skill.animation) and not skill.effects.is_empty(), skill.display_name + " has authored effects, icon and imported animation")
	var bar: SkillBar
	for control in hud.get_child(0).get_children():
		if control is SkillBar: bar = control
	await frames(3)
	player.navigation.command(Vector3(0, 0, 7))
	await mouse(bar.buttons[1].get_global_rect().get_center(), true)
	await mouse(bar.buttons[1].get_global_rect().get_center(), false)
	check(kit.remaining(abilities[1]) > 0 and not player.navigation.active, "Mouse action-bar activation is consumed by UI and starts guard")
	await settle()
	kit.cancel_transient()
	kit.cooldowns.clear()
	var key := InputEventKey.new()
	key.physical_keycode = KEY_2
	key.pressed = true
	Input.parse_input_event(key)
	await frames(2)
	check(kit.busy(), "Numeric hotkey submits the same skill request")
	key = key.duplicate()
	key.pressed = false
	Input.parse_input_event(key)
	await settle()
	kit.cancel_transient()
	kit.cooldowns.clear()
	await frames(3)
	await mouse(bar.buttons[4].get_global_rect().get_center(), true)
	await mouse(bar.buttons[4].get_global_rect().get_center(), false)
	check(kit.armed == abilities[4], "Mouse button arms ground targeting")
	await mouse(Vector2(80, 80), true)
	await mouse(Vector2(80, 80), false)
	check(kit.armed == abilities[4] and not kit.busy(), "HUD clicks cannot confirm a ground-targeted skill")
	var ground_point := player.world_interaction.camera.unproject_position(player.position + Vector3(0, 0, -3))
	await mouse(ground_point, true)
	await mouse(ground_point, false)
	check(kit.busy() and kit.armed == null and not player.navigation.active, "World placement click casts instead of issuing movement")
	await settle()
	kit.cancel_transient()
	kit.cooldowns.clear()
	await frames(2)
	check(not kit.request(abilities[0]) and kit.remaining(abilities[0]) == 0, "Missing target rejects without cooldown")
	target = world.camps[0].pack.members[0]
	check(not kit.request(abilities[0], target) and kit.remaining(abilities[0]) == 0, "Out-of-range target rejects without walking or spending cooldown")
	for camp in world.camps:
		camp.set_physics_process(false)
		for enemy in camp.pack.members:
			for child in enemy.get_children():
				if child is EnemyBrain: child.set_physics_process(false)
	controller.set_physics_process(false)
	player.position = ZoneTerrain.CAMPS[0] + Vector3(0, 0, 3)
	player.rotation.y = 0
	target.global_position = player.position + Vector3(0, 0, -2)
	target.health.maximum = 1000
	target.health.current = 1000
	second = world.camps[0].pack.members[1]
	second.global_position = player.position + Vector3(0.7, 0, -2)
	second.health.maximum = 1000
	second.health.current = 1000
	check(kit.request(abilities[0], target), "Riving Stroke accepts a living target within range")
	check(not kit.request(abilities[1]) and not player.combat.request_attack(), "Rapid skill and basic input cannot overlap commitment")
	check(not player.equipment.unequip(&"weapon"), "Equipment cannot change under a committed skill")
	await frames(8)
	check(target.health.current == 1000 and player.visual.sampled_clip == &"attack_01", "Skill windup uses animation without premature damage")
	await capture("turnwarden_riving_windup")
	await settle()
	check(is_equal_approx(target.health.current, 977.5) and second.health.current < 1000 and target.statuses.has(&"open"), "Selected target drives an actual multi-target opening arc")
	var hp := target.health.current
	player.combat.request_attack()
	check(not kit.request(abilities[1]), "Skill pressed during basic commitment rejects without interruption")
	await settle()
	check(is_equal_approx(hp - target.health.current, 31.25), "Open improves actual basic damage by 25 percent")
	player.combat.cancel()
	player.health.current = 100
	check(await cast(1), "Held Line enters a bounded guard window")
	var front := target.global_position
	target.global_position = player.position + Vector3(0, 0, 2)
	player.health.apply_damage(10, target)
	check(player.health.current == 90 and player.statuses.has(&"guard"), "Rear damage bypasses frontal guard")
	target.global_position = front
	player.health.apply_damage(10, target)
	check(is_equal_approx(player.health.current, 86) and player.statuses.has(&"answer") and not player.statuses.has(&"guard"), "One guarded hit deals reduced damage and earns one Answer")
	await capture("turnwarden_answer")
	hp = target.health.current
	var second_hp := second.health.current
	check(kit.request(abilities[5], target), "Due Return accepts the chosen counter target")
	player.world_interaction.command({"kind": &"enemy", "target": second, "position": second.global_position})
	await settle()
	check(is_equal_approx(hp - target.health.current, 45) and second.health.current == second_hp, "Target changes during windup do not redirect single-target counter")
	check(is_equal_approx(player.health.current, 101) and not player.statuses.has(&"answer"), "Answer counter heals only after a real hit and consumes the opportunity")
	player.statuses.add(&"answer", 5)
	target.statuses.add(&"open", 4, 1, player)
	second.statuses.add(&"open", 4, 1, player)
	hp = target.health.current
	check(await cast(3), "Gate Sweep resolves its broad arc")
	check(is_equal_approx(hp - target.health.current, 35) and not target.statuses.has(&"open") and target.statuses.has(&"slow") and target.statuses.push_remaining > 0, "Sweep consumes Open and Answer for real damage, slow and push")
	await capture("turnwarden_sweep")
	check(await cast(4, null, player.position), "Ground skill creates a persistent Standard")
	check(get_nodes_in_group("skill_areas").size() == 1 and player.statuses.has(&"shelter") and target.statuses.has(&"zone_slow"), "Persistent area applies reusable friendly and hostile effects")
	hp = player.health.current
	player.health.apply_damage(10, target)
	check(is_equal_approx(hp - player.health.current, 8), "Standard changes incoming damage without invulnerability")
	check(is_equal_approx(target.statuses.movement_multiplier(), .65), "Overlapping slows use strongest rather than multiplying")
	await capture("turnwarden_standard")
	controller.set_physics_process(true)
	var start := player.position
	check(kit.request(abilities[2], null, start + Vector3(3, 0, 0)), "Heelturn accepts nearby navigable ground")
	await settle()
	check(player.position.distance_to(start) > 2.4 and player.position.distance_to(start) < 3.5, "Heelturn moves the body through physics instead of teleporting")
	check(get_nodes_in_group("skill_areas").size() == 2, "Heelturn leaves a separate short-lived slow patch")
	controller.set_physics_process(false)
	await frames(310)
	check(get_nodes_in_group("skill_areas").is_empty() and not player.statuses.has(&"shelter") and not target.statuses.has(&"slow"), "Areas and statuses expire, preventing permanent control")
	player.position = start
	kit.cooldowns.clear()
	var wall := StaticBody3D.new()
	wall.collision_layer = 1
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(3, 3, .3)
	shape.shape = box
	wall.add_child(shape)
	world.add_child(wall)
	wall.global_position = player.position + Vector3(0, 1, -1)
	await frames(2)
	check(not kit.request(abilities[0], second) and kit.remaining(abilities[0]) == 0, "Static obstacles reject a targeted skill without cooldown cost")
	check(not kit.request(abilities[2], null, player.position + Vector3(0, 0, -3)), "Heelturn cannot cross an obstructed lane")
	wall.queue_free()
	await frames(2)
	controller.set_physics_process(true)
	check(kit.request(abilities[0], second), "Skill accepts after obstruction is removed")
	var committed_position := player.position
	Input.action_press("move_back")
	player.health.apply_damage(2, second)
	await frames(5)
	Input.action_release("move_back")
	check(kit.busy() and player.position.distance_to(committed_position) < .05, "Ordinary damage and held movement cannot cancel or steer committed skill")
	await settle()
	controller.set_physics_process(false)
	player.position = start
	kit.cooldowns.clear() # Isolated failure-case fixture; gameplay never clears cooldowns this way.
	player.statuses.add(&"answer", 5)
	hp = player.health.current
	kit.request(abilities[5], target)
	target.health.apply_damage(10000, null)
	await settle()
	check(player.health.current == hp and kit.last_hits == 0 and kit.remaining(abilities[5]) > 0, "Target dying in windup produces a miss with no heal or cooldown refund")
	kit.cooldowns.clear()
	player.world_interaction.selected_enemy = second
	check(kit.activate(4) and kit.armed == abilities[4], "Ground activation arms a cursor placement instead of casting immediately")
	hud.inventory_panel.set_open(true)
	check(kit.armed == null and not kit.activate(1), "Inventory cancels targeting and prevents skill activation")
	player.ui_session.close()
	kit.request(abilities[0], second)
	player.health.apply_damage(10000, null)
	await frames(2)
	check(not kit.busy() and player.statuses.entries.is_empty(), "Death cancels skill commitment and transient opportunities")
	world.respawn_player()
	await frames(2)
	check(kit.remaining(abilities[0]) > 0, "Respawn does not reset accepted skill cooldowns")
	var save := ProgressionSave.new()
	save.path = "user://skill_test.json"
	check(save.save_player(player), "Save writes class, specialization, ranks and cooldown remainder")
	var snapshot: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(save.path))
	var invalid: Dictionary = snapshot.duplicate(true)
	invalid.skills.specialization = "unfinished"
	check(not save.apply_snapshot(player, invalid), "Unimplemented specialization cannot load into an empty or invalid kit")
	kit.cooldowns.clear()
	check(save.load_player(player) and kit.specialization.id == &"turnwarden" and kit.remaining(abilities[0]) > 0, "Reload restores specialization and prevents cooldown reset exploit")
	for version in [1, 2]:
		var old: Dictionary = snapshot.duplicate(true)
		old.version = version
		old.erase("skills")
		check(save.apply_snapshot(player, old) and kit.specialization.skills.size() == 6, "Older save migrates to playable reference kit: v%d" % version)
	DirAccess.remove_absolute(save.path)
	DirAccess.remove_absolute(save.path + ".bak")
	world.queue_free()
	await frames(3)
	await fresh_world()
	await live_encounters()
	world.queue_free()
	await frames(3)
	print("Turnwarden combat complete: %d failures" % failures)
	quit(1 if failures else 0)

func live_encounters() -> void:
	# Real AI, collision, skill cooldowns and basic attacks in actual Briarwood camps.
	for camp_index in [0, 2]:
		var camp: EnemyCamp = world.camps[camp_index]
		if camp_index == 2:
			player.inventory.add_item(ItemCatalog.get_item(&"briarsteel_edge"))
			player.inventory.add_item(ItemCatalog.get_item(&"briarhide_coat"))
			player.equipment.equip(find_item(&"briarsteel_edge"))
			player.equipment.equip(find_item(&"briarhide_coat"))
			# Actual Smith service upgrades the same equipped sword later used in combat.
			world.respawn_player()
			var smith: WorldNPC = world.settlement.npcs[3]
			player.position = smith.global_position + Vector3(1, 0, 0)
			player.equipment.unequip(&"weapon")
			var index := find_item(&"briarsteel_edge")
			player.inventory.gold += 15
			player.inventory.add_item(ItemCatalog.get_item(&"moss_shard"))
			check(UpgradeService.new().attempt(player, smith, index, player.inventory.slots[index]).get("success", false), "Smith service upgrades weapon used by the live skill kit")
			player.equipment.equip(index)
			check(player.stats.value(&"attack") == 35, "Smith upgrade and level bonuses feed skill scaling through authoritative Attack")
		player.position = camp.position + Vector3(0, 0, 3)
		player.rotation.y = 0
		kit.request(abilities[4], null, camp.position)
		await settle()
		damage_taken = 0
		var skills_used := 0
		var basics_used := 0
		for frame in 2400:
			await frames(1)
			if camp.pack.living_count() == 0 or not player.health.is_alive(): break
			if kit.busy() or player.combat.is_attacking(): continue
			var victim: ActorBody
			var distance := INF
			for enemy in camp.pack.members:
				if enemy.health.is_alive() and enemy.global_position.distance_to(player.position) < distance:
					victim = enemy
					distance = enemy.global_position.distance_to(player.position)
			if victim == null: break
			var direction := victim.global_position - player.position
			player.rotation.y = atan2(-direction.x, -direction.z)
			player.world_interaction.selected_enemy = victim
			if distance > 2.4:
				player.navigation.command(victim.global_position)
				continue
			player.navigation.cancel()
			var accepted := false
			if victim.combat.phase == MeleeCombat.Phase.WINDUP and kit.remaining(abilities[1]) <= 0:
				accepted = kit.request(abilities[1])
			elif player.statuses.has(&"answer") and kit.remaining(abilities[5]) <= 0:
				accepted = kit.request(abilities[5], victim)
			elif not victim.statuses.has(&"open") and kit.remaining(abilities[0]) <= 0:
				accepted = kit.request(abilities[0], victim)
			elif victim.statuses.has(&"open") and kit.remaining(abilities[3]) <= 0 and camp.pack.living_count() > 1:
				accepted = kit.request(abilities[3])
			if accepted: skills_used += 1
			elif player.combat.request_attack(): basics_used += 1
		check(camp.pack.living_count() == 0 and player.health.is_alive(), "Live Turnwarden clears %s without deleting combat risk" % camp.camp_name)
		check(skills_used > 0 and basics_used > 0, "Live encounter uses both skills and relevant basic attacks")
		print("BALANCE %s: %.1f damage taken, %d skill casts, %d basic attacks" % [camp.camp_name, damage_taken, skills_used, basics_used])
		check(damage_taken > 10, "Live group still inflicts meaningful damage, including before level-up healing")
		await capture("turnwarden_live_%d" % camp_index)
		player.world_interaction.cancel()
		for drop in get_nodes_in_group("loot"):
			player.position = drop.global_position
			drop.collect(player)
		await frames(2)
	check(player.progression.kills == 8 and player.inventory.count(&"moss_shard") > 0, "Skill kills integrate with original XP, enemy drops and inventory")
