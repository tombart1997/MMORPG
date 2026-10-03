class_name SkillSpectacle
extends Node3D
## Bounded presentation geometry; damage and durations remain in the gameplay components.
var kind: String = "thunder"
var caster: ActorBody
var lifetime: float = .5
var radius: float = 4
var elapsed: float = 0
var geometry: ImmediateMesh
var weapon: Node3D
var weapon_material: StandardMaterial3D
var echo_source_transform := Transform3D.IDENTITY
var trail: Array[Vector3] = []
var left_trail: Array[Vector3] = []
var right_trail: Array[Vector3] = []
# World-space pose samples exposed for visual review and attachment checks.
var blade_grip := Vector3.ZERO
var blade_tip := Vector3.ZERO
var body_anchor := Vector3.ZERO
var glow: OmniLight3D
var hue := Color(.2,.8,1)

func _ready() -> void:
	# ActorBody samples the final blended skeleton at the default priority.
	process_priority = 50
	add_to_group("skill_spectacles")
	geometry = ImmediateMesh.new()
	var surface := MeshInstance3D.new()
	surface.mesh = geometry
	surface.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := ShaderMaterial.new()
	material.shader = preload("res://assets/skill_energy.gdshader")
	surface.material_override = material
	add_child(surface)
	hue = Color(.2,1,.5) if kind == "spirit" else Color(1,.35,.05) if kind == "fire" else Color(.65,.5,1) if kind == "spin" else Color(1,.8,.25) if kind == "sun" else Color(.15,.75,1)
	if kind in ["spirit", "fire", "sun", "thunder"]:
		glow = OmniLight3D.new()
		glow.light_color = hue
		glow.light_energy = 1.4
		glow.omni_range = 4 if kind == "spirit" else radius * 1.8
		glow.position.y = 1.3
		add_child(glow)
	if kind == "spin" and is_instance_valid(caster):
		# Echo the equipped blade. Mesh references are shared; no duplicate rig/scripts.
		var source := caster.visual.equipped_weapon()
		if source:
			echo_source_transform = source.transform
			weapon = Node3D.new()
			add_child(weapon)
			weapon_material = StandardMaterial3D.new()
			weapon_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			weapon_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			weapon_material.albedo_color = Color(.65,.75,1,.6)
			for part: MeshInstance3D in source.find_children("*", "MeshInstance3D", true, false):
				var echo := MeshInstance3D.new()
				echo.mesh = part.mesh
				echo.transform = source.global_transform.affine_inverse() * part.global_transform
				echo.material_override = weapon_material
				echo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				weapon.add_child(echo)

