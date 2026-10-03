"""CC0 horse adaptation, fitted tack and four-beat/two-beat/canter cycles.
blender -b --factory-startup --python-exit-code 1 -P blender/scripts/build_trail_horse.py
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'game/assets/mounts'; DEST.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'blender/mounts'; SOURCE.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
PARTS=[]
def material(name,color,metal=0,rough=.5):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
coat=material('Horse_BayCoat',(.125,.038,.014),0,.82)
points=material('Horse_DarkPoints',(.038,.023,.014),0,.56)
hair=material('Horse_ManeTail',(.015,.012,.01),0,.66)
leather=material('Horse_SaddleLeather',(.065,.025,.013),0,.63)
blanket=material('Horse_WovenPad',(.37,.265,.13),0,.9)
brass=material('Horse_TackBrass',(.43,.27,.065),.8,.28)
hoofmat=material('Horse_HoofHorn',(.013,.011,.008),0,.64)
ivory=material('Horse_Blaze',(.72,.66,.51),0,.65)
eye=material('Horse_Eye',(.013,.009,.006),.05,.17)
anatomy=[]
def mesh(name,vs,fs,mat,bone=None):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat)
    for p in d.polygons:p.use_smooth=True
    PARTS.append(o)
    if bone:o['skin_bone']=bone
    return o
def ell(name,center,scale,mat,bone=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=center)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    PARTS.append(o)
    if bone:o['skin_bone']=bone
    return o
def sweep(name,rows,mat,bone=None,sides=24):
    vs=[];fs=[]
    for j,(center,rx,ry) in enumerate(rows):
        c=Vector(center);a=Vector(rows[max(0,j-1)][0]);b=Vector(rows[min(len(rows)-1,j+1)][0]);t=(b-a).normalized()
        x=Vector((1,0,0));x=(x-t*x.dot(t)).normalized();y=t.cross(x)
        for i in range(sides):
            q=i*math.tau/sides;vs.append(c+x*(rx*math.cos(q))+y*(ry*math.sin(q)))
    for j in range(len(rows)-1):
        for i in range(sides):a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
    fs.extend([tuple(reversed(range(sides))),tuple((len(rows)-1)*sides+i for i in range(sides))])
    return mesh(name,vs,fs,mat,bone)
def line(name,path,radius,mat,bone='Body',sides=8):
    return sweep(name,[(p,radius if not isinstance(radius,list) else radius[i],radius if not isinstance(radius,list) else radius[i]) for i,p in enumerate(path)],mat,bone,sides)

# The freely licensed base has connected topology and an authored diffuse map.
# Preserve the original in reference/horse; orient it along Blender +Y (Godot -Z).
reference=ROOT/'blender/reference/horse/original/horse.blend'
with bpy.data.libraries.load(str(reference),link=False) as (source,target):
    target.objects=['Circle']
skin=target.objects[0];bpy.context.collection.objects.link(skin)
skin.name='Horse_ContinuousSkin'
bpy.context.view_layer.update()
source_transform=skin.matrix_world.copy()
for v in skin.data.vertices:
    p=source_transform@v.co
    v.co=((p.x-.999957)*.36,-p.y*.35-.09,(p.z+3.15435)*.30+.008)
skin.matrix_world=Matrix.Identity(4)
for attr in list(skin.data.color_attributes):skin.data.color_attributes.remove(attr)
skin.data.materials.clear();skin.data.materials.append(coat)
for p in skin.data.polygons:p.material_index=0;p.use_smooth=True
bpy.context.view_layer.objects.active=skin;skin.select_set(True)
sub=skin.modifiers.new('AnatomicalSurface','SUBSURF');sub.levels=2
bpy.ops.object.modifier_apply(modifier=sub.name)
# A slight filled-out cannon and larger hoof silhouette survive subdivision.
for v in skin.data.vertices:
    p=v.co
    if p.z<.58:
        cx=.266 if p.x>0 else -.266
        p.x=cx+(p.x-cx)*1.24
    if p.z<.09:p.z=max(.008,p.z-.008)
tex=bpy.data.images.load(str(ROOT/'blender/reference/horse/original/horse_diffuse.png'),check_existing=True)
tex.name='BriarwoodBay_Albedo';tex.pack()
shader=coat.node_tree.nodes['Principled BSDF']
node=coat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex
coat.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
PARTS.append(skin)
surface=BVHTree.FromPolygons([v.co for v in skin.data.vertices],[tuple(p.vertices) for p in skin.data.polygons])
def on_face(p,offset=.008):
    at,normal,_,_=surface.find_nearest(Vector(p))
    return at+normal*offset
def flowing(rows):
    result=[]
    for i in range(len(rows)-1):
        for k in range(5):
            t=k/5
            values=[]
            for c in range(3):
                a,b,d,e=[Vector(rows[j][0]) if c==0 else rows[j][c] for j in [max(0,i-1),i,i+1,min(len(rows)-1,i+2)]]
                values.append(.5*((2*b)+(-a+d)*t+(2*a-5*b+4*d-e)*t*t+(-a+3*b-3*d+e)*t*t*t))
            result.append((values[0],max(.001,values[1]),max(.001,values[2])))
    return result+[rows[-1]]
restlegs={}
for side,s in [('L',-1),('R',1)]:
    for front in [True,False]:
        tag=('Fore' if front else 'Hind')+'.'+side
        joints=[(s*.266,.64,1.29),(s*.266,.64,.97),(s*.266,.685,.49),(s*.266,.65,.16),(s*.266,.70,.065)] if front else [(s*.26,-.51,1.30),(s*.266,-.58,.85),(s*.266,-.79,.50),(s*.266,-.81,.16),(s*.266,-.765,.065)]
        restlegs[tag]=[Vector(p) for p in joints]
        foot=joints[-1]
        sweep('Hoof'+tag,[((foot[0],foot[1]-.025,.14),.054,.063),((foot[0],foot[1],.075),.065,.082),((foot[0],foot[1]+.012,.018),.075,.095)],hoofmat,tag+'.Hoof',24)

# Facial cues, ears, fitted bridle, forelock and crest mane.
for side,s in [('L',-1),('R',1)]:
    ell('Eye'+side,on_face((s*.123,1.47,1.84),.003),(.012,.018,.013),eye,'Head')
    ell('Nostril'+side,on_face((s*.085,1.72,1.56),.002),(.009,.020,.013),points,'Head')
    line('CheekStrap'+side,[on_face(p) for p in [(s*.10,1.27,1.91),(s*.133,1.43,1.82),(s*.10,1.69,1.60)]],.007,leather,'Head')
    line('BitRing'+side,[(s*.111,1.665+.024*math.sin(i*math.tau/20),1.57+.024*math.cos(i*math.tau/20)) for i in range(21)],.003,brass,'Head')
line('BrowBand',[on_face(p) for p in [(-.125,1.45,1.88),(-.065,1.51,1.88),(0,1.525,1.88),(.065,1.51,1.88),(.125,1.45,1.88)]],.007,leather,'Head')
line('NoseBand',[on_face(p) for p in [(-.10,1.69,1.62),(-.05,1.73,1.66),(0,1.742,1.672),(.05,1.73,1.66),(.10,1.69,1.62)]],.008,leather,'Head')
for s in [-1,1]:
    rein=line('Rein',[(s*.111,1.665,1.57),(s*.20,1.30,1.53),(s*.23,.88,1.60),(-.04,.44,1.75),(-.15,.22,1.83)],.005,leather,None)
    rein['rein']=True
# Solid tapered hair masses, with overlapping locks for the reference silhouette.
crest=[on_face((0,1.31-i*.19,1.90-i*.09),.004) for i in range(6)]
sweep('ManeMass',flowing([(p,.034,.032) for p in crest]),hair,'Neck',20)
for k in range(23):
    t=k/22;p=on_face((-.018,1.31-.92*t,1.9-.46*t),.006);x,y,z=p
    rows=[((x,y,z),.022,.022),((x-.04,y-.014,z-.02),.025,.025),((x-.095,y-.026,z-.10),.019,.019),((x-.13,y-.04,z-.155),.001,.001)]
    sweep('ManeLock',flowing(rows),hair,'Neck',8)
for k in range(7):
    a=.012*(k-3)
    line('Forelock',[on_face(p,.012) for p in [(a,1.39,1.925),(a,1.47,1.89),(a*.7,1.51,1.85)]], [.012,.013,.001],hair,'Head')
sweep('TailMass',flowing([((0,-.87,1.40),.042,.045),((0,-1.03,1.22),.063,.064),((0,-1.16,.95),.071,.066),((0,-1.21,.63),.052,.052),((0,-1.18,.29),.022,.022),((0,-1.16,.23),.001,.001)]),hair,'Tail',20)
for k in range(16):
    a=k*math.tau/16;r=.053
    path=[(r*math.sin(a),-1.02+r*.5*math.cos(a),1.24),(r*1.25*math.sin(a),-1.16+r*math.cos(a),.97),(r*math.sin(a),-1.22+r*math.cos(a),.65),(r*.4*math.sin(a),-1.18+r*.3*math.cos(a),.27)]
    sweep('TailLock',flowing([(p,v,v) for p,v in zip(path,[.014,.017,.013,.001])]),hair,'Tail',8)

# Shaped pad and saddle sit over the withers without swallowing the horse's barrel.
# Curved cloth follows the back and falls down both sides; no floating flat slab.
padvs=[];padfs=[]
for j in range(9):
    y=-.42+j*.075
    for i in range(21):
        a=-1.40+i/20*2.80
        padvs.append((.345*math.sin(a),y,1.17+.33*math.cos(a)+.014*math.cos(y*5)))
for j in range(8):
    for i in range(20):a=j*21+i;padfs.append((a,a+1,a+22,a+21))
pad=mesh('SaddlePad',padvs,padfs,blanket,'Body')
sol=pad.modifiers.new('WovenThickness','SOLIDIFY');sol.thickness=.012
bpy.context.view_layer.objects.active=pad;bpy.ops.object.modifier_apply(modifier=sol.name)
for s in [-1,1]:
    flap=mesh('SaddleFlap',[(s*.22,-.30,1.49),(s*.335,-.28,1.34),(s*.36,-.17,1.13),(s*.35,.18,1.14),(s*.22,.21,1.50)],[(0,1,2,3,4)],leather,'Body')
    sol=flap.modifiers.new('LeatherThickness','SOLIDIFY');sol.thickness=.013
    bpy.context.view_layer.objects.active=flap;bpy.ops.object.modifier_apply(modifier=sol.name)
    line('PadEdge',[(s*.341,-.42,1.237),(s*.348,-.16,1.24),(s*.341,.18,1.237)],.007,blanket)
    line('StirrupLeather',[(s*.24,.02,1.50),(s*.37,.07,1.19),(s*.42,.08,.88)],.012,leather)
    # A real foot plate and rounded D-shaped iron; feet sit on its lower bar.
    line('StirrupIron',[(s*.37,.08,.80),(s*.37,.08,.90),(s*.40,.08,.94),(s*.45,.08,.94),(s*.48,.08,.90),(s*.48,.08,.80),(s*.37,.08,.80)],.007,brass)
    line('FlapStitch',[(s*.23,-.27,1.49),(s*.348,-.24,1.34),(s*.373,-.13,1.16),(s*.363,.15,1.17)],.0018,ivory)
sweep('SaddleSeat',[((0,-.29,1.565),.185,.065),((0,-.19,1.54),.185,.025),((0,.03,1.535),.17,.025),((0,.16,1.57),.17,.055)],leather,'Body',32)
line('Girth',[(.30,.15,1.46),(.37,.15,1.16),(.29,.15,.94),(0,.15,.89),(-.29,.15,.94),(-.37,.15,1.16),(-.30,.15,1.46)],.020,leather)

# Stable bone contract, continuous skin weights, separate articulated joints.
data=bpy.data.armatures.new('HorseRig');rig=bpy.data.objects.new('HorseRig',data);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=data.edit_bones.new(name);b.head=head;b.tail=tail
    if parent:b.parent=data.edit_bones[parent]
bone('Root',(0,0,0),(0,0,.25))
bone('Body',(0,-.25,1.14),(0,.45,1.35),'Root')
bone('Neck',(0,.64,1.38),(0,1.27,1.90),'Body')
bone('Head',(0,1.27,1.90),(0,1.70,1.58),'Neck')
bone('Tail',(0,-.87,1.40),(0,-1.18,.35),'Body')
for side,s in [('L',-1),('R',1)]:bone('Ear.'+side,(s*.09,1.34,1.96),(s*.11,1.37,2.03),'Head')
chains={}
for tag,joints in restlegs.items():
    names=[tag+'.'+n for n in ['Upper','Lower','Ankle','Hoof']]
    for i,n in enumerate(names):bone(n,joints[i],joints[i+1] if i+1<len(joints) else joints[i]+Vector((0,.1,0)),names[i-1] if i>0 else 'Body')
    chains[tag]=names
bpy.ops.object.mode_set(mode='OBJECT')
def seg_distance(p,a,b):
    d=b-a;t=min(1,max(0,(p-a).dot(d)/d.length_squared));return (p-a-d*t).length
def skin_weights(p):
    if p.z<1.17 and abs(p.x)>.15 and abs(p.y)>.35:
        tag=('Fore' if p.y>.0 else 'Hind')+'.'+('L' if p.x<0 else 'R')
        d=[(n,seg_distance(p,data.bones[n].head_local,data.bones[n].tail_local)) for n in chains[tag]]
        d.sort(key=lambda x:x[1]);pairs=d[:2];raw=[1/(x[1]+.028)**4 for x in pairs]
        return [(pairs[i][0],raw[i]/sum(raw)) for i in range(len(pairs))]
    if p.y>1.26 and p.z>1.48:
        if p.z>1.96:return [('Ear.'+('L' if p.x<0 else 'R'),1)]
        return [('Head',1)]
    if p.y>.54 and p.z>1.20:
        t=min(1,max(0,(p.y-.54)/.38));return [('Neck',t),('Body',1-t)]
    return [('Body',1)]
for o in PARTS:
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
    o.parent=rig
    groups={n:o.vertex_groups.new(name=n) for n in data.bones.keys()}
    fixed=o.get('skin_bone')
    for v in o.data.vertices:
        if o.get('rein'):
            t=min(1,max(0,(v.co.y-1.20)/.46));weights=[('Head',t),('Body',1-t)]
        else:weights=[(fixed,1)] if fixed else skin_weights(v.co)
        for n,w in weights:
            if w>0:groups[n].add([v.index],w,'REPLACE')
    arm=o.modifiers.new('HorseSkin','ARMATURE');arm.object=rig
    if o==skin:
        col=o.data.color_attributes.new(name='CoatVariation',type='FLOAT_COLOR',domain='CORNER')
        for loop in o.data.loops:
            p=o.data.vertices[loop.vertex_index].co
            shade=.78+.03*math.sin(p.z*7+p.y*3)
            # Dark bay with black points, without the original white socks.
            point=min(1,max(0,(p.z-.42)/.32)) if abs(p.y)>.35 else 1
            shade*=.055+.945*point
            col.data[loop.index].color=(shade,shade*.97,shade*.92,1)
        # Multiply the diffuse by the same COLOR_0 in Blender and glTF.
        tint=coat.node_tree.nodes.new('ShaderNodeVertexColor');tint.layer_name='CoatVariation'
        mult=coat.node_tree.nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1
        coat.node_tree.links.new(node.outputs['Color'],mult.inputs[1]);coat.node_tree.links.new(tint.outputs['Color'],mult.inputs[2])
        coat.node_tree.links.new(mult.outputs[0],shader.inputs['Base Color'])
    else:
        neutral=o.data.color_attributes.new(name='CoatVariation',type='FLOAT_COLOR',domain='CORNER')
        for color in neutral.data: color.color=(1,1,1,1)

def global_rotate(n,angles):
    rest=data.bones[n].matrix_local.to_quaternion();q=Euler(angles).to_quaternion();rig.pose.bones[n].rotation_quaternion=rest.inverted()@q@rest
def set_global(n,basis):
    pb=rig.pose.bones[n];m=pb.matrix.copy()
    pos=m.translation.copy();m=basis.to_4x4();m.translation=pos;pb.matrix=m;bpy.context.view_layer.update()
def solve_leg(tag,target):
    names=chains[tag];tip=rig.pose.bones[names[-1]]
    for k in range(7):
        for n in reversed(names[:-1]):
            pb=rig.pose.bones[n];a=tip.head-pb.head;b=target-pb.head
            if a.length>.0001 and b.length>.0001:
                q=a.rotation_difference(b);set_global(n,q.to_matrix()@pb.matrix.to_3x3())
    pb=rig.pose.bones[names[-1]];mat=data.bones[pb.name].matrix_local.copy();mat.translation=pb.head;pb.matrix=mat

scene=bpy.context.scene;scene.render.fps=60
for o in PARTS:
    for m in o.modifiers:m.show_viewport=False
for clip in ['idle','walk','trot','canter']:
    action=bpy.data.actions.new('Horse_'+clip);rig.animation_data_create();rig.animation_data.action=action
    for frame in range(0,61,3):
        t=frame/60
        for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
        moving=clip!='idle';amount={'idle':0,'walk':.008,'trot':.018,'canter':.032}[clip]
        global_rotate('Body',(.008*math.sin(t*math.tau),.009*math.sin(t*math.tau),0))
        rig.pose.bones['Body'].location=data.bones['Body'].matrix_local.to_3x3().inverted()@Vector((0,0,amount*math.sin(t*math.tau*2)))
        global_rotate('Neck',(.015*math.sin(t*math.tau)*(2 if clip=='canter' else 1),0,.006*math.sin(t*math.tau)))
        global_rotate('Head',(-.018*math.sin(t*math.tau),0,.009*math.sin(t*math.tau)))
        global_rotate('Tail',(.025*math.sin(t*math.tau),.075*math.sin(t*math.tau),0))
        for side,sgn in [('L',-1),('R',1)]:global_rotate('Ear.'+side,(.03*math.sin(t*math.tau+sgn),0,.055*sgn*math.sin(t*math.tau)))
        bpy.context.view_layer.update()
        for tag,joints in restlegs.items():
            if clip=='walk':offset={'Hind.L':0,'Fore.L':.25,'Hind.R':.5,'Fore.R':.75}[tag];stance=.65;span=.60;lift=.095
            elif clip=='trot':offset={'Fore.L':0,'Hind.R':0,'Fore.R':.5,'Hind.L':.5}[tag];stance=.40;span=.76;lift=.16
            else:offset={'Hind.L':0,'Hind.R':.12,'Fore.L':.33,'Fore.R':.52}[tag];stance=.30;span=1.0;lift=.23
            phase=(t+offset)%1
            target=joints[-2].copy()
            if moving:
                if phase<stance:target.y+=span*(.5-phase/stance)
                else:
                    u=(phase-stance)/(1-stance);target.y+=span*(-.5+u);target.z+=math.sin(u*math.pi)*lift
            solve_leg(tag,target)
        for pb in rig.pose.bones:
            pb.keyframe_insert(data_path='rotation_quaternion',frame=frame);pb.keyframe_insert(data_path='location',frame=frame)
    tr=rig.animation_data.nla_tracks.new();tr.name=clip;tr.strips.new(clip,0,action);tr.mute=True;rig.animation_data.action=None
for o in PARTS:
    for m in o.modifiers:m.show_viewport=True
for pb in rig.pose.bones:pb.matrix_basis.identity()
rig.animation_data.action=None;scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'trail_horse.blend'))
# One skinned mesh retains material surfaces; source stays editable by part.
bpy.ops.object.select_all(action='DESELECT')
for o in PARTS:o.select_set(True)
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join();combined=bpy.context.object;combined.name='BriarwoodBaySkin'
rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(DEST/'trail_horse.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_skins=True,export_vertex_color='NAME',export_vertex_color_name='CoatVariation')
triangles=sum(len(p.vertices)-2 for p in combined.data.polygons)
(DEST/'manifest.json').write_text(json.dumps({'triangles':triangles,'bones':list(data.bones.keys()),'clips':['idle','walk','trot','canter'],'source':'blender/mounts/trail_horse.blend','base_mesh':{'author':'8tibGames','url':'https://opengameart.org/content/horse','license':'CC0-1.0'},'seat_height':1.535,'stirrup_ankle_height':.92},indent=2))
print('HORSE_COMPLETE',triangles,'triangles',len(data.bones),'bones',flush=True)
