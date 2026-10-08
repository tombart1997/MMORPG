class_name CreatureMaterials
extends RefCounted
## Shared species surfaces retain the authored grain and normals, with neutralized coat color.
const SURFACE = preload("res://assets/shaders/creature_surface.gdshader")
const COATS := {
	&"red_wolf": "974f37", &"blue_wolf": "4b6c91", &"grey_wolf": "777e84",
	&"meadow_wolf": "967651", &"thicket_wolf": "635844", &"frost_wolf": "e8edf1",
	&"dusk_stalker": "403d50", &"moonfang": "9ba9cc", &"bloodfang": "782e26",
	&"ember_hound": "8e3b1f", &"bristle_boar": "8e6744", &"ironhide_boar": "58616a",
	&"mire_boar": "66563e", &"blacktusk": "302c29", &"obsidian_boar": "342e3e",
	&"reed_spider": "937647", &"copper_spider": "b6763d", &"venom_spider": "718842",
	&"widow_spider": "442932", &"silk_matron": "8f5178", &"glass_spider": "819eac",
	&"slate_guardian": "647581", &"cairn_sentinel": "9c8970", &"cairn_colossus": "7c7267",
	&"ancient_warden": "a49674", &"rift_sentinel": "665e92",
	&"cinder_wisp": "ef8136", &"grave_wisp": "83aeb2", &"storm_wisp": "8f9ddb", &"ash_wisp": "db7546",
	&"young": "91a84e", &"grown": "776449", &"ironback": "626b59",
	&"road_bandit": "967651", &"ash_bandit": "a45c38", &"hollow_raider": "586e8e", &"exile_captain": "78597f"
}
static var cache: Dictionary = {}

static func apply(model: Node3D, data: EnemyData, individual: int = 0) -> void:
	var base := Color(COATS.get(data.id,"89735e"))
	for mesh: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		for surface in mesh.mesh.get_surface_count():
			var source := (mesh.get_active_material(surface) if data.family == &"bandit" else mesh.mesh.surface_get_material(surface)) as StandardMaterial3D
			if source == null: continue
			var name_value := source.resource_name
			# Stable generated species fallbacks retain their atlas and eye detail.
			# Tinting the diffuse color avoids replacing the authored atlas with a
			# procedural coat intended for the older separate body materials.
			if name_value.begins_with("Forge_") and data.family in [&"wolf",&"boar"]:
				var atlas_key := "atlas:%s:%s:%d" % [data.id,name_value,individual%3]
				if not cache.has(atlas_key):
					var tinted := source.duplicate() as StandardMaterial3D
					tinted.albedo_color = source.albedo_color * base.lightened(.48+float(individual%3)*.025)
					cache[atlas_key] = tinted
				mesh.set_surface_override_material(surface,cache[atlas_key])
				continue
			var clothing := data.family == &"bandit" and ("Cloth" in name_value or "Leather" in name_value)
			if not (clothing or "Body" in name_value or "Mane" in name_value or "CarvedJade" in name_value or "Bark" in name_value or "ForestJade" in name_value): continue
			var key := "%s:%s:%d" % [data.id,name_value,individual%3]
			if not cache.has(key):
				var material := ShaderMaterial.new();material.shader = SURFACE
				var coat := base.lightened(float(individual%3)*.025)
				if "Mane" in name_value or "BarkShadow" in name_value: coat = coat.darkened(.42)
				if "CarvedJade" in name_value or "ForestJade" in name_value: coat = coat.lightened(.12)
				material.set_shader_parameter("coat",coat)
				material.set_shader_parameter("marking",base.darkened(.60))
				material.set_shader_parameter("underside",base.lightened(.38 if data.family in [&"wolf",&"boar"] else .16))
				material.set_shader_parameter("pattern",float(hash(data.id)%17))
				var kind := 1.0 if data.family == &"spider" else 2.0 if data.family == &"stonekin" else 4.0 if data.family == &"wisp" else 3.0 if data.id in [&"young",&"grown",&"ironback"] else 0.0
				material.set_shader_parameter("surface_kind",kind)
				material.set_shader_parameter("roughness_value",.97 if clothing else .52 if kind == 1.0 else .70 if kind == 4.0 else .91 if kind >= 2.0 else .86)
				material.set_shader_parameter("grain_average",.12 if "Mane" in name_value else .26 if "Jade" in name_value and not "Body" in name_value else .18)
				if source.albedo_texture: material.set_shader_parameter("grain_texture",source.albedo_texture)
				else:
					var image := Image.create(1,1,false,Image.FORMAT_RGB8);image.fill(Color(.18,.18,.18))
					material.set_shader_parameter("grain_texture",ImageTexture.create_from_image(image))
				material.set_shader_parameter("has_normal",source.normal_enabled and source.normal_texture != null)
				if source.normal_texture: material.set_shader_parameter("normal_texture",source.normal_texture)
				cache[key] = material
			mesh.set_surface_override_material(surface,cache[key])
