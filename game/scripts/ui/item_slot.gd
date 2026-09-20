class_name ItemSlot
extends Button
## Drag payload carries a checked instance reference, never copied authoritative state.
var player: ActorBody
var bag_index: int = -1
var equipment_slot: StringName

func stack() -> ItemStack:
	return player.inventory.slots[bag_index] if bag_index >= 0 else player.equipment.slots.get(equipment_slot)

func _get_drag_data(_position: Vector2) -> Variant:
	var instance := stack()
	if instance == null or not player.equipment.can_change(): return null
	var quantity := maxi(1, instance.quantity / 2) if Input.is_key_pressed(KEY_SHIFT) else instance.quantity
	var preview := Label.new()
	preview.text = instance.display_name() + " x%d" % quantity
	preview.modulate = Color(1, 0.86, 0.5)
	set_drag_preview(preview)
	return {"player": player, "index": bag_index, "equipment": equipment_slot, "stack": instance, "quantity": quantity}

func _can_drop_data(_position: Vector2, data: Variant) -> bool:
	if not data is Dictionary or data.get("player") != player or not data.get("stack") is ItemStack or not player.equipment.can_change(): return false
	var instance: ItemStack = data.stack
	if data.index >= 0 and player.inventory.slots[data.index] != instance: return false
	if data.index < 0 and player.equipment.slots.get(data.equipment) != instance: return false
	if bag_index >= 0:
		return data.index >= 0 or player.inventory.slots[bag_index] == null or player.inventory.slots[bag_index].definition().equipment_slot == data.equipment
	return data.index >= 0 and instance.definition().equipment_slot == equipment_slot and data.quantity == instance.quantity

func _drop_data(_position: Vector2, data: Variant) -> void:
	if not _can_drop_data(_position, data): return
	if bag_index >= 0:
		if data.index >= 0: player.inventory.move_slot(data.index, bag_index, data.stack, data.quantity)
		else: player.equipment.to_inventory(data.equipment, bag_index, data.stack)
	else: player.equipment.equip(data.index)
