extends "res://tests/combat_smoke.gd"
## Sustained controller-driven traversal through dense districts, with resident streaming.
func _run() -> void:
	var world=load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled=false
	root.add_child(world)
	current_scene=world
	await frames(15)
	var player: ActorBody=world.player
	var peak:=0
	var visited: Dictionary={}
	# Start and finish each district on an authored travel lane. Walking uses the normal
	# controller/navigation/physics; relocation only skips the long inter-district journey.
	for district in [[Vector3(0,0,0),Vector3(-85,0,-8)],
		[Vector3(-95,0,-75),Vector3(-36,0,-88)],
		[Vector3(95,0,-133),Vector3(36,0,-133)],
		[Vector3(-95,0,-177),Vector3(-36,0,-177)],
		[Vector3(95,0,-222),Vector3(36,0,-222)],
		[Vector3(-95,0,-235),Vector3(-95,0,-275)]]:
		world.respawn_player()
		player.global_position=district[0]+Vector3.UP*.1
		await frames(20)
		player.world_interaction.command({"kind":&"terrain","position":district[1],"normal":Vector3.UP})
		check(player.navigation.active,"Dense district accepts a normal movement command")
		for tick in range(2000):
			await physics_frame
			# Art/performance route does not depend on a fresh character's level.
			player.health.current=player.health.maximum
			peak=maxi(peak,get_nodes_in_group("enemies").size())
			for camp in world.camps:
				if not camp.dormant: visited[camp]=true
			if not player.navigation.active: break
		print("ROUTE target=",district[1]," position=",player.global_position," failure=",player.navigation.failure)
		check(player.global_position.distance_to(district[1])<2.5,"Controller traverses dense district without scenery blocking the road")
		check(get_nodes_in_group("enemies").size()<300,"Dense district retains fewer than one third of the map's actors")
	world.respawn_player()
	await frames(30)
	check(visited.size()>45,"Sustained route activates many distinct spawn groups")
	check(get_nodes_in_group("enemies").size()<150,"Returning home releases distant populations")
	print("TRAVERSAL peak_actors=",peak," visited_groups=",visited.size()," failures=",failures)
	world.queue_free()
	await frames(2)
	quit(1 if failures else 0)
