extends SceneTree
## Identical source/candidate cameras, actual Godot materials and sampled skins.
var viewport: SubViewport
var stage: Node3D
var camera: Camera3D
var caption: Label
var model: Node3D
var players: Array[AnimationPlayer] = []
var meshes: Array[MeshInstance3D] = []
var original_meshes: Array[Mesh] = []
var wire_meshes: Array[Mesh] = []
var bounds: AABB
var clay: StandardMaterial3D
var wire: ShaderMaterial
var reports: Array = []

func _initialize() -> void:
	call_deferred("run")

func capture(text: String) -> Image:
	caption.text=text
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	return viewport.get_texture().get_image()

func mode(kind: String) -> void:
	for i in meshes.size():
		meshes[i].mesh=wire_meshes[i] if kind=="wire" else original_meshes[i]
		meshes[i].material_override=wire if kind=="wire" else clay if kind=="clay" else null

func angle_view(angle: float, size_factor: float=1.0, focus: Vector3=Vector3.INF) -> void:
	var center:=bounds.get_center() if focus==Vector3.INF else focus
	var extent:=maxf(bounds.size.x,maxf(bounds.size.y,bounds.size.z))
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=extent*1.22*size_factor
	camera.position=center+Vector3(sin(angle)*extent*3,extent*.12,cos(angle)*extent*3)
	camera.look_at(center)

func gameplay_view() -> void:
	camera.projection=Camera3D.PROJECTION_PERSPECTIVE;camera.fov=55
	var center:=bounds.get_center()
	camera.position=center+Vector3(3,3,-10)
	camera.look_at(center)

func sample(clip: String, fraction: float) -> void:
	for p in players:
		if p.has_animation(clip):p.play(clip);p.seek(p.get_animation(clip).length*fraction,true)

func prepare(entry: Dictionary) -> void:
	if is_instance_valid(model):stage.remove_child(model);model.free()
	players.clear();meshes.clear();original_meshes.clear();wire_meshes.clear()
	model=Node3D.new();stage.add_child(model)
	var content: Node3D=(load(entry.path) as PackedScene).instantiate();model.add_child(content)
	# Inspection-only orientation; runtime pivots and attachment transforms stay intact.
	if entry.has("inspection_rotation"):
		content.rotation=Vector3(entry.inspection_rotation[0],entry.inspection_rotation[1],entry.inspection_rotation[2])
	for p: AnimationPlayer in model.find_children("*","AnimationPlayer",true,false):
		p.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL;players.append(p)
	sample("idle",0)
	var first:=true
	for mesh: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		var value:=model.global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
		bounds=value if first else bounds.merge(value);first=false
		meshes.append(mesh);original_meshes.append(mesh.mesh)
		var rebuilt:=ArrayMesh.new()
		for s in mesh.mesh.get_surface_count():
			var tool:=SurfaceTool.new();tool.create_from(mesh.mesh,s);tool.deindex();tool.commit(rebuilt)
		wire_meshes.append(rebuilt)
	if not String(entry.get("pair_with","")).is_empty():
		for prior: Dictionary in reports:
			if prior.key==entry.pair_with:entry.framing_bounds=prior.framing_bounds
	if entry.has("framing_bounds"):bounds=AABB(Vector3(entry.framing_bounds[0][0],entry.framing_bounds[0][1],entry.framing_bounds[0][2]),Vector3(entry.framing_bounds[1][0],entry.framing_bounds[1][1],entry.framing_bounds[1][2]))

