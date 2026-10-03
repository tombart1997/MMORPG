class_name PlayerQuests
extends Node
signal changed
var actor: ActorBody
var states: Dictionary = {}

func status(id: StringName) -> String:
	return states.get(String(id), {}).get("status", "available")

func available(quest: QuestData) -> bool:
	if states.has(String(quest.id)): return false
	if actor and actor.progression and actor.progression.level < quest.required_level: return false
	for id in quest.prerequisites:
		if status(id) != "completed": return false
	return true

func accept(id: StringName, npc: WorldNPC) -> bool:
	var quest: QuestData = QuestCatalog.all().get(id)
	if quest == null or not available(quest) or npc.data.id != quest.giver or not npc.can_interact(actor): return false
	var counts: Array = []
	counts.resize(quest.objectives.size())
	counts.fill(0)
	states[String(id)] = {"status": "active", "counts": counts}
	record(&"talk", npc.data.id)
	changed.emit()
	return true

func record(type: StringName, target: StringName, amount: int = 1) -> void:
	for key in states:
		if status(StringName(key)) != "active": continue
		var quest: QuestData = QuestCatalog.all()[StringName(key)]
		for i in quest.objectives.size():
			var objective: Dictionary = quest.objectives[i]
			if objective.type == String(type) and objective.target == String(target):
				states[key].counts[i] = mini(int(objective.get("amount", 1)), int(states[key].counts[i]) + amount)
	changed.emit()

func progress(quest: QuestData, index: int) -> int:
	if status(quest.id) == "completed": return int(quest.objectives[index].get("amount", 1))
	var objective: Dictionary = quest.objectives[index]
	if objective.type == "collect": return mini(actor.inventory.count(StringName(objective.target)), int(objective.amount))
	if objective.type == "return": return 1 if status(quest.id) == "completed" else 0
	return int(states.get(String(quest.id), {}).get("counts", [])[index]) if states.has(String(quest.id)) else 0

func ready(quest: QuestData) -> bool:
	if status(quest.id) != "active": return false
	for i in quest.objectives.size():
		if quest.objectives[i].type != "return" and progress(quest, i) < int(quest.objectives[i].get("amount", 1)): return false
	return true

func claim(id: StringName, npc: WorldNPC) -> String:
	var quest: QuestData = QuestCatalog.all().get(id)
	if quest == null or not ready(quest) or npc.data.id != quest.turn_in or not npc.can_interact(actor): return "Quest is not ready here."
	var bag := actor.inventory
	if bag.transaction_busy: return "Please finish the current transaction."
	var preview := PlayerInventory.new()
	for i in bag.slots.size():
		if bag.slots[i]:
			preview.slots[i] = ItemStack.new(bag.slots[i].id, bag.slots[i].quantity)
			preview.slots[i].properties = bag.slots[i].properties.duplicate(true)
	for objective in quest.objectives:
		if objective.type == "collect": preview.remove_count(StringName(objective.target), int(objective.amount), false)
	var fits := true
	for item_id in quest.items:
		if not preview.add_item(ItemCatalog.get_item(StringName(item_id)), int(quest.items[item_id])): fits = false
	preview.free()
	if not fits: return "Free bag space for the quest reward."
	bag.transaction_busy = true
	states[String(id)].status = "completed"
	for objective in quest.objectives:
		if objective.type == "collect": bag.remove_count(StringName(objective.target), int(objective.amount), false)
	bag.gold += quest.gold
	for item_id in quest.items: bag.add_item(ItemCatalog.get_item(StringName(item_id)), int(quest.items[item_id]))
	actor.progression.award_xp(quest.xp)
	bag.changed.emit()
	bag.transaction_busy = false
	changed.emit()
	return ""

func marker(npc_id: StringName) -> String:
	var active := false
	for quest in QuestCatalog.all().values():
		if quest.turn_in == npc_id and ready(quest): return "[?] "
		if quest.giver == npc_id and available(quest): return "[!] "
		if status(quest.id) == "active":
			if quest.turn_in == npc_id: active = true
			for objective in quest.objectives:
				if objective.type == "talk" and objective.target == String(npc_id): active = true
	return "[...] " if active else ""

func describe(quest: QuestData) -> String:
	var result := quest.title + " - " + status(quest.id).capitalize() + "\n" + quest.description
	for i in quest.objectives.size():
		result += "\n  %s: %d / %d" % [quest.objectives[i].get("label", quest.objectives[i].target), progress(quest, i), int(quest.objectives[i].get("amount", 1))]
	result += "\nReward: %d gold, %d XP" % [quest.gold, quest.xp]
	for id in quest.items: result += ", %s x%d" % [ItemCatalog.get_item(StringName(id)).display_name, quest.items[id]]
	return result

static func valid_snapshot(data: Variant) -> bool:
	if not data is Dictionary: return false
	for key in data:
		var quest: QuestData = QuestCatalog.all().get(StringName(key))
		if quest == null or not data[key] is Dictionary: return false
		if data[key].get("status") not in ["active", "completed"] or not data[key].get("counts") is Array: return false
		if data[key].counts.size() != quest.objectives.size(): return false
		for i in data[key].counts.size():
			var count: Variant = data[key].counts[i]
			if not count is float and not count is int: return false
			if count < 0 or count > int(quest.objectives[i].get("amount", 1)) or float(count) != floorf(float(count)): return false
	return true
