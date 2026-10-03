class_name Settlement
extends Node3D
var npcs: Array[WorldNPC] = []
var dressing: RemasterScenery

func _ready() -> void:
	name = "WaystoneRefuge"
	dressing = RemasterScenery.new()
	add_child(dressing)
	_house(Vector3(-6, 0, 9), Color(0.57, 0.44, 0.29), "Trail Supplies")
	_house(Vector3(6, 0, 11), Color(0.49, 0.46, 0.32), "The Pine Rest")
	_house(Vector3(-5, 0, 23), Color(0.48, 0.40, 0.3), "Warden's Lodge")
	for spec in [[Vector3(-20,0,18),"Weaponry"],[Vector3(20,0,18),"Armory"],[Vector3(-20,0,32),"Apothecary"],[Vector3(20,0,32),"Stables"],[Vector3(-12,0,46),"Relic Workshop"],[Vector3(12,0,46),"Guild Hall"],[Vector3(-27,0,45),"Weaver's Home"],[Vector3(27,0,45),"Watch House"]]:
		_house(spec[0], Color(.53,.45,.33), spec[1])
	for spec in [[Vector3(0,.015,32),Vector3(5,.02,48)],[Vector3(0,.02,22),Vector3(43,.02,3)],[Vector3(0,.02,36),Vector3(43,.02,3)],[Vector3(0,.02,48),Vector3(30,.02,3)]]:
		_box(spec[0],spec[1],Color(.4,.33,.23))
	# Market square, broad lanes, small stalls and well remain traversable.
	for x in [-9,9]:
		for z in [30,37]:
			_box(Vector3(x,.6,z),Vector3(3,1.2,1),Color(.32,.22,.13),true)
			_box(Vector3(x,2.6,z),Vector3(3.5,.15,2),Color(.34,.43,.42))
			for side in [-1,1]:
				_box(Vector3(x+side*1.5,1.3,z+.6),Vector3(.12,2.6,.12),Color(.3,.22,.14))
	_box(Vector3(5,.4,42),Vector3(1.8,.8,1.8),Color(.4,.42,.4),true)
	# A market canopy and counter, open on the road-facing side.
	_box(Vector3(-3.5, 0.55, 13.8), Vector3(2.6, 1.1, 0.65), Color(0.30, 0.20, 0.12), true)
	_box(Vector3(-3.5, 2.55, 14), Vector3(3.2, 0.15, 2.0), Color(0.53, 0.25, 0.13))
	for x in [-4.8, -2.2]: _box(Vector3(x, 1.3, 14.5), Vector3(0.12, 2.6, 0.12), Color(0.26, 0.18, 0.10))
	for x in [-7, 7]:
		for z in range(7, 23, 2):
			_box(Vector3(x, 0.65, z), Vector3(0.16, 1.3, 0.16), Color(0.32, 0.24, 0.15))
		_box(Vector3(x, 0.8, 14), Vector3(0.1, 0.12, 15), Color(0.36, 0.27, 0.17))
	# Gate frames the visible northbound hunting road, without blocking it.
	for x in [-2.5, 2.5]: _box(Vector3(x, 1.65, 5.5), Vector3(0.4, 3.3, 0.4), Color(0.32, 0.24, 0.15), true)
	_box(Vector3(0, 3.3, 5.5), Vector3(5.5, 0.3, 0.35), Color(0.32, 0.24, 0.15))
	_sign(Vector3(0, 3.7, 5.5), "BRIARWOOD MARCH")
	_sign(Vector3(-2.9, 1.7, 6.5), "North: Briar Crossing\nThen west: Old Pine Hollow\nDeep east: Broken Cairn")
	for spec in [["mara", Vector3(-3.4, 0, 12.1)], ["warden", Vector3(2.8, 0, 8.3)], ["keeper", Vector3(1.7, 0, 17)], ["smith", Vector3(-3.4, 0, 19)]]:
		var npc := WorldNPC.new()
		npc.data = load("res://data/npcs/" + spec[0] + ".tres")
		npc.position = spec[1]
		npc.name = spec[0]
		add_child(npc)
		npcs.append(npc)
	for spec in [["weapons",Vector3(-16,0,18)],["armorer",Vector3(16,0,18)],["apothecary",Vector3(-16,0,32)],["stablemaster",Vector3(16,0,32)],["artificer",Vector3(-8,0,46)]]:
		var npc := WorldNPC.new()
		npc.data = load("res://data/npcs/"+spec[0]+".tres")
		npc.position = spec[1]
		npc.name = spec[0]
		add_child(npc)
		npcs.append(npc)
	_box(Vector3(-3.4, 0.6, 20), Vector3(1.3, 1.2, 0.7), Color(0.23, 0.26, 0.27), true)
	# Local paths tie buildings and the market to the road.
	for spec in [[Vector3(0, 0.012, 18), Vector3(3, 0.02, 13)], [Vector3(-2.5, 0.013, 9), Vector3(7, 0.02, 2)], [Vector3(3, 0.014, 11), Vector3(6, 0.02, 2)]]:
		_box(spec[0], spec[1], Color(0.40, 0.33, 0.22))

	dressing.flush()

