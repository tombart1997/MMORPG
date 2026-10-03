"""Hero refinement and sword choreography, reproducible from the preserved high Warden.

blender -b --factory-startup -P blender/scripts/build_warden_hero.py -- --second
An unmodified high-Warden source can also be supplied for faster incremental authoring.
The editable output retains individual fitted parts, weights and both weapon styles.
"""
import bpy, math, importlib.util, json, sys
from pathlib import Path
from mathutils import Vector, Quaternion, Euler
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wh', Path(__file__).with_name('build_warden_high.py'))
wh = importlib.util.module_from_spec(spec); spec.loader.exec_module(wh)
if 'WardenRig' not in bpy.data.objects:
    wh.build()
    for module_name,operation in [('refine_warden_high','refine'),('finish_warden_high','finish')]:
        module_spec=importlib.util.spec_from_file_location(module_name,Path(__file__).with_name(module_name+'.py'))
        module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
        getattr(module,operation)()
wh.RIG = bpy.data.objects['WardenRig']
wh.PARTS = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.find_armature() == wh.RIG]
wh.MATS = {m.name.removeprefix('Warden_'):m for m in bpy.data.materials if m.name.startswith('Warden_')}
RIG = wh.RIG
SECOND = '--second' in sys.argv

def continuous_path(keys,t):
    """Cubic Hermite path with time-aware tangents at unequal key intervals."""
    index=next((i for i in range(len(keys)-1) if t<=keys[i+1][0]),len(keys)-2)
    t1,p1=keys[index];t2,p2=keys[index+1]
    p1,p2=Vector(p1),Vector(p2);interval=t2-t1
    if index==0:m1=Vector()
    else:m1=(p2-Vector(keys[index-1][1]))/(t2-keys[index-1][0])
    if index+2>=len(keys):m2=Vector()
    else:m2=(Vector(keys[index+2][1])-p1)/(keys[index+2][0]-t1)
    u=min(1,max(0,(t-t1)/interval))
    return (2*u**3-3*u*u+1)*p1+(u**3-2*u*u+u)*interval*m1+(-2*u**3+3*u*u)*p2+(u**3-u*u)*interval*m2

wh.smooth_path=continuous_path

def smooth(a,b,x):
    t = min(1,max(0,(x-a)/(b-a))); return t*t*(3-2*t)

def proportion(v):
    x,y,z = v
    # Heroic V taper, thick limbs, tighter pelvis; retain metre-scaled height.
    widen = 1.07 + .24*smooth(1.08,1.37,z)*(1-smooth(1.51,1.62,z))
    x *= widen
    y *= 1 + .14*smooth(1.12,1.35,z)*(1-smooth(1.49,1.60,z))
    z -= .065*smooth(1.50,1.66,z)
    return Vector((x,y,z))

