class_name TrailHorse
extends Node3D
## Imported continuous skin; gameplay movement/collision remains on ActorBody.
signal hoofstep(point: Vector3)
var skeleton: Skeleton3D
var player: AnimationPlayer
var phase := 0.0
var current_clip: StringName = &"idle"
var previous_pose: Array[Quaternion] = []
var previous_positions: Array[Vector3] = []
var blend_time := 1.0
var contacts: Dictionary = {}
var motion_speed := 0.0
var combat_lean := 0.0
const SEAT_REST := Vector3(0,1.535,0)
const STIRRUP_ANKLE_HEIGHT := .92

func stirrup_world(side: float) -> Vector3:
	return bone_point("Body",Vector3(side*.42,STIRRUP_ANKLE_HEIGHT,-.08))

func _ready() -> void:
	var model := preload("res://assets/mounts/trail_horse.glb").instantiate()
	add_child(model)
	skeleton = model.find_children("*","Skeleton3D",true,false)[0]
	player = model.find_children("*","AnimationPlayer",true,false)[0]
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	player.play(&"idle")
	player.seek(0,true)
	for tag in ["Fore.L","Fore.R","Hind.L","Hind.R"]: contacts[tag] = true

func bone_point(name_value: String, rest_point: Vector3) -> Vector3:
	var index := skeleton.find_bone(name_value)
	var deformation := skeleton.get_bone_global_pose(index)*skeleton.get_bone_global_rest(index).affine_inverse()
	return skeleton.global_transform * deformation * rest_point

func saddle_offset() -> Vector3:
	return to_local(bone_point("Body",SEAT_REST))-SEAT_REST

func rein_grip_world() -> Vector3:
	return bone_point("Body",Vector3(-.15,1.83,-.22))

func travel(velocity: Vector3, delta: float) -> void:
	motion_speed = Vector2(velocity.x,velocity.z).length()
	var next: StringName = &"idle" if motion_speed < .15 else &"walk" if motion_speed < 2.8 else &"trot" if motion_speed < 5.5 else &"canter"
	if next != current_clip:
		previous_pose.clear();previous_positions.clear()
		for i in skeleton.get_bone_count():
			previous_pose.append(skeleton.get_bone_pose_rotation(i))
			previous_positions.append(skeleton.get_bone_pose_position(i))
		current_clip = next;blend_time = 0
		player.play(current_clip)
	# Stance foot travel is proportional to real ground speed.
	var cadence := 0.25 if current_clip == &"idle" else motion_speed*.65/.60 if current_clip == &"walk" else motion_speed*.40/.76 if current_clip == &"trot" else motion_speed*.30
	phase = fposmod(phase+delta*cadence,1.0)
	player.seek(phase*player.get_animation(current_clip).length,true)
	blend_time = minf(1,blend_time+delta/.16)
	if blend_time < 1:
		for i in skeleton.get_bone_count():
			skeleton.set_bone_pose_rotation(i,previous_pose[i].slerp(skeleton.get_bone_pose_rotation(i),blend_time))
			skeleton.set_bone_pose_position(i,previous_positions[i].lerp(skeleton.get_bone_pose_position(i),blend_time))
	var actor := get_parent() as ActorBody
	var lean_target := 0.0
	if actor and actor.combat.is_attacking():
		lean_target = (-1.0 if actor.combat.sequence_index%2 == 0 else 1.0)*sin(actor.visual._swing_progress(actor.combat)*PI)
	combat_lean = lerpf(combat_lean,lean_target,minf(1,delta*18))
	var body := skeleton.find_bone("Body")
	var rest := skeleton.get_bone_global_rest(body).basis
	var turn := rest.inverse()*Basis.from_euler(Vector3(.012*absf(combat_lean),0,-.025*combat_lean))*rest
	skeleton.set_bone_pose_rotation(body,skeleton.get_bone_pose_rotation(body)*turn.get_rotation_quaternion())
	for tag in contacts:
		var index := skeleton.find_bone(tag+".Hoof")
		var foot := skeleton.global_transform*skeleton.get_bone_global_pose(index).origin
		var contact := to_local(foot).y < .195
		if contact and not contacts[tag] and motion_speed > .4 and blend_time > .8: hoofstep.emit(foot)
		contacts[tag] = contact
