class_name SkillData
extends Resource
@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export_enum("selected", "facing", "self", "ground", "direction") var targeting: String = "selected"
@export_enum("single", "arc", "circle", "self", "none") var shape: String = "single"
@export var reach: float = 2.8
@export var radius: float = 2.8
@export var angle: float = 85
@export var windup: float = 0.28
@export var recovery: float = 0.3
@export var cooldown: float = 5
@export var animation: StringName = &"attack_01"
@export var color: Color = Color(0.95, 0.65, 0.25)
@export var icon: Texture2D
@export var requirement_text: String
@export var consumes_answer: bool = false
@export var effects: Array[SkillEffect] = []
@export var maximum_rank: int = 1
@export var rank_scaling: float = 0.05
func tooltip() -> String:
	var result := "%s\n%s\nRange %.1fm | Windup %.2fs | Cooldown %.0fs" % [display_name, description, reach, windup, cooldown]
	if not requirement_text.is_empty(): result += "\n" + requirement_text
	if targeting in ["ground", "direction"]: result += "\nClick ground to place; Esc cancels."
	return result
