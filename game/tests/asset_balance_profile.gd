extends SceneTree
## Rendered whole-game timing. Saves are disabled; authored encounters remain intact.
var world: Node3D
var rig: ThirdPersonCamera
var player: ActorBody
var label := "baseline"
var resolution := Vector2i(1920,1080)
var results: Dictionary = {}
var pose := Vector3.ZERO
var yaw := .32
var combat_case := false
var moving_case := false
var dense_only := false
var travel_only := false
var travel_start := Vector3.ZERO
var started_ms := 0
var combat_camps: Array[EnemyCamp]=[]

func _initialize() -> void:
	var args:=OS.get_cmdline_user_args()
	var label_index:=args.find("--label")
	if label_index>=0 and label_index+1<args.size():label=args[label_index+1]
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--label="): label=arg.trim_prefix("--label=")
		if arg=="--dense-only":dense_only=true
		if arg=="--travel-only":travel_only=true
		if arg=="--720p": resolution=Vector2i(1280,720)
	call_deferred("run")

func step() -> void:
	player.health.current=player.health.maximum
	if moving_case:
		# Real click-to-move, mount gait and streaming while crossing the first road.
		pose=player.global_position
	else:
		player.global_position=pose
		player.velocity=Vector3.ZERO
	if combat_case:
		if not player.combat.is_attacking(): player.combat.request_attack()
		for camp: EnemyCamp in combat_camps:
			if not camp.dormant:
				camp.pack.target=player
				for member in camp.pack.members:
					member.health.current=member.health.maximum
	var height:=1.3+(player.mounts.definition.rider_height if player.mounts.mounted else 0.0)
	rig.global_position=player.global_position+Vector3(0,height,0)
	rig.rotation=Vector3(-.48,yaw,0)
	rig.arm.spring_length=11

func wait_seconds(seconds: float) -> void:
	var end:=Time.get_ticks_msec()+int(seconds*1000)
	while Time.get_ticks_msec()<end:
		step()
		await process_frame

func measure(key: String) -> void:
	await wait_seconds(2.0)
	var cost_start:Dictionary=Engine.get_meta("profile_costs",{}).duplicate()
	var samples: Array[float]=[]
	var gpu:=0.0
	var physics:=0.0
	var process_time:=0.0
	var render_cpu:=0.0
	var draws:=0.0
	var primitives:=0.0
	var actors:=0.0
	var riding_frames:=0
	var last:=Time.get_ticks_usec()
	var started:=last
	while Time.get_ticks_usec()-started<8000000:
		step()
		await process_frame
		var now:=Time.get_ticks_usec()
		samples.append((now-last)/1000.0)
		last=now
		gpu+=RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid())
		physics+=Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000
		process_time+=Performance.get_monitor(Performance.TIME_PROCESS)*1000
		render_cpu+=RenderingServer.viewport_get_measured_render_time_cpu(root.get_viewport_rid())
		draws+=Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		primitives+=Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		actors+=get_nodes_in_group("enemies").size()
		if player.mounts.mounted:riding_frames+=1
	samples.sort()
	var n:=samples.size()
	var over_budget:=samples.filter(func(ms):return ms>1000.0/60).size()
	results[key]={"samples":n,"median_ms":samples[n/2],"p95_ms":samples[int(n*.95)],"p99_ms":samples[int(n*.99)],"over_60fps_budget_percent":100.0*over_budget/n,"worst_ms":samples.back(),"gpu_ms":gpu/n,"physics_ms":physics/n,"process_ms":process_time/n,"render_cpu_ms":render_cpu/n,"combat_pose":str(pose),"draw_calls":draws/n,"primitives":primitives/n,"actors":actors/n}
	if moving_case:
		results[key]["mounted_sample_percent"]=100.0*riding_frames/n
		results[key]["distance_travelled_m"]=player.global_position.distance_to(travel_start)
		results[key]["navigation_failure"]=player.navigation.failure
		results[key]["end_position"]=str(player.global_position)
	if Engine.has_meta("profile_costs"):
		var cost_report:Dictionary={}
		for metric in Engine.get_meta("profile_costs"):
			cost_report[metric]=(Engine.get_meta("profile_costs")[metric]-int(cost_start.get(metric,0)))/1000.0/n
		results[key]["instrumented_cpu_ms_per_frame"]=cost_report
		results[key]["long_cpu_spans"]=RuntimeCosts.long_spans.duplicate()
	print("ASSET_BALANCE ",key," ",JSON.stringify(results[key]))
	var file:=FileAccess.open("res://.local/asset_balance_%s.json"%label,FileAccess.WRITE)
	file.store_string(JSON.stringify(results,"\t"))
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.local/asset_balance_%s_%s.png"%[label,key])

