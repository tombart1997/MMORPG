"""Assisted hard-surface repairs of the reviewed multi-view equipment.

TRELLIS rounds thin edges and fills apertures. Build closed clean sections from
the jade front/edge/back references, with real bevels, wrapped grips and PBR.
Variants are authored derivatives, never described as independent inference.
"""
import bpy,json,math,importlib.util
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('clean',Path(__file__).with_name('rebuild_clean_sections.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def sphere(name,point,radii,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=point)
    o=bpy.context.object;o.name=name;o.scale=radii
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat)
    for f in o.data.polygons:f.use_smooth=True
    return o

def export(key,description,folder='weapons'):
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join()
    o=bpy.context.object;o.name='MV_'+key
    # Shared vertex-colour metal and leather surfaces retain physical response
    # while avoiding one draw call for every small fitting.
    from array import array
    colors=o.data.color_attributes.new(name='EquipmentColor',type='FLOAT_COLOR',domain='CORNER')
    metals=[]
    for f in o.data.polygons:
        old=o.data.materials[f.material_index]
        metallic=old.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value>.4
        for i in f.loop_indices:colors.data[i].color=old.diffuse_color
        metals.append(int(metallic))
    o.data.materials.clear()
    for name,metal,rough in [('Grip',0,.69),('Steel',.42,.49)]:
        mat=c.material('Equipment_'+name+'-vcol',(1,1,1),metal,rough)
        node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='EquipmentColor'
        mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        o.data.materials.append(mat)
    for f,m in zip(o.data.polygons,metals):f.material_index=m
    source=ROOT/'blender/multiview_rebuild/equipment'/f'{key}.blend';source.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source))
    dest=ROOT/'game/assets/generated'/folder/f'{key}.glb';dest.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_animations=False,export_skins=False,export_extras=True)
    triangles=sum(len(f.vertices)-2 for f in o.data.polygons)
    (ROOT/'docs/full_asset_rebuild'/f'{key}_equipment.json').write_text(json.dumps({
        'key':key,'output':str(dest),'triangles':triangles,'method':'assisted_clean_remodel',
        'reference':'concepts_docs/art/asset_turnarounds_v2/jade/turnaround.png',
        'native_diagnosis':'Rounded blade tip and fused guard; true edge thickness required.',
        'design':description,'old_geometry_reused':False},indent=2))
    print('EQUIPMENT',key,triangles,flush=True)
    return triangles

SPECS=[('jade',1.08,.040,0,False,'compact',(.022,.15,.085)),
 ('wayfarer',1.08,.035,0,False,'compact',(.085,.039,.018)),
 ('marchguard',1.08,.040,0,False,'swept',(.11,.058,.02)),
 ('briarsteel',1.14,.037,.035,False,'leaf',(.025,.08,.041)),
 ('cairnwarden',1.08,.040,0,False,'ring',(.048,.021,.018)),
 ('wakecleaver',1.23,.053,.025,True,'swept',(.05,.026,.025)),
 ('frontier',1.08,.034,.11,False,'ring',(.055,.045,.021)),
 ('relic',1.30,.042,0,True,'leaf',(.09,.032,.032)),
 ('ember',1.60,.048,.09,True,'ring',(.13,.032,.009)),
 ('glass',1.60,.038,0,True,'swept',(.023,.085,.094)),
 ('rift',1.60,.047,.018,True,'leaf',(.052,.028,.102))]
