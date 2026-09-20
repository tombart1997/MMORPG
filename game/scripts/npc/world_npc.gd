class_name WorldNPC
extends Node3D
@export var data: NPCData
var label: Label3D
var model: Node3D

func _ready() -> void:
	assert(data != null and data.id != &"")
	add_to_group("npcs")
	model = Node3D.new()
	add_child(model)
	var body := CylinderMesh.new()
	body.top_radius = 0.26
	body.bottom_radius = 0.37
	body.height = 1.05
	body.radial_segments = 6
	_part(body, Vector3(0, 0.85, 0), data.clothing_color)
	var head := SphereMesh.new()
	head.radius = 0.23
	head.height = 0.48
	head.radial_segments = 8
	head.rings = 4
	_part(head, Vector3(0, 1.6, 0), Color(0.73, 0.53, 0.34))
	for x in [-0.23, 0.23]:
		var boot := BoxMesh.new()
		boot.size = Vector3(0.2, 0.4, 0.35)
		_part(boot, Vector3(x, 0.2, -0.02), Color(0.16, 0.13, 0.09))
		var arm := BoxMesh.new()
		arm.size = Vector3(0.17, 0.65, 0.18)
		_part(arm, Vector3(x * 1.6, 0.96, 0), data.clothing_color.darkened(0.15))
	var nose := BoxMesh.new()
	nose.size = Vector3(0.10, 0.12, 0.12)
	_part(nose, Vector3(0, 1.59, -0.22), Color(0.68, 0.47, 0.30))
	label = Label3D.new()
	label.text = data.display_name + "\n" + String(data.role).capitalize()
	label.position.y = 2.15
	label.font_size = 32
	label.pixel_size = 0.009
	label.modulate = Color(0.98, 0.85, 0.53)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.visibility_range_end = 18
	add_child(label)
	WorldClickable.attach(self, &"npc")

func _part(mesh: Mesh, point: Vector3, color: Color) -> void:
	var part := MeshInstance3D.new()
	part.mesh = mesh
	part.position = point
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	part.material_override = material
	model.add_child(part)

func can_interact(player: ActorBody) -> bool:
	if not is_instance_valid(player) or not player.health.is_alive() or player.combat.is_attacking() or (player.skills and player.skills.busy()): return false
	if global_position.distance_to(player.global_position) > data.interaction_range: return false
	var ray := PhysicsRayQueryParameters3D.create(player.global_position + Vector3.UP, global_position + Vector3.UP, 1)
	return get_world_3d().direct_space_state.intersect_ray(ray).is_empty()

func _process(delta: float) -> void:
	for player in get_tree().get_nodes_in_group("players"):
		if player.quests: label.text = player.quests.marker(data.id) + data.display_name + "\n" + String(data.role).capitalize()
	if not data.turn_to_player: return
	for player in get_tree().get_nodes_in_group("players"):
		if can_interact(player):
			var direction: Vector3 = player.global_position - global_position
			model.rotation.y = lerp_angle(model.rotation.y, atan2(-direction.x, -direction.z), minf(1, delta * 5))
			break
