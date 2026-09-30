extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var stage := Node3D.new()
	root.add_child(stage)
	current_scene = stage
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color(.055,.063,.074)
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(.7,.78,.9)
	environment.environment.ambient_light_energy = .55
	stage.add_child(environment)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-35,145,0)
	light.light_energy = 1.8
	light.shadow_enabled = true
	stage.add_child(light)
	var fill := OmniLight3D.new()
	fill.position = Vector3(-2,2,-2)
	fill.light_energy = 1.5
	fill.omni_range = 8
	stage.add_child(fill)
	var floor_mesh := MeshInstance3D.new()
	floor_mesh.mesh = PlaneMesh.new()
	floor_mesh.mesh.size = Vector2(12,12)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(.11,.13,.15)
	floor_mesh.material_override = mat
	stage.add_child(floor_mesh)
	var actor := ActorBody.new()
	actor.visual_scene = load("res://scenes/visuals/humanoid.tscn")
	actor.weapon = load("res://data/attacks/player_sword.tres")
	stage.add_child(actor)
	actor.set_process(false)
	actor.combat.set_physics_process(false)
	var camera := Camera3D.new()
	stage.add_child(camera)
	camera.position = Vector3(2.65,1.8,-3.75)
	camera.look_at(Vector3(0,.97,0))
	camera.fov = 38
	camera.current = true
	await frames(3)
	actor.visual.present(Vector3.ZERO,actor.combat,actor.health,"Warden",1)
	await capture("warden_idle")
	var tip := actor.visual.sockets[&"WeaponSocket"].get_node("Equipment/Tip") as Node3D
	for number in range(1,4):
		actor.combat.attack = load("res://data/attacks/" + ["player_sword","player_return","player_finisher"][number-1] + ".tres")
		actor.combat.swing_serial += 1
		for spec in [["load",MeleeCombat.Phase.WINDUP,.55],["contact",MeleeCombat.Phase.ACTIVE,0.0],["follow",MeleeCombat.Phase.ACTIVE,.85],["recover",MeleeCombat.Phase.RECOVERY,.5]]:
			actor.combat.phase=spec[1]
			var duration: float = actor.combat.attack.windup if spec[1]==MeleeCombat.Phase.WINDUP else actor.combat.attack.active if spec[1]==MeleeCombat.Phase.ACTIVE else actor.combat.attack.recovery
			actor.combat.phase_elapsed=duration*spec[2]
			actor.visual.present(Vector3.ZERO,actor.combat,actor.health,"Warden",1)
			await capture("warden_%d_%s" % [number,spec[0]])
			if spec[0]=="contact":
				print("CONTACT ",number," tip=",tip.global_position)
				check(tip.global_position.z < -.7, "Blade reaches forward at damage onset for attack %d" % number)
	actor.combat.cancel()
	actor.visual.present(Vector3.ZERO,actor.combat,actor.health,"Warden",1)
	camera.position=Vector3(.75,1.78,-1.25)
	camera.look_at(Vector3(0,1.68,0))
	camera.fov=27
	await capture("warden_portrait")
	if "--record" in OS.get_cmdline_user_args() and DisplayServer.get_name() != "headless":
		camera.position=Vector3(2.65,1.8,-3.75)
		camera.look_at(Vector3(0,1.15,0))
		camera.fov=40
		DirAccess.make_dir_recursive_absolute("res://.local/warden_frames")
		for frame in range(240):
			var attack_index := mini(2,frame/80)
			var elapsed := (frame%80)/60.0
			actor.combat.attack=load("res://data/attacks/"+["player_sword","player_return","player_finisher"][attack_index]+".tres")
			if frame%80==0: actor.combat.swing_serial+=1
			var attack:=actor.combat.attack
			if elapsed<attack.windup:
				actor.combat.phase=MeleeCombat.Phase.WINDUP
				actor.combat.phase_elapsed=elapsed
			elif elapsed<attack.windup+attack.active:
				actor.combat.phase=MeleeCombat.Phase.ACTIVE
				actor.combat.phase_elapsed=elapsed-attack.windup
			elif elapsed<attack.windup+attack.active+attack.recovery:
				actor.combat.phase=MeleeCombat.Phase.RECOVERY
				actor.combat.phase_elapsed=elapsed-attack.windup-attack.active
			else: actor.combat.cancel()
			actor.visual.present(Vector3.ZERO,actor.combat,actor.health,"Warden",1.0/60)
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("res://.local/warden_frames/%04d.png" % frame)
	print("Warden visual checks: %d failures" % failures)
	quit(1 if failures else 0)

func capture(filename: String) -> void:
	await frames(2)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/"+filename+".png")
