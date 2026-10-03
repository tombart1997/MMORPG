extends "res://tests/mmorpg_loop.gd"
## Render and exercise the actual scene at reference, 1080p and 1440p sizes.
func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(10)
	player = world.player
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	check(hud != null,"World HUD is present")
	check(hud.hp.value == player.health.current,"Painted HP follows live health")
	for dimensions in [Vector2i(1280,720),Vector2i(1920,1080),Vector2i(2560,1440)]:
		root.size = dimensions
		await frames(5)
		for control in [player.ui_session.quick_bar,hud.local_log]:
			var rect: Rect2 = control.get_global_rect()
			check(rect.position.x >= 0 and rect.position.y >= 0 and rect.end.x <= control.get_viewport_rect().size.x and rect.end.y <= control.get_viewport_rect().size.y,"Bottom HUD stays on canvas at %s" % dimensions)
		player.ui_session.open_panel(hud.inventory_panel)
		await frames(4)
		check(hud.inventory_panel.get_global_rect().end.x <= hud.inventory_panel.get_viewport_rect().size.x,"Inventory fits at %s" % dimensions)
		check(hud.inventory_panel.get_global_rect().end.y <= hud.inventory_panel.get_viewport_rect().size.y,"Inventory height fits at %s" % dimensions)
		await capture("painted_inventory_%d" % dimensions.y)
		player.ui_session.close()
		await frames(2)
		await capture("painted_hud_%d" % dimensions.y)
	root.size = Vector2i(1280,720)
	player.ui_session.open_panel(hud.inventory_panel)
	await frames(3)
	var chrome: WindowChrome
	for child in hud.inventory_panel.get_children():
		if child is WindowChrome: chrome = child
	check(chrome != null,"Inventory has reusable window chrome")
	var before := hud.inventory_panel.position
	var origin := chrome.global_position + Vector2(90,12)
	await mouse(origin,true)
	var movement := InputEventMouseMotion.new()
	movement.position = origin - Vector2(110,60)
	movement.relative = Vector2(-110,-60)
	movement.button_mask = MOUSE_BUTTON_MASK_LEFT
	Input.parse_input_event(movement.xformed_by(root.get_final_transform()))
	await frames(3)
	await mouse(origin-Vector2(110,60),false)
	check(hud.inventory_panel.position.distance_to(before)>20,"Title strip drags the window")
	var expanded := hud.inventory_panel.size
	chrome.toggle_collapsed()
	await frames(2)
	check(hud.inventory_panel.size.y < expanded.y,"Window collapses without closing its session")
	chrome.toggle_collapsed()
	await frames(2)
	check(hud.inventory_panel.size.is_equal_approx(expanded),"Expanding restores window dimensions")
	player.ui_session.close()
	for panel in [player.ui_session.journal,player.ui_session.world_map]:
		player.ui_session.open_panel(panel)
		await frames(4)
		check(panel.get_global_rect().end.y <= panel.get_viewport_rect().size.y,"Utility window fits reference height")
		await capture("painted_" + ("journal" if panel is QuestJournal else "map"))
		player.ui_session.close()
	for npc in world.settlement.npcs:
		player.global_position = npc.global_position + Vector3(1,0,1)
		await frames(2)
		if npc.data.role == &"smith":
			hud.smith_panel.open_npc(npc)
			await frames(4)
			await capture("painted_forge")
		elif npc.data.shop:
			hud.town_panel.open_npc(npc)
			await frames(4)
			await capture("painted_shop")
		else: continue
		check(player.ui_session.active.get_global_rect().end.y <= hud.inventory_panel.get_viewport_rect().size.y,"NPC window fits reference height")
		check(player.ui_session.active.get_global_rect().end.x <= hud.inventory_panel.get_viewport_rect().size.x,"NPC window fits reference width")
		player.ui_session.close()
	print("PAINTED_UI failures=",failures)
	quit(1 if failures else 0)
