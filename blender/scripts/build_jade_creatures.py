"""Original Chinese fantasy creature collection, with authored skins and phase-aligned clips.

blender -b --factory-startup --python-exit-code 1 -P blender/scripts/build_jade_creatures.py
No changes to enemy data, colliders, locomotion, drops or attack timing.
"""
import bpy, math, sys, json, importlib.util
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build_characters.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
OUT=ROOT/'game/assets/creatures'; SRC=ROOT/'blender/creatures'
OUT.mkdir(parents=True,exist_ok=True);SRC.mkdir(parents=True,exist_ok=True)
PARTS=[]; RIG=None; M={}; REPORT={}

def material(name,color,metal=0,rough=.6,emission=0):
    m=base.material('Jade_'+name,color,metal,rough)
    if emission:
        s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(*color,1);s.inputs['Emission Strength'].default_value=emission
    return m

def reset():
    global PARTS,M
    base.reset();PARTS=[]
    M={'body':material('Body',(.115,.19,.165),0,.86),
       'mane':material('Mane',(.025,.052,.057),0,.82),
       'ivory':material('Ivory',(.64,.61,.43),0,.58),
       'gold':material('Gold',(.46,.28,.088),.65,.4),
       'jade':material('CarvedJade',(.092,.30,.25),.16,.36),
       'black':material('Crevices',(.009,.018,.022),0,.6),
       'eye':material('SpiritEyes',(.52,.83,.52),.12,.25,.65),
       'silk':material('CinnabarSilk',(.28,.029,.038),0,.57)}

def rig(definition):
    global RIG
    data=bpy.data.armatures.new('SpiritRig');RIG=bpy.data.objects.new('SpiritRig',data)
    bpy.context.collection.objects.link(RIG);bpy.context.view_layer.objects.active=RIG;RIG.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,head,tail,parent in definition:
        b=data.edit_bones.new(name);b.head=head;b.tail=tail
        if parent:b.parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return RIG

def mesh(name,vs,fs,mat,bone='Chest'):
    o=base.mesh_object(name,vs,fs,M[mat],[{bone:1} for _ in vs],RIG);PARTS.append(o);return o

def ell(name,at,size,mat='body',bone='Chest',segments=28,rings=16):
    o=base.ellipsoid(name,at,size,M[mat],bone,RIG,segments,rings);PARTS.append(o);return o

def curve(points,radii,steps=5):
    ps=[Vector(p) for p in points];out=[];rs=[]
    for i in range(len(ps)-1):
        a,b,c,d=ps[max(0,i-1)],ps[i],ps[i+1],ps[min(len(ps)-1,i+2)]
        for j in range(steps):
            t=j/steps;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
            r1,r2=radii[i],radii[i+1]
            rs.append(tuple(x*(1-t)+y*t for x,y in zip(r1,r2)) if isinstance(r1,tuple) else r1*(1-t)+r2*t)
    return out+[ps[-1]],rs+[radii[-1]]

def tube(name,points,radii,mat='body',bone='Chest',sides=16):
    points,radii=curve(points,radii)
    o=base.tube(name,points,radii,M[mat],[{bone:1} for _ in points],RIG,sides);PARTS.append(o);return o

def cloud(name,center,rx,rz,bone='Chest',mat='gold',width=.007):
    x,y,z=center
    ps=[(x+rx*(1-.42*j/40)*math.cos(j/40*math.pi*2.15),y,z+rz*(1-.42*j/40)*math.sin(j/40*math.pi*2.15)) for j in range(41)]
    o=base.tube(name,ps,[width]*len(ps),M[mat],[{bone:1}]*len(ps),RIG,8);PARTS.append(o)

def scale(name,cx,cy,z,width,height,bone='Chest',mat='jade'):
    vs=[(cx-width,cy,z),(cx,cy+.012,z+.04),(cx+width,cy,z),(cx+width*.65,cy+.018,z-height*.7),(cx,cy+.025,z-height),(cx-width*.65,cy+.018,z-height*.7),(cx,cy+.043,z-height*.35)]
    mesh(name,vs,[(i,(i+1)%6,6) for i in range(6)],mat,bone)

