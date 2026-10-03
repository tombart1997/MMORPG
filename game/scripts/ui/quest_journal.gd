class_name QuestJournal
extends PanelContainer
var player: ActorBody
var text: Label
func _ready() -> void:
	position = Vector2(820, 160)
	custom_minimum_size = Vector2(400, 430)
	var column := VBoxContainer.new()
	add_child(column)
	var title := Label.new()
	title.text = "BRIARWOOD JOURNAL [J]"
	column.add_child(title)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(372, 355)
	column.add_child(scroll)
	text = Label.new()
	text.custom_minimum_size.x = 355
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	scroll.add_child(text)
	var close := Button.new()
	close.text = "Close"
	close.pressed.connect(player.ui_session.close)
	column.add_child(close)
	player.quests.changed.connect(refresh)
	WindowChrome.install(self, "Quest journal", player.ui_session.close)
	refresh()
	hide()
func refresh() -> void:
	text.text = ""
	for quest in QuestCatalog.all().values():
		if player.quests.states.has(String(quest.id)) or player.quests.available(quest): text.text += player.quests.describe(quest) + "\n\n"
