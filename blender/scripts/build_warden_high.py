"""Editable high-detail male Warden, authored through the live Blender MCP studio.

Run build() in the studio, review renders, then export(). Gameplay stays authoritative.
The original humanoid bone contract is retained for sockets, skills and mounted combat.
"""
import bpy, math, json, importlib.util
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix, Euler
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('warden_base', Path(__file__).with_name('build_characters.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
RIG = None
PARTS = []
MATS = {}

def material(name, color, metal=0, rough=.5):
    m = base.material('Warden_'+name, color, metal, rough)
    MATS[name] = m
    return m

def mesh(name, verts, faces, mat, bone='Chest', weights=None):
    o = base.mesh_object(name, verts, faces, mat, weights or [{bone:1} for _ in verts], RIG)
    # Metre-scaled UVs keep small material detail consistent between parts.
    uv = o.data.uv_layers.new(name='SurfaceUV')
    for poly in o.data.polygons:
        axis = max(range(3), key=lambda i: abs(poly.normal[i]))
        a,b = [(1,2),(0,2),(0,1)][axis]
        for li in poly.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v[a]*3,v[b]*3)
    PARTS.append(o)
    return o

def ell(name, center, scale, mat, bone='Chest', seg=40, rings=24):
    o=base.ellipsoid(name,center,scale,mat,bone,RIG,seg,rings)
    PARTS.append(o)
    return o

def tube(name, points, radius, mat, bone='Chest', sides=12):
    radii = radius if isinstance(radius,list) else [radius]*len(points)
    o=base.tube(name,points,radii,mat,[{bone:1} for p in points],RIG,sides)
    PARTS.append(o)
    return o

def loft(name, rings, mat, bone='Chest', sides=64, rib=0, weights=None):
    vs,fs,ws=[],[],[]
    for j,(z,rx,ry,cy) in enumerate(rings):
        for i in range(sides):
            a=i*math.tau/sides
            detail=1+rib*math.cos(a*12)
            vs.append((rx*math.sin(a)*detail,cy+ry*math.cos(a)*detail,z))
            ws.append(weights[j] if weights else {bone:1})
    for j in range(len(rings)-1):
        for i in range(sides):
            n=(i+1)%sides; a=j*sides
            fs.append((a+i,a+n,a+sides+n,a+sides+i))
    fs.extend([tuple(reversed(range(sides))),tuple((len(rings)-1)*sides+i for i in range(sides))])
    return mesh(name,vs,fs,mat,bone,ws)

def line(name, points, radius, mat, bone='Chest'):
    return tube(name,points,radius,mat,bone,8)

def oval_trim(name,z,rx,ry,cy,mat,bone='Chest',radius=.003):
    return line(name,[(rx*math.sin(i*math.tau/96),cy+ry*math.cos(i*math.tau/96),z) for i in range(97)],radius,mat,bone)

def sculpt_head():
    # Continuous quad surface with a broad jaw, cheek planes, brow, nose and lip volumes.
    vs,fs=[],[]; seg=128; rings=100
    def g(x,z,cx,cz,sx,sz): return math.exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
    for j in range(rings+1):
        t=j/rings; z=1.565+t*.305
        # Anatomical outline widens at jaw angle, narrows at temples, rounds into skull.
        profile=[(0,.022),(.06,.071),(.16,.100),(.32,.105),(.48,.111),(.66,.105),(.80,.103),(.9,.083),(1,.002)]
        k=next((k for k in range(len(profile)-1) if t<=profile[k+1][0]),len(profile)-2)
        u=(t-profile[k][0])/(profile[k+1][0]-profile[k][0]); u=u*u*(3-2*u)
        rx=profile[k][1]*(1-u)+profile[k+1][1]*u
        ry=.089*math.sin(math.pi*t)**.38+.003
        for i in range(seg):
            a=i*math.tau/seg; x=rx*math.sin(a); front=max(0,math.cos(a))**6
            y=ry*math.cos(a)-.015
            d=.025*g(x,z,0,1.665,.024,.072) # nasal bridge
            d+=.032*g(x,z,0,1.662,.023,.020) # nose tip
            d+=.011*(g(x,z,.018,1.652,.012,.011)+g(x,z,-.018,1.652,.012,.011))
            d-=.015*(g(x,z,.042,1.71,.028,.018)+g(x,z,-.042,1.71,.028,.018))
            d+=.016*(g(x,z,.045,1.735,.040,.014)+g(x,z,-.045,1.735,.040,.014))
            d+=.013*(g(x,z,.066,1.684,.035,.024)+g(x,z,-.066,1.684,.035,.024))
            d+=.013*g(x,z,0,1.625,.038,.009)+.010*g(x,z,0,1.610,.035,.009)
            d-=.006*g(x,z,0,1.619,.038,.003)
            d+=.014*g(x,z,0,1.588,.055,.016)
            vs.append((x,y+d*front,z))
    for j in range(rings):
        for i in range(seg):
            a=j*seg+i; b=j*seg+(i+1)%seg
            fs.append((a,b,b+seg,a+seg))
    fs.extend([tuple(reversed(range(seg))),tuple(rings*seg+i for i in range(seg))])
    head=mesh('Warden_Face',vs,fs,MATS['Skin'],'Head')
    for s in [-1,1]:
        ell('Ear', (s*.107,-.016,1.692),(.019,.022,.039),MATS['Skin'],'Head')
        ell('EarConcha',(s*.117,.001,1.694),(.009,.008,.025),MATS['Lip'],'Head',24,16)
        # Small visible sclera, iris, pupil; fitted eyelids prevent protruding marble eyes.
        ell('EyeWhite',(s*.042,.071,1.711),(.022,.013,.010),MATS['EyeWhite'],'Head')
        ell('Iris',(s*.042,.083,1.711),(.0065,.0028,.0073),MATS['Iris'],'Head',32,16)
        ell('Pupil',(s*.042,.0855,1.711),(.003,.001,.004),MATS['Pupil'],'Head',24,12)
        for upper in [True,False]:
            pts=[]
            for i in range(25):
                a=math.pi*i/24
                pts.append((s*.042+.022*math.cos(a),.074+.005*math.sin(a),1.711+(.011 if upper else -.009)*math.sin(a)))
            line('Eyelid',pts,.0025,MATS['Skin'],'Head')
        line('Eyebrow',[(s*(.019+i*.003),.082-.012*(i/16),1.735+.007*math.sin(i/16*math.pi)) for i in range(17)],.0036,MATS['Hair'],'Head')
        ell('Nostril',(s*.013,.116,1.650),(.006,.0025,.003),MATS['Lip'],'Head',24,12)
    line('MouthSeam',[(x/1000,.083+.012*(1-(x/35)**2),1.619-.0015*math.cos(x/35*math.pi)) for x in range(-34,35,2)],.0012,MATS['Lip'],'Head')
    # Swept short hair: layered continuous scalp and individual swept ridges.
    vs,fs=[],[]
    for j in range(25):
        t=j/24
        for i in range(96):
            a=i*math.tau/96
            edge=1.744+.049*max(0,math.cos(a))-.020*max(0,-math.cos(a))
            z=edge+(1.895-edge)*math.sin(t*math.pi/2)
            r=math.cos(t*math.pi/2)
            vs.append((.110*r*math.sin(a),-.019+.102*r*math.cos(a),z))
    for j in range(24):
        for i in range(96):
            a=j*96+i;b=j*96+(i+1)%96;fs.append((a,b,b+96,a+96))
    mesh('SweptHair',vs,fs,MATS['Hair'],'Head')
    for i in range(30):
        a=i*math.tau/30; pts=[]
        for j in range(18):
            t=j/20; aa=a+t*.34
            edge=1.744+.049*max(0,math.cos(a))-.020*max(0,-math.cos(a))
            pts.append((.111*math.cos(t*math.pi/2)*math.sin(aa),-.019+.104*math.cos(t*math.pi/2)*math.cos(aa),edge+(1.899-edge)*math.sin(t*math.pi/2)))
        line('HairRidge',pts,.0018,MATS['HairHighlight'],'Head')
    return head

def build():
    global RIG,PARTS,MATS
    PARTS=[];MATS={}
    scene=bpy.data.scenes.new('Warden_High_Studio')
    bpy.context.window.scene=scene
    scene.render.fps=60
    RIG=base.armature(False)
    RIG.name='WardenRig'
    material('Skin',(.43,.235,.145),0,.5)
    material('Lip',(.13,.041,.026),0,.62)
    material('EyeWhite',(.63,.63,.55),0,.22)
    material('Iris',(.07,.12,.095),0,.25)
    material('Pupil',(.006,.008,.008),0,.23)
    material('Hair',(.032,.019,.013),0,.52)
    material('HairHighlight',(.055,.034,.019),0,.58)
    material('Steel',(.24,.29,.32),.82,.30)
    material('DarkSteel',(.062,.084,.10),.75,.4)
    material('Brass',(.46,.29,.10),.72,.32)
    material('Leather',(.073,.036,.019),0,.66)
    material('Cloth',(.16,.026,.024),0,.85)
    material('Undercloth',(.035,.045,.053),0,.92)
    material('Stitch',(.30,.20,.105),0,.82)
    sculpt_head()
    loft('Neck',[(1.46+i*.006,.068+.013*math.sin(i/24*math.pi),.069,0) for i in range(25)],MATS['Skin'],'Neck')
    # Shaped torso, with smoothly blended waist weighting beneath articulated plate.
    torso=[(.91,.177,.112),(.98,.183,.116),(1.08,.170,.109),(1.17,.185,.123),(1.28,.227,.143),(1.38,.258,.150),(1.46,.218,.121),(1.51,.099,.083)]
    rings=[];ws=[]
    for k in range(len(torso)-1):
        for j in range(6):
            t=j/6;a=torso[k];b=torso[k+1];z=a[0]*(1-t)+b[0]*t
            rings.append((z,a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t,0))
            w=max(0,min(1,(z-1.10)/.25));ws.append({'Spine':1-w,'Chest':w})
    loft('QuiltedTorso',rings,MATS['Undercloth'],weights=ws,rib=.012)
    # Curved forged cuirass: continuous convex volume, narrowed waist and raised sternum.
    rings=[]
    for j in range(34):
        t=j/33;z=1.14+t*.30
        rx=.182+.068*math.sin(t*math.pi*.73)
        ry=.129+.035*math.sin(t*math.pi*.82)
        rings.append((z,rx,ry,.010))
    loft('ForgedCuirass',rings,MATS['Steel'],rib=.007)
    for z,rx,ry,cy in [rings[0],rings[-1]]: oval_trim('RolledCuirassEdge',z,rx,ry,cy,MATS['Brass'],radius=.0038)
    # Breastplate ornamental ribs are modeled curves, not flat painted diamonds.
    for s in [-1,1]:
        for k in range(3):
            pts=[]
            for j in range(24):
                t=j/23;x=s*(.024+k*.025+t*.082);z=1.18+t*.22
                y=.010+(.137+.025*math.sin(t*math.pi))*(1-(x/.255)**2)**.5+.002
                pts.append((x,y,z))
            line('FlutedBreastRib',pts,.002,MATS['Brass'])
    ell('SunSeal',(0,.173,1.36),(.021,.006,.025),MATS['Brass'],seg=40,rings=24)
    for j in range(3):
        z=1.09-j*.042
        loft('ArticulatedFauld',[(z+i*.004,.188+i*.0017,.132+i*.0007,0) for i in range(9)],MATS['DarkSteel'],'Spine')
        oval_trim('FauldEdge',z,.188,.132,0,MATS['Brass'],'Spine',.002)
    loft('LeatherBelt',[(.988,.192,.136,0),(1.012,.195,.139,0),(1.036,.192,.136,0)],MATS['Leather'],'Hips')
    for x in [-.036,.036]: line('BuckleSide',[(x,.151,1.0),(x,.151,1.032)],.004,MATS['Brass'],'Hips')
    for z in [1.0,1.032]:line('BuckleBar',[(-.036,.151,z),(.036,.151,z)],.004,MATS['Brass'],'Hips')
    for i in range(16):
        a=i*math.tau/16;ell('BeltStud',(.195*math.sin(a),.14*math.cos(a),1.018),(.0035,.0035,.0035),MATS['Brass'],'Hips',16,8)
    for s,side in [(1,'R'),(-1,'L')]:
        # Continuous limbs: increased ring sampling and smoothly blended elbow/knee weights.
        for upper,lower,radius in [('UpperArm','Forearm',.078),('Thigh','Shin',.103)]:
            a=RIG.data.bones[upper+'.'+side];b=RIG.data.bones[lower+'.'+side]
            centers=[];weights=[];radii=[]
            for j in range(41):
                t=j/40;first=t<=.5
                p=a.head_local.lerp(a.tail_local,t*2) if first else b.head_local.lerp(b.tail_local,(t-.5)*2)
                centers.append(p);w=max(0,min(1,(t-.40)/.20));weights.append({a.name:1-w,b.name:w})
                radii.append(radius*(.8+.22*math.sin(t*math.pi*2))*(1-.38*t)*(1+.025*math.sin(t*math.pi*24)))
            o=base.tube('Tailored_'+upper+'_'+side,centers,radii,MATS['Undercloth'],weights,RIG,48);PARTS.append(o)
        for layer in range(3):
            center=(s*(.263+layer*.014),0,1.443-layer*.043)
            # Rounded overlapping shoulder lames; no cube-like plates.
            ell('PauldronLame_'+side,center,(.141-layer*.012,.143-layer*.010,.080-layer*.012),MATS['Steel'] if layer==0 else MATS['DarkSteel'],'UpperArm.'+side,64,32)
            for a in [-1.1,-.55,0,.55,1.1]:
                ell('PauldronRivet',(center[0]+s*.08*math.sin(a),.133*math.cos(a),center[2]),(.004,.004,.004),MATS['Brass'],'UpperArm.'+side,16,10)
        # Segmented leather boots, fitted greave and separate articulated knee cap.
        ell('Body_Boot_'+side,(s*.14,.074,.092),(.083,.179,.086),MATS['Leather'],'Foot.'+side,64,28)
        ell('BootSole_'+side,(s*.14,.071,.035),(.087,.184,.021),MATS['Undercloth'],'Foot.'+side,64,20)
        for j in range(4):
            y=.11+j*.027
            line('Sabatons_'+side,[(s*.14+.067*math.sin(a*math.pi/24),y,.082+.065*math.cos(a*math.pi/24)) for a in range(-12,13)],.009,MATS['DarkSteel'],'Foot.'+side)
        for name,z0,z1,r,bone in [('Greave',.18,.47,.081,'Shin.'+side),('Vambrace',.98,1.16,.062,'Forearm.'+side)]:
            centers=[];rs=[]
            for j in range(22):
                t=j/21;z=z0+(z1-z0)*t
                x=s*(.14 if name=='Greave' else .4-.04*t)
                centers.append((x,.018,z));rs.append((r*(.82+.2*math.sin(t*math.pi)),r*.93))
            tube(name+'_'+side,centers,rs,MATS['DarkSteel'],bone,48)
            for j in [1,20]:
                c=centers[j]; rr=rs[j]
                line('ArmorRim',[(c[0]+rr[0]*math.sin(i*math.tau/64),c[1]+rr[1]*math.cos(i*math.tau/64),c[2]) for i in range(65)],.003,MATS['Brass'],bone)
        ell('KneeCup',(s*.14,.060,.526),(.088,.079,.083),MATS['Steel'],'Shin.'+side,48,32)
        # Palm and curled individual glove fingers wrap the sword socket.
        ell('GlovePalm',(s*.40,.022,.879),(.044,.034,.061),MATS['Leather'],'Hand.'+side,48,28)
        for finger in range(4):
            x=s*(.373+finger*.018)
            pts=[(x,-.001,.900),(x,.014,.861),(x,.044,.847),(x,.069,.862),(x,.062,.881)]
            tube('CurledFinger',pts,[.010,.010,.009,.008,.007],MATS['Leather'],'Hand.'+side,16)
            ell('KnucklePlate',(x,.012,.882),(.009,.022,.018),MATS['Steel'],'Hand.'+side,24,16)
        tube('Thumb',[(s*.366,.028,.904),(s*.354,.052,.879),(s*.375,.070,.865)],[.014,.012,.010],MATS['Leather'],'Hand.'+side,20)
        # Split cloth tassets follow each thigh; visible seam and brass fasteners.
        vs=[];fs=[]
        for j in range(25):
            t=j/24
            for i in range(25):
                u=i/24; x=s*(.035+u*.19+t*.026);z=.977-t*.27
                y=.133+math.sin(u*math.pi*6)*.006+t*.015
                vs.append((x,y,z))
        for j in range(24):
            for i in range(24): a=j*25+i;fs.append((a,a+1,a+26,a+25))
        cloth=mesh('SplitTabard_'+side,vs,fs,MATS['Cloth'],'Thigh.'+side)
        sol=cloth.modifiers.new('ClothThickness','SOLIDIFY');sol.thickness=.004
        for j in range(24):
            z=.970-j*.0108;x=s*(.043+j/24*.026)
            line('HandStitch',[(x,.143,z),(x+s*.005,.144,z-.003)],.0011,MATS['Stitch'],'Thigh.'+side)
    # Segmented collar follows chest; remains below the jaw during torso turns.
    loft('Gorget',[(1.46,.128,.096,0),(1.478,.126,.095,0),(1.504,.099,.084,0),(1.518,.090,.080,0)],MATS['DarkSteel'])
    oval_trim('CollarRolledEdge',1.518,.090,.080,0,MATS['Brass'])
    # Reuse run/death/skill coverage, then replace attacks with authored full-body motion.
    base.animations(RIG,False)
    make_attacks()
    texture_materials()
    bpy.context.scene.frame_set(0)
    print(json.dumps({'scene':scene.name,'meshes':len(PARTS),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in PARTS)}))

