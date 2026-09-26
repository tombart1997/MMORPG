class_name PlayerActions
extends Node
## Assignments reference definitions, never detach stacks from the real bag.
var actor: ActorBody
var slots: Array[StringName] = [&"field_tonic", &""]
var cooldown: float = 0
var feedback: String = "Drag consumables from I into Q / F. Right-click a slot to clear."
var feedback_time: float = 0

func _process(delta: float) -> void:
	cooldown = maxf(0, cooldown - delta)
	feedback_time = maxf(0, feedback_time - delta)

static func usable(item: ItemData) -> bool:
	return item != null and item.item_type == "consumable" and item.healing > 0

func assign(index: int, id: StringName) -> bool:
	if index < 0 or index >= slots.size(): return false
	if id != &"" and not usable(ItemCatalog.get_item(id)): return false
	slots[index] = id
	return true

func can_drop(data: Variant) -> bool:
	if not data is Dictionary or data.get("player") != actor or data.get("equipment", &"") != &"": return false
	var index: Variant = data.get("index")
	if not index is int or index < 0 or index >= actor.inventory.slots.size(): return false
	var stack: ItemStack = actor.inventory.slots[index]
	return stack != null and stack == data.get("stack") and usable(stack.definition())

func unavailable(index: int, allow_inventory: bool = false) -> String:
	if index < 0 or index >= slots.size() or slots[index] == &"": return "Empty — drag a consumable here"
	return item_unavailable(ItemCatalog.get_item(slots[index]), allow_inventory)

func item_unavailable(item: ItemData, allow_inventory: bool = false) -> String:
	if not usable(item): return "No usable consumable"
	if not actor.health.is_alive(): return "Revive first"
	if actor.ui_open and not allow_inventory: return "Close the open panel"
	if actor.combat.is_attacking() or actor.skills and actor.skills.busy(): return "Finish your action"
	if actor.progression.level < item.required_level: return "Requires level %d" % item.required_level
	if actor.inventory.count(item.id) < 1: return "None in inventory"
	if cooldown > 0: return "Restoration cooldown %.1fs" % cooldown
	if actor.health.current >= actor.health.maximum: return "Health is full"
	return ""

func activate(index: int) -> bool:
	var reason := unavailable(index)
	if not reason.is_empty(): report(reason); return false
	return use_item(ItemCatalog.get_item(slots[index]))

func use_item(item: ItemData, allow_inventory: bool = false) -> bool:
	var reason := item_unavailable(item, allow_inventory)
	if not reason.is_empty(): report(reason); return false
	var before := actor.health.current
	if not actor.inventory.use_item(item, actor.health): return false
	cooldown = 3.0
	report("%s: +%d health" % [item.display_name, actor.health.current - before])
	return true

func use_bag(index: int) -> bool:
	if index < 0 or index >= actor.inventory.slots.size() or actor.inventory.slots[index] == null: return false
	var item := actor.inventory.slots[index].definition()
	if item.mount_unlock != &"": return actor.mounts.unlock(index)
	return use_item(item, true)

func report(message: String) -> void:
	feedback = message
	feedback_time = 4

func snapshot() -> Array:
	return [String(slots[0]), String(slots[1])]

static func valid_snapshot(data: Variant) -> bool:
	if not data is Array or data.size() != 2: return false
	for id in data:
		if not id is String or (id != "" and not usable(ItemCatalog.get_item(StringName(id)))): return false
	return true

func restore(data: Array) -> void:
	slots.assign([StringName(data[0]), StringName(data[1])])
	cooldown = 0
	feedback_time = 0
