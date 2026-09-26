class_name SmithPanel
extends PanelContainer
var player: ActorBody
var npc: WorldNPC
var service := UpgradeService.new()
var index: int = -1
var expected: ItemStack
var bag_buttons: Array[ItemSlot] = []
var details: Label
var feedback: Label
var confirm: Button
var drop: UpgradeDrop
var quests: QuestActions
var catalyst: CheckBox

func _ready() -> void:
	position = Vector2(190, 45)
	custom_minimum_size = Vector2(1020, 570)
	z_index = 20
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 14)
	add_child(column)
	var title := Label.new()
	title.text = "OREN'S FORGE | Drag equipment onto the anvil"
	title.add_theme_font_size_override("font_size", 22)
	column.add_child(title)
	quests = QuestActions.new()
	quests.player = player
	column.add_child(quests)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 20)
	column.add_child(row)
	var grid := GridContainer.new()
	grid.columns = 6
	row.add_child(grid)
	for i in PlayerInventory.CAPACITY:
		var button := ItemSlot.new()
		button.player = player
		button.bag_index = i
		button.custom_minimum_size = Vector2(76, 68)
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.add_theme_font_size_override("font_size", 12)
		button.pressed.connect(func(): select_item(i, player.inventory.slots[i]))
		bag_buttons.append(button)
		grid.add_child(button)
	var right := VBoxContainer.new()
	right.custom_minimum_size.x = 475
	row.add_child(right)
	drop = UpgradeDrop.new()
	drop.panel = self
	drop.text = "DROP EQUIPMENT HERE"
	drop.custom_minimum_size = Vector2(475, 65)
	right.add_child(drop)
	details = Label.new()
	details.custom_minimum_size = Vector2(475, 230)
	details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(details)
	catalyst = CheckBox.new()
	catalyst.text = "Spend 1 Wakeglass Ember: guarantee this upgrade"
	catalyst.toggled.connect(func(_pressed): refresh())
	right.add_child(catalyst)
	confirm = Button.new()
	confirm.text = "Confirm upgrade attempt"
	confirm.pressed.connect(attempt)
	right.add_child(confirm)
	feedback = Label.new()
	feedback.custom_minimum_size.y = 28
	column.add_child(feedback)
	quests.message = feedback
	var close := Button.new()
	close.text = "Return to the road [Esc]"
	close.pressed.connect(player.ui_session.close)
	column.add_child(close)
	player.inventory.changed.connect(refresh)
	player.quests.changed.connect(func(): quests.refresh())
	refresh()
	hide()

func open_npc(target: WorldNPC) -> void:
	npc = target
	quests.npc = npc
	player.quests.record(&"talk", npc.data.id)
	quests.refresh()
	index = -1
	expected = null
	feedback.text = npc.data.pages[0].text
	player.ui_session.open_panel(self)
	refresh()

func select_item(slot: int, stack: ItemStack) -> void:
	index = slot
	expected = stack
	feedback.text = ""
	refresh()

func refresh() -> void:
	if details == null: return
	for i in bag_buttons.size():
		var stack := player.inventory.slots[i]
		bag_buttons[i].text = (stack.display_name() + (" x%d" % stack.quantity if stack.quantity > 1 else "")) if stack else "-"
		bag_buttons[i].tooltip_text = stack.tooltip() if stack else "Empty"
	if index >= 0 and player.inventory.slots[index] != expected: expected = null
	var rule := service.quote(expected)
	catalyst.disabled = rule.is_empty() or float(rule.get("chance", 1)) >= 1 or player.inventory.count(&"wakeglass") == 0
	if catalyst.disabled: catalyst.set_pressed_no_signal(false)
	confirm.disabled = rule.is_empty()
	details.text = "Unequip an item first. Drag it from this pack onto the anvil, or select it.\nNo attempt occurs until you confirm."
	if rule.is_empty():
		if expected: details.text = expected.display_name() + "\nNo further upgrade is available."
		return
	details.text = "%s\n+%d -> +%d\nCost: %d gold (you have %d)\nSuccess: %.0f%%\n" % [expected.display_name(), rule.from, rule.to, rule.gold, player.inventory.gold, float(rule.chance) * 100]
	for id in rule.materials: details.text += "%s: %d required / %d held\n" % [ItemCatalog.get_item(StringName(id)).display_name, rule.materials[id], player.inventory.count(StringName(id))]
	for stat in rule.bonuses: details.text += "%s %+.1f\n" % [String(stat).replace("_", " ").capitalize(), float(rule.bonuses[stat])]
	details.text += "Failure: costs spent; item and level retained." if rule.failure == "retain" else "Failure: costs spent; item loses one upgrade level."
	if catalyst.button_pressed: details.text += "\nWakeglass selected: 100% success; consumes one Ember."

func attempt() -> void:
	var result := service.attempt(player, npc, index, expected, catalyst.button_pressed)
	refresh()
	feedback.text = result.get("error", result.get("message", ""))
