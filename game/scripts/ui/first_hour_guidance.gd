class_name FirstHourGuidance
extends RefCounted
## One contextual suggestion; inferred from progression, no modal tutorial tree.
static func hint(player: ActorBody) -> String:
	if not player.health.is_alive(): return "R: return to Briar Crossing. Your gold, gear, XP and horse ownership are kept."
	if player.health.current < player.health.maximum * .35:
		if player.inventory.count(&"field_tonic") > 0: return "Low health: Q uses your assigned tonic between attacks. The waystone heals for free."
		return "Out of restoration? Retreat to the waystone in Briar Crossing for free healing."
	if player.mounts.mounted: return "H dismounts. Attacks, hostile hits and NPC conversations return you to foot."
	for quest in QuestCatalog.all().values():
		if player.quests.ready(quest): return "%s complete — return to %s. J shows the reward." % [quest.title,"Oren" if quest.turn_in == &"smith" else "Elric"]
	if player.progression.kills == 0:
		if SafeArea.protects(player): return "Welcome to Briar Crossing. Click to walk or talk to Elric; accept Briar at the Gate. M opens the map."
		return "Click a mossling to approach and attack. Keep the group in front; 1–6 skills have hover explanations."
	if player.progression.kills < 4: return "Click individual drops or press E nearby. Gold and items stay separate; I compares and equips your finds."
	if player.equipment.slots[&"weapon"] and player.equipment.slots[&"weapon"].id == &"wayfarer_blade":
		return "Mara sells a Marchguard Sword for 40 gold. Equip it in I; keep moss shards for Oren."
	if player.quests.status(&"first_temper") != "completed": return "Oren's first temper is guaranteed. Keep some gold for tonics; later attempts can fail without breaking gear."
	if player.quests.status(&"briarwake_heart") == "available": return "Oren has heard something beyond Old Pine Hollow. Speak with him when your equipment is ready."
	if player.mounts.owned.is_empty() and player.progression.level >= 3 and SafeArea.protects(player):
		return "A farming milestone: Mara's 240-gold bridle unlocks a horse. Use it in I, then H to travel faster."
	return ""
