class_name BriarwakeGrove
extends Node3D
## Fixed art composition around the existing encounter; no gameplay ownership.
const CENTER := Vector3(-8, 0, -49)
const ASSETS := "res://assets/generated/world/"
var scenes: Dictionary = {}
var random := RandomNumberGenerator.new()
var environment: Environment
var sun: DirectionalLight3D
var fill: DirectionalLight3D

func _process(_delta: float) -> void:
	if environment == null:
		for child in get_parent().get_parent().get_children():
			if child is WorldEnvironment: environment=child.environment
			if child is DirectionalLight3D: sun=child
		return
	var camera:=get_viewport().get_camera_3d()
	if camera == null: return
	var weight:=1.0-smoothstep(22.0,34.0,Vector2(camera.global_position.x-CENTER.x,camera.global_position.z-CENTER.z).length())
	environment.ambient_light_color=Color(.67,.74,.79).lerp(Color(.49,.60,.59),weight)
	environment.ambient_light_energy=lerpf(.58,.50,weight)
	environment.fog_light_color=Color("a6bdbd").lerp(Color(.43,.53,.49),weight)
	environment.fog_density=lerpf(.005,.007,weight)
	sun.light_color=Color(1,.94,.83).lerp(Color(1,.85,.64),weight)
	sun.light_energy=lerpf(1.1,.98,weight)
	# A stable sun direction prevents shadows rotating as the player crosses the grove.
	sun.rotation_degrees=Vector3(-38,-28,0)
	fill.light_energy=.18*weight

func _ready() -> void:
	name = "AmberScarArt"
	random.seed = 921
	fill=DirectionalLight3D.new()
	fill.rotation_degrees=Vector3(-28,-32,0)
	fill.light_color=Color(.66,.77,.92)
	fill.light_energy=0
	fill.shadow_enabled=false
	add_child(fill)
	# Authored foreground, side wings and background: open central combat floor.
	var trees := [
		[-9.5, 7.0, 0, 1.15, -.4], [8.6, 6.4, 1, 1.13, 1.0],
		[-8.3, -1.0, 2, 1.12, .6], [8.8, -2.0, 0, 1.12, -1.0],
		[-6.5, -8.0, 1, 1.1, .4], [1.0, -10.0, 2, 1.24, 2.1],
		[7.6, -9.0, 0, 1.1, -.3], [-12.5, -7.0, 2, 1.3, 1.7],
		[13.0, -8.0, 1, 1.2, .8], [-13.0, 6.5, 0, 1.05, 2.4],
		[12.5, 2.0, 2, 1.14, -.8], [-5.0, -16.0, 0, 1.3, .6],
		[4.0, -17.0, 1, 1.4, 1.8], [13.0, -16.0, 2, 1.3, 2.8],
		[-15.0, -15.0, 1, 1.5, -.5], [-15.0, 12.0, 2, 1.12, .4],
		[13.0, 12.0, 0, 1.15, -1.2], [-10.0, 15.0, 2, 1.1, .4],
		[-11.0,-20.0,2,1.7,.8],[-2.0,-21.0,0,1.65,2.1],[8.0,-21.0,1,1.6,-.6],[17.0,-19.0,2,1.6,.4]]
	for item in trees:
		place(["tree_bent", "tree_fork", "tree_wide"][item[2]], Vector2(item[0], item[1]), item[3], item[4], true)
	for item in [[-6,-5,0,1.25,.4], [5,-6,1,1.1,1.8], [9,-4,2,.8,.7], [-9,3,1,.9,-.5],
		[7,7,0,.6,.9], [-5,10,2,.5,.3], [-10,-10,0,1.4,.7], [5,-13,2,1.5,-.3]]:
		place("rock_%d" % item[2], Vector2(item[0], item[1]), item[3], item[4])
	place("fallen_wood", Vector2(-6, 3.4), 1, -.65)
	place("fallen_wood", Vector2(5, -7.5), .8, .9)
	# Fixed seeded placements within authored planting beds, not uniform world scatter.
	var beds := [Vector3(-7,0,5), Vector3(7,0,4), Vector3(-6,0,-4), Vector3(6,0,-4),
		Vector3(-10,0,0), Vector3(10,0,0), Vector3(-3,0,-8), Vector3(3,0,-9), Vector3(-6,0,10), Vector3(8,0,9)]
	for species in ["fern", "sedge", "shrub_laurel", "shrub_briar"]:
		var placements: Array[Transform3D] = []
		var count := 17 if species == "sedge" else (9 if species == "fern" else 3)
		for bed in beds:
			for i in count:
				var point: Vector3 = CENTER + bed + Vector3(random.randf_range(-2.1,2.1),0,random.randf_range(-1.7,1.7))
				if point.distance_to(CENTER) < 3.7: continue
				point.y = ZoneTerrain.height_at(point.x,point.z) + .015
				var size := random.randf_range(.7,1.25)
				placements.append(Transform3D(Basis(Vector3.UP,random.randf()*TAU).scaled(Vector3.ONE*size),point))
		batch(species, placements)
	# Pebble clusters break up the traveled earth without new collision obstacles.
	var stones: Array[Transform3D] = []
	for i in 65:
		var a := i * 2.39996
		var radius := random.randf_range(3.3,10.0)
		var point := CENTER + Vector3(sin(a),0,cos(a))*radius
		point.y=ZoneTerrain.height_at(point.x,point.z)-.03
		stones.append(Transform3D(Basis(Vector3.UP,a).scaled(Vector3.ONE*random.randf_range(.035,.13)),point))
	batch("rock_0",stones)
	var litter: Array[Transform3D]=[]
	for bed in beds:
		for i in 32:
			var point:Vector3=CENTER+bed+Vector3(random.randf_range(-3.2,3.2),0,random.randf_range(-2.4,2.4))
			point.y=ZoneTerrain.height_at(point.x,point.z)+.02
			litter.append(Transform3D(Basis(Vector3.UP,random.randf()*TAU).scaled(Vector3.ONE*random.randf_range(.6,1.2)),point))
	batch("leaf_litter",litter)

