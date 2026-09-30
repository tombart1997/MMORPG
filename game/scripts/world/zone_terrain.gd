class_name ZoneTerrain
extends Node3D
## Small deterministic mesh terrain, level paths/clearings surrounded by low hills.
const CAMPS: Array[Vector3] = [Vector3(14, 0, -24), Vector3(-25, 0, -50), Vector3(26, 0, -82)]
const ROAD: Array[Vector3] = [Vector3(0, 0, 12), Vector3(0, 0, -4), Vector3(18, 0, -4), Vector3(18, 0, -20), Vector3(14, 0, -24), Vector3(14, 0, -32), Vector3(-6, 0, -32), Vector3(-25, 0, -43), Vector3(-25, 0, -50), Vector3(-25, 0, -62), Vector3(-4, 0, -62), Vector3(10, 0, -74), Vector3(26, 0, -82)]
const START := Vector3(0, 0, 12)
const FRACTURE := Vector3(-8, 0, -49)
const FARM_LOOP: Array[Vector3] = [Vector3(-25, 0, -50), FRACTURE, Vector3(-4, 0, -62)]
const BOUNDS := Rect2(-120, -298, 240, 362)
const OUTER_ROAD: Array[Vector3] = [Vector3(0,0,15),Vector3(0,0,-8),Vector3(-95,0,-8),Vector3(-95,0,-88),Vector3(95,0,-88),Vector3(95,0,-133),Vector3(-95,0,-133),Vector3(-95,0,-177),Vector3(95,0,-177),Vector3(95,0,-222),Vector3(-95,0,-222),Vector3(-95,0,-283)]
var rng := RandomNumberGenerator.new()

static func path_distance(point: Vector3) -> float:
	var distance := 100.0
	for i in range(1, OUTER_ROAD.size()):
		var segment := OUTER_ROAD[i] - OUTER_ROAD[i-1]
		var t := clampf((point-OUTER_ROAD[i-1]).dot(segment)/segment.length_squared(),0,1)
		distance = minf(distance,point.distance_to(OUTER_ROAD[i-1]+segment*t))
	for i in range(1, FARM_LOOP.size()):
		var segment := FARM_LOOP[i] - FARM_LOOP[i - 1]
		var t := clampf((point - FARM_LOOP[i - 1]).dot(segment) / segment.length_squared(), 0, 1)
		distance = minf(distance, point.distance_to(FARM_LOOP[i - 1] + segment * t))
	for i in range(1, ROAD.size()):
		var start := ROAD[i - 1]
		var segment := ROAD[i] - start
		var t := clampf((point - start).dot(segment) / segment.length_squared(), 0, 1)
		distance = minf(distance, point.distance_to(start + segment * t))
	return distance

static func height_at(x: float, z: float) -> float:
	var point := Vector3(x, 0, z)
	if absf(x) < 31 and z >= 5 and z <= 55: return 0
	var clearance := path_distance(point) - 2.5
	clearance = minf(clearance, point.distance_to(FRACTURE) - 10)
	for camp in CAMPS:
		clearance = minf(clearance, point.distance_to(camp) - 5)
	for camp in FirstMapContent.POINTS:
		clearance = minf(clearance, point.distance_to(camp) - 8)
	clearance = minf(clearance, point.distance_to(START) - 5)
	return minf(4.5, maxf(0, clearance) * (0.24 + 0.10 * sin(x * 0.18) * cos(z * 0.13)))

