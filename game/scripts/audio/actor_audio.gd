extends Node
## Player cadence and blade movement are sampled after visual posing.
var actor: ActorBody
var previous_point := Vector3.ZERO
var distance := 0.0
var swing_serial := -1

func _ready() -> void:
	process_priority = 60
	actor = get_parent()
	previous_point = actor.global_position
	if preload("res://scripts/audio/monster_voice.gd").supports(actor):
		actor.add_child(preload("res://scripts/audio/monster_voice.gd").new())

func _process(_delta: float) -> void:
	var travel := actor.global_position.distance_to(previous_point)
	previous_point = actor.global_position
	if not actor.health.is_alive(): return
	if actor.combat.phase == MeleeCombat.Phase.ACTIVE and swing_serial != actor.combat.swing_serial and not preload("res://scripts/audio/monster_voice.gd").supports(actor):
		swing_serial = actor.combat.swing_serial
		IronfieldAudio.instance.play_at(&"swing",actor.visual.weapon_marker_world(&"Tip"),-2)
	if actor.mounts and actor.mounts.mounted or actor.ui_open or not actor.is_on_floor(): distance = 0;return
	if travel > 2.5: distance = 0;return
	distance += travel
	if distance > 1.45:
		distance -= 1.45
		IronfieldAudio.instance.play_at(&"step",actor.global_position,-7)
