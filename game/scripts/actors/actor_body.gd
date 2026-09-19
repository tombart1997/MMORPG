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
var progression: PlayerProgression
var inventory: PlayerInventory

func _ready() -> void:
	add_to_group(faction)
	collision_layer = 2
	collision_mask = 3
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.34
	capsule.height = 1.8
	collider.shape = capsule
	collider.position.y = 0.9
	add_child(collider)
	health = HealthComponent.new()
	health.maximum = maximum_health
	add_child(health)
	combat = MeleeCombat.new()
	combat.attack = weapon
	combat.sequence = attack_sequence
	combat.target_group = opponents
	add_child(combat)
	if visual_scene == null:
		visual_scene = load("res://scenes/visuals/humanoid.tscn")
	visual = visual_scene.instantiate() as ActorVisual
	add_child(visual)
	health.damaged.connect(_on_damaged)
	health.died.connect(_on_died)

func _process(delta: float) -> void:
	visual.present(velocity, combat, health, title, delta)

func _on_damaged(_amount: float, _source: Node3D) -> void:
	visual.react_to_hit()

func _on_died(_source: Node3D) -> void:
	combat.cancel()
	collision_layer = 0
	collision_mask = 1
