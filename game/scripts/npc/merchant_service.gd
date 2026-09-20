class_name MerchantService
extends RefCounted
## Validates every command; UI never sets prices or owns balances.
func available(npc: WorldNPC, player: ActorBody) -> bool:
	return is_instance_valid(npc) and npc.data.shop != null and npc.can_interact(player)

func buy(npc: WorldNPC, player: ActorBody, offer_index: int, quantity: int) -> String:
	if not available(npc, player): return "Move closer to the merchant and finish your attack."
	if quantity < 1 or quantity > 99: return "Choose a quantity from 1 to 99."
	if offer_index < 0 or offer_index >= npc.data.shop.offers.size(): return "Offer no longer available."
	var offer: ShopOffer = npc.data.shop.offers[offer_index]
	if offer.item == null or offer.price < 1: return "Invalid merchant offer."
	var bag := player.inventory
	if bag.transaction_busy: return "Transaction already in progress."
	var cost := offer.price * quantity
	if bag.gold < cost: return "Not enough gold: need %d." % cost
	if not bag.can_add(offer.item, quantity): return "Inventory full. Sell something or free a slot."
	bag.transaction_busy = true
	bag.gold -= cost
	var added := bag.add_item(offer.item, quantity)
	if not added: bag.gold += cost
	bag.transaction_busy = false
	return "" if added else "Purchase could not be completed."

func sell(npc: WorldNPC, player: ActorBody, index: int, expected: ItemStack, quantity: int) -> String:
	if not available(npc, player): return "Move closer to the merchant and finish your attack."
	var bag := player.inventory
	if bag.transaction_busy: return "Transaction already in progress."
	if index < 0 or index >= bag.slots.size() or expected == null or bag.slots[index] != expected: return "Select the item again; the bag has changed."
	if quantity < 1 or quantity > expected.quantity: return "That quantity is not in this stack."
	var value := expected.definition().value
	if value <= 0: return "This item cannot be sold."
	bag.transaction_busy = true
	expected.quantity -= quantity
	if expected.quantity == 0: bag.slots[index] = null
	bag.gold += quantity * value
	bag.changed.emit()
	bag.transaction_busy = false
	return ""
