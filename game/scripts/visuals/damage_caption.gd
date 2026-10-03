class_name DamageCaption
extends Label3D

static func show_hit(target: Node3D, amount: float, source: Node3D) -> void:
	if not is_instance_valid(target) or not target.is_inside_tree(): return
	var caption := DamageCaption.new()
	var heavy := amount >= 70.0
	caption.text = str(roundi(amount))
	caption.font_size = 32 if heavy else 27
	caption.pixel_size = 0.00125
	caption.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	caption.no_depth_test = true
	caption.fixed_size = true
	caption.modulate = Color("ff4949") if source is ActorBody and source.faction == &"players" else Color("ff9d64")
	caption.outline_modulate = Color("351118")
	caption.outline_size = 4
	caption.position = target.global_position + Vector3(randf_range(-0.22, 0.22), 1.75, 0)
	target.get_tree().current_scene.add_child(caption)
	var start := caption.position
	var side := -1.0 if randi() % 2 == 0 else 1.0
	var tween := caption.create_tween().set_parallel(true)
	tween.tween_property(caption, "position", start + Vector3(side * 0.35, 0.65, 0), 0.65).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(caption, "modulate:a", 0.0, 0.30).set_delay(0.35)
	tween.chain().tween_callback(caption.queue_free)
