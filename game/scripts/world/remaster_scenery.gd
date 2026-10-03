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

static func append(surface: SurfaceTool, primitive: PrimitiveMesh, position_value: Vector3, scale_value: Vector3 = Vector3.ONE, rotation_value: Vector3 = Vector3.ZERO) -> void:
	surface.append_from(primitive,0,Transform3D(Basis.from_euler(rotation_value).scaled(scale_value),position_value))

static func box(surface: SurfaceTool,p: Vector3,s: Vector3,rotation_value: Vector3 = Vector3.ZERO) -> void:
	var primitive := BoxMesh.new()
	primitive.size = Vector3.ONE
	append(surface,primitive,p,s,rotation_value)

static func branch(surface: SurfaceTool,a: Vector3,b: Vector3,radius: float) -> void:
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = radius*.6
	cylinder.bottom_radius = radius
	cylinder.height = a.distance_to(b)
	cylinder.radial_segments = 6
	cylinder.rings = 1
	surface.append_from(cylinder,0,Transform3D(Basis(Quaternion(Vector3.UP,(b-a).normalized())),(a+b)*.5))

static func sphere(surface: SurfaceTool,p: Vector3,s: Vector3) -> void:
	var primitive := SphereMesh.new()
	primitive.radius = 1
	primitive.height = 2
	primitive.radial_segments = 7
	primitive.rings = 3
	append(surface,primitive,p,s)

static func finish(surface: SurfaceTool,mesh: ArrayMesh,material: Material) -> void:
	surface.index()
	surface.set_material(material)
	surface.commit(mesh)

