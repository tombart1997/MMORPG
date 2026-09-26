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
	mesh = MeshInstance3D.new()
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var top:=Vector3(.04,.25,-.025)
	var bottom:=Vector3(-.025,-.17,.02)
	for i in 5:
		var a:=i*TAU/5
		var b:=(i+1)*TAU/5
		var p:=Vector3(cos(a)*.14,.025*sin(a*2),sin(a)*.11)
		var q:=Vector3(cos(b)*.14,.025*sin(b*2),sin(b)*.11)
		for point in [top,p,q,bottom,q,p]: surface.add_vertex(point)
	surface.generate_normals()
	mesh.mesh = surface.commit()
	mesh.position.y = 0.3
	var material := StandardMaterial3D.new()
	material.albedo_color = item.color if item else Color(1, 0.75, 0.2)
	material.emission_enabled = is_rare()
	material.emission = material.albedo_color * 0.4
	mesh.material_override = material
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
	lifetime -= delta
	mesh.rotation.y += delta
	if lifetime <= 0:
		queue_free()

func display_text() -> String:
	return ("RARE | " if is_rare() else "") + ("%s x%d" % [item.display_name, quantity] if item else "%d gold" % coins)
