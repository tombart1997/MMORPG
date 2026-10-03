class_name WorldFracture
extends Node3D
signal notice_requested(message: String)
## Encounter lifetime, not combat authority. Existing Health/Melee own all hits.
@export var data: FractureData
@export var location_id: String = "hollow_briarwake"
var body: ActorBody
var target: ActorBody
var active: bool = false
var remaining: float = 0
var abandon: float = 0
var next_wave: int = 0
var warning: float = 0
var pending: Array[Vector3] = []
var markers: Array[MeshInstance3D] = []
var defenders: Array[EnemyCamp] = []
var rng := RandomNumberGenerator.new()
var completions: int = 0
var loot_parent: Node3D
func _ready() -> void:
	add_to_group("world_fractures")
	spawn_body()
func spawn_body() -> void:
	if is_instance_valid(body):
		remove_child(body)
		body.queue_free()
	body = ActorBody.new()
	body.title = data.display_name
	body.faction = &"enemies"
	body.opponents = &"players"
	body.maximum_health = data.maximum_health
	body.visual_scene = load("res://scenes/visuals/briarwake_fracture.tscn")
	add_child(body)
	WorldClickable.attach(body, &"enemy", 3.0)
	body.health.damaged.connect(_damaged)
	body.health.died.connect(_destroyed)
	active = false
	target = null
	next_wave = 0
	abandon = 0
	_update_damage_floor()

func _update_damage_floor() -> void:
	# Burst damage may reach the following phase, but cannot erase unreleased waves.
	# This is a brief telegraph boundary, not extra health or additional reward rolls.
	var floor_value := 0.0
	if next_wave < data.waves.size():
		floor_value = 1.0
		if next_wave+1 < data.waves.size():
			floor_value = maxf(1.0,body.health.maximum*data.waves[next_wave+1].health_fraction)
	body.health.damage_floor = floor_value
func _damaged(_amount: float, source: Node3D) -> void:
	if source is ActorBody and source.health.is_alive() and source.faction == &"players":
		target = source
		active = true
		abandon = 0
		if pending.is_empty() and next_wave < data.waves.size() and body.health.current/body.health.maximum <= data.waves[next_wave].health_fraction:
			prepare_wave(data.waves[next_wave])
func clear_warning() -> void:
	for marker in markers:
		if is_instance_valid(marker): marker.queue_free()
	markers.clear()
	pending.clear()
	warning = 0
func reset_attempt() -> void:
	clear_warning()
	for camp in defenders:
		if is_instance_valid(camp): camp.queue_free()
	defenders.clear()
	if remaining <= 0: spawn_body()
	active = false
	target = null
func living_defenders() -> int:
	var total := 0
	for camp in defenders:
		if is_instance_valid(camp): total += camp.pack.living_count()
	return total
func prepare_wave(wave: FractureWave) -> void:
	var map := get_world_3d().navigation_map
	if NavigationServer3D.map_get_iteration_id(map) == 0: return
	for i in wave.count:
		for attempt in 20:
			var angle := rng.randf_range(0, TAU)
			var point := global_position + Vector3(sin(angle), 0, cos(angle)) * (data.spawn_radius + attempt * 0.16)
			point.y = ZoneTerrain.height_at(point.x, point.z)
			var projected := NavigationServer3D.map_get_closest_point(map, point)
			if projected.distance_to(point) > 0.7 or projected.distance_to(target.global_position) < 3.5: continue
			var clear := true
			for previous in pending:
				if previous.distance_to(projected) < 1: clear = false
			if not clear: continue
			pending.append(projected)
			var marker := SkillVFX.ring(0.65, Color(0.9, 0.55, 0.18))
			add_child(marker)
			marker.global_position = projected + Vector3.UP * 0.05
			markers.append(marker)
			break
	if pending.is_empty(): return
	warning = wave.warning_seconds
	notice_requested.emit("Briarwake stirs: %d defenders approaching" % pending.size())
func release_wave() -> void:
	var wave: FractureWave = data.waves[next_wave]
	var points: Array[Vector3] = []
	for point in pending:
		# The player can move onto a warning. Delay that individual spawn, never overlap.
		if is_instance_valid(target) and point.distance_to(target.global_position) >= 2.5:
			points.append(point - global_position)
	if points.is_empty(): clear_warning(); return
	var camp := EnemyCamp.new()
	camp.formation_override = true
	camp.enemy_data = wave.enemy
	camp.count = mini(points.size(), data.population_cap - living_defenders())
	camp.spawn_points = points
	camp.rewards_enabled = false # Completion owns reward budget; no reset-farming adds.
	camp.respawn_enabled = false
	camp.corpse_seconds = 5
	camp.leash_distance = data.leash_distance
	add_child(camp)
	camp.pack.target = target
	for point in points:
		ArtVFX.burst(self, point + Vector3.UP*.1, Color(.63,.55,.28), 5, .5)
	defenders.append(camp)
	next_wave += 1
	_update_damage_floor()
	clear_warning()
func _destroyed(source: Node3D) -> void:
	if remaining > 0: return
	active = false
	remaining = data.respawn_seconds
	completions += 1
	clear_warning()
	SkillVFX.flash(get_parent(), global_position, 3.3, Color(1, 0.72, 0.3), 360, 0)
	if source is ActorBody and source.progression:
		if source.quests: source.quests.record(&"fracture", &"briarwake")
		source.progression.award_xp(data.xp)
		var drops := data.rewards.roll(rng)
		create_drop(null, rng.randi_range(data.gold_min, data.gold_max), 0)
		for i in drops.size(): create_drop(drops[i], 0, i + 1)
	notice_requested.emit("Briarwake collapsed! Claim its scattered heart. Remaining defenders still fight.")
func create_drop(stack: ItemStack, coins: int, index: int) -> LootPickup:
	var drop := LootPickup.new()
	if stack: drop.item = stack.definition(); drop.quantity = stack.quantity
	drop.coins = coins
	drop.encounter_id = location_id
	loot_parent.add_child(drop)
	var angle := index * 2.39996
	drop.global_position = global_position + Vector3(sin(angle), 0, cos(angle)) * (1.5 + index * 0.25)
	drop.global_position.y = ZoneTerrain.height_at(drop.global_position.x, drop.global_position.z)
	return drop
func _physics_process(delta: float) -> void:
	if remaining > 0:
		remaining = maxf(0, remaining - delta)
		if remaining == 0:
			for player: ActorBody in get_tree().get_nodes_in_group("players"):
				if player.global_position.distance_to(global_position) < 10: remaining = 1; return
			reset_attempt()
		return
	if not active: return
	if not is_instance_valid(target) or not target.health.is_alive() or SafeArea.protects(target) or target.global_position.distance_to(global_position) > data.leash_distance:
		for camp in defenders:
			if is_instance_valid(camp): camp.pack.disengage()
		abandon += delta
		if abandon >= data.abandon_seconds: reset_attempt()
		return
	abandon = 0
	for camp in defenders:
		if is_instance_valid(camp) and not camp.pack.has_target(): camp.pack.target = target
	if not pending.is_empty():
		warning -= delta
		if warning <= 0: release_wave()
	elif next_wave < data.waves.size() and living_defenders() + data.waves[next_wave].count <= data.population_cap:
		if body.health.current / body.health.maximum <= data.waves[next_wave].health_fraction:
			prepare_wave(data.waves[next_wave])
