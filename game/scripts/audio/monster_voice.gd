extends Node
## Species voices accompany weapon impacts; one cry per accepted damage/strike.
const FAMILIES := [&"wolf", &"boar", &"mossling"]
var actor: ActorBody
var family: StringName
var hurt_cooldown := 0.0

static func supports(body: ActorBody) -> bool:
	return body.enemy_definition != null and body.enemy_definition.family in FAMILIES

func _ready() -> void:
	actor = get_parent() as ActorBody
	family = actor.enemy_definition.family
	var audio := IronfieldAudio.instance
	if audio == null: return
	# Shared streams are loaded once, even when a whole camp wakes together.
	for event in ["hurt", "attack", "death"]:
		var cue := StringName(String(family) + "_" + event)
		if audio.cues.has(cue): continue
		var paths: Array = []
		for i in 3: paths.append("monsters/%s_%s_%d" % [family, event, i])
		audio._load_cue(cue, paths)
	actor.health.damaged.connect(_damaged)
	actor.health.died.connect(_died)
	actor.combat.phase_changed.connect(_phase_changed)

func _process(delta: float) -> void:
	hurt_cooldown = maxf(0.0, hurt_cooldown - delta)

func _play(event: String, level: float) -> void:
	if IronfieldAudio.instance == null: return
	if not bool(actor.get_parent().get_meta("reference_audio", true)): return
	IronfieldAudio.instance.play_at(StringName(String(family) + "_" + event), actor.global_position + Vector3.UP * .8, level)

func _damaged(_amount: float, _source: Node3D) -> void:
	# Lethal hits use the death cry alone; rapid multi-hit skills cannot stack yelps.
	if not actor.health.is_alive() or hurt_cooldown > 0.0: return
	hurt_cooldown = .18
	_play("hurt", 1.0)

func _died(_source: Node3D) -> void:
	_play("death", 1.0)

func _phase_changed(phase: String) -> void:
	if phase == "ACTIVE" and actor.health.is_alive():
		_play("attack", -1.0)
