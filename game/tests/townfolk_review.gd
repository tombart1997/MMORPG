extends "res://tests/combat_smoke.gd"
## Actual world cameras for art review, plus shared rig and nameplate contracts.
var camera: Camera3D
var world: Node3D

func capture(name: String, point: Vector3, target: Vector3, fov: float = 40) -> void:
	camera.global_position=point
	camera.look_at(target)
	camera.fov=fov
	await frames(12)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.local/townfolk_%s.png"%name)

func _run() -> void:
	root.size=Vector2i(1280,720)
	world=load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled=false
	root.add_child(world)
	current_scene=world
	await frames(10)
	for child in world.get_children():
		if child is CanvasLayer: child.hide()
	var rig: ThirdPersonCamera=world.player.world_interaction.camera.get_parent().get_parent()
	rig.set_process(false)
	for npc in world.settlement.npcs:
		var visual:=npc.model as TownfolkVisual
		check(visual!=null and visual.skeleton.get_bone_count()==18,"Resident uses shared humanoid rig: "+npc.name)
		check(visual.animation.has_animation(visual.appearance.idle),"Resident has appropriate imported idle: "+npc.name)
		var meshes:=visual.find_children("*","MeshInstance3D",true,false)
		check(meshes.size()==visual.visible_modules.size(),"Unselected body/clothing modules are removed: "+npc.name)
		for part: MeshInstance3D in meshes:
			check(part.skin!=null and part.mesh.get_surface_count()==1,"Single material skinned module: "+part.name)
		check(npc.label.pixel_size*npc.label.font_size<.11 and npc.profession.font_size<npc.label.font_size,"Name and profession hierarchy: "+npc.name)
	camera=Camera3D.new()
	world.add_child(camera)
	camera.current=true
	world.player.set_process(false)
	for child in world.player.get_children():
		if child is PlayerController: child.set_physics_process(false)
	# Inspect authored positions; people are not moved into a custom scene.
	world.player.position=Vector3(.0,0,15)
	await capture("crossing",Vector3(8,5.2,23),Vector3(-.5,1,15),52)
	var sella: WorldNPC=world.settlement.npcs[2]
	sella.data=sella.data.duplicate()
	sella.data.turn_to_player=false
	sella.model.rotation.y=0
	await capture("sella",Vector3(3.2,1.85,13.4),sella.global_position+Vector3(0,1.04,0),35)
	await capture("sella_face",Vector3(2.15,1.78,15.3),sella.global_position+Vector3(0,1.68,0),30)
	var oren: WorldNPC=world.settlement.npcs[3]
	oren.data=oren.data.duplicate()
	oren.data.turn_to_player=false
	oren.model.rotation.y=0
	await capture("oren",Vector3(-1.5,1.9,15.1),oren.global_position+Vector3(0,1.01,0),35)
	await capture("oren_face",Vector3(-2.9,1.82,17.3),oren.global_position+Vector3(0,1.75,0),30)
	world.player.rotation.y=0
	await capture("player",Vector3(1.8,1.8,11.1),Vector3(0,1.05,15),35)
	await capture("fire",Vector3(4.1,1.1,10),Vector3(3,.5,12),39)
	await capture("roof",Vector3(9,7,14),Vector3(6,3.4,11),50)
	world.player.global_position=Vector3(14,.2,-20)
	await capture("wilderness",Vector3(14,.2,-20)+Vector3(0,1.3,0)+Vector3(0,0,11).rotated(Vector3.RIGHT,-.48).rotated(Vector3.UP,-.55),Vector3(14,1.5,-20),60)
	for part in world.settlement.get_children():
		if part is MeshInstance3D and part.position==Vector3(6,2.8,11):
			print("ROOF ",part.mesh.get_aabb()," vertices ",part.mesh.surface_get_array_len(0)," material cull=",part.material_override.cull_mode)
	# Idle must deform bones without bobbing the whole body off its soles.
	var resident:=sella.model as TownfolkVisual
	var head:=resident.skeleton.find_bone("Head")
	var previous:=resident.skeleton.get_bone_pose_rotation(head)
	resident.clock+=2
	resident.elapsed=1
	resident.present(.1,world.player)
	check(previous.angle_to(resident.skeleton.get_bone_pose_rotation(head))>.002,"Keeper idle changes the skinned head pose")
	world.player.position=Vector3(1.7,0,24)
	sella.label_clock=0
	sella._process(.2)
	check(sella.label.visible and sella.profession.visible,"Nearby names and professions remain readable")
	world.player.position=Vector3(1.7,0,30)
	sella.label_clock=0
	sella._process(.2)
	check(sella.label.visible and not sella.profession.visible,"Profession recedes before resident name")
	world.player.position=Vector3(1.7,0,45)
	sella.label_clock=0
	sella._process(.2)
	check(not sella.label.visible,"Distant nameplates do not dominate the world")
	resident.equip_visual(&"WeaponSocket",load("res://scenes/visuals/iron_sword.tscn"))
	await frames(2)
	var grip:Node3D=resident.sockets[&"WeaponSocket"].get_node("Equipment/Grip")
	var hand:=resident.skeleton.global_transform*resident.skeleton.get_bone_global_pose(resident.skeleton.find_bone("Hand.R"))
	check(grip.global_position.distance_to(hand.origin)<.12,"NPC kit reuses the established animated weapon grip contract")
	resident.equip_visual(&"WeaponSocket",null)
	check(resident.sockets[&"WeaponSocket"].get_node_or_null("Equipment")==null,"NPC weapon modules can be removed independently")
	world.queue_free()
	await frames(2)
	print("TOWNFOLK_REVIEW failures=",failures)
	quit(1 if failures else 0)
