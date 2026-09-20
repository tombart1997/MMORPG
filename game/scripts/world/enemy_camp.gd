class_name EnemyCamp
extends Node3D
## Encounter lifetime and rewards. Dead actors remain until the whole group respawns.
@export var camp_name: String = "Mossling camp"
@export var count: int = 4
@export var respawn_delay: float = 18.0
var remaining: float = -1.0
var pack: AggroGroup
var generation: int = 0
@export var enemy_data: EnemyData
@export var leash_distance: float = 13.0
@export var drop_table: DropTable = preload("res://data/drops/mossling.tres")
var rng := RandomNumberGenerator.new()
const ENEMY_VISUAL = preload("res://scenes/visuals/mossling.tscn")
const CLAW = preload("res://data/attacks/enemy_claw.tres")
@export var leader_reward: ItemData = preload("res://data/items/briarsteel_edge.tres")

func _ready() -> void:
	if enemy_data:
		drop_table = enemy_data.drops
		leader_reward = enemy_data.leader_reward
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
	if SafeArea.protects(self): return
	for i in range(count):
		var enemy := ActorBody.new()
		enemy.title = enemy_data.display_name if enemy_data else "Mossling"
		enemy.position = Vector3((i % 2) * 1.5 - 0.75, 0.1, -floorf(i / 2.0) * 1.5)
		enemy.rotation.y = PI
		enemy.weapon = enemy_data.attack if enemy_data else CLAW
		enemy.visual_scene = enemy_data.visual if enemy_data else ENEMY_VISUAL
		enemy.maximum_health = enemy_data.maximum_health if enemy_data else 75
		enemy.faction = &"enemies"
		enemy.opponents = &"players"
		add_child(enemy)
		pack.register(enemy)
		WorldClickable.attach(enemy, &"enemy")
		if enemy_data:
			enemy.visual.scale = Vector3.ONE * enemy_data.visual_scale
		var brain := EnemyBrain.new()
		brain.pack = pack
		if enemy_data: brain.speed = enemy_data.speed
		enemy.add_child(brain)
		enemy.health.died.connect(_reward.bind(enemy, i))

func _reward(source: Node3D, enemy: ActorBody, index: int) -> void:
	if source is ActorBody and source.progression:
		source.progression.kills += 1
		source.progression.award_xp(enemy_data.xp if enemy_data else 25)
		if source.quests: source.quests.record(&"kill", enemy_data.id if enemy_data else &"grown")
		var drops: Array[ItemStack] = drop_table.roll(rng)
		if leader_reward and index == 0: drops.append(ItemStack.new(leader_reward.id))
		var gold := LootPickup.new()
		gold.coins = rng.randi_range(enemy_data.gold_min, enemy_data.gold_max) if enemy_data else 4 + index
		get_parent().add_child(gold)
		gold.global_position = enemy.global_position + Vector3(0.7, 0, 0.4)
		for i in drops.size():
			var drop := LootPickup.new()
			drop.item = drops[i].definition()
			drop.quantity = drops[i].quantity
			get_parent().add_child(drop)
			var angle := i * 2.4 + index
			drop.global_position = enemy.global_position + Vector3(sin(angle), 0, cos(angle)) * (1.0 + i * 0.35)
			drop.global_position.y = ZoneTerrain.height_at(drop.global_position.x, drop.global_position.z)

	if pack.living_count() == 0:
		remaining = respawn_delay

func _physics_process(delta: float) -> void:
	if pack == null: return
	if pack.target != null:
		if not pack.has_target() or pack.target.global_position.distance_to(global_position) > leash_distance:
			pack.disengage()
		else:
			for member in pack.members:
				if member.health.is_alive() and (member.global_position.distance_to(global_position) > leash_distance or SafeArea.protects(member)):
					pack.disengage()
					break
	if remaining < 0:
		return
	remaining = maxf(0, remaining - delta)
	if remaining == 0:
		# Do not materialize a pack on top of a player collecting its drops.
		for player in get_tree().get_nodes_in_group("players"):
			if player.global_position.distance_to(global_position) < 6.0:
				return
		spawn_group()
