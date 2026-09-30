class_name PlayerController
extends Node
var actor: ActorBody
var rig: ThirdPersonCamera
var speed: float = 5.5
var attack_requested: bool = false
var auto_attack: bool = false

func stop_auto_attack() -> void:
	if auto_attack: actor.combat.queued = false
	auto_attack = false
	attack_requested = false

func _ready() -> void:
	actor = get_parent() as ActorBody
	rig = ThirdPersonCamera.new()
	rig.subject = actor
	add_child(rig)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("release_mouse"):
		stop_auto_attack()
	if event.is_action_pressed("attack") and not event.is_echo() and not actor.ui_open and actor.health.is_alive():
		if actor.skills: actor.skills.cancel_aim()
		auto_attack = not auto_attack
		attack_requested = auto_attack
		if actor.world_interaction: actor.world_interaction.cancel()
		if not auto_attack: actor.combat.queued = false

func _physics_process(delta: float) -> void:
	if not actor.health.is_alive() or actor.ui_open or (actor.skills and (actor.skills.busy() or actor.skills.armed)):
		stop_auto_attack()
	var direction := Vector3.ZERO
	if actor.health.is_alive() and not actor.ui_open:
		var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		direction = Vector3(input.x, 0, input.y).rotated(Vector3.UP, rig.yaw)
		if input.length_squared() > 0:
			stop_auto_attack()
			if actor.skills: actor.skills.cancel_aim()
			if actor.world_interaction: actor.world_interaction.cancel(true)
		elif actor.navigation and not actor.combat.movement_locked(): direction = actor.navigation.direction(delta)
		if (attack_requested or auto_attack) and actor.combat.is_attacking():
			actor.combat.queue_followup()
		if not actor.combat.is_attacking():
			if attack_requested or auto_attack:
				actor.combat.request_attack()
			elif direction.length_squared() > 0.01 and not (actor.skills and actor.skills.busy()):
				actor.rotation.y = lerp_angle(actor.rotation.y, atan2(-direction.x, -direction.z), minf(delta * 16, 1))
	attack_requested = false
	if actor.skills and actor.skills.motion_remaining > 0:
		direction = Vector3.ZERO
	if actor.combat.movement_locked():
		direction = Vector3.ZERO
	var motion := actor.combat.consume_motion_velocity(delta)
	if actor.stats: speed = actor.stats.value(&"movement_speed")
	if actor.mounts and actor.mounts.mounted: speed = actor.mounts.definition.speed
	if actor.skills: motion += actor.skills.consume_motion(delta)
	motion += actor.statuses.consume_push(delta)
	speed *= actor.statuses.movement_multiplier()
	actor.velocity.x = direction.x * speed + motion.x
	actor.velocity.z = direction.z * speed + motion.z
	if not actor.is_on_floor():
		actor.velocity.y -= 24.0 * delta
	else:
		actor.velocity.y = 0.0
	actor.move_and_slide()
