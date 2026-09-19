class_name EnemyBrain
extends Node
var actor: ActorBody
var pack: AggroGroup
var speed: float = 2.4
var stagger: float = 0.0
var cooldown: float = 0.0

func _ready() -> void:
	actor = get_parent() as ActorBody
	actor.health.damaged.connect(_on_damaged)
	cooldown = float(actor.get_index() % 6) * 0.13

func _on_damaged(_amount: float, _source: Node3D) -> void:
	stagger = 0.22
	actor.combat.cancel()

func _physics_process(delta: float) -> void:
	stagger = maxf(0.0, stagger - delta)
	cooldown = maxf(0.0, cooldown - delta)
	var movement := Vector3.ZERO
	if actor.health.is_alive() and pack.has_target() and stagger <= 0.0:
		var offset := pack.target.global_position - actor.global_position
		offset.y = 0.0
		if not actor.combat.is_attacking():
			if offset.length_squared() > 0.001:
				actor.rotation.y = atan2(-offset.x, -offset.z)
			if offset.length() > 1.35:
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
	actor.velocity.x = movement.x
	actor.velocity.z = movement.z
	if not actor.is_on_floor():
		actor.velocity.y -= 24.0 * delta
	else:
		actor.velocity.y = 0
	actor.move_and_slide()
