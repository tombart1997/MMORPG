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
var nameplate_allowed: bool = true
var trail: MeshInstance3D
var trail_points: Array[Vector3] = []
var long_sword: bool = false
var contact_shadow: MeshInstance3D
static var contact_mesh: PlaneMesh

func weapon_clip(clip: StringName) -> StringName:
	# Equipment style selects presentation only; combat resources retain their timings.
	if not long_sword: return clip
	var styled: StringName = &"longsword_idle" if clip == &"idle" else &"longsword_run" if clip == &"run" else StringName(String(clip).replace("attack_", "longsword_"))
	return styled if animation_player.has_animation(styled) else clip

func apply_variant(data: EnemyData) -> void:
	creature = true
	CreatureMaterials.apply(model,data,get_parent().get_index())
	if data.id == &"young":
		# Fresh saplings have a rounder head and shorter, lighter body than adult guardians.
		skeleton.set_bone_pose_scale(skeleton.find_bone("Head"),Vector3.ONE*1.12)
		label.modulate = Color("dde99d")

func _ready() -> void:
	assert(profile != null and profile.model != null, "Visual profile must provide an imported model")
	creature = profile.creature
	model = profile.model.instantiate() as Node3D
	add_child(model)
	if is_instance_valid(contact_shadow): contact_shadow.queue_free()
	if contact_mesh == null:
		contact_mesh = PlaneMesh.new()
		contact_mesh.size = Vector2(1.35,1.35)
		var shadow_material := ShaderMaterial.new()
		shadow_material.shader = load("res://assets/world_kit/contact_shadow.gdshader")
		contact_mesh.material = shadow_material
	contact_shadow = MeshInstance3D.new()
	contact_shadow.mesh = contact_mesh
	contact_shadow.top_level = true
	contact_shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	contact_shadow.visibility_range_end = 28
	contact_shadow.set_meta("contact_shadow",true)
	contact_shadow.visible = get_parent() is ActorBody
	add_child(contact_shadow)
	# Preserve the authored forged surfaces of the hero; older humanoids use painted tiles.
	if not creature and not profile.preserve_authored_materials: HumanoidPaint.apply(model)
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
	label.font_size = 22
	label.pixel_size = 0.005
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = Color(0.9, 0.85, 0.68)
	label.visibility_range_end = 14.0
	label.visibility_range_end_margin = 2.0
	add_child(label)
	ready_for_animation = true
	_sample(&"idle", 0)
	if not creature:
		trail=MeshInstance3D.new()
		trail.top_level=true
		trail.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var material:=StandardMaterial3D.new()
		material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
		material.cull_mode=BaseMaterial3D.CULL_DISABLED
		material.vertex_color_use_as_albedo=true
		material.albedo_color=Color(.69,.82,.85,.24)
		trail.material_override=material
		add_child(trail)

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
	if slot == &"WeaponSocket":
		long_sword = false
		var weapon_model := socket.get_node_or_null("Equipment") as Node3D
		if weapon_model:
			var tip := weapon_model.get_node_or_null("Tip") as Node3D
			var grip := weapon_model.get_node_or_null("Grip") as Node3D
			if tip and grip:
				long_sword = weapon_model.to_local(tip.global_position).distance_to(weapon_model.to_local(grip.global_position)) * weapon_model.scale.z >= profile.long_sword_minimum_length
			if weapon_model.has_meta("two_handed"): long_sword = bool(weapon_model.get_meta("two_handed"))

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
	return normalized * animation_player.get_animation(weapon_clip(combat.attack.animation_clip)).length

