extends "res://tests/combat_smoke.gd"

func _run() -> void:
	var world = load("res://scenes/arena.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await frames(3)
	var player: ActorBody = world.player
	var controller: PlayerController
	for child in player.get_children():
		if child is PlayerController:
			controller = child
	controller.rig.set_process_unhandled_input(false)
	controller.rig.yaw = 0
	player.position = Vector3(8, 0, 8)
	player.rotation.y = 0
	player.combat.sequence.assign([load("res://data/attacks/player_sword.tres"),
		load("res://data/attacks/player_return.tres"), load("res://data/attacks/player_finisher.tres")])
	Input.action_press("move_back")
	player.combat.request_attack()
	await frames(5)
	check(absf(player.position.z - 8) < 0.01, "WASD cannot move during windup before lunge")
	await frames(27)
	check(absf(player.position.z - 7.65) < 0.03, "Authored 0.35m forward lunge overrides held retreat")
	check(player.combat.movement_locked(), "Movement stays locked into recovery")
	player.combat.queue_followup()
	await frames(12)
	check(player.combat.sequence_index == 1 and player.combat.is_attacking(), "Recovery click chains second attack")
	Input.action_release("move_back")
	await frames(30)
	player.combat.queue_followup()
	await frames(10)
	check(player.combat.sequence_index == 2, "Combo reaches distinct third attack")
	check(player.combat.attack.lunge_distance == 0.55, "Finisher has separate displacement data")
	await frames(100)
	player.combat.request_attack()
	check(player.combat.sequence_index == 0, "Combo resets after grace timeout")
	await frames(45)
	var before := player.position.z
	Input.action_press("move_back")
	await frames(10)
	Input.action_release("move_back")
	check(player.position.z > before + 0.7, "Normal movement returns after recovery")
	player.combat.cancel()
	player.position = Vector3.ZERO
	player.rotation.y = 0
	controller.rig.yaw = 0
	var enemy: ActorBody = world.pack.members[0]
	enemy.position = Vector3(0, 0, -1.4)
	for i in range(1, 6):
		world.pack.members[i].position = Vector3(10 + i, 0, -10)
	Input.action_press("move_back")
	player.combat.request_attack()
	await frames(36)
	Input.action_release("move_back")
	check(player.health.current < player.health.maximum, "Closest enemy lands real timed hit during retreat-held melee commitment")
	check(player.combat.is_attacking(), "Enemy hit arrives while player still committed")
	await frames(50)
	for member in world.pack.members:
		for child in member.get_children():
			if child is EnemyBrain:
				child.set_physics_process(false)
	enemy.combat.cancel()
	player.combat.cancel()
	player.position = Vector3.ZERO
	enemy.position = Vector3(0, 0, -1.5)
	enemy.rotation.y = PI
	var health_before := player.health.current
	enemy.combat.request_attack()
	Input.action_press("move_back")
	await frames(35)
	Input.action_release("move_back")
	check(player.health.current == health_before, "Uncommitted deliberate retreat can avoid telegraphed attack")
	world.queue_free()
	await frames(2)
	print("Melee commitment complete: %d failures" % failures)
	quit(1 if failures else 0)
