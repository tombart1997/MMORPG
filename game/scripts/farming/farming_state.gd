class_name FarmingState
extends Node3D
## World cooldowns and outstanding encounter loot share the player save transaction.
const LOCATION := "hollow_briarwake"
var encounter: WorldFracture
func _ready() -> void:
	encounter = WorldFracture.new()
	encounter.data = load("res://data/farming/briarwake.tres")
	encounter.loot_parent = get_parent()
	encounter.notice_requested.connect(get_parent().announce)
	encounter.position = ZoneTerrain.FRACTURE
	add_child(encounter)
func snapshot() -> Dictionary:
	var drops: Array = []
	for drop: LootPickup in get_tree().get_nodes_in_group("loot"):
		if drop.claimed or drop.encounter_id != LOCATION: continue
		drops.append({"id": String(drop.item.id) if drop.item else "", "quantity": drop.quantity, "coins": drop.coins,
			"position": [drop.global_position.x, drop.global_position.y, drop.global_position.z], "lifetime": drop.lifetime})
	return {"cooldown": encounter.remaining, "completions": encounter.completions, "loot": drops}
static func number(value: Variant, minimum: float, maximum: float) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value >= minimum and value <= maximum
static func valid_snapshot(data: Variant) -> bool:
	if not data is Dictionary: return false
	if data.is_empty(): return true
	for key in ["cooldown", "completions"]:
		if not number(data.get(key), 0, 100000000): return false
	var definition: FractureData = load("res://data/farming/briarwake.tres")
	if float(data.completions) != floorf(float(data.completions)) or data.cooldown > definition.respawn_seconds: return false
	if not data.get("loot") is Array or data.loot.size() > 64: return false
	for drop in data.loot:
		if not drop is Dictionary or not drop.get("id") is String: return false
		if not number(drop.get("coins"), 0, 1000000) or not number(drop.get("quantity"), 1, 999) or not number(drop.get("lifetime"), 0, 300): return false
		if float(drop.coins) != floorf(float(drop.coins)) or float(drop.quantity) != floorf(float(drop.quantity)): return false
		var item := ItemCatalog.get_item(StringName(drop.id)) if drop.id != "" else null
		if drop.id != "" and (item == null or drop.quantity > item.stack_limit()): return false
		if not drop.get("position") is Array or drop.position.size() != 3: return false
		for value in drop.position:
			if not number(value, -1000, 1000): return false
	return true
func restore(data: Dictionary) -> void:
	# Restoring a bag and leaving current world pickups would duplicate transferred loot.
	for drop: LootPickup in get_tree().get_nodes_in_group("loot"):
		drop.claimed = true
		drop.queue_free()
	encounter.remaining = 0
	encounter.reset_attempt()
	encounter.remaining = float(data.get("cooldown", 0))
	encounter.completions = int(data.get("completions", 0))
	if encounter.remaining > 0:
		encounter.body.health.current = 0
		encounter.body._on_died(null)
	for raw in data.get("loot", []):
		var drop := LootPickup.new()
		drop.item = ItemCatalog.get_item(StringName(raw.id)) if raw.id != "" else null
		drop.quantity = int(raw.quantity)
		drop.coins = int(raw.coins)
		drop.encounter_id = LOCATION
		get_parent().add_child(drop)
		drop.global_position = Vector3(raw.position[0], raw.position[1], raw.position[2])
		drop.lifetime = float(raw.lifetime)
