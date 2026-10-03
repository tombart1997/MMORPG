class_name IronfieldAudio
extends Node
## Persistent, bounded audio mixer. Every recording is shipped; no runtime network.
static var instance: IronfieldAudio
var cues: Dictionary = {}
var events: Dictionary = {}
var pool: Array[AudioStreamPlayer3D] = []
var pool_index := 0
var music: Array[AudioStreamPlayer] = []
var ambience: Array[AudioStreamPlayer] = []
var voice: AudioStreamPlayer
var speaker: Node3D
var voice_key := ""
var region := ""
var muted := false
var music_slot := 0
var music_tween: Tween
var duck := 0.0
var serial := 0

func _ready() -> void:
	instance = self
	process_priority = 80
	for bus_name in ["Music","Ambience","Effects","Voice"]:
		if AudioServer.get_bus_index(bus_name) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count-1,bus_name)
			AudioServer.set_bus_send(AudioServer.bus_count-1,"Master")
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Master"),-4)
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Effects"),-4)
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Ambience"),-7)
	var settings := ConfigFile.new()
	if settings.load("user://audio.cfg") == OK: muted = bool(settings.get_value("audio","muted",false))
	AudioServer.set_bus_mute(0,muted)
	for i in 2:
		var channel := AudioStreamPlayer.new();channel.bus = "Music";add_child(channel);music.append(channel)
		var atmosphere := AudioStreamPlayer.new();atmosphere.bus = "Ambience";add_child(atmosphere);ambience.append(atmosphere)
	voice = AudioStreamPlayer.new();voice.bus = "Voice";add_child(voice)
	for i in 16:
		var sound := AudioStreamPlayer3D.new()
		sound.bus = "Effects";sound.unit_size = 6;sound.max_distance = 32;sound.attenuation_filter_cutoff_hz = 7000
		add_child(sound);pool.append(sound)
	_load_cue(&"swing",["sfx/swing_0","sfx/swing_1"])
	_load_cue(&"hit",["sfx/hit_flesh"])
	_load_cue(&"metal",["sfx/hit_metal_0","sfx/hit_metal_1","sfx/hit_metal_2"])
	_load_cue(&"step",["sfx/step_0","sfx/step_1","sfx/step_2"])
	_load_cue(&"hoof",["sfx/hoof_0","sfx/hoof_1","sfx/hoof_2"])
	for name_value in [&"coins",&"pickup",&"equip",&"mount"]: _load_cue(name_value,["sfx/"+String(name_value)])
	for name_value in [&"thunder",&"fire",&"spirit",&"sun",&"spin",&"sprint"]: _load_cue(name_value,["skill_"+String(name_value)])

func _load_cue(id: StringName,paths: Array) -> void:
	var sounds: Array[AudioStream] = []
	for path: String in paths: sounds.append(load("res://assets/audio/"+path+".ogg") as AudioStream)
	cues[id] = sounds

func play_at(id: StringName,point: Vector3,level_db: float = 0) -> void:
	if not cues.has(id): return
	events[id] = int(events.get(id,0))+1
	if muted or DisplayServer.get_name() == "headless": return
	var camera := get_viewport().get_camera_3d()
	if camera and camera.global_position.distance_squared_to(point) > 1024: return
	var sound := pool[pool_index]
	pool_index = (pool_index+1)%pool.size()
	sound.stop();sound.global_position = point
	var choices: Array = cues[id]
	serial += 1
	sound.stream = choices[serial%choices.size()]
	sound.volume_db = level_db
	sound.pitch_scale = 1.0 if id == &"mount" else 1+float(serial%7-3)*.025
	sound.play()

func enter_region(next: String) -> void:
	if next == region: return
	region = next
	if music_tween and music_tween.is_valid(): music_tween.kill()
	var old := music_slot
	music_slot = 1-music_slot
	for pair in [[music,"music_"],[ambience,"ambience_"]]:
		var channels: Array = pair[0]
		var stream := load("res://assets/audio/"+pair[1]+region+".ogg") as AudioStreamOggVorbis
		stream.loop = true
		channels[music_slot].stream = stream
		channels[music_slot].volume_db = -45
		if DisplayServer.get_name() != "headless": channels[music_slot].play()
	music_tween = create_tween().set_parallel(true)
	for channels in [music,ambience]:
		music_tween.tween_property(channels[music_slot],"volume_db",-3.0,2.0)
		music_tween.tween_property(channels[old],"volume_db",-45.0,2.0)
	music_tween.chain().tween_callback(func(): music[old].stop();ambience[old].stop())

func speak(npc: Node3D,page: int = -1) -> void:
	var key := String(npc.data.id)+("_greeting" if page < 0 else "_page%d" % page)
	if speaker == npc and voice_key == key and voice.playing: return
	stop_voice()
	var path := "res://assets/audio/voices/"+key+".ogg"
	if not ResourceLoader.exists(path): return
	speaker = npc;voice_key = key
	voice.stream = load(path)
	voice.volume_db = 0
	if DisplayServer.get_name() != "headless": voice.play()
	events[&"voice"] = int(events.get(&"voice",0))+1

func stop_voice() -> void:
	if voice: voice.stop()
	speaker = null;voice_key = ""

func _process(delta: float) -> void:
	if speaker and not is_instance_valid(speaker): stop_voice()
	duck = move_toward(duck,11.0 if voice.playing else 0.0,delta*18)
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"),-10-duck)

func _exit_tree() -> void:
	shutdown()
	instance = null

func shutdown() -> void:
	if music_tween and music_tween.is_valid(): music_tween.kill()
	for channel in music+ambience:
		channel.stop();channel.stream = null
	for sound in pool:
		sound.stop();sound.stream = null
	stop_voice()
	if voice: voice.stream = null
	cues.clear()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F8:
		muted = not muted
		AudioServer.set_bus_mute(0,muted)
		var settings := ConfigFile.new();settings.set_value("audio","muted",muted);settings.save("user://audio.cfg")
		get_viewport().set_input_as_handled()
