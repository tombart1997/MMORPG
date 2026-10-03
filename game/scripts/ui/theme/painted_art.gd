class_name PaintedArt
extends Control
## Decorative artwork only: never intercepts a slot, drag, or world click.
var part: String = "flames"
var mirrored: bool = false
var round_portrait: bool = false
var quiet: bool = false

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if round_portrait:
		var shader := Shader.new()
		shader.code = "shader_type canvas_item; void fragment(){ vec4 c=texture(TEXTURE,UV); c.a*=1.0-smoothstep(0.45,0.47,length(UV-vec2(0.5))); COLOR=c; }"
		var effect := ShaderMaterial.new()
		effect.shader = shader
		material = effect
	elif part != "portrait":
		var shader := Shader.new()
		shader.code = "shader_type canvas_item; uniform bool quiet=false; void fragment(){ vec4 c=texture(TEXTURE,UV); float v=max(c.r,max(c.g,c.b)); c.a*=smoothstep(0.035,0.16,v); if(quiet){float l=dot(c.rgb,vec3(0.3,0.5,0.2)); c.rgb=l*vec3(0.8,0.64,0.42);} COLOR=c; }"
		var effect := ShaderMaterial.new()
		effect.shader = shader
		effect.set_shader_parameter("quiet",quiet)
		material = effect

func _draw() -> void:
	var texture := PaintedTheme.artwork(part)
	if texture:
		var rect := Rect2(Vector2(size.x,0) if mirrored else Vector2.ZERO,Vector2(-size.x,size.y) if mirrored else size)
		if part == "flames":
			draw_texture_rect_region(texture,rect,Rect2(0,0,texture.get_width(),texture.get_height()/2))
		else: draw_texture_rect(texture,rect,false)
