class_name EnemyCrowd
extends Node
## One spatial snapshot per scene at 10 Hz. Physics/commitments remain full rate.
var cells: Dictionary = {}
var clock: float = 0
var rebuilds: int = 0
var candidates: int = 0
const CELL: float = 1.5
func _physics_process(delta: float) -> void:
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
