extends "res://tests/mmorpg_loop.gd"
const ROUTE: Array[Vector3] = [Vector3(0,0,-4),Vector3(18,0,-4),Vector3(18,0,-20),Vector3(14,0,-32),Vector3(-6,0,-32),Vector3(-25,0,-43),Vector3(-19,0,-49),Vector3(-8,0,-46.9),Vector3(-4,0,-62),Vector3(-25,0,-62),Vector3(-25,0,-43),Vector3(-6,0,-32),Vector3(14,0,-32),Vector3(18,0,-20),Vector3(18,0,-4),Vector3(0,0,-4),ZoneTerrain.START]

func key(action: String) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
	await frames(2)
	event = InputEventAction.new()
	event.action = action
	event.pressed = false
	Input.parse_input_event(event)
	await frames(2)

func route(riding: bool) -> float:
	world.respawn_player()
	await frames(5)
	if riding: await key("mount")
	check(player.mounts.mounted == riding,"Route begins with requested traversal mode")
	var begin := Engine.get_physics_frames()
	for destination in ROUTE:
		await travel(destination,1800)
		if player.global_position.distance_to(destination) >= 1.1: print("ROUTE_BLOCKED position=%s destination=%s failure=%s" % [player.position,destination,player.navigation.failure])
		check(player.global_position.distance_to(destination) < 1.1,"%s route reaches %s through navigation" % ["Horse" if riding else "Foot",destination])
	var seconds := (Engine.get_physics_frames()-begin)/60.0
	check(player.mounts.mounted == riding,"Traversal and sanctuary preserve riding mode")
	return seconds

