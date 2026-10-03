class_name HumanoidPaint
extends RefCounted
## Reuse painted surfaces without altering the established player skin or animation data.
static var textures: Dictionary = {}
static var materials: Dictionary = {}

static func texture(index: int) -> Texture2D:
	if textures.has(index): return textures[index]
	var image:=preload("res://assets/characters/townfolk_atlas.png").get_image()
	var side:=image.get_width()/3
	var tile:=image.get_region(Rect2i(index%3*side,index/3*side,side,side))
	tile.generate_mipmaps()
	textures[index]=ImageTexture.create_from_image(tile)
	return textures[index]

static func surface(source: StandardMaterial3D) -> StandardMaterial3D:
	var key:=source.get_instance_id()
	if materials.has(key): return materials[key]
	var painted:=source.duplicate() as StandardMaterial3D
	var name:=String(source.resource_name)
	if "Steel" in name:
		painted.albedo_texture=texture(6)
		painted.albedo_color=Color(.80,.86,.86) if "Dark" in name else Color(.96,1,1)
		painted.metallic=.12
		painted.roughness=.83
		painted.metallic_specular=.15
	elif "Brass" in name:
		painted.albedo_texture=texture(5)
		painted.albedo_color=Color("b5a27c")
		painted.metallic=.15
		painted.roughness=.81
		painted.metallic_specular=.13
	elif "Leather" in name:
		painted.albedo_texture=texture(4)
		painted.albedo_color=Color("706457")
		painted.roughness=.95
	elif "Undercloth" in name:
		painted.albedo_texture=texture(3)
		painted.albedo_color=Color("898b90")
		painted.roughness=.96
	elif "Cloth" in name:
		painted.albedo_texture=texture(2)
		painted.albedo_color=Color("572d28")
		painted.roughness=.96
	elif "Skin" in name: painted.roughness=.85
	materials[key]=painted
	return painted

static func apply(model: Node3D) -> void:
	for mesh: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		for slot in mesh.mesh.get_surface_count():
			var source:=mesh.get_active_material(slot) as StandardMaterial3D
			if source: mesh.set_surface_override_material(slot,surface(source))