func _process(delta: float) -> void:
	elapsed += delta
	if elapsed >= lifetime or not is_instance_valid(caster) or not caster.health.is_alive(): queue_free(); return
	if kind == "spirit" and not caster.statuses.has(&"spirit_edge"): queue_free(); return
	if kind == "sprint" and not caster.statuses.has(&"haste"): queue_free(); return
	blade_grip = caster.visual.weapon_marker_world(&"Grip")
	blade_tip = caster.visual.weapon_marker_world(&"Tip")
	body_anchor = caster.visual.bone_world_transform(&"Chest").origin
	var grip := to_local(blade_grip)
	var tip := to_local(blade_tip)
	var chest := to_local(body_anchor)
	var fade := minf(1, (lifetime-elapsed)*6)
	geometry.clear_surfaces()
	geometry.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	match kind:
		"thunder":
			_blade_ribbon(grip,tip,hue,fade)
			_line(grip,tip,.09,Color(.65,.95,1,fade))
			for i in 5:
				var angle := -.8 + i*.4
				var end := Vector3(sin(angle)*radius,.8,-cos(angle)*radius)
				_bolt(tip,end,i,fade*.7)
		"sun":
			_blade_ribbon(grip,tip,hue,fade)
			_arc(radius, .18, -.95, .95, .35, hue, fade)
			var point := Vector3(0,.4,-radius*.6)
			_line(grip,tip,.12,Color(1,.9,.45,fade))
			_line(tip,point,.045,Color(1,.8,.25,fade*.65))
			_line(point+Vector3.UP*5,point,.32,Color(1,.85,.3,fade*.65))
			_line(point+Vector3.UP*5,point,.07,Color(1,1,.9,fade))
			for i in 10:
				var angle := i*TAU/10
				_line(point,point+Vector3(sin(angle),.4,-cos(angle))*elapsed*7,.04,Color(1,.8,.2,fade))
		"spin":
			var angle := elapsed*TAU*2.5
			_blade_ribbon(grip,tip,hue,fade)
			_line(grip,tip,.10,Color(.8,.8,1,fade))
			# The body drives the sweep while the floor ring retains the damage radius.
			_arc(radius*.75,chest.y,angle-1.8,angle,.16,hue,fade*.6,Vector3(chest.x,0,chest.z))
			var end := chest+Vector3(sin(angle),0,-cos(angle))*radius*.75
			_line(tip,end,.035,Color(.65,.5,1,fade*.55))
			if weapon:
				var socket_pose := caster.visual.socket_world_transform(&"WeaponSocket")
				var blade_pose := socket_pose * echo_source_transform
				var extend := smoothstep(0,.12,elapsed)*smoothstep(0,.12,lifetime-elapsed)
				var orbit := body_anchor+caster.global_basis*Vector3(sin(angle),0,-cos(angle))*radius*.58
				weapon.global_transform = Transform3D(Basis(Vector3.UP,angle*extend)*blade_pose.basis,blade_grip.lerp(orbit,extend))
				_line(grip,to_local(weapon.global_position),.045,Color(.65,.7,1,fade*.55))
				weapon_material.albedo_color.a = fade*.6
		"fire":
			# Ground flames stay with the placed area; the initial channel comes from the hand.
			if elapsed < .35:
				_line(grip,Vector3(0,.08,0),.075,Color(1,.6,.1,(1-elapsed/.35)*fade))
			_arc(radius,.09,0,TAU,.14,Color(1,.28,.025),fade*.85)
			_arc(radius*.82,.12,0,TAU,.07,Color(1,.7,.1),fade*.6)
			for i in 24:
				var angle := i*2.39996
				var distance := radius*(.4+.55*fmod(i*.37,1))
				var base := Vector3(sin(angle)*distance,.08,cos(angle)*distance)
				var height := .5 + .7*(.5+.5*sin(elapsed*11+i*2.1))
				var lean := Vector3(sin(elapsed*5+i)*.22,0,cos(elapsed*4+i)*.16)
				_flame(base,height,lean,.24,Color(1,.16,.01,fade*.55))
				_flame(base,height*.78,lean*.7,.10,Color(1,.6,.025,fade*.85))
				_flame(base,height*.4,lean*.4,.045,Color(1,.95,.4,fade))
		"spirit":
			var sword := caster.visual.equipped_weapon()
			if sword and sword.get_node_or_null("Tip"):
				var a := grip
				var b := tip
				_line(a,b,.20,Color(.02,1,.1,.2*fade))
				_line(a,b,.075,Color(.08,1,.18,.75*fade))
				_line(a,b,.012,Color(.35,1,.25,fade*.65))
				var direction := (b-a).normalized()
				var side := direction.cross(Vector3.RIGHT).normalized()
				if side.length_squared() < .1: side = Vector3.FORWARD
				var other := direction.cross(side)
				for strand in 2:
					var previous := a
					for step in range(1,15):
						var t := step/14.0
						var angle := t*TAU*1.8-elapsed*8+strand*PI
						var next := a.lerp(b,t)+(side*sin(angle)+other*cos(angle))*.10*sin(t*PI)
						_line(previous,next,.022,Color(.15,1,.2,fade*.8))
						previous = next
			else:
				_arc(.4,.1,0,TAU,.03,hue,fade*.2)
		"sprint":
			for side in ["L", "R"]:
				var points: Array[Vector3] = left_trail if side == "L" else right_trail
				var foot := caster.visual.bone_world_transform(StringName("Foot."+side)).origin
				_line(to_local(foot),to_local(foot+Vector3.UP*.12),.035,Color(.4,.9,1,fade*.6))
				points.append(foot)
				while points.size() > 12: points.pop_front()
				for i in range(1,points.size()):
					_line(to_local(points[i-1]),to_local(points[i]),.055,Color(.2,.8,1,fade*i/float(points.size())*.65))
	geometry.surface_end()
	if glow:
		glow.light_energy = fade*(.8+sin(elapsed*20)*.2)
		if kind != "fire": glow.position = grip

