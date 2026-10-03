class_name TownfolkVisual
extends Node3D
## Presentation only. Dialogue, collision and world interaction stay on WorldNPC.
const KIT = preload("res://assets/characters/townfolk_kit.glb")
const PAINT = preload("res://assets/characters/townfolk.gdshader")
static var materials: Dictionary = {}
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
	var kit:=KIT.instantiate() as Node3D
	add_child(kit)
	skeleton=kit.find_children("*","Skeleton3D",true,false)[0]
	animation=kit.find_children("*","AnimationPlayer",true,false)[0]
	animation.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var face:=appearance.body if appearance.face=="Body default" else appearance.face
	visible_modules=["Body_"+appearance.body,"Head_"+face,"Clothes_"+appearance.clothing,"Hair_"+appearance.hair]
	for accessory in appearance.accessories: visible_modules.append("Gear_"+accessory)
	var cloth:=appearance.cloth_override if appearance.cloth_override.a>0 else data.clothing_color.lightened(.12)
	var key:=str(cloth)+str(appearance.skin_tint)
	if not materials.has(key):
		var mat:=ShaderMaterial.new()
		mat.shader=PAINT
		mat.set_shader_parameter("painted_atlas",preload("res://assets/characters/townfolk_atlas.png"))
		mat.set_shader_parameter("cloth_tint",cloth)
		mat.set_shader_parameter("skin_tint",appearance.skin_tint)
		materials[key]=mat
	for part: MeshInstance3D in kit.find_children("*","MeshInstance3D",true,false):
		if not visible_modules.has(String(part.name)):
			part.get_parent().remove_child(part)
			part.queue_free()
		else:
			part.material_override=materials[key]
			part.visibility_range_end=65
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
