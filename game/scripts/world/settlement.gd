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
			_place("market_stall",Vector3(x,0,z))
			_collision(Vector3(x,.6,z),Vector3(3,1.2,1))
	_place("well",Vector3(5,0,42))
	_collision(Vector3(5,.4,42),Vector3(1.8,.8,1.8))
	# A market canopy and counter, open on the road-facing side.
	_place("market_stall",Vector3(-3.5,0,14),Vector3(.88,1,.88))
	_collision(Vector3(-3.5,.55,13.8),Vector3(2.6,1.1,.65))
	for x in [-7, 7]:
		for z in range(7, 23, 2):
			_place("fence",Vector3(x,0,z+1))
	# Gate frames the visible northbound hunting road, without blocking it.
	_place("gate",Vector3(0,0,5.5))
	for x in [-2.5,2.5]:_collision(Vector3(x,1.65,5.5),Vector3(.4,3.3,.4))
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
	_place("anvil",Vector3(-3.4,0,20))
	_collision(Vector3(-3.4,.6,20),Vector3(1.3,1.2,.7))
	# Local paths tie buildings and the market to the road.
	for spec in [[Vector3(0, 0.012, 18), Vector3(3, 0.02, 13)], [Vector3(-2.5, 0.013, 9), Vector3(7, 0.02, 2)], [Vector3(3, 0.014, 11), Vector3(6, 0.02, 2)]]:
		_box(spec[0], spec[1], Color(0.40, 0.33, 0.22))

	dressing.flush()

func _house(point: Vector3, color: Color, title: String) -> void:
	var reconstructed:=ForgeModelCatalogue.scene_for("world",&"house")
	if reconstructed:
		var building:=reconstructed.instantiate() as Node3D
		building.position=point;building.rotation.y=signf(point.x)*PI*.5;add_child(building)
		var body:=StaticBody3D.new();var collider:=CollisionShape3D.new();var box:=BoxShape3D.new()
		box.size=Vector3(3.8,2.8,3.6);collider.shape=box;body.position=point+Vector3(0,1.4,0)
		body.add_child(collider);add_child(body)
		_sign(point+Vector3(-signf(point.x)*1.98,2.6,0),title)
		for side_value in [-1,1]:dressing.place("crate",point+Vector3(side_value*2.2,0,1.3),Vector3.ONE*.75)
		return
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

func _box(_point: Vector3, _dimensions: Vector3, _color: Color, _collision_value: bool = false) -> void:
	pass # Ground strips are painted into the terrain shader.

func _place(kind: String, point: Vector3, size_value: Vector3 = Vector3.ONE) -> void:
	var scene := ForgeModelCatalogue.scene_for("world",StringName(kind))
	assert(scene != null,"Missing generated settlement model: "+kind)
	var model := scene.instantiate() as Node3D
	model.position=point;model.scale=size_value;add_child(model)

func _collision(point: Vector3, dimensions: Vector3) -> void:
	var body:=StaticBody3D.new();var collider:=CollisionShape3D.new();var shape:=BoxShape3D.new()
	shape.size=dimensions;collider.shape=shape;body.position=point
	body.add_child(collider);add_child(body)
