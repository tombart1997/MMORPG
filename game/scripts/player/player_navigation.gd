class_name PlayerNavigation
extends Node
## Paths come from the baked Godot navigation map. Controllers still apply physical motion.
signal arrived
var actor: ActorBody
var path := PackedVector3Array()
var index: int = 0
var destination := Vector3.ZERO
var active: bool = false
var last_position := Vector3.ZERO
var stuck_time: float = 0
var failure: String = ""

func command(point: Vector3) -> bool:
	var map := actor.get_world_3d().navigation_map
	if NavigationServer3D.map_get_iteration_id(map) == 0: return false
	var projected := NavigationServer3D.map_get_closest_point(map, point)
	if projected.distance_to(point) > 2.5:
		failure = "That point is not reachable."
		return false
	path = NavigationServer3D.map_get_path(map, actor.global_position, projected, true)
	if path.is_empty() or path[-1].distance_to(projected) > 1.0:
		failure = "No route to that point."
		return false
	destination = projected
	index = 0
	active = true
	stuck_time = 0
	last_position = actor.global_position
	failure = ""
	return true

func cancel() -> void:
	active = false
	path.clear()

func direction(delta: float) -> Vector3:
	if not active: return Vector3.ZERO
	while index < path.size():
		var offset := path[index] - actor.global_position
		offset.y = 0
		var tolerance := 0.12 if actor.mounts and actor.mounts.mounted and index < path.size()-1 else 0.35
		if offset.length() > tolerance: break
		index += 1
	if index >= path.size():
		cancel()
		arrived.emit()
		return Vector3.ZERO
	if actor.global_position.distance_to(last_position) < 0.01: stuck_time += delta
	else: stuck_time = 0
	last_position = actor.global_position
	if stuck_time > 2.5:
		cancel()
		failure = "Path blocked. Choose another point."
		return Vector3.ZERO
	var offset := path[index] - actor.global_position
	offset.y = 0
	return offset.normalized()
