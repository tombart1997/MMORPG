class_name EnemyData
extends Resource
@export var id: StringName
@export var display_name: String = "Mossling"
@export_range(1, 25) var level: int = 1
@export_range(1, 5) var tier: int = 1
@export var defense: float = 0.0
@export var aggro_radius: float = 0.0
@export var tint: Color = Color.WHITE
@export var family: StringName = &"mossling"
@export var maximum_health: float = 75
@export var attack: AttackData
@export var visual: PackedScene
@export var visual_scale: float = 1.0
@export var speed: float = 3.2
@export var xp: int = 25
@export var gold_min: int = 6
@export var gold_max: int = 8
@export var drops: DropTable
@export var leader_reward: ItemData
