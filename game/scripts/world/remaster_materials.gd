class_name RemasterMaterials
extends RefCounted
## One painted palette, shared by all repeated world geometry.
static var textures: Dictionary = {}
static var materials: Dictionary = {}
static var camera_fade_materials: Dictionary = {}

static func camera_clearance(source: StandardMaterial3D, near_distance: float = 5.0, far_distance: float = 7.5) -> StandardMaterial3D:
	var key:="%d:%.2f:%.2f" % [source.get_instance_id(),near_distance,far_distance]
	if camera_fade_materials.has(key): return camera_fade_materials[key]
	var material:=source.duplicate() as StandardMaterial3D
	material.distance_fade_mode=BaseMaterial3D.DISTANCE_FADE_PIXEL_DITHER
	material.distance_fade_min_distance=near_distance
	material.distance_fade_max_distance=far_distance
	camera_fade_materials[key]=material
	return material

static func texture(index: int) -> Texture2D:
	if textures.has(index): return textures[index]
	var atlas := load("res://assets/remaster/painted_materials.png") as Texture2D
	var source := atlas.get_image()
	var side := source.get_width()/3
	var tile := source.get_region(Rect2i((index%3)*side,(index/3)*side,side,side))
	tile.generate_mipmaps()
	textures[index] = ImageTexture.create_from_image(tile)
	return textures[index]

static func surface(index: int, tint: Color = Color.WHITE) -> StandardMaterial3D:
	var key := "%d_%s" % [index,tint.to_html()]
	if materials.has(key): return materials[key]
	var material := StandardMaterial3D.new()
	material.albedo_texture = texture(index)
	material.albedo_color = tint
	material.roughness = .95
	material.metallic_specular = .08
	material.uv1_triplanar = true
	material.uv1_world_triplanar = true
	material.uv1_scale = Vector3.ONE*.7
	materials[key] = material
	return material

static func terrain() -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.shader = load("res://assets/remaster/terrain.gdshader")
	for i in 6: material.set_shader_parameter("layer%d" % i,texture(i))
	return material