def quadruped(boar=False):
    h=.80 if boar else .87
    definition=[('Root',(0,0,0),(0,0,.18),None),('Hips',(0,-.39,h),(0,0,h),'Root'),('Chest',(0,0,h),(0,.43,h+.09),'Hips'),('Head',(0,.43,h+.09),(0,.85,h+.12),'Chest'),('Tail',(0,-.61,h),(0,-1,h+.09),'Hips')]
    for side,s in [('R',1),('L',-1)]:
        for fore,y in [('Front',.37),('Hind',-.42)]:
            x=s*(.27 if boar else .215)
            knee=(x,y+(.03 if fore=='Front' else -.10),.35)
            definition.extend([(fore+'Upper.'+side,(x,y,h),knee,'Chest' if fore=='Front' else 'Hips'),(fore+'Lower.'+side,knee,(x,y+.015,.12),fore+'Upper.'+side)])
    rig(definition)
    # Continuous torso tapers from powerful shoulders into tucked flanks.
    tube('Body',[(0,-.73,h),(0,-.48,h+.01),(0,-.10,h+.01),(0,.26,h+.055),(0,.50,h+.10)],[(.09,.12),(.29,.31 if boar else .23),(.32,.35 if boar else .25),(.39 if boar else .34,.36 if boar else .26),(.20,.23)],sides=32)
    ell('Haunch',(0,-.48,h-.08),(.32 if boar else .255,.32,.33),'body','Hips')
    for s,side in [(1,'R'),(-1,'L')]:
        for fore,y in [('Front',.37),('Hind',-.42)]:
            b=RIG.data.bones[fore+'Upper.'+side]; l=RIG.data.bones[fore+'Lower.'+side]
            tube('MuscularLeg',[b.head_local,b.head_local.lerp(b.tail_local,.42),b.tail_local],[.115 if boar else .095,.13 if boar else .10,.072],'body',b.name)
            tube('TaperedShin',[l.head_local,l.head_local.lerp(l.tail_local,.5),l.tail_local],[.075,.052,.05],'mane',l.name)
            ell('Paw',(l.tail_local.x,y+.075,.075),(.095,.143,.075),'mane',l.name,24,12)
            for k in [-1,0,1]:
                tube('Claw',[(l.tail_local.x+k*.05,y+.13,.075),(l.tail_local.x+k*.05,y+.22,.043)],[.022,.001],'ivory',l.name,10)
        # Blade-shaped ears, inset into a heavy brow rather than a spherical toy head.
        mesh('Ear',[(s*.12,.55,h+.34),(s*.22,.56,h+.57),(s*.27,.48,h+.26),(s*.17,.60,h+.32)],[(0,1,3),(1,2,3),(2,0,3)],'mane','Head')
        mesh('EarInset',[(s*.145,.575,h+.35),(s*.216,.577,h+.50),(s*.234,.52,h+.32)],[(0,1,2)],'ivory','Head')
    tube('Head',[(0,.47,h+.08),(0,.66,h+.17),(0,.83,h+.10),(0,1.02,h+.035)],[(.21,.22),(.255,.24),(.12,.14),(.075,.10)],'body','Head',32)
    tube('Jaw',[(0,.62,h-.01),(0,.84,h-.025),(0,1.03,h-.015)],[.13,.075,.05],'mane','Head',24)
    ell('Nose',(0,1.043,h+.046),(.103,.042,.065),'black','Head',24,12)
    for s in [-1,1]:
        ell('EyeSocket',(s*.142,.78,h+.178),(.049,.026,.029),'black','Head',24,12)
        ell('AlmondEye',(s*.142,.803,h+.180),(.027,.012,.011),'eye','Head',24,12)
        tube('Brow',[(s*.092,.805,h+.245),(s*.183,.796,h+.261),(s*.242,.708,h+.215)],[.024,.041,.02],'mane','Head')
        for k in range(2):
            tube('Canine',[(s*(.08+k*.035),.95-k*.13,h-.012),(s*(.08+k*.035),.96-k*.13,h-.095)],[.021,.002],'ivory','Head',10)
        # Flowing cheek mane and beard tufts establish the celestial beast silhouette.
        for k in range(5):
            tube('ManeTuft',[(s*(.18+k*.022),.55-k*.07,h+.21-k*.055),(s*(.31+k*.016),.38-k*.05,h+.14-k*.045),(s*(.30+k*.018),.23-k*.06,h+.20-k*.07)],[.071,.062,.001],'mane','Head',12)
        tube('Whisker',[(s*.12,.97,h+.075),(s*.28,1.04,h+.10),(s*.43,1.06,h+.21)],[.01,.006,.001],'ivory','Head',10)
        # Elite antlers are a separate skin that can be hidden without changing animation.
        tube('Crown_Antler',[(s*.13,.57,h+.33),(s*.20,.44,h+.57),(s*.32,.42,h+.74),(s*.40,.60,h+.78)],[.062,.045,.022,.001],'ivory','Head')
        tube('Crown_Fork',[(s*.24,.43,h+.63),(s*.27,.26,h+.73),(s*.23,.22,h+.85)],[.03,.022,.001],'gold','Head',12)
        if boar:
            tube('CurlingTusk',[(s*.14,1,h-.06),(s*.26,1.09,h-.03),(s*.30,1.10,h+.15),(s*.26,1.05,h+.30)],[.055,.047,.028,.002],'ivory','Head',20)
            for row in range(3):
                for k in range(5):
                    y=-.46+k*.16;z=h+.23-row*.095;xx=s*(.29+row*.015)
                    # Lateral scales oriented outward, distinct from the mane of the wolf.
                    scale('FlankScale',0,0,0,.068,.105,mat='jade')
                    o=PARTS[-1]
                    for v in o.data.vertices: v.co=Vector((xx+s*v.co.y,y+v.co.x,z+v.co.z))
        else:
            cloud('CheekScroll',(s*.22,.72,h+.1),.035,.055,'Head','gold',.004)
    for k in range(7):
        y=-.52+k*.14;z=h+.28+(.12 if k>3 else 0)
        tube('BackMane',[(0,y,z),(0,y-.09,z+.11),(0,y-.25,z+.15)],[.065,.043,.001],'mane','Chest',12)
    for k in range(4):
        ell('SpineJade',(0,-.40+k*.20,h+.32),(.048,.074,.027),'jade','Chest',20,12)
    tail=[(0,-.63,h+.01),(.04,-.92,h+.08),(.13,-1.12,h+.21),(.24,-1.25,h+.42),(.26,-1.18,h+.55)]
    tube('Tail',tail,[.055,.045,.038,.026,.002],'body','Tail',20)
    if not boar:
        tube('TailPlume',tail[1:],[.075,.09,.10,.003],'ivory','Tail',24)