func _house(point: Vector3, color: Color, title: String) -> void:
	_box(point + Vector3(0, 1.4, 0), Vector3(3.8, 2.8, 3.6), color, true)
	var mesh := MeshInstance3D.new()
	mesh.mesh = _roof()
	mesh.position = point + Vector3(0,2.8,0)
	mesh.material_override = RemasterMaterials.surface(8)
	mesh.visibility_range_end = 90
	add_child(mesh)
	_box(point+Vector3(0,.17,0),Vector3(4.1,.34,3.9),Color("77786c"))
	for z in [-1.86,1.86]:
		for x in [-.9,.9]:
			_box(point+Vector3(x,1.35,z),Vector3(.07,2.4,.07),Color("392c20"))
		_box(point+Vector3(0,1.2,z),Vector3(3.9,.08,.07),Color("392c20"))
	for x in [-2.65,2.65]: _box(point+Vector3(x,3.05,0),Vector3(.12,.15,4.7),Color("493b2b"))
	_box(point+Vector3(0,4.13,0),Vector3(.15,.15,4.6),Color("413e33"))
	for side_value in [-1,1]:
		dressing.place("crate",point+Vector3(side_value*2.2,0,1.3),Vector3.ONE*.75)
		dressing.place("log",point+Vector3(side_value*2.3,.05,-1.4),Vector3(.7,.7,.7),PI/2)
	for x in [-1.9, 1.9]:
		for z in [-1.75, 1.75]:
			_box(point + Vector3(x, 1.5, z), Vector3(0.17, 3.0, 0.17), Color("32251d"))
	for y in [0.22, 2.75]:
		for z in [-1.81, 1.81]:
			_box(point + Vector3(0, y, z), Vector3(3.9, 0.15, 0.12), Color("38291e"))
	var chimney := CylinderMesh.new()
	chimney.top_radius = 0.25
	chimney.bottom_radius = 0.28
	chimney.height = 1.1
	chimney.radial_segments = 6
	var vent := MeshInstance3D.new()
	vent.mesh = chimney
	vent.position = point + Vector3(0.95, 4.0, 0.6)
	var soot := StandardMaterial3D.new()
	soot.albedo_color = Color("4b4945")
	vent.material_override = RemasterMaterials.surface(4)
	vent.visibility_range_end = 65
	add_child(vent)
	var side := -signf(point.x)
	_box(point + Vector3(side * 1.91, 0.95, 0), Vector3(0.05, 1.9, 0.8), Color(0.20, 0.13, 0.08))
	_box(point + Vector3(side * 1.98, 1.9, 0), Vector3(0.16, 0.16, 1.25), Color("b78b51"))
	for z in [-1.1, 1.1]: _window(point + Vector3(side * 1.93, 1.65, z),side)
	_sign(point + Vector3(side * 1.95, 2.6, 0), title)

func _sign(point: Vector3, text: String) -> void:
	var label := Label3D.new()
	label.text = text
	label.position = point
	label.font_size = 23
	label.pixel_size = 0.006
	label.modulate = Color(0.95, 0.84, 0.6)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.visibility_range_end = 22
	add_child(label)

func _box(point: Vector3, dimensions: Vector3, color: Color, collision: bool = false) -> void:
	if dimensions.y < .05: return # Ground shader blends these same travel lanes.
	var mesh := BoxMesh.new()
	mesh.size = dimensions
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = point
	var index := 7 if dimensions.y > 2 and dimensions.x > 3 else (4 if color.b > color.r*.95 else 6)
	node.material_override = RemasterMaterials.surface(index,Color("b2b0a3") if index == 7 else Color("c3b7a4"))
	node.visibility_range_end = 90
	add_child(node)
	if collision: node.create_trimesh_collision()

func _window(point: Vector3,side: float) -> void:
	_box(point,Vector3(.055,.75,.65),Color("201e18"))
	for z in [-.3,0,.3]: _box(point+Vector3(side*.035,0,z),Vector3(.08,.8,.055),Color("59432c"))
	for y in [-.35,0,.35]: _box(point+Vector3(side*.04,y,0),Vector3(.08,.05,.65),Color("59432c"))

func _roof() -> ArrayMesh:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var xs := [0.0,1.1,2.2,2.7]
	var ys := [1.3,.6,.1,.26]
	var zs := [-2.3,-1.5,0.0,1.5,2.3]
	for side in [-1,1]:
		var corners := [Vector2i(0,0),Vector2i(0,1),Vector2i(1,0),Vector2i(1,0),Vector2i(0,1),Vector2i(1,1)]
		if side>0: corners.reverse()
		for i in 3:
			for j in 4:
				for uv in corners:
					var x:float=xs[i+uv.x]*side
					var z:float=zs[j+uv.y]
					var y:float=ys[i+uv.x]+pow(absf(z)/2.3,4)*.15
					surface.set_uv(Vector2(x*.5,z*.5))
					surface.add_vertex(Vector3(x,y,z))
	surface.generate_normals()
	var roof := surface.commit()
	return roof
