class_name ForgeModelCatalogue
extends RefCounted
## New multi-image reconstructions and explicitly authored family derivatives.
static var scenes: Dictionary = {}
static var pending: Dictionary = {}

static func collect_ready() -> void:
	for key: String in pending.keys():
		var path: String = pending[key]
		var status := ResourceLoader.load_threaded_get_status(path)
		if status == ResourceLoader.THREAD_LOAD_LOADED:
			scenes[key] = ResourceLoader.load_threaded_get(path) as PackedScene
			ReviewedModels.scenes[path] = scenes[key]
			pending.erase(key)
		elif status == ResourceLoader.THREAD_LOAD_FAILED or status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			pending.erase(key)

static func prefetch(group: String, identity: StringName) -> void:
	var key := group+"/"+String(identity)
	if scenes.has(key) or pending.has(key): return
	var path := ReviewedModels.path_for("res://assets/generated/%s.glb" % key)
	if not ResourceLoader.exists(path): return
	if ResourceLoader.load_threaded_request(path,"PackedScene") == OK:
		pending[key] = path

static func scene_for(group: String, identity: StringName) -> PackedScene:
	var key := group+"/"+String(identity)
	if scenes.has(key):return scenes[key]
	if pending.has(key):
		var requested: String = pending[key]
		if ResourceLoader.load_threaded_get_status(requested) == ResourceLoader.THREAD_LOAD_LOADED:
			scenes[key] = ResourceLoader.load_threaded_get(requested) as PackedScene
			pending.erase(key)
			return scenes[key]
	var path := "res://assets/generated/%s.glb" % key
	if not ResourceLoader.exists(path):return null
	var started := Time.get_ticks_usec() if RuntimeCosts.enabled else 0
	scenes[key]=ReviewedModels.scene_for(path)
	if RuntimeCosts.enabled: RuntimeCosts.record(&"asset_load",started)
	return scenes[key]
