extends SceneTree
## Isolated imported scenes. Numerical contracts never imply visual acceptance.
func _initialize() -> void:call_deferred("run")

func run() -> void:
	var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	var records: Array=[];var failures:=0
	for entry: Dictionary in request.assets:
		var record: Dictionary={"key":entry.key,"path":entry.path,"status":"passed","errors":[],"bones":[],"animations":[],"materials":0,"meshes":0,"surfaces":0,"triangles":0,"sockets":[]}
		var scene:=load(entry.path) as PackedScene
		if not scene:record.errors.append("Scene failed to import")
		else:
			var node:=scene.instantiate() as Node3D;root.add_child(node)
			var first:=true;var bounds:=AABB()
			for mesh: MeshInstance3D in node.find_children("*","MeshInstance3D",true,false):
				record.meshes+=1
				var value:=node.global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
				bounds=value if first else bounds.merge(value);first=false
				if not value.position.is_finite() or not value.size.is_finite():record.errors.append("Non-finite mesh bounds")
				for s in mesh.mesh.get_surface_count():
					record.surfaces+=1
					if mesh.get_active_material(s):record.materials+=1
					else:record.errors.append("Missing material")
					var arrays:=mesh.mesh.surface_get_arrays(s);var indices=arrays[Mesh.ARRAY_INDEX]
					record.triangles+=indices.size()/3 if indices!=null and not indices.is_empty() else arrays[Mesh.ARRAY_VERTEX].size()/3
			for skeleton: Skeleton3D in node.find_children("*","Skeleton3D",true,false):
				for i in skeleton.get_bone_count():record.bones.append(skeleton.get_bone_name(i))
			for player: AnimationPlayer in node.find_children("*","AnimationPlayer",true,false):
				player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
				for clip in player.get_animation_list():
					if clip=="RESET":continue
					record.animations.append(String(clip))
					for sample in [.25,.5,.75]:
						player.play(clip);player.seek(player.get_animation(clip).length*sample,true)
						for skeleton: Skeleton3D in node.find_children("*","Skeleton3D",true,false):
							for i in skeleton.get_bone_count():
								var transform_value:=skeleton.get_bone_global_pose(i)
								if not transform_value.origin.is_finite() or not transform_value.basis.is_finite():record.errors.append("Non-finite pose: "+clip)
			for name in ["Grip","Tip","WeaponSocket","Saddle","saddle_socket"]:
				var found:=node.find_child(name,true,false)
				if found:record.sockets.append(name)
			record.bounds={"position":[bounds.position.x,bounds.position.y,bounds.position.z],"size":[bounds.size.x,bounds.size.y,bounds.size.z]}
			record.root_transform=str(node.transform)
			if record.meshes==0:record.errors.append("No renderable mesh")
			if entry.has("expected_bones"):
				for bone in entry.expected_bones:
					if not record.bones.has(bone):record.errors.append("Missing bone: "+bone)
			if entry.has("expected_clips"):
				for clip in entry.expected_clips:
					if not record.animations.has(clip):record.errors.append("Missing clip: "+clip)
			node.free()
		if not record.errors.is_empty():record.status="failed";failures+=1
		records.append(record)
		await process_frame
	var file:=FileAccess.open(request.output,FileAccess.WRITE);file.store_string(JSON.stringify({"assets":records,"failures":failures,"status":"passed" if failures==0 else "failed","scope":"Isolated scale, pivot, materials, sockets, skin and clip import; visual and whole-game integration are separate."},"\t"));file.close()
	print("REVIEW_INVENTORY_CONTRACTS ",records.size()," failures=",failures);quit(1 if failures else 0)
