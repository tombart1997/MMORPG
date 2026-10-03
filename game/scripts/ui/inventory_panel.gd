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
var stat_values: Dictionary = {}

func _ready() -> void:
	position = Vector2(755, 205)
	z_index = 10
	theme = PaintedTheme.get_theme()
	custom_minimum_size = Vector2(490, 390)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 5)
	add_child(column)
	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 12)
	column.add_child(title_label)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	PaintedTheme.section(column, "Equipment / Inventory")
	column.add_child(row)
	var equipment_column := VBoxContainer.new()
	equipment_column.custom_minimum_size.x = 172
	row.add_child(equipment_column)
	for slot in PlayerEquipment.SLOT_NAMES:
		var button := ItemSlot.new()
		button.player = player
		button.equipment_slot = slot
		button.custom_minimum_size = Vector2(172, 27)
		button.clip_text = true
		button.pressed.connect(select_gear.bind(slot))
		equipment_column.add_child(button)
		gear_buttons[slot] = button
	character = Label.new()
	character.add_theme_font_size_override("font_size", 12)
	equipment_column.add_child(character)
	for caption in ["HP", "Attack", "Defence", "Move speed", "Attack rate"]:
		stat_values[caption] = PaintedTheme.value_row(equipment_column,caption)
	var grid := GridContainer.new()
	grid.columns = 6
	grid.add_theme_constant_override("h_separation", 5)
	grid.add_theme_constant_override("v_separation", 5)
	row.add_child(grid)
	for i in PlayerInventory.CAPACITY:
		var button := ItemSlot.new()
		button.player = player
		button.bag_index = i
		button.custom_minimum_size = Vector2(44, 44)
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", 30)
		button.add_theme_font_size_override("font_size", 13)
		button.pressed.connect(select_slot.bind(i))
		grid.add_child(button)
		bag_buttons.append(button)
	details = Label.new()
	details.custom_minimum_size = Vector2(460, 95)
	details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	details.add_theme_font_size_override("font_size", 12)
	column.add_child(details)
	var actions := HBoxContainer.new()
	column.add_child(actions)
	action = Button.new()
	action.custom_minimum_size = Vector2(150, 25)
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
	WindowChrome.install(self, "Character · Inventory", func(): set_open(false))
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
		success = player.equipment.equip(selected) if item.equipment_slot != &"" else (player.actions.use_bag(selected) if player.actions else player.inventory.use_slot(selected, player.health))
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
			button.text = str(stack.quantity) if item.stackable else ""
			button.tooltip_text = stack.tooltip()
			button.icon = PaintedTheme.painted_icon(item.icon)
		button.add_theme_stylebox_override("normal", PaintedTheme.slot())
		button.modulate = Color(1, 0.86, 0.55) if i == selected else Color.WHITE
	for slot in gear_buttons:
		var stack: ItemStack = player.equipment.slots[slot]
		gear_buttons[slot].text = String(slot).capitalize() + ": " + (stack.display_name() if stack else "-")
		gear_buttons[slot].tooltip_text = stack.tooltip() if stack else "Empty equipment slot"
	title_label.text = "TRAVELER'S PACK   %d / %d     |     %d gold" % [used, PlayerInventory.CAPACITY, player.inventory.gold]
	character.text = "Lv.%d   XP %d / %d" % [player.progression.level,player.progression.xp,player.progression.xp_required()]
	stat_values["HP"].text = "%d/%d" % [player.health.current,player.health.maximum]
	stat_values["Attack"].text = "%.1f" % player.stats.value(&"attack")
	stat_values["Defence"].text = "%.1f" % player.stats.value(&"defense")
	stat_values["Move speed"].text = "%.1f" % player.stats.value(&"movement_speed")
	stat_values["Attack rate"].text = "%.2fx" % player.stats.value(&"attack_speed")
	var stack: ItemStack = player.equipment.slots.get(selected_gear) if selected_gear != &"" else (player.inventory.slots[selected] if selected >= 0 else null)
	details.text = (stack.tooltip() + "\n" + EquipmentComparison.describe(stack.definition(), player, stack)) if stack else "Drag to move/equip; Shift-drag splits a stack. Hover for a tooltip.\nEquipment can be changed when alive and outside an attack."
	action.text = "Unequip" if selected_gear != &"" else ("Equip" if stack and stack.definition().equipment_slot != &"" else "Use")
	discard.disabled = selected < 0 or stack == null
	discard.text = "Confirm discard" if discard_armed else "Discard stack"
	action.disabled = stack == null or (selected_gear == &"" and stack.definition().equipment_slot == &"" and stack.definition().healing <= 0 and stack.definition().mount_unlock == &"")

func discard_selection() -> void:
	if selected < 0 or not player.equipment.can_change(): return
	if not discard_armed:
		discard_armed = true
		refresh()
		return
	player.inventory.discard_slot(selected)
	discard_armed = false
	refresh()
