@tool
extends EditorScenePostImport
## Keep the authored coat tint and black points when importing the horse GLB.
func _post_import(scene: Node) -> Object:
	for node: MeshInstance3D in scene.find_children("*","MeshInstance3D",true,false):
		if node.mesh == null: continue
		for surface in node.mesh.get_surface_count():
			var material := node.mesh.surface_get_material(surface) as StandardMaterial3D
			var colors: PackedColorArray = node.mesh.surface_get_arrays(surface)[Mesh.ARRAY_COLOR]
			if material and colors.size()>0:
				material.vertex_color_use_as_albedo=true
	return scene
