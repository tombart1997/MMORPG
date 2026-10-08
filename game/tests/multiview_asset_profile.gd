extends "res://tests/asset_balance_profile.gd"
## Controlled additional mesh load inside the real game. Static candidates
## cannot use ActorVisual until a species rig and required clips are authored.
var prototype_instances := 0

func measure(key: String) -> void:
	if key=="dense_combat" and OS.get_cmdline_user_args().has("--prototype-grid"):
		var packed:=load("res://review_assets/multiview_ironhide_boar/runtime.glb") as PackedScene
		var holder:=Node3D.new()
		world.add_child(holder)
		for row in 5:
			for col in 5:
				var instance:=packed.instantiate() as Node3D
				holder.add_child(instance)
				# Explicit prototype-only scale: native reconstruction has no meters.
				instance.scale=Vector3.ONE*1.8
				instance.position=pose+Vector3((col-2)*2.0,0.9,(row-2)*2.0)
				instance.position.y=ZoneTerrain.height_at(instance.position.x,instance.position.z)+.3422*1.8
				prototype_instances+=1
		results["prototype"]={"instances":prototype_instances,"triangles_each":17983,
			"static":true,"game_mapping_changed":false,"scope":"Additional GPU mesh load; existing combat AI and authored camps remain active"}
	await super.measure(key)