func _blade_ribbon(grip: Vector3, tip: Vector3, color: Color, alpha: float) -> void:
	trail.append(grip.lerp(tip,.25))
	trail.append(tip)
	while trail.size() > 10: trail.pop_front(); trail.pop_front()
	for i in range(0,trail.size()-2,2):
		_quad(to_local(trail[i]),to_local(trail[i+1]),to_local(trail[i+3]),to_local(trail[i+2]),Color(color,alpha*(i+2)/trail.size()*.4))

func _arc(r: float, y: float, start: float, end: float, width: float, color: Color, alpha: float, offset: Vector3 = Vector3.ZERO) -> void:
	for i in 36:
		var a := lerpf(start,end,i/36.0)
		var b := lerpf(start,end,(i+1)/36.0)
		var brightness := alpha*(.25+.75*i/36.0)
		var outer_a := offset+Vector3(sin(a)*r,y,-cos(a)*r)
		var outer_b := offset+Vector3(sin(b)*r,y,-cos(b)*r)
		var inner_a := offset+Vector3(sin(a)*(r-width),y,-cos(a)*(r-width))
		var inner_b := offset+Vector3(sin(b)*(r-width),y,-cos(b)*(r-width))
		_quad(outer_a,inner_a,inner_b,outer_b,Color(color,brightness))
		_line(outer_a,outer_b,.025,Color(1,1,1,brightness*.8))

func _bolt(a: Vector3, b: Vector3, seed_value: int, alpha: float) -> void:
	var previous := a
	for i in range(1,10):
		var t := i/9.0
		var noise := Vector3(sin(i*4.1+seed_value+floor(elapsed*24)),sin(i*7.3+seed_value)*.6,0)*.25*sin(PI*t)
		var next := a.lerp(b,t)+noise
		_line(previous,next,.09,Color(hue,alpha*.35))
		_line(previous,next,.016,Color(.65,.95,1,alpha))
		previous = next

func _line(a: Vector3, b: Vector3, width: float, color: Color) -> void:
	var direction := b-a
	if direction.length_squared() < .000001: return
	var camera := get_viewport().get_camera_3d()
	var view := to_local(camera.global_position)-(a+b)*.5 if camera else Vector3(0,2,5)
	var side := direction.cross(view).normalized()*width
	_quad(a-side,a+side,b+side,b-side,color)

func _quad(a: Vector3, b: Vector3, c: Vector3, d: Vector3, color: Color) -> void:
	geometry.surface_set_color(color)
	var vertices := [a,b,c,a,c,d]
	var uvs := [Vector2(0,0),Vector2(1,0),Vector2(1,1),Vector2(0,0),Vector2(1,1),Vector2(0,1)]
	for i in 6:
		geometry.surface_set_uv(uvs[i])
		geometry.surface_add_vertex(vertices[i])

func _flame(base: Vector3, height: float, lean: Vector3, width: float, color: Color) -> void:
	var camera := get_viewport().get_camera_3d()
	var view := to_local(camera.global_position)-base if camera else Vector3.FORWARD
	var side := Vector3.UP.cross(view).normalized()
	for i in 6:
		var t0 := i/6.0
		var t1 := (i+1)/6.0
		var a := base+Vector3.UP*height*t0+lean*t0*t0
		var b := base+Vector3.UP*height*t1+lean*t1*t1
		var w0 := width*(1-t0)*(.7+.3*sin(PI*t0))
		var w1 := width*(1-t1)*(.7+.3*sin(PI*t1))
		_quad(a-side*w0,a+side*w0,b+side*w1,b-side*w1,Color(color,color.a*(1-t0*.65)))
