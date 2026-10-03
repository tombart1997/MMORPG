class_name SkillBar
extends PanelContainer
var player: ActorBody
var buttons: Array[Button] = []
var status: Label
var mount_button: Button
var ornaments: Array[PaintedArt] = []
var active_flames: Array[PaintedArt] = []
var cooldown_labels: Array[Label] = []
func _ready() -> void:
	position = Vector2(-280, -104)
	set_anchors_preset(Control.PRESET_CENTER_BOTTOM, true)
	custom_minimum_size = Vector2(560, 66)
	theme = PaintedTheme.get_theme()
	add_theme_stylebox_override("panel",PaintedTheme.frame(8))
	z_index = 5
	var column := VBoxContainer.new()
	add_child(column)
	status = Label.new()
	status.clip_text = true
	status.custom_minimum_size = Vector2(530, 14)
	status.add_theme_font_size_override("font_size", 12)
	column.add_child(status)
	var groups := HBoxContainer.new()
	groups.add_theme_constant_override("separation",6)
	column.add_child(groups)
	var row := section(groups,"SKILLS")
	for i in player.skills.specialization.skills.size():
		var skill := player.skills.specialization.skills[i]
		var button := Button.new()
		button.custom_minimum_size = Vector2(46, 40)
		button.add_theme_font_size_override("font_size", 12)
		button.autowrap_mode = TextServer.AUTOWRAP_OFF
		button.icon = PaintedTheme.ability(i)
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", 36)
		button.tooltip_text = skill.tooltip()
		button.pressed.connect(func(): player.skills.activate(i))
		row.add_child(button)
		buttons.append(button)
		var key := Label.new()
		key.text = str(i+1)
		key.position = Vector2(3,1)
		key.add_theme_font_size_override("font_size",10)
		key.add_theme_constant_override("outline_size",3)
		key.add_theme_color_override("font_outline_color",Color.BLACK)
		key.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(key)
		var timer := Label.new()
		timer.position = Vector2(4,22)
		timer.add_theme_font_size_override("font_size",11)
		timer.add_theme_constant_override("outline_size",3)
		timer.add_theme_color_override("font_outline_color",Color.BLACK)
		timer.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(timer)
		cooldown_labels.append(timer)
		var fire := PaintedArt.new()
		fire.position = Vector2(-2,-8)
		fire.size = Vector2(48,22)
		button.add_child(fire)
		active_flames.append(fire)
	var consumables := section(groups,"CONSUMABLES")
	for i in 2:
		var slot := ConsumableSlot.new()
		slot.player = player
		slot.slot = i
		consumables.add_child(slot)
	var utility := section(groups,"UTILITY")
	mount_button = Button.new()
	mount_button.custom_minimum_size = Vector2(48,40)
	mount_button.icon = PaintedTheme.inventory_icon(6)
	mount_button.add_theme_constant_override("icon_max_width",25)
	mount_button.add_theme_font_size_override("font_size",12)
	mount_button.pressed.connect(func(): player.mounts.toggle())
	utility.add_child(mount_button)
	for side in [-1,1]:
		var art := PaintedArt.new()
		art.set_as_top_level(true)
		art.mirrored = side < 0
		art.size = Vector2(94,47)
		add_child(art)
		ornaments.append(art)
		art.global_position = global_position + Vector2(-44 if side < 0 else size.x-50,-26)


func section(parent: Control, title: String) -> HBoxContainer:
	var column := VBoxContainer.new()
	parent.add_child(column)
	var label := Label.new()
	label.text = title
	label.add_theme_font_size_override("font_size",9)
	label.add_theme_color_override("font_color",Color("b3a578"))
	column.add_child(label)
	var row := HBoxContainer.new()
	column.add_child(row)
	return row

func _process(_delta: float) -> void:
	for i in ornaments.size(): ornaments[i].global_position = global_position + Vector2(-44 if i == 0 else size.x-50,-26)
	var skills := player.skills
	for i in buttons.size():
		var skill := skills.specialization.skills[i]
		var cooldown := skills.remaining(skill)
		cooldown_labels[i].text = "%.1f" % cooldown if cooldown > 0 else ("AIM" if skills.armed == skill else "")
		active_flames[i].visible = skills.armed == skill or (skills.current != null and skills.current.skill == skill)
		buttons[i].modulate = Color(1, .82, .45) if skills.armed == skill else (Color(.7, .73, .75) if not skills.unavailable(skill).is_empty() else Color.WHITE)
	var opportunity := ""
	if player.statuses.has(&"guard"): opportunity = " | GUARD %.1fs" % player.statuses.entries[&"guard"].remaining
	elif player.statuses.has(&"answer"): opportunity = " | ANSWER %.1fs: Storm or Sunbreaker" % player.statuses.entries[&"answer"].remaining
	if player.statuses.has(&"spirit_edge"): opportunity += " | SPIRIT %.1fs" % player.statuses.entries[&"spirit_edge"].remaining
	if player.statuses.has(&"haste"): opportunity += " | SPEED +80%% %.1fs" % player.statuses.entries[&"haste"].remaining
	status.text = opportunity.trim_prefix(" | ") if not opportunity.is_empty() else skills.feedback
	if status.text.is_empty(): status.text = "TURNWARDEN  ·  1–6 techniques  /  Q · F supplies  /  H mount"

	mount_button.text = "H\n" + ("Ride" if not player.mounts.mounted else "Off")
	mount_button.tooltip_text = "Briarwood horse - H\n" + player.mounts.unavailable() + "\nSpace attacks 35% faster; two consecutive hits knock foes back.\nSkills and conversations dismount. Ownership is permanent."
	mount_button.modulate = Color(.65,.67,.62) if not player.mounts.unavailable().is_empty() else Color.WHITE
	if player.actions.feedback_time > 0 and opportunity.is_empty(): status.text = player.actions.feedback
