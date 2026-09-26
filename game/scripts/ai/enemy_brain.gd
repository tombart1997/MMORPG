class_name EnemyBrain
extends Node
var actor: ActorBody
var pack: AggroGroup
var speed: float = 3.2
var stagger: float = 0.0
var cooldown: float = 0.0
var home: Vector3
var crowd: EnemyCrowd
var steering_clock: float = 0
var separation := Vector3.ZERO
var route := PackedVector3Array()
var route_clock: float = 0
var aggro_radius: float = 0
var aggro_clock: float = 0

func _ready() -> void:
	actor = get_parent() as ActorBody
	# Ordinary mobs separate through steering, not quadratic body-body contacts.
	# They still collide with terrain and the player; player masks include layer 8.
	actor.collision_layer = 8
	actor.collision_mask = 3
	home = actor.global_position
	actor.health.damaged.connect(_on_damaged)
	cooldown = float(actor.get_index() % 6) * 0.13
	var scene: Node = actor
	while scene.get_parent() != get_tree().root: scene = scene.get_parent()
	crowd = scene.get_meta("enemy_crowd") as EnemyCrowd if scene.has_meta("enemy_crowd") else null
	if crowd == null:
		crowd = EnemyCrowd.new()
		crowd.name = "EnemyCrowd"
		scene.set_meta("enemy_crowd", crowd)
		scene.add_child.call_deferred(crowd)
	steering_clock = float(actor.get_index() % 6) * 0.017

func _on_damaged(_amount: float, _source: Node3D) -> void:
	# Ordinary hits react visually but cannot endlessly interrupt a committed strike.
	if not actor.combat.is_attacking():
		stagger = 0.08

func _physics_process(delta: float) -> void:
	if not actor.health.is_alive(): return
	aggro_clock -= delta
	if aggro_radius > 0 and aggro_clock <= 0 and not pack.has_target():
		aggro_clock = .25
		# Solo elites actively hunt nearby players; terrain and sanctuary block acquisition.
		for candidate: ActorBody in get_tree().get_nodes_in_group("players"):
			if candidate.health.is_alive() and not SafeArea.protects(candidate) and not SafeArea.protects(actor) and home.distance_to(candidate.global_position) <= aggro_radius:
				if SkillTargeting.line_clear(actor, actor.global_position, candidate.global_position):
					pack.target = candidate
					pack.alerted.emit(candidate)
					break
	if not is_instance_valid(crowd) or not crowd.is_inside_tree():
		var scene: Node = actor
		while scene.get_parent() != get_tree().root: scene = scene.get_parent()
		crowd = scene.get_node_or_null("EnemyCrowd") as EnemyCrowd
	steering_clock -= delta
	route_clock -= delta
	if not pack.has_target() and actor.combat.is_attacking(): actor.combat.cancel()
	stagger = maxf(0.0, stagger - delta)
	cooldown = maxf(0.0, cooldown - delta)
	if not pack.has_target() and not actor.combat.is_attacking() and actor.is_on_floor() and actor.statuses.push_remaining <= 0:
		var resting := home - actor.global_position
		resting.y = 0
		if resting.length_squared() < 0.0225:
			actor.velocity = Vector3.ZERO
			return
	var movement := Vector3.ZERO
	if actor.health.is_alive() and pack.has_target() and stagger <= 0.0:
		var offset := pack.target.global_position - actor.global_position
		offset.y = 0.0
		if route_clock <= 0:
			route_clock = 0.6 + float(actor.get_index() % 5) * 0.03
			route.clear()
			if offset.length() > 2 and not SkillTargeting.line_clear(actor, actor.global_position, pack.target.global_position):
				var map := actor.get_world_3d().navigation_map
				if NavigationServer3D.map_get_iteration_id(map) > 0:
					route = NavigationServer3D.map_get_path(map, actor.global_position, pack.target.global_position, true)
		if not actor.combat.is_attacking():
			if offset.length_squared() > 0.001:
				actor.rotation.y = atan2(-offset.x, -offset.z)
			if offset.length() > 1.65:
				movement = offset.normalized() * speed
				while not route.is_empty() and actor.global_position.distance_to(route[0]) < 0.65: route.remove_at(0)
				if not route.is_empty():
					var toward := route[0] - actor.global_position
					toward.y = 0
					movement = toward.normalized() * speed
			elif cooldown <= 0.0 and separation.length() < 2.8:
				actor.combat.request_attack()
				cooldown = 0.3
		# Mild separation helps the pack spread around the player.
		if not actor.combat.is_attacking():
			if steering_clock <= 0 and is_instance_valid(crowd):
				steering_clock = 0.1
				separation = crowd.separation(actor)
			movement += separation
	if actor.health.is_alive() and not pack.has_target() and not actor.combat.is_attacking():
		var offset := home - actor.global_position
		offset.y = 0
		if offset.length() > 0.15:
			movement = offset.normalized() * speed
			actor.rotation.y = atan2(-offset.x, -offset.z)
	movement *= actor.statuses.movement_multiplier()
	movement += actor.combat.consume_motion_velocity(delta) + actor.statuses.consume_push(delta)
	actor.velocity.x = movement.x
	actor.velocity.z = movement.z
	if not actor.is_on_floor():
		actor.velocity.y -= 24.0 * delta
	else:
		actor.velocity.y = 0
	actor.move_and_slide()
