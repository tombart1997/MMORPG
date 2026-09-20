class_name ZoneHUD
extends CanvasLayer
var zone: Node3D
var player: ActorBody
var stats: Label
var encounters: Label
var controls: Label
var message: Label
var hp: ProgressBar
var xp: ProgressBar
var debug_visible: bool = false
var inventory_panel: InventoryPanel
var town_panel: TownPanel
var smith_panel: SmithPanel

func _ready() -> void:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	inventory_panel = InventoryPanel.new()
	inventory_panel.player = player
	inventory_panel.zone = zone
	root.add_child(inventory_panel)
	player.ui_session = UISession.new()
	player.ui_session.player = player
	player.ui_session.inventory_panel = inventory_panel
	add_child(player.ui_session)
	town_panel = TownPanel.new()
	town_panel.player = player
	town_panel.session = player.ui_session
	town_panel.theme = inventory_panel.theme
	root.add_child(town_panel)
	smith_panel = SmithPanel.new()
	smith_panel.player = player
	smith_panel.theme = inventory_panel.theme
	root.add_child(smith_panel)
	var journal := QuestJournal.new()
	journal.player = player
	journal.theme = inventory_panel.theme
	root.add_child(journal)
	player.ui_session.journal = journal
	zone.interaction.npc_requested.connect(func(npc):
		if npc.data.role == &"smith": smith_panel.open_npc(npc)
		else: town_panel.open_npc(npc))
	var skill_bar := SkillBar.new()
	skill_bar.player = player
	skill_bar.theme = inventory_panel.theme
	root.add_child(skill_bar)
	var left := _panel(root, Vector2(22, 20), Vector2(310, 150))
	stats = _label(left, Vector2(14, 10), 19)
	hp = _bar(left, Vector2(14, 75), Color(0.56, 0.17, 0.12))
	xp = _bar(left, Vector2(14, 106), Color(0.53, 0.47, 0.22))
	var right := _panel(root, Vector2(-316, 20), Vector2(294, 168))
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT, true)
	encounters = _label(right, Vector2(14, 10), 17)
	var bottom := _panel(root, Vector2(22, -124), Vector2(365, 104))
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_LEFT, true)
	controls = _label(bottom, Vector2(12, 8), 13)
	message = _label(root, Vector2(26, 185), 18)
	message.add_theme_color_override("font_color", Color(1, 0.88, 0.58))

func _panel(parent: Control, offset: Vector2, dimensions: Vector2) -> Panel:
	var panel := Panel.new()
	panel.position = offset
	panel.size = dimensions
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.10, 0.08, 0.9)
	style.border_color = Color(0.43, 0.37, 0.22)
	style.set_border_width_all(2)
	style.set_corner_radius_all(4)
	panel.add_theme_stylebox_override("panel", style)
	parent.add_child(panel)
	return panel

func _label(parent: Control, offset: Vector2, font_size: int) -> Label:
	var label := Label.new()
	label.position = offset
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color(0.88, 0.86, 0.73))
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	return label

func _bar(parent: Control, offset: Vector2, color: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.position = offset
	bar.size = Vector2(280, 23)
	bar.show_percentage = false
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = color
	bar.add_theme_stylebox_override("fill", style)
	parent.add_child(bar)
	return bar

func _process(_delta: float) -> void:
	var progress := player.progression
	var inventory := player.inventory
	stats.text = "TRAVELER  |  Level %d\nHP %d / %d    XP %d / %d" % [progress.level,
		player.health.current, player.health.maximum, progress.xp, progress.xp_required()]
	hp.max_value = player.health.maximum
	hp.value = player.health.current
	xp.max_value = progress.xp_required()
	xp.value = progress.xp
	encounters.visible = debug_visible
	encounters.get_parent().visible = debug_visible
	encounters.text = "BRIARWOOD MARCH\n"
	for camp in zone.camps:
		var status := "%d alive" % camp.pack.living_count()
		if camp.remaining >= 0:
			status = "clear / %ds" % ceili(camp.remaining) if camp.remaining > 0 else "leave to respawn"
		encounters.text += "%s: %s\n" % [camp.camp_name, status]
	encounters.text += "Gold %d   Shards %d   Tonics %d" % [inventory.gold,
		inventory.count(&"moss_shard"), inventory.count(&"field_tonic")]
	controls.text = "LMB travel / interact / target | RMB orbit\nWASD move | Space basic | 1-6 skills\nI bag | J quests | E interact | Q tonic\nF5/F9 save/load | F3 debug | F6 Turnwarden\nGold %d | Tonics %d" % [inventory.gold, inventory.count(&"field_tonic")]
	if debug_visible: controls.text += "   |   %s / Hits %d / Kills %d" % [player.combat.phase_name(), player.combat.swing_hits, progress.kills]
	message.text = zone.notice if zone.notice_time > 0 else player.world_interaction.hover_text
	if not player.health.is_alive():
		message.text = "You fell. R: return to waystone (keep XP and inventory)."
	elif not player.world_interaction.hover_text.is_empty() and not player.ui_open:
		message.text = player.world_interaction.hover_text
	elif zone.interaction.nearest_npc() != null and not player.ui_open:
		message.text = "E - talk to " + zone.interaction.nearest_npc().data.display_name
	elif zone.notice_time <= 0 and SafeArea.protects(player):
		message.text = "Waystone Refuge - sanctuary. Visit Mara, then follow the road through the north gate."
	elif zone.notice_time <= 0:
		for drop in get_tree().get_nodes_in_group("loot"):
			if drop.can_collect(player):
				message.text = "E - pick up nearest entry"
				break

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F3:
		debug_visible = not debug_visible
