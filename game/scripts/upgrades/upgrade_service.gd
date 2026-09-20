class_name UpgradeService
extends RefCounted
var rng := RandomNumberGenerator.new()

func quote(stack: ItemStack) -> Dictionary:
	if stack == null: return {}
	var profile := stack.definition().upgrade_profile
	if profile == null or stack.upgrade_level() >= profile.steps.size(): return {}
	var rule: Dictionary = profile.steps[stack.upgrade_level()].duplicate(true)
	rule["from"] = stack.upgrade_level()
	rule["to"] = stack.upgrade_level() + 1
	rule["failure"] = profile.failure_policy
	return rule

func attempt(player: ActorBody, npc: WorldNPC, index: int, expected: ItemStack) -> Dictionary:
	if not is_instance_valid(npc) or npc.data.role != &"smith" or not npc.can_interact(player): return {"error": "Approach the Smith outside combat."}
	var bag := player.inventory
	if bag.transaction_busy or index < 0 or index >= bag.slots.size() or bag.slots[index] != expected or expected == null: return {"error": "Item changed. Select it again."}
	var rule := quote(expected)
	if rule.is_empty(): return {"error": "This item cannot be improved further."}
	if bag.gold < int(rule.gold): return {"error": "Not enough gold."}
	for id in rule.get("materials", {}):
		if bag.count(StringName(id)) < int(rule.materials[id]): return {"error": "Missing materials."}
	bag.transaction_busy = true
	bag.gold -= int(rule.gold)
	for id in rule.get("materials", {}): bag.remove_count(StringName(id), int(rule.materials[id]), false)
	var success := rng.randf() < float(rule.chance)
	if success: expected.properties["upgrade"] = int(rule.to)
	elif rule.failure == "downgrade": expected.properties["upgrade"] = maxi(0, int(rule.from) - 1)
	bag.changed.emit()
	bag.transaction_busy = false
	if success and player.quests: player.quests.record(&"upgrade", &"equipment")
	return {"success": success, "message": "Improved to +%d." % expected.upgrade_level() if success else "Attempt failed. Costs spent; item retained at +%d." % expected.upgrade_level()}
