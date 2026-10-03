"""Ten original forged blades and a minted, bevelled gold cash coin.
Assets use Blender +Y forward, exported to Godot -Z. Grip origin stays zero.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'game/assets/weapons';SOURCE=ROOT/'blender/weapons'
DEST.mkdir(parents=True,exist_ok=True);SOURCE.mkdir(parents=True,exist_ok=True)
def mat(name,color,metal=0,rough=.4):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
def mesh(name,vs,fs,m,smooth=False):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(m)
    for p in d.polygons:p.use_smooth=smooth
    return o
def tube(name,path,radii,m,sides=16):
    vs=[];fs=[]
    for j,p in enumerate(path):
        center=Vector(p);t=(Vector(path[min(j+1,len(path)-1)])-Vector(path[max(0,j-1)])).normalized()
        x=Vector((1,0,0));x=(x-t*x.dot(t)).normalized() if abs(t.x)<.9 else Vector((0,0,1));y=t.cross(x);r=radii[j] if isinstance(radii,list) else radii
        for i in range(sides):a=i*math.tau/sides;vs.append(center+(x*math.cos(a)+y*math.sin(a))*r)
    for j in range(len(path)-1):
        for i in range(sides):a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
    fs.extend([tuple(reversed(range(sides))),tuple((len(path)-1)*sides+i for i in range(sides))]);return mesh(name,vs,fs,m,True)
def ell(name,c,scale,m,segments=24,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=c);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    return o
SPECS=[
('wayfarer',1.08,.034,0,False,'plain',(.07,.032,.014)),
('marchguard',1.08,.039,0,False,'quillon',(.105,.053,.019)),
('briarsteel',1.14,.035,.035,False,'leaf',(.038,.07,.042)),
('cairnwarden',1.08,.038,0,False,'disc',(.045,.017,.014)),
('wakecleaver',1.23,.047,.025,True,'quillon',(.045,.018,.022)),
('frontier',1.08,.033,.11,False,'disc',(.04,.035,.023)),
('relic',1.30,.040,0,True,'leaf',(.08,.022,.028)),
('ember',1.60,.047,.09,True,'disc',(.12,.035,.015)),
('glass',1.60,.037,0,True,'quillon',(.04,.072,.075)),
('rift',1.60,.045,.018,True,'leaf',(.045,.030,.070))]
manifest={}
for name,length,width,curve,long,guard,wrapcolor in SPECS:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    steel=mat('Forged_'+name+'_Steel',(.42,.47,.49),.83,.28)
    edge=mat('Forged_'+name+'_HonedEdge',(.65,.69,.7),.9,.20)
    fuller=mat('Forged_'+name+'_RecessedFuller',(.19,.23,.25),.8,.35)
    brass=mat('Forged_'+name+'_Fittings',(.42,.265,.065),.80,.3)
    dark=mat('Forged_'+name+'_Iron',(.075,.085,.085),.75,.34)
    leather=mat('Forged_'+name+'_Grip',wrapcolor,0,.75)
    jade=mat('Forged_'+name+'_Inlay',(.034,.18,.12),.15,.31)
    # Broad central planes, recessed fuller, bevelled shoulders, fine cutting edge.
    cross=[(-1,0),(-.82,.7),(-.24,1),(-.11,.72),(.11,.72),(.24,1),(.82,.7),(1,0),(.82,-.7),(.24,-1),(.11,-.72),(-.11,-.72),(-.24,-1),(-.82,-.7)]
    rows=[(.095,width*.62,.006),(.16,width,.008),(.30,width,.008),(.64*length,width*.86,.007),(.86*length,width*.65,.005),(length,.0004,.0004)]
    vs=[];fs=[]
    for y,w,h in rows:
        shift=curve*(max(0,(y-.2)/(length-.2)))**1.8
        for x,z in cross:vs.append((shift+x*w,y,z*h))
    n=len(cross)
    for j in range(len(rows)-1):
        for k in range(n):a=j*n+k;b=j*n+(k+1)%n;fs.append((a,b,b+n,a+n))
    fs.extend([tuple(reversed(range(n))),tuple((len(rows)-1)*n+i for i in range(n))])
    blade=mesh('ContinuousForgedBlade',vs,fs,steel);blade.data.materials.append(edge);blade.data.materials.append(fuller)
    for j,p in enumerate(blade.data.polygons):
        if j<(len(rows)-1)*n:
            p.material_index=1 if j%n in [0,6,7,13] else 2 if j%n in [2,3,4,9,10,11] else 0
    # Closed, fitted leather grip with diagonally stitched wraps.
    end=-.35 if long else -.205
    tube('LeatherGrip',[(0,end,0),(0,.045,0)],[.018,.022],leather,24)
    for k in range(15 if long else 10):
        y=end+.018+k*((.045-end-.025)/(15 if long else 10))
        tube('GripBinding',[(.022*math.cos(i*math.tau/24),y+.008*i/24,.022*math.sin(i*math.tau/24)) for i in range(25)],.0015,dark,6)
    tube('Ferrule',[(0,.040,0),(0,.071,0)],[.027,.027],brass,24)
    if guard=='disc':
        # A forged oval tsuba-like guard, with thickness, open center and beveled rim.
        rowsg=[(.06,.075),(.065,.086),(.080,.086),(.085,.075)]
        gv=[];gf=[]
        for y,r in rowsg:
            for i in range(48):a=i*math.tau/48;gv.append((r*math.cos(a),y,.70*r*math.sin(a)))
        for j in range(3):
            for k in range(48):a=j*48+k;b=j*48+(k+1)%48;gf.append((a,b,b+48,a+48))
        gf.extend([tuple(reversed(range(48))),tuple(3*48+i for i in range(48))]);mesh('OvalForgedGuard',gv,gf,brass,True)
    else:
        for s in [-1,1]:
            reach=.14 if guard=='quillon' else .105 if guard=='leaf' else .083
            path=[(s*(.020+reach*t/16),.062-(.022 if guard=='quillon' else -.02)*math.sin(t/16*math.pi/2),.006*math.sin(t/16*math.pi)) for t in range(17)]
            tube('ForgedQuillon',path,[.017*(1-t/20)+.002 for t in range(17)],brass if guard!='plain' else dark,16)
    tube('PommelNeck',[(0,end-.026,0),(0,end+.005,0)],[.020,.020],brass,24)
    ell('WeightedPommel',(0,end-.049,0),(.036,.034,.017),brass)
    if name in ['cairnwarden','relic','wakecleaver','rift','glass']:
        ell('PommelInlay',(0,end-.050,.017),(.013,.014,.0035),jade)
        for s in [-1,1]:tube('GuardEngraving',[(s*.027,.09,.009),(s*.039,.13,.009),(s*.021,.17,.009)],.0013,brass,6)
    bpy.context.view_layer.objects.active=blade
    bevel=blade.modifiers.new('ForgedEdgeBevel','BEVEL');bevel.width=.00065;bevel.segments=2;bpy.ops.object.modifier_apply(modifier=bevel.name)
    for marker,point in [('Grip',(0,0,0)),('Tip',(curve,length,0))]+([('OffhandGrip',(0,-.18,0))] if long else []):
        o=bpy.data.objects.new(marker,None);bpy.context.collection.objects.link(o);o.location=point
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(name+'.blend')))
    # Join by material; keep empty markers separately.
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=blade;bpy.ops.object.join();blade.name='Forged_'+name
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(DEST/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=False)
    manifest[name]={'blade_length':length,'two_handed':long,'tip':[curve,0,-length],'triangles':sum(len(p.vertices)-2 for p in blade.data.polygons)}

# A thick minted cash coin with an actual square hole, rim beads and raised seals.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
gold=mat('MintedGold',(.72,.44,.065),.94,.27);aged=mat('GoldRecess',(.35,.19,.025),.85,.39)
vs=[];fs=[];n=64
rows=[(.058,-.004),(.063,-.0025),(.063,.0025),(.058,.004),(.014,.004),(.014,-.004)]
for r,z in rows:
    for i in range(n):
        a=i*math.tau/n
        if r==.014:r2=.012/max(abs(math.cos(a)),abs(math.sin(a)))
        else:r2=r
        vs.append((r2*math.cos(a),r2*math.sin(a),z))
for j in range(len(rows)):
    for i in range(n):a=j*n+i;b=j*n+(i+1)%n;c=((j+1)%len(rows))*n+(i+1)%n;d=((j+1)%len(rows))*n+i;fs.append((a,b,c,d))
coin=mesh('GoldCashCoin',vs,fs,gold,True)
for polygon in coin.data.polygons:
    # Minted faces are flat; interpolated edge normals create triangular fans.
    if polygon.index//n in [3,5]: polygon.use_smooth=False
for z,s in [(.0043,1),(-.0043,-1)]:
    tube('MintedRim',[(.054*math.cos(i*math.tau/32),.054*math.sin(i*math.tau/32),z) for i in range(33)],.0013,gold,6)
    for i in range(24):a=i*math.tau/24;ell('RimBead',(.059*math.cos(a),.059*math.sin(a),z),(.0015,.0015,.0007),gold,8,4)
    for i in range(4):
        a=i*math.pi/2;x=.032*math.cos(a);y=.032*math.sin(a)
        tube('SealStroke',[(x-.009,y-.009,z),(x+.008,y-.009,z),(x+.008,y+.009,z),(x-.009,y+.009,z)],.0018,gold,8)
        tube('SealBar',[(x-.011,y,z),(x+.011,y,z)],.0013,aged,8)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'gold_coin.blend'))
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=coin;bpy.ops.object.join();coin.name='MintedGoldCoin'
bpy.ops.export_scene.gltf(filepath=str(DEST/'gold_coin.glb'),export_format='GLB',use_selection=True,export_animations=False)
manifest['gold_coin']={'triangles':sum(len(p.vertices)-2 for p in coin.data.polygons)}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2));print('SWORD_SUITE_COMPLETE',json.dumps(manifest),flush=True)