def spider():
    definition=[('Root',(0,0,0),(0,0,.18),None),('Hips',(0,-.35,.60),(0,0,.60),'Root'),('Chest',(0,0,.56),(0,.35,.56),'Hips'),('Head',(0,.35,.56),(0,.62,.56),'Chest')]
    for s,side in [(1,'R'),(-1,'L')]:
        for k in range(4):
            y=.39-k*.26; knee=(s*(.70+abs(k-1.5)*.12),y-.03,.67)
            definition.extend([(f'Leg{k}Upper.{side}',(s*.24,y,.51),knee,'Chest'),(f'Leg{k}Lower.{side}',knee,(s*(1.0+abs(k-1.5)*.10),y+.11,.065),f'Leg{k}Upper.{side}')])
    rig(definition)
    ell('Abdomen',(0,-.46,.67),(.41,.56,.32),'jade','Hips',40,24)
    ell('Thorax',(0,.13,.55),(.30,.38,.19),'mane','Chest',32,20)
    ell('MaskHead',(0,.48,.55),(.24,.20,.17),'jade','Head',32,20)
    for s,side in [(1,'R'),(-1,'L')]:
        for k in range(4):
            b=RIG.data.bones[f'Leg{k}Upper.{side}'];l=RIG.data.bones[f'Leg{k}Lower.{side}']
            tube('LegBlade',[b.head_local,b.head_local.lerp(b.tail_local,.6)+Vector((0,0,.045)),b.tail_local],[.060,.043,.036],'jade',b.name,16)
            tube('LegHook',[l.head_local,l.head_local.lerp(l.tail_local,.75),l.tail_local],[.036,.024,.001],'mane',l.name,14)
            ell('LegJoint',b.tail_local,(.046,.046,.046),'gold',l.name,16,10)
        tube('Fang',[(s*.10,.65,.51),(s*.14,.79,.45),(s*.08,.82,.33)],[.042,.035,.002],'ivory','Head')
        for k in range(3):
            ell('Eye',(s*(.055+.05*k),.646-k*.014,.595+.029*(k%2)),(.024,.019,.025),'eye','Head',20,12)
        # Gold petal ridges hug the carapace; no billboard aura over the attack silhouette.
        tube('ShellPetal',[(s*.03,-.98,.76),(s*.30,-.72,.90),(s*.35,-.40,.85),(s*.12,-.04,.81)],[.005,.007,.007,.002],'gold','Hips',8)
        tube('Crown_Antenna',[(s*.11,.45,.70),(s*.19,.36,.83),(s*.27,.39,1.05)],[.022,.015,.001],'gold','Head',12)
    ell('AbdomenJewel',(0,-.41,.978),(.048,.070,.018),'eye','Hips',24,12)

