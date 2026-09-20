class_name EnemyBrain
extends Node
var actor: ActorBody
var pack: AggroGroup
var speed: float = 3.2
var stagger: float = 0.0
var cooldown: float = 0.0
var home: Vector3

func _ready() -> void:
	actor = get_parent() as ActorBody
	home = actor.global_position
	actor.health.damaged.connect(_on_damaged)
	cooldown = float(actor.get_index() % 6) * 0.13

func _on_damaged(_amount: float, _source: Node3D) -> void:
	# Ordinary hits react visually but cannot endlessly interrupt a committed strike.
	if not actor.combat.is_attacking():
		stagger = 0.08

func _physics_process(delta: float) -> void:
	if not pack.has_target() and actor.combat.is_attacking(): actor.combat.cancel()
	stagger = maxf(0.0, stagger - delta)
	cooldown = maxf(0.0, cooldown - delta)
	var movement := Vector3.ZERO
	if actor.health.is_alive() and pack.has_target() and stagger <= 0.0:
		var offset := pack.target.global_position - actor.global_position
		offset.y = 0.0
		if not actor.combat.is_attacking():
			if offset.length_squared() > 0.001:
				actor.rotation.y = atan2(-offset.x, -offset.z)
			if offset.length() > 1.65:
				movement = offset.normalized() * speed
			elif cooldown <= 0.0:
				actor.combat.request_attack()
				cooldown = 0.3
		# Mild separation helps the pack spread around the player.
		if not actor.combat.is_attacking():
			for other in pack.members:
				if other == actor or not other.health.is_alive():
					continue
				var away := actor.global_position - other.global_position
				away.y = 0
				if away.length() < 0.95 and away.length() > 0.001:
					movement += away.normalized() * (0.95 - away.length()) * 3.0
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
