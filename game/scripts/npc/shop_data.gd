class_name ShopData
extends Resource
@export var id: StringName
@export var title: String
## Unlimited supplies for now; no transient stock to serialize.
@export var offers: Array[ShopOffer] = []
