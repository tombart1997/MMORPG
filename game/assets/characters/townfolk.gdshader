shader_type spatial;
render_mode cull_disabled;
uniform sampler2D painted_atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform vec4 cloth_tint : source_color = vec4(0.4,0.32,0.24,1);
uniform vec4 skin_tint : source_color = vec4(1.0);
void fragment() {
	vec3 painted=texture(painted_atlas,UV).rgb*COLOR.rgb;
	painted *= mix(vec3(1.0),cloth_tint.rgb*1.7,COLOR.a);
	float skin_cell=step(UV.x,0.333)*step(UV.y,0.333);
	painted *= mix(vec3(1.0),skin_tint.rgb,skin_cell);
	ALBEDO=painted;
	ROUGHNESS=.94;
	METALLIC=0.0;
	SPECULAR=.12;
}
