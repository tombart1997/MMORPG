@tool
extends EditorScenePostImport
## Respect glTF vertex albedo on repairs as well as imported PBR textures.
func _post_import(scene: Node) -> Object:
	for part: MeshInstance3D in scene.find_children("*","MeshInstance3D",true,false):
		if not part.mesh is ArrayMesh: continue
		for surface in part.mesh.get_surface_count():
			if (part.mesh.surface_get_format(surface) & Mesh.ARRAY_FORMAT_COLOR) == 0: continue
			var material := part.mesh.surface_get_material(surface) as StandardMaterial3D
			if material:
				material = material.duplicate() as StandardMaterial3D
				material.vertex_color_use_as_albedo = true
				part.mesh.surface_set_material(surface,material)
	return scene