manifest={}
for name,length,width,curve,long,guard,color in SPECS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    steel=c.material('TemperedSteel',(.31,.37,.40),.86,.34)
    edge=c.material('HonedBevel',(.61,.68,.71),.92,.24)
    recess=c.material('FullerShadow',(.11,.16,.17),.78,.43)
    brass=c.material('AgedBrass',(.42,.255,.069),.83,.39)
    leather=c.material('WrappedGrip',color,0,.72)
    jade=c.material('JadeInlay',(.025,.185,.11),.1,.30)
    # Eight closed ring sections: sharpened side edges and recessed central
    # channel, tapered shoulder and a pointed final section with no bulge.
    cross=[(-1,0),(-.77,.75),(-.27,1),(-.16,.56),(.16,.56),(.27,1),(.77,.75),(1,0),(.77,-.75),(.27,-1),(.16,-.56),(-.16,-.56),(-.27,-1),(-.77,-.75)]
    rows=[(.07,width*.69,.006),(.145,width,.008),(.27,width*.99,.008),
          (.48*length,width*.92,.007),(.71*length,width*.78,.006),
          (.87*length,width*.56,.0045),(.96*length,width*.24,.0025),(length,.00008,.00015)]
    vertices=[];faces=[];n=len(cross)
    for y,w,h in rows:
        xshift=curve*(max(0,(y-.07)/(length-.07)))**1.7
        vertices.extend((xshift+x*w,y,z*h) for x,z in cross)
    for j in range(len(rows)-1):
        for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend([tuple(reversed(range(n))),tuple((len(rows)-1)*n+i for i in range(n))])
    blade=c.mesh('CleanBladeWithRecessedFuller',vertices,faces,steel,False)
    blade.data.materials.append(edge);blade.data.materials.append(recess)
    for f in blade.data.polygons:
        if f.index<(len(rows)-1)*n:f.material_index=1 if f.index%n in [0,6,7,13] else 2 if f.index%n in [2,3,4,9,10,11] else 0
    bevel=blade.modifiers.new('FineEdgeBevel','BEVEL');bevel.width=.00035;bevel.segments=2
    bpy.context.view_layer.objects.active=blade;bpy.ops.object.modifier_apply(modifier=bevel.name)
    end=-.34 if long else -.20
    c.tube('OvalGrip',[(0,end,0),(0,-.05,0),(0,.035,0)],[.019,.020,.022],leather,12)
    for k in range(14 if long else 9):
        y=end+.02+k*(.025-end)/(14 if long else 9)
        c.tube('CrossBinding',[(.021*math.cos(i*math.tau/16),y+i*.005/16,.021*math.sin(i*math.tau/16)) for i in range(17)],.0016,brass,4)
    c.tube('BladeCollar',[(0,.027,0),(0,.073,0)],[.027,.025],brass,12)
    if guard=='ring':
        c.tube('PiercedOvalGuard',[(.078*math.cos(i*math.tau/32),.055,.048*math.sin(i*math.tau/32)) for i in range(33)],.007,brass,6)
        for side in [-1,1]:c.tube('GuardSupport',[(side*.026,.055,0),(side*.076,.055,0)],.009,brass,6)
    else:
        reach={'compact':.093,'swept':.145,'leaf':.115}[guard]
        for side in [-1,1]:
            c.tube('GuardQuillon',[(side*.017,.055,0),(side*reach*.6,.055,0),(side*reach,.033 if guard=='swept' else .078,0)], [.014,.012,.008],brass,8)
            if guard=='leaf':sphere('LeafGuardTip',(side*reach,.075,0),(.018,.025,.009),jade)
    c.tube('PommelCollar',[(0,end-.017,0),(0,end+.008,0)],.023,brass,12)
    sphere('FacetedCounterweight',(0,end-.044,0),(.032,.030,.018),brass)
    sphere('PommelStone',(0,end-.043,.017),(.014,.015,.004),jade)
    if name=='jade':
        for side in [-1,1]:
            c.mesh('InsetJade', [(-.006,.16,side*.006),(.006,.16,side*.006),(.004,.62,side*.0044),(-.004,.62,side*.0044)],[(0,1,2,3)],jade,False)
    triangles=export(name,f'Sharp {length:.2f} m blade; {guard} guard, real fuller, separately wrapped grip and jade pommel.')
    manifest[name]={'blade_length':length,'two_handed':long,'tip':[curve,0,-length],'triangles':triangles}
(ROOT/'game/assets/weapons/manifest.json').write_text(json.dumps(manifest,indent=2))
