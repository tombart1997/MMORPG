extends "res://tests/combat_smoke.gd"
## Render the actual assets, mounted cuts and mixed audio in the production scene.
var world: Node3D
var player: ActorBody
var controller: PlayerController
var soundscape: Node
var output := "res://.local/presentation_review"
var recorder: AudioEffectCapture
var audio_frames := PackedVector2Array()

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output+"/"+label+".png")

func drain_audio() -> void:
	if recorder and recorder.get_frames_available() > 0: audio_frames.append_array(recorder.get_buffer(recorder.get_frames_available()))

func close_view(point: Vector3,target: Vector3,label: String) -> void:
	var names: Dictionary = {}
	for name_label: Label3D in world.find_children("*","Label3D",true,false):
		names[name_label] = name_label.layers;name_label.layers = 2
	var camera := Camera3D.new()
	camera.cull_mask = 1
	world.add_child(camera);camera.global_position = point;camera.look_at(target);camera.fov = 40;camera.current = true
	for node in world.get_children():
		if node is CanvasLayer: node.visible = false
	await frames(3);await capture(label)
	camera.queue_free();controller.rig.camera.current = true
	for name_label in names:
		if is_instance_valid(name_label): name_label.layers = names[name_label]
	for node in world.get_children():
		if node is CanvasLayer: node.visible = true