func present(velocity: Vector3, combat: MeleeCombat, health: HealthComponent, title: String, delta: float) -> void:
	if not ready_for_animation:
		return
	if is_instance_valid(contact_shadow) and get_parent() is ActorBody:
		var actor := get_parent() as ActorBody
		contact_shadow.global_position = actor.global_position+Vector3.UP*.026
		if actor.is_on_floor(): contact_shadow.basis = Basis(Quaternion(Vector3.UP,actor.get_floor_normal()))
		contact_shadow.visible = health.is_alive() and not (actor.enemy_definition and actor.enemy_definition.family == &"wisp")
		var size_value := maxf(.7,scale.x) * (1.7 if actor.mounts and actor.mounts.mounted else 1.0)
		contact_shadow.scale = Vector3(size_value,1,size_value)
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
			if creature: ArtVFX.burst(self, Vector3(0,.65,0), Color(.48,.40,.19), 7, .6)
			death_time = 0.0
			hit_time = 1.0
		death_time = minf(death_time + delta, animation_player.get_animation(clip).length)
		time = death_time
	elif get_parent() is ActorBody and get_parent().skills and get_parent().skills.busy():
		var skills: PlayerSkills = get_parent().skills
		var skill := skills.current.skill
		next = &"skill"
		clip = skill.animation
		if not creature and not (get_parent().mounts and get_parent().mounts.mounted):
			# Sword skills use the same body mechanics and equipment grip as basic cuts.
			clip = weapon_clip(&"attack_03" if clip == &"skill_riposte" else clip)
		key = "%s:skill:%d" % [clip, skills.serial]
		var normalized := 0.0
		if skills.elapsed < skill.windup: normalized = 0.3 * skills.elapsed / maxf(0.01, skill.windup)
		else: normalized = 0.3 + 0.7 * clampf((skills.elapsed - skill.windup) / maxf(0.01, skill.recovery), 0, 1)
		time = normalized * animation_player.get_animation(clip).length
	elif get_parent() is ActorBody and get_parent().statuses.has(&"guard") and not creature and not combat.is_attacking() and speed < .15:
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
	if not creature and health.is_alive() and next != &"skill" and next != &"guard":
		if not (get_parent().mounts and get_parent().mounts.mounted): clip = weapon_clip(clip)
		key += ":long" if long_sword else ":regular"
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
	var running_legs: Dictionary = {}
	if next == &"skill" and speed > .15:
		locomotion_time += delta * clampf(speed / profile.run_reference_speed, 0, 2.5)
		_sample(&"run", fposmod(locomotion_time, animation_player.get_animation(&"run").length))
		for bone_name in ["Thigh.L", "Thigh.R", "Shin.L", "Shin.R", "Foot.L", "Foot.R"]:
			var index := skeleton.find_bone(bone_name)
			if index >= 0: running_legs[index] = skeleton.get_bone_pose_rotation(index)
	_sample(clip, time)
	for index in running_legs: skeleton.set_bone_pose_rotation(index, running_legs[index])
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
	# Imported clips key scale as well as rotation. Keep the sapling proportions
	# on the final sampled pose instead of letting those scale keys restore adults.
	if creature and get_parent() is ActorBody and get_parent().enemy_definition and get_parent().enemy_definition.id == &"young":
		skeleton.set_bone_pose_scale(skeleton.find_bone("Head"),Vector3.ONE*1.12)
	if health.is_alive() and get_parent() is ActorBody and get_parent().mounts and get_parent().mounts.mounted:
		if combat.is_attacking():
			# Solve the final mounted pose after transitions/recoil; blending an outside
			# cut with the old inward guard would sweep the blade through the saddle.
			_mounted_cut(combat)
		else:
			_sample(&"idle", 0.0)
			var horse := get_parent().mounts.model as TrailHorse
			_rider_bone("Spine",Vector3(.025*sin(horse.phase*TAU),0,0))
			_pose_weapon(Vector3(.42,1.12,-.12),Vector3(.68,-.68,.27))
		for side in ["L", "R"]:
			var sign_value := -1.0 if side == "L" else 1.0
			_rider_bone("Thigh." + side, Vector3(.64,0,sign_value*.62))
			_rider_bone("Shin." + side, Vector3(-.94,0,0))
			# The pelvis can rotate without pulling either boot out of its stirrup.
			var stirrup := to_local(get_parent().mounts.model.stirrup_world(sign_value))
			_pose_chain(["Shin."+side,"Thigh."+side],"Foot."+side,stirrup)
			var foot_index := skeleton.find_bone("Foot."+side)
			_set_global_bone_basis(foot_index,skeleton.get_bone_global_rest(foot_index).basis)
		var rein_point := to_local(get_parent().mounts.model.rein_grip_world())
		var hand_index := skeleton.find_bone("Hand.L")
		for iteration in 3:
			var hand_point: Vector3 = skeleton.to_local(to_global(rein_point))-skeleton.get_bone_global_pose(hand_index).basis*sockets[&"OffhandSocket"].position
			_pose_chain(["Forearm.L","UpperArm.L"],"Hand.L",to_local(skeleton.to_global(hand_point)))
	label.text = title
	if get_parent() is ActorBody:
		var statuses: CombatStatuses = get_parent().statuses
		if statuses.has(&"open"): label.text += " | OPEN"
		if statuses.movement_multiplier() < 1: label.text += " | SLOW"
	label.visible = health.is_alive() and creature and nameplate_allowed
	# Manual animation seeking updates the skin before BoneAttachment's deferred signal.
	# Keep equipment and effects on that same pose, including transition and recoil.
	for socket_name in sockets:
		var socket: Node3D = sockets[socket_name]
		var attachment := socket.get_parent() as BoneAttachment3D
		attachment.transform = skeleton.get_bone_global_pose(skeleton.find_bone(attachment.bone_name))
	_update_trail(combat, health.is_alive())

