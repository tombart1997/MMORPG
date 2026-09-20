class_name WorldInteraction
extends Node
## One replaceable intent: terrain travel, approach/interact, or melee focus.
var actor: ActorBody
var camera: Camera3D
var zone: Node3D
var target: Node3D
var kind: StringName
var repath_time: float = 0
var ring: MeshInstance3D
var selected_enemy: ActorBody
var hover_text: String = ""

func _ready() -> void:
	ring = MeshInstance3D.new()
	var mesh := TorusMesh.new()
	mesh.inner_radius = 0.55
	mesh.outer_radius = 0.62
	mesh.rings = 24
	mesh.ring_segments = 6
	ring.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.95, 0.67, 0.24)
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring.material_override = material
	zone.add_child(ring)
	ring.hide()

func _unhandled_input(event: InputEvent) -> void:
	if actor.ui_open or not actor.health.is_alive(): return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if actor.skills and actor.skills.armed: actor.skills.handle_world_click(event.position)
		else: command(WorldPicker.pick(camera, event.position))
		get_viewport().set_input_as_handled()
	if event.is_action_pressed("release_mouse"):
		if actor.skills: actor.skills.cancel_aim()
		cancel()

func cancel() -> void:
	target = null
	kind = &""
	selected_enemy = null
	actor.navigation.cancel()

func command(hit: Dictionary) -> void:
	if hit.is_empty() or actor.ui_open or not actor.health.is_alive(): return
	if actor.skills and actor.skills.busy():
		if hit.kind == &"enemy": selected_enemy = hit.target
		return
	cancel()
	kind = hit.kind
	if kind == &"terrain":
		if hit.get("normal", Vector3.UP).y < 0.7: return
		if not actor.navigation.command(hit.position): zone.announce(actor.navigation.failure)
	else:
		target = hit.target
		if kind == &"enemy": selected_enemy = target
		repath_time = 0

func _physics_process(delta: float) -> void:
	if not actor.health.is_alive(): cancel()
	if actor.ui_open or (actor.skills and (actor.skills.busy() or actor.skills.armed)): return
	if kind == &"terrain": return
	if not is_instance_valid(target) or target.is_queued_for_deletion():
		target = null
		actor.navigation.cancel()
		return
	if target is ActorBody and not target.health.is_alive(): cancel(); return
	var distance := actor.global_position.distance_to(target.global_position)
	var range_limit := 2.1
	if target is WorldNPC: range_limit = target.data.interaction_range - 0.35
	elif target is LootPickup: range_limit = 1.9
	elif target is ActorBody and actor.combat.attack: range_limit = minf(2.1, actor.combat.attack.reach - 0.35)
	var ray := PhysicsRayQueryParameters3D.create(actor.global_position + Vector3.UP, target.global_position + Vector3.UP, 1)
	var visible_target := actor.get_world_3d().direct_space_state.intersect_ray(ray).is_empty()
	if distance <= range_limit and visible_target:
		actor.navigation.cancel()
		if actor.combat.is_attacking():
			return
		var direction := target.global_position - actor.global_position
		actor.rotation.y = atan2(-direction.x, -direction.z)
		if kind == &"npc":
			zone.interaction.npc_requested.emit(target)
			target = null
		elif kind == &"loot":
			if not target.collect(actor): zone.announce(actor.inventory.last_pickup)
			target = null
		elif kind == &"enemy":
			if actor.combat.attack == null: zone.announce("Equip a weapon to attack."); cancel()
			else: actor.combat.request_attack()
	else:
		repath_time -= delta
		if repath_time <= 0 and not actor.combat.is_attacking():
			repath_time = 0.6
			if not actor.navigation.command(target.global_position):
				zone.announce(actor.navigation.failure)
				cancel()

func _process(_delta: float) -> void:
	ring.visible = is_instance_valid(selected_enemy) and selected_enemy.health.is_alive()
	if ring.visible: ring.global_position = selected_enemy.global_position + Vector3.UP * 0.07
	if actor.ui_open: hover_text = ""; return
	var hit := WorldPicker.pick(camera, get_viewport().get_mouse_position())
	hover_text = ""
	if not hit.is_empty():
		match hit.kind:
			&"npc": hover_text = "Talk: " + hit.target.data.display_name
			&"enemy": hover_text = "Attack: " + hit.target.title
			&"loot": hover_text = "Pick up: " + hit.target.display_text()
