class_name QuestActions
extends VBoxContainer
var player: ActorBody
var npc: WorldNPC
var message: Label

func refresh() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	if not is_instance_valid(npc) or player.quests == null: return
	for quest in QuestCatalog.all().values():
		if quest.giver == npc.data.id and player.quests.available(quest):
			var button := Button.new()
			button.text = "[!] Accept: " + quest.title
			button.tooltip_text = player.quests.describe(quest)
			button.pressed.connect(func(): player.quests.accept(quest.id, npc); refresh())
			add_child(button)
		elif quest.turn_in == npc.data.id and player.quests.ready(quest):
			var button := Button.new()
			button.text = "[?] Complete: " + quest.title
			button.pressed.connect(func():
				var error := player.quests.claim(quest.id, npc)
				if message: message.text = error if not error.is_empty() else "Quest complete. Rewards received."
				refresh())
			add_child(button)
