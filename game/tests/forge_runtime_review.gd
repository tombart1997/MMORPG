extends "res://tests/combat_smoke.gd"
## Verify imported catalogue skins, textures, animations, and breakable parts.

func inspect_model(path: String, animate: bool) -> void:
	var packed := load(path) as PackedScene
	check(packed!=null,"Imported scene: "+path)
	if not packed: return
	var model := packed.instantiate() as Node3D
	root.add_child(model)
	var meshes := model.find_children("*","MeshInstance3D",true,false)
	check(not meshes.is_empty(),"Reconstructed geometry: "+path)
	var surfaced := false
	for part: MeshInstance3D in meshes:
		check(part.get_aabb().size.is_finite() and part.get_aabb().size.length()>.001,"Finite model bounds: "+path)
		for surface in part.mesh.get_surface_count():
			var mat := part.get_active_material(surface) as StandardMaterial3D
			if mat:
				surfaced=true
				check(is_finite(mat.roughness) and mat.roughness>=0 and mat.roughness<=1,"Valid PBR roughness: "+path)
			else:check(false,"Missing PBR material: "+path)
		if animate: check(part.skin!=null,"Imported skin: "+path)
	check(surfaced,"Imported PBR texture, vertex color or authored solid surface: "+path)
	if animate:
		var rigs := model.find_children("*","Skeleton3D",true,false)
		var players := model.find_children("*","AnimationPlayer",true,false)
		check(rigs.size()==1 and players.size()==1,"Single runtime rig: "+path)
		var skeleton := rigs[0] as Skeleton3D
		var player := players[0] as AnimationPlayer
		player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		for clip in player.get_animation_list():
			if clip=="RESET":continue
			player.play(clip);player.seek(player.current_animation_length*.45,true)
			for bone in skeleton.get_bone_count():
				var pose := skeleton.get_bone_global_pose(bone)
				if not pose.origin.is_finite() or not pose.basis.is_finite():
					check(false,"Non-finite animation pose: "+path+" / "+clip)
	model.queue_free()

func _run() -> void:
	var report := JSON.parse_string(FileAccess.get_file_as_string("res://data/visuals/generated_manifest.json")) as Dictionary
	for item: Dictionary in report.models:
		var path: String=item.path
		check(FileAccess.get_sha256(path)==item.sha256,"Shipped model hash: "+path)
		inspect_model(path,"/mobs/" in path or "/npcs/" in path or path.ends_with("/warrior.glb") or path.ends_with("/bay_horse.glb"))
		await frames(1)
	var stage := Node3D.new();root.add_child(stage)
	var fracture = load("res://scripts/farming/fracture_visual.gd").new()
	stage.add_child(fracture)
	check(fracture.ribs.size()==7,"Reconstructed Fracture retains seven independently breakable ribs")
	check(fracture.cores.size()==1,"Reconstructed Fracture retains its separately animated core")
	fracture.pose_rib(0,.6)
	check(not fracture.ribs[0].transform.is_equal_approx(fracture.rib_rest[0]),"New rib geometry responds to collapse animation")
	stage.queue_free();await frames(2)
	print("FORGE_RUNTIME_REVIEW failures=",failures)
	quit(1 if failures else 0)