def texture_materials():
    import numpy as np
    n=512;y,x=np.mgrid[0:n,0:n];rng=np.random.default_rng(823)
    for key in ['Steel','DarkSteel','Brass','Leather','Cloth','Undercloth','Skin']:
        mat=MATS[key];bsdf=mat.node_tree.nodes.get('Principled BSDF')
        color=np.array(mat.diffuse_color[:3]);noise=rng.random((n,n))
        weave=(np.sin(x*math.pi/2)*np.sin(y*math.pi/2)) if key in ['Cloth','Undercloth'] else np.sin(x*.19+y*.07)*.35
        strength=.10 if key=='Skin' else .16
        rgb=np.clip(color[None,None,:]*(1+strength*(noise-.5+weave*.3))[:,:,None],0,1)
        pix=np.ones((n,n,4),dtype=np.float32);pix[:,:,:3]=rgb
        image=bpy.data.images.new('Warden_'+key+'_Surface',n,n)
        image.pixels.foreach_set(pix.ravel());image.pack()
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
        mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])

def smooth_path(keys,t):
    # Catmull-Rom positions give continuous velocity through the contact pose.
    idx=next((i for i in range(len(keys)-1) if t<=keys[i+1][0]),len(keys)-2)
    t0,p1=keys[idx];t1,p2=keys[idx+1];p0=keys[max(0,idx-1)][1];p3=keys[min(len(keys)-1,idx+2)][1]
    u=max(0,min(1,(t-t0)/(t1-t0)))
    p0,p1,p2,p3=map(Vector,[p0,p1,p2,p3])
    return .5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)