def refine_model():
    RIG.animation_data.action = None
    for pb in RIG.pose.bones: pb.matrix_basis.identity()
    for obj in wh.PARTS:
        for v in obj.data.vertices: v.co = proportion(v.co)
    bpy.context.view_layer.objects.active = RIG
    bpy.ops.object.mode_set(mode='EDIT')
    for b in RIG.data.edit_bones:
        b.head = proportion(b.head); b.tail = proportion(b.tail)
    bpy.ops.object.mode_set(mode='OBJECT')
    # A stronger jaw and chin with a compact, handsome face, not an enlarged skull.
    head = bpy.data.objects.get('AnatomicalHead')
    if head:
        for v in head.data.vertices:
            x,y,z = v.co
            jaw = (1-smooth(1.63,1.70,z))*smooth(1.52,1.57,z)
            v.co.x *= 1+.18*jaw
            v.co.y += .006*jaw*smooth(.00,.07,y)
        # Controlled skin colour: large facial planes, subtle stubble, reduced pore noise.
        if head.data.color_attributes.get('SkinTint'):
            attr = head.data.color_attributes['SkinTint']
            for i,v in enumerate(head.data.vertices):
                x,y,z = v.co
                beard = (1-smooth(1.63,1.68,z))*smooth(1.53,1.56,z)*smooth(.005,.045,y)
                mouth = math.exp(-(x/.028)**2-((z-1.60)/.012)**2)
                a = .45*beard*(1-mouth)
                attr.data[i].color = (1-a,1-a*.95,1-a*.9,1)
    # Replace pillow-like shoulder ellipsoids with continuous shaped plate shells.
    for obj in list(wh.PARTS):
        if obj.name.startswith(('PauldronLame','PauldronRivet')):
            wh.PARTS.remove(obj); bpy.data.objects.remove(obj,do_unlink=True)
    for s,side in [(1,'R'),(-1,'L')]:
        for layer in range(3):
            vs,fs = [],[]
            for j in range(10):
                t=j/9
                for i in range(25):
                    a=-1.48+i/24*2.96
                    x=s*(.281+.138*t+.019*layer)
                    y=(.143-.035*t)*math.sin(a)
                    z=1.46-.055*t-.046*layer+(.063-.015*t)*math.cos(a)
                    # A gentle crest and flattened outer facet communicate forged metal.
                    z += .015*math.exp(-(a/.38)**2)*(1-.3*t)
                    vs.append((x,y,z))
            for j in range(9):
                for i in range(24):
                    k=j*25+i;fs.append((k,k+1,k+26,k+25))
            obj=wh.mesh('HeroPauldron_'+side+'_'+str(layer),vs,fs,wh.MATS['Steel'] if layer==0 else wh.MATS['DarkSteel'],'UpperArm.'+side)
            sol=obj.modifiers.new('ForgedThickness','SOLIDIFY');sol.thickness=.009
            bevel=obj.modifiers.new('PlateBevel','BEVEL');bevel.width=.003;bevel.segments=2
            wh.line('ShoulderRolledLip',vs[-25:],.004,wh.MATS['Brass'],'UpperArm.'+side)
        # Muscular upper sleeves with a tailored convex biceps profile.
        upper=RIG.data.bones['UpperArm.'+side]
        centers=[upper.head_local.lerp(upper.tail_local,j/24) for j in range(25)]
        radii=[(.080+.029*math.sin(j/24*math.pi)**.7,.080+.026*math.sin(j/24*math.pi)) for j in range(25)]
        wh.tube('HeroBiceps_'+side,centers,radii,wh.MATS['Undercloth'],'UpperArm.'+side,32)
        # Broad upper thighs taper into fitted greaves rather than tubular trousers.
        thigh=RIG.data.bones['Thigh.'+side]
        centers=[thigh.head_local.lerp(thigh.tail_local,j/24) for j in range(25)]
        radii=[(.098+.019*math.sin(j/24*math.pi),.108+.017*math.sin(j/24*math.pi)) for j in range(25)]
        wh.tube('HeroThigh_'+side,centers,radii,wh.MATS['Undercloth'],'Thigh.'+side,32)
    # Breastplate has pectoral planes, a central ridge and taper into the armoured waist.
    plate=bpy.data.objects.get('ForgedCuirass')
    if plate:
        for v in plate.data.vertices:
            x,y,z=v.co
            front=smooth(.02,.13,y)
            pec=math.exp(-((abs(x)-.115)/.106)**2-((z-1.345)/.09)**2)
            v.co.y += front*(.022*pec+.013*math.exp(-(x/.032)**2))
        # Chest rib ornaments are refitted to the new breastplate surface.
        for obj in wh.PARTS:
            if obj.name.startswith(('FlutedBreastRib','SunSeal')):
                for v in obj.data.vertices:
                    x,y,z=v.co;v.co.y += .02*math.exp(-((abs(x)-.115)/.106)**2-((z-1.345)/.09)**2)+.013*math.exp(-(x/.032)**2)
    # Give the cloth a longer split fall and a shaped hem, readable from the rear too.
    for obj in wh.PARTS:
        if obj.name.startswith('SplitTabard'):
            for v in obj.data.vertices:
                t=1-smooth(.70,.97,v.co.z)
                v.co.z -= .055*t
                v.co.y += .012*t
    # Less noisy steel; clear material hierarchy under the actual Godot sunlight.
    palette={'Steel':((.29,.37,.43),.48,.47),'DarkSteel':((.078,.108,.14),.42,.52),
             'Brass':((.46,.29,.10),.62,.40),'Leather':((.041,.023,.016),0,.82),
             'Undercloth':((.025,.033,.043),0,.94),'Cloth':((.17,.022,.028),0,.9),
             'Skin':((.44,.265,.183),0,.66),'Hair':((.012,.008,.006),0,.95)}
    import numpy as np
    rng=np.random.default_rng(531)
    for key,(color,metal,rough) in palette.items():
        mat=wh.MATS[key];mat.diffuse_color=(*color,1)
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Metallic'].default_value=metal
        bsdf.inputs['Roughness'].default_value=rough
        bsdf.inputs['Base Color'].default_value=(*color,1)
        bsdf.inputs['Specular IOR Level'].default_value=.25 if key=='Skin' else .4
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                im=node.image;n=im.size[0]; yy,xx=np.mgrid[:n,:n]
                noise=rng.random((n,n))-.5
                amt=.024 if key=='Skin' else .045
                variation=1+amt*noise
                if key in ['Cloth','Undercloth']: variation += .018*np.sin(xx*math.pi/2)*np.sin(yy*math.pi/2)
                pix=np.ones((n,n,4),np.float32);pix[:,:,:3]=np.array(color)[None,None,:]*variation[:,:,None]
                im.pixels.foreach_set(pix.ravel());im.pack()
    # Recalculate winding on all newly shaped surfaces.
    if SECOND: finish_model()
    import bmesh
    for obj in wh.PARTS:
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(obj.data);bm.free()

