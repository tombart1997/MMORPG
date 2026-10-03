class_name WindowChrome
extends Control
## Shared title strip with dragging constrained to the reference canvas.
var window: Control
var drag_offset := Vector2.ZERO
var dragging := false
var collapsed := false
var expanded_size := Vector2.ZERO
var expanded_minimum := Vector2.ZERO
var content_visibility: Dictionary = {}

static func install(target: Control, title: String, close_action: Callable) -> void:
	target.theme = PaintedTheme.get_theme()
	target.add_theme_stylebox_override("panel",PaintedTheme.frame(12))
	var chrome := WindowChrome.new()
	chrome.window = target
	chrome.set_as_top_level(true)
	target.add_child(chrome)
	chrome.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	chrome.offset_top = -25
	chrome.offset_bottom = 0
	var strip := Panel.new()
	strip.add_theme_stylebox_override("panel",PaintedTheme.slot())
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	strip.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	chrome.add_child(strip)
	var label := Label.new()
	label.text = title
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Georgia", "Noto Serif", "serif"])
	label.add_theme_font_override("font",font)
	chrome.add_child(label)
	var close := Button.new()
	close.text = "×"
	close.tooltip_text = "Close [Esc]"
	close.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	close.position = Vector2(-25,1)
	close.size = Vector2(23,23)
	close.pressed.connect(close_action)
	chrome.add_child(close)
	var minimize := Button.new()
	minimize.text = "−"
	minimize.tooltip_text = "Collapse / expand"
	minimize.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	minimize.position = Vector2(-49,1)
	minimize.size = Vector2(23,23)
	minimize.pressed.connect(chrome.toggle_collapsed)
	chrome.add_child(minimize)
	chrome._process(0)

func toggle_collapsed() -> void:
	collapsed = not collapsed
	if collapsed:
		expanded_size = window.size
		expanded_minimum = window.custom_minimum_size
		content_visibility.clear()
		for child in window.get_children():
			if child is Control and child != self:
				content_visibility[child] = child.visible
				child.hide()
		window.custom_minimum_size.y = 0
		window.size.y = 24
	else:
		for child in content_visibility:
			if is_instance_valid(child): child.visible = content_visibility[child]
		window.custom_minimum_size = expanded_minimum
		window.size = expanded_size

func _process(_delta: float) -> void:
	global_position = window.global_position + Vector2(0,-25)
	size = Vector2(window.size.x,25)

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and not event.pressed: dragging = false

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		dragging = event.pressed
		drag_offset = get_global_mouse_position() - window.global_position
		accept_event()
	if event is InputEventMouseMotion and dragging:
		var desired: Vector2 = window.global_position + event.relative
		window.global_position = desired.clamp(Vector2(6,30), (get_viewport_rect().size-window.size-Vector2(6,6)).max(Vector2(6,30)))
		accept_event()
