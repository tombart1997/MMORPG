extends "res://tests/combat_smoke.gd"
## Terrain changes must keep production travel, encounter floors and loot usable.
func _run() -> void:
	for point in ZoneTerrain.ROAD+ZoneTerrain.OUTER_ROAD+ZoneTerrain.CAMPS+FirstMapContent.POINTS:
		check(absf(ZoneTerrain.height_at(point.x,point.z))<.01,"Existing Briarwood route/camp floor stays level")
	for point in CinderfallTerrain.CAMPS:
		check(absf(CinderfallTerrain.height_at(point.x,point.z))<.01,"Cinderfall encounter floor stays level")
	var world = load("res://scenes/cinderfall_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(12)
	var player: ActorBody = world.player
	check(player.is_on_floor(),"Player spawns grounded at the rebuilt outpost")
	for destination in [Vector3(0,0,28),Vector3(-6,0,8),Vector3(5,0,-22),Vector3(0,0,-48)]:
		player.world_interaction.command({"kind":&"terrain","position":destination,"normal":Vector3.UP})
		check(player.navigation.active,"Basin road accepts normal click travel")
		for tick in 1500:
			await physics_frame
			player.health.current = player.health.maximum
			if not player.navigation.active: break
		check(player.position.distance_to(destination)<1.1,"Normal controller reaches basin route point")
		check(player.is_on_floor(),"Basin travel retains floor contact")
	for camp: EnemyCamp in world.camps:
		var map := player.get_world_3d().navigation_map
		var projected := NavigationServer3D.map_get_closest_point(map,camp.global_position)
		var route := NavigationServer3D.map_get_path(map,player.global_position,projected,true)
		check(projected.distance_to(camp.global_position)<.6 and not route.is_empty(),"Every basin encounter is reachable on baked terrain")
	var target: ActorBody = world.camps[0].pack.members[0]
	target.health.apply_damage(9999,player)
	await frames(2)
	for drop in get_nodes_in_group("loot"):
		check(absf(drop.global_position.y-CinderfallTerrain.height_at(drop.global_position.x,drop.global_position.z))<.1,"Encounter rewards sit on the basin terrain")
	world.queue_free()
	await frames(2)
	print("WORLD_LANDSCAPE failures=",failures)
	quit(1 if failures else 0)
