extends "res://tests/combat_smoke.gd"
var world: Node3D
var player: ActorBody
var kit: PlayerSkills
var controller: PlayerController
var abilities: Array[SkillData]
var foes: Array[ActorBody] = []
const FIELD := Vector3(14,0,-28)

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://.local/skill_"+label+".png")

func reset_fixture() -> void:
	for key in ["move_forward", "move_back", "move_left", "move_right"]: Input.action_release(key)
	kit.cancel_transient()
	kit.cooldowns.clear()
	controller.stop_auto_attack()
	player.combat.cancel()
	player.world_interaction.cancel()
	player.position = FIELD
	player.rotation.y = 0
	player.velocity = Vector3.ZERO
	player.health.current = player.health.maximum
	controller.rig.yaw = 0
	for i in foes.size():
		foes[i].combat.cancel()
		foes[i].statuses.clear()
		foes[i].health.maximum = 10000
		foes[i].health.current = 10000
		foes[i].global_position = FIELD+Vector3((i-1)*1.2,0,-2.5)
	await frames(2)

func key(index: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = KEY_1+index
	event.pressed = true
	Input.parse_input_event(event)
	await frames(1)
	event.pressed = false
	Input.parse_input_event(event)

func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(12)
	player = world.player
	kit = player.skills
	abilities = kit.specialization.skills
	for child in player.get_children():
		if child is PlayerController: controller = child
	for camp in world.camps:
		camp.set_physics_process(false)
		for enemy in camp.pack.members:
			for child in enemy.get_children():
				if child is EnemyBrain: child.set_physics_process(false)
	foes.assign(world.camps[0].pack.members)
	check(abilities.size()==6,"Six complete skills retain stable save IDs")
	for skill in abilities:
		check(skill.icon!=null and not skill.effects.is_empty() and player.visual.animation_player.has_animation(skill.animation),skill.display_name+" has working effects, icon and animation")
	# Exercise actual hotkeys with held movement, not direct skill requests alone.
	for i in range(6):
		await reset_fixture()
		Input.action_press("move_right")
		var start := player.position
		await key(i)
		await frames(10)
		var distance := player.position.distance_to(start)
		check(distance>.7,abilities[i].display_name+" preserves moving input (%.2fm)" % distance)
		check(kit.remaining(abilities[i])>0 and kit.armed==null,abilities[i].display_name+" casts on one press without a placement click")
		if i==2: check(distance>3.8 and player.statuses.has(&"haste"),"Flashstep dashes in held direction and grants speed")
		Input.action_release("move_right")
		await capture("moving_%d" % (i+1))
	# A selected enemy remains the aim target while strafing sideways.
	await reset_fixture()
	player.world_interaction.selected_enemy = foes[1]
	Input.action_press("move_right")
	await frames(3)
	kit.activate(0)
	await frames(10)
	check(foes[1].health.current<10000 and player.world_interaction.selected_enemy==foes[1],"Strafing preserves selection and aims lightning at the selected enemy")
	# Casting cancels the basic attack, but retains legitimate click travel.
	await reset_fixture()
	player.combat.request_attack()
	check(kit.activate(0) and kit.busy() and not player.combat.is_attacking(),"Skill immediately takes over a basic attack windup")
	check(not player.combat.request_attack(),"Basic attacks cannot double-hit over a skill")
	check(not player.equipment.unequip(&"weapon"),"Equipment changes remain blocked during skill execution")
	await frames(22)
	check(foes[1].health.current<9960 and foes[1].statuses.has(&"open"),"Lightning cleave inflicts substantial area damage and opens enemies")
	await capture("lightning_hit")
	await reset_fixture()
	player.navigation.command(FIELD+Vector3(3,0,0))
	check(kit.activate(1) and player.navigation.active,"Buff preserves click-to-move path")
	await frames(10)
	check(player.position.x>FIELD.x+.6,"Click travel continues through buff animation")
	await reset_fixture()
	kit.activate(5)
	player.world_interaction.command({"kind":&"terrain","position":FIELD+Vector3(3,0,0)})
	check(player.navigation.active,"New click-to-move commands are accepted during a cast")
	await frames(10)
	check(player.position.x>FIELD.x+.6,"New click destination moves immediately during cast")
	# Green aura carries real basic attack benefits and directional defense.
	await reset_fixture()
	kit.activate(1)
	await frames(9)
	check(player.statuses.has(&"spirit_edge") and player.statuses.has(&"guard"),"Spirit Edge applies weapon power and guard")
	player.combat.request_attack()
	check(is_equal_approx(player.combat.swing_speed,1.3) and is_equal_approx(player.combat.swing_damage,36.25),"Spirit Edge grants 45% basic damage and 30% attack speed")
	player.combat.cancel()
	player.health.current = 100
	foes[0].global_position = player.position+Vector3(0,0,2)
	player.health.apply_damage(10,foes[0])
	check(player.health.current==90 and player.statuses.has(&"guard"),"Rear hits bypass spirit guard")
	foes[0].global_position = player.position+Vector3(0,0,-2)
	player.health.apply_damage(10,foes[0])
	check(is_equal_approx(player.health.current,86.5) and player.statuses.has(&"answer"),"Frontal guard reduces damage and earns Answer")
	controller.rig.distance = 5
	await frames(3)
	await capture("spirit_blade")
	# Storm hits behind the actor and follows while moving; no single-hit visual fake.
	await reset_fixture()
	foes[2].global_position = FIELD+Vector3(0,0,2)
	kit.activate(3)
	await frames(8)
	var first_hit := foes[2].health.current
	check(first_hit<10000,"Bladestorm hits enemies behind the player")
	Input.action_press("move_right")
	await frames(12)
	await capture("bladestorm")
	await frames(24)
	Input.action_release("move_right")
	check(foes[2].health.current<first_hit,"Orbiting blade deals repeated damage as player moves")
	await reset_fixture()
	kit.activate(4)
	await frames(10)
	check(player.statuses.has(&"shelter") and foes[1].statuses.has(&"zone_slow"),"Fire field combines shelter with enemy slow")
	var initial := foes[1].health.current
	await capture("phoenix")
	await frames(40)
	check(foes[1].health.current<initial-10,"Fire field burns enemies repeatedly")
	# Sunbreaker needs no selected target and heals only on successful damage.
	await reset_fixture()
	player.health.current = 100
	kit.activate(5)
	await frames(9)
	check(foes[1].health.current<=9925 and player.health.current>100,"Sunbreaker lands a heavy hit and heals")
	await capture("sunbreaker")
	# Speed and blade buffs expire instead of permanently changing base stats.
	await reset_fixture()
	Input.action_press("move_right")
	kit.activate(2)
	await frames(16)
	check(controller.speed>9.8,"Flashstep actually raises movement speed from 5.5 to 9.9 m/s")
	Input.action_release("move_right")
	await frames(250)
	check(not player.statuses.has(&"haste") and is_equal_approx(controller.speed,5.5),"Four-second speed burst expires and restores base speed")
	kit.activate(1)
	await frames(370)
	check(not player.statuses.has(&"spirit_edge"),"Six-second spirit blade power expires")
	# Buffer exactly one follow-up, not an unlimited spam queue.
	await reset_fixture()
	kit.activate(5)
	kit.activate(0)
	kit.activate(1)
	await frames(25)
	check(kit.remaining(abilities[1])>0 and kit.remaining(abilities[0])==0,"Latest buffered skill wins and executes once")
	await reset_fixture()
	kit.activate(5)
	kit.activate(0)
	player.ui_session.open_panel(player.ui_session.world_map)
	await frames(25)
	check(kit.queued_index==-1 and kit.remaining(abilities[0])==0,"Opening UI clears pending casts")
	player.ui_session.close()
	# Shortened cooldowns accept existing saves; class validation is still strict.
	await reset_fixture()
	kit.activate(1)
	await frames(10)
	var save := ProgressionSave.new()
	save.path = "user://skill_rework_test.json"
	check(save.save_player(player),"Reworked skills save with stable IDs")
	var snapshot: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(save.path))
	snapshot.skills.cooldowns["standard_of_ash"] = 18.0
	check(save.apply_snapshot(player,snapshot) and kit.remaining(abilities[4])==10,"Old cooldowns migrate to shorter timers without rejecting save")
	check(not player.statuses.has(&"spirit_edge"),"Loading does not retain transient power buffs")
	var invalid := snapshot.duplicate(true)
	invalid.skills.specialization = "missing"
	check(not save.apply_snapshot(player,invalid),"Invalid specialization still rejects atomically")
	# Obstacles and sanctuary remain authoritative for fast casts and damaging areas.
	await reset_fixture()
	var wall := StaticBody3D.new()
	var collider := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(8,3,.4)
	collider.shape = box
	wall.add_child(collider)
	world.add_child(wall)
	wall.global_position = FIELD+Vector3(0,1,-1)
	await frames(2)
	kit.activate(0)
	await frames(16)
	check(foes[1].health.current==10000,"Lightning cannot damage enemies through walls")
	kit.cooldowns.clear()
	check(not kit.request(abilities[2],null,FIELD+Vector3(0,0,-4)),"Dash rejects a path crossing a wall")
	wall.queue_free()
	await reset_fixture()
	world.respawn_player()
	foes[0].global_position = player.global_position+Vector3(0,0,-2)
	kit.activate(4)
	await frames(40)
	check(foes[0].health.current==10000,"Fire cannot damage sanctuary occupants")
	await reset_fixture()
	kit.activate(1)
	await frames(8)
	kit.activate(3)
	await frames(8)
	player.health.apply_damage(10000,null)
	await frames(3)
	check(not kit.busy() and kit.queued_index==-1 and player.statuses.entries.is_empty() and get_nodes_in_group("skill_areas").is_empty(),"Death clears buffs, moving areas and buffered input")
	await frames(45)
	check(get_nodes_in_group("skill_spectacles").is_empty(),"Visual effects clean up after death")
	# Real pack AI and physical movement: clear six wolves using skills while strafing.
	world.respawn_player()
	kit.cooldowns.clear()
	var camp: EnemyCamp = world.camps[3]
	camp.set_physics_process(true)
	for foe in camp.pack.members:
		for child in foe.get_children():
			if child is EnemyBrain: child.set_physics_process(true)
	player.position = camp.position+Vector3(-1,0,3)
	controller.rig.distance = 8
	var previous := player.position
	var travelled := 0.0
	var casts := 0
	var actions := [1,4,3,0,5]
	var moves := ["move_right","move_forward","move_left","move_back"]
	for frame in range(720):
		if camp.pack.living_count()==0 or not player.health.is_alive(): break
		if frame%25==0:
			for move in moves: Input.action_release(move)
			Input.action_press(moves[(frame/25)%4])
		var nearest: ActorBody
		var distance := INF
		for foe in camp.pack.members:
			if foe.health.is_alive() and foe.global_position.distance_to(player.global_position)<distance:
				nearest=foe
				distance=foe.global_position.distance_to(player.global_position)
		player.world_interaction.selected_enemy=nearest
		if frame%18==0:
			var index: int = actions[(frame/18)%actions.size()]
			if kit.activate(index): casts+=1
		await frames(1)
		travelled += player.position.distance_to(previous)
		previous = player.position
		if frame==40: await capture("live_pack")
	for move in moves: Input.action_release(move)
	check(camp.pack.living_count()==0 and player.health.is_alive(),"Mobile skills clear a real six-wolf pack with live aggro and attacks")
	check(travelled>2 and casts>=3,"Live pack fight uses sustained movement and multiple skills")
	print("LIVE_SKILLS distance=%.2fm casts=%d hp=%.1f wolves=%d" % [travelled,casts,player.health.current,camp.pack.living_count()])
	print("Responsive skill combat complete: %d failures" % failures)
	quit(1 if failures else 0)