func _ready() -> void:
	rng.seed = 7823
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for x in range(-120, 120, 2):
		for z in range(-298, 64, 2):
			for corner in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1),
				Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]:
				var px: float = float(x) + corner.x * 2
				var pz: float = float(z) + corner.y * 2
				var dirt := path_distance(Vector3(px, 0, pz)) < 1.6
				var color := Color(0.39, 0.32, 0.2) if dirt else Color(0.20, 0.29, 0.17).lerp(Color(0.28, 0.29, 0.24), clampf(-pz / 110.0, 0, 1))
				color *= 0.94 + 0.08 * sin(px * 1.7 + pz * 0.7)
				surface.set_color(color)
				surface.add_vertex(Vector3(px, height_at(px, pz), pz))
	surface.generate_normals()
	var ground := MeshInstance3D.new()
	ground.mesh = surface.commit()
	var material := ShaderMaterial.new()
	material.shader = load("res://assets/benchmark/forest_floor.gdshader")
	material.set_shader_parameter("soil_color", load("res://assets/benchmark/textures/soil_color.png"))
	material.set_shader_parameter("soil_normal", load("res://assets/benchmark/textures/soil_normal.png"))
	ground.material_override = material
	add_child(ground)
	ground.create_trimesh_collision()
	for i in range(550):
		var point := Vector3(rng.randf_range(-114, 114), 0, rng.randf_range(-291, 58))
		if path_distance(point) < 4 or (absf(point.x) < 32 and point.z > 4 and point.z < 56):
			continue
		if point.distance_to(FRACTURE) < 25: continue
		var clear := true
		for camp in CAMPS:
			if point.distance_to(camp) < 6:
				clear = false
		for camp in FirstMapContent.POINTS:
			if point.distance_to(camp) < 10: clear = false
		if not clear:
			continue
		point.y = height_at(point.x, point.z)
		if i % 3 == 0:
			rock(point, rng.randf_range(0.6, 1.4))
		else:
			tree(point, rng.randf_range(0.85, 1.4))
	# Deliberate ridges block views between districts; openings follow the bent road.
	for row in [-12, -40, -67]:
		for x in range(-48, 49, 5):
			var point := Vector3(x, 0, row)
			if point.distance_to(FRACTURE) < 25: continue
			if path_distance(point) < 5: continue
			point.y = height_at(point.x, point.z)
			rock(point, 3.3)
			if x % 2 == 0: tree(point + Vector3(1, 0, 1), 1.5)
	# Natural outer limits, with no physics walls across the travel route.
	for x in range(-118, 119, 5):
		for z in [-296, 62]: rock(Vector3(x, height_at(x, z), z), 3.0)
	for z in range(-296, 63, 5):
		for x in [-118, 118]: rock(Vector3(x, height_at(x, z), z), 3.0)
	# Spawn landmark: a standing stone and a small sheltered campfire.
	rock(START + Vector3(3, 0, 4), 1.0)
	for i in range(8):
		var angle := i * TAU / 8
		rock(START + Vector3(3 + sin(angle) * 0.55, 0, cos(angle) * 0.55), 0.2)
	var fire := OmniLight3D.new()
	fire.position = START + Vector3(3, 0.6, 0)
	fire.light_color = Color(1, 0.55, 0.2)
	fire.light_energy = 2
	fire.omni_range = 5
	add_child(fire)
	var flame := SphereMesh.new()
	flame.radius = 0.25
	flame.height = 0.7
	var flame_node := prop(flame, fire.position, Color(1, 0.45, 0.1))
	flame_node.material_override.emission_enabled = true
	flame_node.material_override.emission = Color(1, 0.35, 0.05)
	add_child(BriarwakeGrove.new())

func prop(mesh: Mesh, location: Vector3, color: Color) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = location
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 1.0
	node.material_override = material
	add_child(node)
	return node

func tree(point: Vector3, size: float) -> void:
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.16 * size
	trunk.bottom_radius = 0.26 * size
	trunk.height = 3.5 * size
	trunk.radial_segments = 6
	var node := prop(trunk, point + Vector3.UP * 1.75 * size, Color(0.22, 0.16, 0.1))
	node.create_convex_collision()
	for layer in range(3):
		var leaves := CylinderMesh.new()
		leaves.top_radius = 0
		leaves.bottom_radius = (1.7 - layer * 0.35) * size
		leaves.height = 2.2 * size
		leaves.radial_segments = 7
		prop(leaves, point + Vector3.UP * (2.5 + layer * 0.8) * size,
			Color(0.12 + layer * 0.025, 0.24 + layer * 0.025, 0.15))

func rock(point: Vector3, size: float) -> void:
	var stone := SphereMesh.new()
	stone.radius = size
	stone.height = size * 1.4
	stone.radial_segments = 7
	stone.rings = 3
	var node := prop(stone, point + Vector3.UP * size * 0.45, Color(0.36, 0.38, 0.32))
	node.rotation.y = rng.randf() * TAU
	if size > 0.4:
		node.create_convex_collision()