def guardian():
    rig(base.rig_definition(True))
    # Sculpted stone armor assembled on a full articulated humanoid rig.
    tube('Torso',[(0,0,.57),(0,-.015,.77),(0,0,1.03),(0,.025,1.22)],[(.21,.18),(.29,.22),(.37,.26),(.23,.16)],'jade','Chest',32)
    for s,side in [(1,'R'),(-1,'L')]:
        for a,b in [('UpperArm','Forearm'),('Thigh','Shin')]:
            for prefix in [a,b]:
                bone=RIG.data.bones[prefix+'.'+side]
                radius=.15 if prefix in ['UpperArm','Thigh'] else .12
                tube('StoneLimb',[bone.head_local,bone.head_local.lerp(bone.tail_local,.55),bone.tail_local],[radius*.84,radius,radius*.70],'jade',bone.name,20)
        hand=RIG.data.bones['Hand.'+side].head_local
        tube('StonePalm',[hand,hand+Vector((0,.045,-.06)),hand+Vector((0,.07,-.10))],[.10,.125,.085],'mane','Hand.'+side,16)
        for finger in range(4):
            x=(finger-1.5)*.052
            tube('CarvedKnuckle',[hand+Vector((x,.06,-.01)),hand+Vector((x,.16,-.055)),hand+Vector((x,.145,-.12))],[.031,.034,.022],'jade','Hand.'+side,12)
        ell('StoneSole',(s*.25,.065,.09),(.125,.22,.09),'mane','Foot.'+side)
        for k in range(3):
            z=1.23-k*.073;cx=s*(.32+k*.022)
            vs=[(cx-s*.12,-.14,z),(cx+s*.17,-.13,z-.05),(cx+s*.20,.14,z-.09),(cx,.22,z-.01),(cx,-.01,z+.06)]
            mesh('SweptShoulder',vs,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'gold' if k==0 else 'jade','UpperArm.'+side)
        cloud('ShoulderScroll',(s*.38,.185,1.155),.08,.059,'UpperArm.'+side)
        for k in range(4):
            scale('ArmorSkirt',s*.16,.205,.74-k*.075,.128,.12,'Thigh.'+side,'mane')
        tube('Crown_Wing',[(s*.15,.04,1.58),(s*.31,-.01,1.80),(s*.36,.08,1.93)],[.055,.034,.001],'gold','Head')
        tube('MaskBrow',[(s*.025,.378,1.455),(s*.12,.382,1.48),(s*.23,.31,1.455)],[.018,.040,.022],'gold','Head')
        ell('MaskEye',(s*.10,.405,1.417),(.050,.017,.016),'eye','Head',24,12)
        cloud('MaskCheek',(s*.16,.35,1.35),.04,.04,'Head','gold',.005)
    tube('GuardianMask',[(0,.15,1.19),(0,.19,1.32),(0,.17,1.51),(0,.13,1.62)],[(.115,.13),(.21,.20),(.18,.22),(.08,.12)],'jade','Head',28)
    tube('MaskNose',[(0,.385,1.44),(0,.40,1.34),(0,.367,1.30)],[.018,.032,.022],'gold','Head',12)
    tube('MaskMouth',[(-.07,.373,1.294),(0,.385,1.285),(.07,.373,1.294)],[.008,.010,.008],'black','Head',8)
    cloud('BreastCloud',(0,.279,1.04),.15,.10)
    ell('HeartJade',(0,.294,1.04),(.046,.027,.073),'eye','Chest')
    for row in range(3):
        for col in range(6):
            x=(col-2.5)*.089;z=.83+row*.073
            scale('StoneLamella',x,.24*math.sqrt(max(.25,1-(x/.36)**2))+.008,z,.045,.081,mat='mane')
    for k in range(4):
        scale('Crown_Lotus',(k-1.5)*.055,.19,1.675+(.03 if k in [1,2] else 0),.042,.12,'Head','gold')

