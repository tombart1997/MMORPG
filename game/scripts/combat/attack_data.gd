class_name AttackData
extends Resource
## Timings are seconds, distances are meters, cone angle is the full width.
@export var display_name: String = "Sword sweep"
@export var animation_clip: StringName = &"attack_01"
@export var damage: float = 25.0
@export var windup: float = 0.18
@export var active: float = 0.16
@export var recovery: float = 0.30
@export var reach: float = 2.8
@export var cone_degrees: float = 115.0
@export var height_tolerance: float = 1.5
@export_range(0.0, 1.0) var recovery_movement_unlock: float = 1.0
@export var lunge_distance: float = 0.35
@export var lunge_start: float = 0.12
@export var lunge_duration: float = 0.22
