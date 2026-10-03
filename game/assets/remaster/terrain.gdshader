shader_type spatial;
render_mode specular_disabled;
uniform sampler2D layer0 : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D layer1 : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D layer2 : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D layer3 : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D layer4 : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D layer5 : source_color, filter_linear_mipmap, repeat_enable;
varying vec3 world;
varying vec3 ground_normal;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;ground_normal=normalize(mat3(MODEL_MATRIX)*NORMAL);}
void fragment(){
 vec2 p=world.xz;
 float macro=noise(p*.065), patches=noise(p*.29), grit=noise(p*2.4);
 vec2 uv=p*.42;
 vec3 warm=texture(layer0,uv).rgb;
 vec3 lush=texture(layer1,uv*.83+vec2(.21,.36)).rgb;
 vec3 dirt=texture(layer2,uv*.73).rgb;
 vec3 dry=texture(layer3,uv*.94).rgb;
 vec3 stone=texture(layer4,uv*.65).rgb;
 vec3 mud=texture(layer5,uv*.71).rgb;
 float path=1.0-smoothstep(1.25,3.0,COLOR.r*12.0+(patches-.5)*1.7+(grit-.5)*.28);
 float scar=COLOR.g*(.5+patches*.5);
 float dry_weight=smoothstep(.58,.88,macro)*.32;
 vec3 grass=mix(mix(warm,lush,smoothstep(.15,.75,patches)*.85),dry,dry_weight)*vec3(.73,.85,.72);
 vec3 earth=mix(dirt,mud,COLOR.b*.72);
 vec3 ground=mix(grass,earth,max(path,scar*.72));
 float slope=1.0-ground_normal.y;
 float outcrop=max(smoothstep(.08,.25,slope),smoothstep(.65,.85,noise(p*.16))*smoothstep(.8,3.6,world.y)*.55)*(1.0-path);
 ground=mix(ground,stone,outcrop);
 ground*=.76+macro*.32+grit*.06;
 ALBEDO=ground*.82;
 ROUGHNESS=1.0;
}
