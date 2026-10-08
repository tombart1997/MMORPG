extends "res://tests/combat_smoke.gd"
## Reproducible presentation fixture. Uses the shipped world and player camera.
func _run() -> void:
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(15)
	var player: ActorBody = world.player
	player.health.maximum = 10000
	player.health.current = player.health.maximum
	var rig: ThirdPersonCamera
	for child in player.get_children():
		if child is PlayerController:
			rig = child.rig
	player.position=ZoneTerrain.FRACTURE+Vector3(-14, .1, 1)
	rig.yaw=-PI/2
	rig.pitch=-.38
	rig.distance=9.2
	Input.warp_mouse(Vector2(1260,700))
	await frames(10)
	await capture_art("approach")
	player.position = ZoneTerrain.FRACTURE + Vector3(-3.3, 0.1, 5.1)
	player.rotation.y = -0.25
	rig.yaw = -0.38
	rig.pitch = -0.42
	rig.distance = 8.0
	var encounter: WorldFracture = player.farming.encounter
	# Real damage activates the existing encounter; no alternate art-only enemy path.
	encounter.rng.seed = 921
	encounter.body.health.apply_damage(1, player)
	await frames(110)
	for camp in encounter.defenders:
		for i in camp.pack.members.size():
			var enemy: ActorBody = camp.pack.members[i]
			enemy.global_position = ZoneTerrain.FRACTURE + [Vector3(-3.4, 0.1, 1.6), Vector3(2.8, 0.1, 2.7), Vector3(.2, 0.1, 2.7), Vector3(-3.5, 0.1, -1)][i % 4]
			enemy.look_at(Vector3(player.position.x, enemy.position.y, player.position.z))
			for brain in enemy.get_children():
				if brain is EnemyBrain: brain.set_physics_process(false)
	player.combat.cancel()
	player.navigation.cancel()
	player.position = ZoneTerrain.FRACTURE + Vector3(-3.3, 0.1, 5.1)
	world.notice_time=0
	Input.warp_mouse(Vector2(1260,700))
	await frames(5)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/art_benchmark.png")
	print("ART_CAPTURE real gameplay camera; defenders=", encounter.living_defenders())
	print("ART_CAMERA player=",player.global_position," camera=",rig.camera.global_position," yaw=",rig.yaw," pitch=",rig.pitch," arm=",rig.arm.get_hit_length())
	check(encounter.next_wave==1 and encounter.living_defenders()==encounter.data.waves[0].count,"Benchmark uses the configured first defender wave")
	var skins:=0
	var surfaces:=0
	for part:MeshInstance3D in encounter.defenders[0].pack.members[0].visual.model.find_children("*","MeshInstance3D",true,false):
		if part.skin != null: skins+=1
		surfaces+=part.mesh.get_surface_count()
	check(skins==1 and surfaces<=5,"Production Mossling imports as one skin with at most five surfaces")
	check(encounter.body.visual.ribs.size()==7,"Fracture imports seven independently damageable visual ribs")
	encounter.body.health.apply_damage(560,player)
	await frames(12)
	await capture_art("damaged")
	# Complete the real telegraphed waves; burst damage cannot skip their gates.
	for round_index in 6:
		for camp in encounter.defenders:
			for defender in camp.pack.members:
				if defender.health.is_alive(): defender.health.apply_damage(100000,player)
		encounter.body.health.apply_damage(encounter.body.health.maximum,player)
		await frames(150)
		if not encounter.body.health.is_alive(): break
	await frames(50)
	await capture_art("collapsed")
	check(encounter.body.visual.collapsed,"Fracture visual follows authoritative death")
	# Explicit reward fixture for presentation only; production drop probabilities stay intact.
	var reward:=LootPickup.new()
	reward.item=ItemCatalog.get_item(&"wakeglass")
	world.add_child(reward)
	reward.position=player.position+Vector3(1.5,0,-1)
	await frames(8)
	await capture_art("reward")
	quit(1 if failures else 0)

func capture_art(label:String) -> void:
	if DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.local/art_%s.png" % label)
