class_name InventoryPanel
extends PanelContainer
## Presentation and commands only. Inventory/equipment retain authority.
var player: ActorBody
var zone: Node3D
var bag_buttons: Array[Button] = []
var gear_buttons: Dictionary = {}
var details: Label
var character: Label
var title_label: Label
var action: Button
var discard: Button
var discard_armed: bool = false
var selected: int = -1
var selected_gear: StringName = &""

func _ready() -> void:
	position = Vector2(340, 20)
	z_index = 10
	theme = Theme.new()
	var tooltip_style := StyleBoxFlat.new()
	tooltip_style.bg_color = Color(0.035, 0.045, 0.04, 1)
	tooltip_style.border_color = Color(0.58, 0.47, 0.27)
	tooltip_style.set_border_width_all(1)
	tooltip_style.content_margin_left = 10
	tooltip_style.content_margin_right = 10
	tooltip_style.content_margin_top = 8
	tooltip_style.content_margin_bottom = 8
	theme.set_stylebox("panel", "TooltipPanel", tooltip_style)
	theme.set_color("font_color", "TooltipLabel", Color(0.95, 0.91, 0.79))
	custom_minimum_size = Vector2(900, 550)
	var theme_style := StyleBoxFlat.new()
	theme_style.bg_color = Color(0.055, 0.075, 0.075, 0.98)
	theme_style.border_color = Color(0.58, 0.47, 0.27)
	theme_style.set_border_width_all(2)
	theme_style.content_margin_left = 18
	theme_style.content_margin_right = 18
	theme_style.content_margin_top = 16
	theme_style.content_margin_bottom = 16
	add_theme_stylebox_override("panel", theme_style)
	theme.set_stylebox("panel", "PanelContainer", theme_style)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	add_child(column)
	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 22)
	column.add_child(title_label)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 18)
	column.add_child(row)
	var equipment_column := VBoxContainer.new()
	equipment_column.custom_minimum_size.x = 200
	row.add_child(equipment_column)
	for slot in PlayerEquipment.SLOT_NAMES:
		var button := ItemSlot.new()
		button.player = player
		button.equipment_slot = slot
		button.custom_minimum_size = Vector2(200, 34)
		button.pressed.connect(select_gear.bind(slot))
		equipment_column.add_child(button)
		gear_buttons[slot] = button
	character = Label.new()
	character.add_theme_font_size_override("font_size", 16)
	equipment_column.add_child(character)
	var grid := GridContainer.new()
	grid.columns = 6
	grid.add_theme_constant_override("h_separation", 5)
	grid.add_theme_constant_override("v_separation", 5)
	row.add_child(grid)
	for i in PlayerInventory.CAPACITY:
		var button := ItemSlot.new()
		button.player = player
		button.bag_index = i
		button.custom_minimum_size = Vector2(100, 76)
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", 24)
		button.add_theme_font_size_override("font_size", 13)
		button.pressed.connect(select_slot.bind(i))
		grid.add_child(button)
		bag_buttons.append(button)
	details = Label.new()
	details.custom_minimum_size = Vector2(850, 118)
	details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	details.add_theme_font_size_override("font_size", 15)
	column.add_child(details)
	var actions := HBoxContainer.new()
	column.add_child(actions)
	action = Button.new()
	action.custom_minimum_size = Vector2(220, 36)
	action.pressed.connect(activate_selection)
	actions.add_child(action)
	discard = Button.new()
	discard.text = "Discard stack"
	discard.pressed.connect(discard_selection)
	actions.add_child(discard)
	var close := Button.new()
	close.text = "Close [I / Esc]"
	close.pressed.connect(func(): set_open(false))
	actions.add_child(close)
	player.progression.changed.connect(refresh)
	player.inventory.changed.connect(refresh)
	player.equipment.changed.connect(refresh)
	player.stats.changed.connect(refresh)
	player.health.changed.connect(func(_current, _maximum): refresh())
	refresh()
	hide()

func _input(event: InputEvent) -> void:
	if player.ui_session: return
	if event.is_action_pressed("inventory") or visible and event.is_action_pressed("release_mouse"):
		set_open(not visible)
		get_viewport().set_input_as_handled()
	elif visible and event is InputEventMouseButton:
		# Stop outside-panel clicks reaching gameplay/camera; GUI handles inside clicks.
		if not get_global_rect().has_point(event.position): get_viewport().set_input_as_handled()

