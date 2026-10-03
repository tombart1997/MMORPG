class_name PaintedTheme
extends RefCounted
## Shared lacquer/bronze skin. Artwork is sampled once; corners never stretch.
const ATLAS_PATH := "res://assets/ui/painted_atlas.png"
const INK := Color("100c0b")
const IVORY := Color("d4c5a3")
const GOLD := Color("9e8050")
static var cached: Theme
static var textures: Dictionary = {}

static func inventory_icon(index: int) -> Texture2D:
	var key := "item_%d" % index
	if textures.has(key): return textures[key]
	var atlas := load("res://assets/ui/painted_items.png") as Texture2D
	var tile := AtlasTexture.new()
	tile.atlas = atlas
	var cell := Vector2(atlas.get_width()/3.0,atlas.get_height()/3.0)
	tile.region = Rect2(Vector2(index%3,index/3)*cell,cell)
	tile.filter_clip = true
	textures[key] = tile
	return tile

static func painted_icon(original: Texture2D) -> Texture2D:
	if original == null: return null
	var icons := {"sword":0,"armor":1,"cap":2,"boots":3,"consumable":4,"material":5,"horse":6}
	var id := original.resource_path.get_file().get_basename()
	return inventory_icon(icons[id]) if icons.has(id) else original

static func ability(index: int) -> Texture2D:
	var atlas := load("res://assets/ui/painted_abilities.png") as Texture2D
	var tile := AtlasTexture.new()
	tile.atlas = atlas
	var cell := Vector2(atlas.get_width()/3.0,atlas.get_height()/2.0)
	tile.region = Rect2(Vector2(index%3,index/3)*cell,cell)
	tile.filter_clip = true
	return tile

static func artwork(part: String) -> Texture2D:
	if textures.has(part): return textures[part]
	var atlas := load(ATLAS_PATH) as Texture2D
	if atlas == null: return null
	var cells := {"portrait": Vector2i(0,0), "panel": Vector2i(1,0), "ring": Vector2i(0,1), "flames": Vector2i(1,1)}
	var cell: Vector2i = cells[part]
	var source := atlas.get_image()
	var side := source.get_width() / 2
	var picture := source.get_region(Rect2i(cell * side, Vector2i(side,side)))
	if part == "panel": picture.resize(192,192,Image.INTERPOLATE_LANCZOS)
	var texture := ImageTexture.create_from_image(picture)
	textures[part] = texture
	return texture

static func frame(padding: float = 9, tint: Color = Color.WHITE) -> StyleBoxTexture:
	if not textures.has("frame"):
		var picture := artwork("panel").get_image()
		picture.resize(96,96,Image.INTERPOLATE_LANCZOS)
		textures["frame"] = ImageTexture.create_from_image(picture)
	var style := StyleBoxTexture.new()
	style.texture = textures["frame"]
	style.set_texture_margin_all(32)
	style.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	style.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	style.set_content_margin_all(padding)
	style.modulate_color = tint
	return style

static func slot(tint: Color = Color.WHITE) -> StyleBoxTexture:
	# Small controls use the painted center and narrow edge strips, not four
	# oversized dragon corners. This is runtime atlas assembly, cached once.
	if not textures.has("slot"):
		var source := artwork("panel").get_image()
		var tile := source.get_region(Rect2i(66,66,60,60))
		tile.blit_rect(source,Rect2i(66,2,60,3),Vector2i.ZERO)
		tile.blit_rect(source,Rect2i(66,185,60,3),Vector2i(0,57))
		tile.blit_rect(source,Rect2i(2,66,3,60),Vector2i.ZERO)
		tile.blit_rect(source,Rect2i(185,66,3,60),Vector2i(57,0))
		textures["slot"] = ImageTexture.create_from_image(tile)
	var style := StyleBoxTexture.new()
	style.texture = textures["slot"]
	style.set_texture_margin_all(3)
	style.set_content_margin_all(4)
	style.modulate_color = tint
	return style

