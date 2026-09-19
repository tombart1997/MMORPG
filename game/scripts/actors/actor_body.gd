class_name ActorBody
extends CharacterBody3D
## Actor composition and placeholder presentation, independent of controllers.
var health: HealthComponent
var combat: MeleeCombat
var visual: Node3D
var sword_pivot: Node3D
var body_mesh: MeshInstance3D
var status_label: Label3D
var base_color := Color(0.2, 0.65, 0.9)
var flash_time: float = 0.0
var maximum_health: float = 100.0
var weapon: AttackData
var faction: StringName = &"players"
var opponents: StringName = &"enemies"
var title: String = "Player"

func _ready() -> void:
	add_to_group(faction)
	collision_layer = 2
	collision_mask = 3
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.34
	capsule.height = 1.8
	collider.shape = capsule
	collider.position.y = 0.9
	add_child(collider)
	health = HealthComponent.new()
	health.maximum = maximum_health
	add_child(health)
	combat = MeleeCombat.new()
	combat.attack = weapon
	combat.target_group = opponents
	add_child(combat)
	visual = Node3D.new()
	add_child(visual)
	body_mesh = MeshInstance3D.new()
	var mesh := CapsuleMesh.new()
	mesh.radius = 0.34
	mesh.height = 1.8
	body_mesh.mesh = mesh
	body_mesh.position.y = 0.9
	var material := StandardMaterial3D.new()
	material.albedo_color = base_color
	body_mesh.material_override = material
	visual.add_child(body_mesh)
	# A nose makes forward direction readable even without animation assets.
	var nose := MeshInstance3D.new()
	var nose_mesh := BoxMesh.new()
	nose_mesh.size = Vector3(0.22, 0.18, 0.25)
	nose.mesh = nose_mesh
	nose.position = Vector3(0, 1.5, -0.36)
	visual.add_child(nose)
	sword_pivot = Node3D.new()
	sword_pivot.position.y = 1.0
	visual.add_child(sword_pivot)
	var sword := MeshInstance3D.new()
	var blade := BoxMesh.new()
	blade.size = Vector3(0.09, 0.12, 1.45)
	sword.mesh = blade
	sword.position = Vector3(0.55, 0, -0.7)
	sword_pivot.add_child(sword)
	status_label = Label3D.new()
	status_label.position.y = 2.25
	status_label.font_size = 32
	status_label.pixel_size = 0.006
	status_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(status_label)
	health.damaged.connect(_on_damaged)
	health.died.connect(_on_died)

func _process(delta: float) -> void:
	flash_time = maxf(0.0, flash_time - delta)
	var color := base_color
	if not health.is_alive():
		color = Color(0.19, 0.2, 0.23)
	elif flash_time > 0.0:
		color = Color.WHITE
	elif combat.phase == MeleeCombat.Phase.WINDUP:
		color = Color(1.0, 0.65, 0.15)
	elif combat.phase == MeleeCombat.Phase.ACTIVE:
		color = Color(1.0, 0.25, 0.12)
	body_mesh.material_override.albedo_color = color
	status_label.text = "%s  %d / %d" % [title, health.current, health.maximum]
	match combat.phase:
		MeleeCombat.Phase.WINDUP:
			sword_pivot.rotation.y = lerpf(0.0, -1.15, clampf(combat.phase_elapsed / weapon.windup, 0, 1))
		MeleeCombat.Phase.ACTIVE:
			sword_pivot.rotation.y = lerpf(-1.15, 1.15, clampf(combat.phase_elapsed / weapon.active, 0, 1))
		MeleeCombat.Phase.RECOVERY:
			sword_pivot.rotation.y = lerpf(1.15, 0.0, clampf(combat.phase_elapsed / weapon.recovery, 0, 1))
		_:
			sword_pivot.rotation.y = 0.0

func _on_damaged(_amount: float, _source: Node3D) -> void:
	flash_time = 0.18
	var tween := create_tween()
	visual.scale = Vector3(1.15, 0.85, 1.15)
	tween.tween_property(visual, "scale", Vector3.ONE, 0.18)

func _on_died(_source: Node3D) -> void:
	combat.cancel()
	collision_layer = 0
	collision_mask = 1
	visual.rotation.z = PI * 0.5
	status_label.modulate = Color(0.5, 0.5, 0.5)
