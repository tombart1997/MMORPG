class_name UpgradeDrop
extends Button
var panel: SmithPanel
func _can_drop_data(_position: Vector2, data: Variant) -> bool:
	return data is Dictionary and data.get("player") == panel.player and int(data.get("index", -1)) >= 0 and data.get("stack") is ItemStack and not panel.service.quote(data.stack).is_empty()
func _drop_data(_position: Vector2, data: Variant) -> void:
	if _can_drop_data(_position, data): panel.select_item(data.index, data.stack)
