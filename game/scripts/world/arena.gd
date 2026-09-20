extends Node3D
## Composition root: owns encounter lifetime, geometry, and input defaults.
const PLAYER_SWORD = preload("res://data/attacks/player_sword.tres")
const ENEMY_CLAW = preload("res://data/attacks/enemy_claw.tres")
const CONE = preload("res://scripts/combat/combat_cone.gd")
var player: ActorBody
var pack: AggroGroup

func _ready() -> void:
	configure_inputs()
	_build_world()
	pack = AggroGroup.new()
	pack.name = "Pack"
	add_child(pack)
	player = ActorBody.new()
	player.name = "Player"
	player.weapon = PLAYER_SWORD
	player.maximum_health = 160.0
	player.position = Vector3(0, 0.1, 6)
	add_child(player)
	player.add_child(PlayerController.new())
	player.add_child(CONE.new())
	var spawn_points := [Vector3(-1.1, 0.1, 0), Vector3(0, 0.1, -0.3),
		Vector3(1.1, 0.1, 0), Vector3(-1.1, 0.1, -1.5),
		Vector3(0, 0.1, -1.8), Vector3(1.1, 0.1, -1.5)]
	for i in range(spawn_points.size()):
		var enemy := ActorBody.new()
		enemy.name = "Enemy%d" % (i + 1)
		enemy.title = "Raider %d" % (i + 1)
		enemy.position = spawn_points[i]
		enemy.rotation.y = PI
		enemy.base_color = Color(0.7, 0.22, 0.18)
		enemy.maximum_health = 75.0
		enemy.weapon = ENEMY_CLAW
		enemy.faction = &"enemies"
		enemy.opponents = &"players"
		add_child(enemy)
		pack.register(enemy)
		var brain := EnemyBrain.new()
		brain.pack = pack
		enemy.add_child(brain)
	var hud := CombatHUD.new()
	hud.player = player
	hud.pack = pack
	add_child(hud)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"):
		get_tree().reload_current_scene()

static func configure_inputs() -> void:
	var bindings := {"move_forward": KEY_W, "move_back": KEY_S,
		"move_left": KEY_A, "move_right": KEY_D, "release_mouse": KEY_ESCAPE,
		"restart": KEY_R, "toggle_debug": KEY_F3}
	for action in bindings:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
			var event := InputEventKey.new()
			event.physical_keycode = bindings[action]
			InputMap.action_add_event(action, event)
	if not InputMap.has_action("attack"):
		InputMap.add_action("attack")
		var event := InputEventKey.new()
		event.physical_keycode = KEY_SPACE
		InputMap.action_add_event("attack", event)

func _build_world() -> void:
	var environment := WorldEnvironment.new()
	var settings := Environment.new()
	settings.background_mode = Environment.BG_COLOR
	settings.background_color = Color(0.09, 0.13, 0.19)
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color(0.75, 0.83, 1.0)
	settings.ambient_light_energy = 0.65
	environment.environment = settings
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -25, 0)
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	add_child(sun)
	_box(Vector3(0, -0.25, 0), Vector3(32, 0.5, 32), Color(0.22, 0.27, 0.28))
	for side in [-1, 1]:
		_box(Vector3(side * 16, 1, 0), Vector3(0.5, 2, 32), Color(0.3, 0.35, 0.4))
		_box(Vector3(0, 1, side * 16), Vector3(32, 2, 0.5), Color(0.3, 0.35, 0.4))
	# Floor markings make relative movement and scale easy to judge.
	for index in range(-7, 8):
		_marker(Vector3(index * 2, 0.006, 0), Vector3(0.025, 0.01, 31))
		_marker(Vector3(0, 0.006, index * 2), Vector3(31, 0.01, 0.025))

func _box(location: Vector3, size: Vector3, color: Color) -> void:
	var body := StaticBody3D.new()
	body.position = location
	add_child(body)
	var collider := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collider.shape = shape
	body.add_child(collider)
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	mesh.material_override = material
	body.add_child(mesh)

func _marker(location: Vector3, size: Vector3) -> void:
	var mesh := MeshInstance3D.new()
	mesh.position = location
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.32, 0.38, 0.38)
	mesh.material_override = material
	add_child(mesh)
