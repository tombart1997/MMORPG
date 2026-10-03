class_name NPCAppearance
extends Resource
## Every selection uses the same rig, material atlas and imported module resources.
@export_enum("Male", "Female") var body: String = "Male"
@export_enum("Body default", "Male", "Female") var face: String = "Body default"
@export_enum("Tunic", "Robe", "Apron") var clothing: String = "Tunic"
@export_enum("Swept", "Bun", "Topknot") var hair: String = "Topknot"
@export var accessories: Array[String] = ["Merchant"]
@export var weapon: PackedScene
@export var offhand: PackedScene
@export var skin_tint: Color = Color.WHITE
@export var cloth_override: Color = Color.TRANSPARENT
@export var stature: Vector3 = Vector3.ONE
@export_enum("idle", "keeper_idle", "smith_idle") var idle: String = "idle"

static func for_resident(data: NPCData) -> NPCAppearance:
	if data.appearance: return data.appearance
	var result := NPCAppearance.new()
	match data.id:
		&"keeper":
			result.body="Female"
			result.clothing="Robe"
			result.hair="Bun"
			result.accessories=["Keeper"]
			result.stature=Vector3(.96,.97,.96)
			result.idle="keeper_idle"
		&"smith":
			result.clothing="Apron"
			result.hair="Swept"
			result.accessories=["Smith"]
			result.stature=Vector3(1.14,1.04,1.09)
			result.cloth_override=Color(.58,.53,.44)
			result.idle="smith_idle"
		&"mara", &"apothecary":
			result.body="Female"
			result.hair="Bun"
			result.stature=Vector3(.96,.95,.96)
		&"artificer":
			result.clothing="Robe"
			result.accessories=["Artificer"]
		&"warden", &"ash_scout": result.accessories=["Guard"]
		&"armorer", &"weapons": result.accessories=["Merchant","Guard"]
		&"stablemaster": result.skin_tint=Color(.84,.81,.73)
	return result