func run() -> void:
	if OS.get_cmdline_user_args().has("--staged"):
		ReviewedModels.loaded=true
		ReviewedModels.mappings=JSON.parse_string(FileAccess.get_file_as_string("res://review_assets/staged_mappings.json")).mappings
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://.local"))
	RuntimeCosts.enabled=OS.get_cmdline_user_args().has("--cpu-profile")
	Engine.max_fps=0
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.size=resolution
	RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(),true)
	started_ms=Time.get_ticks_msec()
	world=load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled=false
	root.add_child(world)
	current_scene=world
	player=world.player
	player.health.maximum=100000
	rig=player.world_interaction.camera.get_parent().get_parent()
	rig.set_process(false)
	rig.set_process_input(false)
	rig.set_process_unhandled_input(false)
	results={"hardware":RenderingServer.get_video_adapter_name(),"resolution":str(resolution),"renderer":"Compatibility, uncapped","target_fps":60,"startup_ms":Time.get_ticks_msec()-started_ms,"authored_camps":world.camps.size(),"saving_enabled":false}
	pose=ZoneTerrain.START+Vector3.UP*.1
	if not dense_only and not travel_only:await measure("settlement")
	pose=Vector3(14,.2,-20)
	yaw=-.55
	if not dense_only and not travel_only:await measure("wilderness")
	# Use the densest real authored clearing, without adding synthetic monsters.
	var density:=0
	for camp: EnemyCamp in world.camps:
		if SafeArea.protects(camp):continue
		var nearby:=0
		for other: EnemyCamp in world.camps:
			if other.global_position.distance_to(camp.global_position)<18:nearby+=other.count
		if nearby>density:
			density=nearby
			pose=camp.global_position+Vector3(0,.15,3)
	combat_case=true
	for camp: EnemyCamp in world.camps:
		if camp.global_position.distance_to(pose)<17:combat_camps.append(camp)
	if not travel_only:await measure("dense_combat")
	if dense_only:
		quit()
		return
	combat_case=false
	for camp: EnemyCamp in world.camps:camp.pack.disengage()
	player.combat.cancel()
	player.world_interaction.cancel()
	player.navigation.cancel()
	player.global_position=ZoneTerrain.START+Vector3(0,.1,-5)
	pose=player.global_position
	# Let the actual collision/ground state settle before requesting a mount.
	moving_case=true
	await wait_seconds(.6)
	player.mounts.combat_lock=0
	player.mounts.owned.append(&"trail_horse")
	player.mounts.selected=&"trail_horse"
	player.mounts.toggle()
	results["travel_mount_succeeded"]=player.mounts.mounted
	if not player.mounts.mounted:
		push_error("Travel benchmark could not mount: "+player.mounts.unavailable())
		quit(1)
		return
	travel_start=player.global_position
	player.world_interaction.command({"kind":&"terrain","position":Vector3(0,.1,-85),"normal":Vector3.UP})
	await measure("mounted_travel")
	if results.mounted_travel.mounted_sample_percent<99 or results.mounted_travel.distance_travelled_m<20:
		push_error("Travel benchmark did not sustain real mounted movement")
		quit(1)
		return
	print("ASSET_BALANCE_COMPLETE ",label)
	quit()
