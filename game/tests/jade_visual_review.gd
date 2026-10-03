extends "res://tests/combat_smoke.gd"
## Visual review in the actual map. Movie frames use the real 60 Hz gameplay camera.
var output := "res://.local/jade_review"
var controller: PlayerController

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output + "/" + label + ".png")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var label_index := args.find("--label")
	if label_index >= 0 and label_index + 1 < args.size(): output += "/" + args[label_index + 1]
	DirAccess.make_dir_recursive_absolute(output)
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(8)
	var player: ActorBody = world.player
	for child in player.get_children():
		if child is PlayerController: controller = child
	for original: EnemyCamp in world.camps:
		original.set_physics_process(false)
		for actor in original.pack.members:
			actor.hide()
			actor.remove_from_group("enemies")
			actor.collision_layer = 0
			actor.collision_mask = 0
			actor.set_process(false)
			for child in actor.get_children():
				if child is EnemyBrain: child.set_physics_process(false)
	var origin: Vector3 = world.camps[0].global_position + Vector3(3,.15,4)
	player.equipment.slots[&"weapon"] = ItemStack.new(&"wakecleaver")
	player.equipment.refresh()
	player.health.maximum = 10000
	player.health.current = 10000
	controller.rig.pitch = -.55
	controller.rig.distance = 8
	for id in ["meadow_wolf", "ironhide_boar", "silk_matron", "cairn_sentinel", "storm_wisp", "young_mosslings", "ironback", "road_bandit"]:
		var data: EnemyData = load("res://data/enemies/" + id + ".tres")
		var camp := EnemyCamp.new()
		camp.enemy_data = data
		camp.count = 1 if data.tier >= 3 else 3
		camp.rewards_enabled = false
		camp.respawn_enabled = false
		camp.position = origin
		world.add_child(camp)
		camp.set_physics_process(false)
		var target: ActorBody = camp.pack.members[0]
		var brain: EnemyBrain
		for actor in camp.pack.members:
			for child in actor.get_children():
				if child is EnemyBrain:
					child.set_physics_process(false)
					if actor == target: brain = child
			if actor != target:
				actor.hide()
				actor.remove_from_group("enemies")
				actor.collision_layer = 0
				actor.collision_mask = 0
		player.global_position = origin
		player.statuses.clear()
		player.velocity = Vector3.ZERO
		player.rotation.y = 0
		player.combat.cancel()
		player.navigation.cancel()
		player.world_interaction.cancel()
		player.ui_session.close()
		target.global_position = origin + Vector3(0,0,-1.9)
		target.rotation.y = PI
		target.health.maximum = 10000
		target.health.current = 10000
		var visual: ActorVisual = target.visual
		check(visual.ready_for_animation and visual.skeleton != null, id + " uses an imported animated skin")
		for clip in [&"idle", &"run", &"attack_01", &"hit", &"death"]:
			check(visual.animation_player.has_animation(clip), id + " preserves " + clip)
		var crowns := visual.model.find_children("EliteCrown*", "MeshInstance3D", true, false)
		for crown in crowns: check(crown.visible == (data.tier >= 3), id + " crown matches elite tier")
		controller.rig.yaw = .5
		controller.rig.distance = 5.5
		await frames(10)
		await capture(id + "_front")
		controller.rig.yaw = 1.75
		await frames(6)
		await capture(id + "_side")
		controller.rig.yaw = -.35
		controller.rig.distance = 8
		await frames(8)
		await capture(id + "_gameplay")
		var hero_hits := player.combat.total_hits
		var monster_hits := target.combat.total_hits
		brain.set_physics_process(true)
		camp.pack.target = player
		controller.auto_attack = true
		var seen_attack := false
		for frame in range(120):
			await frames(1)
			if not seen_attack and target.combat.phase == MeleeCombat.Phase.ACTIVE:
				seen_attack = true
				await capture(id + "_impact")
		controller.auto_attack = false
		await frames(25)
		check(player.combat.total_hits > hero_hits, id + " takes real auto-attack damage")
		check(seen_attack and target.combat.total_hits > monster_hits, id + " attacks through the real AI and damage resolver")
		camp.queue_free()
		await frames(3)
	print("Jade visual review: %d failures" % failures)
	quit(1 if failures else 0)
