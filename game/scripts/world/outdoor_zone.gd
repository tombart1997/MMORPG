extends Node3D
@export_enum("briarwood", "cinderfall") var region_id: String = "briarwood"
const TONIC = preload("res://data/items/field_tonic.tres")
var persistence := ProgressionSave.new()
var persistence_enabled: bool = true
var save_clock: float = 0.0
var interaction: InteractionService
var settlement: Settlement
var sanctuary: SafeArea
var player: ActorBody
var camps: Array[EnemyCamp] = []
var portal: RegionPortal
var notice: String = "Clear mossling camps. Gather drops. Return to the waystone to recover."
var notice_time: float = 0

func _ready() -> void:
	IronfieldAudio.instance.enter_region(region_id)
	var identity: Dictionary = get_tree().root.get_meta("character_login", {})
	if not identity.is_empty(): persistence.path = identity.path
	load("res://scripts/world/arena.gd").configure_inputs()
	for binding in [["pickup", KEY_E], ["tonic", KEY_Q], ["inventory", KEY_I], ["save_game", KEY_F5], ["load_game", KEY_F9], ["journal", KEY_J], ["world_map", KEY_M], ["quick_second", KEY_F], ["mount", KEY_H]]:
		if not InputMap.has_action(binding[0]):
			InputMap.add_action(binding[0])
			var event := InputEventKey.new()
			event.physical_keycode = binding[1]
			InputMap.action_add_event(binding[0], event)
	add_child(CinderfallTerrain.new() if region_id == "cinderfall" else ZoneTerrain.new())
	sanctuary = SafeArea.new()
	sanctuary.position = Vector3(0, 0, 48) if region_id == "cinderfall" else Vector3(0, 0, 15)
	sanctuary.radius = 11
	add_child(sanctuary)
	# The original gate stays at z=5; expanded markets behind it are also safe.
	for point in ([] if region_id == "cinderfall" else [Vector3(-17,0,29),Vector3(17,0,29),Vector3(0,0,43)]):
		var market_safe := SafeArea.new()
		market_safe.position = point
		market_safe.radius = 17
		add_child(market_safe)
	if region_id == "briarwood":
		settlement = Settlement.new()
		add_child(settlement)
	_lighting()
	player = ActorBody.new()
	player.name = "Traveler"
	player.title = identity.get("name", "Traveler")
	player.set_meta("class_identity", identity.get("class", "Ironvow"))
	player.position = (Vector3(0, 0, 48) if region_id == "cinderfall" else ZoneTerrain.START) + Vector3.UP * 0.1
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
	player.actions = PlayerActions.new()
	player.actions.actor = player
	player.add_child(player.actions)
	player.mounts = PlayerMount.new()
	player.mounts.actor = player
	player.add_child(player.mounts)
	player.add_child(load("res://scripts/audio/actor_audio.gd").new())
	player.map_state = PlayerMap.new()
	player.map_state.actor = player
	if region_id == "cinderfall": player.map_state.region = load("res://data/maps/cinderfall.tres")
	player.add_child(player.map_state)
	var cone = load("res://scripts/combat/combat_cone.gd").new()
	cone.enabled = false
	player.add_child(cone)
	if region_id == "cinderfall":
		_build_cinderfall()
	else:
		_build_briarwood()
	player.farming = FarmingState.new()
	add_child(player.farming)
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
	player.visual.apply_class_tint(String(player.get_meta("class_identity", "Ironvow")))
	get_tree().auto_accept_quit = false
	var navigation := ZoneNavigation.new()
	add_child(navigation)
	navigation.build(self)
	if identity.get("transitioning", false):
		identity.erase("transitioning")
		get_tree().root.set_meta("character_login", identity)
		save_progress(false)

func _build_briarwood() -> void:
	var names := ["Briarwood Verge", "Old Pine Hollow", "The Broken Cairn"]
	for i in range(3):
		var camp := EnemyCamp.new()
		camp.streaming_enabled = true
		camp.observer = player
		camp.position = ZoneTerrain.CAMPS[i]
		camp.camp_name = names[i]
		camp.count = 3 + i
		# Keep the narrow through-road clear of idle bodies at Old Pine Hollow.
		if i == 1:
			camp.spawn_points.assign([Vector3(4.5,0.1,-2),Vector3(6,0.1,-2),Vector3(4.5,0.1,1),Vector3(6,0.1,1)])
		camp.enemy_data = load("res://data/enemies/%s.tres" % ["young_mosslings", "grown", "ironback"][i])
		add_child(camp)
		camps.append(camp)
		_landmark(camp.position + Vector3(-3, 0, 1.5), names[i] + "\n" + ["Young mosslings - first hunt", "Mosslings - better gear advised", "Ironbacks - danger"][i])
	for i in FirstMapContent.IDS.size():
		var camp := EnemyCamp.new()
		camp.streaming_enabled = true
		camp.observer = player
		camp.enemy_data = load("res://data/enemies/%s.tres" % FirstMapContent.IDS[i])
		camp.camp_name = camp.enemy_data.display_name
		camp.position = FirstMapContent.POINTS[i]
		# Three ordinary members keep cold-start overlapping clearings within
		# the measured simulation budget; elites and opening camps retain size.
		camp.count = 3 if camp.enemy_data.tier <= 2 else 1
		camp.leash_distance = 20
		camp.respawn_delay = 45 if camp.enemy_data.tier <= 2 else 120 + camp.enemy_data.tier * 30
		add_child(camp)
		camps.append(camp)
		_landmark(camp.position + Vector3(0,0,7), "%s / Lv.%d / T%d" % [camp.camp_name,camp.enemy_data.level,camp.enemy_data.tier])
	_landmark(ZoneTerrain.START + Vector3(3, 0, 4), "Briar Crossing - Waystone Refuge\nRest here to heal")
	portal = RegionPortal.new()
	portal.position = Vector3(0, 0, -1)
	portal.title = "Cinderfall Basin / Lv.18+"
	add_child(portal)

