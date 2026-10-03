extends Node
## Measure the currently sampled skin every render tick without forcing combat phases.
var actor: ActorBody
var previous_tip := Vector3.ZERO
var previous_serial := -1
var maximum_step := 0.0
var maximum_combo_step := 0.0
var maximum_grip_gap := 0.0
var frames := 0
var elapsed := 0.0
var rows: Array = []

func marker_position(socket_name: StringName, marker: Vector3) -> Vector3:
	var visual := actor.visual
	var socket: Node3D = visual.sockets[socket_name]
	var attachment := socket.get_parent() as BoneAttachment3D
	var bone := visual.skeleton.find_bone(attachment.bone_name)
	return visual.skeleton.global_transform * visual.skeleton.get_bone_global_pose(bone) * socket.transform * marker

func _process(delta: float) -> void:
	if not actor.combat.is_attacking(): return
	var visual := actor.visual
	var equipment: Node3D = visual.sockets[&"WeaponSocket"].get_node("Equipment")
	var tip_marker: Node3D = equipment.get_node("Tip")
	var tip := marker_position(&"WeaponSocket", equipment.transform * tip_marker.position)
	var combat := actor.combat
	var step := previous_tip.distance_to(tip)
	if frames > 0:
		if previous_serial == combat.swing_serial: maximum_step = maxf(maximum_step,step)
		else: maximum_combo_step = maxf(maximum_combo_step,step)
	if equipment.has_node("OffhandGrip"):
		var offhand := marker_position(&"OffhandSocket",Vector3.ZERO)
		var grip := marker_position(&"WeaponSocket", equipment.transform * equipment.get_node("OffhandGrip").position)
		maximum_grip_gap = maxf(maximum_grip_gap,offhand.distance_to(grip))
	rows.append([frames,combat.swing_serial,combat.phase_name(),combat.phase_elapsed,visual.sampled_time,delta,tip.x,tip.y,tip.z])
	previous_tip=tip
	previous_serial=combat.swing_serial
	frames+=1
	elapsed+=delta

func report(path: String) -> Dictionary:
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_csv_line(PackedStringArray(["frame","swing","phase","phase_seconds","clip_seconds","render_delta","tip_x","tip_y","tip_z"]))
	for row in rows:
		var values := PackedStringArray()
		for value in row: values.append(str(value))
		file.store_csv_line(values)
	return {"render_frames":frames,"attack_seconds":elapsed,"max_step_m":maximum_step,"combo_step_m":maximum_combo_step,"offhand_gap_m":maximum_grip_gap}
