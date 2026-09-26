extends SceneTree

var meshes := 0
var surfaces := 0
var triangles := 0
var missing_materials := 0
var bounds := AABB()
var first := true

func walk(node: Node) -> void:
	if node is MeshInstance3D:
		meshes += 1
		var instance := node as MeshInstance3D
		var box := instance.global_transform * instance.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
		for surface in instance.mesh.get_surface_count():
			surfaces += 1
			var arrays := instance.mesh.surface_get_arrays(surface)
			var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			triangles += indices.size() / 3 if not indices.is_empty() else arrays[Mesh.ARRAY_VERTEX].size() / 3
			if instance.get_active_material(surface) == null:
				missing_materials += 1
	for child in node.get_children():
		walk(child)

func _initialize() -> void:
	call_deferred("verify")

func verify() -> void:
	var packed = load("res://sword.glb")
	if not packed is PackedScene:
		push_error("GLB did not import as a PackedScene")
		quit(1)
		return
	var stage := Node3D.new()
	root.add_child(stage)
	var sword: Node3D = packed.instantiate()
	stage.add_child(sword)
	walk(sword)
	var report := {"engine": Engine.get_version_info().string, "meshes": meshes,
		"surfaces": surfaces, "triangles": triangles, "missing_materials": missing_materials,
		"bounds_position": [bounds.position.x,bounds.position.y,bounds.position.z],
		"bounds_size": [bounds.size.x,bounds.size.y,bounds.size.z]}
	var file := FileAccess.open("res://../output/godot_validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  "))
	file.close()
	print(JSON.stringify(report))
	if meshes < 1 or triangles < 1 or missing_materials > 0:
		quit(1)
		return
	if "--capture" not in OS.get_cmdline_user_args():
		quit(0)
		return
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.18,0.18,0.18)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.75,0.78,0.82)
	env.environment.ambient_light_energy = 0.65
	# Metals require an environment to reflect; fixed gray background remains neutral.
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.45,0.48,0.52)
	sky_material.sky_horizon_color = Color(0.7,0.7,0.7)
	sky_material.ground_bottom_color = Color(0.16,0.16,0.16)
	sky_material.ground_horizon_color = Color(0.5,0.5,0.5)
	sky.sky_material = sky_material
	env.environment.sky = sky
	env.environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	stage.add_child(env)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-30,-35,0)
	key.light_energy = 1.8
	stage.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(20,140,0)
	fill.light_energy = 0.7
	stage.add_child(fill)
	var camera := Camera3D.new()
	stage.add_child(camera)
	camera.current = true
	var center := bounds.get_center()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 1.42
	camera.position = center + Vector3(0.5,0.1,3)
	camera.look_at(center)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../output/previews/godot_close.png")
	camera.projection = Camera3D.PROJECTION_PERSPECTIVE
	camera.fov = 60
	camera.position = center + Vector3(0,3.0,7.42)
	camera.look_at(center)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../output/previews/godot_8m.png")
	quit(0)
