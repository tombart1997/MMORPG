shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D soil_color : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D soil_normal : hint_normal, filter_linear_mipmap, repeat_enable;
varying vec3 world_position;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
float noise(vec2 p) {
 vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
 return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
}
float segment_distance(vec2 p, vec2 a, vec2 b) { vec2 ab=b-a; return length(p-a-ab*clamp(dot(p-a,ab)/dot(ab,ab),0.0,1.0)); }
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
 vec2 p=world_position.xz;
 float grove=1.0-smoothstep(20.0,28.0,distance(p,vec2(-8,-49)));
 float n=noise(p*.62)*.65+noise(p*2.2)*.25+noise(p*7.0)*.1;
 float path=smoothstep(-.035,.045,COLOR.r-COLOR.g);
 float approach=1.0-smoothstep(.8,2.3,segment_distance(p,vec2(-15,-37),vec2(-8,-49))+(n-.5)*1.3);
 path=max(path,approach);
 vec3 duff=mix(vec3(.12,.105,.066),vec3(.21,.225,.10),smoothstep(.25,.75,n));
 vec3 earth=mix(vec3(.22,.15,.085),vec3(.37,.285,.17),n);
 vec3 color=mix(duff,earth,path*.84);
 float scar=1.0-smoothstep(2.0,4.2,distance(p,vec2(-8,-49))+(n-.5)*2.1);
 color=mix(color,vec3(.105,.087,.062)*(0.7+n*.6),scar);
 float stone=smoothstep(.70,.82,noise(p*.8))*(1.0-path)*.4;
 color=mix(color,vec3(.28,.30,.26),stone);
 float grit=texture(soil_color,p*.48).r;
 color*=.70+grit*.62;
 ALBEDO=mix(COLOR.rgb,color,grove);
 ROUGHNESS=.94;
 NORMAL_MAP=mix(vec3(.5,.5,1),texture(soil_normal,p*.48).rgb,grove*.7);
 NORMAL_MAP_DEPTH=.5;
}
