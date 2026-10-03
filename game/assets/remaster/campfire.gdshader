shader_type spatial;
render_mode unshaded, cull_disabled;
varying float height;
float grain(vec2 p) { return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453); }
void vertex() {
	height=UV.y;
	VERTEX.x+=sin(TIME*3.6+VERTEX.y*4.8+UV.x*5.0)*.055*UV.y;
	VERTEX.y*=1.0+sin(TIME*4.3+UV.x*6.2)*.065*UV.y;
}
void fragment() {
	vec3 paint=COLOR.rgb*(.88+.12*grain(floor(UV*130.0)));
	ALBEDO=paint;
	EMISSION=paint*.3;
}
