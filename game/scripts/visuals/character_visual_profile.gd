class_name CharacterVisualProfile
extends Resource
## Imported asset and rig contract. Different rigs can remap sockets without changing gameplay.
@export var model: PackedScene
@export var creature: bool = false
@export var run_reference_speed: float = 5.5
@export var label_height: float = 2.05
@export var weapon: PackedScene
@export var armor: PackedScene
@export var socket_bones: Dictionary = {
	&"WeaponSocket": &"Hand.R", &"OffhandSocket": &"Hand.L",
	&"ArmorSocket": &"Chest", &"HeadSocket": &"Head",
	&"RightBootSocket": &"Foot.R", &"LeftBootSocket": &"Foot.L"}
@export var reaction_bones: Array[StringName] = [&"Chest", &"Head"]
@export var socket_offsets: Dictionary = {
	&"WeaponSocket": Vector3(0, -0.06, -0.035),
	&"OffhandSocket": Vector3(0, -0.06, -0.035)}
@export_range(0.0, 1.0) var active_marker: float = 0.30
@export_range(0.0, 1.0) var recovery_marker: float = 0.55