def finish_model():
    head=bpy.data.objects.get('AnatomicalHead')
    if head:
        for v in head.data.vertices:
            x,y,z=v.co
            if z<1.59:
                t=1-smooth(1.505,1.59,z)
                v.co.x*=1-.58*t
                v.co.y*=1-.34*t
                v.co.z-=.062*t
    hair=bpy.data.objects.get('CroppedHair')
    if hair:
        # Short swept forelock with faded sides, following the existing anatomical scalp.
        for v in hair.data.vertices:
            x,y,z=v.co
            top=smooth(1.70,1.79,z)
            front=smooth(-.015,.05,y)
            v.co.z += top*(.011+.012*front)*(1-.26*abs(x)/.1)
            v.co.x += .007*top*front
        # Flatten only hairline boundary wiggles, not the surface of the scalp.
        import bmesh
        bm=bmesh.new();bm.from_mesh(hair.data)
        for v in bm.verts:
            if v.is_boundary and v.co.y>.005:
                blend=smooth(.005,.04,v.co.y)
                line_z=1.734+.007*(abs(v.co.x)/.105)**2
                v.co.z=v.co.z*(1-blend)+line_z*blend
        bm.to_mesh(hair.data);bm.free()
    # Articulated knee shields replace round cap primitives with a forged silhouette.
    for obj in list(wh.PARTS):
        if obj.name.startswith('KneeCup'):
            wh.PARTS.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)
    for s,side in [(1,'R'),(-1,'L')]:
        cx=s*.15
        outline=[(-.058,.591),(.055,.591),(.079,.548),(.050,.49),(0,.469),(-.05,.49),(-.079,.548)]
        verts=[(cx+x,.091,z) for x,z in outline]+[(cx,.128,.543)]
        faces=[(i,(i+1)%7,7) for i in range(7)]
        knee=wh.mesh('ForgedKneeShield_'+side,verts,faces,wh.MATS['Steel'],'Shin.'+side)
        sol=knee.modifiers.new('ShieldThickness','SOLIDIFY');sol.thickness=.012
        bevel=knee.modifiers.new('ShieldRolledBevel','BEVEL');bevel.width=.004;bevel.segments=3
        wh.line('KneeShieldLip',verts[:7]+[verts[0]],.0025,wh.MATS['Brass'],'Shin.'+side)
        # Upper sabaton plates follow the toe; the existing sole stays the ground contact.
        for j in range(4):
            y=.08+j*.035
            verts=[(cx-.070,y-.014,.078),(cx+.070,y-.014,.078),(cx+.064,y+.015,.073),(cx-.064,y+.015,.073),(cx,y-.014,.143-j*.009),(cx,y+.015,.135-j*.009)]
            plate=wh.mesh('HeroSabaton_'+side+'_'+str(j),verts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)],wh.MATS['DarkSteel'],'Foot.'+side)
            sol=plate.modifiers.new('SabatonsThickness','SOLIDIFY');sol.thickness=.006
    # Split rear cloth breaks up the plain back silhouette, following the thighs.
    for s,side in [(1,'R'),(-1,'L')]:
        verts=[];faces=[]
        for j in range(17):
            t=j/16
            for i in range(17):
                u=i/16;x=s*(.025+.184*u+t*.025)
                z=.979-.365*t+.018*math.sin(u*math.pi)
                y=-.15-.022*t-.004*math.cos(u*math.pi*8)
                verts.append((x,y,z))
        for j in range(16):
            for i in range(16):
                k=j*17+i;faces.append((k,k+17,k+18,k+1))
        o=wh.mesh('RearOxbloodTasset_'+side,verts,faces,wh.MATS['Cloth'],'Thigh.'+side)
        sol=o.modifiers.new('ClothWeight','SOLIDIFY');sol.thickness=.004
        wh.line('RearClothPiping',[verts[j*17] for j in range(17)],.0024,wh.MATS['Brass'],'Thigh.'+side)
    # Fitted sword-belt strap and spinal embossing make the back read as authored armor.
    for s in [-1,1]:
        points=[]
        for j in range(28):
            t=j/27;x=s*(.25-.21*t);z=1.40-.245*t
            y=-(.145+.018*math.sin(t*math.pi))*math.sqrt(max(.2,1-(x/.31)**2))-.015
            points.append((x,y,z))
        wh.tube('BackHarnessStrap',points,[(.014,.005)]*len(points),wh.MATS['Leather'],'Chest',8)
        for j in [5,13,22]:wh.ell('HarnessRivet',points[j],(.003,.003,.003),wh.MATS['Brass'],'Chest',12,8)
    wh.line('SpinePlateRidge',[(0,-.159,1.18),(0,-.176,1.27),(0,-.171,1.37),(0,-.139,1.43)],.0034,wh.MATS['Brass'],'Chest')
    print('Second fit pass: collar, swept hair, knee shields, sabatons, rear tassets',flush=True)

