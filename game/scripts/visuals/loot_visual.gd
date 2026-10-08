class_name LootVisual
extends RefCounted
static var coin_mesh: Mesh

static func create(drop: LootPickup) -> Node3D:
	var root := Node3D.new()
	root.name = "GroundLootVisual"
	if drop.item and drop.item.equipment_slot == &"weapon" and drop.item.visual:
		var sword := drop.item.visual.instantiate() as Node3D
		root.add_child(sword)
		sword.position.y = .026
		sword.rotation.y = float(drop.item.id.hash()%628)/100.0
		for part: MeshInstance3D in sword.find_children("*","MeshInstance3D",true,false):
			part.visibility_range_end = 36
		root.set_meta("physical_weapon",true)
	elif drop.item == null and drop.coins > 0:
		if coin_mesh == null:
			var source := ReviewedModels.scene_for("res://assets/generated/equipment/gold_coin.glb").instantiate()
			coin_mesh = source.find_children("*","MeshInstance3D",true,false)[0].mesh
			source.free()
		var count := clampi(2+drop.coins/8,3,14)
		var batch := MultiMesh.new()
		batch.transform_format = MultiMesh.TRANSFORM_3D
		batch.mesh = coin_mesh
		batch.instance_count = count
		for i in count:
			var angle := i*2.39996
			var distance := .037*sqrt(float(i))
			var point := Vector3(sin(angle)*distance,.014+float(i%3)*.009,cos(angle)*distance)
			var tilt := Vector3(.08*sin(i*3.4),angle,.10*cos(i*4.1))
			batch.set_instance_transform(i,Transform3D(Basis.from_euler(tilt),point))
		var pile := MultiMeshInstance3D.new()
		pile.multimesh = batch
		pile.name = "MintedGoldCoins"
		pile.visibility_range_end = 28
		root.add_child(pile)
		root.set_meta("physical_coins",true)
	else:
		var pouch := load("res://assets/generated/world/pouch.glb").instantiate() as Node3D
		root.add_child(pouch)
	return root
