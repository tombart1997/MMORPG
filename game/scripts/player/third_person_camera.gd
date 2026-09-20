class_name ThirdPersonCamera
extends Node3D
var yaw: float = 0.0
var orbiting: bool = false
var pitch: float = -0.55
var distance: float = 8.0
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
	camera.fov = 60
	camera.current = true
	arm.add_child(camera)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT and not event.pressed: orbiting = false

func _unhandled_input(event: InputEvent) -> void:
	if subject is ActorBody and subject.ui_open: return
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			orbiting = event.pressed
			get_viewport().set_input_as_handled()
		if event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP: distance = maxf(4.0, distance - 0.6)
		if event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN: distance = minf(13.0, distance + 0.6)
	if event is InputEventMouseMotion and orbiting:
		apply_look_delta(event.relative)
		get_viewport().set_input_as_handled()

func apply_look_delta(relative: Vector2) -> void:
	yaw -= relative.x * 0.003
	pitch = clampf(pitch - relative.y * 0.003, -1.05, 0.15)

func _process(_delta: float) -> void:
	global_position = subject.global_position + Vector3(0, 1.3, 0)
	rotation = Vector3(pitch, yaw, 0)
	arm.spring_length = distance

func forward() -> Vector3:
	return Vector3(-sin(yaw), 0, -cos(yaw))
