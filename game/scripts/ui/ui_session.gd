class_name UISession
extends Node
## One modal at a time. Buttons close through this owner; their click stays consumed.
var player: ActorBody
var inventory_panel: InventoryPanel
var active: Control
var world_map: WorldMapPanel
var quick_bar: Control
var journal: QuestJournal

func open_panel(panel: Control) -> void:
	if active and active != panel: IronfieldAudio.instance.stop_voice()
	if active and active != panel: active.hide()
	if player.mounts and (panel is TownPanel or panel is SmithPanel): player.mounts.dismount("Dismounted to talk")
	active = panel
	active.show()
	player.ui_open = true
	if player.skills: player.skills.cancel_aim()
	if player.world_interaction: player.world_interaction.cancel()
	_clear_attack_input()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func close() -> void:
	IronfieldAudio.instance.stop_voice()
	if active: active.hide()
	active = null
	player.ui_open = false
	_clear_attack_input()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _clear_attack_input() -> void:
	if player.skills: player.skills.clear_buffer()
	for child in player.get_children():
		if child is PlayerController: child.stop_auto_attack()

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("world_map"):
		if active == world_map: close()
		else: open_panel(world_map)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("journal"):
		if active == journal: close()
		else: open_panel(journal); journal.refresh()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("inventory"):
		if active == inventory_panel: close()
		else:
			open_panel(inventory_panel)
			inventory_panel.refresh()
		get_viewport().set_input_as_handled()
	elif active and event.is_action_pressed("release_mouse"):
		close()
		get_viewport().set_input_as_handled()
	elif active and event.is_action_pressed("pickup"):
		get_viewport().set_input_as_handled()
	elif active and event is InputEventMouseButton and not active.get_global_rect().grow_individual(0,25,0,0).has_point(event.position):
		# Inventory drag release must reach the quick slots outside the modal.
		if active == inventory_panel and quick_bar and quick_bar.get_global_rect().has_point(event.position): return
		get_viewport().set_input_as_handled()

func _unhandled_input(event: InputEvent) -> void:
	if active and event is InputEventMouseButton: get_viewport().set_input_as_handled()

func _process(_delta: float) -> void:
	if active and (not player.health.is_alive() or ((active is TownPanel or active is SmithPanel) and (not is_instance_valid(active.npc) or not active.npc.can_interact(player)))): close()