def set_hand(name,position,pitch,yaw):
    q=Euler((math.radians(pitch),0,math.radians(yaw)),'XYZ').to_quaternion()
    mat=q.to_matrix().to_4x4() @ RIG.data.bones[name].matrix_local
    mat.translation=position;RIG.pose.bones[name].matrix=mat
    bpy.context.view_layer.update()
    return q

def key_pose(frame):
    for pb in RIG.pose.bones:
        pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
        pb.keyframe_insert('location',frame=frame,group=pb.name)

def reset_pose():
    for pb in RIG.pose.bones:
        pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
    bpy.context.view_layer.update()

def two_hand_target(target,pitch,yaw):
    """Project the shared handle into both arm reach spheres before solving the arms."""
    target=Vector(target)
    q=Euler((math.radians(pitch),0,math.radians(yaw)),'XYZ').to_quaternion()
    offset=q@Vector((0,-.18,0))
    for iteration in range(10):
        for side,shift in [('R',Vector()),('L',offset)]:
            start=RIG.pose.bones['UpperArm.'+side].head
            reach=sum(RIG.data.bones[n+'.'+side].length for n in ['UpperArm','Forearm'])-.012
            d=target+shift-start
            if d.length>reach:target=start+d.normalized()*reach-shift
    return target

def make_clip(name,long=False,cut=0):
    action=bpy.data.actions.new('Hero_'+name);RIG.animation_data.action=action
    guard=(.30,.27,1.105) if not long else (.085,.36,1.195)
    gp,gy=(18,-23) if not long else (46,-14)
    duration=120 if cut==0 else 60
    # Paths travel through damage onset at .30 and finish the cut by .55.
    paths={
      1:[(0,guard),(.15,(.45,.10,1.44)),(.21,(.40,.30,1.40)),(.30,(.24,.53,1.32)),(.43,(-.12,.48,1.07)),(.55,(-.21,.32,.98)),(.74,(.13,.34,1.025)),(1,guard)],
      2:[(0,guard),(.18,(-.035,.30,1.20)),(.23,(-.02,.44,1.25)),(.30,(.13,.54,1.27)),(.43,(.52,.31,1.39)),(.55,(.53,.12,1.35)),(.74,(.37,.26,1.1)),(1,guard)],
      3:[(0,guard),(.14,(.20,.12,1.71)),(.21,(.18,.36,1.61)),(.30,(.17,.50,1.45)),(.43,(.14,.55,1.0)),(.55,(.22,.39,.93)),(.76,(.28,.30,1.025)),(1,guard)]}
    yaw_paths={1:[(0,(0,0,gy)),(.15,(0,0,-68)),(.21,(0,0,-52)),(.30,(0,0,-24)),(.43,(0,0,61)),(.55,(0,0,84)),(.76,(0,0,8)),(1,(0,0,gy))],
               2:[(0,(0,0,gy)),(.18,(0,0,40)),(.30,(0,0,24)),(.43,(0,0,-61)),(.55,(0,0,-80)),(.76,(0,0,-37)),(1,(0,0,gy))],
               3:[(0,(0,0,gy)),(.16,(0,0,7)),(.30,(0,0,3)),(.55,(0,0,-5)),(1,(0,0,gy))]}
    pitch_paths={1:[(0,(gp,0,0)),(.15,(30,0,0)),(.21,(17,0,0)),(.30,(-9,0,0)),(.43,(-26,0,0)),(.55,(-31,0,0)),(.76,(-10,0,0)),(1,(gp,0,0))],
                 2:[(0,(gp,0,0)),(.18,(-15,0,0)),(.30,(5,0,0)),(.43,(22,0,0)),(.55,(25,0,0)),(.76,(12,0,0)),(1,(gp,0,0))],
                 3:[(0,(gp,0,0)),(.14,(90,0,0)),(.21,(54,0,0)),(.30,(-3,0,0)),(.43,(-64,0,0)),(.55,(-78,0,0)),(.76,(-17,0,0)),(1,(gp,0,0))]}
    for frame in range(duration+1):
        t=frame/duration; reset_pose()
        breath=math.sin(t*math.tau)*.003 if cut==0 else 0
        sgn=-1 if cut==2 else 1
        # The pelvis initiates the cut; the shoulders unwind slightly later.
        # Bake this before arm IK so the sword grip survives the stronger body motion.
        body_keys=[(0,(0,0,0)),(.16,(0,0,-45*sgn)),(.25,(0,0,-20*sgn)),(.30,(0,0,7*sgn)),(.46,(0,0,52*sgn)),(.70,(0,0,21*sgn)),(1,(0,0,0))]
        twist=0 if cut==0 else wh.smooth_path(body_keys,t).z * (.48 if cut==3 else 1)
        hips_twist=0 if cut==0 else wh.smooth_path(body_keys,min(1,t+.035*math.sin(math.pi*t))).z * (.48 if cut==3 else 1)
        lean=0 if cut==0 else wh.smooth_path([(0,(0,0,0)),(.16,(-9 if cut==3 else -5,0,0)),(.30,(7,0,0)),(.48,(19 if cut==3 else 12,0,0)),(.72,(5,0,0)),(1,(0,0,0))],t).x
        bank=0 if cut==0 else math.sin(t*math.tau)*4*sgn*(.3 if cut==3 else 1)
        for bone_name,angles in {'Hips':(lean*.18,bank*.4,hips_twist*.35),'Spine':(lean*.32,bank*.3,twist*.25),'Chest':(lean*.50,bank*.3,twist*.40),'Head':(-lean*.65,-bank*.5,-twist*.80)}.items():
            RIG.pose.bones[bone_name].rotation_quaternion=wh.base.world_rotation(RIG,bone_name,angles)
        weight=0 if cut==0 else math.sin(t*math.pi)
        drop=.035 if long else .022
        shift=Vector() if cut==0 else wh.smooth_path([(0,(0,0,0)),(.16,(-.055*sgn,-.025,-.020)),(.30,(.012*sgn,.035,-.035)),(.48,(.065*sgn,.075,-.055 if cut==3 else -.040)),(.74,(.028*sgn,.025,-.015)),(1,(0,0,0))],t)
        RIG.pose.bones['Hips'].location=RIG.data.bones['Hips'].matrix_local.to_3x3().inverted() @ (shift+Vector((0,0,-drop-breath)))
        bpy.context.view_layer.update()
        for side,s in [('L',-1),('R',1)]:
            # Staggered footing, stable contact patches throughout the cut.
            foot=(s*(.19 if long else .177),(.11 if s==-1 else -.055),.14)
            wh.solve_limb('Thigh.'+side,'Shin.'+side,'Foot.'+side,foot,(s*.22,.85,.6))
            pb=RIG.pose.bones['Foot.'+side];mat=RIG.data.bones[pb.name].matrix_local.copy()
            # Small planted pivots, rather than sliding both boots with the pelvis.
            pivot=math.radians(hips_twist*.24*(1 if s==sgn else .5))
            mat=Euler((0,0,pivot)).to_matrix().to_4x4() @ mat
            mat.translation=pb.head;pb.matrix=mat
        bpy.context.view_layer.update()
        hand_target=Vector(guard) if cut==0 else wh.smooth_path(paths[cut],t)
        if long and cut>0: hand_target.x=guard[0]+(hand_target.x-guard[0])*.70
        hand_target.z+=breath
        pitch=gp if cut==0 else wh.smooth_path(pitch_paths[cut],t).x
        yaw=gy if cut==0 else wh.smooth_path(yaw_paths[cut],t).z
        if long: hand_target=two_hand_target(hand_target,pitch,yaw)
        right=wh.solve_limb('UpperArm.R','Forearm.R','Hand.R',hand_target,(.9,-.16,1.15))
        q=set_hand('Hand.R',right,pitch,yaw)
        if long:
            # Offhand palm remains on the extended handle in every frame, including recovery.
            # Socket offsets are in model coordinates and rotate with this same blade basis.
            left_target=right + q @ Vector((0,-.18,0))
            left=wh.solve_limb('UpperArm.L','Forearm.L','Hand.L',left_target,(-.73,-.13,1.10))
            set_hand('Hand.L',left,pitch,yaw)
        else:
            free=Vector((-.30,.30,1.24+breath))
            if cut>0:
                free=Euler((0,0,math.radians(twist*.55))).to_matrix() @ (free-Vector((0,0,1.1)))+Vector((0,0,1.1))+shift*.5
            left=wh.solve_limb('UpperArm.L','Forearm.L','Hand.L',free,(-.70,-.06,1.05))
            set_hand('Hand.L',left,10,12)
        key_pose(frame)
    track=RIG.animation_data.nla_tracks.new()
    strip=track.strips.new(name,0,action);strip.action_frame_start=0;strip.action_frame_end=duration;track.mute=True
    track.name=name
    RIG.animation_data.action=None

