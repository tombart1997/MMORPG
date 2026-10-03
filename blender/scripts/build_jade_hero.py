"""Modern Chinese martial-fantasy wardrobe on the existing muscular, animated hero.

Run: blender -b blender/characters/warden_high.blend -P blender/scripts/build_jade_hero.py
Keeps the 18-bone contract and all one/two-hand choreography. Safe to rebuild.
"""
import bpy, math, importlib.util, sys
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wh', Path(__file__).with_name('build_warden_high.py'))
wh = importlib.util.module_from_spec(spec); spec.loader.exec_module(wh)
wh.RIG = bpy.data.objects['WardenRig']
wh.PARTS = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.find_armature() == wh.RIG]
wh.MATS = {m.name.removeprefix('Warden_'): m for m in bpy.data.materials if m.name.startswith('Warden_')}
rig = wh.RIG
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.scene.frame_set(0)

def remove(prefixes):
    for obj in list(wh.PARTS):
        if obj.name.startswith(prefixes):
            wh.PARTS.remove(obj); bpy.data.objects.remove(obj, do_unlink=True)

remove(('Jade_', 'FlutedBreastRib', 'Gorget', 'CollarRolledEdge', 'SunSeal',
        'SplitTabard', 'HandStitch', 'RearOxblood', 'RearCloth', 'BackHarness',
        'HarnessRivet', 'SpinePlateRidge', 'CroppedHair'))

def mat(key, color, metallic, rough):
    existing = bpy.data.materials.get('Warden_'+key)
    if existing:
        wh.MATS[key] = existing
        bsdf = existing.node_tree.nodes.get('Principled BSDF')
        for node in list(existing.node_tree.nodes):
            if node.type == 'TEX_IMAGE': existing.node_tree.nodes.remove(node)
        existing.diffuse_color = (*color,1)
        bsdf.inputs['Base Color'].default_value = (*color,1)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = rough
        return existing
    return wh.material(key,color,metallic,rough)

ink = mat('Undercloth',(.024,.036,.040),0,.83)
steel = mat('Steel',(.085,.16,.17),.48,.36)
dark = mat('DarkSteel',(.033,.074,.084),.45,.42)
gold = mat('Brass',(.55,.35,.115),.7,.32)
ivory = mat('JadeIvory',(.68,.62,.46),0,.72)
silk = mat('Cloth',(.052,.24,.215),.08,.48)
red = mat('JadeCinnabar',(.30,.022,.032),0,.64)
jade = mat('JadeStone',(.10,.40,.30),.18,.26)
hair = mat('Hair',(.009,.014,.018),0,.84)
hairline = mat('HairHighlight',(.014,.022,.027),0,.82)

def shell(name, vs, fs, material, bone, thickness=.004):
    o=wh.mesh('Jade_'+name,vs,fs,material,bone)
    sol=o.modifiers.new('TailoredThickness','SOLIDIFY'); sol.thickness=thickness
    bevel=o.modifiers.new('SoftEdge','BEVEL'); bevel.width=.0015; bevel.segments=2
    return o

def front_y(x,z,back=False):
    width=.215+.115*min(1,max(0,(z-1.12)/.26))
    depth=.161+.025*math.sin((z-1.12)/.34*math.pi)
    return (-1 if back else 1)*(depth*math.sqrt(max(.20,1-(x/width)**2))+.016)

# Layered lamellae follow the athletic torso, with broad quiet surfaces between details.
for back in [False,True]:
    for row in range(5):
        z=1.15+row*.052
        width=.215+.105*(row/4)
        for col in range(12):
            x=(col-5.5)*width/6; half=width/12*.94
            outline=[(-half,.027),(half,.027),(half,-.021),(half*.65,-.035),(-half*.65,-.035),(-half,-.021)]
            vs=[(x+dx,front_y(x+dx,z+dz,back),z+dz) for dx,dz in outline]
            shell('Lamella',vs,[(0,1,2,3,4,5)],steel if (row+col)%4 else dark,'Chest',.005)
            wh.line('Jade_LamellaHem',[vs[2],vs[3],vs[4],vs[5]],.0016,gold,'Chest')
            if col%2==0:
                wh.ell('Jade_Lacing',(x,front_y(x,z,back)+(-.006 if back else .006),z+.015),(.003,.003,.006),gold,'Chest',12,8)