def point_bone(name, head, tail):
    bone=RIG.pose.bones[name]
    rest=RIG.data.bones[name]
    q=(rest.tail_local-rest.head_local).rotation_difference(tail-head)
    matrix=(q.to_matrix().to_4x4() @ rest.matrix_local)
    matrix.translation=head
    bone.matrix=matrix
    bpy.context.view_layer.update()

def solve_limb(upper,lower,end,target,pole):
    a=RIG.pose.bones[upper];b=RIG.pose.bones[lower]
    start=a.head.copy();l1=RIG.data.bones[upper].length;l2=RIG.data.bones[lower].length
    v=Vector(target)-start;d=min(v.length,l1+l2-.004);axis=v.normalized()
    along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along))
    side=Vector(pole)-start;side=(side-axis*side.dot(axis)).normalized()
    elbow=start+axis*along+side*height;tip=start+axis*d
    point_bone(upper,start,elbow);point_bone(lower,elbow,tip)
    return tip

def make_attacks():
    global RIG
    for tr in list(RIG.animation_data.nla_tracks):
        if tr.name.startswith('attack_'): RIG.animation_data.nla_tracks.remove(tr)
    guard=(.41,.14,1.03)
    paths=[
      [(0,guard),(.15,(.53,-.07,1.53)),(.23,(.56,.12,1.55)),(.30,(.25,.48,1.34)),(.43,(-.15,.40,1.07)),(.55,(-.23,.26,.99)),(.78,(.32,.15,1.0)),(1,guard)],
      [(0,guard),(.15,(-.12,.28,1.24)),(.23,(-.15,.36,1.26)),(.30,(.18,.50,1.35)),(.43,(.58,.22,1.42)),(.55,(.61,.06,1.35)),(.78,(.43,.10,1.0)),(1,guard)],
      [(0,guard),(.15,(.25,-.02,1.87)),(.23,(.25,.18,1.87)),(.30,(.22,.49,1.48)),(.43,(.19,.47,.99)),(.55,(.25,.31,.93)),(.78,(.43,.15,1.02)),(1,guard)]
    ]
    for number,path in enumerate(paths,1):
        action=bpy.data.actions.new('attack_%02d'%number)
        RIG.animation_data.action=action
        for frame in range(61):
            t=frame/60;sgn=1 if number!=2 else -1
            twist=smooth_path([(0,(0,0,0)),(.17,(0,0,-18*sgn)),(.28,(0,0,10*sgn)),(.46,(0,0,20*sgn)),(.7,(0,0,8*sgn)),(1,(0,0,0))],t).z
            for pb in RIG.pose.bones:
                pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
            for name,angles in {'Hips':(0,0,twist*.35),'Spine':(4*math.sin(t*math.pi),0,twist*.30),'Chest':(5*math.sin(t*math.pi),0,twist*.35),'Head':(-3*math.sin(t*math.pi),0,-twist*.55)}.items():
                RIG.pose.bones[name].rotation_quaternion=base.world_rotation(RIG,name,angles)
            # Lower center of mass before contact; feet stay planted through leg IK.
            weight=math.sin(t*math.pi)
            RIG.pose.bones['Hips'].location=RIG.data.bones['Hips'].matrix_local.to_3x3().inverted() @ Vector((-.027*sgn*weight,.020*weight,-.035*weight))
            bpy.context.view_layer.update()
            solve_limb('Thigh.L','Shin.L','Foot.L',(-.14,.014*weight,.14),(-.14,.8,.6))
            solve_limb('Thigh.R','Shin.R','Foot.R',(.14,-.014*weight,.14+.018*weight),(.14,.8,.6))
            for side in ['L','R']:
                pb=RIG.pose.bones['Foot.'+side];mat=RIG.data.bones[pb.name].matrix_local.copy();mat.translation=pb.head;pb.matrix=mat
            bpy.context.view_layer.update()
            hand=solve_limb('UpperArm.R','Forearm.R','Hand.R',smooth_path(path,t),(.85,-.22,1.2))
            # Hand presents the edge forward at the active marker, then follows the cut.
            yaw=smooth_path([(0,(0,0,-5)),(.17,(0,0,-65*sgn)),(.30,(0,0,-6*sgn)),(.46,(0,0,60*sgn)),(.60,(0,0,75*sgn)),(1,(0,0,-5))],t).z
            pitch=smooth_path([(0,(-22,0,0)),(.17,((65 if number==3 else 30),0,0)),(.30,((5 if number==3 else -6),0,0)),(.48,(-35,0,0)),(1,(-22,0,0))],t).x
            q=Euler((math.radians(pitch),0,math.radians(yaw)),'XYZ').to_quaternion()
            mat=q.to_matrix().to_4x4() @ RIG.data.bones['Hand.R'].matrix_local
            mat.translation=hand;RIG.pose.bones['Hand.R'].matrix=mat
            left=solve_limb('UpperArm.L','Forearm.L','Hand.L',(-.27,.29,1.23+.035*math.sin(t*math.pi)),(-.65,.02,1.10))
            for pb in RIG.pose.bones:
                pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
                pb.keyframe_insert('location',frame=frame,group=pb.name)
        track=RIG.animation_data.nla_tracks.new();track.name='attack_%02d'%number
        strip=track.strips.new(track.name,0,action);strip.action_frame_start=0;strip.action_frame_end=60;track.mute=True
    RIG.animation_data.action=None
    for pb in RIG.pose.bones:pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
    bpy.context.scene.frame_set(0)

