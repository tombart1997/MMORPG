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

func _ready() -> void:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	var left := _panel(root, Vector2(22, 20), Vector2(310, 150))
	stats = _label(left, Vector2(14, 10), 19)
	hp = _bar(left, Vector2(14, 75), Color(0.56, 0.17, 0.12))
	xp = _bar(left, Vector2(14, 106), Color(0.53, 0.47, 0.22))
	var right := _panel(root, Vector2(-316, 20), Vector2(294, 168))
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT, true)
	encounters = _label(right, Vector2(14, 10), 17)
	var bottom := _panel(root, Vector2(22, -108), Vector2(760, 88))
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_LEFT, true)
	controls = _label(bottom, Vector2(14, 9), 16)
	message = _label(root, Vector2(26, 185), 18)
	message.add_theme_color_override("font_color", Color(1, 0.88, 0.58))

func _panel(parent: Control, offset: Vector2, dimensions: Vector2) -> Panel:
	var panel := Panel.new()
	panel.position = offset
	panel.size = dimensions
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
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
	encounters.text = "BRIARWOOD MARCH\n"
	for camp in zone.camps:
		var status := "%d alive" % camp.pack.living_count()
		if camp.remaining >= 0:
			status = "clear / %ds" % ceili(camp.remaining) if camp.remaining > 0 else "leave to respawn"
		encounters.text += "%s: %s\n" % [camp.camp_name, status]
	encounters.text += "Gold %d   Shards %d   Tonics %d" % [inventory.gold,
		inventory.count(&"moss_shard"), inventory.count(&"field_tonic")]
	controls.text = "WASD move  |  Mouse aim  |  LMB strike; click in recovery to chain\n"
	controls.text += "E gather nearby  |  Q tonic  |  Wheel zoom  |  Esc cursor  |  F3 cone\n"
	controls.text += "%s  [%d/3]  %s  |  Hits %d  |  Kills %d" % [player.combat.attack.display_name,
		maxi(1, player.combat.sequence_index + 1), player.combat.phase_name(), player.combat.swing_hits, progress.kills]
	message.text = zone.notice if zone.notice_time > 0 else ""
	if not player.health.is_alive():
		message.text = "You fell. R: return to waystone (keep XP and inventory)."
	elif player.global_position.distance_to(ZoneTerrain.START) < 4:
		message.text = "Waystone Refuge - rest to recover health. Follow the path to the mosslings."
	else:
		for drop in get_tree().get_nodes_in_group("loot"):
			if drop.can_collect(player):
				message.text = "E - gather nearby gold and items"
				break
