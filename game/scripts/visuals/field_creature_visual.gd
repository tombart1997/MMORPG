extends ActorVisual
## Shared prototype silhouettes. Variant data supplies species, size and palette.
var parts: Array[MeshInstance3D] = []
var legs: Array[Node3D] = []
var palette := Color("657887")
var family: StringName = &"wolf"

func _ready() -> void:
	creature = true
	model = Node3D.new()
	add_child(model)
	label = Label3D.new()
	label.position.y = 1.85
	label.font_size = 24
	label.pixel_size = .004
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.visibility_range_end = 22
	add_child(label)

func apply_variant(data: EnemyData) -> void:
	palette = data.tint
	family = data.family
	if family == &"wisp":
		part(Vector3(0,1,0),Vector3(.65,.85,.65),palette,true)
		for i in 3:
			part(Vector3(sin(i*TAU/3)*.5,.7,cos(i*TAU/3)*.5),Vector3(.16,.42,.16),palette.lightened(.3))
	elif family == &"stonekin":
		part(Vector3(0,.95,0),Vector3(.85,1.15,.55),palette)
		part(Vector3(0,1.7,-.08),Vector3(.55,.5,.5),palette.lightened(.15))
		for side in [-1,1]:
			part(Vector3(side*.63,.95,0),Vector3(.38,.9,.4),palette.darkened(.15))
			legs.append(part(Vector3(side*.28,.28,0),Vector3(.38,.55,.45),palette))
	elif family == &"spider":
		part(Vector3(0,.55,.25),Vector3(.95,.65,1.05),palette,true)
		part(Vector3(0,.48,-.45),Vector3(.55,.4,.5),palette.darkened(.2),true)
		for side in [-1,1]:
			for i in 4:
				var leg := part(Vector3(side*.65,.28,-.5+i*.3),Vector3(.95,.12,.14),palette.darkened(.3))
				leg.rotation.z = side*.45
				legs.append(leg)
	else:
		var boar := family == &"boar"
		part(Vector3(0,.7,0),Vector3(.7 if boar else .5,.7,1.2),palette,true)
		part(Vector3(0,.88,-.65),Vector3(.52,.52,.55),palette,true)
		part(Vector3(0,.77,-1.0),Vector3(.38,.25,.48),palette.darkened(.2))
		for side in [-1,1]:
			var ear := part(Vector3(side*.2,1.2,-.63),Vector3(.14,.38,.16),palette.darkened(.2))
			ear.rotation.z = side*.25
			for z in [-.4,.4]:
				legs.append(part(Vector3(side*.23,.28,z),Vector3(.18,.55,.2),palette.darkened(.25)))
			if boar: part(Vector3(side*.26,.7,-1.05),Vector3(.1,.28,.1),Color("e8dfba"))
		var tail := part(Vector3(0,.8,.78),Vector3(.18,.18,.65),palette)
		tail.rotation.x = -.4
	# Eyes and an elite crown make variants readable beyond just tint.
	for side in [-1,1]: part(Vector3(side*.16,1.02 if family != &"spider" else .55,-.87 if family != &"spider" else -.71),Vector3(.065,.065,.07),Color("e6c77b"))
	if data.tier >= 3:
		label.modulate = [Color.WHITE,Color.WHITE,Color.WHITE,Color("cba7ee"),Color("eaa05d"),Color("f07165")][data.tier]
		for side in [-1,1]:
			var horn := part(Vector3(side*.32,1.35,-.25),Vector3(.14,.65,.14),Color("dcc99c"))
			horn.rotation.z = side*.35

func part(point: Vector3, dimensions: Vector3, color: Color, rounded: bool = false) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	if rounded:
		var sphere := SphereMesh.new()
		sphere.radius = .5
		sphere.height = 1
		sphere.radial_segments = 10
		sphere.rings = 5
		node.mesh = sphere
	else:
		node.mesh = BoxMesh.new()
		node.mesh.size = Vector3.ONE
	node.scale = dimensions
	node.position = point
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = .8
	node.material_override = mat
	model.add_child(node)
	parts.append(node)
	return node

func present(velocity: Vector3, combat: MeleeCombat, health: HealthComponent, title: String, delta: float) -> void:
	locomotion_time += delta
	hit_time += delta
	label.text = title
	label.visible = health.is_alive() and nameplate_allowed
	if not health.is_alive():
		model.rotation.z = lerp_angle(model.rotation.z,PI*.5,minf(1,delta*7))
		model.position.y = -.15
		return
	var speed := Vector2(velocity.x,velocity.z).length()
	model.position.y = sin(locomotion_time*(5 if family == &"wisp" else 11))*(.12 if family == &"wisp" else .035*minf(speed,1))
	model.rotation.x = -.15 if combat.phase == MeleeCombat.Phase.WINDUP else (.2 if combat.phase == MeleeCombat.Phase.ACTIVE else 0.0)
	for i in legs.size(): legs[i].rotation.x = sin(locomotion_time*11+i*PI)*.45*minf(speed,1)
	for p in parts:
		var mat := p.material_override as StandardMaterial3D
		mat.emission_enabled = combat.phase == MeleeCombat.Phase.WINDUP or hit_time < .1
		mat.emission = Color(.45,.13,.01) if combat.phase == MeleeCombat.Phase.WINDUP else Color(.35,.35,.35)
