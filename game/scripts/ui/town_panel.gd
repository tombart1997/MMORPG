class_name TownPanel
extends PanelContainer
## Dialogue and trading presentation. Sessions/services remain usable without this UI.
var player: ActorBody
var npc: WorldNPC
var session: UISession
var merchant := MerchantService.new()
var dialogue := DialogueSession.new()
var quest_actions: QuestActions
var title_label: Label
var dialogue_box: VBoxContainer
var dialogue_text: Label
var responses: VBoxContainer
var shop_box: VBoxContainer
var stock_list: ItemList
var bag_list: ItemList
var info: Label
var feedback: Label
var quantity: SpinBox
var trade: Button
var mode: StringName = &"buy"
var offer_index: int = -1
var bag_index: int = -1
var expected_stack: ItemStack
var bag_indices: Array[int] = []

func _ready() -> void:
	position = Vector2(240, 55)
	custom_minimum_size = Vector2(980, 570)
	z_index = 20
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.045, 0.065, 0.06, 0.99)
	style.border_color = Color(0.6, 0.47, 0.25)
	style.set_border_width_all(2)
	style.content_margin_left = 20
	style.content_margin_right = 20
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	add_theme_stylebox_override("panel", style)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	add_child(column)
	var header := HBoxContainer.new()
	column.add_child(header)
	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 23)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title_label)
	var talk := Button.new()
	talk.text = "Talk"
	talk.pressed.connect(show_dialogue)
	header.add_child(talk)
	var bag := Button.new()
	bag.text = "Equipment [I]"
	bag.pressed.connect(func(): session.open_panel(session.inventory_panel); session.inventory_panel.refresh())
	header.add_child(bag)
	var close := Button.new()
	close.text = "Leave [Esc]"
	close.pressed.connect(session.close)
	header.add_child(close)
	quest_actions = QuestActions.new()
	quest_actions.player = player
	column.add_child(quest_actions)
	dialogue_box = VBoxContainer.new()
	column.add_child(dialogue_box)
	dialogue_text = Label.new()
	dialogue_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	dialogue_text.custom_minimum_size = Vector2(900, 180)
	dialogue_text.add_theme_font_size_override("font_size", 22)
	dialogue_box.add_child(dialogue_text)
	responses = VBoxContainer.new()
	dialogue_box.add_child(responses)
	shop_box = VBoxContainer.new()
	column.add_child(shop_box)
	var captions := Label.new()
	captions.text = "MERCHANT SUPPLIES (unit buy price)                         YOUR PACK (unit sell value)"
	shop_box.add_child(captions)
	var lists := HBoxContainer.new()
	shop_box.add_child(lists)
	stock_list = ItemList.new()
	bag_list = ItemList.new()
	for list in [stock_list, bag_list]:
		list.custom_minimum_size = Vector2(464, 220)
		list.fixed_icon_size = Vector2i(26, 26)
		list.add_theme_font_size_override("font_size", 17)
		lists.add_child(list)
	stock_list.item_selected.connect(select_offer)
	bag_list.item_selected.connect(select_sale)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size.y = 145
	shop_box.add_child(scroll)
	info = Label.new()
	info.custom_minimum_size.x = 900
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_font_size_override("font_size", 16)
	scroll.add_child(info)
	var buttons := HBoxContainer.new()
	shop_box.add_child(buttons)
	var qty_label := Label.new()
	qty_label.text = "Quantity: "
	buttons.add_child(qty_label)
	quantity = SpinBox.new()
	quantity.min_value = 1
	quantity.max_value = 99
	quantity.value = 1
	quantity.value_changed.connect(func(_value): update_details())
	buttons.add_child(quantity)
	trade = Button.new()
	trade.custom_minimum_size = Vector2(260, 36)
	trade.pressed.connect(transact)
	buttons.add_child(trade)
	feedback = Label.new()
	feedback.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	feedback.custom_minimum_size = Vector2(900, 34)
	feedback.modulate = Color(1, 0.85, 0.51)
	column.add_child(feedback)
	quest_actions.message = feedback
	player.quests.changed.connect(func(): quest_actions.refresh())
	player.inventory.changed.connect(refresh_shop)
	player.equipment.changed.connect(update_details)
	hide()

