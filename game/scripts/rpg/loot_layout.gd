class_name LootLayout
extends Node
## A single bounded label pass, shared by all ground entries in this scene.
var clock: float = 0
func _process(delta: float) -> void:
	clock -= delta
	if clock > 0: return
	clock = 0.1
	var camera := get_viewport().get_camera_3d()
	if camera == null: return
	var drops := get_tree().get_nodes_in_group("loot")
	drops.sort_custom(func(a, b):
		if a.is_rare() != b.is_rare(): return a.is_rare()
		return a.global_position.distance_squared_to(camera.global_position) < b.global_position.distance_squared_to(camera.global_position))
	var occupied: Dictionary = {}
	var common_count := 0
	for drop: LootPickup in drops:
		var point := drop.global_position + Vector3.UP * 0.7
		var distance := camera.global_position.distance_to(point)
		drop.label.visible = not camera.is_position_behind(point) and distance < 30 and (drop.is_rare() or common_count < 18)
		if not drop.label.visible: continue
		if not drop.is_rare(): common_count += 1
		var screen := camera.unproject_position(point)
		var view := get_viewport().get_visible_rect().size
		screen.x = clampf(screen.x, 120, view.x - 120)
		screen.y = clampf(screen.y, 200, view.y - 200)
		var key := Vector2i(floori(screen.x / 190), floori(screen.y / 30))
		for attempt in 32:
			if not occupied.has(key) and not occupied.has(key + Vector2i(1, 0)) and not occupied.has(key - Vector2i(1, 0)): break
			key.y -= 1
		if key.y * 30 < 190 and not drop.is_rare():
			drop.label.hide()
			continue
		occupied[key] = true
		screen.y = key.y * 30 + 15
		drop.label.global_position = camera.project_position(screen, -camera.to_local(point).z)
