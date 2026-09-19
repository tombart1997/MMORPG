class_name PlayerInventory
extends Node
signal changed
var gold: int = 0
var items: Dictionary = {}
var last_pickup: String = ""

func collect(coins: int, item: ItemData) -> void:
	gold += maxi(0, coins)
	last_pickup = "+%d gold" % coins
	if item:
		items[item.id] = count(item.id) + 1
		last_pickup += " / " + item.display_name
	changed.emit()

func count(id: StringName) -> int:
	return int(items.get(id, 0))

func use_item(item: ItemData, health: HealthComponent) -> bool:
	if count(item.id) <= 0 or not health.is_alive() or health.current >= health.maximum or item.healing <= 0:
		return false
	items[item.id] -= 1
	health.heal(item.healing)
	changed.emit()
	return true
