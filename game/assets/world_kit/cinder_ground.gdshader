shader_type spatial;
render_mode specular_disabled;
uniform sampler2D rock : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D earth : source_color, filter_linear_mipmap, repeat_enable;
varying vec3 world;
varying vec3 terrain_normal;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1)).xyz;terrain_normal=normalize(mat3(MODEL_MATRIX)*NORMAL);}
void fragment(){
 vec2 p=world.xz;
 float macro=noise(p*.068), fine=noise(p*.48);
 float path=1.0-smoothstep(2.0,5.0,COLOR.r*20.0+(fine-.5)*1.4);
 vec3 stone=texture(rock,p*.26).rgb*vec3(.36,.33,.38);
 vec3 ash=texture(earth,p*.31).rgb*vec3(.50,.46,.48);
 float exposed=max(smoothstep(.04,.22,1.0-terrain_normal.y),smoothstep(.4,.7,macro));
 vec3 color=mix(ash,stone,exposed*(1.0-path*.6));
 // Branching fissures belong to the ground instead of raised strips.
 float wave=p.x+sin(p.y*.16)*2.2+sin(p.y*.49)*.5;
 float seam=abs(sin(wave*.46+noise(p*.20)*1.4));
 float heat=(1.0-smoothstep(.015,.075,seam))*smoothstep(.44,.62,macro)*(1.0-path)*COLOR.g;
 ALBEDO=color*(.8+macro*.32+fine*.10);
 EMISSION=vec3(.8,.18,.025)*heat*.8;
 ROUGHNESS=.96;
}
