class_name TrailHorse
extends Node3D
## Original low-poly bay horse: shaped ring lofts, four articulated legs,
## dark points, flaxen saddle blanket and a restrained two-beat travel gait.
var legs: Array[Node3D] = []
var knees: Array[Node3D] = []
var phase: float = 0

func _ready() -> void:
	var bay := Color("72503b")
	var dark := Color("292922")
	var leather := Color("403b2d")
	# Local forward is -Z, matching player and equipment conventions.
	loft(self, [[Vector3(0,1.12,.79),.20,.24], [Vector3(0,1.15,.52),.34,.40], [Vector3(0,1.17,-.18),.31,.38], [Vector3(0,1.25,-.57),.24,.31]], bay)
	loft(self, [[Vector3(0,1.30,-.46),.23,.28], [Vector3(0,1.64,-.68),.18,.26], [Vector3(0,1.96,-.76),.13,.17]], bay)
	loft(self, [[Vector3(0,1.95,-.72),.14,.19], [Vector3(0,1.91,-.91),.16,.19], [Vector3(0,1.70,-1.24),.12,.12], [Vector3(0,1.68,-1.32),.10,.10]], bay.lightened(.08))
	loft(self, [[Vector3(0,1.69,-1.22),.125,.12], [Vector3(0,1.68,-1.34),.11,.09]], dark)
	for side in [-1.0, 1.0]:
		loft(self, [[Vector3(side*.105,2.03,-.78),.065,.07], [Vector3(side*.13,2.25,-.76),.015,.025]], dark)
		loft(self, [[Vector3(side*.153,1.94,-.88),.025,.027], [Vector3(side*.165,1.94,-.89),.018,.024]], Color("141b17"), 6)
		for front in [true, false]:
			var pivot := Node3D.new()
			pivot.position = Vector3(side*.235,1.13,-.43 if front else .50)
			add_child(pivot)
			legs.append(pivot)
			loft(pivot, [[Vector3.ZERO,.12,.14], [Vector3(0,-.36,.02 if front else .13),.065,.08], [Vector3(0,-.57,.01),.048,.065]], bay, 8)
			var knee := Node3D.new()
			knee.position = Vector3(0,-.55,.01)
			pivot.add_child(knee)
			knees.append(knee)
			loft(knee, [[Vector3.ZERO,.052,.07], [Vector3(0,-.37,0),.038,.05], [Vector3(0,-.48,-.025),.06,.075]], dark, 8)
			loft(knee, [[Vector3(0,-.46,-.035),.072,.085], [Vector3(0,-.57,-.055),.085,.10]], Color("232723"), 8)
	# Mane follows the neck ridge; tail is a tapered swept tuft.
	loft(self, [[Vector3(0,1.48,-.42),.05,.07], [Vector3(0,1.78,-.55),.055,.12], [Vector3(0,2.02,-.67),.035,.08]], dark, 6)
	loft(self, [[Vector3(0,1.37,.74),.085,.10], [Vector3(0,.96,1.03),.11,.10], [Vector3(0,.42,1.05),.06,.065], [Vector3(0,.30,.97),.015,.025]], dark, 8)
	loft(self, [[Vector3(0,1.38,.33),.35,.10], [Vector3(0,1.43,.23),.35,.09], [Vector3(0,1.45,-.24),.34,.09], [Vector3(0,1.39,-.33),.33,.08]], Color("7d7951"))
	loft(self, [[Vector3(0,1.50,.24),.24,.095], [Vector3(0,1.48,.12),.23,.055], [Vector3(0,1.49,-.22),.23,.06], [Vector3(0,1.57,-.29),.20,.08]], leather)
	# Pale blaze and bridle read from the ordinary gameplay camera.
	loft(self, [[Vector3(0,2.05,-.90),.035,.018], [Vector3(0,1.88,-1.13),.027,.018], [Vector3(0,1.73,-1.30),.025,.015]], Color("c6bda0"), 6)
	loft(self, [[Vector3(0,1.78,-1.18),.137,.12], [Vector3(0,1.75,-1.22),.137,.12]], leather, 10)

func loft(parent: Node3D, rings: Array, color: Color, sides: int = 10) -> void:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Rings lie in XY. Their displaced centers create the neck/head/leg curves.
	var points: Array[Vector3] = []
	for row in rings.size():
		var ring: Array = rings[row]
		var tangent: Vector3 = (rings[mini(row+1,rings.size()-1)][0] - rings[maxi(0,row-1)][0]).normalized()
		var axis_x := Vector3.RIGHT - tangent * tangent.dot(Vector3.RIGHT)
		if axis_x.length_squared() < .01: axis_x = Vector3.UP - tangent * tangent.dot(Vector3.UP)
		axis_x = axis_x.normalized()
		var axis_y := tangent.cross(axis_x).normalized()
		for i in sides:
			var angle := TAU * i / sides
			points.append(ring[0] + axis_x*cos(angle)*ring[1] + axis_y*sin(angle)*ring[2])
	for row in rings.size() - 1:
		for i in sides:
			var a := row*sides+i
			var b := row*sides+(i+1)%sides
			for index in [a,b,a+sides,b,b+sides,a+sides]: surface.add_vertex(points[index])
	for i in range(1,sides-1):
		for index in [0,i+1,i]: surface.add_vertex(points[index])
		var base := (rings.size()-1)*sides
		for index in [base,base+i,base+i+1]: surface.add_vertex(points[index])
	surface.generate_normals()
	var mesh := MeshInstance3D.new()
	mesh.mesh = surface.commit()
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = .92
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.material_override = material
	parent.add_child(mesh)

func travel(velocity: Vector3, delta: float) -> void:
	var speed := Vector2(velocity.x,velocity.z).length()
	phase += delta * minf(speed, 9) * 1.8
	var amount := clampf(speed/5,0,1)
	for i in legs.size():
		var gait := sin(phase + (PI if i in [1,2] else 0))
		legs[i].rotation.x = gait * .43 * amount
		knees[i].rotation.x = maxf(0,-gait) * .55 * amount
	position.y = absf(sin(phase)) * .025 * amount
