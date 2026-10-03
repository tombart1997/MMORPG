class_name PlayerMount
extends Node
## Mounts share the actor's navigation, feet position and terrain collider.
## Ownership persists; riding and combat lockout are transient.
var actor: ActorBody
var owned: Array[StringName] = []
var selected: StringName = &""
var mounted: bool = false
var definition: MountData
var model: Node3D
var combat_lock: float = 0
const ATTACK_SPEED_MULTIPLIER := 1.35
var hit_chains: Dictionary = {}
var combat_time: float = 0

func _ready() -> void:
	process_priority = -10 # Pose the saddle before the rider samples its skeleton.
	actor.health.damaged.connect(func(_amount, _source):
		combat_lock = 5)
	actor.health.died.connect(func(_source): dismount())

func _process(delta: float) -> void:
	combat_time += delta
	for id in hit_chains.keys():
		if combat_time - float(hit_chains[id].time) > 1.5: hit_chains.erase(id)
	combat_lock = maxf(0, combat_lock - delta)
	if mounted:
		if not actor.health.is_alive() or actor.skills and actor.skills.busy(): dismount()
		elif model and model.has_method("travel"):
			model.travel(actor.velocity, delta)
			if model.has_method("saddle_offset"):
				actor.visual.position = Vector3(0,definition.rider_height,0)+model.saddle_offset()

func unlock(index: int) -> bool:
	if not actor.equipment.can_change() or index < 0 or index >= actor.inventory.slots.size(): return false
	var stack: ItemStack = actor.inventory.slots[index]
	if stack == null: return false
	var item := stack.definition()
	var mount := MountData.find(item.mount_unlock)
	if mount == null or owned.has(mount.id) or actor.progression.level < item.required_level: return false
	if not actor.inventory.remove_count(item.id, 1): return false
	owned.append(mount.id)
	selected = mount.id
	actor.actions.report("%s unlocked! Close your pack and press H to ride." % mount.display_name)
	return true

func unavailable() -> String:
	if mounted: return ""
	if selected == &"" or not owned.has(selected): return "Horse: Mara sells a bridle, level 3 · 240 gold"
	if not actor.health.is_alive(): return "Revive first"
	if actor.ui_open: return "Close the open panel"
	if not actor.is_on_floor(): return "Find firm ground"
	if actor.combat.is_attacking() or actor.skills and actor.skills.busy(): return "Finish your action"
	if combat_lock > 0: return "Under attack — wait %.0fs" % ceilf(combat_lock)
	for foe: Node3D in get_tree().get_nodes_in_group("enemies"):
		if foe is ActorBody and foe.health.is_alive() and foe.combat.is_attacking() and foe.global_position.distance_to(actor.global_position) < 8:
			return "Enemies too close"
		if foe is ActorBody and foe.health.is_alive() and foe.global_position.distance_to(actor.global_position) < 10:
			for child in foe.get_children():
				if child is EnemyBrain and child.pack.has_target() and child.pack.target == actor: return "Lose your pursuers before mounting"
	return ""

func toggle() -> bool:
	if mounted: dismount("Dismounted"); return true
	var reason := unavailable()
	if not reason.is_empty(): actor.actions.report(reason); return false
	definition = MountData.find(selected)
	if definition == null or definition.visual == null: return false
	# Baked agents have a .5 m radius / 2 m height. Do not exceed that envelope.
	var shape := CapsuleShape3D.new()
	shape.radius = 0.38
	shape.height = 2.0
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = shape
	query.transform = Transform3D(Basis.IDENTITY, actor.global_position + Vector3.UP * 1.02)
	query.collision_mask = 9
	query.exclude = [actor.get_rid()]
	if not actor.get_world_3d().direct_space_state.intersect_shape(query, 1).is_empty():
		actor.actions.report("More room needed to mount")
		return false
	actor.body_collider.set_deferred("shape", shape)
	actor.body_collider.set_deferred("position", Vector3(0,1,0))
	mounted = true
	IronfieldAudio.instance.play_at(&"mount",actor.global_position,-4)
	model = definition.visual.instantiate()
	actor.add_child(model)
	if model is TrailHorse: model.hoofstep.connect(func(point: Vector3): IronfieldAudio.instance.play_at(&"hoof",point,-5))
	actor.visual.position.y = definition.rider_height
	actor.visual.present(actor.velocity,actor.combat,actor.health,actor.title,0.0)
	actor.actions.report("Mounted — Space: faster attacks · two hits knock enemies back · H dismount")
	return true

func record_hit(target: ActorBody, serial: int, reach: float) -> void:
	if not mounted or not is_instance_valid(target) or not target.health.is_alive(): return
	var id := target.get_instance_id()
	var previous: Dictionary = hit_chains.get(id, {})
	var consecutive := not previous.is_empty() and int(previous.serial) == serial - 1 and combat_time - float(previous.time) <= 1.5
	if consecutive:
		hit_chains.erase(id)
		var direction := target.global_position - actor.global_position
		direction.y = 0
		if direction.length_squared() < .001: direction = -actor.global_basis.z
		var distance := maxf(2.8, reach + 1.4 - direction.length())
		target.combat.cancel()
		target.statuses.push(direction, distance, .22)
		for child in target.get_children():
			if child is EnemyBrain: child.stagger = .4
	else:
		hit_chains[id] = {"serial": serial, "time": combat_time}

func dismount(message: String = "") -> void:
	if not mounted: return
	mounted = false
	hit_chains.clear()
	if is_instance_valid(model): model.queue_free()
	model = null
	actor.visual.position = Vector3.ZERO
	var shape := CapsuleShape3D.new()
	shape.radius = 0.34
	shape.height = 1.8
	actor.body_collider.set_deferred("shape", shape)
	actor.body_collider.set_deferred("position", Vector3(0, 0.9, 0))
	if not message.is_empty(): actor.actions.report(message)

func snapshot() -> Dictionary:
	var ids: Array = []
	for id in owned: ids.append(String(id))
	return {"owned": ids, "selected": String(selected)}

static func valid_snapshot(data: Variant) -> bool:
	if not data is Dictionary or not data.get("owned") is Array or not data.get("selected") is String: return false
	var unique: Array = []
	for id in data.owned:
		if not id is String or id.is_empty() or unique.has(id) or MountData.find(StringName(id)) == null: return false
		unique.append(id)
	return data.selected == "" or unique.has(data.selected)

func restore(data: Dictionary) -> void:
	dismount()
	owned.clear()
	for id in data.owned: owned.append(StringName(id))
	selected = StringName(data.selected)
	combat_lock = 0
