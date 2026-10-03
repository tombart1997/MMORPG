extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(15)
	var player: ActorBody = world.player
	check(world.camps.size()==FirstMapContent.POINTS.size()+3,"All authored spawn groups survive streaming")
	check(get_nodes_in_group("enemies").size()<200,"Starting settlement does not instantiate the whole map")
	var far: EnemyCamp = world.camps.back()
	check(far.dormant and far.pack.members.is_empty(),"Distant camp has no combat actors")
	var camp: EnemyCamp = world.camps[0]
	player.position = camp.position+Vector3(0,.1,4)
	await frames(15)
	check(camp.pack.members[0].simulation_interval==0,"Nearby actors retain full simulation")
	player.position = camp.position+Vector3(0,.1,40)
	await frames(15)
	check(camp.pack.members[0].simulation_interval==.2,"Unengaged medium actors use reduced updates")
	player.position = camp.position+Vector3(0,.1,4)
	await frames(15)
	var survivor: ActorBody = camp.pack.members[1]
	survivor.health.current -= 10
	var health := survivor.health.current
	camp.pack.members[0].health.apply_damage(10000,player)
	var kills := player.progression.kills
	var generation := camp.generation
	camp.pack.disengage()
	player.position = ZoneTerrain.START
	# Use a farther safe location to cross the unload threshold.
	player.position = Vector3(0,.1,62)
	await frames(35)
	check(camp.dormant and camp.pack.members.is_empty(),"Leaving unloads actors while retaining encounter state")
	player.position = camp.position+Vector3(0,.1,4)
	await frames(20)
	check(camp.generation==generation and camp.pack.living_count()==camp.count-1,"Returning does not resurrect killed members")
	check(is_equal_approx(camp.pack.members[0].health.current,health),"Partial damage survives unloading")
	check(player.progression.kills==kills,"Reloading never duplicates rewards")
	# Status effects cannot be dodged by unloading an encounter.
	var retained: ActorBody = camp.pack.members[0]
	retained.statuses.add(&"slow",5,.2,player)
	camp.pack.disengage()
	player.position = Vector3(0,.1,62)
	camp.update_residency()
	check(not camp.dormant,"A pending status prevents unloading")
	retained.statuses.clear()
	camp.update_residency()
	await frames(2)
	check(camp.dormant,"Unloading resumes after transient effects end")
	player.position = camp.position+Vector3(0,.1,4)
	await frames(20)
	camp.respawn_delay = .4
	for member in camp.pack.members.duplicate(): member.health.apply_damage(10000,player)
	var cleared_kills := player.progression.kills
	await frames(35)
	check(camp.generation==generation,"Respawn waits while player occupies the clearing")
	player.position = Vector3(0,.1,62)
	await frames(35)
	check(camp.generation==generation+1 and camp.dormant,"Respawn timer advances without creating distant actors")
	player.position = camp.position+Vector3(0,.1,8)
	await frames(20)
	check(camp.pack.living_count()==camp.count and player.progression.kills==cleared_kills,"Re-entering activates one fresh generation without rewards")
	var nav := player.get_world_3d().navigation_map
	for npc in world.settlement.npcs:
		var route := NavigationServer3D.map_get_path(nav,ZoneTerrain.START,npc.global_position,true)
		check(not route.is_empty() and route[-1].distance_to(npc.global_position)<2,"Service access preserved: %s" % npc.name)
	for index in [0,1,2,world.camps.size()/2,world.camps.size()-1]:
		var target: EnemyCamp = world.camps[index]
		var route := NavigationServer3D.map_get_path(nav,ZoneTerrain.START,target.global_position,true)
		check(not route.is_empty() and route[-1].distance_to(target.global_position)<2,"Progression camp remains navigable: %d" % index)
	print("REMASTER_STREAMING failures=",failures)
	quit(1 if failures else 0)
