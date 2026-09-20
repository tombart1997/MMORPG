class_name NPCData
extends Resource
@export var id: StringName
@export var display_name: String
@export var role: StringName = &"resident"
@export var interaction_range: float = 2.8
@export var turn_to_player: bool = true
@export var clothing_color: Color = Color(0.3, 0.4, 0.5)
@export var pages: Array[DialoguePage] = []
@export var shop: ShopData
