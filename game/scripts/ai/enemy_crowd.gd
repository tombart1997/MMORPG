class_name EnemyCrowd
extends Node
## One spatial snapshot per scene at 10 Hz. Physics/commitments remain full rate.
var cells: Dictionary = {}
var clock: float = 0
var rebuilds: int = 0
var candidates: int = 0
var route_queue: Array[Dictionary] = []
var queued_routes: Dictionary = {}
var path_queries_last_tick := 0
const PATH_QUERIES_PER_TICK := 2
const PATH_TIME_BUDGET_USEC := 1000
const CELL: float = 1.5

func request_route(brain: EnemyBrain) -> void:
	var identity:=brain.get_instance_id()
	if queued_routes.has(identity):return
	queued_routes[identity]=true
	route_queue.append({"identity":identity,"brain":brain})

func _resolve_routes() -> void:
	path_queries_last_tick=0
	var started:=Time.get_ticks_usec()
	while not route_queue.is_empty() and path_queries_last_tick<PATH_QUERIES_PER_TICK:
		var request: Dictionary=route_queue.pop_front()
		queued_routes.erase(request.identity)
		if not is_instance_valid(request.brain):continue
		var brain: EnemyBrain=request.brain
		if not is_instance_valid(brain.actor) or not brain.actor.is_inside_tree() or not brain.actor.health.is_alive():continue
		if not is_instance_valid(brain.pack) or not brain.pack.has_target():continue
		var map:=brain.actor.get_world_3d().navigation_map
		if NavigationServer3D.map_get_iteration_id(map)==0:continue
		brain.route=NavigationServer3D.map_get_path(map,brain.actor.global_position,brain.pack.target.global_position,true)
		path_queries_last_tick+=1
		if Time.get_ticks_usec()-started>=PATH_TIME_BUDGET_USEC:break

func _physics_process(delta: float) -> void:
	if not RuntimeCosts.enabled:
		_profiled__physics_process(delta)
		return
	var started:=Time.get_ticks_usec()
	_profiled__physics_process(delta)
	RuntimeCosts.record(&"crowd",started)

func _profiled__physics_process(delta: float) -> void:
	# Obstructed packs can request paths together. Spread expensive map queries
	# over ticks; actors keep their previous route and physical collision meantime.
	var route_started:=Time.get_ticks_usec() if RuntimeCosts.enabled else 0
	_resolve_routes()
	if RuntimeCosts.enabled:RuntimeCosts.record(&"navigation",route_started)
	clock -= delta
	if clock > 0: return
	clock = 0.1
	cells.clear()
	rebuilds += 1
	var players := get_tree().get_nodes_in_group("players")
	var player: ActorBody = players[0] if not players.is_empty() else null
	var nearest: ActorBody
	var nearest_distance: float = 16
	for actor: ActorBody in get_tree().get_nodes_in_group("enemies"):
		if not actor.health.is_alive(): continue
		actor.visual.nameplate_allowed = false
		if player:
			var distance := player.global_position.distance_squared_to(actor.global_position)
			if distance < nearest_distance: nearest = actor; nearest_distance = distance
		var key := Vector2i(floori(actor.global_position.x / CELL), floori(actor.global_position.z / CELL))
		if not cells.has(key): cells[key] = []
		cells[key].append(actor)
	var selected: ActorBody = player.world_interaction.selected_enemy if player and player.world_interaction else null
	if is_instance_valid(selected) and selected.health.is_alive(): selected.visual.nameplate_allowed = true
	elif is_instance_valid(nearest): nearest.visual.nameplate_allowed = true
func separation(actor: ActorBody) -> Vector3:
	var result := Vector3.ZERO
	var key := Vector2i(floori(actor.global_position.x / CELL), floori(actor.global_position.z / CELL))
	for x in range(-1, 2):
		for y in range(-1, 2):
			for candidate in cells.get(key + Vector2i(x, y), []):
				if not is_instance_valid(candidate): continue
				var other: ActorBody = candidate
				if other == actor or not other.health.is_alive(): continue
				candidates += 1
				var away := actor.global_position - other.global_position
				away.y = 0
				var length := away.length()
				if length > 0.001 and length < 1.05: result += away / length * (1.05 - length) * 5
	return result.limit_length(4.5)