func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(10)
	player = world.player
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	check(not player.mounts.toggle(),"Fresh traveler cannot summon an unowned horse")
	check(player.map_state.markers().size() == 1 + world.settlement.npcs.size(),"Fresh map contains only known refuge and services")
	check(player.map_state.subarea().contains("Briar Crossing"),"Arrival identifies region and sanctuary subarea")
	await key("world_map")
	check(player.ui_session.active == player.ui_session.world_map and player.ui_open,"M opens full map through modal owner")
	await key("world_map")
	check(not player.ui_open,"M closes map and releases gameplay")
	var mara: WorldNPC = world.settlement.npcs[0]
	await approach(mara,&"npc")
	var merchant := MerchantService.new()
	player.inventory.gold = 400
	check(not merchant.buy(mara,player,5,1).is_empty(),"Horse purchase enforces level milestone")
	while player.progression.level < 3: player.progression.award_xp(player.progression.xp_required())
	check(merchant.buy(mara,player,5,1).is_empty() and player.inventory.gold == 160,"Horse bridle is bought through real gold/inventory transaction")
	check(not merchant.buy(mara,player,5,1).is_empty(),"Duplicate bridle purchase rejected")
	hud.inventory_panel.set_open(true)
	hud.inventory_panel.select_slot(find_item(&"trail_bridle"))
	hud.inventory_panel.activate_selection()
	check(player.mounts.owned.has(&"trail_horse") and player.inventory.count(&"trail_bridle") == 0,"Inventory use consumes bridle once and unlocks permanent ownership")
	player.ui_session.close()
	world.respawn_player()
	await frames(5)
	await key("mount")
	check(player.mounts.mounted,"H action mounts from normal gameplay input")
	await frames(2)
	check(is_instance_valid(player.mounts.model) and player.visual.position.y > 0,"Original horse appears and rider is raised onto saddle")
	check(is_equal_approx(player.body_collider.shape.radius,.38),"Mounted collision remains within baked navigation envelope")
	var rig := player.world_interaction.camera.get_parent().get_parent() as ThirdPersonCamera
	check(is_equal_approx(rig.global_position.y-player.global_position.y,1.3+player.mounts.definition.rider_height),"Camera follows raised rider without changing orbit or zoom")
	await key("mount")
	check(not player.mounts.mounted,"H dismounts responsively")
	# Native inventory drag to the external action bar, including modal mouse-release routing.
	hud.inventory_panel.set_open(true)
	var quick: ConsumableSlot = player.ui_session.quick_bar.find_children("*","ConsumableSlot",true,false)[1]
	var source := hud.inventory_panel.bag_buttons[find_item(&"field_tonic")]
	await drag_between(source,quick)
	check(player.actions.slots[1] == &"field_tonic" and player.inventory.count(&"field_tonic") == 2,"Native drag assigns quick slot without moving or duplicating inventory")
	var payload := {"player":player,"index":find_item(&"field_tonic"),"equipment":&"","stack":ItemStack.new(&"field_tonic")}
	check(not player.actions.can_drop(payload),"Stale stack drag rejected")
	payload.index = 999
	check(not player.actions.can_drop(payload),"Out-of-range drag rejected safely")
	check(not player.actions.assign(1,&"moss_shard"),"Materials cannot enter consumable slots")
	player.ui_session.close()
	player.position = Vector3(0,0,-4)
	await frames(5)
	player.health.current -= 70
	var before := player.health.current
	await key("quick_second")
	check(player.inventory.count(&"field_tonic") == 1 and player.health.current > before+40,"F consumes real assigned tonic and restores health")
	check(not player.actions.activate(0) and player.inventory.count(&"field_tonic") == 1,"Shared restoration cooldown prevents double use")
	player.inventory.remove_count(&"field_tonic",1)
	check(not player.actions.activate(1) and player.actions.slots[1] == &"field_tonic","Depleted slot is unavailable but retains assignment")
	world.respawn_player()
	await frames(5)
	var foot := await route(false)
	var horse := await route(true)
	print("ROUTE_TRAVERSAL foot=%.2fs horse=%.2fs reduction=%.1f%% speed=5.5/8.8 m/s waypoints=%d" % [foot,horse,(1-horse/foot)*100,ROUTE.size()])
	check(horse < foot*.8 and horse > foot*.5,"Horse materially reduces dead travel time without doubling world speed")
	check(player.map_state.discoveries.get("briarwood",[]).has("briarwake"),"Fracture landmark is discovered from real nearby travel and sight")
	await approach(mara,&"npc")
	check(player.ui_open and not player.mounts.mounted,"Mounted click approach safely dismounts to converse with NPC")
	player.ui_session.close()
	world.respawn_player()
	await frames(5)
	await key("mount")
	var save := ProgressionSave.new()
	save.path = "user://route_mount_test.json"
	check(save.save_player(player),"Save captures ownership, map discoveries and quick slots while mounted")
	player.actions.assign(1,&"")
	player.map_state.discoveries.clear()
	check(save.load_player(player),"Version 5 snapshot loads")
	check(not player.mounts.mounted and player.mounts.owned.has(&"trail_horse") and player.actions.slots[1] == &"field_tonic" and player.map_state.discoveries.get("briarwood",[]).has("briarwake"),"Load restores assignments/discovery/ownership and safely leaves player on foot")
	var snapshot: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(save.path))
	var corrupt := snapshot.duplicate(true)
	corrupt.mounts.owned = ["missing_species"]
	corrupt.gold = 99999
	check(not save.apply_snapshot(player,corrupt) and player.inventory.gold != 99999,"Unknown mount rejects whole snapshot before mutation")
	corrupt = snapshot.duplicate(true)
	corrupt.actions = ["moss_shard",""]
	check(not save.apply_snapshot(player,corrupt),"Malformed action assignment rejects snapshot")
	corrupt = snapshot.duplicate(true)
	corrupt.map = {"briarwood":["secret_not_authored"]}
	check(not save.apply_snapshot(player,corrupt),"Unknown landmark rejects snapshot")
	var legacy := snapshot.duplicate(true)
	legacy.version = 4
	for field in ["actions","mounts","map"]: legacy.erase(field)
	check(save.apply_snapshot(player,legacy) and player.mounts.owned.is_empty() and player.actions.slots[0] == &"field_tonic","Version 4 migrates to safe defaults")
	check(save.apply_snapshot(player,snapshot),"Current state restores after legacy migration")
	await frames(5)
	await key("mount")
	player.position = Vector3(-9,0,9)
	player.world_interaction.command({"kind": &"terrain", "position": Vector3(-2,0,9), "normal": Vector3.UP})
	check(player.navigation.path.size()>2,"Mounted route detours around solid settlement building")
	for i in 900:
		await frames(1)
		if not player.navigation.active: break
	check(player.position.distance_to(Vector3(-2,0,9)) < 1 and player.mounts.mounted,"Horse collision follows detour without teleport or stuck traversal")
	player.combat.request_attack()
	check(player.mounts.mounted and player.combat.is_attacking(),"Accepted basic attack preserves mounted combat")
	player.combat.cancel()
	player.mounts.dismount()
	player.position = Vector3(0,0,-4)
	await frames(5)
	await key("mount")
	var foe: ActorBody = world.camps[0].pack.members[0]
	player.health.apply_damage(10,foe)
	check(player.mounts.mounted,"Hostile hit preserves riding during combat")
	player.mounts.dismount()
	check(not player.mounts.toggle(),"Combat lock prevents immediate remount after dismounting")
	await frames(310)
	await key("mount")
	check(player.mounts.mounted,"Horse can be summoned again after escaping combat")
	player.health.apply_damage(10000,foe)
	await frames(3)
	check(not player.mounts.mounted and player.mounts.owned.has(&"trail_horse"),"Death removes horse visual while preserving ownership")
	world.respawn_player()
	await frames(5)
	check(not player.mounts.mounted and player.health.is_alive(),"Revival is a safe unmounted sanctuary return")
	print("Map / action bar / mount route complete: %d failures" % failures)
	quit(1 if failures else 0)
