class_name ActorVisual
extends Node3D
## Presentation-only state driver. Imported animations never move the actor or apply damage.
@export var profile: CharacterVisualProfile
var creature: bool = false
var skeleton: Skeleton3D
var animation_player: AnimationPlayer
var model: Node3D
var sockets: Dictionary = {}
var label: Label3D
var state: StringName = &""
var sampled_clip: StringName = &""
var sampled_time: float = 0.0
var locomotion_time: float = 0.0
var death_time: float = 0.0
var hit_time: float = 1.0
var hit_weight: float = 0.0
var transition_time: float = 1.0
var transition_duration: float = 0.1
var previous_key: String = ""
var previous_rotations: Array[Quaternion] = []
var previous_positions: Array[Vector3] = []
var ready_for_animation: bool = false

func _ready() -> void:
	assert(profile != null and profile.model != null, "Visual profile must provide an imported model")
	creature = profile.creature
	model = profile.model.instantiate() as Node3D
	add_child(model)
	var rigs := model.find_children("*", "Skeleton3D", true, false)
	var players := model.find_children("*", "AnimationPlayer", true, false)
	assert(rigs.size() == 1 and players.size() == 1, "Expected one imported rig and AnimationPlayer")
	skeleton = rigs[0] as Skeleton3D
	animation_player = players[0] as AnimationPlayer
	animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for clip in [&"idle", &"run", &"attack_01", &"hit", &"death"]:
		assert(animation_player.has_animation(clip), "Imported model missing clip: " + clip)
	for socket_name in profile.socket_bones:
		var bone_name: StringName = profile.socket_bones[socket_name]
		var index := skeleton.find_bone(bone_name)
		assert(index >= 0, "Missing socket bone: " + bone_name)
		var attachment := BoneAttachment3D.new()
		attachment.name = String(socket_name) + "Attachment"
		attachment.bone_name = bone_name
		skeleton.add_child(attachment)
		# Equipment is authored in model coordinates at the attachment origin.
		# Undo only the bone's bind orientation; animated bone motion remains intact.
		var socket := Node3D.new()
		socket.name = socket_name
		socket.basis = skeleton.get_bone_global_rest(index).basis.inverse()
		socket.position = socket.basis * Vector3(profile.socket_offsets.get(socket_name, Vector3.ZERO))
		attachment.add_child(socket)
		sockets[socket_name] = socket
	equip_visual(&"WeaponSocket", profile.weapon)
	equip_visual(&"ArmorSocket", profile.armor)
	label = Label3D.new()
	label.position.y = profile.label_height
	label.font_size = 26
	label.pixel_size = 0.007
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = Color(0.9, 0.85, 0.68)
	label.visibility_range_end = 14.0
	label.visibility_range_end_margin = 2.0
	add_child(label)
	ready_for_animation = true
	_sample(&"idle", 0)

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

func _sample(clip: StringName, time: float) -> void:
	if animation_player.current_animation != clip:
		animation_player.play(clip)
	animation_player.seek(time, true)

func _remember_pose() -> void:
	previous_rotations.clear()
	previous_positions.clear()
	for i in range(skeleton.get_bone_count()):
		previous_rotations.append(skeleton.get_bone_pose_rotation(i))
		previous_positions.append(skeleton.get_bone_pose_position(i))

func attack_sample_time(combat: MeleeCombat) -> float:
	var normalized := 0.0
	match combat.phase:
		MeleeCombat.Phase.WINDUP:
			normalized = profile.active_marker * clampf(combat.phase_elapsed / combat.attack.windup, 0, 1)
		MeleeCombat.Phase.ACTIVE:
			normalized = lerpf(profile.active_marker, profile.recovery_marker,
				clampf(combat.phase_elapsed / combat.attack.active, 0, 1))
		MeleeCombat.Phase.RECOVERY:
			normalized = lerpf(profile.recovery_marker, 1.0,
				clampf(combat.phase_elapsed / combat.attack.recovery, 0, 1))
	return normalized * animation_player.get_animation(combat.attack.animation_clip).length

