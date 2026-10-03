shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D grain_texture : source_color, filter_linear_mipmap;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap;
uniform bool has_normal = false;
uniform vec4 coat : source_color = vec4(0.5,0.3,0.2,1.0);
uniform vec4 marking : source_color = vec4(0.12,0.08,0.06,1.0);
uniform vec4 underside : source_color = vec4(0.7,0.6,0.5,1.0);
uniform float surface_kind = 0.0; // fur, chitin, stone, bark, translucent essence
uniform float roughness_value = 0.85;
uniform float pattern = 0.0;
uniform float grain_average = 0.16;
varying vec3 local_point;
float noise3(vec3 p) {
	return sin(p.x*3.7+sin(p.z*4.1))*sin(p.y*5.3+p.z*2.7)*0.5+0.5;
}
void vertex() { local_point = VERTEX; }
void fragment() {
	vec3 source = texture(grain_texture,UV).rgb;
	// Preserve painted grain/creases without multiplying the baked green coat into every species.
	float grain = clamp(dot(source,vec3(0.299,0.587,0.114))/grain_average,0.62,1.36);
	float stripes = sin(local_point.z*11.0+local_point.y*4.0+pattern)*0.5+0.5;
	float dorsal = smoothstep(0.75,1.45,local_point.y)*(0.32+0.17*stripes);
	float belly = (1.0-smoothstep(0.45,1.10,local_point.y))*0.36;
	vec3 base = mix(mix(coat.rgb,marking.rgb,dorsal),underside.rgb,belly);
	float fiber = sin(UV.x*940.0+sin(UV.y*73.0)*2.0)*sin(UV.y*380.0);
	if (surface_kind < 0.5) { grain *= (0.83+noise3(local_point*3.0)*0.32)*(1.0+fiber*0.09); }
	else if (surface_kind < 1.5) { grain *= 0.94+0.06*stripes; }
	else if (surface_kind < 3.5) { grain *= 1.0+sin(local_point.x*67.0+local_point.z*43.0)*0.04; }
	ALBEDO = base*grain;
	ROUGHNESS = roughness_value;
	SPECULAR = surface_kind < 0.5 ? 0.26 : 0.42;
	if (has_normal) { NORMAL_MAP=texture(normal_texture,UV).rgb; NORMAL_MAP_DEPTH=0.7; }
	if (surface_kind > 3.5) { EMISSION=coat.rgb*0.22; }
}
