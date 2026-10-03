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

static func spectacle(parent: Node, kind: String, point: Vector3, actor: ActorBody, duration: float, radius: float = 4) -> Node3D:
	var effect := SkillSpectacle.new()
	effect.kind = kind
	effect.caster = actor
	effect.lifetime = duration
	effect.radius = radius
	parent.add_child(effect)
	effect.position = point
	return effect

static func cast(context: SkillContext) -> void:
	var actor := context.actor
	var kind := "thunder"
	var duration := .42
	match context.skill.id:
		&"held_line": kind = "spirit"; duration = 6
		&"heelturn": kind = "sprint"; duration = 4
		&"gate_sweep": IronfieldAudio.instance.play_at(&"spin",actor.global_position,-3); return
		&"standard_of_ash": IronfieldAudio.instance.play_at(&"fire",actor.global_position,-3); return
		&"due_return": kind = "sun"; duration = .5
	var effect := spectacle(actor.get_parent(), kind, actor.position, actor, duration, context.skill.radius)
	IronfieldAudio.instance.play_at(StringName(kind),actor.global_position,-3)
	effect.rotation.y = atan2(-context.direction.x,-context.direction.z)

static func hit(context: SkillContext, target: ActorBody, damage: float) -> void:
	ArtVFX.burst(target.get_parent(), target.position+Vector3.UP*.8, context.skill.color, 10, 1.1)
	damage_number(target, damage, context.skill.color)
	flash(target.get_parent(), target.global_position, .55, context.skill.color)

static var live_numbers: int = 0
static var number_serial: int = 0
static func damage_number(target: ActorBody, amount: float, color: Color) -> void:
	if DisplayServer.get_name() == "headless" or live_numbers >= 32: return
	var label := Label3D.new()
	label.text = str(roundi(amount))
	label.font_size = 30
	label.outline_size = 5
	label.pixel_size = .004
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = color.lightened(.4)
	label.no_depth_test = false
	target.get_parent().add_child(label)
	label.global_position = target.global_position + Vector3((number_serial%3-1)*.18,1.9,0)
	number_serial += 1
	live_numbers += 1
	label.tree_exited.connect(func(): live_numbers -= 1)
	var tween := label.create_tween().set_parallel(true)
	tween.tween_property(label,"position:y",label.position.y+.8,.5)
	tween.tween_property(label,"modulate:a",0.0,.3).set_delay(.2)
	tween.tween_property(label,"outline_modulate:a",0.0,.3).set_delay(.2)
	tween.chain().tween_callback(label.queue_free)
