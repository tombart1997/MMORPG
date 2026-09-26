extends "res://tests/farming_loop.gd"
## Deterministic automation of earned progression, not a novice human playtest.
var total_damage: float = 0
var first_clear_seconds: float = 0
var first_clear_damage: float = 0

func gather() -> void:
	player.world_interaction.cancel()
	for drop in get_nodes_in_group("loot"):
		if is_instance_valid(drop) and not drop.is_queued_for_deletion() and drop.global_position.distance_to(player.position) < 22:
			await approach(drop,&"loot",800)
	for i in player.inventory.slots.size():
		var stack: ItemStack = player.inventory.slots[i]
		if stack == null or stack.definition().equipment_slot == &"": continue
		var slot := stack.definition().equipment_slot
		var current: ItemStack = player.equipment.slots[slot]
		var stat := "attack" if slot == &"weapon" else "defense"
		if current == null or float(stack.modifiers().get(stat,0)) > float(current.modifiers().get(stat,0)):
			player.equipment.equip(i)

func clear_camp(camp: EnemyCamp, basics: bool = false) -> Vector2:
	var before := total_damage
	var start := Engine.get_physics_frames()
	for enemy in camp.pack.members.duplicate():
		if not is_instance_valid(enemy) or not enemy.health.is_alive(): continue
		if basics: await approach(enemy,&"enemy",1600)
		else: await fight(enemy,2400)
		if not player.health.is_alive(): break
	var result := Vector2((Engine.get_physics_frames()-start)/60.0,total_damage-before)
	check(camp.pack.living_count() == 0 and player.health.is_alive(),"Earned level %d loadout clears %s" % [player.progression.level,camp.camp_name])
	return result

func recover() -> void:
	player.ui_session.close()
	await travel(ZoneTerrain.START,3000)
	for i in 1000:
		if player.health.current >= player.health.maximum: break
		await frames(1)
	check(player.health.current == player.health.maximum,"Return to sanctuary restores health without spending gold")

func fail_if_dead() -> bool:
	if player.health.is_alive(): return false
	print("FIRST_HOUR halted: level=%d attack=%.1f defense=%.1f kills=%d gold=%d" % [player.progression.level,player.stats.value(&"attack"),player.stats.value(&"defense"),player.progression.kills,player.inventory.gold])
	quit(1)
	return true

