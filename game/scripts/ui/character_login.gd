extends Control
const CLASSES := ["Ironvow", "Threadseer", "Cinderhand", "Fenstrider"]
const COLORS := [Color("bccbd6"), Color("9a91d7"), Color("d89361"), Color("83ad86")]
const STORIES := ["Stand firm. Answer with steel.", "Follow the unseen threads of the March.", "Carry the fire through the long night.", "Walk the wild paths beyond the refuge."]
var selected: int = 0
var preview: Node3D
var heading: Label
var story: Label
var name_input: LineEdit
var message: Label
var saved: OptionButton
var roster: Array = []
var dragging: bool = false
var roster_path: String = "user://characters.cfg"

func _ready() -> void:
	IronfieldAudio.instance.enter_region("briarwood")
	theme = PaintedTheme.get_theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := Panel.new()
	background.add_theme_stylebox_override("panel", PaintedTheme.frame(20))
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for edge in ["left", "right", "top", "bottom"]: margin.add_theme_constant_override("margin_" + edge, 38)
	add_child(margin)
	var layout := HBoxContainer.new()
	layout.add_theme_constant_override("separation", 38)
	margin.add_child(layout)
	var left := VBoxContainer.new()
	left.custom_minimum_size.x = 450
	left.add_theme_constant_override("separation", 14)
	layout.add_child(left)
	var brand := Label.new()
	brand.text = "I R O N F I E L D"
	brand.add_theme_font_size_override("font_size", 36)
	brand.modulate = Color("dbc59a")
	left.add_child(brand)
	var subtitle := Label.new()
	subtitle.text = "BRIARWOOD MARCH  /  LOCAL CHARACTER LOGIN"
	subtitle.add_theme_font_size_override("font_size", 13)
	left.add_child(subtitle)
	heading = Label.new()
	heading.add_theme_font_size_override("font_size", 30)
	left.add_child(heading)
	story = Label.new()
	left.add_child(story)
	var choices := HBoxContainer.new()
	left.add_child(choices)
	for i in CLASSES.size():
		var button := Button.new()
		button.text = CLASSES[i]
		button.pressed.connect(_select.bind(i))
		choices.add_child(button)
	var arrows := HBoxContainer.new()
	left.add_child(arrows)
	_button(arrows, "< Previous class", func(): _select(posmod(selected-1,4)))
	_button(arrows, "Next class >", func(): _select((selected+1)%4))
	name_input = LineEdit.new()
	name_input.placeholder_text = "Character name"
	name_input.max_length = 24
	left.add_child(name_input)
	_button(left, "Create character & enter the March", _create)
	message = Label.new()
	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message.custom_minimum_size = Vector2(450,48)
	left.add_child(message)
	var note := Label.new()
	note.text = "Four class identities. All currently share the sword combo
and Turnwarden prototype skills. More class kits to come."
	note.modulate = Color("a8b2ba")
	note.add_theme_font_size_override("font_size", 13)
	note.add_theme_constant_override("line_spacing", 2)
	note.add_theme_constant_override("paragraph_spacing", 2)
	left.add_child(note)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(spacer)
	saved = OptionButton.new()
	left.add_child(saved)
	var config := ConfigFile.new()
	if config.load(roster_path) == OK:
		var entries: Variant = config.get_value("characters", "roster", [])
		if entries is Array:
			for entry in entries:
				if entry is Dictionary and entry.get("name") is String and entry.get("class") in CLASSES and entry.get("path") is String and entry.path.begins_with("user://character_"):
					roster.append(entry)
	for entry in roster: saved.add_item(entry.name + " / " + entry.class)
	if FileAccess.file_exists("user://progression.json"): saved.add_item("Traveler / existing save")
	var resume := _button(left, "Enter with selected character", _resume)
	resume.disabled = saved.item_count == 0
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.add_child(right)
	var container := SubViewportContainer.new()
	container.stretch = true
	container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(container)
	container.gui_input.connect(_preview_input)
	var viewport := SubViewport.new()
	viewport.size = Vector2i(550,550)
	viewport.own_world_3d = true
	container.add_child(viewport)
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("18120f")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("bac9da")
	env.ambient_light_energy = .7
	environment.environment = env
	viewport.add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-30,-35,0)
	sun.light_energy = 1.7
	viewport.add_child(sun)
	var camera := Camera3D.new()
	camera.position = Vector3(0,1.3,2.8)
	viewport.add_child(camera)
	camera.look_at(Vector3(0,1,0))
	preview = load("res://scenes/visuals/humanoid.tscn").instantiate()
	viewport.add_child(preview)
	preview.rotation.y = PI
	var platform := MeshInstance3D.new()
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = .8
	cylinder.bottom_radius = .9
	cylinder.height = .12
	platform.mesh = cylinder
	var stone := StandardMaterial3D.new()
	stone.albedo_color = Color("35434a")
	platform.material_override = stone
	platform.position.y = -.08
	viewport.add_child(platform)
	var hint := Label.new()
	hint.text = "DRAG TO ROTATE  /  SELECT A CLASS TO BEGIN"
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.modulate = Color("dbc59a")
	right.add_child(hint)
	_select(0)

func _button(parent: Node, title: String, action: Callable) -> Button:
	var button := Button.new()
	button.text = title
	button.custom_minimum_size.y = 29
	button.pressed.connect(action)
	parent.add_child(button)
	return button

func _select(index: int) -> void:
	selected = index
	heading.text = CLASSES[index]
	heading.modulate = COLORS[index]
	story.text = STORIES[index]
	preview.rotation.y = PI + .25
	for mesh: MeshInstance3D in preview.find_children("*", "MeshInstance3D", true, false):
		if mesh.mesh == null: continue
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.mesh.surface_get_material(surface) as StandardMaterial3D
			if source:
				var material := source.duplicate() as StandardMaterial3D
				material.albedo_color *= COLORS[index]
				mesh.set_surface_override_material(surface, material)

func _preview_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT: dragging = event.pressed
	if event is InputEventMouseMotion and dragging: preview.rotation.y += event.relative.x * .012

func _create() -> void:
	var title := name_input.text.strip_edges()
	if title.length() < 2:
		message.text = "Choose a name of 2 to 24 characters."
		return
	for entry in roster:
		if entry.name.to_lower() == title.to_lower():
			message.text = "That name already exists. Select it below to continue."
			return
	var entry := {"name": title, "class": CLASSES[selected], "path": "user://character_%d_%d.json" % [Time.get_unix_time_from_system(), Time.get_ticks_usec()]}
	roster.append(entry)
	var config := ConfigFile.new()
	config.set_value("characters", "roster", roster)
	if config.save(roster_path) != OK:
		roster.pop_back()
		message.text = "Could not save the character. Please try again."
		return
	_enter(entry)

func _resume() -> void:
	if saved.selected < 0: return
	if saved.selected < roster.size(): _enter(roster[saved.selected])
	else: _enter({"name":"Traveler", "class":"Ironvow", "path":"user://progression.json"})

func _enter(entry: Dictionary) -> void:
	var region := "briarwood"
	if FileAccess.file_exists(entry.path):
		var save: Variant = JSON.parse_string(FileAccess.get_file_as_string(entry.path))
		if save is Dictionary and save.get("region") == "cinderfall": region = "cinderfall"
	entry["region"] = region
	get_tree().root.set_meta("character_login", entry)
	get_tree().change_scene_to_file("res://scenes/cinderfall_zone.tscn" if region == "cinderfall" else "res://scenes/outdoor_zone.tscn")
