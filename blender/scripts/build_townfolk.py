"""Shared townfolk kit: one compatible 18-bone rig, interchangeable skinned modules.

Run Blender --background --python blender/scripts/build_townfolk.py.
Editable source keeps anatomical/clothing parts; export joins each logical module.
No gameplay animations or player assets are overwritten.
"""
import bpy, math, json, importlib.util
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('townfolk_base', Path(__file__).with_name('build_characters.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
RIG = None
MAT = None
MODULES = {}
PARTS = []

def finish(obj, tile, shade=(1,1,1)):
    PARTS.append(obj)
    uv = obj.data.uv_layers.new(name='PaintedAtlas')
    colors = obj.data.color_attributes.new(name='PaintedShadows', type='FLOAT_COLOR', domain='CORNER')
    coords = [v.co for v in obj.data.vertices]
    lo = [min(v[i] for v in coords) for i in range(3)]
    hi = [max(v[i] for v in coords) for i in range(3)]
    for polygon in obj.data.polygons:
        axis = max(range(3),key=lambda i:abs(polygon.normal[i]))
        a,b = [(1,2),(0,2),(0,1)][axis]
        for li in polygon.loop_indices:
            v = obj.data.vertices[obj.data.loops[li].vertex_index].co
            u = (v[a]-lo[a])/max(.001,hi[a]-lo[a]); w = (v[b]-lo[b])/max(.001,hi[b]-lo[b])
            uv.data[li].uv = ((tile%3+.045+u*.91)/3, 1-(tile//3+.045+w*.91)/3)
            # Painted shadow remains visible under broad ambient lighting.
            depth = .81+.19*w
            colors.data[li].color = (*[c*depth for c in shade],1 if tile==2 and not obj.name.startswith(('Eye','IvoryStole','RolledCuff')) else 0)
    return obj

def mesh(name, vs, fs, tile, bone='Chest', weights=None, shade=(1,1,1)):
    return finish(base.mesh_object(name,vs,fs,MAT,weights or [{bone:1} for _ in vs],RIG),tile,shade)

def ell(name, p, scale, tile, bone='Chest', seg=16, rings=10, shade=(1,1,1)):
    return finish(base.ellipsoid(name,p,scale,MAT,bone,RIG,seg,rings),tile,shade)

def tube(name, pts, radii, tile, bone='Chest', weights=None, sides=10, shade=(1,1,1)):
    return finish(base.tube(name,pts,radii if isinstance(radii,list) else [radii]*len(pts),MAT,weights or [{bone:1} for _ in pts],RIG,sides),tile,shade)

def loft(name, rings, tile, bone='Chest', sides=24, weights=None, pleat=0):
    vs,fs,ws=[],[],[]
    for j,(z,rx,ry,cy) in enumerate(rings):
        for i in range(sides):
            a=i*math.tau/sides; r=1+pleat*math.cos(a*12)
            vs.append((rx*math.sin(a)*r,cy+ry*math.cos(a)*r,z))
            ws.append(weights[j] if weights else {bone:1})
    for j in range(len(rings)-1):
        for i in range(sides):
            a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
    fs += [tuple(reversed(range(sides))),tuple((len(rings)-1)*sides+i for i in range(sides))]
    return mesh(name,vs,fs,tile,bone,ws)

def ribbon(name, pts, width, tile, bone='Chest'):
    vs=[]
    for x,y,z in pts: vs += [(x-width/2,y,z),(x+width/2,y,z)]
    return mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)],tile,bone)

def module(name, fn):
    start=len(PARTS);fn(); MODULES[name]=PARTS[start:]

def face(female):
    # Continuous jaw/cheek/brow/nose planes, exaggerated slightly for the game camera.
    seg=32;profiles=[(1.57,.030,.048),(1.60,.073,.078),(1.64,.098,.094),
        (1.69,.108,.103),(1.74,.105,.094),(1.79,.105,.087),(1.84,.078,.071),(1.875,.015,.013)]
    vs,fs=[],[];sx=.92 if female else 1.02
    def g(x,z,cx,cz,wx,wz): return math.exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
    for k in range(len(profiles)-1):
        for j in range(3):
            t=j/3;a,b=profiles[k],profiles[k+1];z=a[0]*(1-t)+b[0]*t
            rx=(a[1]*(1-t)+b[1]*t)*sx;ry=a[2]*(1-t)+b[2]*t
            for i in range(seg):
                angle=i*math.tau/seg;x=rx*math.sin(angle);front=max(0,math.cos(angle))**5
                sculpt=.021*g(x,z,0,1.69,.020,.056)+.033*g(x,z,0,1.675,.025,.016)
                sculpt+=.010*(g(x,z,.057,1.70,.033,.025)+g(x,z,-.057,1.70,.033,.025))
                sculpt-=.010*(g(x,z,.041,1.73,.025,.014)+g(x,z,-.041,1.73,.025,.014))
                sculpt+=.012*g(x,z,0,1.626,.040,.010)
                vs.append((x,ry*math.cos(angle)-.006+sculpt*front,z))
    n=len(vs)//seg
    for j in range(n-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
    fs += [tuple(reversed(range(seg))),tuple((n-1)*seg+i for i in range(seg))]
    mesh('ShapedFace',vs,fs,0,'Head',shade=(1,.95,.92) if female else (.88,.76,.65))
    for s in [-1,1]:
        ell('Ear',(s*.105,-.007,1.717),(.017,.021,.032),0,'Head',12,8)
        ell('EyeSocket',(s*.041,.082,1.732),(.027,.009,.012),1,'Head',12,6,shade=(.45,.40,.37))
        ell('Eye',(s*.041,.091,1.732),(.019,.005,.007),2,'Head',12,6)
        ell('Iris',(s*.041,.096,1.732),(.006,.002,.007),1,'Head',10,6)
        tube('Brow',[(s*.020,.091,1.756),(s*.043,.094,1.762),(s*.064,.077,1.751)],[.003,.004,.002],1,'Head',sides=6)
        tube('UpperLid',[(s*.022,.094,1.733),(s*.040,.097,1.739),(s*.060,.088,1.734)],.0023,1,'Head',sides=6)
    tube('Mouth',[(-.027,.083,1.63),(0,.094,1.626),(.027,.083,1.631)],[.0015,.0025,.0015],4,'Head',sides=6,shade=(.49,.28,.24))
    tube('LowerLip',[(-.023,.086,1.621),(0,.091,1.620),(.023,.086,1.622)],.0027,0,'Head',sides=6,shade=(.77,.55,.5))

def foundation(female):
    loft('Neck',[(1.46,.065,.067,0),(1.54,.060,.059,0),(1.59,.065,.059,0)],0,'Neck',16)
    broad=.91 if female else 1.09
    # The continuous clothed torso follows shoulders, ribcage, waist and pelvis.
    rings=[(.87,.174,.109,0),(.98,.180,.12,0),(1.08,.158,.100,0),(1.19,.18,.111,0),
        (1.32,.219,.133,.010),(1.41,.239,.132,0),(1.46,.225,.100,0),(1.50,.083,.068,0)]
    weights=[{'Hips':1},{'Hips':.8,'Spine':.2},{'Spine':1},{'Spine':.65,'Chest':.35},{'Chest':1},{'Chest':1},{'Chest':1},{'Chest':1}]
    loft('Torso',[(z,rx*broad,ry,cy) for z,rx,ry,cy in rings],2,weights=weights)
    for side,s in [('L',-1),('R',1)]:
        upper=RIG.data.bones['UpperArm.'+side];lower=RIG.data.bones['Forearm.'+side]
        pts=[upper.head_local,upper.head_local.lerp(upper.tail_local,.4),upper.tail_local,lower.head_local.lerp(lower.tail_local,.45),lower.tail_local]
        ws=[{upper.name:1},{upper.name:1},{upper.name:.5,lower.name:.5},{lower.name:1},{lower.name:1}]
        tube('Sleeve_'+side,pts[:3],[.086*broad,.094*broad,.067],2,weights=ws[:3],sides=16)
        tube('Forearm_'+side,pts[2:],[.065,.074,.045],0,weights=ws[2:],sides=16,shade=(.87,.84,.80))
        hand='Hand.'+side
        ell('Palm_'+side,(s*.402,.024,.884),(.044,.041,.064),0,hand,14,10)
        # Separate thumb and fitted fingers give the hand a readable silhouette.
        for k in range(4):
            x=s*(.375+k*.017)
            tube('Finger',[(x,.045,.873),(x,.067,.843),(x,.061,.818+k*.003)],[.010,.010,.006],0,hand,sides=7)
        tube('Thumb',[(s*.367,.015,.899),(s*.350,.055,.865)],[.017,.012],0,hand,sides=8)
        hip=RIG.data.bones['Thigh.'+side];shin=RIG.data.bones['Shin.'+side]
        pts=[hip.head_local,hip.head_local.lerp(hip.tail_local,.32),hip.tail_local,shin.head_local.lerp(shin.tail_local,.50),shin.tail_local]
        ws=[{hip.name:1},{hip.name:1},{hip.name:.5,shin.name:.5},{shin.name:1},{shin.name:1}]
        tube('Trousers_'+side,pts,[.104,.104,.077,.078,.054],2,weights=ws,sides=16,shade=(.52,.55,.57))
        tube('BootShaft_'+side,[(s*.14,0,.15),(s*.14,.008,.28),(s*.14,.015,.44)],[.075,.082,.085],4,'Shin.'+side,sides=16)
        ell('Boot_'+side,(s*.14,.068,.09),(.081,.164,.079),4,'Foot.'+side,16,10)
        ell('Sole_'+side,(s*.14,.068,.029),(.085,.168,.025),1,'Foot.'+side,16,6)
    loft('Sash',[(.968,.19,.126,0),(1.015,.178,.117,0)],4,'Hips',24)

def tunic():
    loft('SplitTunic',[(.65,.235,.157,0),(.79,.206,.133,0),(.95,.183,.120,0)],2,'Hips',32,pleat=.022)
    ribbon('CrossCollar',[(-.07,.087,1.50),(.11,.139,1.31),(.065,.123,1.12)],.045,5)
    ribbon('CrossCollar',[(-.085,.087,1.48),(-.11,.139,1.32),(-.063,.123,1.12)],.040,4)
    ribbon('BeltTail',[(-.13,.149,.99),(-.17,.167,.82),(-.18,.173,.72)],.055,4,'Hips')

def robe():
    loft('PleatedKeeperRobe',[(.17,.335,.230,.008),(.29,.320,.218,0),(.54,.277,.177,0),(.77,.219,.153,0),(.99,.180,.122,0)],3,'Hips',40,pleat=.04)
    loft('RobeHem',[(.17,.339,.234,.008),(.22,.335,.232,.008)],5,'Hips',40)
    loft('RobeTorso',[(1.015,.182,.127,0),(1.20,.186,.121,0),(1.39,.227,.142,0),(1.46,.210,.115,0)],3,weights=[{'Spine':1},{'Spine':.7,'Chest':.3},{'Chest':1},{'Chest':1}])
    for side,s in [('L',-1),('R',1)]:
        a=RIG.data.bones['UpperArm.'+side];b=RIG.data.bones['Forearm.'+side]
        tube('WideSleeve',[a.head_local,a.tail_local,b.tail_local],[.126,.124,.152],3,weights=[{a.name:1},{a.name:.5,b.name:.5},{b.name:1}],sides=16)
        tube('Cuff',[b.tail_local,b.tail_local+Vector((s*.003,0,-.032))],[.155,.156],5,b.name,sides=16)
    ribbon('IvoryStole',[(-.11,.082,1.50),(-.17,.159,1.38),(-.13,.147,1.10),(-.10,.160,.88),(-.12,.184,.58)],.11,2)
    ribbon('IvoryStole',[(.11,.082,1.50),(.17,.159,1.38),(.13,.147,1.10),(.10,.160,.88),(.12,.184,.58)],.11,2)
    loft('KeeperSash',[(.98,.19,.137,0),(1.045,.18,.127,0)],5,'Spine',32)

def apron():
    # Curved leather bib/tasset with scalloped hem, straps, pockets, seam and rivets.
    vs=[];rows=[(1.34,.135,.147),(1.15,.165,.135),(.99,.19,.153),(.78,.225,.182),(.55,.24,.190),(.40,.22,.201)]
    for z,w,y in rows:
        for i in range(9):
            x=(i/8*2-1)*w;vs.append((x,y-.030*(x/w)**2,z+(.015*math.cos(i*.8) if z<.5 else 0)))
    mesh('WornApron',vs,[(j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i) for j in range(5) for i in range(8)],4,weights=[{'Chest':1} if v[2]>1.24 else {'Spine':1} if v[2]>1.04 else {'Hips':1} for v in vs])
    for s in [-1,1]:
        ribbon('ApronStrap',[(s*.125,.13,1.34),(s*.125,.085,1.51),(s*.12,-.095,1.38)],.040,4)
        tube('ApronSeam',[(s*w,y-.03,z) for z,w,y in rows],.003,5,'Spine',sides=6)
    ell('Pocket',(.07,.198,.77),(.100,.019,.097),4,'Hips',12,8,shade=(.7,.75,.76))
    for x in [-.1,.1]:ell('BibRivet',(x,.155,1.30),(.009,.004,.009),5,'Chest',8,6)

def hair(style):
    vs,fs=[],[];seg=32
    for j in range(9):
        t=j/8
        for i in range(seg):
            a=i*math.tau/seg;edge=1.734+.066*max(0,math.cos(a))-.009*max(0,-math.cos(a))
            z=edge+(1.895-edge)*math.sin(t*math.pi/2);r=max(.02,math.cos(t*math.pi/2))
            vs.append((.111*r*math.sin(a),-.017+.100*r*math.cos(a),z))
    for j in range(8):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
    mesh('HairCap',vs,fs,1,'Head')
    for i in range(9):
        a=(i/8*1.4-.7);tube('SweptLock',[(.098*math.sin(a),.09*math.cos(a),1.80),(.083*math.sin(a+.3),.096*math.cos(a+.3),1.85),(.03*math.sin(a+.8),.02,1.899)],[.008,.012,.004],1,'Head',sides=6)
    if style=='bun':
        ell('CoiledBun',(0,-.12,1.78),(.092,.075,.084),1,'Head',20,12)
        tube('Hairpin',[(-.15,-.12,1.82),(.16,-.12,1.82)],.007,5,'Head',sides=8)
        ell('JadePin',(.17,-.12,1.82),(.018,.012,.024),8,'Head',12,8)
        for s in [-1,1]: tube('TempleLock',[(s*.10,.007,1.79),(s*.107,.026,1.68),(s*.115,.045,1.57)],[.015,.012,.003],1,'Head',sides=8)
    if style=='topknot':
        ell('Topknot',(0,-.02,1.931),(.050,.052,.065),1,'Head',16,10)
        tube('Tie',[(0,-.02,1.89),(0,-.02,1.912)],[.053,.053],4,'Head',sides=12)

def gear(kind):
    if kind=='keeper':
        # Broad layered shoulder shawl, cloud-like swept tips and a quiet jade pendant.
        for s in [-1,1]:
            ell('KeeperShawl',(s*.215,-.020,1.44),(.15,.13,.055),3,'Chest',20,10)
            tube('ShawlEdge',[(s*.07,.112,1.46),(s*.24,.114,1.43),(s*.34,.024,1.46)],[.008,.010,.003],5,sides=8)
        for i in range(9):
            a=i/8*math.pi;ell('PrayerBead',(.11*math.cos(a),.146,1.37-.12*math.sin(a)),(.011,.012,.013),5,seg=8,rings=6)
        ell('JadeWaystoneSeal',(0,.163,1.205),(.031,.014,.048),8,seg=16,rings=10)
        ribbon('Talisman',[(-.185,.183,.99),(-.22,.195,.81),(-.20,.219,.68)],.052,7,'Hips')
    elif kind=='smith':
        # Beard planes, rolled cuffs, hammer and belt tongs are profession modules.
        vs=[]
        for row in range(4):
            for i in range(17):
                t=i/16;x=(t*2-1)*(.086-row*.006)
                top=1.633+.018*abs(t*2-1)
                z=top-row*.020+math.sin(i*1.6)*.0015
                vs.append((x,.055+.034*math.sin(t*math.pi)-row*.004,z))
        mesh('ShapedBeard',vs,[(j*17+i,j*17+i+1,(j+1)*17+i+1,(j+1)*17+i) for j in range(3) for i in range(16)],1,'Head')
        for s in [-1,1]:tube('Moustache',[(0,.103,1.652),(s*.025,.092,1.648),(s*.043,.084,1.642)],[.003,.006,.003],1,'Head',sides=8)
        for s,side in [(-1,'L'),(1,'R')]:
            tube('RolledCuff',[(s*.359,.006,1.18),(s*.365,.009,1.145)],[.074,.075],2,'Forearm.'+side,sides=16)
        tube('HammerHandle',[(.232,.093,.70),(.264,.108,1.012)],.015,4,'Hips',sides=8)
        tube('HammerHead',[(.211,.106,1.013),(.312,.106,1.013)],.043,6,'Hips',sides=6)
        for x in [-.217,-.246]:tube('BeltTongs',[(x,.093,1.0),(x,.137,.77),(x-.015,.156,.73)],[.008,.006,.011],6,'Hips',sides=6)
    else:
        ell('Satchel',(.238,.047,.833),(.094,.076,.131),4,'Hips',16,10)
        ribbon('SatchelStrap',[(-.17,.075,1.48),(0,.15,1.27),(.17,.137,1.01),(.24,.071,.91)],.036,4)
        ell('Buckle',(.238,.124,.873),(.023,.006,.019),5,'Hips',10,6)
        if kind=='artificer':
            for i in range(3):tube('Scroll',[(.26,-.054+i*.030,.75),(.26,-.054+i*.030,.96)],.025,7,'Hips',sides=10)
        if kind=='guard':
            for s in [-1,1]:ell('LacquerShoulder',(s*.22,0,1.46),(.115,.12,.07),6,'Chest',16,10)
            loft('LacquerGuard',[(1.10,.176,.13,0),(1.22,.208,.142,0),(1.37,.235,.15,0)],6,'Chest',24)

def idle_clips():
    RIG.animation_data_create()
    for clip,duration in [('idle',6),('keeper_idle',8),('smith_idle',7)]:
        action=bpy.data.actions.new(clip);RIG.animation_data.action=action
        end=int(duration*60)
        for frame in range(0,end+1,4):
            t=frame/end;breath=math.sin(t*math.tau)
            pose={'Chest':(breath*.8,0,breath*.3),'Head':(math.sin(t*math.tau)*1.2,0,math.sin(t*math.tau)*3),
                  'Forearm.L':(8+breath*2,0,0),'Forearm.R':(10-breath*2,0,0),
                  'UpperArm.L':(3,0,-3),'UpperArm.R':(3,0,3),'Hips':(0,0,breath*.35)}
            if clip=='keeper_idle':
                pose.update({'UpperArm.L':(7+breath*1.2,0,-5),'Forearm.L':(35+breath*2,0,0),'Head':(-2+breath,0,math.sin(t*math.tau)*3)})
            if clip=='smith_idle':
                pause=math.sin(math.pi*max(0,min(1,(t-.35)/.30)))**2 if .35<t<.65 else 0
                pose.update({'UpperArm.R':(8+pause*13,0,5),'Forearm.R':(16+pause*22,0,0),'Head':(2+pause*6,0,-pause*6)})
            for bone in RIG.pose.bones:
                bone.rotation_mode='QUATERNION';bone.rotation_quaternion=base.world_rotation(RIG,bone.name,pose.get(bone.name,(0,0,0)))
                bone.location=(0,0,0);bone.keyframe_insert('rotation_quaternion',frame=frame,group=bone.name)
        track=RIG.animation_data.nla_tracks.new();track.name=clip
        strip=track.strips.new(clip,0,action);strip.action_frame_start=0;strip.action_frame_end=end;track.mute=True
    RIG.animation_data.action=None
    for bone in RIG.pose.bones:bone.rotation_quaternion=Quaternion();bone.location=(0,0,0)
    bpy.context.scene.frame_set(0)

def build():
    global RIG,MAT
    base.reset();RIG=base.armature(False);RIG.name='TownfolkRig'
    MAT=base.material('TownfolkPainted',(1,1,1),0,.93)
    tex=bpy.data.images.load(str(ROOT/'game/assets/characters/townfolk_atlas.png'))
    tex.pack();node=MAT.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex
    MAT.node_tree.links.new(node.outputs['Color'],MAT.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    MAT.use_backface_culling=False
    module('Body_Male',lambda:foundation(False));module('Body_Female',lambda:foundation(True))
    module('Head_Male',lambda:face(False));module('Head_Female',lambda:face(True))
    module('Clothes_Tunic',tunic);module('Clothes_Robe',robe);module('Clothes_Apron',apron)
    for style in ['swept','bun','topknot']: module('Hair_'+style.capitalize(),lambda s=style:hair(s))
    for kind in ['keeper','smith','merchant','artificer','guard']:module('Gear_'+kind.capitalize(),lambda k=kind:gear(k))
    idle_clips()
    source=ROOT/'blender/characters/townfolk_kit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(source))
    # Mesh/material resources are shared between every runtime resident. Invisible variants
    # are removed when instantiated. Source remains an editable library of parts.
    counts={}
    for name,parts in MODULES.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in parts:obj.select_set(True)
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();bpy.context.object.name=name
        counts[name]=sum(len(p.vertices)-2 for p in bpy.context.object.data.polygons)
    info=base.validate(RIG)
    info.update({'bones':[b.name for b in RIG.data.bones],'modules':list(MODULES),'module_triangles':counts,'material_slots_per_module':1,'clips':{'idle':6,'keeper_idle':8,'smith_idle':7}})
    dest=ROOT/'game/assets/characters/townfolk_kit.glb'
    # The editable blend is textured; runtime binds the external shared atlas once.
    for node in list(MAT.node_tree.nodes):
        if node.type=='TEX_IMAGE': MAT.node_tree.nodes.remove(node)
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_yup=True,export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_apply=False,export_extras=True,export_vertex_color='ACTIVE')
    (ROOT/'game/assets/characters/townfolk_manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print('TOWNFOLK',json.dumps(info))

if __name__=='__main__':build()
