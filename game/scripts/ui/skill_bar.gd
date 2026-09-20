class_name SkillBar
extends PanelContainer
var player: ActorBody
var buttons: Array[Button] = []
var status: Label
func _ready() -> void:
	position = Vector2(410, -166)
	set_anchors_preset(Control.PRESET_BOTTOM_LEFT, true)
	custom_minimum_size = Vector2(620, 150)
	z_index = 5
	var column := VBoxContainer.new()
	add_child(column)
	status = Label.new()
	status.clip_text = true
	status.custom_minimum_size = Vector2(580, 38)
	status.add_theme_font_size_override("font_size", 14)
	column.add_child(status)
	var row := HBoxContainer.new()
	column.add_child(row)
	for i in player.skills.specialization.skills.size():
		var skill := player.skills.specialization.skills[i]
		var button := Button.new()
		button.custom_minimum_size = Vector2(92, 66)
		button.add_theme_font_size_override("font_size", 12)
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.icon = skill.icon
		button.add_theme_constant_override("icon_max_width", 24)
		button.tooltip_text = skill.tooltip()
		button.pressed.connect(func(): player.skills.activate(i))
		row.add_child(button)
		buttons.append(button)
func _process(_delta: float) -> void:
	var skills := player.skills
	for i in buttons.size():
		var skill := skills.specialization.skills[i]
		var cooldown := skills.remaining(skill)
		buttons[i].text = "%d  %s\n%s" % [i + 1, skill.display_name, "%.1fs" % cooldown if cooldown > 0 else ("PLACE" if skills.armed == skill else "Ready")]
		buttons[i].modulate = Color(1, .82, .45) if skills.armed == skill else (Color(.7, .73, .75) if not skills.unavailable(skill).is_empty() else Color.WHITE)
	var opportunity := ""
	if player.statuses.has(&"guard"): opportunity = " | GUARD %.1fs" % player.statuses.entries[&"guard"].remaining
	elif player.statuses.has(&"answer"): opportunity = " | ANSWER %.1fs: Sweep or Return" % player.statuses.entries[&"answer"].remaining
	status.text = "TURNWARDEN" + opportunity + "\n" + skills.feedback
