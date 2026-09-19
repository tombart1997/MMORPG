extends MeshInstance3D
## Floor projection of the exact center-based cone test (F3 toggles).
var actor: ActorBody
var enabled: bool = true

func _ready() -> void:
	actor = get_parent() as ActorBody
	position.y = 0.055
	var geometry := ImmediateMesh.new()
	mesh = geometry
	geometry.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var half_angle := deg_to_rad(actor.weapon.cone_degrees * 0.5)
	for step in range(24):
		var a := lerpf(-half_angle, half_angle, step / 24.0)
		var b := lerpf(-half_angle, half_angle, (step + 1) / 24.0)
		geometry.surface_add_vertex(Vector3.ZERO)
		geometry.surface_add_vertex(Vector3(sin(a), 0, -cos(a)) * actor.weapon.reach)
		geometry.surface_add_vertex(Vector3(sin(b), 0, -cos(b)) * actor.weapon.reach)
	geometry.surface_end()
	var material := StandardMaterial3D.new()
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material_override = material

func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("toggle_debug"):
		enabled = not enabled
	visible = enabled and actor.health.is_alive()
	var color := Color(0.3, 0.7, 1.0, 0.08)
	if actor.combat.phase == MeleeCombat.Phase.WINDUP:
		color = Color(1.0, 0.7, 0.1, 0.2)
	elif actor.combat.phase == MeleeCombat.Phase.ACTIVE:
		color = Color(1.0, 0.25, 0.1, 0.45)
	material_override.albedo_color = color
