class_name PlayerInventory
extends Node
signal changed
const CAPACITY = 24
var gold: int = 0
var transaction_busy: bool = false
var slots: Array[ItemStack] = []
var last_pickup: String = ""

func _init() -> void:
	slots.resize(CAPACITY)

func count(id: StringName) -> int:
	var total := 0
	for stack in slots:
		if stack and stack.id == id: total += stack.quantity
	return total

func can_add(item: ItemData, amount: int = 1) -> bool:
	var room := 0
	for stack in slots:
		if stack == null: room += item.stack_limit()
		elif stack.id == item.id and stack.properties.is_empty(): room += item.stack_limit() - stack.quantity
	return amount > 0 and room >= amount

func add_item(item: ItemData, amount: int = 1) -> bool:
	if not can_add(item, amount): return false
	for stack in slots:
		if stack and stack.id == item.id and stack.properties.is_empty():
			var moved := mini(amount, item.stack_limit() - stack.quantity)
			stack.quantity += moved
			amount -= moved
	for i in slots.size():
		if amount > 0 and slots[i] == null:
			var moved := mini(amount, item.stack_limit())
			slots[i] = ItemStack.new(item.id, moved)
			amount -= moved
	changed.emit()
	return true

func collect(coins: int, item: ItemData, amount: int = 1) -> bool:
	if item and not can_add(item, amount):
		last_pickup = "Inventory full | bundle remains on the ground."
		return false
	if item: add_item(item, amount)
	gold += maxi(0, coins)
	last_pickup = "+%d gold%s" % [coins, " / %s x%d" % [item.display_name, amount] if item else ""]
	changed.emit()
	return true

func use_slot(index: int, health: HealthComponent) -> bool:
	if index < 0 or index >= slots.size() or slots[index] == null: return false
	var item := slots[index].definition()
	if item.healing <= 0 or not health.is_alive() or health.current >= health.maximum: return false
	health.heal(item.healing)
	slots[index].quantity -= 1
	if slots[index].quantity == 0: slots[index] = null
	changed.emit()
	return true

func use_item(item: ItemData, health: HealthComponent) -> bool:
	for i in slots.size():
		if slots[i] and slots[i].id == item.id: return use_slot(i, health)
	return false

func discard_slot(index: int) -> bool:
	if index < 0 or index >= slots.size() or slots[index] == null: return false
	slots[index] = null
	changed.emit()
	return true

func move_slot(source: int, destination: int, expected: ItemStack, quantity: int = -1) -> bool:
	if transaction_busy or source < 0 or source >= slots.size() or destination < 0 or destination >= slots.size() or source == destination: return false
	if expected == null or slots[source] != expected: return false
	var amount := expected.quantity if quantity == -1 else quantity
	if amount < 1 or amount > expected.quantity: return false
	var target := slots[destination]
	if target and target.id == expected.id and target.properties == expected.properties and target.definition().stackable:
		var moved := mini(amount, target.definition().stack_limit() - target.quantity)
		if moved == 0: return false
		target.quantity += moved
		expected.quantity -= moved
		if expected.quantity == 0: slots[source] = null
	elif target == null and amount < expected.quantity:
		var split := ItemStack.new(expected.id, amount)
		split.properties = expected.properties.duplicate(true)
		slots[destination] = split
		expected.quantity -= amount
	else:
		if amount != expected.quantity: return false
		slots[source] = target
		slots[destination] = expected
	changed.emit()
	return true

func remove_count(id: StringName, amount: int, notify: bool = true) -> bool:
	if amount < 0 or count(id) < amount: return false
	for i in slots.size():
		if slots[i] and slots[i].id == id:
			var take := mini(amount, slots[i].quantity)
			slots[i].quantity -= take
			amount -= take
			if slots[i].quantity == 0: slots[i] = null
	if notify: changed.emit()
	return true