func _build_cinderfall() -> void:
	for spec in [["ember_hound", Vector3(-28,0,13), 6], ["glass_spider", Vector3(27,0,-15), 6], ["ash_wisp", Vector3(-23,0,-50), 5], ["rift_sentinel", Vector3(23,0,-70), 1]]:
		var camp := EnemyCamp.new()
		camp.enemy_data = load("res://data/enemies/%s.tres" % spec[0])
		camp.camp_name = camp.enemy_data.display_name
		camp.position = spec[1]
		camp.count = spec[2]
		camp.leash_distance = 20
		camp.respawn_delay = 75
		add_child(camp)
		camps.append(camp)
		_landmark(camp.position + Vector3(0,0,6), "%s / Lv.%d" % [camp.camp_name, camp.enemy_data.level])
	var npc := WorldNPC.new()
	npc.data = load("res://data/npcs/ash_scout.tres")
	npc.position = Vector3(5,0,46)
	add_child(npc)
	_landmark(Vector3(0,0,48), "Cinderfall Outpost")
	portal = RegionPortal.new()
	portal.destination = "briarwood"
	portal.title = "Briarwood March"
	portal.position = Vector3(0,0,62)
	add_child(portal)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pickup") and portal and portal.can_use(player):
		travel(portal.destination)
		get_viewport().set_input_as_handled()
		return
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
	if event.is_action_pressed("tonic"): player.actions.activate(0)
	if event.is_action_pressed("quick_second"): player.actions.activate(1)
	if event.is_action_pressed("mount"): player.mounts.toggle()
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
	if player.mounts: player.mounts.dismount()
	if player.skills: player.skills.cancel_transient()
	if player.world_interaction: player.world_interaction.cancel()
	for camp in camps: camp.pack.disengage()
	if player.ui_session: player.ui_session.close()
	player.position = (Vector3(0, 0, 48) if region_id == "cinderfall" else ZoneTerrain.START) + Vector3.UP * 0.1
	player.velocity = Vector3.ZERO
	player.health.current = player.health.maximum
	player.health.changed.emit(player.health.current, player.health.maximum)
	player.collision_layer = 2
	player.collision_mask = 11
	player.combat.cancel()
	announce("Recovered at the waystone")

func travel(destination: String) -> void:
	if not persistence_enabled or not save_progress(false): return
	var identity: Dictionary = get_tree().root.get_meta("character_login", {})
	identity["region"] = destination
	identity["transitioning"] = true
	get_tree().root.set_meta("character_login", identity)
	get_tree().change_scene_to_file("res://scenes/cinderfall_zone.tscn" if destination == "cinderfall" else "res://scenes/outdoor_zone.tscn")

func _physics_process(delta: float) -> void:
	save_clock += delta
	if persistence_enabled and save_clock >= 30:
		save_clock = 0
		save_progress(false)
	notice_time = maxf(0, notice_time - delta)
	if player.health.is_alive() and SafeArea.protects(player) and not player.combat.is_attacking():
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
	sky_material.sky_top_color = Color("627e99")
	sky_material.sky_horizon_color = Color("bcc9c5")
	sky_material.ground_horizon_color = Color("bcc9c5")
	sky_material.ground_bottom_color = Color("38484e")
	if region_id == "cinderfall":
		sky_material.sky_top_color = Color("41445a")
		sky_material.sky_horizon_color = Color("9c9293")
		sky_material.ground_horizon_color = Color("777582")
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(.67,.74,.79)
	environment.ambient_light_energy = .58
	environment.fog_enabled = true
	environment.fog_light_color = Color("a6bdbd")
	environment.fog_density = .005
	if region_id == "cinderfall":
		environment.ambient_light_color = Color("9aa5bf")
		environment.ambient_light_energy = .48
		environment.fog_light_color = Color("828191")
		environment.fog_density = .006
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, -28, 0)
	sun.light_color = Color(1, 0.94, 0.83)
	if region_id == "cinderfall": sun.light_color = Color("edc8a5")
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70
	sun.shadow_bias = .035
	sun.shadow_normal_bias = .65
	add_child(sun)

func _landmark(point: Vector3, title: String) -> void:
	var label := Label3D.new()
	label.position = point + Vector3.UP * 2.6
	label.text = title.get_slice("\n", 0)
	label.font_size = 18
	label.visibility_range_end = 20
	label.pixel_size = 0.0013
	label.fixed_size = true
	label.modulate = Color(0.95, 0.82, 0.53)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

func save_progress(notify_player: bool = true) -> bool:
	if not persistence_enabled: return false
	var success := persistence.save_player(player)
	if notify_player or not success: announce("Progress saved" if success else "Save failed: " + persistence.error)
	return success

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		save_progress(false)
		get_tree().quit()

func _process(_delta: float) -> void:
	ForgeModelCatalogue.collect_ready()
