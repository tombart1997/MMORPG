class_name ItemData
extends Resource
## Immutable authored definition; runtime stacks reference its stable ID.
@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export_enum("weapon", "armor", "consumable", "material", "miscellaneous") var item_type: String = "miscellaneous"
@export var icon: Texture2D
@export var color: Color = Color.WHITE
@export var stackable: bool = true
@export_range(1, 999) var maximum_stack: int = 20
@export var value: int = 1
@export var equipment_slot: StringName
@export var modifiers: Dictionary = {}
@export var visual: PackedScene
@export var weapon_family: StringName = &"sword"
@export var attacks: Array[AttackData] = []
@export var required_level: int = 1
@export var rarity: StringName = &"common"
@export var upgrade_profile: UpgradeProfile
@export var properties: Dictionary = {}
@export var healing: float = 0.0

func stack_limit() -> int:
	return maximum_stack if stackable else 1

func tooltip() -> String:
	var result := display_name + "\n" + description + "\n" + item_type.capitalize()
	if equipment_slot != &"": result += " / " + String(equipment_slot).capitalize()
	for key in modifiers:
		result += "\n%+.1f %s" % [float(modifiers[key]), String(key).replace("_", " ").capitalize()]
	if healing > 0: result += "\nRestores %.1f HP" % healing
	return result + "\nLevel %d | Value %d gold" % [required_level, value]