# Crossed collar / silk wrap over the pectoral armor, continued around the back neck.
for sign in [-1,1]:
    vs=[]
    for j in range(21):
        t=j/20; x=sign*(.19-(.25 if sign==-1 else .21)*t); z=1.485-(.31 if sign==-1 else .205)*t
        for dx in [-.032,.032]:
            xx=x+dx;vs.append((xx,front_y(xx,z)+.021,z))
    shell('CrossCollar',vs,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(20)],ivory,'Chest',.006)
    wh.line('Jade_CollarPiping',[vs[j*2] for j in range(21)],.003,gold,'Chest')
wh.loft('Jade_StandingCollar',[(1.468,.097,.081,0),(1.508,.082,.074,0)],ivory,'Neck',48)
wh.oval_trim('Jade_CollarBand',1.510,.083,.075,0,gold,'Neck',.002)

# Split silk robe: four curved fall panels, each weighted toward its moving thigh.
def cloth_weights(obj,side):
    for group in list(obj.vertex_groups):obj.vertex_groups.remove(group)
    hip=obj.vertex_groups.new(name='Hips');thigh=obj.vertex_groups.new(name='Thigh.'+side)
    for v in obj.data.vertices:
        t=min(1,max(0,(.997-v.co.z)/.53))*.72
        hip.add([v.index],1-t,'REPLACE');thigh.add([v.index],t,'REPLACE')

for back in [False,True]:
    for sign,side in [(1,'R'),(-1,'L')]:
        vs=[];ws=[]
        for j in range(25):
            t=j/24
            for i in range(13):
                u=i/12
                x=sign*(.032+u*(.179+.045*t)+.025*t)
                z=.997-.53*t+.032*math.sin(u*math.pi)*t
                waist=.153*math.sqrt(max(.2,1-(x/.27)**2))+.009
                y=(-1 if back else 1)*(waist*(1-t)+(.195+.012*math.cos(u*math.pi*4))*t)
                vs.append((x,y,z));ws.append({'Hips':1-.72*t,'Thigh.'+side:.72*t})
        o=wh.mesh('Jade_SilkFall',vs,[(j*13+i,j*13+i+1,(j+1)*13+i+1,(j+1)*13+i) for j in range(24) for i in range(12)],silk,'Hips',ws)
        sol=o.modifiers.new('SilkThickness','SOLIDIFY');sol.thickness=.004
        edge=wh.line('Jade_RobeBorder',[vs[j*13] for j in range(25)],.0035,gold,'Thigh.'+side)
        cloth_weights(edge,side)
        # Large embroidery motif at the hem, visible at normal gameplay distance.
        for k in range(2):
            points=[]
            for j in range(31):
                a=j/30*math.pi*1.65
                x=sign*(.115+.038*math.cos(a)+k*.049);z=.59+.030*math.sin(a)+k*.027;t=(.997-z)/.53
                waist=.153*math.sqrt(max(.2,1-(x/.27)**2))+.009
                points.append((x,(-1 if back else 1)*(waist*(1-t)+.201*t),z))
            embroidery=wh.line('Jade_CloudEmbroidery',points,.0028,gold,'Thigh.'+side)
            cloth_weights(embroidery,side)

wh.loft('Jade_SilkSash',[(.978,.218,.148,0),(1.034,.229,.155,0)],red,'Hips',64)
# Jade bi-style buckle: an open ring, not a painted green dot.
wh.line('Jade_BeltRing',[(.041*math.sin(i*math.tau/64),.163,1.002+.041*math.cos(i*math.tau/64)) for i in range(65)],.009,jade,'Hips')
for s in [-1,1]:
    wh.line('Jade_SashCord',[(s*.055,.162,1.01),(s*.14,.183,.98),(s*.245,.12,.92),(s*.27,.10,.83)],.008,red,'Hips')
    wh.ell('Jade_SashPendant',(s*.27,.10,.79),(.020,.014,.036),jade,'Hips',24,16)
    for k in range(7):
        wh.line('Jade_Tassel',[(s*.27+(k-3)*.004,.104,.77),(s*.28+(k-3)*.005,.11,.66)],.0028,red,'Hips')

