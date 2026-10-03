class_name WorldNPC
extends Node3D
@export var data: NPCData
var label: Label3D
var model: Node3D

var profession: Label3D
var label_clock: float = 0
var observer: ActorBody

func _ready() -> void:
	assert(data != null and data.id != &"")
	add_to_group("npcs")
	var resident:=TownfolkVisual.new()
	resident.data=data
	add_child(resident)
	model=resident
	label=_nameplate(data.display_name,2.12,19,Color("d4c5a3"))
	profession=_nameplate(String(data.role).capitalize(),1.99,13,Color("a49c83"))
	WorldClickable.attach(self,&"npc")

func _nameplate(text: String, height: float, size: int, color: Color) -> Label3D:
	var plate:=Label3D.new()
	plate.text=text
	plate.position.y=height
	plate.font_size=size
	plate.pixel_size=.005
	plate.modulate=color
	plate.outline_modulate=Color("201812")
	plate.outline_size=4
	plate.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	plate.no_depth_test=false
	plate.visibility_range_end=20
	add_child(plate)
	return plate

func can_interact(player: ActorBody) -> bool:
	if not is_instance_valid(player) or not player.health.is_alive() or player.combat.is_attacking() or (player.skills and player.skills.busy()): return false
	if global_position.distance_to(player.global_position) > data.interaction_range: return false
	var ray := PhysicsRayQueryParameters3D.create(player.global_position + Vector3.UP, global_position + Vector3.UP, 1)
	return get_world_3d().direct_space_state.intersect_ray(ray).is_empty()

func _process(delta: float) -> void:
	if not is_instance_valid(observer):
		var players:=get_tree().get_nodes_in_group("players")
		if not players.is_empty(): observer=players[0]
	if not is_instance_valid(observer): return
	(model as TownfolkVisual).present(delta,observer)
	label_clock-=delta
	if label_clock<=0:
		label_clock=.15
		var distance:=global_position.distance_to(observer.global_position)
		var marker:=observer.quests.marker(data.id) if observer.quests else ""
		var title:=marker+data.display_name
		if label.text!=title: label.text=title
		# Titles recede first; important quest markers keep their useful range.
		label.visible=distance<20 if not marker.is_empty() else distance<16
		profession.visible=distance<9
		var alpha:=clampf((20-distance)/4,0,1) if not marker.is_empty() else clampf((16-distance)/3,0,1)
		label.modulate.a=alpha
		profession.modulate.a=clampf((9-distance)/2,0,1)
	if data.turn_to_player and can_interact(observer):
		var direction:=observer.global_position-global_position
		model.rotation.y=lerp_angle(model.rotation.y,atan2(-direction.x,-direction.z),minf(1,delta*5))
