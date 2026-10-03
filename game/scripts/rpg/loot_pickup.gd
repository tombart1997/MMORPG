class_name LootPickup
extends Node3D
## One selectable ground entry: item+quantity or a gold pouch. No rigid body.
var coins: int = 0
var item: ItemData
var quantity: int = 1
var claimed: bool = false
var lifetime: float = 90.0
var mesh: Node3D
var label: Label3D
var encounter_id: String = ""
func is_rare() -> bool:
	return item != null and item.rarity == &"rare"

func _ready() -> void:
	add_to_group("loot")
	var scene := get_parent()
	if not scene.has_meta("loot_layout"):
		var layout := LootLayout.new()
		scene.set_meta("loot_layout", layout)
		scene.add_child.call_deferred(layout)
	if is_rare(): lifetime = maxf(lifetime, 300)
	mesh = LootVisual.create(self)
	add_child(mesh)
	label = Label3D.new()
	label.text = display_text()
	label.position.y = 0.7
	label.font_size = 24 if is_rare() else 20
	label.pixel_size = 0.0015
	label.fixed_size = true
	label.no_depth_test = true
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	if is_rare():
		label.modulate = Color(0.45, 0.9, 1)
		ArtVFX.burst(self, Vector3(0,.35,0), Color(.4,.82,.91), 6, .45)
		var beam := MeshInstance3D.new()
		var pillar := CylinderMesh.new()
		pillar.top_radius = 0.015
		pillar.bottom_radius = 0.09
		pillar.height = 2.5
		pillar.radial_segments = 6
		beam.mesh = pillar
		beam.position.y = 1.25
		var glow := StandardMaterial3D.new()
		glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		glow.albedo_color = Color(0.25, 0.75, 0.95, 0.45)
		glow.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		beam.material_override = glow
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(beam)
	add_child(label)
	label.visibility_range_end = 25
	var clickable := WorldClickable.attach(self, &"loot", 0.6)
	clickable.label = label
	call_deferred("_ground_visual")

func _ground_visual() -> void:
	var query := PhysicsRayQueryParameters3D.create(global_position+Vector3.UP*.6,global_position-Vector3.UP*1.5,1)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():
		mesh.global_position = hit.position+Vector3.UP*.004
		mesh.global_basis = Basis(Quaternion(Vector3.UP,hit.normal))

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
	IronfieldAudio.instance.play_at(&"coins" if item == null else &"pickup",global_position,-2)
	queue_free()
	return true

func _process(delta: float) -> void:
	lifetime -= delta
	if lifetime <= 0:
		queue_free()

func display_text() -> String:
	return ("RARE | " if is_rare() else "") + ("%s x%d" % [item.display_name, quantity] if item else "%d gold" % coins)
