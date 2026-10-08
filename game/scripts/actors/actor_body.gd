class_name ActorBody
extends CharacterBody3D
## Gameplay composition only; model, bones, animations and equipment live in visual scenes.
var health: HealthComponent
var combat: MeleeCombat
var visual: ActorVisual
var base_color := Color(0.2, 0.65, 0.9)
var maximum_health: float = 100.0
var weapon: AttackData
var attack_sequence: Array[AttackData] = []
var visual_scene: PackedScene
var faction: StringName = &"players"
var opponents: StringName = &"enemies"
var title: String = "Player"
var enemy_definition: EnemyData
var progression: PlayerProgression
var inventory: PlayerInventory
var equipment: PlayerEquipment
var stats: CharacterStats
var ui_open: bool = false
var ui_session: UISession
var navigation: PlayerNavigation
var world_interaction: WorldInteraction
var quests: PlayerQuests
var skills: PlayerSkills
var statuses: CombatStatuses
var actions: PlayerActions
var mounts: PlayerMount
var map_state: PlayerMap
var body_collider: CollisionShape3D
var farming: FarmingState
var visual_elapsed: float = 0
var simulation_interval: float = 0.0

func _ready() -> void:
	add_to_group(faction)
	collision_layer = 2
	collision_mask = 11
	var collider := CollisionShape3D.new()
	body_collider = collider
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.34
	capsule.height = 1.8
	collider.shape = capsule
	collider.position.y = 0.9
	add_child(collider)
	health = HealthComponent.new()
	health.maximum = maximum_health
	add_child(health)
	statuses = CombatStatuses.new()
	add_child(statuses)
	combat = MeleeCombat.new()
	combat.attack = weapon
	combat.sequence = attack_sequence
	combat.target_group = opponents
	add_child(combat)
	if visual_scene == null:
		visual_scene = load("res://scenes/visuals/humanoid.tscn")
	visual = visual_scene.instantiate() as ActorVisual
	add_child(visual)
	add_child(StatusVisual.new())
	health.damaged.connect(_on_damaged)
	health.died.connect(_on_died)

func _process(delta: float) -> void:
	if not RuntimeCosts.enabled:
		_profiled__process(delta)
		return
	var started:=Time.get_ticks_usec()
	_profiled__process(delta)
	RuntimeCosts.record(&"presentation",started)

func _profiled__process(delta: float) -> void:
	visual_elapsed += delta
	if simulation_interval > 0 and visual_elapsed < simulation_interval and not combat.is_attacking(): return
	if faction == &"enemies":
		var camera := get_viewport().get_camera_3d()
		# Peripheral skeletons need fewer samples; combat timing, movement and
		# collisions continue at their normal physics rate. Close attacks stay smooth.
		if camera and camera.global_position.distance_squared_to(global_position)>400 and visual_elapsed<1.0/30.0:return
	# Nearby action retains full-rate telegraphs. Distant idle skeletons tick at 5 Hz.
	if not has_meta("full_detail") and faction == &"enemies" and health.is_alive() and not combat.is_attacking():
		var camera := get_viewport().get_camera_3d()
		if camera and camera.global_position.distance_squared_to(global_position) > 900 and visual_elapsed < 0.2: return
	visual.present(velocity, combat, health, title, visual_elapsed)
	visual_elapsed = 0

func _on_damaged(amount: float, source: Node3D) -> void:
	IronfieldAudio.instance.play_at(&"metal" if enemy_definition and enemy_definition.family == &"stonekin" else &"hit",global_position+Vector3.UP*.8,-3)
	visual.react_to_hit()
	DamageCaption.show_hit(self, amount, source)

func _on_died(_source: Node3D) -> void:
	combat.cancel()
	statuses.clear()
	if skills: skills.cancel_transient()
	collision_layer = 0
	collision_mask = 1
	for child in get_children():
		if child is WorldClickable: child.set_deferred("collision_layer", 0)
