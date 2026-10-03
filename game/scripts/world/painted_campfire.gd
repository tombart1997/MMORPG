class_name PaintedCampfire
extends Node3D
## Layered cutout brush tongues: no particle lights, collision or per-frame mesh rebuild.
static var shared_flames: ArrayMesh
static var shared_material: ShaderMaterial
var glow: OmniLight3D
var clock: float = 0

func _ready() -> void:
	if not shared_flames:
		shared_material=ShaderMaterial.new()
		shared_material.shader=preload("res://assets/remaster/campfire.gdshader")
		var surface:=SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		var colors:=[Color("6a1710"),Color("c44213"),Color("e7751a"),Color("ffb83b")]
		for tongue in range(7):
			var angle:=tongue*2.4
			var radius:=.15 if tongue>0 else 0.0
			var origin:=Vector3(sin(angle)*radius,.08,cos(angle)*radius)
			var tall:=.85+sin(tongue*1.9)*.16
			for layer in range(4):
				var width:=.23-layer*.039
				var scale_y:=1.0-layer*.16
				var points:=[Vector2(-width,0),Vector2(-width*.94,.24),Vector2(-width*.25,.53),Vector2(width*.45,.71),Vector2(-width*.15,.94),Vector2(width*.42,1.0),Vector2(width*.78,.67),Vector2(width,.30),Vector2(width*.78,0)]
				var curved:=PackedVector2Array()
				for i in range(points.size()):
					var a:Vector2=points[posmod(i-1,points.size())]
					var b:Vector2=points[i]
					var c:Vector2=points[(i+1)%points.size()]
					var d:Vector2=points[(i+2)%points.size()]
					for sample in range(4):
						var t:=float(sample)/4
						curved.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
				var triangles:=Geometry2D.triangulate_polygon(curved)
				for facing in [-1,1]:
					for index in triangles:
						var point:=curved[index]
						surface.set_color(colors[layer])
						surface.set_uv(Vector2(.5+point.x/.46,point.y))
						var local:=Vector3(point.x,point.y*tall*scale_y,layer*.004*facing)
						surface.add_vertex(origin+local.rotated(Vector3.UP,angle))
		surface.generate_normals()
		shared_flames=surface.commit()
	var flames:=MeshInstance3D.new()
	flames.mesh=shared_flames
	flames.material_override=shared_material
	flames.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	flames.visibility_range_end=42
	add_child(flames)
	for i in range(3):
		var log:=MeshInstance3D.new()
		var wood:=CylinderMesh.new()
		wood.top_radius=.065
		wood.bottom_radius=.085
		wood.height=.73
		wood.radial_segments=7
		log.mesh=wood
		log.material_override=RemasterMaterials.surface(6,Color("5a4331"))
		log.position=Vector3(0,.10,0)
		log.rotation=Vector3(PI/2,i*PI/3,0)
		log.visibility_range_end=42
		add_child(log)
	glow=OmniLight3D.new()
	glow.position=Vector3(0,.55,0)
	glow.light_color=Color("ff9c42")
	glow.light_energy=1.15
	glow.omni_range=3.5
	glow.shadow_enabled=false
	add_child(glow)
	_smoke()

func _smoke() -> void:
	var smoke:=GPUParticles3D.new()
	smoke.amount=7
	smoke.lifetime=3.6
	smoke.position.y=.68
	smoke.visibility_aabb=AABB(Vector3(-1,0,-1),Vector3(2,3,2))
	smoke.visibility_range_end=28
	smoke.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material:=ParticleProcessMaterial.new()
	material.direction=Vector3.UP
	material.spread=14
	material.initial_velocity_min=.25
	material.initial_velocity_max=.45
	material.gravity=Vector3(.025,.035,.01)
	material.scale_min=.25
	material.scale_max=.46
	var gradient:=Gradient.new()
	gradient.set_color(0,Color(.26,.23,.20,.15))
	gradient.set_color(1,Color(.38,.35,.30,0))
	var ramp:=GradientTexture1D.new()
	ramp.gradient=gradient
	material.color_ramp=ramp
	smoke.process_material=material
	var quad:=QuadMesh.new()
	quad.size=Vector2.ONE
	var paint:=ShaderMaterial.new()
	paint.shader=Shader.new()
	paint.shader.code="shader_type spatial; render_mode unshaded, cull_disabled, depth_draw_never; void vertex(){ MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0],INV_VIEW_MATRIX[1],INV_VIEW_MATRIX[2],MODEL_MATRIX[3]); } void fragment(){ float a=smoothstep(.5,.08,length(UV-.5)); ALBEDO=COLOR.rgb; ALPHA=COLOR.a*a*.4; }"
	quad.material=paint
	smoke.draw_pass_1=quad
	add_child(smoke)

func _process(delta: float) -> void:
	clock+=delta
	if clock<.1: return
	clock=0
	var camera:=get_viewport().get_camera_3d()
	if not camera: return
	glow.light_energy=(1.05+sin(Time.get_ticks_msec()*.005)*.12) if camera.global_position.distance_to(global_position)<24 else 0.0