func _run() -> void:
	world = load("res://scenes/outdoor_zone.tscn").instantiate()
	world.persistence_enabled = false
	root.add_child(world)
	current_scene = world
	await frames(10)
	player = world.player
	for child in world.get_children():
		if child is ZoneHUD: hud = child
	for i in world.camps.size(): world.camps[i].rng.seed = 734+i
	encounter = player.farming.encounter
	encounter.rng.seed = 924
	player.health.damaged.connect(func(amount,_source): total_damage += amount)
	var warden: WorldNPC = world.settlement.npcs[1]
	var mara: WorldNPC = world.settlement.npcs[0]
	var smith: WorldNPC = world.settlement.npcs[3]
	var merchant := MerchantService.new()
	await approach(warden,&"npc")
	check(player.quests.available(QuestCatalog.all()[&"briar_watch"]),"First hunt available without preliminary errands")
	check(player.quests.accept(&"briar_watch",warden),"Fresh start accepts purposeful hunting introduction")
	player.quests.accept(&"welcome",warden)
	player.ui_session.close()
	await approach(mara,&"npc")
	player.ui_session.close()
	await approach(warden,&"npc")
	check(player.quests.claim(&"welcome",warden).is_empty(),"Optional local introduction remains compatible")
	player.ui_session.close()
	await travel(ZoneTerrain.CAMPS[0]+Vector3(0,0,3))
	var first := await clear_camp(world.camps[0],true)
	first_clear_seconds = first.x
	first_clear_damage = first.y
	if fail_if_dead(): return
	await gather()
	check(player.inventory.count(&"moss_shard") >= 3 and player.inventory.gold >= 47,"First hunt produces useful upgrade materials and spendable gold")
	await approach(warden,&"npc",3000)
	check(player.quests.claim(&"briar_watch",warden).is_empty(),"Hunt reward can fund a tangible equipment purchase")
	check(player.quests.accept(&"first_temper",warden),"Smith introduction follows first hunting reward")
	player.ui_session.close()
	await approach(mara,&"npc")
	check(merchant.buy(mara,player,0,1).is_empty(),"Earned gold buys Marchguard sword")
	check(player.equipment.equip(find_item(&"marchguard_sword")),"Purchased sword equips through real bag")
	player.ui_session.close()
	await approach(smith,&"npc")
	player.equipment.unequip(&"weapon")
	var index := find_item(&"marchguard_sword")
	var stack: ItemStack = player.inventory.slots[index]
	var forge := UpgradeService.new()
	check(forge.attempt(player,smith,index,stack).get("success",false),"First upgrade affordable after sword purchase and guaranteed")
	player.equipment.equip(index)
	check(player.quests.claim(&"first_temper",smith).is_empty(),"First temper returns restoration supplies")
	check(player.quests.accept(&"briarwake_heart",smith),"Smith offers Fracture investigation after first temper")
	check(not player.map_state.discoveries.get("briarwood",[]).has("briarwake"),"Fracture quest gives a direction without revealing its map location")
	await recover()
	# Farm actual replenishing camps. No direct XP, gold, health or item grants.
	for lap in 3:
		await travel(ZoneTerrain.CAMPS[0]+Vector3(0,0,3))
		await clear_camp(world.camps[0])
		if fail_if_dead(): return
		await gather()
		await travel(Vector3(-25,0,-43))
		await clear_camp(world.camps[1])
		if fail_if_dead(): return
		await gather()
		if player.progression.level >= 4:
			await travel(Vector3(-25,0,-62))
			await travel(Vector3(-4,0,-62))
			await travel(Vector3(10,0,-74))
			await clear_camp(world.camps[2])
			if fail_if_dead(): return
			await gather()
		await recover()
		await approach(mara,&"npc")
		for i in player.inventory.slots.size():
			var spare: ItemStack = player.inventory.slots[i]
			if spare and spare.definition().equipment_slot != &"": merchant.sell(mara,player,i,spare,1)
		if player.equipment.slots[&"chest"].id == &"travelers_vest" and player.inventory.gold >= 30:
			merchant.buy(mara,player,1,1)
			player.equipment.equip(find_item(&"quilted_jack"))
		player.ui_session.close()
		print("FIRST_HOUR lap=%d level=%d kills=%d attack=%.1f defense=%.1f gold=%d tonics=%d" % [lap+1,player.progression.level,player.progression.kills,player.stats.value(&"attack"),player.stats.value(&"defense"),player.inventory.gold,player.inventory.count(&"field_tonic")])
		if player.progression.level >= 6: break
	check(player.progression.level >= 5,"Repeated farming yields several modest levels through real rewards")
	await travel(ZoneTerrain.CAMPS[0]+Vector3(0,0,3))
	var stronger := await clear_camp(world.camps[0],true)
	check(stronger.x < first_clear_seconds*.8,"Returning loadout clears first group noticeably faster with the same basic-attack policy")
	print("RETURN_POWER initial=%.2fs/%.1f damage return=%.2fs/%.1f damage level=%d attack=%.1f" % [first_clear_seconds,first_clear_damage,stronger.x,stronger.y,player.progression.level,player.stats.value(&"attack")])
	await gather()
	await recover()
	await travel(Vector3(-25,0,-43))
	await travel(Vector3(-19,0,-49))
	await travel(Vector3(-8,0,-46.9))
	check(player.map_state.discoveries.get("briarwood",[]).has("briarwake"),"Investigation discovers Fracture by travelling to it")
	await fight(encounter.body,3600)
	check(player.health.is_alive() and not encounter.body.health.is_alive(),"Naturally earned farming loadout defeats Fracture through live skills and combat")
	if fail_if_dead(): return
	check(player.quests.ready(QuestCatalog.all()[&"briarwake_heart"]),"Authoritative Fracture destruction advances investigation quest")
	await recover()
	await approach(smith,&"npc")
	var rare_before := player.inventory.count(&"wakeglass")
	check(player.quests.claim(&"briarwake_heart",smith).is_empty() and player.inventory.count(&"wakeglass") == rare_before+1,"First Fracture quest grants one guaranteed rare catalyst, separate from random drops")
	check(not player.quests.claim(&"briarwake_heart",smith).is_empty(),"Rare first-clear reward cannot be claimed twice")
	player.equipment.unequip(&"weapon")
	index = -1
	for i in player.inventory.slots.size():
		if player.inventory.slots[i] and player.inventory.slots[i].definition().equipment_slot == &"weapon": index=i; break
	stack = player.inventory.slots[index]
	if stack.upgrade_level() == 0: forge.attempt(player,smith,index,stack)
	var before_gold := player.inventory.gold
	check(forge.attempt(player,smith,index,stack,true).get("success",false) and player.inventory.gold == before_gold-30,"Earned Wakeglass guarantees uncertain temper while still charging normal gold")
	player.equipment.equip(index)
	player.ui_session.close()
	await approach(mara,&"npc")
	check(player.inventory.gold >= 240 and merchant.buy(mara,player,5,1).is_empty(),"Natural farming and quest rewards fund horse after equipment decisions")
	check(player.actions.use_bag(find_item(&"trail_bridle")),"Earned mount unlocks through inventory item")
	player.ui_session.close()
	print("FIRST_HOUR final level=%d kills=%d gold=%d attack=%.1f defense=%.1f horse=%s" % [player.progression.level,player.progression.kills,player.inventory.gold,player.stats.value(&"attack"),player.stats.value(&"defense"),player.mounts.owned])
	print("First-hour progression automation complete: %d failures; human pacing unverified" % failures)
	quit(1 if failures else 0)
