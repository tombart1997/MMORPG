extends Node3D
const TONIC = preload("res://data/items/field_tonic.tres")
var player: ActorBody
var camps: Array[EnemyCamp] = []
var notice: String = "Clear mossling camps. Gather drops. Return to the waystone to recover."
var notice_time: float = 0

func _ready() -> void:
	load("res://scripts/world/arena.gd").configure_inputs()
	for binding in [["pickup", KEY_E], ["tonic", KEY_Q]]:
		if not InputMap.has_action(binding[0]):
			InputMap.add_action(binding[0])
			var event := InputEventKey.new()
			event.physical_keycode = binding[1]
			InputMap.action_add_event(binding[0], event)
	add_child(ZoneTerrain.new())
	_lighting()
	player = ActorBody.new()
	player.name = "Traveler"
	player.title = "Traveler"
	player.position = ZoneTerrain.START + Vector3.UP * 0.1
	player.maximum_health = 160
	player.weapon = load("res://data/attacks/player_sword.tres")
	player.attack_sequence.assign([player.weapon, load("res://data/attacks/player_return.tres"),
		load("res://data/attacks/player_finisher.tres")])
	player.visual_scene = load("res://scenes/visuals/humanoid.tscn")
	add_child(player)
	player.progression = PlayerProgression.new()
	player.add_child(player.progression)
	player.inventory = PlayerInventory.new()
	player.add_child(player.inventory)
	player.inventory.items[&"field_tonic"] = 2
	player.progression.level_gained.connect(_on_level)
	player.health.died.connect(_on_player_death)
	player.add_child(PlayerController.new())
	var cone = load("res://scripts/combat/combat_cone.gd").new()
	cone.enabled = false
	player.add_child(cone)
	var names := ["Briar Crossing", "Old Pine Hollow", "The Broken Cairn"]
	for i in range(3):
		var camp := EnemyCamp.new()
		camp.position = ZoneTerrain.CAMPS[i]
		camp.camp_name = names[i]
		camp.count = 3 + i
		add_child(camp)
		camps.append(camp)
		_landmark(camp.position + Vector3(-3, 0, 1.5), names[i])
	_landmark(ZoneTerrain.START + Vector3(-3, 0, 0), "Waystone Refuge\nRest here to heal")
	var hud := ZoneHUD.new()
	hud.zone = self
	hud.player = player
	add_child(hud)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pickup"):
		pickup_nearby()
	if event.is_action_pressed("tonic") and not player.combat.movement_locked():
		if player.inventory.use_item(TONIC, player.health):
			announce("Field tonic: +45 health")
	if event.is_action_pressed("restart") and not player.health.is_alive():
		respawn_player()

func pickup_nearby() -> int:
	var collected := 0
	for drop in get_tree().get_nodes_in_group("loot"):
		if drop.collect(player):
			collected += 1
	if collected > 0:
		announce("Collected %d bundle(s). %s" % [collected, player.inventory.last_pickup])
	return collected

func announce(message: String) -> void:
	notice = message
	notice_time = 5.0

func _on_level(level: int) -> void:
	player.health.maximum = 160 + (level - 1) * 20
	player.health.heal(player.health.maximum)
	announce("LEVEL %d - maximum health increased; health restored" % level)

func _on_player_death(_source: Node3D) -> void:
	for camp in camps:
		camp.pack.target = null
	announce("You fell. Press R to return to the waystone. XP and inventory are kept.")

func respawn_player() -> void:
	player.position = ZoneTerrain.START + Vector3.UP * 0.1
	player.velocity = Vector3.ZERO
	player.health.current = player.health.maximum
	player.health.changed.emit(player.health.current, player.health.maximum)
	player.collision_layer = 2
	player.collision_mask = 3
	player.combat.cancel()
	announce("Recovered at the waystone")

func _physics_process(delta: float) -> void:
	notice_time = maxf(0, notice_time - delta)
	if player.health.is_alive() and player.position.distance_to(ZoneTerrain.START) < 4 and not player.combat.is_attacking():
		var safe := true
		for camp in camps:
			if camp.pack.has_target(): safe = false
		if safe: player.health.heal(18 * delta)
	for camp in camps:
		if camp.pack.has_target() and player.global_position.distance_to(camp.global_position) > 13:
			camp.pack.target = null

func _lighting() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.28, 0.43, 0.55)
	sky_material.sky_horizon_color = Color(0.75, 0.73, 0.6)
	sky_material.ground_horizon_color = Color(0.75, 0.73, 0.6)
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.73, 0.8, 0.86)
	environment.ambient_light_energy = 0.55
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-42, -32, 0)
	sun.light_color = Color(1, 0.87, 0.66)
	sun.light_energy = 1.45
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 85
	add_child(sun)

func _landmark(point: Vector3, title: String) -> void:
	var label := Label3D.new()
	label.position = point + Vector3.UP * 2.6
	label.text = title
	label.font_size = 32
	label.pixel_size = 0.008
	label.modulate = Color(0.95, 0.82, 0.53)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)
