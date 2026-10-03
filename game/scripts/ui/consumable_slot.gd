class_name ConsumableSlot
extends Button
var player: ActorBody
var slot: int = 0

func _ready() -> void:
	custom_minimum_size = Vector2(48,40)
	add_theme_font_size_override("font_size",12)
	add_theme_constant_override("icon_max_width",25)
	pressed.connect(func(): player.actions.activate(slot))

func _process(_delta: float) -> void:
	var id := player.actions.slots[slot]
	var item := ItemCatalog.get_item(id) if id != &"" else null
	icon = PaintedTheme.painted_icon(item.icon) if item else null
	var reason := player.actions.unavailable(slot)
	text = "%s  %s\n%s" % ["Q" if slot == 0 else "F",str(player.inventory.count(id)) if item else "—","%.1f" % player.actions.cooldown if player.actions.cooldown > 0 else ""]
	tooltip_text = (item.tooltip()+"\n" if item else "") + reason + "\nDrag from inventory to assign. Right-click to clear."
	modulate = Color(.57,.59,.56) if not reason.is_empty() else Color.WHITE
	if player.actions.feedback_time > 3.6 and player.actions.cooldown > 2.6: modulate = Color(1,.8,.45)

func _can_drop_data(_position: Vector2, data: Variant) -> bool:
	return player.actions.can_drop(data)

func _drop_data(_position: Vector2, data: Variant) -> void:
	if player.actions.can_drop(data): player.actions.assign(slot,data.stack.id)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
		player.actions.assign(slot,&"")
		accept_event()
