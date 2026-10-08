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
var target_label: Label
var target_hp: ProgressBar
var location_label: Label
var currency: Label
var combat_target: ActorBody
var hp_value: Label
var xp_value: Label
var notice_panel: Panel
var local_log: EventLog
var notice_flame: PaintedArt

func _ready() -> void:
	player.combat.hit_landed.connect(func(target): combat_target = target as ActorBody)
	player.health.damaged.connect(func(_amount, source): combat_target = source as ActorBody)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = PaintedTheme.get_theme()
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
	var map_panel := WorldMapPanel.new()
	map_panel.player = player
	map_panel.theme = inventory_panel.theme
	root.add_child(map_panel)
	player.ui_session.world_map = map_panel
	var minimap := MapCanvas.new()
	minimap.player = player
	minimap.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	minimap.position = Vector2(-190,18)
	minimap.size = Vector2(170,170)
	root.add_child(minimap)
	var map_ring := PaintedArt.new()
	map_ring.part = "ring"
	map_ring.quiet = true
	map_ring.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	map_ring.position = Vector2(-204,4)
	map_ring.size = Vector2(198,198)
	root.add_child(map_ring)
	for i in 2:
		var zoom_button := Button.new()
		zoom_button.text = "+" if i == 0 else "−"
		root.add_child(zoom_button)
		zoom_button.position = Vector2(-193 if i == 0 else -42,153)
		zoom_button.set_anchors_preset(Control.PRESET_TOP_RIGHT,true)
		zoom_button.size = Vector2(23,23)
		zoom_button.tooltip_text = "Zoom in" if i == 0 else "Zoom out"
		zoom_button.pressed.connect(func(): minimap.zoom = clampf(minimap.zoom + (0.5 if i == 0 else -0.5),1.5,5.0))
	var skill_bar := SkillBar.new()
	skill_bar.player = player
	skill_bar.theme = inventory_panel.theme
	root.add_child(skill_bar)
	player.ui_session.quick_bar = skill_bar
	var left := _panel(root, Vector2(74, 28), Vector2(252, 76))
	stats = _label(left, Vector2(46, 9), 12)
	hp = _bar(left, Vector2(46, 29), Color("801c22"))
	hp.size = Vector2(190, 13)
	hp_value = _label(left, Vector2(46,28),10)
	hp_value.size = Vector2(190,14)
	hp_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	xp = _bar(left, Vector2(46, 49), Color("74603a"))
	xp.size = Vector2(190, 5)
	xp_value = _label(left, Vector2(46,57),9)
	var portrait := PaintedArt.new()
	portrait.part = "portrait"
	portrait.round_portrait = true
	portrait.position = Vector2(24,29)
	portrait.size = Vector2(76,76)
	root.add_child(portrait)
	var ring := PaintedArt.new()
	ring.part = "ring"
	ring.position = Vector2(7,12)
	ring.size = Vector2(111,111)
	root.add_child(ring)
	local_log = EventLog.new()
	local_log.player = player
	root.add_child(local_log)
	var right := _panel(root, Vector2(-316, 20), Vector2(294, 168))
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT, true)
	encounters = _label(right, Vector2(14, 10), 17)
	var bottom := _panel(root, Vector2(22, -124), Vector2(365, 104))
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_LEFT, true)
	controls = _label(bottom, Vector2(12, 8), 13)
	notice_panel = _panel(root, Vector2(20, 130), Vector2(310, 74))
	message = _label(notice_panel, Vector2(12, 9), 12)
	message.size = Vector2(286,56)
	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message.add_theme_color_override("font_color", Color(1, 0.88, 0.58))
	notice_flame = PaintedArt.new()
	notice_flame.position = Vector2(256,-20)
	notice_flame.size = Vector2(66,32)
	notice_panel.add_child(notice_flame)
	target_label = _label(root, Vector2(-140, 16), 12)
	target_label.set_anchors_preset(Control.PRESET_CENTER_TOP, true)
	target_label.size = Vector2(280, 20)
	target_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	target_label.add_theme_color_override("font_shadow_color", Color(0,0,0,.9))
	target_label.add_theme_constant_override("shadow_offset_x", 1)
	target_label.add_theme_constant_override("shadow_offset_y", 1)
	target_hp = _bar(root, Vector2(-140, 37), Color(.75,.18,.12))
	target_hp.set_anchors_preset(Control.PRESET_CENTER_TOP, true)
	target_hp.size = Vector2(280, 10)
	var plaque := _panel(root, Vector2(-206,188),Vector2(202,48))
	plaque.set_anchors_preset(Control.PRESET_TOP_RIGHT,true)
	location_label = _label(plaque, Vector2(8, 6), 11)
	location_label.add_theme_font_size_override("font_size",12)
	location_label.size=Vector2(186,36)
	location_label.clip_text = true
	location_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	currency = _label(root, Vector2(-234,-79), 11)
	currency.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT,true)
	var menus := HBoxContainer.new()
	root.add_child(menus)
	menus.position = Vector2(-232,-45)
	menus.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT,true)
	for entry in [["I · Pack",inventory_panel,7],["J · Quests",journal,8],["M · Map",map_panel,8]]:
		var button := Button.new()
		button.text = entry[0].left(1)
		button.tooltip_text = entry[0]
		button.icon = PaintedTheme.inventory_icon(entry[2])
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width",22)
		button.custom_minimum_size = Vector2(67,27)
		button.pressed.connect(func(): player.ui_session.open_panel(entry[1]))
		menus.add_child(button)

