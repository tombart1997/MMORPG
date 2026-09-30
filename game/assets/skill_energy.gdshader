shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;
void fragment() {
	float edge = max(0.0, 1.0 - abs(UV.x * 2.0 - 1.0));
	float soft = smoothstep(0.0, 0.55, edge);
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a * soft;
}
