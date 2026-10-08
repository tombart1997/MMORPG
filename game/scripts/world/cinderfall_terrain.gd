class_name CinderfallTerrain
extends Node3D
## Authored ash basin. Existing encounter floors, central lane and outpost stay level.
const BOUNDS := Rect2(-75,-75,150,150)
const CAMPS := [Vector3(-28,0,13),Vector3(27,0,-15),Vector3(-23,0,-50),Vector3(23,0,-70)]
const ROAD := [Vector2(0,62),Vector2(0,48),Vector2(0,28),Vector2(-6,8),Vector2(5,-22),Vector2(0,-48),Vector2(0,-72)]
var dressing: RemasterScenery

static func road_distance(x: float,z: float) -> float:
	var p := Vector2(x,z)
	var distance := 100.0
	for i in range(1,ROAD.size()): distance = minf(distance,RemasterGround.distance_segment(p,ROAD[i-1],ROAD[i]))
	for camp in CAMPS: distance = minf(distance,RemasterGround.distance_segment(p,Vector2(0,camp.z),Vector2(camp.x,camp.z)))
	return distance

static func height_at(x: float,z: float) -> float:
	var clearance := road_distance(x,z)-3.0
	clearance = minf(clearance,Vector2(x,z).distance_to(Vector2(0,48))-12)
	clearance = minf(clearance,Vector2(x,z).distance_to(Vector2(5,46))-6)
	for camp in CAMPS: clearance = minf(clearance,Vector2(x,z).distance_to(Vector2(camp.x,camp.z))-10)
	var mass := 3.0+2.2*sin(x*.075+z*.021)+1.8*cos(z*.06-x*.014)
	var edge := smoothstep(45,74,absf(x))*7.0
	return minf(maxf(0,clearance)*.38,maxf(.3,mass+edge))

static func weights(x: float,z: float) -> Color:
	return Color(clampf(road_distance(x,z)/20,0,1),1.0-smoothstep(-25,25,z),0,1)

func _ready() -> void:
	dressing = RemasterScenery.new()
	add_child(dressing)
	var material := ShaderMaterial.new()
	material.shader = load("res://assets/shaders/cinder_ground.gdshader")
	material.set_shader_parameter("rock",RemasterMaterials.texture(4))
	material.set_shader_parameter("earth",RemasterMaterials.texture(5))
	LandscapeMesh.build(self,BOUNDS,height_at,weights,material)
	LandscapeMesh.backdrop(self,BOUNDS,true,height_at)
	var rng := RandomNumberGenerator.new()
	rng.seed = 104927
	for spec in [[-51,35,2.3,.2],[48,27,2.1,-.6],[-52,-3,2.4,.4],[53,-37,2.6,-.3],[-52,-53,2.5,.5],[46,-63,1.8,-.4]]:
		_place("cliff",Vector3(spec[0],0,spec[1]),Vector3.ONE*spec[2],spec[3])
	for i in 95:
		var point := Vector3(rng.randf_range(-68,68),0,rng.randf_range(-71,68))
		if road_distance(point.x,point.z)<5 or point.distance_to(Vector3(0,0,48))<15: continue
		var clear := true
		for camp in CAMPS:
			if point.distance_to(camp)<11: clear = false
		if not clear: continue
		var size_value := rng.randf_range(.5,1.45)
		var rock_scale := Vector3(size_value,size_value*rng.randf_range(.8,1.7),size_value)
		var rock_yaw := rng.randf()*TAU
		_place("rock%d" % (i%3),point,rock_scale,rock_yaw)
		if size_value>1.1:
			var body := StaticBody3D.new()
			body.position = Vector3(point.x,height_at(point.x,point.z)-.05,point.z)
			body.rotation.y = rock_yaw
			var collision := CollisionShape3D.new()
			var shape := ConvexPolygonShape3D.new()
			var vertices := WorldAssetKit.mesh_for("rock%d" % (i%3)).get_faces()
			for j in vertices.size(): vertices[j] *= rock_scale
			shape.points = vertices
			collision.shape = shape
			body.add_child(collision)
			add_child(body)
		if i%9==0: _place("dead_tree",point+Vector3(1.2,0,1),Vector3.ONE*rng.randf_range(.7,1.25),rng.randf()*TAU)
	# Continuous collision boundary, irregular visual buttresses with exposed slopes between.
	for z in range(-70,71,13):
		for x in [-73,73]:
			_boundary(Vector3(x,0,z),Vector3(3,8,14))
			if (z+70)%26 == 0:
				_place("cliff1" if z%3 else "cliff",Vector3(x,0,z),Vector3(1.7,1.1+.5*sin(z),1.2),PI*.5+.15*sin(z))
	for x in range(-65,66,13):
		for z in [-74,74]:
			_boundary(Vector3(x,0,z),Vector3(14,8,3))
			if (x+65)%26 == 0:
				_place("cliff1",Vector3(x,0,z),Vector3(1.7,1.3+.4*cos(x),1.2),.1*cos(x))
	_place("ruin_arch",Vector3(35,0,-32),Vector3.ONE*2.0,-.3)
	_place("shrine",Vector3(-35,0,-36),Vector3.ONE*1.9,.35)
	_place("watchtower",Vector3(-12,0,40),Vector3.ONE*.85,0)
	for camp in CAMPS:
		for side in [-1,1]:
			_place("dead_tree",camp+Vector3(side*8,0,-5),Vector3.ONE*.9,side*.5)
			_place("rock1",camp+Vector3(side*7,0,5),Vector3(1.4,.8,1.1),side*.7)
	for i in 550:
		var point := Vector3(rng.randf_range(-69,69),0,rng.randf_range(-70,69))
		if point.distance_to(Vector3(0,0,48))<12: continue
		var road := road_distance(point.x,point.z)
		if road<2 or road>12: continue
		_place("rock0",point,Vector3.ONE*rng.randf_range(.06,.20),rng.randf()*TAU)
	_outpost()
	dressing.flush()
	for batch: MultiMeshInstance3D in dressing.get_children():
		if batch.name.begins_with("rock") or batch.name.begins_with("cliff"):
			batch.material_override = RemasterMaterials.camera_clearance(RemasterMaterials.surface(4,Color("6c6064")))
		elif batch.name == "dead_tree": batch.material_override = RemasterMaterials.surface(6,Color("5d5557"))
	var beacon := OmniLight3D.new()
	beacon.position = Vector3(-3,1.5,43)
	beacon.light_color = Color("ee8954")
	beacon.light_energy = .8
	beacon.omni_range = 8
	add_child(beacon)

func _place(kind: String,point: Vector3,size_value: Vector3,yaw: float) -> void:
	point.y = height_at(point.x,point.z)-.05
	dressing.place(kind,point,size_value,yaw)

func _boundary(point: Vector3, dimensions: Vector3) -> void:
	var body := StaticBody3D.new()
	body.position = point+Vector3.UP*(height_at(point.x,point.z)+2.0)
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = dimensions
	collision.shape = shape
	body.add_child(collision)
	add_child(body)

func _outpost() -> void:
	for side in [-1,1]:
		_place("shrine",Vector3(side*7,0,51),Vector3.ONE*.8,0)
		_place("crate",Vector3(side*6,0,45),Vector3.ONE,side*.4)
	_place("tent",Vector3(-8,0,46),Vector3.ONE*1.7,PI*.5)
	_place("banner",Vector3(-8,0,49),Vector3.ONE*.85,0)
	var fire := PaintedCampfire.new()
	fire.position = Vector3(-3,0,43)
	add_child(fire)