def lantern():
    rig([('Root',(0,0,0),(0,0,.18),None),('Hips',(0,0,.85),(0,0,1.0),'Root'),('Chest',(0,0,1.0),(0,0,1.3),'Hips'),('Head',(0,0,1.3),(0,0,1.5),'Chest')])
    ell('LanternSoul',(0,0,1.03),(.23,.23,.35),'eye','Chest',32,20)
    # Arched metal ribs and lotus caps establish an actual object around the light.
    for k in range(8):
        a=k/8*math.tau
        points=[(.26*math.sin(a)*math.sin(j/20*math.pi),.26*math.cos(a)*math.sin(j/20*math.pi),.67+j/20*.72) for j in range(21)]
        o=base.tube('LanternRib',points,[.014]*21,M['gold'],[{'Chest':1}]*21,RIG,10);PARTS.append(o)
    for z in [.69,1.36]:
        ell('LotusCap',(0,0,z),(.21,.21,.065),'jade','Chest',32,12)
    for s in [-1,1]:
        cloud('Crown_LotusWing',(s*.22,0,1.30),.17,.12,'Head','gold',.012)
    for k in range(6):
        a=k/6*math.tau
        tube('SilkStreamer',[(.14*math.sin(a),.14*math.cos(a),.70),(.20*math.sin(a+.3),.20*math.cos(a+.3),.40),(.15*math.sin(a+.6),.15*math.cos(a+.6),.13)],[.016,.025,.001],'silk','Hips',12)
    tube('LanternHook',[(0,0,1.40),(0,0,1.51),(.06,0,1.55),(.07,0,1.49)],[.016,.014,.011,.004],'gold','Head')

