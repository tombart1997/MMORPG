extends "res://tests/combat_smoke.gd"
## Development only. Wall-frame timings are measurements, not a guaranteed FPS.
func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(10)
	for camp in world.camps: camp.queue_free()
	world.camps.clear()
	world.player.position = ZoneTerrain.CAMPS[1] + Vector3(0, 0, 2)
	world.player.health.maximum = 1000000
	world.player.health.current = 1000000
	for count in [10, 20, 40, 80]:
		var camp := EnemyCamp.new()
		camp.position = ZoneTerrain.CAMPS[1]
		camp.count = count
		camp.enemy_data = load("res://data/enemies/young.tres")
		camp.leash_distance = 100
		world.add_child(camp)
		for i in count:
			var angle: float = i * 2.39996
			var radius := 2.5 + sqrt(float(i)) * 0.55
			camp.pack.members[i].global_position = camp.global_position + Vector3(sin(angle), 0.1, cos(angle)) * radius
		camp.pack.target = world.player
		await frames(90)
		var samples: Array[float] = []
		var physics_ms := 0.0
		var process_ms := 0.0
		for i in 180:
			var start := Time.get_ticks_usec()
			await frames(1)
			samples.append((Time.get_ticks_usec() - start) / 1000.0)
			physics_ms += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000
			process_ms += Performance.get_monitor(Performance.TIME_PROCESS) * 1000
		samples.sort()
		print("STRESS mode=%s count=%d wall_median_ms=%.3f wall_p95_ms=%.3f physics_mean_ms=%.3f process_mean_ms=%.3f" % [DisplayServer.get_name(), count, samples[90], samples[171], physics_ms / 180, process_ms / 180])
		var locations: Dictionary = {}
		for actor in camp.pack.members:
			locations[Vector2i(roundi(actor.position.x * 3), roundi(actor.position.z * 3))] = true
		check(locations.size() >= count * 0.75, "Crowd retains distinct positions at %d enemies" % count)
		if DisplayServer.get_name() != "headless":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("res://.local/farming_stress_%d.png" % count)
		print("RENDER count=%d draw_calls=%d objects=%d primitives=%d" % [count, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)])
		if count == 40:
			for actor in camp.pack.members: actor.set_process(false)
			await sample_variant("40 frozen animation, visible meshes")
			for actor in camp.pack.members: actor.set_process(true); actor.visual.hide()
			await sample_variant("40 live animation, hidden meshes")
			for actor in camp.pack.members: actor.visual.show()
			# Hold the exact scene pose while isolating new art rendering costs.
			var prior_mode:int=world.process_mode
			world.process_mode=Node.PROCESS_MODE_DISABLED
			var prior_vsync:int=DisplayServer.window_get_vsync_mode()
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
			await sample_variant("40 fixed scene uncapped, full art")
			var grove:Node=world.find_child("AmberScarArt",true,false)
			var shadows:Dictionary={}
			for mesh:MeshInstance3D in grove.find_children("*","MeshInstance3D",true,false):
				shadows[mesh]=mesh.cast_shadow
				mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			await sample_variant("40 fixed scene uncapped, grove shadows disabled")
			for mesh in shadows: mesh.cast_shadow=shadows[mesh]
			var prior_msaa:int=root.msaa_3d
			root.msaa_3d=Viewport.MSAA_DISABLED
			await sample_variant("40 fixed scene uncapped, MSAA disabled")
			root.msaa_3d=prior_msaa
			DisplayServer.window_set_vsync_mode(prior_vsync)
			world.process_mode=prior_mode
		camp.queue_free()
		await frames(3)
	for i in 60:
		var drop := LootPickup.new()
		drop.item = ItemCatalog.get_item(&"wakeglass" if i % 20 == 0 else &"moss_shard")
		world.add_child(drop)
		drop.position = world.player.position + Vector3(sin(i * 2.4), 0, cos(i * 2.4)) * (1 + sqrt(float(i)) * 0.25)
	await frames(30)
	var loot_samples: Array[float] = []
	for i in 180:
		var start := Time.get_ticks_usec()
		await frames(1)
		loot_samples.append((Time.get_ticks_usec() - start) / 1000.0)
	loot_samples.sort()
	print("LOOT_STRESS count=60 rare=3 wall_median_ms=%.3f wall_p95_ms=%.3f" % [loot_samples[90], loot_samples[171]])
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/farming_loot_stress.png")
	quit(1 if failures else 0)
func sample_variant(label: String) -> void:
	await frames(30)
	var samples: Array[float] = []
	for i in 120:
		var start := Time.get_ticks_usec()
		await frames(1)
		samples.append((Time.get_ticks_usec() - start) / 1000.0)
	samples.sort()
	print("PROFILE %s median_ms=%.3f p95_ms=%.3f" % [label, samples[60], samples[114]])
