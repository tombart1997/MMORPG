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
static var camp_cells: Dictionary = {}
var scenery: RemasterScenery

static func nearby_camps(x: float,z: float) -> Array:
	if camp_cells.is_empty():
		for point in FirstMapContent.POINTS:
			var key := Vector2i(floori(point.x/32),floori(point.z/32))
			if not camp_cells.has(key): camp_cells[key] = []
			camp_cells[key].append(point)
	var cell := Vector2i(floori(x/32),floori(z/32))
	var result: Array = []
	for i in range(-1,2):
		for j in range(-1,2): result.append_array(camp_cells.get(cell+Vector2i(i,j),[]))
	return result

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
	for camp in nearby_camps(x,z):
		clearance = minf(clearance, point.distance_to(camp) - 8)
	clearance = minf(clearance, point.distance_to(START) - 5)
	# Broad landforms independent of placement: rolling shoulders, a central saddle,
	# western low ground, and taller boundary ridges. Paths/camp floors remain level.
	var rolling := 2.4+1.7*sin(x*.047+z*.013)+1.3*cos(z*.055-x*.018)
	var shoulder := 4.0*exp(-pow((x-42)/21,2)-pow((z+43)/32,2))
	var edge := smoothstep(87,119,absf(x))*6
	var hollow := -1.3*exp(-pow((x+48)/22,2)-pow((z+105)/30,2))
	var erosion := sin(x*.28+sin(z*.11))*cos(z*.22)*.16
	var envelope := maxf(0,clearance)*.34
	return minf(envelope,maxf(.1,rolling+shoulder+edge+hollow))+smoothstep(1,6,clearance)*erosion

func _ready() -> void:
	rng.seed = 7823
	scenery = RemasterScenery.new()
	add_child(scenery)
	LandscapeMesh.build(self,BOUNDS,height_at,RemasterGround.weights,RemasterMaterials.terrain())
	LandscapeMesh.backdrop(self,BOUNDS,false,height_at)
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
	# Unequal terrain shoulders frame the first hunt instead of straight boulder rows.
	for feature in [[-3,-16,1.1,.25],[34,-39,1.4,-.5],[-43,-46,1.3,.8],[45,-69,1.6,-.4],[-14,-110,1.5,.25],[13,-157,1.7,-.6],[-10,-204,1.5,.4],[14,-251,1.9,-.4]]:
		var point := Vector3(feature[0],0,feature[1])
		point.y = height_at(point.x,point.z)-.3
		scenery.place("cliff",point,Vector3.ONE*feature[2],feature[3])
		for j in 3:
			var tree_point := point+Vector3(-4+j*3.5,0,-3.5)
			if path_distance(Vector3(tree_point.x,0,tree_point.z))<4: continue
			tree_point.y = height_at(tree_point.x,tree_point.z)
			scenery.plant_tree(tree_point,1.0+float(j)*.13,j*.8,j)
	# Natural outer limits, with no physics walls across the travel route.
	# A narrow slate shoulder separates the western lane from the wolf clearing.
	# Its open ends lead around the camp, preserving the actual southbound road.
	var lane_shoulder := Vector3(-91,height_at(-91,-77),-77)
	scenery.place("cliff1",lane_shoulder,Vector3(1,.65,.8),PI*.5)
	var shoulder_body := StaticBody3D.new()
	shoulder_body.position = lane_shoulder+Vector3.UP*.8
	var shoulder_collision := CollisionShape3D.new()
	var shoulder_shape := BoxShape3D.new()
	shoulder_shape.size = Vector3(1.8,1.6,8)
	shoulder_collision.shape = shoulder_shape
	shoulder_body.add_child(shoulder_collision)
	add_child(shoulder_body)
	for x in range(-118, 119, 5):
		for z in [-296, 62]: rock(Vector3(x, height_at(x, z), z), 3.0)
	for z in range(-296, 63, 5):
		for x in [-118, 118]: rock(Vector3(x, height_at(x, z), z), 3.0)
	# Spawn landmark: a standing stone and a small sheltered campfire.
	rock(START + Vector3(3, 0, 4), 1.0)
	for i in range(8):
		var angle := i * TAU / 8
		rock(START + Vector3(3 + sin(angle) * 0.55, 0, cos(angle) * 0.55), 0.2)
	var fire := PaintedCampfire.new()
	fire.position = START + Vector3(3, 0, 0)
	add_child(fire)
	add_child(BriarwakeGrove.new())
	# Landmarks visible from travel lanes, with distinct vertical silhouettes.
	for feature in [["watchtower",-10,0,1.0,0.0],["shrine",25,-12,1.0,.4],["shrine",26,-36,1.2,.2],["ruin_arch",35,-73,1.5,-.4],["shrine",-82,-125,1.3,.8],["ruin_arch",82,-211,1.8,.25]]:
		var point := Vector3(feature[1],0,feature[2])
		point.y = height_at(point.x,point.z)
		scenery.place(feature[0],point,Vector3.ONE*feature[3],feature[4])
	scenery.dress_ground()
	scenery.flush()

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
	scenery.plant_tree(point,size,rng.randf()*TAU,rng.randi_range(0,2))
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.16 * size
	trunk.bottom_radius = 0.26 * size
	trunk.height = 3.5 * size
	trunk.radial_segments = 6
	var node := prop(trunk, point + Vector3.UP * 1.75 * size, Color(0.22, 0.16, 0.1))
	node.create_convex_collision()
	node.hide() # Preserve the original navigation obstacle, replace only its art.

func rock(point: Vector3, size: float) -> void:
	var yaw := rng.randf()*TAU
	var kind := "rock%d" % rng.randi_range(0,2)
	scenery.place(kind,point-Vector3.UP*.08,Vector3(size,size*.8,size),yaw)
	if size > 0.4:
		# Preserve the old navigation envelope while replacing its visible surface.
		var body := StaticBody3D.new()
		var collision := CollisionShape3D.new()
		var shape := SphereShape3D.new()
		shape.radius = size
		collision.shape = shape
		collision.position.y = size*.45
		body.position = point
		body.add_child(collision)
		add_child(body)