def animations(family):
    # 60Hz baked curves. Windup ends at .30, contact .30-.55, recovery .55-1.
    durations={'idle':2,'run':.6,'attack_01':1,'hit':.3,'death':1.2}
    RIG.animation_data_create()
    for clip,duration in durations.items():
        action=bpy.data.actions.new(clip);RIG.animation_data.action=action;end=round(duration*60)
        for frame in range(end+1):
            t=frame/end;cycle=t*math.tau
            for b in RIG.pose.bones:b.matrix_basis.identity();b.rotation_mode='QUATERNION'
            pose={};root_height=0
            if clip=='idle':
                pose={'Chest':(math.sin(cycle)*1.4,0,0),'Head':(-math.sin(cycle)*.8,0,0),'Tail':(0,0,math.sin(cycle)*7)}
                if family=='wisp':root_height=.05*math.sin(cycle)
            elif clip=='run':
                if family in ['wolf','boar']:
                    root_height=.035*math.sin(cycle*2)
                    pose={'Chest':(math.sin(cycle)*2,0,0),'Head':(-math.sin(cycle)*2,0,0),'Tail':(0,0,math.sin(cycle)*14)}
                    for side,s in [('R',1),('L',-1)]:
                        for pair,phase in [('Front',0),('Hind',math.pi)]:
                            w=math.sin(cycle+phase)*s
                            pose[pair+'Upper.'+side]=(w*27,0,0);pose[pair+'Lower.'+side]=(-max(0,-w)*37,0,0)
                elif family=='spider':
                    for side,s in [('R',1),('L',-1)]:
                        for k in range(4):
                            w=math.sin(cycle+k*math.pi)*s
                            pose[f'Leg{k}Upper.{side}']=(0,w*9,w*10);pose[f'Leg{k}Lower.{side}']=(w*10,0,0)
                elif family=='wisp':
                    root_height=.09*math.sin(cycle);pose={'Chest':(12,0,math.sin(cycle)*5)}
                else:
                    for side,s in [('R',1),('L',-1)]:
                        w=math.sin(cycle)*s
                        pose['Thigh.'+side]=(w*25,0,0);pose['Shin.'+side]=(-max(0,-w)*35,0,0)
                        pose['UpperArm.'+side]=(-w*13,0,0);pose['Forearm.'+side]=(12,0,0)
            elif clip=='attack_01':
                # Cosine interpolation gives a held anticipation and a fast, continuous snap.
                keys=[(0,0),(.22,-1),(.30,-.65),(.43,1),(.55,.75),(.78,.15),(1,0)]
                i=next((i for i in range(len(keys)-1) if t<=keys[i+1][0]),len(keys)-2)
                u=(t-keys[i][0])/(keys[i+1][0]-keys[i][0]);u=.5-.5*math.cos(math.pi*u)
                v=keys[i][1]*(1-u)+keys[i+1][1]*u
                if family in ['wolf','boar']:
                    pose={'Chest':(-v*12,0,0),'Head':(-v*20,0,0),'Hips':(v*4,0,0)}
                    for side in ['L','R']:pose['FrontUpper.'+side]=(v*10,0,0)
                elif family=='spider':
                    pose={'Chest':(-v*16,0,0),'Head':(-v*19,0,0)}
                    for side,s in [('R',1),('L',-1)]:pose['Leg0Upper.'+side]=(v*20,0,-s*v*15)
                elif family=='wisp':pose={'Chest':(-v*26,0,0),'Head':(-v*8,0,0)};root_height=-v*.12
                else:
                    reach=math.sin(math.pi*min(1,t/.75))**.65 if t<.75 else 0
                    pose={'Chest':(-v*8,0,v*20),'Head':(v*5,0,-v*12),'UpperArm.R':(reach*78,0,v*55),'Forearm.R':(reach*15,0,0),'Hand.R':(-reach*20,0,0),'UpperArm.L':(reach*26,0,-v*10)}
            elif clip=='hit':
                v=math.sin(t*math.pi)**2;pose={'Chest':(v*12,0,v*5),'Head':(v*16,0,-v*5)}
            else:
                v=min(1,max(0,(t-.1)/.65));v=v*v*(3-2*v)
                pose={'Root':(0,v*86,v*7),'Head':(-v*18,0,0)};root_height=.14*v
            for name,angles in pose.items():
                if name in RIG.pose.bones:RIG.pose.bones[name].rotation_quaternion=base.world_rotation(RIG,name,angles)
            RIG.pose.bones['Root'].location=RIG.data.bones['Root'].matrix_local.to_3x3().inverted()@Vector((0,0,root_height))
            for b in RIG.pose.bones:b.keyframe_insert('rotation_quaternion',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
        tr=RIG.animation_data.nla_tracks.new();tr.name=clip;st=tr.strips.new(clip,0,action);st.action_frame_start=0;st.action_frame_end=end;tr.mute=True
    RIG.animation_data.action=None
    for b in RIG.pose.bones:b.matrix_basis.identity()
    bpy.context.scene.frame_set(0)
    return durations

def join(parts,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();bpy.context.object.name=name
    return bpy.context.object

def finish_surfaces(family):
    """Subtle authored grain and tangent detail distinguish fur, bark, stone and chitin."""
    import numpy as np
    folder=OUT/'textures';folder.mkdir(exist_ok=True)
    y,x=np.mgrid[:256,:256]/256
    for key in ['body','mane','jade','ivory']:
        material_data=M[key];bs=material_data.node_tree.nodes.get('Principled BSDF')
        color=np.array(material_data.diffuse_color[:3])
        rng=np.random.default_rng(sum(map(ord,family+key)))
        noise=rng.random((256,256))-.5
        soft=.5*np.sin(x*math.tau*3+y*math.tau*2)+.3*np.sin(y*math.tau*7-x*math.tau*4)
        if family=='forest':grain=np.cos(x*math.tau*13+.7*np.sin(y*math.tau*3))**12;strength=.08
        elif family in ['wolf','boar'] and key in ['body','mane']:grain=np.cos(x*math.tau*53+1.4*np.sin(y*math.tau*4))**10;strength=.025
        elif family=='stonekin' or key=='jade':grain=np.sin(x*math.tau*8+np.sin(y*math.tau*5)*1.5);strength=.012
        else:grain=np.cos(x*math.tau*31)*np.cos(y*math.tau*29);strength=.014
        h=grain*strength+noise*.003+soft*.006
        variation=1+grain*.07+soft*.05+noise*.022
        for channel in ['albedo','normal']:
            pixels=np.ones((256,256,4),np.float32)
            if channel=='albedo':pixels[:,:,:3]=np.clip(color[None,None,:]*variation[:,:,None],0,1)
            else:
                dx=(np.roll(h,1,1)-np.roll(h,-1,1))*2
                dy=(np.roll(h,1,0)-np.roll(h,-1,0))*2
                normals=np.stack((dx,dy,np.ones_like(dx)),axis=2);normals/=np.linalg.norm(normals,axis=2)[:,:,None]
                pixels[:,:,:3]=normals*.5+.5
            name=family+'_'+key+'_'+channel
            im=bpy.data.images.new(name,256,256,alpha=True)
            im.colorspace_settings.name='sRGB' if channel=='albedo' else 'Non-Color'
            im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save();im.pack()
            tex=material_data.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
            if channel=='albedo':material_data.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
            else:
                normal=material_data.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.45
                material_data.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);material_data.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    for obj in PARTS:
        uv=obj.data.uv_layers.new(name='DetailUV')
        for p in obj.data.polygons:
            axis=max(range(3),key=lambda i:abs(p.normal[i]));a,b=[(1,2),(0,2),(0,1)][axis]
            for li in p.loop_indices:
                v=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=(v[a]*2.5,v[b]*2.5)

def export(family,clips):
    import bmesh
    for o in PARTS:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
    crestparts=[p for p in PARTS if p.name.startswith('Crown_')]
    skin=join([p for p in PARTS if not p.name.startswith('Crown_')],'SpiritSkin')
    if crestparts:join(crestparts,'EliteCrown')
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/(family+'.blend')))
    bpy.ops.export_scene.gltf(filepath=str(OUT/(family+'.glb')),export_format='GLB',export_yup=True,export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_apply=False)
    REPORT[family]={'bones':[b.name for b in RIG.data.bones],'clips':clips,'triangles':sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons),'runtime_skins':2 if crestparts else 1}
    studio(family)

