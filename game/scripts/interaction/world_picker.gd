class_name WorldPicker
extends RefCounted
static func pick(camera: Camera3D, screen: Vector2) -> Dictionary:
	var origin := camera.project_ray_origin(screen)
	var end := origin + camera.project_ray_normal(screen) * 180
	var space := camera.get_world_3d().direct_space_state
	# Labels extend the selectable area of small loot. Screen-nearest visible label wins.
	var selected: WorldClickable
	var nearest := INF
	for proxy in camera.get_tree().get_nodes_in_group("clickables"):
		if proxy.kind != &"loot" or not proxy.valid() or proxy.label == null or not proxy.label.visible: continue
		var point: Vector3 = proxy.label.global_position
		if camera.is_position_behind(point) or camera.global_position.distance_to(point) > 30: continue
		var delta: Vector2 = screen - camera.unproject_position(point)
		if absf(delta.x) > 85 or absf(delta.y) > 11: continue
		var ray := PhysicsRayQueryParameters3D.create(origin, point, 1)
		if not space.intersect_ray(ray).is_empty(): continue
		if delta.length_squared() < nearest:
			nearest = delta.length_squared()
			selected = proxy
	if selected: return {"kind": selected.kind, "target": selected.target, "position": selected.target.global_position}
	var query := PhysicsRayQueryParameters3D.create(origin, end, 5)
	query.collide_with_areas = true
	var hit := space.intersect_ray(query)
	if hit.is_empty(): return {}
	if hit.collider is WorldClickable:
		var proxy: WorldClickable = hit.collider
		if proxy.valid(): return {"kind": proxy.kind, "target": proxy.target, "position": proxy.target.global_position}
		return {}
	return {"kind": &"terrain", "position": hit.position, "normal": hit.normal}
