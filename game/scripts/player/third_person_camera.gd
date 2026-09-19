class_name ThirdPersonCamera
extends Node3D
var yaw: float = 0.0
var pitch: float = -0.3
var distance: float = 6.5
var subject: Node3D
var arm: SpringArm3D
var camera: Camera3D

func _ready() -> void:
	top_level = true
	arm = SpringArm3D.new()
	arm.spring_length = distance
	arm.margin = 0.2
	arm.collision_mask = 1
	var probe := SphereShape3D.new()
	probe.radius = 0.2
	arm.shape = probe
	add_child(arm)
	camera = Camera3D.new()
	camera.fov = 70
	camera.current = true
	arm.add_child(camera)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("release_mouse"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			get_viewport().set_input_as_handled()
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			distance = maxf(3.0, distance - 0.5)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			distance = minf(10.0, distance + 0.5)
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		apply_look_delta(event.relative)

func apply_look_delta(relative: Vector2) -> void:
	yaw -= relative.x * 0.003
	pitch = clampf(pitch - relative.y * 0.003, -1.05, 0.15)

func _process(_delta: float) -> void:
	global_position = subject.global_position + Vector3(0, 1.5, 0)
	rotation = Vector3(pitch, yaw, 0)
	arm.spring_length = distance

func forward() -> Vector3:
	return Vector3(-sin(yaw), 0, -cos(yaw))