static func inset(color: Color = INK, edge: Color = Color("584329")) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.border_color = edge
	style.set_border_width_all(1)
	style.set_content_margin_all(4)
	style.shadow_color = Color(0,0,0,.7)
	style.shadow_size = 1
	return style

static func get_theme() -> Theme:
	if cached: return cached
	cached = Theme.new()
	cached.default_font_size = 12
	for type in ["Label", "Button", "LineEdit", "ItemList", "CheckBox", "OptionButton", "RichTextLabel", "TooltipLabel"]:
		cached.set_color("font_color",type,IVORY)
		cached.set_color("font_shadow_color",type,Color("080504"))
		cached.set_constant("shadow_offset_x",type,1)
		cached.set_constant("shadow_offset_y",type,1)
	for type in ["Panel", "PanelContainer", "PopupPanel", "TooltipPanel"]:
		cached.set_stylebox("panel",type,frame())
	for type in ["Button", "OptionButton", "MenuButton"]:
		cached.set_stylebox("normal",type,slot())
		cached.set_stylebox("hover",type,slot(Color(1.25,1.14,.94)))
		cached.set_stylebox("pressed",type,slot(Color(.72,.58,.44)))
		cached.set_stylebox("disabled",type,slot(Color(.48,.46,.42)))
		cached.set_stylebox("focus",type,inset(Color.TRANSPARENT,GOLD))
		cached.set_color("font_disabled_color",type,Color("6b6253"))
		cached.set_color("font_hover_color",type,Color("f0d6a2"))
	for type in ["LineEdit", "TextEdit", "ItemList"]:
		cached.set_stylebox("normal",type,slot(Color(.7,.66,.61)))
		cached.set_stylebox("panel",type,slot(Color(.7,.66,.61)))
		cached.set_stylebox("focus",type,inset(Color.TRANSPARENT,GOLD))
	cached.set_stylebox("selected", "ItemList", inset(Color("382519"),GOLD))
	cached.set_stylebox("selected_focus", "ItemList", inset(Color("382519"),GOLD))
	var groove := inset()
	groove.set_content_margin_all(0)
	cached.set_stylebox("background","ProgressBar",groove)
	cached.set_stylebox("fill","ProgressBar",inset(Color("761d20"),Color("a04b36")))
	for type in ["HScrollBar", "VScrollBar"]:
		cached.set_stylebox("scroll",type,inset())
		for state in ["grabber","grabber_highlight","grabber_pressed"]:
			cached.set_stylebox(state,type,inset(Color("63462d"),GOLD))
	for state in ["tab_selected", "tab_hovered", "tab_unselected", "tab_disabled"]:
		cached.set_stylebox(state,"TabContainer",frame(5))
	cached.set_stylebox("panel","TabContainer",frame())
	for type in ["HBoxContainer","VBoxContainer"]: cached.set_constant("separation",type,4)
	return cached

static func section(parent: Node, title: String) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var label := Label.new()
	label.text = "◆  " + title
	label.add_theme_color_override("font_color",GOLD)
	label.add_theme_font_size_override("font_size",11)
	row.add_child(label)
	var rule := HSeparator.new()
	rule.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rule.add_theme_stylebox_override("separator",inset(Color("3d2c1c"),Color("3d2c1c")))
	row.add_child(rule)

static func value_row(parent: Node, caption: String) -> Label:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var label := Label.new()
	label.text = caption
	label.add_theme_font_size_override("font_size",10)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(label)
	var field := PanelContainer.new()
	field.custom_minimum_size.x = 64
	var recess := slot(Color(.65,.60,.53))
	recess.content_margin_top = 0
	recess.content_margin_bottom = 0
	field.add_theme_stylebox_override("panel",recess)
	row.add_child(field)
	var value := Label.new()
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value.add_theme_font_size_override("font_size",10)
	field.add_child(value)
	return value