func open_npc(target: WorldNPC) -> void:
	if not target.can_interact(player): return
	npc = target
	player.quests.record(&"talk", npc.data.id)
	quest_actions.npc = npc
	quest_actions.refresh()
	dialogue.npc = npc
	dialogue.player = player
	dialogue.page = 0
	feedback.text = ""
	offer_index = -1
	bag_index = -1
	expected_stack = null
	session.open_panel(self)
	if npc.data.shop: show_shop()
	else: show_dialogue()

func show_dialogue() -> void:
	if not is_instance_valid(npc): return
	shop_box.hide()
	dialogue_box.show()
	title_label.text = npc.data.display_name
	dialogue_text.text = dialogue.text()
	for child in responses.get_children():
		responses.remove_child(child)
		child.queue_free()
	var options := dialogue.options()
	for i in options.size():
		var button := Button.new()
		button.text = options[i].get("text", "Continue")
		button.custom_minimum_size.y = 42
		button.pressed.connect(choose_response.bind(i))
		responses.add_child(button)

func choose_response(index: int) -> void:
	match dialogue.choose(index):
		&"shop": show_shop()
		&"close": session.close()
		&"talk": show_dialogue()

func show_shop() -> void:
	if not merchant.available(npc, player): return
	dialogue_box.hide()
	shop_box.show()
	refresh_shop()

func refresh_shop() -> void:
	if not is_instance_valid(npc) or npc.data.shop == null: return
	title_label.text = "%s | Gold %d" % [npc.data.shop.title, player.inventory.gold]
	stock_list.clear()
	for offer in npc.data.shop.offers:
		var index := stock_list.add_item("%s   -   %dg" % [offer.item.display_name, offer.price], offer.item.icon)
		stock_list.set_item_tooltip(index, offer.item.tooltip() + "\n" + EquipmentComparison.describe(offer.item, player))
	bag_list.clear()
	bag_indices.clear()
	for i in player.inventory.slots.size():
		var stack := player.inventory.slots[i]
		if stack:
			var item := stack.definition()
			bag_indices.append(i)
			var index := bag_list.add_item("%s x%d   -   %dg each" % [stack.display_name(), stack.quantity, item.value], item.icon)
			bag_list.set_item_tooltip(index, stack.tooltip())
	# Preserve selection only while the exact stack still occupies that slot.
	if bag_index >= 0 and player.inventory.slots[bag_index] != expected_stack:
		bag_index = -1
		expected_stack = null
	if offer_index >= 0: stock_list.select(offer_index)
	if bag_indices.has(bag_index): bag_list.select(bag_indices.find(bag_index))
	update_details()

func select_offer(index: int) -> void:
	mode = &"buy"
	offer_index = index
	bag_list.deselect_all()
	quantity.value = 1
	update_details()

func select_sale(index: int) -> void:
	if index < 0 or index >= bag_indices.size(): return
	mode = &"sell"
	bag_index = bag_indices[index]
	expected_stack = player.inventory.slots[bag_index]
	stock_list.deselect_all()
	quantity.value = 1
	update_details()

func update_details() -> void:
	if not is_instance_valid(npc) or npc.data.shop == null or info == null: return
	var item: ItemData
	var price := 0
	var limit := 1
	if mode == &"buy" and offer_index >= 0 and offer_index < npc.data.shop.offers.size():
		var offer: ShopOffer = npc.data.shop.offers[offer_index]
		item = offer.item
		price = offer.price
		limit = 99 if item.stackable else 1
	elif mode == &"sell" and expected_stack and bag_index >= 0 and player.inventory.slots[bag_index] == expected_stack:
		item = expected_stack.definition()
		price = item.value
		limit = expected_stack.quantity
	quantity.set_value_no_signal(minf(quantity.value, limit))
	quantity.max_value = limit
	trade.disabled = item == null
	trade.text = "%s for %d gold" % ["Buy" if mode == &"buy" else "Sell", price * int(quantity.value)]
	info.text = ((expected_stack.tooltip() if mode == &"sell" and expected_stack else item.tooltip()) + "\n" + EquipmentComparison.describe(item, player, expected_stack if mode == &"sell" else null)) if item else "Select merchant supplies to buy, or an item in your pack to sell.\nEquipped items must be unequipped before selling. Supplies are unlimited."

func transact() -> void:
	var result := merchant.buy(npc, player, offer_index, int(quantity.value)) if mode == &"buy" else merchant.sell(npc, player, bag_index, expected_stack, int(quantity.value))
	refresh_shop()
	feedback.text = ("Purchase complete. Press I to equip your new gear." if mode == &"buy" else "Sale complete.") if result.is_empty() else result
