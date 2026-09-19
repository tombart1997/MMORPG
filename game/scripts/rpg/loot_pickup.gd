class_name LootPickup
extends Node3D
## A single atomic bundle per enemy. Currency and item are collected together.
var coins: int = 0
var item: ItemData
var claimed: bool = false
var lifetime: float = 90.0
var mesh: MeshInstance3D

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
	var label := Label3D.new()
	label.text = "%dg%s" % [coins, " + " + item.display_name if item else ""]
	label.position.y = 0.7
	label.font_size = 24
	label.pixel_size = 0.005
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

func can_collect(player: ActorBody) -> bool:
	return (not claimed and player.health.is_alive() and player.inventory != null
		and global_position.distance_to(player.global_position) <= 2.3)

func collect(player: ActorBody) -> bool:
	if not can_collect(player):
		return false
	claimed = true
	player.inventory.collect(coins, item)
	queue_free()
	return true

func _process(delta: float) -> void:
	lifetime -= delta
	mesh.rotation.y += delta
	if lifetime <= 0:
		queue_free()