# Stylized cloud scrolls accent the shoulder silhouette without widening the sword grip.
for s,side in [(1,'R'),(-1,'L')]:
    for k in range(2):
        pts=[]
        for j in range(33):
            t=j/32; a=t*math.pi*1.6
            pts.append((s*(.305+.055*k+.040*math.cos(a)),.133+.013*math.sin(a),1.446-.035*k+.022*math.sin(a)))
        wh.line('Jade_ShoulderCloud',pts,.0035,gold,'UpperArm.'+side)
    wh.ell('Jade_ShoulderGem',(s*.347,.135,1.44),(.028,.009,.017),jade,'UpperArm.'+side,24,16)

# Anatomical fitted scalp, swept into a high tied knot and a narrow back fall.
head=bpy.data.objects['AnatomicalHead'].data
chosen=[p for p in head.polygons if all(head.vertices[i].co.z>(1.739 if head.vertices[i].co.y>.014 else 1.696 if abs(head.vertices[i].co.x)>.08 else 1.656) for i in p.vertices)]
used=sorted({i for p in chosen for i in p.vertices});indices={i:j for j,i in enumerate(used)}
vs=[head.vertices[i].co+head.vertices[i].normal*.0045 for i in used]
fs=[[indices[i] for i in p.vertices] for p in chosen]
wh.mesh('Jade_SweptHair',vs,fs,hair,'Head')
from mathutils.kdtree import KDTree
kd=KDTree(len(vs))
for i,v in enumerate(vs):kd.insert(v,i)
kd.balance()
wh.ell('Jade_Topknot',(0,-.055,1.851),(.045,.048,.047),hair,'Head',40,24)
wh.oval_trim('Jade_KnotTie',1.846,.047,.048,-.055,gold,'Head',.003)
wh.line('Jade_Hairpin',[(-.070,-.055,1.850),(.073,-.055,1.850)],.0045,gold,'Head')
wh.ell('Jade_HairpinStone',(.074,-.055,1.850),(.009,.01,.012),jade,'Head',24,12)
for k in range(28):
    a=k/28*math.tau
    pts=[]
    for j in range(19):
        t=j/18; aa=a+.25*t;r=math.cos(t*math.pi/2)
        edge=1.69+.054*max(0,math.cos(a))-.045*max(0,-math.cos(a))
        target=Vector((.104*r*math.sin(aa),-.027+.104*r*math.cos(aa),edge+(1.827-edge)*math.sin(t*math.pi/2)))
        nearest,index,distance=kd.find(target);pts.append(nearest+head.vertices[used[index]].normal*.0015)
    wh.line('Jade_SweptStrand',pts,.0012,hairline,'Head')
for k in range(8):
    a=k/8*math.tau
    wh.line('Jade_KnotStrand',[(.046*math.sin(a)*math.cos(j/20*math.pi),-.055+.049*math.cos(a)*math.cos(j/20*math.pi),1.851+.047*math.sin(j/20*math.pi)) for j in range(21)],.0014,hairline,'Head')
wh.tube('Jade_Ponytail',[(0,-.090,1.831),(.012,-.135,1.76),(.014,-.151,1.64),(-.017,-.151,1.48),(-.023,-.16,1.41)],[.025,.028,.025,.017,.002],hair,'Head',24)

# The same ornament language carries onto the back, important for the play camera.
for s in [-1,1]:
    wh.line('Jade_BackCloud',[(s*(.10+.05*math.cos(j/40*math.pi*2)),front_y(s*.14,1.32,True)-.012,1.32+.052*math.sin(j/40*math.pi*2)) for j in range(41)],.003,gold,'Chest')

import bmesh
for obj in wh.PARTS:
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(obj.data);bm.free()
wh.export()
# Reuse the studio framing, without regenerating or modifying any attack clips.
spec=importlib.util.spec_from_file_location('hero',Path(__file__).with_name('build_warden_hero.py'))
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
hero.studio_render('jade_pass2' if '--second' in sys.argv else 'jade_pass1')
