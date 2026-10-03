extends SceneTree
## Reproducible uncapped 720p benchmark, with CPU/animation and shadow ablations.
var world: Node3D
var results: Dictionary = {}
var label := "before"
var rig: ThirdPersonCamera
var pose := Vector3.ZERO
var yaw := .32
var ablations_only: bool = false

func lock_pose() -> void:
	root.size = Vector2i(1280,720)
	if not is_instance_valid(world): return
	world.player.global_position = pose
	world.player.velocity = Vector3.ZERO
	rig.global_position = pose+Vector3(0,1.3,0)
	rig.rotation = Vector3(-.48,yaw,0)
	rig.arm.spring_length = 11

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--label="): label = arg.trim_prefix("--label=")
		if arg=="--ablations-only": ablations_only=true
	call_deferred("run")

func settle(count: int) -> void:
	for i in count:
		lock_pose()
		await process_frame

func measure(key: String) -> void:
	await settle(45)
	var warm_until := Time.get_ticks_msec()+2000
	while Time.get_ticks_msec()<warm_until:
		lock_pose()
		await process_frame
	var samples: Array[float] = []
	var cpu := 0.0
	var physics := 0.0
	var gpu := 0.0
	var render_cpu := 0.0
	var draw_calls := 0.0
	var primitives := 0.0
	var last := Time.get_ticks_usec()
	var started := last
	while samples.size()<180 or Time.get_ticks_usec()-started<5000000:
		lock_pose()
		await process_frame
		var now := Time.get_ticks_usec()
		samples.append((now-last)/1000.0)
		last = now
		cpu += Performance.get_monitor(Performance.TIME_PROCESS)*1000
		physics += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000
		gpu += RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid())
		render_cpu += RenderingServer.viewport_get_measured_render_time_cpu(root.get_viewport_rid())
		draw_calls += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		primitives += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	samples.sort()
	var n := samples.size()
	results[key] = {"samples":n,"frame_median_ms":samples[n/2],"frame_p95_ms":samples[int(n*.95)],"process_ms":cpu/n,"physics_ms":physics/n,"render_cpu_ms":render_cpu/n,"render_gpu_ms":gpu/n,"draw_calls":draw_calls/n,"primitives":primitives/n,"actors":get_nodes_in_group("enemies").size(),"nodes":Performance.get_monitor(Performance.OBJECT_NODE_COUNT)}
	print("PROFILE ",key," ",JSON.stringify(results[key]))
	write_results()

func write_results() -> void:
	var file := FileAccess.open("res://.local/remaster_%s.json" % label,FileAccess.WRITE)
	file.store_string(JSON.stringify(results,"\t"))

func capture(key: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.local/remaster_%s_%s.png" % [label,key])

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://.local"))
	Engine.max_fps = 0
	root.unresizable = true
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.size = Vector2i(1280,720)
	RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(),true)
	var start := Time.get_ticks_msec()
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	results["startup_ms"] = Time.get_ticks_msec()-start
	results["hardware"] = RenderingServer.get_video_adapter_name()
	results["resolution"] = "1280x720, uncapped, Compatibility renderer"
	results["engine"] = Engine.get_version_info().string
	results["groups"] = world.camps.size()
	rig = world.player.world_interaction.camera.get_parent().get_parent()
	rig.set_process(false)
	rig.set_process_input(false)
	rig.set_process_unhandled_input(false)
	pose = ZoneTerrain.START+Vector3.UP*.1
	rig.yaw = .32
	rig.pitch = -.48
	rig.distance = 11
	if not ablations_only:
		await measure("settlement")
		await capture("settlement_ui")
		for child in world.get_children():
			if child is CanvasLayer: child.hide()
		await settle(2)
		await capture("settlement")
		for child in world.get_children():
			if child is CanvasLayer: child.show()
	pose = Vector3(14,.2,-20)
	yaw = -.55
	if not ablations_only:
		await measure("wilderness")
		await capture("wilderness_ui")
		for child in world.get_children():
			if child is CanvasLayer: child.hide()
		await settle(2)
		await capture("wilderness")
		for child in world.get_children():
			if child is CanvasLayer: child.show()
	for actor in get_nodes_in_group("enemies"): actor.process_mode = Node.PROCESS_MODE_DISABLED
	await measure("enemies_frozen")
	for actor in get_nodes_in_group("enemies"): actor.process_mode = Node.PROCESS_MODE_INHERIT
	for child in world.get_children():
		if child is DirectionalLight3D: child.shadow_enabled = false
	await measure("shadows_off")
	write_results()
	quit()
