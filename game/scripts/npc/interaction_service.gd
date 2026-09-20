class_name InteractionService
extends Node
## NPCs take precedence over loot. Nearest NPC wins; stable ID breaks equal distances.
var player: ActorBody
signal npc_requested(npc: WorldNPC)

func nearest_npc() -> WorldNPC:
	var nearest: WorldNPC
	var distance := INF
	for npc in get_tree().get_nodes_in_group("npcs"):
		if not npc.can_interact(player): continue
		var next: float = npc.global_position.distance_squared_to(player.global_position)
		if next < distance - 0.001 or (is_equal_approx(next, distance) and (nearest == null or String(npc.data.id) < String(nearest.data.id))):
			nearest = npc
			distance = next
	return nearest

func interact() -> bool:
	if player.ui_open: return true
	var npc := nearest_npc()
	if npc == null: return false
	npc_requested.emit(npc)
	return true
