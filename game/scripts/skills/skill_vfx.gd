class_name SkillVFX
extends RefCounted
static func ring(radius: float, color: Color, angle: float = 360) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	var mesh := ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var steps := maxi(8, int(angle / 8))
	for i in steps:
		var a := deg_to_rad(-angle / 2 + angle * i / steps)
		var b := deg_to_rad(-angle / 2 + angle * (i + 1) / steps)
		var outer_a := Vector3(sin(a), 0.07, -cos(a)) * radius
		var outer_b := Vector3(sin(b), 0.07, -cos(b)) * radius
		var inner_a := Vector3(sin(a), 0.07, -cos(a)) * maxf(0.01, radius - 0.07)
		var inner_b := Vector3(sin(b), 0.07, -cos(b)) * maxf(0.01, radius - 0.07)
		for point in [outer_a, outer_b, inner_b, outer_a, inner_b, inner_a]: mesh.surface_add_vertex(point)
	mesh.surface_end()
	node.mesh = mesh
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.albedo_color = color
	node.material_override = material
	return node
static func flash(parent: Node, point: Vector3, radius: float, color: Color, angle: float = 360, yaw: float = 0) -> void:
	var node := ring(radius, color, angle)
	node.material_override.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	node.global_position = point
	node.rotation.y = yaw
	var tween := node.create_tween().set_parallel(true)
	tween.tween_property(node, "scale", Vector3.ONE * 1.12, 0.24)
	tween.tween_property(node.material_override, "albedo_color:a", 0.0, 0.24)
	tween.chain()
	tween.tween_callback(node.queue_free)