def match_idle_guard():
    """Carry the same comfortable guard into and out of the three attack clips."""
    action=next(tr.strips[0].action for tr in RIG.animation_data.nla_tracks if tr.name=='idle')
    RIG.animation_data.action=action
    for frame in range(121):
        bpy.context.scene.frame_set(frame)
        breath=.003*math.sin(frame/120*math.tau)
        hand=solve_limb('UpperArm.R','Forearm.R','Hand.R',(.41,.14,1.03+breath),(.85,-.22,1.2))
        q=Euler((math.radians(-22),0,math.radians(-5)),'XYZ').to_quaternion()
        mat=q.to_matrix().to_4x4() @ RIG.data.bones['Hand.R'].matrix_local;mat.translation=hand;RIG.pose.bones['Hand.R'].matrix=mat
        solve_limb('UpperArm.L','Forearm.L','Hand.L',(-.27,.29,1.23+breath),(-.65,.02,1.1))
        for name in ['UpperArm.R','Forearm.R','Hand.R','UpperArm.L','Forearm.L','Hand.L']:
            pb=RIG.pose.bones[name];pb.keyframe_insert('rotation_quaternion',frame=frame,group=name);pb.keyframe_insert('location',frame=frame,group=name)
    RIG.animation_data.action=None
    for pb in RIG.pose.bones:pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
    bpy.context.scene.frame_set(0)

