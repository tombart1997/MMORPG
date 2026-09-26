class_name SkillBar
extends PanelContainer
var player: ActorBody
var buttons: Array[Button] = []
var status: Label
var mount_button: Button
func _ready() -> void:
	position = Vector2(-305, -110)
	set_anchors_preset(Control.PRESET_CENTER_BOTTOM, true)
	custom_minimum_size = Vector2(610, 94)
	var style := StyleBoxFlat.new()
	style.bg_color=Color(.025,.035,.032,.85)
	style.border_color=Color(.43,.36,.23,.8)
	style.set_border_width_all(1)
	style.content_margin_left=10
	style.content_margin_right=10
	style.content_margin_top=5
	style.content_margin_bottom=7
	add_theme_stylebox_override("panel",style)
	z_index = 5
	var column := VBoxContainer.new()
	add_child(column)
	status = Label.new()
	status.clip_text = true
	status.custom_minimum_size = Vector2(585, 18)
	status.add_theme_font_size_override("font_size", 12)
	column.add_child(status)
	var groups := HBoxContainer.new()
	groups.add_theme_constant_override("separation",12)
	column.add_child(groups)
	var row := section(groups,"SKILLS")
	for i in player.skills.specialization.skills.size():
		var skill := player.skills.specialization.skills[i]
		var button := Button.new()
		button.custom_minimum_size = Vector2(54, 48)
		button.add_theme_font_size_override("font_size", 12)
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.icon = skill.icon
		button.add_theme_constant_override("icon_max_width", 27)
		button.tooltip_text = skill.tooltip()
		button.pressed.connect(func(): player.skills.activate(i))
		row.add_child(button)
		buttons.append(button)
	var consumables := section(groups,"CONSUMABLES")
	for i in 2:
		var slot := ConsumableSlot.new()
		slot.player = player
		slot.slot = i
		consumables.add_child(slot)
	var utility := section(groups,"UTILITY")
	mount_button = Button.new()
	mount_button.custom_minimum_size = Vector2(68,48)
	mount_button.icon = preload("res://assets/icons/horse.svg")
	mount_button.add_theme_constant_override("icon_max_width",25)
	mount_button.add_theme_font_size_override("font_size",12)
	mount_button.pressed.connect(func(): player.mounts.toggle())
	utility.add_child(mount_button)

func section(parent: Control, title: String) -> HBoxContainer:
	var column := VBoxContainer.new()
	parent.add_child(column)
	var label := Label.new()
	label.text = title
	label.add_theme_font_size_override("font_size",10)
	label.add_theme_color_override("font_color",Color("b3a578"))
	column.add_child(label)
	var row := HBoxContainer.new()
	column.add_child(row)
	return row

func _process(_delta: float) -> void:
	var skills := player.skills
	for i in buttons.size():
		var skill := skills.specialization.skills[i]
		var cooldown := skills.remaining(skill)
		buttons[i].text = "%d\n%s" % [i + 1, "%.1f" % cooldown if cooldown > 0 else ("AIM" if skills.armed == skill else "")]
		buttons[i].modulate = Color(1, .82, .45) if skills.armed == skill else (Color(.7, .73, .75) if not skills.unavailable(skill).is_empty() else Color.WHITE)
	var opportunity := ""
	if player.statuses.has(&"guard"): opportunity = " | GUARD %.1fs" % player.statuses.entries[&"guard"].remaining
	elif player.statuses.has(&"answer"): opportunity = " | ANSWER %.1fs: Sweep or Return" % player.statuses.entries[&"answer"].remaining
	status.text = opportunity.trim_prefix(" | ") if not opportunity.is_empty() else skills.feedback

	mount_button.text = "H\n" + ("Ride" if not player.mounts.mounted else "Off")
	mount_button.tooltip_text = "Briarwood horse ? H\n" + player.mounts.unavailable() + "\nAttacks, hostile hits and conversations dismount.\nOwnership is permanent; loading returns on foot."
	mount_button.modulate = Color(.65,.67,.62) if not player.mounts.unavailable().is_empty() else Color.WHITE
	if player.actions.feedback_time > 0: status.text = player.actions.feedback
