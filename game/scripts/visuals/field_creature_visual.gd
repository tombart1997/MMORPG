extends ActorVisual
## Authored Chinese fantasy creatures. EnemyData continues to own every gameplay value.
const SPECIES := {
	&"wolf": preload("res://assets/generated/mobs/meadow_wolf.glb"),
	&"boar": preload("res://assets/generated/mobs/bristle_boar.glb"),
	&"spider": preload("res://assets/generated/mobs/reed_spider.glb"),
	&"stonekin": preload("res://assets/generated/mobs/cairn_sentinel.glb"),
	&"wisp": preload("res://assets/generated/mobs/grave_wisp.glb")
}
static var profiles: Dictionary = {}
var family: StringName = &"wolf"

func _ready() -> void:
	# EnemyCamp applies its definition immediately after adding the actor to the tree.
	creature = true

func apply_variant(data: EnemyData) -> void:
	family = data.family if SPECIES.has(data.family) else &"wolf"
	var reconstructed := ForgeModelCatalogue.scene_for("mobs",data.id)
	var identity: StringName=data.id if reconstructed else family
	if not profiles.has(identity):
		var authored := CharacterVisualProfile.new()
		authored.model = reconstructed if reconstructed else SPECIES[family]
		authored.preserve_authored_materials=reconstructed!=null
		authored.creature = true
		authored.socket_bones = {}
		authored.socket_offsets = {}
		authored.reaction_bones.assign([&"Chest", &"Head"])
		authored.run_reference_speed = 3.2
		authored.label_height = 1.3 if family == &"spider" else 2.0 if family == &"stonekin" else 1.8
		profiles[identity] = authored
	if model:
		remove_child(model)
		model.queue_free()
		remove_child(label)
		label.queue_free()
		previous_key = ""
	profile = profiles[identity]
	super._ready()
	# Stable individual proportions and pose phase; no actor/collider/stat changes.
	var individual := get_parent().get_index()
	var variation := float((individual*37)%11)/10.0
	model.scale = Vector3(lerpf(.95,1.06,variation),lerpf(.97,1.04,variation),lerpf(.96,1.07,variation))
	locomotion_time = variation*1.7
	var crowns := model.find_children("EliteCrown*", "MeshInstance3D", true, false)
	for crown: MeshInstance3D in crowns: crown.visible = data.tier >= 3
	label.modulate = [Color.WHITE, Color("d1d8c1"), Color("c8d6c9"), Color("cba7ee"), Color("eaa05d"), Color("f07165")][clampi(data.tier, 0, 5)]
	if not reconstructed:CreatureMaterials.apply(model,data,individual)
