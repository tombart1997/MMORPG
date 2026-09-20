class_name DropTable
extends Resource
@export var entries: Array[DropEntry] = []

func roll(rng: RandomNumberGenerator) -> Array[ItemStack]:
	var result: Array[ItemStack] = []
	for entry in entries:
		if entry.item and rng.randf() < entry.chance:
			result.append(ItemStack.new(entry.item.id, rng.randi_range(maxi(1, entry.minimum), maxi(entry.minimum, entry.maximum))))
	return result
