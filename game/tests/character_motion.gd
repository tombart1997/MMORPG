extends "res://tests/combat_smoke.gd"
## Full-body choreography and live, moving skill attachment review.
var output := "res://.local/character_motion"
var player: ActorBody
var controller: PlayerController

class AttachmentProbe:
	extends Node
	var actor: ActorBody
	var anchor_error := 0.0
	var equipment_error := 0.0
	func _ready() -> void:
		process_priority = 100
	func _process(_delta: float) -> void:
		var visual := actor.visual
		for effect: SkillSpectacle in get_tree().get_nodes_in_group("skill_spectacles"):
			if effect.caster != actor or effect.is_queued_for_deletion() or effect.elapsed <= 0: continue
			anchor_error = maxf(anchor_error,effect.blade_tip.distance_to(visual.weapon_marker_world(&"Tip")))
			anchor_error = maxf(anchor_error,effect.body_anchor.distance_to(visual.bone_world_transform(&"Chest").origin))
		var equipment := visual.equipped_weapon()
		if equipment:
			equipment_error = maxf(equipment_error,equipment.get_node("Tip").global_position.distance_to(visual.weapon_marker_world(&"Tip")))

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output+"/"+label+".png")

func _run() -> void:
	var arguments := OS.get_cmdline_user_args()
	var label_index := arguments.find("--label")
	if label_index >= 0 and label_index+1 < arguments.size(): output += "/"+arguments[label_index+1]
	DirAccess.make_dir_recursive_absolute(output)
	var world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(12)
	player = world.player
	for child in player.get_children():
		if child is PlayerController: controller = child
	for enemy: ActorBody in get_nodes_in_group("enemies"):
		for child in enemy.get_children():
			if child is EnemyBrain: child.set_physics_process(false)
		enemy.hide()
		enemy.collision_layer = 0
		enemy.collision_mask = 0
	player.global_position = Vector3(14,.1,-28)
	player.rotation.y = 0
	controller.rig.yaw = 2.3
	controller.rig.pitch = -.24
	controller.rig.distance = 4.8
	await frames(12)
	player.set_process(false)
	var visual := player.visual
	var rig := visual.skeleton
	var results: Array = []
	for style in ["attack", "longsword"]:
		player.equipment.slots[&"weapon"] = ItemStack.new(&"wakecleaver" if style == "longsword" else &"wayfarer_blade")
		player.equipment.refresh()
		for cut in range(1,4):
			var clip := StringName("%s_%02d" % [style,cut])
			var hips: Array[Quaternion] = []
			var chests: Array[Quaternion] = []
			var hip_points: Array[Vector3] = []
			var foot_points: Array[Vector3] = []
			var foot_drift := 0.0
			var grip_error := 0.0
			for sample in range(41):
				visual._sample(clip,sample/40.0*visual.animation_player.get_animation(clip).length)
				hips.append(rig.get_bone_global_pose(rig.find_bone("Hips")).basis.get_rotation_quaternion())
				chests.append(rig.get_bone_global_pose(rig.find_bone("Chest")).basis.get_rotation_quaternion())
				hip_points.append(rig.get_bone_global_pose(rig.find_bone("Hips")).origin)
				for side in ["L", "R"]:
					var foot := rig.get_bone_global_pose(rig.find_bone("Foot."+side)).origin
					if sample == 0: foot_points.append(foot)
					else: foot_drift = maxf(foot_drift,foot.distance_to(foot_points[0 if side == "L" else 1]))
				if style == "longsword":
					grip_error = maxf(grip_error,visual.socket_world_transform(&"OffhandSocket").origin.distance_to(visual.weapon_marker_world(&"OffhandGrip")))
			var hip_angle := 0.0
			var chest_angle := 0.0
			var weight_shift := 0.0
			for i in hips.size():
				for j in hips.size():
					hip_angle = maxf(hip_angle,rad_to_deg(hips[i].angle_to(hips[j])))
					chest_angle = maxf(chest_angle,rad_to_deg(chests[i].angle_to(chests[j])))
					weight_shift = maxf(weight_shift,hip_points[i].distance_to(hip_points[j]))
			check(hip_angle > 14 and chest_angle > 30 and weight_shift > .07,String(clip)+" visibly drives hips, shoulders and weight transfer")
			check(foot_drift < .025,String(clip)+" keeps both boot contacts planted")
			check(grip_error < .04,String(clip)+" retains the two-hand grip")
			var result := {"clip":clip,"hip_degrees":hip_angle,"shoulder_degrees":chest_angle,"weight_shift_m":weight_shift,"foot_drift_m":foot_drift,"grip_error_m":grip_error}
			results.append(result)
			print("BODY_MOTION ",JSON.stringify(result))
			if cut in [1,3]:
				for phase in [.16,.40,.55]:
					visual._sample(clip,phase*visual.animation_player.get_animation(clip).length)
					for socket_name in visual.sockets:
						var socket: Node3D = visual.sockets[socket_name]
						var attachment := socket.get_parent() as BoneAttachment3D
						attachment.transform = rig.get_bone_global_pose(rig.find_bone(attachment.bone_name))
					await capture("%s_%02d" % [clip,int(phase*100)])
	player.set_process(true)
	# Sample after presentation, rather than between physics movement and render updates.
	var probe := AttachmentProbe.new()
	probe.actor = player
	world.add_child(probe)
	for skill_index in range(6):
		player.skills.cancel_transient()
		player.skills.cooldowns.clear()
		player.statuses.clear()
		player.global_position = Vector3(14,.1,-28)
		player.rotation.y = 0
		await frames(2)
		Input.action_press("move_right")
		check(player.skills.activate(skill_index),"Skill %d casts through the real skill controller" % (skill_index+1))
		var effects_seen := false
		var cut_pose_seen := false
		for frame in range(14):
			await frames(1)
			if player.skills.busy() and skill_index in [0,3,5]:
				var cut := &"attack_01" if skill_index == 0 else &"attack_02" if skill_index == 3 else &"attack_03"
				cut_pose_seen = cut_pose_seen or visual.sampled_clip == visual.weapon_clip(cut)
			for effect: SkillSpectacle in get_nodes_in_group("skill_spectacles"):
				if effect.caster != player or effect.is_queued_for_deletion() or effect.elapsed <= 0: continue
				effects_seen = true
			if frame in [4,8]: await capture("skill_%d_frame_%d" % [skill_index+1,frame])
		Input.action_release("move_right")
		check(effects_seen,"Skill %d emits its skeleton-connected spectacle while moving" % (skill_index+1))
		if skill_index in [0,3,5]: check(cut_pose_seen,"Sword skill %d uses its full-body, equipment-specific cut" % (skill_index+1))
	player.skills.cancel_transient()
	player.skills.cooldowns.clear()
	player.statuses.clear()
	check(player.skills.activate(3),"Bladestorm starts for equipment replacement review")
	await frames(22)
	check(player.equipment.unequip(&"weapon"),"Weapon can be removed after cast recovery while its area remains active")
	await frames(3)
	player.equipment.slots[&"weapon"] = ItemStack.new(&"wayfarer_blade")
	player.equipment.refresh()
	await frames(3)
	check(probe.anchor_error < .005,"Skill blade and body anchors use the current render pose (%.4fm)" % probe.anchor_error)
	check(probe.equipment_error < .005,"Visible equipment and effects share the same pose (%.4fm)" % probe.equipment_error)
	player.skills.cancel_transient()
	player.statuses.clear()
	await frames(55)
	check(get_nodes_in_group("skill_spectacles").is_empty(),"Skill spectacles expire without detached remnants")
	var file := FileAccess.open(output+"/metrics.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"body_clips":results,"effect_anchor_error_m":probe.anchor_error,"equipment_error_m":probe.equipment_error,"failures":failures},"\t"))
	print("Character motion review: %d failures" % failures)
	quit(1 if failures else 0)
