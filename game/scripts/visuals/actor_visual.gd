class_name ActorVisual
extends Node3D
## Replaceable presentation adapter. Gameplay never addresses bones or meshes.
@export var creature: bool = false
@export var tint := Color(0.22, 0.34, 0.48)
var skeleton: Skeleton3D
var animation_player: AnimationPlayer
var sockets: Dictionary = {}
var material: StandardMaterial3D
var label: Label3D
var flash: float = 0.0
var state: StringName = &""

func _ready() -> void:
	material = StandardMaterial3D.new()
	material.albedo_color = tint
	skeleton = Skeleton3D.new()
	skeleton.name = "Skeleton3D"
	add_child(skeleton)
	_bone("Root", Vector3.ZERO)
	_bone("Torso", Vector3(0, 1.05, 0))
	_bone("Head", Vector3(0, 1.62, -0.06))
	_bone("RightHand", Vector3(0.43, 1.25, 0))
	_bone("LeftHand", Vector3(-0.43, 1.25, 0))
	_bone("RightLeg", Vector3(0.18, 0.65, 0))
	_bone("LeftLeg", Vector3(-0.18, 0.65, 0))
	var torso := _socket("Torso", "ArmorSocket")
	var head := _socket("Head", "HeadSocket")
	var right := _socket("RightHand", "WeaponSocket")
	var left := _socket("LeftHand", "OffhandSocket")
	var leg_r := _socket("RightLeg", "RightBootSocket")
	var leg_l := _socket("LeftLeg", "LeftBootSocket")
	_box(torso, Vector3.ZERO, Vector3(0.65, 0.65, 0.38), material)
	var skin := _material(Color(0.43, 0.55, 0.26) if creature else Color(0.76, 0.58, 0.4))
	_box(head, Vector3.ZERO, Vector3(0.49, 0.42, 0.4), skin)
	_box(head, Vector3(0, -0.02, -0.23), Vector3(0.32, 0.12, 0.14), skin)
	for side in [-1, 1]:
		_box(head, Vector3(side * 0.13, 0.04, -0.215), Vector3(0.07, 0.05, 0.03), _material(Color(0.9, 0.8, 0.35)))
	_box(right, Vector3(0, -0.23, 0), Vector3(0.2, 0.5, 0.22), skin)
	_box(left, Vector3(0, -0.23, 0), Vector3(0.2, 0.5, 0.22), skin)
	var leather := _material(Color(0.19, 0.14, 0.1))
	_box(leg_r, Vector3(0, -0.3, -0.04), Vector3(0.24, 0.65, 0.32), leather)
	_box(leg_l, Vector3(0, -0.3, -0.04), Vector3(0.24, 0.65, 0.32), leather)
	if creature:
		_box(head, Vector3(-0.32, 0.1, 0), Vector3(0.25, 0.14, 0.17), skin)
		_box(head, Vector3(0.32, 0.1, 0), Vector3(0.25, 0.14, 0.17), skin)
		_box(right, Vector3(0, -0.45, -0.34), Vector3(0.15, 0.16, 0.8), leather)
	else:
		equip_visual(&"WeaponSocket", preload("res://scenes/visuals/iron_sword.tscn"))
		equip_visual(&"ArmorSocket", preload("res://scenes/visuals/traveler_armor.tscn"))
	label = Label3D.new()
	label.position.y = 2.2
	label.font_size = 28
	label.pixel_size = 0.005
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)
	animation_player = AnimationPlayer.new()
	animation_player.name = "AnimationPlayer"
	add_child(animation_player)
	var library := AnimationLibrary.new()
	for clip in [&"idle", &"run", &"windup", &"active", &"recovery", &"death"]:
		library.add_animation(clip, _clip(clip))
	animation_player.add_animation_library("", library)

func _bone(bone_name: String, location: Vector3) -> void:
	var index := skeleton.get_bone_count()
	skeleton.add_bone(bone_name)
	if index > 0:
		skeleton.set_bone_parent(index, 0)
	skeleton.set_bone_rest(index, Transform3D(Basis.IDENTITY, location))
	skeleton.set_bone_pose_position(index, location)

