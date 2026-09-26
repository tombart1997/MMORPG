extends ActorVisual
## Authored rib units react to authoritative health; no gameplay state here.
var ribs: Array[MeshInstance3D] = []
var cores: Array[MeshInstance3D] = []
var light: OmniLight3D
var clock: float = 0
var collapsed: bool = false
var activation_seen: bool = false
var rib_rest: Array[Transform3D] = []

func _ready() -> void:
	model = load("res://assets/benchmark/briarwake.glb").instantiate()
	add_child(model)
	for part: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if part.name.begins_with("Rib_"):
			ribs.append(part)
			rib_rest.append(part.transform)
		if part.name.begins_with("Core_"): cores.append(part)
	light = OmniLight3D.new()
	light.position.y = 2.0
	light.light_color = Color(1, .42, .09)
	light.light_energy = 1.4
	light.omni_range = 5
	light.shadow_enabled = false
	add_child(light)
	label = Label3D.new()
	label.position.y = 4.9
	label.font_size = 22
	label.pixel_size = .006
	label.modulate = Color(.92,.78,.48)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.visibility_range_end = 19
	add_child(label)

func present(_velocity: Vector3, _combat: MeleeCombat, health: HealthComponent, title: String, delta: float) -> void:
	clock += delta
	hit_time += delta
	var fraction := health.current / health.maximum
	var active: bool = get_parent().get_parent().active
	label.text = title
	label.visible = health.is_alive() and nameplate_allowed
	if active and not activation_seen:
		activation_seen = true
		ArtVFX.burst(self, Vector3(0, 1.7, 0), Color(1,.57,.15), 12, 1.2)
	light.light_energy = ((1.5 if active else .6) + .18 * sin(clock*2.2) + (1-fraction)*.9 + (.7 if hit_time<.13 else 0)) if health.is_alive() else 0
	for core in cores:
		core.visible = health.is_alive()
		core.position.y = sin(clock * 1.3) * .065
		core.rotation.y = sin(clock * .5) * .08
	if health.is_alive():
		for i in ribs.size():
			var damage := floorf((1-fraction)*3)/3
			pose_rib(i,damage*.10)
	elif not collapsed:
		collapsed = true
		ArtVFX.burst(self, Vector3(0,1.6,0), Color(1,.55,.12), 22, 2.2)
		for i in ribs.size():
			var tween := create_tween()
			tween.tween_method(func(t:float): pose_rib(i,t),.1,1.35,.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)

func pose_rib(index:int, tilt:float) -> void:
	var number:=int(String(ribs[index].name).trim_prefix("Rib_"))
	var a:=number*TAU/7+.18
	var outward:=Vector3(cos(a),0,-sin(a))
	var pivot:=outward*1.3
	var rotation:=Basis(Vector3.UP.cross(outward),tilt)
	ribs[index].transform=Transform3D(rotation,pivot-rotation*pivot)*rib_rest[index]

func react_to_hit() -> void:
	super.react_to_hit()
	ArtVFX.burst(self, Vector3(0,1.8,0), Color(.92,.59,.24), 5, .5)
