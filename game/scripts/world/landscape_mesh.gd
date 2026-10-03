class_name LandscapeMesh
extends RefCounted
## Indexed terrain chunks: shared border samples/normals and independent frustum culling.
static func build(parent: Node3D, bounds: Rect2, height: Callable, weights: Callable, material: Material) -> void:
	var samples: Dictionary = {}
	var step := 2
	var chunk := 24
	for cx in range(int(bounds.position.x),int(bounds.end.x),chunk):
		for cz in range(int(bounds.position.y),int(bounds.end.y),chunk):
			var nx := mini(chunk,int(bounds.end.x)-cx)/step
			var nz := mini(chunk,int(bounds.end.y)-cz)/step
			var vertices := PackedVector3Array()
			var normals := PackedVector3Array()
			var colors := PackedColorArray()
			var indices := PackedInt32Array()
			for z in range(nz+1):
				for x in range(nx+1):
					var px := cx+x*step
					var pz := cz+z*step
					var key := Vector2i(px,pz)
					if not samples.has(key):
						var y: float = height.call(px,pz)
						var dx: float = height.call(px-1,pz)-height.call(px+1,pz)
						var dz: float = height.call(px,pz-1)-height.call(px,pz+1)
						samples[key] = [y,Vector3(dx,2,dz).normalized(),weights.call(px,pz)]
					vertices.append(Vector3(x*step,samples[key][0],z*step))
					normals.append(samples[key][1])
					colors.append(samples[key][2])
					if x<nx and z<nz:
						var a := z*(nx+1)+x
						indices.append_array(PackedInt32Array([a,a+1,a+nx+1,a+1,a+nx+2,a+nx+1]))
			var arrays := []
			arrays.resize(Mesh.ARRAY_MAX)
			arrays[Mesh.ARRAY_VERTEX] = vertices
			arrays[Mesh.ARRAY_NORMAL] = normals
			arrays[Mesh.ARRAY_COLOR] = colors
			arrays[Mesh.ARRAY_INDEX] = indices
			var mesh := ArrayMesh.new()
			mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
			var node := MeshInstance3D.new()
			node.name = "Terrain_%d_%d" % [cx,cz]
			node.position = Vector3(cx,0,cz)
			node.mesh = mesh
			node.material_override = material
			parent.add_child(node)
			node.create_trimesh_collision()

static func backdrop(parent: Node3D, bounds: Rect2, volcanic: bool = false, height: Callable = Callable()) -> void:
	# Continuous uneven mountain belts outside the traversable map, with a low foothill skirt.
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var center := bounds.get_center()
	var half := bounds.size*.5
	var rings: Array[float] = [0.0,18.0,55.0,110.0,190.0]
	var points: Array[Vector3] = []
	for ring in rings:
		for i in 128:
			var angle := float(i)*TAU/128
			var direction := Vector2(sin(angle),cos(angle))
			var radial := minf(half.x/maxf(absf(direction.x),.001),half.y/maxf(absf(direction.y),.001))
			var point := center+direction*(radial+ring)
			var ridge := 17+14*sin(angle*5+.8)+8*cos(angle*11)+5*sin(angle*19+.5)
			var rise := (8+maxf(1,ridge)) * sin(clampf(ring/210,0,1)*PI*.73)
			var base_height: float = height.call(point.x,point.y) if height.is_valid() else 3.0
			points.append(Vector3(point.x,base_height-.15 if ring == 0 else 3+rise,point.y))
	for r in range(4):
		for i in 128:
			var j := (i+1)%128
			for index in [r*128+i,r*128+j,(r+1)*128+i,r*128+j,(r+1)*128+j,(r+1)*128+i]:
				surface.set_uv(Vector2(points[index].x,points[index].z)*.06)
				surface.add_vertex(points[index])
	surface.generate_normals()
	var node := MeshInstance3D.new()
	node.name = "DistantMountainBelt"
	node.mesh = surface.commit()
	node.material_override = RemasterMaterials.surface(4,Color("565568") if volcanic else Color("6a8581"))
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	# Low foothill skirt closes views beneath the perimeter and the distant ridge mesh.
	var skirt := MeshInstance3D.new()
	skirt.name = "MountainFoothillSkirt"
	var plane := PlaneMesh.new()
	plane.size = bounds.size+Vector2(380,380)
	skirt.mesh = plane
	skirt.position = Vector3(center.x,-.25,center.y)
	skirt.material_override = node.material_override
	skirt.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(skirt)