def animate():
    # IK only needs bones. Avoid evaluating the detailed skinned meshes during baking.
    modifiers=[m for obj in wh.PARTS for m in obj.modifiers if m.show_viewport]
    for m in modifiers: m.show_viewport=False
    for tr in list(RIG.animation_data.nla_tracks):
        if tr.name=='idle' or tr.name.startswith(('attack_','longsword_')): RIG.animation_data.nla_tracks.remove(tr)
    make_clip('idle')
    make_clip('longsword_idle',True)
    for i in range(1,4):
        make_clip('attack_%02d'%i,False,i)
        make_clip('longsword_%02d'%i,True,i)
    make_long_run()
    reset_pose();RIG.animation_data.action=None;bpy.context.scene.frame_set(0)
    for m in modifiers: m.show_viewport=True
    print('HERO_CLIPS', [tr.name for tr in RIG.animation_data.nla_tracks],flush=True)

def make_long_run():
    original=next(tr.strips[0].action for tr in RIG.animation_data.nla_tracks if tr.name=='run')
    action=bpy.data.actions.new('Hero_longsword_run')
    for frame in range(37):
        RIG.animation_data.action=original;bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        bob=.016*math.sin(frame/36*math.tau*2)
        right=wh.solve_limb('UpperArm.R','Forearm.R','Hand.R',two_hand_target((.085,.36,1.195+bob),40,-14),(.85,-.16,1.12))
        q=set_hand('Hand.R',right,40,-14)
        left=wh.solve_limb('UpperArm.L','Forearm.L','Hand.L',right+q@Vector((0,-.18,0)),(-.70,-.12,1.08))
        set_hand('Hand.L',left,40,-14)
        RIG.animation_data.action=action;key_pose(frame)
    track=RIG.animation_data.nla_tracks.new()
    strip=track.strips.new('longsword_run',0,action);strip.action_frame_start=0;strip.action_frame_end=36
    track.name='longsword_run';track.mute=True;RIG.animation_data.action=None

