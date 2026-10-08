extends "res://tests/combat_smoke.gd"
## Inspect shipped GLB materials and the actual mounted pose on a neutral stage.
## godot --path game --script res://tests/horse_reference_review.gd -- --label final
var stage: Node3D
var actor: ActorBody
var horse: TrailHorse
var camera: Camera3D
var output := ""

func capture(name_value: String, direction: Vector3, target: Vector3, size_value: float) -> void:
	camera.position = target+direction
	camera.look_at(target)
	camera.size = size_value
	await frames(3)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output+"/"+name_value+".png")

func _run() -> void:
	if OS.get_cmdline_user_args().has("--staged"):
		ReviewedModels.loaded=true
		ReviewedModels.mappings=JSON.parse_string(FileAccess.get_file_as_string("res://review_assets/staged_mappings.json")).mappings
	output=ProjectSettings.globalize_path("res://").path_join("../docs/screenshots/horse-reference/godot").simplify_path()
	var args := OS.get_cmdline_user_args()
	var index := args.find("--label")
	if index >= 0 and index+1 < args.size(): output += "/"+args[index+1]
	DirAccess.make_dir_recursive_absolute(output)
	stage=Node3D.new();root.add_child(stage);current_scene=stage
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode=Environment.BG_COLOR
	environment.background_color=Color("9ca5ac")
	environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color=Color("ced9e3")
	environment.ambient_light_energy=.50
	world_environment.environment=environment;stage.add_child(world_environment)
	for entry in [[Vector3(-45,150,0),1.0,Color("ffe6cc")],[Vector3(-25,-30,0),.35,Color("d4e4ff")]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees=entry[0];light.light_energy=entry[1];light.light_color=entry[2]
		light.shadow_enabled=true;stage.add_child(light)
	var floor_mesh := MeshInstance3D.new()
	var plane := PlaneMesh.new();plane.size=Vector2(200,200)
	var floor_material := StandardMaterial3D.new();floor_material.albedo_color=Color("343b3e");floor_material.roughness=1
	plane.material=floor_material;floor_mesh.mesh=plane;floor_mesh.position.y=-.015;stage.add_child(floor_mesh)
	camera=Camera3D.new();camera.projection=Camera3D.PROJECTION_ORTHOGONAL;stage.add_child(camera);camera.current=true
	actor=ActorBody.new();actor.weapon=load("res://data/attacks/player_sword.tres")
	actor.attack_sequence.assign([load("res://data/attacks/player_sword.tres"),load("res://data/attacks/player_return.tres")])
	stage.add_child(actor);actor.set_process(false)
	actor.mounts=PlayerMount.new();actor.mounts.actor=actor;actor.add_child(actor.mounts);actor.mounts.set_process(false)
	actor.visual.contact_shadow.hide()
	actor.visual.sockets[&"WeaponSocket"].get_node("Equipment").hide()
	actor.visual.sockets[&"ArmorSocket"].get_node("Equipment").hide()
	await frames(4)
	actor.visual._sample(&"idle",0)
	actor.visual.hide()
	horse=load("res://scenes/visuals/trail_horse.tscn").instantiate();actor.add_child(horse)
	actor.mounts.model=horse;actor.mounts.definition=MountData.find(&"trail_horse")
	check(horse.skeleton.get_bone_count()==23,"Adapted horse retains the 23-bone runtime rig")
	for clip in [&"idle",&"walk",&"trot",&"canter"]:
		check(horse.player.has_animation(clip),"Adapted horse imports "+String(clip))
	horse.travel(Vector3.ZERO,0)
	var textured := false
	for imported: MeshInstance3D in horse.find_children("*","MeshInstance3D",true,false):
		for surface in imported.mesh.get_surface_count():
			var material := imported.mesh.surface_get_material(surface) as StandardMaterial3D
			if material and material.albedo_texture:
				textured=true
	check(textured,"Horse imports its retained bay coat diffuse texture")
	for view in [["front",Vector3(0,.15,-6)],["side",Vector3(6,.05,0)],["threequarter",Vector3(5,.7,-6)]]:
		await capture("horse_"+view[0],view[1],Vector3(0,1.10,-.1),3.4)
	horse.hide();actor.visual.show();actor.visual.position=Vector3.ZERO
	for view in [["front",Vector3(0,.10,-5)],["side",Vector3(5,.05,0)],["threequarter",Vector3(4,.25,-5)]]:
		await capture("rider_"+view[0],view[1],Vector3(0,.97,0),2.25)
	horse.show();actor.mounts.mounted=true
	actor.visual.position=Vector3(0,actor.mounts.definition.rider_height,0)+horse.saddle_offset()
	actor.visual.present(Vector3.ZERO,actor.combat,actor.health,"Rider",0)
	for view in [["front",Vector3(0,.15,-6)],["side",Vector3(6,.05,0)],["threequarter",Vector3(5,.7,-6)]]:
		await capture("mounted_"+view[0],view[1],Vector3(0,1.32,-.1),3.55)
	var foot_error := 0.0
	for side in ["L","R"]:
		foot_error=maxf(foot_error,actor.visual.bone_world_transform(StringName("Foot."+side)).origin.distance_to(horse.stirrup_world(-1 if side=="L" else 1)))
	check(foot_error<.025,"Mounted ankles follow the saddle's stirrups (%.4fm)" % foot_error)
	var rein_error := actor.visual.socket_world_transform(&"OffhandSocket").origin.distance_to(horse.rein_grip_world())
	check(rein_error<.025,"Mounted left hand follows the rein grip (%.4fm)" % rein_error)
	var report := {"foot_error_m":foot_error,"rein_error_m":rein_error,"failures":failures}
	FileAccess.open(output+"/metrics.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("HORSE_REFERENCE_REVIEW ",JSON.stringify(report))
	root.get_node("GameAudio").shutdown();stage.queue_free();await frames(3)
	quit(1 if failures else 0)
