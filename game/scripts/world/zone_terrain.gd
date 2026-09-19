class_name ZoneTerrain
extends Node3D
## Small deterministic mesh terrain, level paths/clearings surrounded by low hills.
const CAMPS: Array[Vector3] = [Vector3(0, 0, 0), Vector3(-13, 0, -11), Vector3(14, 0, -17)]
const START := Vector3(0, 0, 12)
var rng := RandomNumberGenerator.new()

static func path_distance(point: Vector3) -> float:
	var distance := 100.0
	for end in CAMPS:
		var start := START if end == CAMPS[0] else CAMPS[0]
		var segment := end - start
		var t := clampf((point - start).dot(segment) / segment.length_squared(), 0, 1)
		distance = minf(distance, point.distance_to(start + segment * t))
	return distance

static func height_at(x: float, z: float) -> float:
	var point := Vector3(x, 0, z)
	var clearance := path_distance(point) - 2.5
	for camp in CAMPS:
		clearance = minf(clearance, point.distance_to(camp) - 5)
	clearance = minf(clearance, point.distance_to(START) - 5)
	return maxf(0, clearance) * (0.12 + 0.06 * sin(x * 0.28) * cos(z * 0.23))

func _ready() -> void:
	rng.seed = 7823
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for x in range(-36, 36):
		for z in range(-36, 36):
			for corner in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1),
				Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]:
				var px: float = float(x) + corner.x
				var pz: float = float(z) + corner.y
				var dirt := path_distance(Vector3(px, 0, pz)) < 1.6
				var color := Color(0.39, 0.32, 0.2) if dirt else Color(0.23, 0.32, 0.16)
				color *= 0.94 + 0.08 * sin(px * 1.7 + pz * 0.7)
				surface.set_color(color)
				surface.add_vertex(Vector3(px, height_at(px, pz), pz))
	surface.generate_normals()
	var ground := MeshInstance3D.new()
	ground.mesh = surface.commit()
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	material.roughness = 1
	ground.material_override = material
	add_child(ground)
	ground.create_trimesh_collision()
	for i in range(80):
		var point := Vector3(rng.randf_range(-33, 33), 0, rng.randf_range(-33, 30))
		if path_distance(point) < 4 or point.distance_to(START) < 5:
			continue
		var clear := true
		for camp in CAMPS:
			if point.distance_to(camp) < 6:
				clear = false
		if not clear:
			continue
		point.y = height_at(point.x, point.z)
		if i % 3 == 0:
			rock(point, rng.randf_range(0.6, 1.4))
		else:
			tree(point, rng.randf_range(0.85, 1.4))
	# A ring of large rocks closes the playable zone without an invisible cliff.
	for i in range(64):
		var angle := i * TAU / 64
		var point := Vector3(sin(angle), 0, cos(angle)) * 33
		point.y = height_at(point.x, point.z)
		rock(point, 3.5)
	# Spawn landmark: a standing stone and a small sheltered campfire.
	rock(START + Vector3(-3, 0, 0), 1.0)
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