func present(velocity: Vector3, combat: MeleeCombat, health: HealthComponent, title: String, delta: float) -> void:
	if not ready_for_animation:
		return
	var clip: StringName = &"idle"
	var key := "idle"
	var next: StringName = &"idle"
	var time := 0.0
	var speed := Vector2(velocity.x, velocity.z).length()
	if not health.is_alive():
		next = &"death"
		clip = &"death"
		key = "death"
		if state != &"death":
			death_time = 0.0
			hit_time = 1.0
		death_time = minf(death_time + delta, animation_player.get_animation(clip).length)
		time = death_time
	elif get_parent() is ActorBody and get_parent().skills and get_parent().skills.busy():
		var skills: PlayerSkills = get_parent().skills
		var skill := skills.current.skill
		next = &"skill"
		clip = skill.animation
		key = "%s:skill:%d" % [clip, skills.serial]
		var normalized := 0.0
		if skills.elapsed < skill.windup: normalized = 0.3 * skills.elapsed / maxf(0.01, skill.windup)
		else: normalized = 0.3 + 0.7 * clampf((skills.elapsed - skill.windup) / maxf(0.01, skill.recovery), 0, 1)
		time = normalized * animation_player.get_animation(clip).length
	elif get_parent() is ActorBody and get_parent().statuses.has(&"guard") and not creature and not combat.is_attacking():
		next = &"guard"
		clip = &"skill_guard"
		key = "guard"
		time = 0.3
	elif combat.is_attacking():
		next = StringName(combat.phase_name().to_lower())
		clip = combat.attack.animation_clip
		key = "%s:%d" % [clip, combat.swing_serial]
		assert(animation_player.has_animation(clip), "Missing attack clip: " + clip)
		time = attack_sample_time(combat)
	else:
		if speed > 0.15:
			next = &"run"
			clip = &"run"
			key = "run"
			locomotion_time += delta * clampf(speed / profile.run_reference_speed, 0.0, 1.6)
		else:
			locomotion_time += delta
		time = fposmod(locomotion_time, animation_player.get_animation(clip).length)
	if key != previous_key:
		_remember_pose()
		transition_time = 0.0
		transition_duration = 0.045 if combat.is_attacking() else 0.10
		# Revival discards the fallen pose instead of slowly twisting upright.
		if state == &"death" and health.is_alive():
			transition_duration = 0.0
			hit_time = 1.0
		previous_key = key
	transition_time += delta
	state = next
	# Read the imported hit clip as a delta from rest, then sample the authoritative base clip.
	var hit_rotations: Dictionary = {}
	var hit_length := animation_player.get_animation(&"hit").length
	hit_time += delta
	hit_weight = 0.0
	if health.is_alive() and hit_time < hit_length:
		_sample(&"hit", hit_time)
		hit_weight = sin(PI * hit_time / hit_length)
		for bone_name in profile.reaction_bones:
			var index := skeleton.find_bone(bone_name)
			if index >= 0:
				hit_rotations[index] = skeleton.get_bone_rest(index).basis.get_rotation_quaternion().inverse() * skeleton.get_bone_pose_rotation(index)
	_sample(clip, time)
	sampled_clip = clip
	sampled_time = time
	var blend := 1.0 if transition_duration <= 0 else clampf(transition_time / transition_duration, 0, 1)
	if blend < 1.0:
		for i in range(skeleton.get_bone_count()):
			skeleton.set_bone_pose_rotation(i, previous_rotations[i].slerp(skeleton.get_bone_pose_rotation(i), blend))
			skeleton.set_bone_pose_position(i, previous_positions[i].lerp(skeleton.get_bone_pose_position(i), blend))
	for index in hit_rotations:
		# A small additive recoil preserves leg cadence and the visible attacking arm.
		var recoil: Quaternion = Quaternion.IDENTITY.slerp(hit_rotations[index], 0.65 if combat.is_attacking() else 1.0)
		skeleton.set_bone_pose_rotation(index, skeleton.get_bone_pose_rotation(index) * recoil)
	label.text = "%s  %d/%d" % [title, health.current, health.maximum]
	if get_parent() is ActorBody:
		var statuses: CombatStatuses = get_parent().statuses
		if statuses.has(&"open"): label.text += " | OPEN"
		if statuses.movement_multiplier() < 1: label.text += " | SLOW"
	label.visible = health.is_alive() and creature

func react_to_hit() -> void:
	hit_time = 0.0
