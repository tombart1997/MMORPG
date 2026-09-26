class_name ArtVFX
extends RefCounted
## Short, bounded mesh particles. One draw per burst, no per-particle nodes/lights.
static var shard: ArrayMesh
static var live_bursts: int = 0
static func burst(parent: Node3D, point: Vector3, color: Color, amount: int=5, spread: float=.6) -> void:
	if live_bursts >= 12: return
	if shard == null:
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		for v in [Vector3(0,.055,0),Vector3(-.018,0,0),Vector3(.018,0,0),Vector3(0,-.035,.01),Vector3(.018,0,0),Vector3(-.018,0,0)]: surface.add_vertex(v)
		surface.generate_normals()
		shard=surface.commit()
	var effect := MultiMeshInstance3D.new()
	effect.multimesh=MultiMesh.new()
	effect.multimesh.transform_format=MultiMesh.TRANSFORM_3D
	effect.multimesh.mesh=shard
	effect.multimesh.instance_count=amount
	var starts: Array[Vector3]=[]
	for i in amount:
		var direction := Vector3(sin(i*2.4), .3+fmod(i*.31,.7), cos(i*2.4))
		starts.append(direction*spread)
		effect.multimesh.set_instance_transform(i,Transform3D(Basis.IDENTITY,direction*.03))
	var mat := StandardMaterial3D.new()
	mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	mat.albedo_color=color
	effect.material_override=mat
	effect.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(effect)
	effect.position=point
	live_bursts+=1
	effect.tree_exited.connect(func(): live_bursts-=1)
	var tween:=effect.create_tween()
	tween.tween_method(func(t:float):
		for i in amount:
			var p:=starts[i]*t+Vector3.DOWN*t*t*.8
			effect.multimesh.set_instance_transform(i,Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*(1-t*.8)),p)),0.0,1.0,.55)
	tween.tween_callback(effect.queue_free)
