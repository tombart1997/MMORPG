extends Node3D
@export_enum("ember", "glass", "rift") var style: String = "ember"
## Continuous forged surfaces with bevelled edges and a usable two-handed grip.
static var cached: Dictionary = {}

func _ready() -> void:
	set_meta("two_handed", true)
	var grip := Marker3D.new()
	grip.name = "Grip"
	add_child(grip)
	if not cached.has(style): cached[style] = _forge()
	for entry in cached[style]:
		var part := MeshInstance3D.new()
		part.mesh = entry.mesh
		part.material_override = entry.material
		add_child(part)
	var tip := Marker3D.new()
	tip.name = "Tip"
	tip.position.z = -1.6
	add_child(tip)
	var offhand := Marker3D.new()
	offhand.name = "OffhandGrip"
	offhand.position.z = .18
	add_child(offhand)

func _material(color: Color, metal: float, rough: float, glow: float = 0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.metallic = metal
	mat.roughness = rough
	if glow > 0:
		mat.emission_enabled = true
		mat.emission = color
		mat.emission_energy_multiplier = glow
	return mat

func _loft(rings: Array, material: StandardMaterial3D) -> Dictionary:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var points: Array[Vector3] = []
	for ring in rings:
		var z: float = ring[0]
		var w: float = ring[1]
		var h: float = ring[2]
		for xy in [Vector2(-w,0),Vector2(-w*.72,h*.7),Vector2(0,h),Vector2(w*.72,h*.7),Vector2(w,0),Vector2(w*.72,-h*.7),Vector2(0,-h),Vector2(-w*.72,-h*.7)]:
			points.append(Vector3(xy.x,xy.y,z))
	for i in range(rings.size()-1):
		for j in range(8):
			var a := i*8+j
			var b := i*8+(j+1)%8
			for k in [a,b,b+8,a,b+8,a+8]: surface.add_vertex(points[k])
	for j in range(1,7):
		for k in [0,j+1,j,(rings.size()-1)*8,(rings.size()-1)*8+j,(rings.size()-1)*8+j+1]: surface.add_vertex(points[k])
	surface.generate_normals()
	return {"mesh":surface.commit(),"material":material}

func _forge() -> Array:
	var tint := Color("b57d57") if style == "ember" else Color("8db4bf") if style == "glass" else Color("8d82a9")
	var steel := _material(tint,.72,.32)
	var dark := _material(Color("263441"),.68,.46)
	var brass := _material(Color("a98c58"),.66,.38)
	var leather := _material(Color("631e2b"),0,.78)
	var width := .10 if style == "glass" else .15 if style == "ember" else .19
	var result: Array = []
	result.append(_loft([[.075,.025,.024],[.04,.03,.024],[-.19,.03,.024],[-.30,width*.75,.025],[-.48,width,.033],[-1.13,width*.70,.027],[-1.40,width*.42,.017],[-1.60,.001,.001]],steel))
	result.append(_loft([[-.33,width*.12,.028],[-.49,width*.17,.036],[-1.13,width*.12,.030],[-1.38,.001,.020]],dark))
	result.append(_loft([[.04,.026,.026],[.08,.032,.028],[.28,.028,.026],[.32,.024,.024]],leather))
	result.append(_loft([[.315,.023,.024],[.345,.048,.041],[.38,.039,.034],[.40,.018,.017]],brass))
	result.append(_cloud_guard(brass))
	for n in range(9):
		var z := .065+n*.026
		result.append(_loft([[z,.029,.028],[z+.003,.029,.028]],dark))
	var gem := _material(tint.lightened(.12),.30,.3,.22)
	result.append(_loft([[-.14,.036,.032],[-.16,.051,.047],[-.20,.028,.033]],gem))
	var batches: Dictionary = {}
	for entry in result:
		var mat: StandardMaterial3D = entry.material
		if not batches.has(mat):
			var surface := SurfaceTool.new()
			surface.begin(Mesh.PRIMITIVE_TRIANGLES)
			batches[mat] = surface
		batches[mat].append_from(entry.mesh, 0, Transform3D.IDENTITY)
	var combined: Array = []
	for mat in batches: combined.append({"mesh":batches[mat].commit(), "material":mat})
	return combined

func _cloud_guard(material: StandardMaterial3D) -> Dictionary:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for sign_value in [-1.0, 1.0]:
		var points: Array[Vector3] = []
		for ring in range(25):
			var t := float(ring) / 24
			var center := Vector3(sign_value * (.018 + .265 * t), 0, -.13 - .10 * sin(t * PI * .80))
			var radius := lerpf(.032, .005, t)
			for side in range(12):
				var angle := float(side) / 12 * TAU
				points.append(center + Vector3(0, cos(angle) * radius * .75, sin(angle) * radius))
		for ring in range(24):
			for side in range(12):
				var a := ring * 12 + side
				var b := ring * 12 + (side + 1) % 12
				for k in [a, b, b+12, a, b+12, a+12]: surface.add_vertex(points[k])
		for side in range(1,11):
			for k in [0,side+1,side,288,288+side,288+side+1]: surface.add_vertex(points[k])
	surface.generate_normals()
	return {"mesh":surface.commit(), "material":material}
