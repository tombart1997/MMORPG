class_name DialogueSession
extends RefCounted
var npc: WorldNPC
var player: ActorBody
var page: int = 0

func valid() -> bool:
	return is_instance_valid(npc) and npc.can_interact(player) and page >= 0 and page < npc.data.pages.size()

func text() -> String:
	return npc.data.pages[page].text if valid() else ""

func options() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if not valid(): return result
	for response in npc.data.pages[page].responses:
		if player.progression.level >= int(response.get("min_level", 1)): result.append(response)
	return result

func choose(index: int) -> StringName:
	var choices := options()
	if index < 0 or index >= choices.size(): return &"invalid"
	var choice: Dictionary = choices[index]
	var action := StringName(choice.get("action", "talk"))
	if action == &"talk":
		var next := int(choice.get("next", -1))
		if next < 0 or next >= npc.data.pages.size(): return &"close"
		page = next
	return action
