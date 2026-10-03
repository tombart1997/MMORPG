extends SceneTree
## Actual production scenes, deterministic camera views, isolated from saved games.
var world: Node3D
var rig: ThirdPersonCamera
var pose := Vector3.ZERO
var yaw := 0.0
var label := "review"
var results: Dictionary = {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--label="): label = arg.trim_prefix("--label=")
	call_deferred("run")

func lock_pose() -> void:
	world.player.global_position = pose
	world.player.velocity = Vector3.ZERO
	world.player.health.current = world.player.health.maximum
	rig.global_position = pose + Vector3(0,1.3,0)
	rig.rotation = Vector3(-.40,yaw,0)
	rig.arm.spring_length = 11

func frames(count: int) -> void:
	for i in count:
		if is_instance_valid(world): lock_pose()
		await process_frame

func view(key: String, point: Vector3, angle: float) -> void:
	point.y = CinderfallTerrain.height_at(point.x,point.z) if world.region_id == "cinderfall" else ZoneTerrain.height_at(point.x,point.z)
	pose = point + Vector3.UP*.08
	yaw = angle
	await frames(60)
	var samples: Array[float] = []
	var draws := 0.0
	var primitives := 0.0
	var previous := Time.get_ticks_usec()
	for i in 120:
		lock_pose()
		await process_frame
		var now := Time.get_ticks_usec()
		samples.append((now-previous)/1000.0)
		previous = now
		draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		primitives += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	samples.sort()
	results[key] = {"median_ms":samples[60],"p95_ms":samples[114],"draw_calls":draws/120,"primitives":primitives/120,"enemies":get_nodes_in_group("enemies").size()}
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("../docs/screenshots/visual-pass/%s_%s.png" % [label,key])
	print("VISUAL_REVIEW ",label," ",key," ",JSON.stringify(results[key]))

func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Visual review requires real rendering")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute("../docs/screenshots/visual-pass")
	root.size = Vector2i(1280,720)
	Engine.max_fps = 0
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	for region in ["outdoor", "cinderfall"]:
		var started := Time.get_ticks_msec()
		world = load("res://scenes/%s_zone.tscn" % region).instantiate()
		world.persistence_enabled = false
		root.add_child(world)
		current_scene = world
		results[region+"_startup_ms"] = Time.get_ticks_msec()-started
		rig = world.player.world_interaction.camera.get_parent().get_parent()
		rig.set_process(false)
		rig.set_process_input(false)
		rig.set_process_unhandled_input(false)
		if region == "outdoor":
			await view("settlement", ZoneTerrain.START, .32)
			await view("verge", Vector3(14,0,-20), -.55)
			await view("route", Vector3(-85,0,-88), -1.1)
			await view("amber", Vector3(-8,0,-37), 0)
		else:
			await view("outpost", Vector3(0,0,48), .32)
			await view("basin", Vector3(12,0,-4), .32)
		world.queue_free()
		await process_frame
		await process_frame
	results["hardware"] = RenderingServer.get_video_adapter_name()
	var file := FileAccess.open("../docs/screenshots/visual-pass/%s_metrics.json" % label,FileAccess.WRITE)
	file.store_string(JSON.stringify(results,"\t"))
	quit()
