class_name RemasterScenery
extends Node3D
## Deterministic, chunked scenery. Tiny props have no shadows or collision.
static var meshes: Dictionary = {}
var batches: Dictionary = {}
var random := RandomNumberGenerator.new()
const CHUNK := 24.0

func place(kind: String, point: Vector3, scale_value: Vector3 = Vector3.ONE, yaw: float = 0) -> void:
	var cell := Vector2i(floori(point.x/CHUNK),floori(point.z/CHUNK))
	var key := "%s:%d:%d" % [kind,cell.x,cell.y]
	if not batches.has(key): batches[key] = {"kind":kind,"cell":cell,"transforms":[]}
	batches[key].transforms.append(Transform3D(Basis(Vector3.UP,yaw).scaled(scale_value),point-Vector3(cell.x*CHUNK,0,cell.y*CHUNK)))

func plant_tree(point: Vector3, size_value: float, yaw: float, variant: int) -> void:
	place("tree%d" % variant,point,Vector3.ONE*size_value,yaw)

func flush() -> void:
	for batch in batches.values():
		var node := MultiMeshInstance3D.new()
		node.name = batch.kind
		node.position = Vector3(batch.cell.x*CHUNK,0,batch.cell.y*CHUNK)
		var multimesh := MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.mesh = mesh_for(batch.kind)
		multimesh.instance_count = batch.transforms.size()
		for i in batch.transforms.size(): multimesh.set_instance_transform(i,batch.transforms[i])
		node.multimesh = multimesh
		var tree := String(batch.kind).begins_with("tree")
		var large: bool = tree or String(batch.kind).begins_with("rock") or String(batch.kind).begins_with("cliff") or batch.kind in ["ruin_arch","shrine","watchtower"]
		node.visibility_range_end = 140 if large else (75 if batch.kind in ["tent","ruin","banner","dead_tree"] else 44)
		node.visibility_range_end_margin = 6
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if large else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(node)
	batches.clear()

func dress_ground() -> void:
	random.seed = 23811
	var noise := FastNoiseLite.new()
	noise.seed = 171
	noise.frequency = .095
	for x in range(-116,117,2):
		for z in range(-292,60,2):
			var p := Vector3(x+random.randf_range(-.8,.8),0,z+random.randf_range(-.8,.8))
			var weights := RemasterGround.weights(p.x,p.z)
			if weights.r*12 < 3.0 or weights.g > .75: continue
			# Keep all settlement counters, doors, stairs and NPC access clear.
			if p.z>5 and absf(p.x)<30:
				var near_house := false
				for h in RemasterGround.houses:
					if Vector2(p.x,p.z).distance_to(h)<3.6: near_house=true
				if near_house: continue
			var density := noise.get_noise_2d(p.x,p.z)
			if random.randf() > .52+density*.9: continue
			p.y = ZoneTerrain.height_at(p.x,p.z)
			var pick := random.randf()
			var kind := "grass" if pick<.66 else ("fern" if pick<.79 else ("shrub" if pick<.88 else ("stone" if pick<.95 else "flowers")))
			place(kind,p,Vector3.ONE*random.randf_range(.65,1.35),random.randf()*TAU)
			if density>.22 and pick>.94:
				place("mushroom",p+Vector3(.6,0,.4),Vector3.ONE,random.randf()*TAU)
			if pick<.007: place("log",p,Vector3.ONE,random.randf()*TAU)
	# Small planted groves frame the village without entering its travel lanes.
	for p in [Vector3(-11,0,6),Vector3(11,0,8),Vector3(-12,0,24),Vector3(12,0,26),Vector3(-29,0,12),Vector3(29,0,26),Vector3(-4,0,53),Vector3(5,0,55)]:
		plant_tree(p,.8,random.randf()*TAU,random.randi_range(0,2))
	for i in FirstMapContent.POINTS.size():
		var data := load("res://data/enemies/%s.tres" % FirstMapContent.IDS[i]) as EnemyData
		dress_camp(FirstMapContent.POINTS[i],data.family,data.tier,i)

func dress_camp(center: Vector3,family: StringName,tier: int,seed_value: int) -> void:
	var hostile := tier>=3 or center.z < -170
	if family == &"wisp" and tier>=3:
		var motes := GPUParticles3D.new()
		motes.position = center+Vector3(0,1,0)
		motes.amount = 8
		motes.lifetime = 5
		motes.visibility_aabb = AABB(Vector3(-4,-1,-4),Vector3(8,5,8))
		motes.visibility_range_end = 42
		motes.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var process := ParticleProcessMaterial.new()
		process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
		process.emission_box_extents = Vector3(3,.3,3)
		process.gravity = Vector3(0,.12,0)
		process.scale_min = .04
		process.scale_max = .10
		motes.process_material = process
		var quad := QuadMesh.new()
		var glow := StandardMaterial3D.new()
		glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		glow.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		glow.albedo_color = Color(.5,.65,.52,.36)
		glow.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		quad.material = glow
		motes.draw_pass_1 = quad
		add_child(motes)
	for i in 4:
		var a := float(i)*TAU/4+float(seed_value)*.73
		var p := center+Vector3(sin(a),0,cos(a))*6.5
		if ZoneTerrain.path_distance(p)<3.0: continue
		p.y = ZoneTerrain.height_at(p.x,p.z)
		var kind := "bones"
		if family == &"spider": kind = "web" if i%2==0 else "eggs"
		elif family in [&"bandit",&"human"]: kind = "tent" if i==0 else ("crate" if i%2==1 else "banner")
		elif family in [&"wisp",&"stonekin"]: kind = "ruin" if i%2==0 else "dead_tree"
		elif i%2==0: kind = "dead_tree" if hostile else "stone"
		place(kind,p,Vector3.ONE*(1.25 if hostile else 1.0),a)
		if family in [&"bandit",&"human"] and i==1: place("fire",p+Vector3(1,0,1))

static func mesh_for(kind: String) -> Mesh:
	if meshes.has(kind): return meshes[kind]
	meshes[kind] = WorldAssetKit.mesh_for("rock0" if kind == "stone" else kind)
	return meshes[kind]
