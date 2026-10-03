class_name EventLog
extends PanelContainer
## Local system/combat history, not a simulated multiplayer chat feed.
var player: ActorBody
var history: Array[Dictionary] = []
var feed: RichTextLabel
var channel: String = "All"

func _ready() -> void:
	theme = PaintedTheme.get_theme()
	position = Vector2(18,-158)
	set_anchors_preset(Control.PRESET_BOTTOM_LEFT,true)
	custom_minimum_size = Vector2(280,140)
	var column := VBoxContainer.new()
	add_child(column)
	var tabs := HBoxContainer.new()
	column.add_child(tabs)
	var group := ButtonGroup.new()
	for title in ["All","System","Combat"]:
		var button := Button.new()
		button.text = title
		button.toggle_mode = true
		button.button_group = group
		button.button_pressed = title == "All"
		button.pressed.connect(func(): channel = title; refresh())
		tabs.add_child(button)
	feed = RichTextLabel.new()
	feed.custom_minimum_size = Vector2(260,86)
	feed.scroll_following = true
	feed.selection_enabled = true
	column.add_child(feed)
	var label := Label.new()
	label.text = "LOCAL LOG    ·    I  Pack    J  Journal    M  Map"
	label.add_theme_font_size_override("font_size",10)
	label.modulate = PaintedTheme.GOLD
	column.add_child(label)
	append("System","Welcome to " + player.map_state.region.display_name + ".")
	player.health.damaged.connect(func(amount,_source): append("Combat","Received %d damage." % amount))
	player.progression.changed.connect(func(): append("System","Level %d · XP %d/%d" % [player.progression.level,player.progression.xp,player.progression.xp_required()]))

func append(kind: String, message: String) -> void:
	if not history.is_empty() and history.back().text == message: return
	history.append({"kind":kind,"text":message})
	if history.size() > 80: history.pop_front()
	refresh()

func refresh() -> void:
	feed.clear()
	for entry in history:
		if channel != "All" and entry.kind != channel: continue
		feed.push_color(Color("bd7861") if entry.kind == "Combat" else Color("9baf8a"))
		feed.add_text("[%s] " % entry.kind)
		feed.pop()
		feed.add_text(entry.text + "\n")
