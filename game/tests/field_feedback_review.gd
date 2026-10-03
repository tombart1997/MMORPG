extends "res://tests/presentation_upgrade.gd"
## Rendered review and regressions for field readability and mounted blade clearance.
func _run() -> void:
	output = "res://.local/field_feedback"
	var args := OS.get_cmdline_user_args()
	var at := args.find("--label")
	if at >= 0: output += "/"+args[at+1]
	DirAccess.make_dir_recursive_absolute(output)
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false;root.add_child(world);current_scene = world
	await frames(30);player = world.player
	for child in player.get_children():
		if child is PlayerController: controller = child;controller.set_physics_process(false)
	var young_camps := 0
	for camp: EnemyCamp in world.camps:
		if camp.enemy_data and camp.enemy_data.id == &"young":
			young_camps += 1;player.position = camp.global_position+Vector3(0,0,7)
			await frames(18)
			check(not camp.dormant and camp.pack.living_count() == camp.count,"Young Mossling camp streams at "+str(camp.position))
			for mob: ActorBody in camp.pack.members:
				check(mob.visual.is_visible_in_tree() and mob.is_on_floor(),"Young Mossling is rendered above the terrain")
				check(mob.visual.skeleton.get_bone_pose_scale(mob.visual.skeleton.find_bone("Head")).x > 1.10,"Sapling proportions persist through imported animation scale tracks")
	check(young_camps >= 7,"All starting and field Young Mossling camps exist")
	check((load("res://data/enemies/young.tres") as EnemyData).id == &"young","Legacy Young Mossling resource and saved quest identity remain valid")
	player.position = Vector3(18,0,-20);await frames(18)
	for actor: ActorBody in get_nodes_in_group("enemies"):
		for brain in actor.get_children():
			if brain is EnemyBrain: brain.set_physics_process(false)
	await close_view(Vector3(19,3,-18),Vector3(14,1,-25),"young_mosslings")
	var specimens: Array[ActorBody] = []
	for species in ["red_wolf","blue_wolf","grey_wolf"]:
		var data: EnemyData = load("res://data/enemies/"+species+".tres")
		var mob := ActorBody.new();mob.visual_scene = data.visual;mob.enemy_definition = data
		world.add_child(mob);mob.position = Vector3((specimens.size()-1)*2.2,0,19);mob.rotation.y = PI
		mob.visual.apply_variant(data);specimens.append(mob)
		var found := false
		for mesh: MeshInstance3D in mob.visual.model.find_children("*","MeshInstance3D",true,false):
			for surface in mesh.mesh.get_surface_count():
				var material := mesh.get_active_material(surface) as ShaderMaterial
				if material:
					var coat: Color = material.get_shader_parameter("coat")
					if species == "red_wolf": check(coat.r > coat.b*1.5,"Red Wolf has a rust coat without baked green contamination")
					if species == "blue_wolf": check(coat.b > coat.r*1.5,"Blue Wolf has a blue slate coat without baked green contamination")
					found = true;break
			if found: break
		check(found,"Wolf uses the shared fur surface with preserved authored texture")
	await close_view(Vector3(1.5,2.8,29),Vector3(0,.9,19),"wolf_coats")
	for mob in specimens: mob.queue_free()
	specimens.clear()
	for species in ["bristle_boar","venom_spider","slate_guardian","cinder_wisp"]:
		var data: EnemyData = load("res://data/enemies/"+species+".tres")
		var mob := ActorBody.new();mob.visual_scene = data.visual;mob.enemy_definition = data
		world.add_child(mob);mob.position = Vector3((specimens.size()-1.5)*2.4,0,19);mob.rotation.y = PI
		mob.visual.apply_variant(data);specimens.append(mob)
	await close_view(Vector3(1.5,3.7,33),Vector3(0,1,19),"creature_surfaces")
	for mob in specimens: mob.queue_free()
	specimens.clear()
	for species in ["road_bandit","exile_captain"]:
		var data: EnemyData = load("res://data/enemies/"+species+".tres")
		var mob := ActorBody.new();mob.visual_scene = data.visual;mob.enemy_definition = data
		world.add_child(mob);mob.position = Vector3((specimens.size()-.5)*2.4,0,19);mob.rotation.y = PI
		mob.visual.apply_variant(data);specimens.append(mob)
		var cloth_found := false;var skin_preserved := false
		for mesh: MeshInstance3D in mob.visual.model.find_children("*","MeshInstance3D",true,false):
			for surface in mesh.mesh.get_surface_count():
				var source := mesh.mesh.surface_get_material(surface)
				if source and "Skin" in source.resource_name: skin_preserved = mesh.get_active_material(surface) is StandardMaterial3D
				if source and "Cloth" in source.resource_name: cloth_found = mesh.get_active_material(surface) is ShaderMaterial
		check(cloth_found and skin_preserved,"Bandit clothing receives a species palette while skin retains its authored surface")
	await close_view(Vector3(1.5,2.8,28),Vector3(0,1,19),"bandit_clothes")
	for mob in specimens: mob.queue_free()
	player.position = Vector3(18,0,-20);player.rotation = Vector3.ZERO
	player.mounts.owned.assign([&"trail_horse"]);player.mounts.selected = &"trail_horse"
	check(player.mounts.toggle(),"Mount uses the real horse controller")
	var camera := Camera3D.new();world.add_child(camera);camera.fov = 40;camera.current = true
	for node in world.get_children():
		if node is CanvasLayer: node.visible = false
	var overlaps := 0;var rider_overlaps := 0;var worst := 100.0
	var video_frame := 0
	var record := args.has("--record")
	if record: DirAccess.make_dir_recursive_absolute(output+"/video_frames")
	for weapon in [&"wayfarer_blade",&"rift_cleaver"]:
		player.equipment.slots[&"weapon"] = ItemStack.new(weapon);player.equipment.refresh()
		player.combat.sequence_index = -1;player.combat.idle_elapsed = 2
		for cut in 2:
			check(player.combat.request_attack(),"Outside mounted cut starts")
			for frame in 44:
				await frames(1)
				camera.global_position = player.global_position+Vector3(-3.8 if cut == 0 else 3.8,2.6,-4.7);camera.look_at(player.global_position+Vector3(0,1.6,0))
				if record and DisplayServer.get_name() != "headless":
					await RenderingServer.frame_post_draw
					root.get_texture().get_image().save_png(output+"/video_frames/frame_%04d.png" % video_frame)
					video_frame += 1
				var grip := player.to_local(player.visual.weapon_marker_world(&"Grip"))
				var tip := player.to_local(player.visual.weapon_marker_world(&"Tip"))
				var pommel := grip-(tip-grip).normalized()*.32
				for sample in 31:
					var point := pommel.lerp(tip,float(sample)/30.0)
					for envelope in [[Vector3(0,1.22,.20),Vector3(.40,.45,.96)],[Vector3(0,1.60,-.99),Vector3(.23,.49,.40)],[Vector3(0,2.03,-1.43),Vector3(.20,.24,.38)]]:
						var clearance: float = ((point-envelope[0])/envelope[1]).length()
						worst = minf(worst,clearance)
						if clearance < 1.0:
							if overlaps < 8: print("HORSE CONTACT ",weapon," cut=",cut," frame=",frame," point=",point)
							overlaps += 1
					for part in [[&"Chest",Vector3(.22,.27,.18),.08],[&"Head",Vector3(.13,.19,.13),.10]]:
						var transform := player.visual.bone_world_transform(part[0])
						var center: Vector3 = player.to_local(transform.origin)+Vector3.UP*part[2]
						if ((point-center)/part[1]).length() < 1.0:
							if rider_overlaps < 8: print("RIDER CONTACT ",weapon," cut=",cut," frame=",frame," part=",part[0]," point=",point," center=",center)
							rider_overlaps += 1
				if frame in [4,12,20,28]:
					print("CUT ",weapon," side=",cut," frame=",frame," grip=",grip," tip=",tip)
					await capture("%s_cut%d_frame%d" % [weapon,cut,frame])
			await frames(6)
	print("BLADE horse overlap samples=",overlaps," rider samples=",rider_overlaps," minimum ellipsoid clearance=",worst)
	check(overlaps == 0,"Entire blade clears the horse during both cuts with short and long swords")
	check(rider_overlaps == 0,"Blade and pommel clear rider head and torso through the complete attacks")
	camera.queue_free();controller.rig.camera.current = true;player.mounts.dismount()
	for node in world.get_children():
		if node is CanvasLayer: node.visible = true
	var trophy_ids: Array[StringName] = []
	var icon_paths: Dictionary = {}
	for item_path in DirAccess.get_files_at("res://data/items"):
		if not item_path.ends_with(".tres"): continue
		var item: ItemData = load("res://data/items/"+item_path)
		if item.icon and "/trophies/" in item.icon.resource_path:
			trophy_ids.append(item.id);icon_paths[item.icon.resource_path] = true
	check(trophy_ids.size() == 35 and icon_paths.size() == 35,"35 material items each have a distinct inventory icon")
	var drop_rng := RandomNumberGenerator.new();drop_rng.seed = 1223
	for species in ["young","grown","red_wolf","fracture"]:
		var table: DropTable = load("res://data/drops/"+species+".tres")
		var quantity := 0
		for roll in 10000:
			for stack in table.roll(drop_rng): quantity += stack.quantity
		var mean := quantity/10000.0
		print("DROP mean items ",species,"=",mean)
		check(mean < (1.8 if species == "fracture" else .80 if species == "young" else .70 if species == "grown" else .32),"Common drop budget is reduced for "+species)
		for entry in table.entries:
			if entry.item.equipment_slot != &"": check(entry.chance <= .004,"Rare gear probability retains its original reward budget")
	var vocal := load("res://assets/audio/sfx/mount.ogg") as AudioStreamOggVorbis
	check(vocal.get_length() > 1.5 and vocal.get_length() < 2.5,"Mount plays the recorded horse vocal")
	for node in world.get_children():
		if is_instance_valid(node) and node is ZoneHUD:
			for page in 2:
				for i in PlayerInventory.CAPACITY: player.inventory.slots[i] = ItemStack.new(trophy_ids[(i+page*24)%35])
				player.inventory.changed.emit();node.inventory_panel.show();await frames(3);await capture("inventory_trophies%d" % page)
			node.inventory_panel.hide()
	var encounter: WorldFracture = player.farming.encounter
	player.position = encounter.global_position+Vector3(0,0,2)
	player.health.maximum = 100000;player.health.current = 100000
	encounter.reset_attempt();encounter.rng.seed = 924
	for wave in encounter.data.waves.size():
		encounter.body.health.apply_damage(100000,player)
		check(encounter.body.health.is_alive(),"Burst cannot skip root defender wave %d" % wave)
		await frames(45)
		check(encounter.next_wave == wave+1,"Root releases wave %d while still alive" % wave)
		check(encounter.defenders[wave].pack.members.size() == encounter.data.waves[wave].count,"Root respects authored reinforcement count")
		if wave == 1: await close_view(encounter.global_position+Vector3(7,3.8,9),encounter.global_position+Vector3(0,1,0),"root_waves_during_combat")
	check(encounter.living_defenders() == 24,"Four root phases release 24 defenders during the fight")
	encounter.body.health.apply_damage(100000,player)
	check(not encounter.body.health.is_alive() and encounter.completions == 1,"Root finishes normally after releasing its waves")
	root.get_node("GameAudio").shutdown();await frames(3)
	print("FIELD_FEEDBACK_REVIEW failures=",failures)
	quit(1 if failures else 0)
