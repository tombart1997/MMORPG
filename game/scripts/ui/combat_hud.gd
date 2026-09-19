class_name CombatHUD
extends CanvasLayer
var player: ActorBody
var pack: AggroGroup
var text: Label

func _ready() -> void:
	var panel := PanelContainer.new()
	panel.position = Vector2(18, 18)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(panel)
	text = Label.new()
	text.add_theme_font_size_override("font_size", 18)
	text.add_theme_color_override("font_color", Color(0.92, 0.95, 1))
	panel.add_child(text)
	var crosshair := Label.new()
	crosshair.text = "+"
	crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(crosshair)

func _process(_delta: float) -> void:
	var message := "Approach the red pack and strike to alert it."
	if not player.health.is_alive():
		message = "YOU FELL — press R to restart the encounter."
	elif pack.living_count() == 0:
		message = "PACK DEFEATED — press R for another fight."
	text.text = ("  IRONFIELD | combat sandbox\n"
		+ "  HP: %d / %d    Pack: %d / 6    Aggro: %s\n"
		+ "  Sword: %s    Hits this swing: %d    Total hits: %d\n"
		+ "  WASD move | Mouse aim | LMB attack | Wheel zoom\n"
		+ "  Esc release mouse | Click capture | R restart | F3 combat cone\n"
		+ "  %s  ") % [player.health.current, player.health.maximum,
		pack.living_count(), "ALERT" if pack.has_target() else "idle",
		player.combat.phase_name(), player.combat.swing_hits, player.combat.total_hits, message]
