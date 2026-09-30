class_name PlayerMap
extends Node
var actor: ActorBody
var region: MapRegionData = preload("res://data/maps/briarwood.tres")
var discoveries: Dictionary = {}
var elapsed: float = 0

func _process(delta: float) -> void:
	elapsed += delta
	if elapsed < .25: return
	elapsed = 0
	if not actor.health.is_alive(): return
	for landmark in region.landmarks:
		if known(landmark): continue
		var point: Vector3 = landmark.position
		if actor.global_position.distance_to(point) > float(landmark.radius): continue
		if landmark.get("sight_required", false) and not SkillTargeting.line_clear(actor, actor.global_position, point): continue
		var key := String(region.id)
		if not discoveries.has(key): discoveries[key] = []
		discoveries[key].append(landmark.id)
		actor.actions.report("Discovered: " + String(landmark.name))

func known(landmark: Dictionary) -> bool:
	return landmark.get("known", false) or discoveries.get(String(region.id), []).has(landmark.id)

func subarea() -> String:
	var nearest := INF
	var title := "Waystone Road"
	for landmark in region.landmarks:
		if not known(landmark): continue
		var distance := actor.global_position.distance_to(landmark.position)
		if distance < float(landmark.radius) and distance < nearest:
			nearest = distance
			title = landmark.name
	return title

func markers() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for landmark in region.landmarks:
		if known(landmark): result.append({"position":landmark.position, "label":landmark.name, "glyph":"◇", "color":Color("b7a66c")})
	# Town services are known. Quest indicators reflect actual accepted/available state.
	for npc: WorldNPC in get_tree().get_nodes_in_group("npcs"):
		var glyph := "S" if npc.data.role == &"smith" else ("$" if npc.data.role == &"merchant" else "•")
		var quest := actor.quests.marker(npc.data.id).strip_edges() if actor.quests else ""
		if quest in ["[!]", "[?]"]: glyph = quest.substr(1,1)
		result.append({"service":true, "position":npc.global_position, "label":npc.data.display_name + " · " + String(npc.data.role), "glyph":glyph, "color":Color("e0ce8d")})
	return result

static func valid_snapshot(data: Variant) -> bool:
	if not data is Dictionary: return false
	var registry: Dictionary = {}
	for definition in MapRegionData.regions(): registry[String(definition.id)] = definition
	for id in data:
		if not registry.has(id) or not data[id] is Array: return false
		var allowed: Array = []
		for landmark in registry[id].landmarks: allowed.append(landmark.id)
		var unique: Array = []
		for landmark_id in data[id]:
			if not landmark_id is String or not allowed.has(landmark_id) or unique.has(landmark_id): return false
			unique.append(landmark_id)
	return true