func _run() -> void:
	soundscape = root.get_node("GameAudio")
	var args := OS.get_cmdline_user_args()
	var index := args.find("--label")
	if index >= 0 and index+1 < args.size(): output += "/"+args[index+1]
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name() != "headless":
		Engine.max_fps = 60
		recorder = AudioEffectCapture.new();recorder.buffer_length = 30
		AudioServer.add_bus_effect(0,recorder)
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false;root.add_child(world);current_scene = world
	await frames(12);player = world.player
	for child in player.get_children():
		if child is PlayerController: controller = child
	for actor: ActorBody in get_nodes_in_group("enemies"):
		for child in actor.get_children():
			if child is EnemyBrain: child.set_physics_process(false)
		actor.global_position += Vector3(0,0,-25) # Keep close-up review views unobstructed.
	player.global_position = Vector3(14,.1,-28)
	player.rotation.y = 0
	player.health.maximum = 10000;player.health.current = 10000
	controller.rig.distance = 5;controller.rig.yaw = 2.4;controller.rig.pitch = -.30
	await frames(12)
	await close_view(player.global_position+Vector3(.08,1.68,-.62),player.global_position+Vector3(0,1.67,0),"hero_face")
	var drops: Array[LootPickup] = []
	for i in range(5):
		var drop := LootPickup.new()
		if i == 0: drop.coins = 160
		else: drop.item = ItemCatalog.get_item([&"cairnwarden_sword",&"wakecleaver",&"ember_fang",&"rift_cleaver"][i-1])
		world.add_child(drop);drop.global_position = player.global_position+Vector3(-1.6+i*.8,0,-1.6)
		drops.append(drop)
	await frames(5)
	check(drops[0].mesh.get_meta("physical_coins",false),"Gold is a pile of minted metallic coins")
	for i in range(1,drops.size()): check(drops[i].mesh.get_meta("physical_weapon",false),"Dropped "+drops[i].item.display_name+" uses its actual equipped model")
	var coin_point := drops[0].global_position
	await close_view(coin_point+Vector3(.27,.29,.30),coin_point+Vector3(0,.02,0),"minted_gold")
	controller.rig.yaw = 0;controller.rig.pitch = -.6;controller.rig.distance = 6
	await frames(4);await capture("ground_weapons")
	var distinct_models: Dictionary = {}
	for id in [&"wayfarer_blade",&"marchguard_sword",&"briarsteel_edge",&"cairnwarden_sword",&"wakecleaver",&"frontier_blade_6",&"relic_blade_6",&"ember_fang",&"glass_sabre",&"rift_cleaver"]:
		var item := ItemCatalog.get_item(id)
		check(item and item.visual,"Sword available through existing progression: "+String(id))
		distinct_models[item.visual.resource_path] = true
	check(distinct_models.size() == 10,"Ten authored sword designs retain their existing item IDs")
	# Isolate the actual imported geometry without changing the playable world.
	var sword_rack := Node3D.new();world.add_child(sword_rack)
	sword_rack.position = player.global_position+Vector3(0,1,8)
	var sword_number := 0
	for path in distinct_models:
		var blade: Node3D = load(path).instantiate();sword_rack.add_child(blade)
		blade.position = Vector3((sword_number-4.5)*.38,0,0)
		blade.rotation.x = PI/2
		sword_number += 1
	await close_view(sword_rack.global_position+Vector3(0,1.05,4.7),sword_rack.global_position+Vector3(0,.62,0),"sword_suite")
	sword_rack.queue_free()
	player.mounts.owned.assign([&"trail_horse"]);player.mounts.selected = &"trail_horse"
	check(player.mounts.toggle(),"Mounted fixture uses the ordinary mount controller")
	var horse := player.mounts.model as TrailHorse
	check(horse.skeleton.get_bone_count() == 23,"Horse has an imported anatomical rig")
	for clip in [&"idle",&"walk",&"trot",&"canter"]: check(horse.player.has_animation(clip),"Horse imports its "+String(clip)+" cycle")
	controller.rig.yaw = 1.25;controller.rig.pitch = -.3;controller.rig.distance = 6.5
	await frames(8);await capture("mounted_profile")
	await close_view(player.global_position+Vector3(3.7,2.2,-3.7),player.global_position+Vector3(0,1.35,0),"horse_close")
	Input.action_press("move_forward")
	await frames(15);await capture("horse_canter")
	check(horse.current_clip == &"canter","Travel speed selects the real canter")
	Input.action_release("move_forward");await frames(6)
	controller.rig.yaw = 1.25;controller.rig.pitch = -.22;controller.rig.distance = 4.8
	var target: ActorBody = world.camps[0].pack.members[0]
	target.health.maximum = 10000;target.health.current = 10000
	var hip_rotations: Array[Quaternion] = []
	var shoulder_rotations: Array[Quaternion] = []
	var foot_error := 0.0
	var rein_error := 0.0
	var hits := player.combat.total_hits
	player.combat.sequence_index = -1;player.combat.idle_elapsed = 2
	for cut in 2:
		target.global_position = player.global_position-Vector3(0,0,1.8)
		check(player.combat.request_attack(),"Mounted cut %d starts through real combat" % cut)
		for frame in range(38):
			await frames(1);drain_audio()
			var rig := player.visual.skeleton
			hip_rotations.append(rig.get_bone_global_pose(rig.find_bone("Hips")).basis.get_rotation_quaternion())
			shoulder_rotations.append(rig.get_bone_global_pose(rig.find_bone("Chest")).basis.get_rotation_quaternion())
			for side in ["L","R"]:
				var sign_value := -1.0 if side == "L" else 1.0
				foot_error = maxf(foot_error,player.visual.bone_world_transform(StringName("Foot."+side)).origin.distance_to(horse.stirrup_world(sign_value)))
			rein_error = maxf(rein_error,player.visual.socket_world_transform(&"OffhandSocket").origin.distance_to(horse.rein_grip_world()))
			if frame in [5,15,25]: await capture("mounted_cut%d_frame%d" % [cut,frame])
		await frames(6)
	var hip_angle := 0.0
	var shoulder_angle := 0.0
	for i in hip_rotations.size():
		for j in hip_rotations.size():
			hip_angle = maxf(hip_angle,rad_to_deg(hip_rotations[i].angle_to(hip_rotations[j])))
			shoulder_angle = maxf(shoulder_angle,rad_to_deg(shoulder_rotations[i].angle_to(shoulder_rotations[j])))
	check(hip_angle > 15 and shoulder_angle > 45,"Mounted cuts drive pelvis and shoulders through a visible weight shift")
	check(foot_error < .035,"Rider boots stay in the stirrups (%.3fm)" % foot_error)
	check(rein_error < .05,"Rein hand stays connected through both cuts (%.3fm)" % rein_error)
	check(player.combat.total_hits >= hits+2,"Mounted attacks retain real hits and phase timing")
	check(int(soundscape.events.get(&"swing",0)) >= 2 and int(soundscape.events.get(&"hit",0)) > 0,"Real sword swings and hits emit audio")
	check(int(soundscape.events.get(&"hoof",0)) > 0,"Hoof sounds follow the animated contacts")
	player.mounts.dismount();player.combat.cancel()
	var npc: WorldNPC = world.settlement.npcs[1]
	player.global_position = npc.global_position+Vector3(0,.1,1.7)
	await frames(8)
	var town: TownPanel
	for layer in world.get_children():
		if layer is ZoneHUD: town = layer.town_panel
	town.open_npc(npc)
	check(player.ui_session.active == town,"Ordinary NPC conversation opens the existing panel")
	check(soundscape.voice.stream and soundscape.voice.stream.get_length() > 1,"NPC speaks a shipped recording of its actual dialogue")
	await frames(90);drain_audio();await capture("npc_voice")
	if DisplayServer.get_name() != "headless": check(soundscape.duck > 0,"Dialogue lowers the background music")
	town.choose_response(0)
	check(soundscape.voice_key == "warden_page1","Choosing a dialogue response replaces the voice with the next actual page")
	player.ui_session.close()
	check(not soundscape.voice.playing,"Closing conversation stops its voice")
	soundscape.enter_region("cinderfall");await frames(130);drain_audio()
	if DisplayServer.get_name() != "headless": check(soundscape.music[soundscape.music_slot].playing and not soundscape.music[1-soundscape.music_slot].playing,"Region music crossfades and retires the old stream")
	soundscape.enter_region("briarwood")
	if recorder:
		drain_audio()
		var pcm := PackedByteArray();pcm.resize(audio_frames.size()*4)
		var peak := 0.0
		for i in audio_frames.size():
			peak = maxf(peak,maxf(absf(audio_frames[i].x),absf(audio_frames[i].y)))
			pcm.encode_s16(i*4,int(clampf(audio_frames[i].x,-1,1)*32767));pcm.encode_s16(i*4+2,int(clampf(audio_frames[i].y,-1,1)*32767))
		var stream := AudioStreamWAV.new();stream.format = AudioStreamWAV.FORMAT_16_BITS;stream.stereo = true;stream.mix_rate = int(AudioServer.get_mix_rate());stream.data = pcm
		stream.save_to_wav(output+"/runtime_mix.wav")
		check(audio_frames.size()>10000 and peak>.005 and peak<.98,"Actual runtime audio mix is audible and avoids clipping (peak %.3f)" % peak)
		AudioServer.remove_bus_effect(0,AudioServer.get_bus_effect_count(0)-1)
	var report := {"hip_degrees":hip_angle,"shoulder_degrees":shoulder_angle,"foot_error_m":foot_error,"rein_error_m":rein_error,"audio_events":soundscape.events,"failures":failures}
	FileAccess.open(output+"/metrics.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("PRESENTATION_UPGRADE ",JSON.stringify(report))
	soundscape.shutdown()
	world.queue_free();await frames(3)
	quit(1 if failures else 0)
