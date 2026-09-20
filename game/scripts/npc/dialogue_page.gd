class_name DialoguePage
extends Resource
@export_multiline var text: String
## Options: text, next (page index, -1 closes), action (talk/shop/close), min_level.
@export var responses: Array[Dictionary] = []