func _socket(bone_name: String, socket_name: String) -> BoneAttachment3D:
	var attachment := BoneAttachment3D.new()
	attachment.name = socket_name
	attachment.bone_name = bone_name
	skeleton.add_child(attachment)
	sockets[StringName(socket_name)] = attachment
	return attachment

func equip_visual(slot: StringName, scene: PackedScene) -> void:
	if not sockets.has(slot):
		return
	var socket: Node3D = sockets[slot]
	var previous := socket.get_node_or_null("Equipment")
	if previous:
		socket.remove_child(previous)
		previous.queue_free()
	if scene:
		var equipment := scene.instantiate()
		equipment.name = "Equipment"
		socket.add_child(equipment)

func _clip(clip: StringName) -> Animation:
	var animation := Animation.new()
	animation.length = 1.0
	if clip == &"idle" or clip == &"run":
		animation.loop_mode = Animation.LOOP_LINEAR
	for bone_name in ["Root", "Torso", "RightHand", "LeftHand", "RightLeg", "LeftLeg"]:
		var track := animation.add_track(Animation.TYPE_ROTATION_3D)
		animation.track_set_path(track, NodePath("Skeleton3D:" + bone_name))
		for step in range(5):
			var t := step / 4.0
			var angle := Vector3.ZERO
			if clip == &"run" and bone_name != "Root" and bone_name != "Torso":
				angle.x = sin(t * TAU) * 0.65 * (-1.0 if bone_name in ["LeftLeg", "RightHand"] else 1.0)
			elif clip == &"idle" and bone_name == "Torso":
				angle.x = sin(t * TAU) * 0.025
			elif bone_name == "RightHand":
				if clip == &"windup":
					angle = Vector3(-0.7 * t, -1.2 * t, 0)
				elif clip == &"active":
					angle = Vector3(-0.7, lerpf(-1.2, 1.3, t), 0)
				elif clip == &"recovery":
					angle = Vector3(-0.7 * (1 - t), 1.3 * (1 - t), 0)
			if clip == &"death" and bone_name == "Root":
				angle.z = t * PI * 0.5
			animation.rotation_track_insert_key(track, t, Quaternion.from_euler(angle))
	return animation

func present(velocity: Vector3, combat: MeleeCombat, health: HealthComponent, title: String, delta: float) -> void:
	flash = maxf(0, flash - delta)
	var next: StringName = &"idle"
	var duration := 1.0
	if not health.is_alive():
		next = &"death"
	elif combat.is_attacking():
		next = StringName(combat.phase_name().to_lower())
		match combat.phase:
			MeleeCombat.Phase.WINDUP: duration = combat.attack.windup
			MeleeCombat.Phase.ACTIVE: duration = combat.attack.active
			MeleeCombat.Phase.RECOVERY: duration = combat.attack.recovery
	elif Vector2(velocity.x, velocity.z).length() > 0.2:
		next = &"run"
		duration = 0.6
	if next != state:
		state = next
		animation_player.play(next, 0.04, 1.0 / maxf(duration, 0.01))
	var color := tint
	if not health.is_alive(): color = Color(0.22, 0.23, 0.18)
	elif flash > 0: color = Color(1, 0.95, 0.8)
	elif next == &"windup": color = Color(0.95, 0.58, 0.14)
	elif next == &"active": color = Color(0.8, 0.25, 0.1)
	material.albedo_color = color
	label.text = "%s  %d/%d" % [title, health.current, health.maximum]
	label.visible = health.is_alive()

func react_to_hit() -> void:
	flash = 0.18

func _material(color: Color) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	return result

func _box(parent: Node3D, location: Vector3, size: Vector3, surface: Material) -> void:
	var instance := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = size
	instance.mesh = box
	instance.position = location
	instance.material_override = surface
	parent.add_child(instance)
