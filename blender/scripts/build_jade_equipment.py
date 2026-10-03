"""Jian-inspired equipment, preserving the existing grip and 1.08 m tip contract."""
import bpy, importlib.util, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build_characters.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base.reset()
steel=base.material('JadeBlade',(.43,.54,.55),.78,.28)
gold=base.material('JadeSwordGold',(.48,.31,.09),.72,.34)
jade=base.material('JadeSwordStone',(.055,.32,.23),.2,.28)
silk=base.material('JadeSwordWrap',(.22,.022,.031),0,.75)
dark=base.material('JadeSwordFuller',(.045,.079,.084),.64,.39)

def blade(name,rings,mat):
    vs=[];fs=[]
    for z,w,h in rings:
        vs.extend([(x,y,z) for x,y in [(-w,0),(-w*.76,h*.65),(0,h),(w*.76,h*.65),(w,0),(w*.76,-h*.65),(0,-h),(-w*.76,-h*.65)]])
    for j in range(len(rings)-1):
        for k in range(8):
            a=j*8+k;b=j*8+(k+1)%8;fs.append((a,b,b+8,a+8))
    fs.extend([tuple(reversed(range(8))),tuple((len(rings)-1)*8+i for i in range(8))])
    o=base.mesh_object(name,vs,fs,mat)
    for p in o.data.polygons:p.use_smooth=False

blade('JianBlade',[(.065,.023,.005),(.13,.044,.008),(.68,.035,.007),(.93,.027,.005),(1.08,.0005,.0005)],steel)
blade('JianFuller',[(.15,.005,.0085),(.70,.004,.0075),(.89,.0005,.0057)],dark)
base.tube('SilkGrip',[(0,0,-.12),(0,0,.065)],[.017,.020],silk,sides=24)
for k in range(10):
    z=-.108+k*.017
    points=[(.0186*math.sin(i*math.tau/24),.0186*math.cos(i*math.tau/24),z+.006*i/24) for i in range(25)]
    base.tube('GripBraid',points,[.0015]*25,gold,sides=6)
for s in [-1,1]:
    pts=[];r=[]
    for i in range(25):
        t=i/24
        pts.append((s*(.015+.17*t),0,.073+.052*math.sin(t*math.pi*.82)))
        r.append(.018*(1-t)+.003)
    base.tube('CloudGuard',pts,r,gold,sides=16)
base.ellipsoid('GuardJade',(0,-.013,.079),(.023,.009,.028),jade,segments=32,rings=16)
base.ellipsoid('JadePommel',(0,0,-.145),(.028,.019,.022),gold,segments=32,rings=16)
base.ellipsoid('PommelStone',(0,-.017,-.145),(.014,.006,.015),jade,segments=24,rings=12)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/characters/jade_sword.blend'))
parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=str(ROOT/'game/assets/characters/jade_sword.glb'),export_format='GLB',export_yup=True,export_animations=False)

# Ironback mantle: fitted, overlapping carved leaves instead of floating cone spikes.
base.reset()
jade=base.material('IronbackJade',(.065,.22,.15),.2,.42)
gold=base.material('IronbackGold',(.43,.29,.11),.55,.5)
for s in [-1,1]:
    for row in range(4):
        cx=s*(.11+row*.037);z=.20-row*.065;cy=-.19
        vs=[(cx-s*.08,cy,z),(cx+s*.10,cy,z+.035),(cx+s*.17,cy-.05,z-.045),(cx+s*.065,cy-.085,z-.11),(cx,cy-.07,z-.065),(cx+s*.04,cy-.115,z-.012)]
        o=base.mesh_object('IronbackLeaf',vs,[(k,(k+1)%5,5) for k in range(5)],jade)
        for p in o.data.polygons:p.use_smooth=False
        base.tube('MantlePiping',[vs[1],vs[2],vs[3]],[.004,.004,.002],gold,sides=8)
    base.tube('MantleHorn',[(s*.17,-.19,.23),(s*.27,-.22,.34),(s*.34,-.16,.42)],[.035,.022,.001],gold,sides=16)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/characters/jade_ironback_mantle.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'game/assets/characters/jade_ironback_mantle.glb'),export_format='GLB',export_yup=True,export_animations=False)
