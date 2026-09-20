class_name WorldClickable
extends Area3D
## Shared pick proxy: terrain=layer 1, physical actors=2, interaction proxies=4.
var target: Node3D
var kind: StringName
var label: Label3D

static func attach(node: Node3D, category: StringName, height: float = 1.7) -> WorldClickable:
	var proxy := WorldClickable.new()
	proxy.target = node
	proxy.kind = category
	proxy.collision_layer = 4
	proxy.collision_mask = 0
	var collision := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.45 if category != &"loot" else 0.28
	shape.height = maxf(height, shape.radius * 2)
	collision.shape = shape
	collision.position.y = height / 2
	proxy.add_child(collision)
	node.add_child(proxy)
	proxy.add_to_group("clickables")
	return proxy

func valid() -> bool:
	if not is_instance_valid(target) or target.is_queued_for_deletion(): return false
	if target is ActorBody: return target.health.is_alive()
	if target is LootPickup: return not target.claimed
	return true