def studio_render(label):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
    scene.cycles.use_denoising=True
    scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('HeroStudioWorld');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.075,.095,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    scene.view_settings.view_transform='AgX'
    lights=[]
    for at,energy,size,color in [((3,4,5),450,4,(1,.88,.75)),((-3,1,3),330,3,(.65,.78,1)),((1,-3,4),550,3,(.8,.86,1))]:
        data=bpy.data.lights.new('StudioSoftbox','AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
        obj=bpy.data.objects.new('StudioSoftbox',data);scene.collection.objects.link(obj);obj.location=at
        obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler();lights.append(obj)
    cam_data=bpy.data.cameras.new('HeroReviewCamera');cam=bpy.data.objects.new('HeroReviewCamera',cam_data);scene.collection.objects.link(cam);scene.camera=cam
    cam_data.type='ORTHO';cam_data.ortho_scale=2.28
    dest=ROOT/'blender/renders/hero';dest.mkdir(parents=True,exist_ok=True)
    action=next(tr.strips[0].action for tr in RIG.animation_data.nla_tracks if tr.name=='idle')
    RIG.animation_data.action=action;scene.frame_set(0)
    for name,pos in [('front',(0,4,1.7)),('threequarter',(3,4,2.25)),('rear',(-3,-4,2.7))]:
        cam.location=pos;cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(dest/(label+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
    cam_data.ortho_scale=.57;cam.location=(.85,3,1.84);cam.rotation_euler=(Vector((0,0,1.66))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(dest/(label+'_portrait.png'));bpy.ops.render.render(write_still=True)
    RIG.animation_data.action=None;reset_pose()
    for obj in lights+[cam]: bpy.data.objects.remove(obj,do_unlink=True)

if __name__=='__main__':
    bpy.context.scene.render.fps=60
    refine_model();animate()
    studio_render('hero_pass2' if SECOND else 'hero_pass1')
    wh.export()
