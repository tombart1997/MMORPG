class_name SkillArea
extends Node3D
var caster: ActorBody
var id: StringName
var radius: float
var remaining: float
var slow: float
var shelter: float
var color: Color
func _ready() -> void:
	add_to_group("skill_areas")
	add_child(SkillVFX.ring(radius, color))
	if shelter > 0:
		var post := MeshInstance3D.new()
		var mesh := CylinderMesh.new()
		mesh.top_radius = 0.035
		mesh.bottom_radius = 0.045
		mesh.height = 1.0
		post.mesh = mesh
		post.position.y = 0.5
		add_child(post)
		var flag := MeshInstance3D.new()
		var flag_mesh := PrismMesh.new()
		flag_mesh.size = Vector3(0.45, 0.28, 0.04)
		flag.mesh = flag_mesh
		flag.position = Vector3(0.2, 0.88, 0)
		var material := StandardMaterial3D.new()
		material.albedo_color = color
		flag.material_override = material
		add_child(flag)
func _physics_process(delta: float) -> void:
	remaining -= delta
	if remaining <= 0 or not is_instance_valid(caster) or not caster.health.is_alive(): queue_free(); return
	for actor: ActorBody in get_tree().get_nodes_in_group(caster.opponents):
		if actor.global_position.distance_to(global_position) <= radius and SkillTargeting.line_clear(actor, global_position, actor.global_position):
			actor.statuses.add(&"zone_slow", 0.25, slow, caster)
	if shelter > 0 and caster.global_position.distance_to(global_position) <= radius and SkillTargeting.line_clear(caster, global_position, caster.global_position): caster.statuses.add(&"shelter", 0.25, shelter, caster)