static func mesh_for(kind: String) -> Mesh:
	if meshes.has(kind): return meshes[kind]
	if kind in ["tree0","tree1","tree2","rock0","rock1","rock2","cliff","cliff1","dead_tree","log","fern","shrub","grass","ruin_arch","shrine","watchtower","stone","tent"]:
		meshes[kind] = WorldAssetKit.mesh_for("rock0" if kind == "stone" else kind)
		return meshes[kind]
	var mesh := ArrayMesh.new()
	var wood := SurfaceTool.new()
	wood.begin(Mesh.PRIMITIVE_TRIANGLES)
	var leaves := SurfaceTool.new()
	leaves.begin(Mesh.PRIMITIVE_TRIANGLES)
	var material := RemasterMaterials.surface(6)
	if kind.begins_with("tree") or kind == "dead_tree":
		var variant := kind.trim_prefix("tree").to_int()
		var bend := float(variant-1)*.4
		branch(wood,Vector3.ZERO,Vector3(bend,2.4,0),.28)
		branch(wood,Vector3(bend,2.4,0),Vector3(bend*.4,4.8,.25),.19)
		for i in 7:
			var a := i*2.4+variant*.6
			var tip := Vector3(sin(a)*(1.1+float(i%3)*.27),3.2+i*.35,cos(a)*1.3)
			branch(wood,Vector3(bend,2.1+i*.22,0),tip,.09)
			if kind != "dead_tree": sphere(leaves,tip+Vector3(0,.4,0),Vector3(1.15+float(i%2)*.3,.6+float(i%3)*.16,1.15))
		finish(wood,mesh,RemasterMaterials.camera_clearance(material))
		if kind != "dead_tree": finish(leaves,mesh,RemasterMaterials.camera_clearance(RemasterMaterials.surface(1,Color("b7c286") if variant!=2 else Color("d9ca83"))))
	elif kind in ["grass","fern","flowers"]:
		for i in (7 if kind=="fern" else 5):
			var a := i*2.4
			var height := .32+float(i%3)*.12
			var base := Vector3(sin(a)*.16,0,cos(a)*.16)
			var tip := base+Vector3(sin(a)*.30,height,cos(a)*.30)
			var across := Vector3(cos(a),0,-sin(a))*(.14 if kind=="fern" else .045)
			for v in [base-across,base+across,tip]:
				wood.set_normal(Vector3.UP)
				wood.set_uv(Vector2(v.x*3,v.y*2))
				wood.add_vertex(v)
			if kind=="flowers": sphere(leaves,tip,Vector3(.06,.035,.06))
		var plant_material := RemasterMaterials.surface(0,Color("c0bc7c")) if kind=="grass" else RemasterMaterials.surface(1,Color("9eaf73"))
		plant_material.cull_mode = BaseMaterial3D.CULL_DISABLED
		finish(wood,mesh,plant_material)
		if kind=="flowers": finish(leaves,mesh,RemasterMaterials.surface(7,Color("cbba91")))
	elif kind=="shrub":
		for i in 4: sphere(wood,Vector3(sin(i*2.4)*.32,.35,cos(i*2.4)*.32),Vector3(.43,.38,.45))
		finish(wood,mesh,RemasterMaterials.surface(1,Color("96a276")))
	elif kind in ["stone","eggs","mushroom"]:
		for i in 3:
			var p := Vector3(i*.24,.15+float(i%2)*.1,sin(i)*.2)
			sphere(wood,p,Vector3(.24,.16,.21) if kind=="stone" else Vector3(.17,.25,.17))
			if kind=="mushroom": sphere(leaves,p+Vector3(0,.17,0),Vector3(.26,.09,.26))
		finish(wood,mesh,RemasterMaterials.surface(4 if kind=="stone" else 7,Color("a5aa92")))
		if kind=="mushroom": finish(leaves,mesh,RemasterMaterials.surface(3,Color("b78259")))
	elif kind in ["log","bones"]:
		branch(wood,Vector3(-.8,.16,0),Vector3(.8,.16,.2),.2 if kind=="log" else .07)
		for i in 4: branch(wood,Vector3(-.6+i*.35,.16,.1),Vector3(-.5+i*.35,.45,.35),.07 if kind=="log" else .035)
		finish(wood,mesh,RemasterMaterials.surface(6 if kind=="log" else 7,Color("b6ae94")))
	elif kind=="crate":
		box(wood,Vector3(0,.4,0),Vector3(.85,.8,.75))
		box(wood,Vector3(0,.4,-.4),Vector3(.1,.95,.06),Vector3(0,0,.7))
		finish(wood,mesh,material)
	elif kind in ["banner","web"]:
		branch(wood,Vector3(-.9,0,0),Vector3(-.9,2.3,0),.08)
		branch(wood,Vector3(.9,0,0),Vector3(.9,2.3,0),.08)
		if kind=="banner":
			box(leaves,Vector3(0,1.65,0),Vector3(1.7,1.1,.035))
		else:
			for i in 7:
				var a:=float(i)*TAU/7
				branch(leaves,Vector3(0,1.25,0),Vector3(sin(a)*.9,1.25+cos(a)*.9,0),.012)
				for r in [0.3,.55,.8]: branch(leaves,Vector3(sin(a)*r,1.25+cos(a)*r,0),Vector3(sin(a+TAU/7)*r,1.25+cos(a+TAU/7)*r,0),.009)
		finish(wood,mesh,material)
		finish(leaves,mesh,RemasterMaterials.surface(7,Color("7c3930") if kind=="banner" else Color("b5b7a4")))
	elif kind=="tent":
		box(wood,Vector3(-.65,.85,0),Vector3(.08,2.15,2.4),Vector3(0,0,-.65))
		box(wood,Vector3(.65,.85,0),Vector3(.08,2.15,2.4),Vector3(0,0,.65))
		branch(leaves,Vector3(0,0,-1.3),Vector3(0,1.75,-1.3),.065)
		finish(wood,mesh,RemasterMaterials.surface(7,Color("827456")))
		finish(leaves,mesh,material)
	elif kind=="ruin":
		for i in 3: box(wood,Vector3(i*.6,.55+i*.12,0),Vector3(.48,1.1+i*.24,.45),Vector3(.05,0,.09*i))
		finish(wood,mesh,RemasterMaterials.surface(4,Color("7f887d")))
	elif kind=="fire":
		for i in 5:
			var a:=i*TAU/5
			branch(wood,Vector3(sin(a)*.4,.08,cos(a)*.4),Vector3(0,.22,0),.08)
			var cone:=CylinderMesh.new()
			cone.top_radius=0
			cone.bottom_radius=.1
			cone.height=.45
			cone.radial_segments=4
			append(leaves,cone,Vector3(sin(a)*.12,.32,cos(a)*.12))
		finish(wood,mesh,material)
		var ember := RemasterMaterials.surface(3,Color("db7b31"))
		ember.emission_enabled=true
		ember.emission=Color("8c3d0c")
		finish(leaves,mesh,ember)
	meshes[kind] = mesh
	return mesh