func source(asset: String) -> PackedScene:
	if not scenes.has(asset): scenes[asset]=ReviewedModels.scene_for(ASSETS+asset+".glb")
	return scenes[asset]

func place(asset: String, offset: Vector2, size: float, yaw: float, trunk_collision: bool=false) -> Node3D:
	var node: Node3D = source(asset).instantiate()
	add_child(node)
	node.position=CENTER+Vector3(offset.x,0,offset.y)
	node.position.y=ZoneTerrain.height_at(node.position.x,node.position.z)
	node.rotation.y=yaw
	node.scale=Vector3.ONE*size
	for mesh: MeshInstance3D in node.find_children("*","MeshInstance3D",true,false):
		mesh.visibility_range_end=65
		if asset.begins_with("tree"):
			# These authored trees bypass WorldAssetKit's MultiMesh material path.
			# Apply the same clearance to their retained leaf cards and trunks.
			for surface in mesh.mesh.get_surface_count():
				var material:=mesh.get_active_material(surface) as StandardMaterial3D
				if material:mesh.set_surface_override_material(surface,RemasterMaterials.camera_clearance(material,8.0,11.0))
			mesh.set_meta("camera_clearance",true)
	if trunk_collision and ZoneTerrain.path_distance(node.position)>3.2:
		var body := StaticBody3D.new()
		var collision := CollisionShape3D.new()
		var shape := CylinderShape3D.new()
		shape.radius=.45
		shape.height=3.4
		collision.shape=shape
		collision.position.y=1.7
		node.add_child(body)
		body.add_child(collision)
	return node

func batch(asset: String, placements: Array[Transform3D]) -> void:
	var original: Node3D=source(asset).instantiate()
	var meshes=original.find_children("*","MeshInstance3D",true,false)
	for part: MeshInstance3D in meshes:
		var local := part.transform
		var parent := part.get_parent()
		while parent is Node3D:
			local=parent.transform*local
			parent=parent.get_parent()
		var instance := MultiMeshInstance3D.new()
		instance.multimesh=MultiMesh.new()
		instance.multimesh.transform_format=MultiMesh.TRANSFORM_3D
		instance.multimesh.mesh=part.mesh
		instance.multimesh.instance_count=placements.size()
		for i in placements.size(): instance.multimesh.set_instance_transform(i,placements[i]*local)
		instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		instance.visibility_range_end=45
		add_child(instance)
	original.free()
