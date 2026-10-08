extends "res://tests/combat_smoke.gd"
## Staged visual replacements use real gameplay composition before deployment.
var output := "res://../docs/asset_review/integration"
var camera: Camera3D

func capture(title: String, point: Vector3, target: Vector3) -> void:
	camera.global_position=point;camera.look_at(target)
	await frames(4)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output+"/"+title+".png")

func _run() -> void:
	output=ProjectSettings.globalize_path(output)
	DirAccess.make_dir_recursive_absolute(output)
	root.size=Vector2i(1600,1000)
	if not OS.get_cmdline_user_args().has("--deployed"):
		ReviewedModels.loaded=true
		ReviewedModels.mappings=JSON.parse_string(FileAccess.get_file_as_string("res://review_assets/staged_mappings.json")).mappings
	for original: String in ReviewedModels.mappings:
		check(ReviewedModels.path_for(original)!=original,"Version resolves: "+original)
	var world=load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled=false;root.add_child(world);current_scene=world
	await frames(20)
	check(world.camps.size()==153,"All 153 authored camps retained")
	check(world.settlement.npcs.size()==9,"All nine settlement services retained")
	var actor: ActorBody=world.player
	check(actor.body_collider.shape is CapsuleShape3D and actor.collision_mask==11,"Visual mapping retains player collision")
	var nav:=actor.get_world_3d().navigation_map
	for npc: WorldNPC in world.settlement.npcs:
		var route:=NavigationServer3D.map_get_path(nav,ZoneTerrain.START,npc.global_position,true)
		check(not route.is_empty(),"Service navigation: "+npc.name)
		check(not npc.find_children("*","MeshInstance3D",true,false).is_empty(),"NPC reconstructed body exists: "+npc.name)
		var rig: Skeleton3D=npc.find_children("*","Skeleton3D",true,false)[0]
		check(rig.get_bone_count()==18,"NPC retains its 18-bone rig: "+npc.name)
	for ctl in actor.get_children():
		if ctl is PlayerController:
			ctl.set_physics_process(false);ctl.rig.set_process(false)
	actor.set_process(false)
	camera=Camera3D.new();world.add_child(camera);camera.current=true;camera.fov=60
	await capture("settlement",Vector3(7,6,26),Vector3(0,1.3,12))
	check(actor.visual.sockets[&"WeaponSocket"].has_node("Equipment"),"Player weapon attachment retained")
	check(actor.visual.sockets[&"ArmorSocket"].has_node("Equipment"),"Player armor attachment retained")
	var equipment=actor.visual.sockets[&"ArmorSocket"].get_node("Equipment")
	check(not equipment.find_children("*","MeshInstance3D",true,false).is_empty(),"Worn armor contains geometry")
	# Actual mount composition, collision state and existing clip/IK contracts.
	actor.mounts.owned.append(&"trail_horse");actor.mounts.selected=&"trail_horse"
	actor.mounts.combat_lock=0;actor.mounts.toggle()
	check(actor.mounts.mounted,"Reviewed horse mounts in the world")
	if actor.mounts.mounted:
		check(actor.mounts.model.skeleton.get_bone_count()==23,"Horse retains 23 bones")
		actor.mounts.dismount()
	# A neutral stage uses the same ActorVisual.apply_variant and equipment path.
	world.queue_free();await frames(3)
	var stage:=Node3D.new();root.add_child(stage);current_scene=stage
	var env_node:=WorldEnvironment.new();var env:=Environment.new()
	env.background_mode=Environment.BG_COLOR;env.background_color=Color("76818a")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("d4dce5");env.ambient_light_energy=.7
	env_node.environment=env;stage.add_child(env_node)
	var light:=DirectionalLight3D.new();light.rotation_degrees=Vector3(-45,-35,0);light.light_energy=1.1;stage.add_child(light)
	var fill:=DirectionalLight3D.new();fill.rotation_degrees=Vector3(-25,150,0);fill.light_energy=.6;stage.add_child(fill)
	camera=Camera3D.new();stage.add_child(camera);camera.current=true
	var ground:=MeshInstance3D.new();var plane:=PlaneMesh.new();plane.size=Vector2(40,40)
	var mat:=StandardMaterial3D.new();mat.albedo_color=Color("414a48");plane.material=mat;ground.mesh=plane;stage.add_child(ground)
	var species=["red_wolf","grey_wolf","ironhide_boar","bristle_boar","young","venom_spider","slate_guardian","road_bandit"]
	for i in species.size():
		var data:=load("res://data/enemies/"+species[i]+".tres") as EnemyData
		check(data!=null,"Enemy definition exists: "+species[i])
		if not data:continue
		var mob:=ActorBody.new();mob.enemy_definition=data;mob.weapon=data.attack;mob.visual_scene=data.visual
		mob.faction=&"enemies";mob.position=Vector3((i%4)*3.5-5.25,.02,-(i/4)*4)
		stage.add_child(mob);mob.set_process(false);mob.visual.apply_variant(data)
		mob.visual.scale=Vector3.ONE*data.visual_scale
		mob.visual.label.hide();mob.visual.contact_shadow.hide()
		mob.visual._sample(&"run",.25)
		check(mob.visual.skeleton!=null and mob.visual.animation_player.has_animation(&"run"),"Live replacement runs: "+species[i])
		if data.family==&"bandit":check(mob.visual.sockets[&"WeaponSocket"].has_node("Equipment"),"Reconstructed bandit retains separate weapon")
	await capture("runtime_families",Vector3(5,5,-13),Vector3(0,1,-2))
	var hero:=ActorBody.new();hero.weapon=load("res://data/attacks/player_sword.tres");stage.add_child(hero)
	hero.position=Vector3(0,.02,6);hero.set_process(false);hero.visual.label.hide();hero.visual.contact_shadow.hide()
	for armor in ["traveler_guard","jade_ironback_mantle","warden_insignia"]:
		hero.visual.equip_visual(&"ArmorSocket",load("res://assets/generated/equipment/"+armor+".glb"))
		hero.visual._sample(&"idle",0)
		await capture("worn_"+armor,Vector3(2,1.8,2),Vector3(0,1,6))
		await capture("worn_"+armor+"_side",Vector3(4,1.8,6),Vector3(0,1,6))
		await capture("worn_"+armor+"_back",Vector3(2,1.8,10),Vector3(0,1,6))
	var mode: String="deployed" if OS.get_cmdline_user_args().has("--deployed") else "staged"
	var report={"failures":failures,"status":"passed" if failures==0 else "failed","scope":"Actual %s world, collisions, navigation, NPC selection, creature variants, separate equipment and mount composition; visual acceptance separate."%mode}
	FileAccess.open(output+"/contracts.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("REVIEWED_INTEGRATION ",JSON.stringify(report));quit(1 if failures else 0)