func _panel(parent: Control, offset: Vector2, dimensions: Vector2) -> Panel:
	var panel := Panel.new()
	panel.position = offset
	panel.size = dimensions
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.add_theme_stylebox_override("panel", PaintedTheme.frame())
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
	style.border_color = color.lightened(.22)
	style.border_width_top = 1
	bar.add_theme_stylebox_override("fill", style)
	parent.add_child(bar)
	return bar

func _process(_delta: float) -> void:
	var progress := player.progression
	var inventory := player.inventory
	stats.tooltip_text = player.title
	stats.text = "%s · Lv.%02d" % [String(player.get_meta("class_identity", "Ironvow")), progress.level]
	hp_value.text = "%d / %d" % [player.health.current,player.health.maximum]
	xp_value.text = "EXP  %d / %d" % [progress.xp,progress.xp_required()]
	stats.tooltip_text = "Experience %d / %d" % [progress.xp, progress.xp_required()]
	currency.text = "%d gold    /    %d tonics" % [inventory.gold,inventory.count(&"field_tonic")]
	var target: ActorBody = player.world_interaction.selected_enemy
	if (not is_instance_valid(target) or not target.health.is_alive()) and is_instance_valid(combat_target):
		if combat_target.health.is_alive() and player.global_position.distance_to(combat_target.global_position) < 30:
			target = combat_target
	if not is_instance_valid(target) and player.farming:
		var body := player.farming.encounter.body
		if body.global_position.distance_to(player.global_position)<13: target=body
	target_label.visible=is_instance_valid(target) and target.health.is_alive()
	target_hp.visible=target_label.visible
	if target_label.visible:
		target_label.text="%s   %d / %d" % [target.title, target.health.current, target.health.maximum]
		target_hp.max_value=target.health.maximum
		target_hp.value=target.health.current
	location_label.text=player.map_state.region.display_name.to_upper() + "\n" + player.map_state.subarea()
	location_label.visible=not debug_visible
	controls.get_parent().visible=debug_visible
	currency.visible=not debug_visible
	hp.max_value = player.health.maximum
	hp.value = player.health.current
	xp.max_value = progress.xp_required()
	xp.value = progress.xp
	encounters.visible = debug_visible
	encounters.get_parent().visible = debug_visible
	if debug_visible:
		encounters.text = "BRIARWOOD MARCH\n"
		for camp in zone.camps:
			if camp.global_position.distance_to(player.global_position) > 40: continue
			var status := "%d alive" % camp.pack.living_count()
			if camp.remaining >= 0:
				status = "clear / %ds" % ceili(camp.remaining) if camp.remaining > 0 else "leave to respawn"
			encounters.text += "%s: %s\n" % [camp.camp_name, status]
		encounters.text += "Gold %d   Shards %d   Tonics %d" % [inventory.gold,
			inventory.count(&"moss_shard"), inventory.count(&"field_tonic")]
		if player.farming:
			var fracture := player.farming.encounter
			encounters.text += "\nBriarwake: wave %d / defenders %d / return %.0fs" % [fracture.next_wave, fracture.living_defenders(), fracture.remaining]
		controls.text = "LMB travel / interact / target | RMB orbit\nWASD move | Space auto on/off | 1-6 skills\nI bag | J quests | M map | E interact\nQ/F consumables | H mount\nF5/F9 save/load | F3 debug | F6 Turnwarden\nGold %d | Tonics %d" % [inventory.gold, inventory.count(&"field_tonic")]
	local_log.visible = not debug_visible
	notice_flame.visible = zone.notice_time > 0 or not player.health.is_alive()
	if debug_visible: controls.text += "   |   %s / Hits %d / Kills %d" % [player.combat.phase_name(), player.combat.swing_hits, progress.kills]
	message.text = zone.notice if zone.notice_time > 0 else player.world_interaction.hover_text
	if not player.health.is_alive():
		message.text = "You fell. R: return to waystone (keep XP and inventory)."
	elif not player.world_interaction.hover_text.is_empty() and not player.ui_open:
		message.text = player.world_interaction.hover_text
	elif zone.interaction.nearest_npc() != null and not player.ui_open:
		message.text = "E - talk to " + zone.interaction.nearest_npc().data.display_name
	elif zone.notice_time <= 0 and SafeArea.protects(player):
		message.text = FirstHourGuidance.hint(player)
	elif zone.notice_time <= 0:
		message.text = FirstHourGuidance.hint(player)
		for drop in get_tree().get_nodes_in_group("loot"):
			if drop.can_collect(player):
				message.text = "E - pick up nearest entry"
				break

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F3:
		debug_visible = not debug_visible
