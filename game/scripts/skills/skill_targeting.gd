class_name SkillTargeting
extends RefCounted
static func line_clear(actor: ActorBody, origin: Vector3, point: Vector3) -> bool:
	var ray := PhysicsRayQueryParameters3D.create(origin + Vector3.UP, point + Vector3.UP, 1)
	return actor.get_world_3d().direct_space_state.intersect_ray(ray).is_empty()
static func validate(context: SkillContext) -> String:
	var skill := context.skill
	var actor := context.actor
	if skill.targeting == "selected":
		if not is_instance_valid(context.target) or not context.target.health.is_alive() or context.target.faction != actor.opponents: return "Select a living enemy."
		context.point = context.target.global_position
		if SafeArea.protects(actor) or SafeArea.protects(context.target): return "Sanctuary protects both sides."
	if skill.targeting in ["selected", "ground", "direction"]:
		if actor.global_position.distance_to(context.point) > skill.reach + 0.1: return "Out of range. Move closer first."
		if not line_clear(actor, actor.global_position, context.point): return "The way is obstructed."
	if skill.targeting in ["ground", "direction"]:
		var map := actor.get_world_3d().navigation_map
		var projected := NavigationServer3D.map_get_closest_point(map, context.point)
		if projected.distance_to(context.point) > 0.8: return "Choose traversable ground."
		var path := NavigationServer3D.map_get_path(map, actor.global_position, projected, true)
		if path.is_empty() or path[-1].distance_to(projected) > 0.7: return "No route to that ground."
		if skill.targeting == "direction":
			# A dash needs continuous navigable ground, not a path around an obstacle/gap.
			for i in 12:
				var sample := actor.global_position.lerp(projected, (i + 1) / 12.0)
				if NavigationServer3D.map_get_closest_point(map, sample).distance_to(sample) > 0.55: return "No clear footing for Heelturn."
		context.point = projected
	return ""
static func targets(context: SkillContext) -> Array[ActorBody]:
	var result: Array[ActorBody] = []
	var skill := context.skill
	if skill.shape == "self": return [context.actor]
	if skill.shape == "none": return result
	var center := context.point if skill.targeting == "ground" else context.actor.global_position
	for target: ActorBody in context.actor.get_tree().get_nodes_in_group(context.actor.opponents):
		if not target.health.is_alive() or SafeArea.protects(target) or SafeArea.protects(context.actor): continue
		if skill.shape == "single" and target != context.target: continue
		var offset := target.global_position - center
		if absf(offset.y) > 1.8: continue
		offset.y = 0
		var limit := skill.reach if skill.shape == "single" else skill.radius
		if offset.length() > limit: continue
		if skill.shape == "arc" and offset.length_squared() > 0.001 and context.direction.dot(offset.normalized()) < cos(deg_to_rad(skill.angle * 0.5)): continue
		if line_clear(context.actor, center, target.global_position): result.append(target)
	return result