func bone_world_transform(bone_name: StringName) -> Transform3D:
	var index := skeleton.find_bone(bone_name)
	return skeleton.global_transform * skeleton.get_bone_global_pose(index) if index >= 0 else global_transform

func socket_world_transform(socket_name: StringName) -> Transform3D:
	var socket: Node3D = sockets[socket_name]
	var attachment := socket.get_parent() as BoneAttachment3D
	return bone_world_transform(attachment.bone_name) * socket.transform

func equipped_weapon() -> Node3D:
	return sockets[&"WeaponSocket"].get_node_or_null("Equipment") as Node3D

func weapon_marker_world(marker_name: StringName) -> Vector3:
	var equipment := equipped_weapon()
	var socket_pose := socket_world_transform(&"WeaponSocket")
	if equipment == null: return socket_pose.origin
	var marker := equipment.get_node_or_null(NodePath(marker_name)) as Node3D
	if marker == null: return (socket_pose * equipment.transform).origin
	var marker_local := equipment.global_transform.affine_inverse() * marker.global_transform
	return (socket_pose * equipment.transform * marker_local).origin

func _update_trail(combat: MeleeCombat, alive: bool) -> void:
	if trail == null: return
	var active:=alive and combat.phase==MeleeCombat.Phase.ACTIVE
	var actor:=get_parent() as ActorBody
	if alive and actor.skills and actor.skills.busy():
		var skill := actor.skills.current.skill
		var cutting := String(skill.animation).begins_with("attack_") or skill.animation == &"skill_riposte"
		active=cutting and actor.skills.elapsed>=skill.windup and actor.skills.elapsed<skill.windup+.16
	var equipment:Node3D=sockets[&"WeaponSocket"].get_node_or_null("Equipment")
	trail.material_override.albedo_color = Color(.2,1,.55,.3) if actor.statuses.has(&"spirit_edge") else (Color(actor.skills.current.skill.color, .3) if actor.skills and actor.skills.busy() else Color(.69,.82,.85,.24))
	if not active or equipment==null or equipment.get_node_or_null("Tip")==null:
		trail.hide()
		trail_points.clear()
		return
	var tip := weapon_marker_world(&"Tip")
	var grip := weapon_marker_world(&"Grip")
	trail_points.append(grip.lerp(tip,.45))
	trail_points.append(tip)
	while trail_points.size()>8:
		trail_points.pop_front()
		trail_points.pop_front()
	if trail_points.size()<4: return
	var surface:=SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(0,trail_points.size()-2,2):
		surface.set_color(Color(1,1,1,(i+2)/float(trail_points.size())))
		for index in [i,i+1,i+3,i,i+3,i+2]: surface.add_vertex(trail_points[index])
	trail.mesh=surface.commit()
	trail.show()

func react_to_hit() -> void:
	hit_time = 0.0
	ArtVFX.burst(self, Vector3(0,.95,0), Color(.76,.64,.35) if creature else Color(.85,.78,.56), 4, .34)

func _rider_bone(bone_name: String, angles: Vector3) -> void:
	var index := skeleton.find_bone(bone_name)
	if index < 0: return
	var rest := skeleton.get_bone_global_rest(index).basis
	var rotation_delta := rest.inverse() * Basis.from_euler(angles) * rest
	skeleton.set_bone_pose_rotation(index, skeleton.get_bone_pose_rotation(index) * rotation_delta.get_rotation_quaternion())

func _swing_progress(combat: MeleeCombat) -> float:
	match combat.phase:
		MeleeCombat.Phase.WINDUP: return .3 * clampf(combat.phase_elapsed / combat.attack.windup, 0, 1)
		MeleeCombat.Phase.ACTIVE: return .3 + .35 * clampf(combat.phase_elapsed / combat.attack.active, 0, 1)
		_: return .65 + .35 * clampf(combat.phase_elapsed / combat.attack.recovery, 0, 1)

