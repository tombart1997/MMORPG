class_name WorldMapPanel
extends PanelContainer
var player: ActorBody

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	position = Vector2(-380,-290)
	custom_minimum_size = Vector2(760,580)
	z_index = 10
	var column := VBoxContainer.new()
	add_child(column)
	var title := Label.new()
	title.text = "  " + player.map_state.region.display_name.to_upper()
	title.add_theme_font_size_override("font_size",22)
	column.add_child(title)
	var canvas := MapCanvas.new()
	canvas.player = player
	canvas.full = true
	canvas.custom_minimum_size = Vector2(740,470)
	column.add_child(canvas)
	var legend := Label.new()
	legend.text = "  S Smith · $ Merchant · ! Quest · ? Return · ◇ Known landmark\n  Unmarked country must be explored. Roads show direction, not safe passage."
	legend.add_theme_font_size_override("font_size",14)
	column.add_child(legend)
	var close := Button.new()
	close.text = "Close [M / Esc]"
	close.pressed.connect(func(): player.ui_session.close())
	column.add_child(close)
	hide()
