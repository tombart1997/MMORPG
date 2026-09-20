class_name LootPickup
extends Node3D
## One selectable ground entry: item+quantity or a gold pouch. No rigid body.
var coins: int = 0
var item: ItemData
var quantity: int = 1
var claimed: bool = false
var lifetime: float = 90.0
var mesh: MeshInstance3D
var label: Label3D

func _ready() -> void:
	add_to_group("loot")
	mesh = MeshInstance3D.new()
	var gem := SphereMesh.new()
	gem.radius = 0.16
	gem.height = 0.42
	gem.radial_segments = 6
	gem.rings = 2
	mesh.mesh = gem
	mesh.position.y = 0.3
	var material := StandardMaterial3D.new()
	material.albedo_color = item.color if item else Color(1, 0.75, 0.2)
	material.emission_enabled = true
	material.emission = material.albedo_color * 0.4
	mesh.material_override = material
	add_child(mesh)
	label = Label3D.new()
	label.text = display_text()
	label.position.y = 0.7
	label.font_size = 32
	label.pixel_size = 0.009
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)
	label.visibility_range_end = 25
	var clickable := WorldClickable.attach(self, &"loot", 0.6)
	clickable.label = label

func can_collect(player: ActorBody) -> bool:
	return (not claimed and player.health.is_alive() and player.inventory != null
		and global_position.distance_to(player.global_position) <= 2.3)

func collect(player: ActorBody) -> bool:
	if not can_collect(player):
		return false
	if item and not player.inventory.can_add(item, quantity):
		player.inventory.last_pickup = "Inventory full - this item remains on the ground."
		return false
	claimed = true
	player.inventory.collect(coins, item, quantity)
	queue_free()
	return true

func _process(delta: float) -> void:
	# Separate nearby labels in screen space while leaving each pickup in place.
	var camera := get_viewport().get_camera_3d()
	label.global_position = global_position + Vector3.UP * 0.7
	if camera and not camera.is_position_behind(label.global_position):
		var screen := camera.unproject_position(label.global_position)
		for other in get_tree().get_nodes_in_group("loot"):
			if other == self: break
			if other.claimed or camera.is_position_behind(other.label.global_position): continue
			var point: Vector2 = camera.unproject_position(other.label.global_position)
			if absf(screen.x - point.x) < 145 and absf(screen.y - point.y) < 22: screen.y = point.y - 23
		var depth := -camera.to_local(label.global_position).z
		label.global_position = camera.project_position(screen, depth)
	lifetime -= delta
	mesh.rotation.y += delta
	if lifetime <= 0:
		queue_free()

func display_text() -> String:
	return "%s x%d" % [item.display_name, quantity] if item else "%d gold" % coins
