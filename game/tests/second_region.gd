extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world = load("res://scenes/cinderfall_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(5)
	check(world.region_id == "cinderfall" and world.player.map_state.region.id == &"cinderfall", "Cinderfall loads its own map")
	check(world.camps.size() == 4, "Cinderfall has four distinct encounters")
	check(world.portal.destination == "briarwood" and world.portal.can_use(world.player) == false, "Return portal requires approach")
	var ids := {}
	for camp: EnemyCamp in world.camps: ids[camp.enemy_data.id] = true
	check(ids.has_all([&"ember_hound", &"glass_spider", &"ash_wisp", &"rift_sentinel"]), "Second map spawns its own monsters")
	for id in [&"through_the_veil", &"shattered_web", &"heart_of_the_rift"]:
		check(QuestCatalog.all().has(id), "Quest registered: " + String(id))
	for id in [&"ember_fang", &"glass_sabre", &"rift_cleaver"]:
		var item := ItemCatalog.get_item(id)
		check(item != null and item.icon != null and item.visual != null, "Sword and matching inventory icon: " + String(id))
		var visual: Node3D = item.visual.instantiate()
		root.add_child(visual)
		var blades := visual.find_children("*","MeshInstance3D",true,false)
		check(not blades.is_empty() and blades[0].mesh.get_surface_count() >= 4 and blades[0].mesh.get_aabb().size.length() > 1.6 and visual.has_node("OffhandGrip"), "Sword has authored blade, fittings and long grip: " + String(id))
		visual.queue_free()
	var scout: WorldNPC
	for npc in get_nodes_in_group("npcs"):
		if npc.data.id == &"ash_scout": scout = npc
	check(scout != null, "Scout Vela offers Cinderfall contracts")
	world.player.global_position = scout.global_position + Vector3(1.2,0,0)
	world.player.progression.level = 20
	world.player.quests.states["through_the_veil"] = {"status":"completed","counts":[3,0]}
	await frames(2)
	check(world.player.quests.accept(&"shattered_web", scout), "Scout quest can be accepted")
	world.player.quests.record(&"kill", &"glass_spider", 4)
	check(world.player.quests.ready(QuestCatalog.all()[&"shattered_web"]), "Glass Spider kills advance quest")
	check(world.player.quests.claim(&"shattered_web", scout).is_empty(), "Quest rewards the matching Glass Sabre")
	check(world.player.inventory.count(&"glass_sabre") == 1, "Quest sword enters inventory")
	var target: ActorBody = world.camps[0].pack.members[0]
	var before: int = world.get_child_count()
	target.health.apply_damage(12, null)
	check(world.get_child_count() == before + 1, "Damage creates floating manga caption")
	await frames(60)
	check(world.get_child_count() == before, "Damage caption cleans itself up")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/cinderfall_review.png")
	var save_path := "user://second_region_portal_test.json"
	root.set_meta("character_login", {"name":"PortalTest","class":"Ironvow","path":save_path})
	world.persistence.path = save_path
	world.persistence_enabled = true
	world.player.global_position = world.portal.global_position + Vector3(1,0,0)
	check(world.portal.can_use(world.player), "Portal activates in interaction range")
	world.travel("briarwood")
	await frames(5)
	check(current_scene is Node3D and current_scene.region_id == "briarwood", "Portal returns to Briarwood")
	check(FileAccess.file_exists(save_path), "Travel preserves character save")
	var saved: Variant = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	check(saved is Dictionary and saved.get("region") == "briarwood", "Destination is saved for next login")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/briarwood_return_review.png")
	check(current_scene.portal.position.z == -1 and current_scene.portal.destination == "cinderfall", "Briarwood portal stands beyond the north gate")
	current_scene.player.global_position = current_scene.portal.global_position + Vector3(1,0,0)
	check(current_scene.portal.can_use(current_scene.player), "North gate portal accepts interaction")
	current_scene.travel("cinderfall")
	await frames(5)
	check(current_scene.region_id == "cinderfall", "Briarwood portal enters Cinderfall")
	if current_scene: current_scene.queue_free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(save_path))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(save_path + ".bak"))
	root.remove_meta("character_login")
	await frames(2)
	print("Second region: %d failures" % failures)
	quit(1 if failures else 0)