def export():
    scene=bpy.context.scene
    RIG.animation_data.action=None
    for pb in RIG.pose.bones:pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
    scene.frame_set(0)
    # Export combined copies: one shared skin while the blend retains editable components.
    # Preserve other open scenes and data; only named character copies are exported.
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/characters/warden_high.blend'))
    copies=[]
    bpy.ops.object.select_all(action='DESELECT')
    for source in PARTS:
        if source.name=='SunSeal': continue # Exported separately as the equipment insignia.
        o=source.copy();o.data=source.data.copy();scene.collection.objects.link(o);copies.append(o)
        bpy.context.view_layer.objects.active=o
        for modifier in list(o.modifiers):
            if modifier.type!='ARMATURE': bpy.ops.object.modifier_apply(modifier=modifier.name)
        o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();combined=bpy.context.object;combined.name='WardenHighSkin'
    RIG.select_set(True)
    dest=ROOT/'game/assets/characters/warden_high.glb'
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_apply=False)
    info={'triangles':sum(len(p.vertices)-2 for p in combined.data.polygons),'bones':[b.name for b in RIG.data.bones],'clips':{tr.name:(tr.strips[0].action_frame_end-tr.strips[0].action_frame_start)/60 for tr in RIG.animation_data.nla_tracks},'source_meshes':len(PARTS),'runtime_skins':1}
    manifest_path=ROOT/'game/assets/characters/manifest.json';manifest=json.loads(manifest_path.read_text());manifest['assets']['warden_high']=info;manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    bpy.data.objects.remove(combined,do_unlink=True)
    print(json.dumps(info))

if __name__=='__main__': build()
