class_name WorldAssetKit
extends RefCounted
## Cache imported authored meshes, baking the GLB root transform for MultiMesh use.
static var meshes: Dictionary = {}

static func mesh_for(kind: String) -> ArrayMesh:
	if meshes.has(kind): return meshes[kind]
	var path := "res://assets/generated/world/%s.glb" % kind
	var scene := ReviewedModels.scene_for(path)
	var source := scene.instantiate() as Node3D
	var combined := ArrayMesh.new()
	var parts := source.find_children("*","MeshInstance3D",true,false)
	for part: MeshInstance3D in parts:
		var transform_value := part.transform
		var ancestor := part.get_parent()
		while ancestor is Node3D:
			transform_value = ancestor.transform * transform_value
			ancestor = ancestor.get_parent()
		var preserve_lods := parts.size() == 1 and transform_value.is_equal_approx(Transform3D.IDENTITY)
		if preserve_lods: combined = part.mesh.duplicate() as ArrayMesh
		for i in part.mesh.get_surface_count():
			var material := part.get_active_material(i).duplicate() as StandardMaterial3D
			material.vertex_color_use_as_albedo = true
			# Broad leaf cards can cross the view while their vertices are several
			# metres from the camera. Fade canopy across the mounted camera arm.
			if kind.begins_with("tree"): material = RemasterMaterials.camera_clearance(material,8.0,11.0)
			elif kind == "shrub": material = RemasterMaterials.camera_clearance(material)
			if kind.begins_with("rock") or kind.begins_with("cliff"): material = RemasterMaterials.camera_clearance(material)
			if preserve_lods:
				combined.surface_set_material(i,material)
			else:
				var surface := SurfaceTool.new()
				surface.begin(Mesh.PRIMITIVE_TRIANGLES)
				surface.append_from(part.mesh,i,transform_value)
				surface.set_material(material)
				surface.commit(combined)
	source.free()
	meshes[kind] = combined
	return combined
