class_name EnemyCamp
extends Node3D
## Encounter lifetime and rewards. Dead actors remain until the whole group respawns.
@export var camp_name: String = "Mossling camp"
@export var count: int = 4
@export var respawn_delay: float = 18.0
var remaining: float = -1.0
var pack: AggroGroup
var generation: int = 0
const ENEMY_VISUAL = preload("res://scenes/visuals/mossling.tscn")
const CLAW = preload("res://data/attacks/enemy_claw.tres")
const SHARD = preload("res://data/items/moss_shard.tres")
const TONIC = preload("res://data/items/field_tonic.tres")

func _ready() -> void:
	spawn_group()

func spawn_group() -> void:
	if pack:
		for member in pack.members:
			if is_instance_valid(member):
				remove_child(member)
				member.queue_free()
		remove_child(pack)
		pack.queue_free()
	pack = AggroGroup.new()
	add_child(pack)
	generation += 1
	remaining = -1
	for i in range(count):
		var enemy := ActorBody.new()
		enemy.title = "Mossling"
		enemy.position = Vector3((i % 2) * 1.5 - 0.75, 0.1, -floorf(i / 2.0) * 1.5)
		enemy.rotation.y = PI
		enemy.weapon = CLAW
		enemy.visual_scene = ENEMY_VISUAL
		enemy.maximum_health = 75
		enemy.faction = &"enemies"
		enemy.opponents = &"players"
		add_child(enemy)
		pack.register(enemy)
		var brain := EnemyBrain.new()
		brain.pack = pack
		enemy.add_child(brain)
		enemy.health.died.connect(_reward.bind(enemy, i))

func _reward(source: Node3D, enemy: ActorBody, index: int) -> void:
	if source is ActorBody and source.progression:
		source.progression.kills += 1
		source.progression.award_xp(25)
		var drop := LootPickup.new()
		drop.coins = 4 + index
		drop.item = TONIC if index % 3 == 0 else SHARD
		get_parent().add_child(drop)
		drop.global_position = enemy.global_position
	if pack.living_count() == 0:
		remaining = respawn_delay

func _physics_process(delta: float) -> void:
	if remaining < 0:
		return
	remaining = maxf(0, remaining - delta)
	if remaining == 0:
		# Do not materialize a pack on top of a player collecting its drops.
		for player in get_tree().get_nodes_in_group("players"):
			if player.global_position.distance_to(global_position) < 6.0:
				return
		spawn_group()