func sheet(entry: Dictionary) -> void:
	prepare(entry)
	var atlas:=Image.create(1280,1600,false,Image.FORMAT_RGBA8)
	var angles: Array[float]=[PI,PI/2,0,PI*.75]
	var names: Array[String]=["front","side","back","three-quarter"]
	for row in 3:
		var kind: String=["textured","clay","wire"][row];mode(kind)
		for col in 4:
			angle_view(angles[col]);atlas.blit_rect(await capture(kind+" / "+names[col]),Rect2i(0,0,320,320),Vector2i(col*320,row*320))
	mode("textured")
	var detail:=bounds.position+Vector3(bounds.size.x*.5,bounds.size.y*.8,bounds.size.z*.5)
	if entry.has("detail_center"):detail=Vector3(entry.detail_center[0],entry.detail_center[1],entry.detail_center[2])
	for col in 2:
		angle_view(angles[col],.38,detail);atlas.blit_rect(await capture("detail / "+names[col]),Rect2i(0,0,320,320),Vector2i(col*320,960))
	gameplay_view();atlas.blit_rect(await capture("gameplay / 11 m"),Rect2i(0,0,320,320),Vector2i(640,960))
	var ref:=Image.new()
	if ref.load(str(entry.get("reference","")))==OK:
		ref.convert(Image.FORMAT_RGBA8)
		var factor:=minf(320.0/ref.get_width(),320.0/ref.get_height());ref.resize(int(ref.get_width()*factor),int(ref.get_height()*factor),Image.INTERPOLATE_LANCZOS)
		atlas.blit_rect(ref,Rect2i(Vector2i.ZERO,ref.get_size()),Vector2i(960+(320-ref.get_width())/2,960+(320-ref.get_height())/2))
	for col in 4:
		mode("textured");sample("run",float(col)*.25)
		if players.is_empty():angle_view(angles[col]);camera.size*=1.8
		else:angle_view(PI*.75)
		atlas.blit_rect(await capture("run / "+str(col*25)+"%" if not players.is_empty() else "gameplay angle / "+names[col]),Rect2i(0,0,320,320),Vector2i(col*320,1280))
	DirAccess.make_dir_recursive_absolute(String(entry.output).get_base_dir())
	atlas.save_png(entry.output)
	var record: Dictionary={"key":entry.key,"output":entry.output,"path":entry.path,"framing_bounds":[[bounds.position.x,bounds.position.y,bounds.position.z],[bounds.size.x,bounds.size.y,bounds.size.z]],"clips":[],"status":"rendered_requires_visual_review","camera_contract":"4 orthographic angles; unchanged physical scale; identical paired framing; gameplay at 11m; 320px tiles"}
	if not players.is_empty():
		var clips: Array[String]=[]
		for name in players[0].get_animation_list():
			if name!="RESET":clips.append(String(name))
		record.clips=clips
		var animation_atlas:=Image.create(1280,320*clips.size(),false,Image.FORMAT_RGBA8)
		for row in clips.size():
			for col in 4:
				sample(clips[row],float(col)*.25);angle_view(PI*.75)
				animation_atlas.blit_rect(await capture(clips[row]+" / "+str(col*25)+"%"),Rect2i(0,0,320,320),Vector2i(col*320,row*320))
		animation_atlas.save_png(String(entry.output).trim_suffix(".png")+"_animation.png")
	reports.append(record)
	print("REVIEW_RENDERED ",entry.key)

func run() -> void:
	var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	root.size=Vector2i(480,360)
	viewport=SubViewport.new();viewport.size=Vector2i(320,320);viewport.own_world_3d=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	stage=Node3D.new();viewport.add_child(stage)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color("56616b");env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("e2e7ed");env.ambient_light_energy=.65
	var world:=WorldEnvironment.new();world.environment=env;stage.add_child(world)
	for spec in [[Vector3(-35,-25,0),1.2],[Vector3(-25,140,0),.5]]:
		var light:=DirectionalLight3D.new();light.rotation_degrees=spec[0];light.light_energy=spec[1];stage.add_child(light)
	camera=Camera3D.new();stage.add_child(camera);camera.current=true
	caption=Label.new();caption.position=Vector2(8,294);caption.add_theme_font_size_override("font_size",14);viewport.add_child(caption)
	clay=StandardMaterial3D.new();clay.albedo_color=Color(.58,.60,.62);clay.roughness=.85
	wire=ShaderMaterial.new();wire.shader=Shader.new();wire.shader.code="shader_type spatial; render_mode unshaded, cull_disabled; varying vec3 bary; void vertex(){int i=VERTEX_ID%3;bary=i==0?vec3(1,0,0):(i==1?vec3(0,1,0):vec3(0,0,1));} void fragment(){vec3 edge=smoothstep(vec3(0),fwidth(bary)*1.2,bary);ALBEDO=mix(vec3(.82,.86,.9),vec3(.07,.09,.1),min(edge.x,min(edge.y,edge.z)));}"
	for entry: Dictionary in request.assets:await sheet(entry)
	var file:=FileAccess.open(request.report,FileAccess.WRITE);file.store_string(JSON.stringify({"assets":reports},"\t"));file.close()
	quit(0)
