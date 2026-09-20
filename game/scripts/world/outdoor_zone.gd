extends Node3D
const TONIC = preload("res://data/items/field_tonic.tres")
var persistence := ProgressionSave.new()
var persistence_enabled: bool = true
var save_clock: float = 0.0
var interaction: InteractionService
var settlement: Settlement
var sanctuary: SafeArea
var player: ActorBody
var camps: Array[EnemyCamp] = []
var notice: String = "Clear mossling camps. Gather drops. Return to the waystone to recover."
var notice_time: float = 0

func _ready() -> void:
	load("res://scripts/world/arena.gd").configure_inputs()
	for binding in [["pickup", KEY_E], ["tonic", KEY_Q], ["inventory", KEY_I], ["save_game", KEY_F5], ["load_game", KEY_F9], ["journal", KEY_J]]:
		if not InputMap.has_action(binding[0]):
			InputMap.add_action(binding[0])
			var event := InputEventKey.new()
			event.physical_keycode = binding[1]
			InputMap.action_add_event(binding[0], event)
	add_child(ZoneTerrain.new())
	sanctuary = SafeArea.new()
	sanctuary.position = Vector3(0, 0, 15)
	sanctuary.radius = 11
	add_child(sanctuary)
	settlement = Settlement.new()
	add_child(settlement)
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
	player.inventory.gold = 20
	player.inventory.add_item(TONIC, 2)
	player.equipment = PlayerEquipment.new()
	player.equipment.actor = player
	player.add_child(player.equipment)
	player.stats = CharacterStats.new()
	player.stats.actor = player
	player.add_child(player.stats)
	player.equipment.slots[&"weapon"] = ItemStack.new(&"wayfarer_blade")
	player.equipment.slots[&"chest"] = ItemStack.new(&"travelers_vest")
	player.equipment.refresh()
	player.quests = PlayerQuests.new()
	player.quests.actor = player
	player.add_child(player.quests)
	player.inventory.changed.connect(func(): player.quests.changed.emit())
	player.navigation = PlayerNavigation.new()
	player.navigation.actor = player
	player.add_child(player.navigation)
	player.progression.level_gained.connect(_on_level)
	player.health.died.connect(_on_player_death)
	var controller := PlayerController.new()
	player.add_child(controller)
	player.world_interaction = WorldInteraction.new()
	player.world_interaction.actor = player
	player.world_interaction.camera = controller.rig.camera
	player.world_interaction.zone = self
	player.add_child(player.world_interaction)
	player.skills = PlayerSkills.new()
	player.skills.actor = player
	player.add_child(player.skills)
	var cone = load("res://scripts/combat/combat_cone.gd").new()
	cone.enabled = false
	player.add_child(cone)
	var names := ["Briar Crossing", "Old Pine Hollow", "The Broken Cairn"]
	for i in range(3):
		var camp := EnemyCamp.new()
		camp.position = ZoneTerrain.CAMPS[i]
		camp.camp_name = names[i]
		camp.count = 3 + i
		camp.enemy_data = load("res://data/enemies/%s.tres" % ["young", "grown", "ironback"][i])
		add_child(camp)
		camps.append(camp)
		_landmark(camp.position + Vector3(-3, 0, 1.5), names[i] + "\n" + ["Young mosslings - first hunt", "Mosslings - better gear advised", "Ironbacks - danger"][i])
	_landmark(ZoneTerrain.START + Vector3(3, 0, 4), "Waystone Refuge\nRest here to heal")
	interaction = InteractionService.new()
	interaction.player = player
	add_child(interaction)
	var hud := ZoneHUD.new()
	hud.zone = self
	hud.player = player
	add_child(hud)
	if persistence_enabled and (FileAccess.file_exists(persistence.path) or FileAccess.file_exists(persistence.path + ".bak")):
		if not persistence.load_player(player):
			persistence_enabled = false
			announce("Save could not be loaded; saving disabled to preserve the original file.")
	get_tree().auto_accept_quit = false
	var navigation := ZoneNavigation.new()
	add_child(navigation)
	navigation.build(self)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("save_game"):
		save_progress()
	if event.is_action_pressed("load_game"):
		if persistence_enabled and persistence.load_player(player):
			var hp_before := player.health.current
			respawn_player()
			player.health.current = hp_before
			player.health.changed.emit(player.health.current, player.health.maximum)
			announce("Progress loaded at the waystone")
		else: announce(persistence.error)
	if event.is_action_pressed("pickup") and not interaction.interact():
		pickup_nearby()
	if event.is_action_pressed("tonic") and not player.combat.movement_locked() and not (player.skills and player.skills.busy()):
		if player.inventory.use_item(TONIC, player.health):
			announce("Field tonic: +45 health")
	if event.is_action_pressed("restart") and not player.health.is_alive():
		respawn_player()

func pickup_nearby() -> int:
	var nearest: LootPickup
	var distance := INF
	for drop in get_tree().get_nodes_in_group("loot"):
		if drop.can_collect(player):
			var next: float = drop.global_position.distance_squared_to(player.global_position)
			if next < distance: nearest = drop; distance = next
	if nearest and nearest.collect(player):
		announce(player.inventory.last_pickup)
		return 1
	announce(player.inventory.last_pickup if nearest else "No loot within reach")
	return 0

func announce(message: String) -> void:
	notice = message
	notice_time = 5.0

func _on_level(level: int) -> void:
	player.stats.recalculate()
	player.health.heal(player.health.maximum)
	announce("LEVEL %d - maximum health increased; health restored" % level)

func _on_player_death(_source: Node3D) -> void:
	for camp in camps:
		camp.pack.disengage()
	if player.ui_session: player.ui_session.close()
	announce("You fell. Press R to return to the waystone. XP and inventory are kept.")

func respawn_player() -> void:
	if player.skills: player.skills.cancel_transient()
	if player.world_interaction: player.world_interaction.cancel()
	for camp in camps: camp.pack.disengage()
	if player.ui_session: player.ui_session.close()
	player.position = ZoneTerrain.START + Vector3.UP * 0.1
	player.velocity = Vector3.ZERO
	player.health.current = player.health.maximum
	player.health.changed.emit(player.health.current, player.health.maximum)
	player.collision_layer = 2
	player.collision_mask = 3
	player.combat.cancel()
	announce("Recovered at the waystone")

func _physics_process(delta: float) -> void:
	save_clock += delta
	if persistence_enabled and save_clock >= 30:
		save_clock = 0
		save_progress(false)
	notice_time = maxf(0, notice_time - delta)
	if player.health.is_alive() and sanctuary.contains(player.position) and not player.combat.is_attacking():
		var safe := true
		for camp in camps:
			if camp.pack.has_target(): safe = false
		if safe: player.health.heal(18 * delta)

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
	environment.fog_enabled = true
	environment.fog_light_color = Color(0.46, 0.53, 0.49)
	environment.fog_density = 0.007
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-42, -32, 0)
	sun.light_color = Color(1, 0.94, 0.83)
	sun.light_energy = 1.0
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 85
	add_child(sun)

func _landmark(point: Vector3, title: String) -> void:
	var label := Label3D.new()
	label.position = point + Vector3.UP * 2.6
	label.text = title
	label.font_size = 28
	label.visibility_range_end = 20
	label.pixel_size = 0.008
	label.modulate = Color(0.95, 0.82, 0.53)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

func save_progress(notify_player: bool = true) -> void:
	if not persistence_enabled: return
	var success := persistence.save_player(player)
	if notify_player or not success: announce("Progress saved" if success else "Save failed: " + persistence.error)

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		save_progress(false)
		get_tree().quit()
