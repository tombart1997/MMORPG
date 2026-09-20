class_name ProgressionSave
extends RefCounted
## Versioned, validated snapshots. Parse fully before mutating gameplay state.
const VERSION = 3
var path: String = "user://progression.json"
var error: String = ""

func encode_stack(stack: ItemStack) -> Variant:
	return {"id": String(stack.id), "quantity": stack.quantity, "properties": stack.properties} if stack else null

func save_player(actor: ActorBody) -> bool:
	var bag: Array = []
	var gear: Dictionary = {}
	for stack in actor.inventory.slots: bag.append(encode_stack(stack))
	for slot in actor.equipment.slots: gear[String(slot)] = encode_stack(actor.equipment.slots[slot])
	var data := {"version": VERSION, "level": actor.progression.level, "xp": actor.progression.xp,
		"kills": actor.progression.kills, "gold": actor.inventory.gold, "hp": actor.health.current,
		"inventory": bag, "equipment": gear, "quests": actor.quests.states if actor.quests else {}}
	data["skills"] = actor.skills.snapshot() if actor.skills else PlayerSkills.default_snapshot()
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	if file == null:
		error = "Cannot write save"
		return false
	file.store_string(JSON.stringify(data, "  "))
	file.flush()
	file.close()
	# Keep the previous complete snapshot; recover it if the primary is damaged.
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path + ".bak")
		if DirAccess.rename_absolute(path, path + ".bak") != OK: return false
	if DirAccess.rename_absolute(path + ".tmp", path) != OK:
		error = "Cannot finalize save"
		return false
	error = ""
	return true

func decode_stack(data: Variant) -> ItemStack:
	if not data is Dictionary or not data.get("id") is String: return null
	var item := ItemCatalog.get_item(StringName(data.id))
	if item == null or not data.get("quantity") is float and not data.get("quantity") is int: return null
	if float(data.quantity) != floorf(float(data.quantity)): return null
	var amount := int(data.quantity)
	if amount < 1 or amount > item.stack_limit() or not data.get("properties", {}) is Dictionary: return null
	var upgrade: Variant = data.get("properties", {}).get("upgrade", 0)
	if not upgrade is float and not upgrade is int: return null
	if float(upgrade) != floorf(float(upgrade)) or upgrade < 0: return null
	if upgrade > 0 and (item.upgrade_profile == null or upgrade > item.upgrade_profile.steps.size()): return null
	var stack := ItemStack.new(item.id, amount)
	stack.properties = data.get("properties", {}).duplicate(true)
	return stack

func load_player(actor: ActorBody) -> bool:
	for candidate in [path, path + ".bak"]:
		if not FileAccess.file_exists(candidate): continue
		var parser := JSON.new()
		if parser.parse(FileAccess.get_file_as_string(candidate)) != OK: continue
		if apply_snapshot(actor, parser.data):
			error = "Loaded backup save" if candidate.ends_with(".bak") else ""
			return true
	error = "No valid save found"
	return false

func apply_snapshot(actor: ActorBody, data: Variant) -> bool:
	if not data is Dictionary or (data.get("version") != 1 and data.get("version") != 2 and data.get("version") != VERSION): return false
	for key in ["level", "xp", "kills", "gold", "hp"]:
		if not data.get(key) is float and not data.get(key) is int: return false
		if not is_finite(float(data[key])) or data[key] < 0 or data[key] > 100000000: return false
	for key in ["level", "xp", "kills", "gold"]:
		if float(data[key]) != floorf(float(data[key])): return false
	if data.level < 1 or data.level > 10000 or data.xp >= 80 + (data.level - 1) * 40: return false
	if not data.get("inventory") is Array or data.inventory.size() != PlayerInventory.CAPACITY: return false
	if not data.get("equipment") is Dictionary: return false
	var bag: Array[ItemStack] = []
	var gear: Dictionary = {}
	for raw in data.inventory:
		var stack := decode_stack(raw)
		if raw != null and stack == null: return false
		bag.append(stack)
	for slot in PlayerEquipment.SLOT_NAMES:
		if not data.equipment.has(String(slot)): return false
		var raw: Variant = data.equipment.get(String(slot))
		var stack := decode_stack(raw)
		if raw != null and (stack == null or stack.definition().equipment_slot != slot or stack.definition().required_level > data.level): return false
		gear[slot] = stack
	var quests: Variant = data.get("quests", {})
	if not PlayerQuests.valid_snapshot(quests): return false
	var skill_state: Variant = data.get("skills", PlayerSkills.default_snapshot() if data.version < 3 else null)
	if not PlayerSkills.valid_snapshot(skill_state): return false
	if actor.skills: actor.skills.restore(skill_state)
	if actor.quests: actor.quests.states = quests.duplicate(true)
	actor.progression.level = int(data.level)
	actor.progression.xp = int(data.xp)
	actor.progression.kills = int(data.kills)
	actor.inventory.gold = int(data.gold)
	actor.inventory.slots = bag
	actor.equipment.slots = gear
	actor.equipment.refresh()
	# Loading is a safe waystone return; dead snapshots revive there.
	actor.health.current = clampf(float(data.hp), 1, actor.health.maximum) if data.hp > 0 else actor.health.maximum
	actor.health.changed.emit(actor.health.current, actor.health.maximum)
	actor.inventory.changed.emit()
	actor.progression.changed.emit()
	if actor.quests: actor.quests.changed.emit()
	return true
