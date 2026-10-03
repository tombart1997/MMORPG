class_name PlayerEquipment
extends Node
signal changed
const SLOT_NAMES = [&"weapon", &"head", &"chest", &"hands", &"legs", &"feet"]
var actor: ActorBody
var slots: Dictionary = {}

func _init() -> void:
	for slot in SLOT_NAMES: slots[slot] = null

func can_change() -> bool:
	return actor.health.is_alive() and not actor.combat.is_attacking() and not (actor.skills and actor.skills.busy())

func equip(index: int) -> bool:
	if not can_change() or index < 0 or index >= actor.inventory.slots.size(): return false
	var stack: ItemStack = actor.inventory.slots[index]
	if stack == null: return false
	var item := stack.definition()
	if not slots.has(item.equipment_slot) or item.required_level > actor.progression.level: return false
	# Swap in place, including a full bag; preserve the instance.
	actor.inventory.slots[index] = slots[item.equipment_slot]
	slots[item.equipment_slot] = stack
	refresh()
	actor.inventory.changed.emit()
	IronfieldAudio.instance.play_at(&"equip",actor.global_position,-5)
	return true

func unequip(slot: StringName) -> bool:
	if not can_change() or not slots.has(slot) or slots[slot] == null: return false
	var index := actor.inventory.slots.find(null)
	if index < 0: return false
	actor.inventory.slots[index] = slots[slot]
	slots[slot] = null
	refresh()
	actor.inventory.changed.emit()
	return true

func refresh() -> void:
	actor.combat.cancel()
	var weapon: ItemStack = slots[&"weapon"]
	actor.visual.equip_visual(&"WeaponSocket", weapon.definition().visual if weapon else null)
	var chest: ItemStack = slots[&"chest"]
	actor.visual.equip_visual(&"ArmorSocket", chest.definition().visual if chest else null)
	actor.combat.sequence.clear()
	if weapon:
		actor.combat.sequence.assign(weapon.definition().attacks)
	actor.combat.attack = actor.combat.sequence[0] if not actor.combat.sequence.is_empty() else null
	actor.stats.recalculate()
	if actor.mounts and actor.mounts.mounted:
		actor.visual.present(actor.velocity,actor.combat,actor.health,actor.title,0.0)
	changed.emit()

func to_inventory(slot: StringName, index: int, expected: ItemStack) -> bool:
	if not can_change() or not slots.has(slot) or slots[slot] != expected or expected == null: return false
	if index < 0 or index >= actor.inventory.slots.size(): return false
	var replacement: ItemStack = actor.inventory.slots[index]
	if replacement and (replacement.definition().equipment_slot != slot or replacement.definition().required_level > actor.progression.level): return false
	actor.inventory.slots[index] = expected
	slots[slot] = replacement
	refresh()
	actor.inventory.changed.emit()
	return true
