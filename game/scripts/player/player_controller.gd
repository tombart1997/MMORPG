class_name PlayerController
extends Node
var actor: ActorBody
var rig: ThirdPersonCamera
var speed: float = 5.5
var attack_requested: bool = false

func _ready() -> void:
	actor = get_parent() as ActorBody
	rig = ThirdPersonCamera.new()
	rig.subject = actor
	add_child(rig)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("attack") and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		attack_requested = true

func _physics_process(delta: float) -> void:
	var direction := Vector3.ZERO
	if actor.health.is_alive():
		var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		direction = Vector3(input.x, 0, input.y).rotated(Vector3.UP, rig.yaw)
		if attack_requested and actor.combat.is_attacking():
			actor.combat.queue_followup()
		if not actor.combat.is_attacking():
			if attack_requested and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
				actor.rotation.y = rig.yaw
				actor.combat.request_attack()
			elif direction.length_squared() > 0.01:
				actor.rotation.y = lerp_angle(actor.rotation.y, atan2(-direction.x, -direction.z), minf(delta * 16, 1))
	attack_requested = false
	if actor.combat.movement_locked():
		direction = Vector3.ZERO
	var motion := actor.combat.consume_motion_velocity(delta)
	actor.velocity.x = direction.x * speed + motion.x
	actor.velocity.z = direction.z * speed + motion.z
	if not actor.is_on_floor():
		actor.velocity.y -= 24.0 * delta
	else:
		actor.velocity.y = 0.0
	actor.move_and_slide()
