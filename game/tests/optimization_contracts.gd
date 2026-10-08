extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world=load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled=false
	root.add_child(world);current_scene=world
	await frames(15)
	var player:ActorBody=world.player
	var grove:=world.find_child("AmberScarArt",true,false) as BriarwakeGrove
	var fading_meshes:=0
	for mesh: MeshInstance3D in grove.find_children("*","MeshInstance3D",true,false):
		if not mesh.get_meta("camera_clearance",false):continue
		fading_meshes+=1
		for surface in mesh.mesh.get_surface_count():
			var material:=mesh.get_active_material(surface) as StandardMaterial3D
			check(material.distance_fade_mode==BaseMaterial3D.DISTANCE_FADE_PIXEL_DITHER and is_equal_approx(material.distance_fade_min_distance,8.0),"Authored grove tree receives mounted camera clearance")
	check(fading_meshes>0,"Authored grove trees use the clearance material path")
	var camp:EnemyCamp=world.camps[0]
	player.position=camp.position+Vector3(0,.1,4)
	await frames(15)
	var crowd:EnemyCrowd=world.get_meta("enemy_crowd")
	crowd.set_physics_process(false)
	crowd.route_queue.clear();crowd.queued_routes.clear()
	camp.pack.target=player
	var brains:Array[EnemyBrain]=[]
	for actor in camp.pack.members:
		for child in actor.get_children():
			if child is EnemyBrain:
				child.set_physics_process(false)
				brains.append(child)
				crowd.request_route(child);crowd.request_route(child)
	check(crowd.route_queue.size()==brains.size(),"Duplicate route requests share one queue entry")
	var remaining:=brains.size()
	for tick in 10:
		crowd._resolve_routes()
		check(crowd.path_queries_last_tick<=EnemyCrowd.PATH_QUERIES_PER_TICK,"Route requests respect the per-tick query budget")
		remaining=crowd.route_queue.size()
		if remaining==0:break
	check(remaining==0 and crowd.queued_routes.is_empty(),"Queued pack paths drain and release their identities")
	for brain in brains:check(not brain.route.is_empty(),"Deferred route reaches the real navigation map")
	var stale:=EnemyBrain.new()
	crowd.request_route(stale)
	stale.free()
	crowd._resolve_routes()
	check(crowd.route_queue.is_empty() and crowd.queued_routes.is_empty(),"Unloaded actors leave no stale queue identities")
	camp.pack.disengage()
	crowd.request_route(brains[0]);crowd._resolve_routes()
	check(crowd.path_queries_last_tick==0 and crowd.queued_routes.is_empty(),"Disengaged packs do not compute obsolete routes")
	var hud:ZoneHUD
	for node in world.get_children():
		if node is ZoneHUD:hud=node
	var panel:=hud.inventory_panel
	panel.select_slot(0)
	var selected:=panel.selected
	var slot_style:=panel.bag_buttons[0].get_theme_stylebox("normal")
	player.health.apply_damage(7, null)
	check(panel.stat_values["HP"].text=="%d/%d"%[player.health.current,player.health.maximum],"Damage updates the hidden inventory HP label immediately")
	check(panel.selected==selected and panel.bag_buttons[0].get_theme_stylebox("normal")==slot_style,"Health changes retain inventory selection and slot styles")
	var log:EventLog=hud.local_log
	log.history.clear();log.refresh()
	for i in 20:log.append("Combat","Batch hit %d"%i)
	check(log.history.size()==20 and log.refresh_pending,"A damage batch retains every entry before repaint")
	log._process(.11)
	check(log.feed.get_parsed_text().contains("Batch hit 19"),"The log displays the latest batch within its refresh interval")
	log.hide();log.append("System","Hidden entry")
	log._process(.11)
	check(log.refresh_pending,"Hidden logs retain pending updates")
	log.show();log._process(.11)
	check(log.feed.get_parsed_text().contains("Hidden entry"),"Showing the log catches up without losing events")
	log.channel="System";log.refresh()
	check(log.feed.get_parsed_text().contains("Hidden entry") and not log.feed.get_parsed_text().contains("Batch hit"),"Channel changes preserve history and update filtering")
	print("OPTIMIZATION_CONTRACTS failures=",failures)
	quit(1 if failures else 0)
