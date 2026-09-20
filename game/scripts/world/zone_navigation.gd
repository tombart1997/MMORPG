class_name ZoneNavigation
extends NavigationRegion3D
var ready_for_paths: bool = false

func build(root: Node3D) -> void:
	var mesh := NavigationMesh.new()
	mesh.agent_radius = 0.5
	mesh.agent_height = 2.0
	mesh.agent_max_climb = 0.5
	mesh.agent_max_slope = 38
	mesh.cell_size = 0.25
	mesh.cell_height = 0.25
	mesh.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	mesh.geometry_collision_mask = 1
	var geometry := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(mesh, geometry, root)
	NavigationServer3D.bake_from_source_geometry_data(mesh, geometry)
	NavigationServer3D.map_set_use_async_iterations(get_world_3d().navigation_map, false)
	navigation_mesh = mesh
	NavigationServer3D.map_force_update(get_world_3d().navigation_map)
	ready_for_paths = true
