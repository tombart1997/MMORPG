class_name FractureWave
extends Resource
@export_range(0, 1) var health_fraction: float = 1.0
@export var enemy: EnemyData
@export_range(1, 24) var count: int = 3
@export var warning_seconds: float = 1.2
