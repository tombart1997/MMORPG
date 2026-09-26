class_name FractureData
extends Resource
@export var id: StringName
@export var display_name: String = "Briarwake Fracture"
@export var maximum_health: float = 950
@export var waves: Array[FractureWave] = []
@export var rewards: DropTable
@export var gold_min: int = 28
@export var gold_max: int = 42
@export var xp: int = 100
@export var respawn_seconds: float = 180
@export var abandon_seconds: float = 12
@export var leash_distance: float = 22
@export var spawn_radius: float = 7
@export var population_cap: int = 24