func _mounted_cut(combat: MeleeCombat) -> void:
	var t := _swing_progress(combat)
	var side := -1.0 if combat.sequence_index % 2 == 0 else 1.0
	# Each cut makes a backward circle in an OUTSIDE diagonal plane. Transfer to
	# the next side happens above the rider, with the blade pointing up throughout.
	var enter := smoothstep(0.0,.18,t)
	var leave := smoothstep(.82,1.0,t)
	var weight := enter*(1.0-leave)
	var circle := clampf((t-.18)/.64,0.0,1.0)*TAU
	_sample(&"idle", 0)
	_rider_bone("Hips",Vector3(.035*weight,-side*.20*weight,-side*.10*weight))
	_rider_bone("Spine",Vector3(.055*weight,-side*.22*weight,-side*.12*weight))
	_rider_bone("Chest",Vector3(.10*weight,-side*.37*weight,-side*.12*weight))
	_rider_bone("Head",Vector3(-.07*weight,side*.48*weight,0))
	# The sword arm reaches directly on the right and across the chest on the left.
	# Give the direct cut extra lateral room for the pommel, and the crossed cut
	# extra forward room; a symmetric hand arc clips the hilt into the cuirass.
	var hand := Vector3(side*((.56 if side < 0 else .72)+.035*sin(circle)),1.40+.13*cos(circle),(-.45 if side < 0 else -.36)+.10*sin(circle))
	var direction := Vector3(side*.76,.60*cos(circle)-.16*sin(circle),.16*cos(circle)+.60*sin(circle)).normalized()
	var transfer := sin(weight*PI)
	var grip := Vector3(.48,1.63,-.35).lerp(hand,weight)+Vector3(0,.30*transfer,-.24*transfer)
	_pose_weapon(grip,Vector3(.55,.81,-.20).lerp(direction,weight).normalized())

func _pose_weapon(hand_point: Vector3, blade_direction: Vector3) -> void:
	var hand := skeleton.find_bone("Hand.R")
	if hand < 0: return
	var socket: Node3D = sockets[&"WeaponSocket"]
	var equipment := socket.get_node_or_null("Equipment") as Node3D
	if equipment == null or equipment.get_node_or_null("Tip") == null: return
	var local_blade: Vector3 = socket.basis * equipment.basis * (equipment.get_node("Tip").position - equipment.get_node("Grip").position)
	var toward := (skeleton.global_basis.inverse() * global_basis * blade_direction).normalized()
	# Constrain the physical Grip, not just Hand.R's origin. The bone/socket offset
	# changes when the wrist rotates and otherwise pulls the blade into the torso.
	for iteration in 4:
		var hand_basis := skeleton.get_bone_global_pose(hand).basis
		var grip_offset: Vector3 = socket.transform*equipment.transform*equipment.get_node("Grip").position
		var target := skeleton.to_local(to_global(hand_point))-hand_basis*grip_offset
		_pose_chain(["Forearm.R","UpperArm.R"],"Hand.R",to_local(skeleton.to_global(target)))
		hand_basis = skeleton.get_bone_global_pose(hand).basis
		var from := (hand_basis * local_blade).normalized()
		_set_global_bone_basis(hand, Basis(Quaternion(from,toward)) * hand_basis)

func _pose_chain(chain: Array, tip_name: String, point: Vector3) -> void:
	var tip_index := skeleton.find_bone(tip_name)
	var target := skeleton.to_local(to_global(point))
	for iteration in 9:
		for bone_name in chain:
			var bone := skeleton.find_bone(bone_name)
			var pose := skeleton.get_bone_global_pose(bone)
			var from := skeleton.get_bone_global_pose(tip_index).origin-pose.origin
			var toward := target-pose.origin
			if from.length_squared() < .00001 or toward.length_squared() < .00001: continue
			_set_global_bone_basis(bone,Basis(Quaternion(from.normalized(),toward.normalized()))*pose.basis)

func _set_global_bone_basis(bone: int, desired: Basis) -> void:
	var parent := skeleton.get_bone_parent(bone)
	var parent_basis := skeleton.get_bone_global_pose(parent).basis if parent >= 0 else Basis.IDENTITY
	skeleton.set_bone_pose_rotation(bone,(parent_basis.inverse()*desired).orthonormalized().get_rotation_quaternion())

func apply_class_tint(identity: String) -> void:
	var colors := {"Ironvow":Color.WHITE, "Threadseer":Color("9a91d7"), "Cinderhand":Color("d89361"), "Fenstrider":Color("83ad86")}
	for mesh: MeshInstance3D in find_children("*", "MeshInstance3D", true, false):
		if mesh.mesh == null: continue
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.mesh.surface_get_material(surface) as StandardMaterial3D
			if source and not creature and model.is_ancestor_of(mesh) and not profile.preserve_authored_materials: source=HumanoidPaint.surface(source)
			if source:
				var material := source.duplicate() as StandardMaterial3D
				var name_value := String(source.resource_name)
				if not ("Skin" in name_value or "Eye" in name_value or "Iris" in name_value or "Pupil" in name_value or "Hair" in name_value or "FaceCrease" in name_value):
					material.albedo_color *= colors.get(identity, Color.WHITE)
				mesh.set_surface_override_material(surface, material)
