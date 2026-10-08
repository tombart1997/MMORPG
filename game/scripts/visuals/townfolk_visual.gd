class_name TownfolkVisual
extends Node3D
## Presentation only. Dialogue, collision and world interaction stay on WorldNPC.
const KIT = preload("res://assets/generated/npcs/smith.glb")
var data: NPCData
var appearance: NPCAppearance
var skeleton: Skeleton3D
var animation: AnimationPlayer
var clock: float = 0
var elapsed: float = 0
var visible_modules: Array[String] = []
var observer: ActorBody
var sockets: Dictionary = {}

func _ready() -> void:
	appearance=NPCAppearance.for_resident(data)
	scale=appearance.stature
	clock=float(data.id.hash()%997)*.013
	var reconstructed:=ForgeModelCatalogue.scene_for("npcs",data.id)
	var kit: Node3D=ReviewedModels.resolve(reconstructed if reconstructed else KIT).instantiate() as Node3D
	add_child(kit)
	skeleton=kit.find_children("*","Skeleton3D",true,false)[0]
	animation=kit.find_children("*","AnimationPlayer",true,false)[0]
	animation.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	visible_modules.clear()
	for part: MeshInstance3D in kit.find_children("*","MeshInstance3D",true,false):
		part.visibility_range_end=65
		visible_modules.append(String(part.name))
	animation.play(appearance.idle)
	animation.seek(fposmod(clock,animation.current_animation_length),true)
	equip_visual(&"WeaponSocket",appearance.weapon)
	equip_visual(&"OffhandSocket",appearance.offhand)

func equip_visual(slot: StringName, scene: PackedScene) -> void:
	if not sockets.has(slot):
		if not scene: return
		var bone: StringName=&"Hand.R" if slot==&"WeaponSocket" else &"Hand.L"
		var index:=skeleton.find_bone(bone)
		var attachment:=BoneAttachment3D.new()
		attachment.bone_name=bone
		skeleton.add_child(attachment)
		var socket:=Node3D.new()
		socket.name=slot
		socket.basis=skeleton.get_bone_global_rest(index).basis.inverse()
		socket.position=socket.basis*Vector3(0,-.06,-.035)
		attachment.add_child(socket)
		sockets[slot]=socket
	var socket: Node3D=sockets[slot]
	var previous:=socket.get_node_or_null("Equipment")
	if previous:
		socket.remove_child(previous)
		previous.queue_free()
	if scene:
		var equipment:=scene.instantiate()
		equipment.name="Equipment"
		socket.add_child(equipment)

func present(delta: float, player: ActorBody) -> void:
	observer=player
	clock+=delta
	elapsed+=delta
	var distance:=global_position.distance_to(player.global_position) if is_instance_valid(player) else 0.0
	var interval:=.05 if distance<16 else .2
	if distance>65 or elapsed<interval: return
	elapsed=0
	animation.seek(fposmod(clock,animation.current_animation_length),true)