func set_open(open: bool) -> void:
	if player.ui_session:
		if open: player.ui_session.open_panel(self)
		else: player.ui_session.close()
		refresh()
		return
	visible = open
	player.ui_open = open
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if open else Input.MOUSE_MODE_VISIBLE
	refresh()

func select_slot(index: int) -> void:
	discard_armed = false
	selected = index
	selected_gear = &""
	refresh()

func select_gear(slot: StringName) -> void:
	discard_armed = false
	selected = -1
	selected_gear = slot
	refresh()

func activate_selection() -> void:
	var success := false
	if not player.equipment.can_change():
		zone.announce("Finish your attack or revive before using equipment or items.")
		return
	if selected_gear != &"": success = player.equipment.unequip(selected_gear)
	elif selected >= 0 and player.inventory.slots[selected]:
		var item := player.inventory.slots[selected].definition()
		success = player.equipment.equip(selected) if item.equipment_slot != &"" else player.inventory.use_slot(selected, player.health)
	var feedback := "Equipment / inventory updated" if success else "Cannot use: check bag space, required level or current health."
	zone.announce(feedback)
	refresh()
	details.text += "\n" + feedback

func refresh() -> void:
	if title_label == null: return
	var used := 0
	for i in bag_buttons.size():
		var stack := player.inventory.slots[i]
		var button := bag_buttons[i]
		button.text = "-"
		button.tooltip_text = "Empty slot"
		button.icon = null
		if stack:
			used += 1
			var item := stack.definition()
			button.text = stack.display_name() + ("\nx%d" % stack.quantity if item.stackable else "")
			button.tooltip_text = stack.tooltip()
			button.icon = item.icon
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.10, 0.13, 0.13)
		style.border_color = Color(0.72, 0.57, 0.30) if i == selected else Color(0.25, 0.29, 0.26)
		style.set_border_width_all(2 if i == selected else 1)
		style.set_corner_radius_all(3)
		button.add_theme_stylebox_override("normal", style)
		button.modulate = Color(1, 0.86, 0.55) if i == selected else Color.WHITE
	for slot in gear_buttons:
		var stack: ItemStack = player.equipment.slots[slot]
		gear_buttons[slot].text = String(slot).capitalize() + ": " + (stack.display_name() if stack else "-")
		gear_buttons[slot].tooltip_text = stack.tooltip() if stack else "Empty equipment slot"
	title_label.text = "TRAVELER'S PACK   %d / %d     |     %d gold" % [used, PlayerInventory.CAPACITY, player.inventory.gold]
	character.text = "Level %d   XP %d / %d\nHP %d / %d\nAttack %.1f   Defense %.1f\nMove %.1f   Attack speed %.2fx" % [player.progression.level, player.progression.xp, player.progression.xp_required(), player.health.current, player.health.maximum, player.stats.value(&"attack"), player.stats.value(&"defense"), player.stats.value(&"movement_speed"), player.stats.value(&"attack_speed")]
	var stack: ItemStack = player.equipment.slots.get(selected_gear) if selected_gear != &"" else (player.inventory.slots[selected] if selected >= 0 else null)
	details.text = (stack.tooltip() + "\n" + EquipmentComparison.describe(stack.definition(), player, stack)) if stack else "Drag to move/equip; Shift-drag splits a stack. Hover for a tooltip.\nEquipment can be changed when alive and outside an attack."
	action.text = "Unequip" if selected_gear != &"" else ("Equip" if stack and stack.definition().equipment_slot != &"" else "Use")
	discard.disabled = selected < 0 or stack == null
	discard.text = "Confirm discard" if discard_armed else "Discard stack"
	action.disabled = stack == null or (selected_gear == &"" and stack.definition().equipment_slot == &"" and stack.definition().healing <= 0)

func discard_selection() -> void:
	if selected < 0 or not player.equipment.can_change(): return
	if not discard_armed:
		discard_armed = true
		refresh()
		return
	player.inventory.discard_slot(selected)
	discard_armed = false
	refresh()
