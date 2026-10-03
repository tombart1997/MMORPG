class_name RegionPortal
extends Node3D

var destination: String = "cinderfall"
var title: String = "Cinderfall Gate"

func _ready() -> void:
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 1.35
	torus.outer_radius = 1.62
	torus.rings = 28
	torus.ring_segments = 12
	ring.mesh = torus
	ring.rotation.x = PI * 0.5
	ring.position.y = 1.7
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("51216d") if destination == "cinderfall" else Color("247376")
	material.emission_enabled = true
	material.emission = Color("b34fe9") if destination == "cinderfall" else Color("63e4cf")
	material.emission_energy_multiplier = 2.5
	ring.material_override = material
	add_child(ring)
	var inner := MeshInstance3D.new()
	var disc := SphereMesh.new()
	disc.radius = 1.25
	disc.height = 2.6
	inner.mesh = disc
	inner.position.y = 1.7
	inner.scale.z = 0.12
	var veil := StandardMaterial3D.new()
	veil.albedo_color = Color(0.47, 0.17, 0.65, 0.48) if destination == "cinderfall" else Color(0.2, 0.68, 0.68, 0.48)
	veil.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	veil.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	veil.emission_enabled = true
	veil.emission = veil.albedo_color
	inner.material_override = veil
	add_child(inner)
	var label := Label3D.new()
	label.text = title + "\n[E] Travel"
	label.position.y = 3.6
	label.font_size = 24
	label.pixel_size = 0.006
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = Color("f4d99d")
	add_child(label)

func can_use(actor: ActorBody) -> bool:
	return actor.health.is_alive() and not actor.ui_open and actor.global_position.distance_to(global_position) < 3.4
