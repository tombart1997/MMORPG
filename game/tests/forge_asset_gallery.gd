extends SceneTree
## Render the actual imported materials; each row is front, side, three-quarter.
var stage: Node3D
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var manifest := JSON.parse_string(FileAccess.get_file_as_string(args[0])) as Dictionary
	stage=Node3D.new();root.add_child(stage);current_scene=stage
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color("76818b")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("e2e7ed");env.ambient_light_energy=.65
	var world:=WorldEnvironment.new();world.environment=env;stage.add_child(world)
	for entry in [[Vector3(-35,-25,0),1.2],[Vector3(-25,140,0),.5]]:
		var light:=DirectionalLight3D.new();light.rotation_degrees=entry[0];light.light_energy=entry[1];stage.add_child(light)
	var rows: Array=manifest.assets
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_DISABLED;root.content_scale_size=Vector2i.ZERO;root.size=Vector2i(1200,rows.size()*400)
	var camera:=Camera3D.new();camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.keep_aspect=Camera3D.KEEP_WIDTH;camera.size=8.2
	var midpoint:=float(rows.size()-1)*1.35+1.2
	stage.add_child(camera);camera.position=Vector3(0,midpoint,20);camera.look_at(Vector3(0,midpoint,0));camera.current=true
	for row in rows.size():
		var source:=load(rows[row].path) as PackedScene
		assert(source,"Cannot load gallery model: "+str(rows[row].path))
		for col in 3:
			var pivot:=Node3D.new();stage.add_child(pivot);pivot.position=Vector3((col-1)*2.6,(rows.size()-1-row)*2.7,0)
			var model:=Node3D.new();pivot.add_child(model)
			var imported:=source.instantiate() as Node3D;model.add_child(imported)
			# Equipment's runtime forward axis follows its socket. Stand it up only
			# on the inspection stage so all faces can be reviewed clearly.
			var equipment_path := String(rows[row].path)
			if "coin" in equipment_path:imported.rotation_degrees.x=90
			elif "/weapons/" in equipment_path or equipment_path.ends_with("_sword.glb"):
				var native_bounds:=AABB();var native_first:=true
				for mesh: MeshInstance3D in imported.find_children("*","MeshInstance3D",true,false):
					var value:=model.global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
					native_bounds=value if native_first else native_bounds.merge(value);native_first=false
				var axis:=native_bounds.size.max_axis_index()
				var forward:=Vector3.ZERO;forward[axis]=1 if native_bounds.get_center()[axis]>=0 else -1
				imported.quaternion=Quaternion(forward,Vector3.UP)
			for player: AnimationPlayer in model.find_children("*","AnimationPlayer",true,false):
				var clip:=str(manifest.get("clip","idle"))
				if player.has_animation(clip):
					player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL;player.play(clip);player.seek(float(manifest.get("time",0)),true)
			var bounds:=AABB();var first:=true
			for mesh: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
				var value:=model.global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
				bounds=value if first else bounds.merge(value);first=false
			var factor:=1.95/maxf(bounds.size.x,maxf(bounds.size.y,bounds.size.z))
			model.scale*=factor;model.position=-bounds.get_center()*factor+Vector3(0,1.18,0)
			pivot.rotation_degrees.y=[180,90,135][col]
			var text:=Label3D.new();text.text=str(rows[row].name)+" / "+["front","side","three-quarter"][col]
			text.position=Vector3((col-1)*2.6,(rows.size()-1-row)*2.7+.05,1.3);text.font_size=28;text.pixel_size=.0043;text.no_depth_test=true;stage.add_child(text)
	for i in 8:await process_frame
	await RenderingServer.frame_post_draw
	var out:=str(manifest.output);DirAccess.make_dir_recursive_absolute(out.get_base_dir())
	var error:=root.get_texture().get_image().save_png(out)
	print("FORGE_GALLERY ",out," ",error);quit(error)
