shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled;
void fragment(){
 float radius=length((UV-vec2(.5))*2.0);
 ALBEDO=vec3(.055,.07,.07);
 ALPHA=(1.0-smoothstep(.12,.95,radius))*.25;
}