def studio(family):
    RIG.animation_data.action=next(t.strips[0].action for t in RIG.animation_data.nla_tracks if t.name=='idle')
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.render.resolution_x=960;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('JadeStudio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.085,.09,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    for pos,power,color in [((3,4,5),480,(1,.87,.71)),((-3,1,3),370,(.70,.86,1)),((0,-4,3),540,(.73,1,.88))]:
        d=bpy.data.lights.new('Softbox','AREA');d.energy=power;d.size=4;d.color=color
        o=bpy.data.objects.new('Softbox',d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('Review');o=bpy.data.objects.new('Review',d);scene.collection.objects.link(o);scene.camera=o;d.type='ORTHO';d.ortho_scale=3.05
    dest=ROOT/'blender/renders/jade';dest.mkdir(parents=True,exist_ok=True)
    for label,pos in [('front',(2.7,4,2.6)),('rear',(-3,-4,2.6))]:
        o.location=pos;o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/(family+'_'+label+'.png'));bpy.ops.render.render(write_still=True)

def forest_spirit():
    global RIG,PARTS,M
    # Same 18 bones and clip durations as the original mossling; fully rebuilt surface.
    reset();rig(base.rig_definition(True))
    M['body']=material('Bark',(.14,.18,.085),0,.88)
    M['mane']=material('BarkShadow',(.051,.073,.030),0,.9)
    M['jade']=material('ForestJade',(.054,.24,.13),.08,.53)
    M['ivory']=material('AntlerWood',(.38,.45,.23),0,.77)
    tube('RootTorso',[(0,0,.50),(0,-.02,.74),(0,-.015,1.02),(0,.04,1.19)],[(.19,.14),(.26,.20),(.35,.22),(.23,.16)],'body','Chest',32)
    tube('CarvedForestMask',[(0,.16,1.18),(0,.22,1.31),(0,.18,1.49),(0,.09,1.59)],[(.11,.10),(.21,.16),(.24,.18),(.12,.08)],'body','Head',32)
    for s in [-1,1]:
        side='R' if s==1 else 'L'
        for name in ['UpperArm','Forearm','Thigh','Shin']:
            b=RIG.data.bones[name+'.'+side]
            radius=.14 if name=='UpperArm' else .12 if name=='Thigh' else .092
            tube('TwistedRootLimb',[b.head_local,b.head_local.lerp(b.tail_local,.45)+Vector((s*.035,0,0)),b.tail_local],[radius*.85,radius,radius*.69],'body',b.name,20)
            for groove in [-1,1]:
                offset=Vector((groove*radius*.45,radius*.82,0))
                tube('BarkRidge',[b.head_local+offset,b.head_local.lerp(b.tail_local,.45)+offset+Vector((s*.025,0,0)),b.tail_local+offset*.7],[.014,.023,.008],'mane',b.name,10)
        hand=RIG.data.bones['Hand.'+side].head_local
        tube('GraspingPalm',[hand,hand+Vector((0,.08,-.055)),hand+Vector((0,.12,-.1))],[.077,.112,.060],'body','Hand.'+side)
        for finger in range(3):
            p=hand+Vector(((finger-1)*.074,.09,-.075))
            tube('RootClaw',[p,p+Vector((s*.02,.13,-.06)),p+Vector((s*.02,.24,-.05)),p+Vector((0,.28,.01))],[.036,.030,.018,.001],'ivory','Hand.'+side,12)
        foot=RIG.data.bones['Foot.'+side].head_local
        tube('RootFoot',[foot+Vector((0,-.08,-.015)),foot+Vector((0,.08,-.02)),foot+Vector((0,.24,-.065))],[(.08,.06),(.12,.078),(.035,.018)],'body','Foot.'+side,20)
        tube('BranchAntler',[(s*.18,.03,1.51),(s*.26,-.01,1.71),(s*.38,.035,1.80),(s*.46,.17,1.88)],[.071,.048,.026,.001],'ivory','Head',16)
        tube('AntlerFork',[(s*.25,-.01,1.69),(s*.24,-.16,1.82),(s*.19,-.17,1.92)],[.031,.020,.001],'ivory','Head',12)
        ell('MaskEyeSocket',(s*.105,.374,1.408),(.082,.025,.042),'mane','Head')
        ell('MaskEye',(s*.105,.397,1.41),(.047,.014,.017),'eye','Head',24,12)
        tube('CarvedBrow',[(s*.02,.39,1.46),(s*.12,.39,1.489),(s*.23,.29,1.445)],[.019,.038,.015],'jade','Head')
        cloud('MaskCheek',(s*.145,.382,1.344),.042,.046,'Head','gold',.004)
        for k in range(4):
            x=s*(.23+k*.04);z=1.23-k*.032
            scale('LeafMantle',x,-.035,z,.078,.22,'Chest','jade')
        for k in range(3):
            x=s*(.07+k*.065)
            tube('TorsoBarkFlute',[(x,.13,.62),(x*1.3,.20,.9),(x*1.42,.16,1.16)],[.027,.043,.015],'mane','Chest',12)
    tube('MaskNose',[(0,.38,1.47),(0,.421,1.35),(0,.402,1.30)],[.019,.047,.023],'ivory','Head')
    tube('MouthCarving',[(-.13,.367,1.28),(0,.402,1.259),(.13,.367,1.28)],[.010,.014,.010],'mane','Head',10)
    for s in [-1,1]:
        tube('MaskBeard',[(s*.1,.31,1.25),(s*.08,.30,1.17),(s*.04,.27,1.11)],[.045,.029,.001],'jade','Head',12)
    cloud('HeartSeal',(0,.246,.98),.064,.065,'Chest','gold',.005)
    ell('HeartStone',(0,.266,.98),(.025,.016,.039),'jade','Chest',24,12)
    # Authored bark striations break the perfectly smooth primitive surfaces.
    for o in PARTS:
        if o.name.startswith(('RootTorso','TwistedRootLimb','CarvedForestMask','BranchAntler')):
            for v in o.data.vertices:
                v.co+=v.normal*(.005*math.sin(v.co.z*91+v.co.x*37)*math.sin(v.co.y*67))
    clips=animations('stonekin')
    finish_surfaces('forest')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/characters/briarling.blend'))
    # Export consolidated copies; editable source parts remain available.
    copies=[]
    for o in PARTS:
        c=o.copy();c.data=o.data.copy();bpy.context.collection.objects.link(c);copies.append(c)
    combined=join(copies,'BriarlingSkin')
    bpy.ops.object.select_all(action='DESELECT');combined.select_set(True);RIG.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'game/assets/characters/briarling.glb'),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_apply=False)
    mf=ROOT/'game/assets/characters/manifest.json';report=json.loads(mf.read_text())
    info=report['assets'].setdefault('briarling',{})
    info.update({'vertices':len(combined.data.vertices),'triangles':sum(len(p.vertices)-2 for p in combined.data.polygons),'meshes':1,'source_meshes':len(PARTS),'runtime_skins':1,'bones':[b.name for b in RIG.data.bones],'clips':clips,'attack_markers_normalized':{'active':.30,'recovery':.55},'run_reference_speed':3.2})
    mf.write_text(json.dumps(report,indent=2)+'\n')
    bpy.data.objects.remove(combined,do_unlink=True)
    studio('forest_spirit')

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    chosen=args[0] if args else 'all'
    for family,build in [('wolf',lambda:quadruped()),('boar',lambda:quadruped(True)),('spider',spider),('stonekin',guardian),('wisp',lantern)]:
        if chosen in ['all',family]:
            reset();build();clips=animations(family);finish_surfaces(family);export(family,clips)
    if chosen in ['all','forest']:forest_spirit()
    mf=OUT/'manifest.json';previous=json.loads(mf.read_text()) if mf.exists() else {};previous.update(REPORT);mf.write_text(json.dumps(previous,indent=2)+'\n')
