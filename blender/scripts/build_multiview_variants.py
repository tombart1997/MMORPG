"""Publish metric variants of reviewed new bases; never import legacy surfaces.

One reconstruction per shared body plan, with authored species/resident
variations. The manifest distinguishes this from independent neural inference.
"""
import bpy,bmesh,json,math,sys,re,importlib.util,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
for module,file in [('bridge','forge_bind_export.py'),('clean','rebuild_clean_sections.py')]:
    spec=importlib.util.spec_from_file_location(module,Path(__file__).with_name(file));obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);globals()[module]=obj
OUT=ROOT/'game/assets/generated';DOC=ROOT/'docs/full_asset_rebuild'
only=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
records=json.loads((DOC/'variant_lineage.json').read_text()) if (DOC/'variant_lineage.json').exists() else []

def write(key,group,base,method):
    source=ROOT/'blender/multiview_rebuild/variants'/group/f'{key}.blend';source.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source))
    dest=OUT/group/f'{key}.glb';dest.parent.mkdir(parents=True,exist_ok=True)
    rig=next((o for o in bpy.context.scene.objects if o.type=='ARMATURE'),None)
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_yup=True,
        export_skins=rig is not None,export_animations=rig is not None,
        export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False,export_extras=True)
    record={'key':key,'group':group,'base':base,'path':str(dest.relative_to(ROOT)).replace('\\','/'),
        'method':method,'independent_neural_generation':False,'old_geometry_reused':False,
        'triangles':sum(len(f.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for f in o.data.polygons)}
    records.append(record);(DOC/'variant_lineage.json').write_text(json.dumps(list({(r['group'],r['key']):r for r in records}.values()),indent=2))
    print('VARIANT',group,key,record['triangles'],flush=True)

def tint_materials(parts,color,strength=.46):
    # glTF exports constant factors faithfully, unlike arbitrary multiply nodes.
    tint=Vector(color)
    for o in parts:
        for mat in o.data.materials:
            if not mat or not mat.use_nodes:continue
            shader=mat.node_tree.nodes.get('Principled BSDF')
            if shader:
                original_factor=shader.inputs['Base Color'].default_value[:]
                shader.inputs['Base Color'].default_value=(*[original_factor[i]*((1-strength)+strength*c) for i,c in enumerate(tint)],original_factor[3])
                mat.diffuse_color=shader.inputs['Base Color'].default_value
                if shader.inputs['Base Color'].links:
                    node=shader.inputs['Base Color'].links[0].from_node
                    if node.type=='TEX_IMAGE':
                        original=node.image
                        pixels=np.empty(len(original.pixels),dtype=np.float32);original.pixels.foreach_get(pixels)
                        # Fresh generated storage prevents a copied packed FILE
                        # image from exporting its original, untinted PNG bytes.
                        atlas=bpy.data.images.new(o.name+'_Tint',width=original.size[0],height=original.size[1],alpha=True)
                        atlas.colorspace_settings.name=original.colorspace_settings.name;node.image=atlas
                        rgba=pixels.reshape(-1,4);rgba[:,:3]*=np.array(shader.inputs['Base Color'].default_value[:3],dtype=np.float32)
                        atlas.pixels.foreach_set(pixels);atlas.pack();shader.inputs['Base Color'].default_value=(1,1,1,1)

def skinned_variant(key,base,group,family,tier=1,color=(1,1,1)):
    source=ROOT/'blender/multiview_rebuild/rigged'/f'{base}.blend'
    if not source.exists():return
    bpy.ops.wm.open_mainfile(filepath=str(source));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    rig.data.pose_position='REST'
    parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in parts:
        # Body-width changes remain deliberately small so bind anchors and
        # existing actor scale continue to own the physical gameplay size.
        width=1+min(tier,4)*.025 if family in ['boar','stonekin','mossling'] else 1
        for v in o.data.vertices:
            v.co.x*=width
            if family=='wolf' and key in ['bloodfang','ember_hound','moonfang'] and v.co.z>.9 and v.co.y<.45:v.co.z+=.04*(tier-1)
        o.name='MV_'+key
    if family!='wolf':tint_materials(parts,color,.57 if family not in ['humanoid','bandit'] else .23)
    if family=='wolf' and key!='meadow_wolf':
        # Derive coat hues from the actual concept palette while retaining
        # the reconstructed fur's local variation, dark muzzle and paws.
        # Multiplication alone cannot translate a brown coat into snow white.
        for o in parts:
            for mat in o.data.materials:
                p=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
                if not p or not p.inputs['Base Color'].links:continue
                node=p.inputs['Base Color'].links[0].from_node
                if node.type!='TEX_IMAGE':continue
                atlas=node.image.copy();atlas.name=key+'_Coat';node.image=atlas
                pixels=np.empty(len(atlas.pixels),dtype=np.float32);atlas.pixels.foreach_get(pixels);pixels=pixels.reshape(-1,4)
                luminance=pixels[:,:3]@np.array([.2126,.7152,.0722],dtype=np.float32)
                fur=np.clip((luminance-.023)/.13,0,1)
                detail=np.clip(luminance/.30,.10,1)
                target=np.array(color,dtype=np.float32)*.84
                coat=pixels[:,:3]*.22+target[None,:]*(.30+.65*np.sqrt(detail[:,None]))*.78
                pixels[:,:3]=pixels[:,:3]*(1-fur[:,None])+coat*fur[:,None]
                atlas.pixels.foreach_set(pixels.ravel());atlas.pack()
                p.inputs['Base Color'].default_value=(1,1,1,1)
    additions=[]
    detail_guide=bridge.weights_guide(parts,rig)
    def top_at(x,y):
        close=[v.co.z for part in parts for v in part.data.vertices if abs(v.co.x-x)<.10 and abs(v.co.y-y)<.10]
        return max(close) if close else 1.05
    if family=='wolf' and key=='thicket_wolf':
        foliage=clean.material('ThicketLeaves',(.12,.16,.034))
        for i in range(14):
            y=-.65+i*.08;x=.09*math.sin(i*2.4);z=top_at(x,y)-.008
            o=clean.mesh('ThicketLeaf',[(x,y,z),(x+.06,y+.08,z+.045),(x,y+.17,z+.02),(x-.035,y+.08,z+.045)],[(0,1,2,3)],foliage)
            additions.append((o,'Chest' if y>0 else 'Hips'))
    if family=='wolf' and key=='bloodfang':
        bone=clean.material('BloodfangIvory',(.53,.47,.34))
        for side in [-1,1]:additions.append((clean.tube('LongCanine',[(side*.09,.85,.94),(side*.075,.94,.72)],[.026,.001],bone,8),'Head'))
    if family=='boar' and key in ['blacktusk','obsidian_boar']:
        tusk=clean.material('ObsidianTusk',(.026,.022,.023))
        for side in [-1,1]:additions.append((clean.tube('DarkCurvedTusk',[(side*.22,.83,.63),(side*.29,1.06,.80),(side*.24,1.1,1.03)],[.051,.030,.001],tusk,10),'Head'))
    if family=='boar' and key=='ironhide_boar':
        ivory=clean.material('IronhideBristles',(.34,.34,.27))
        for i in range(9):
            y=-.6+i*.115;z=top_at(0,y)-.015
            additions.append((clean.tube('DorsalBristle',[(0,y,z),(0,y-.025,z+.19)],[.026,.001],ivory,5),'Hips' if y<0 else 'Chest'))
    # Native bark and stone armor already express the tier silhouette. Extra
    # rounded rear plates were rejected after opening the four-angle renders.
    if family=='wisp':
        glow=clean.material(key+'_SpiritGlow',color,rough=.6)
        p=glow.node_tree.nodes['Principled BSDF'];p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=2.0
        for side in [-1,1]:
            o=clean.ellipsoid('SpiritEye',(side*.070,.16,1.30),(.029,.021,.030),glow,10,5)
            additions.append((o,'Head'))
    for o,bone in additions:
        o.parent=rig
        # Preserve the reconstructed surface's local blend, rather than
        # assigning an entire decoration to a nearby old-template bone.
        location=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
        nearest=detail_guide[0].find(location);weights=detail_guide[1][nearest[1]][1]
        for name,weight in weights.items():o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))),weight,'REPLACE')
        mod=o.modifiers.new('NewVariantSkin','ARMATURE');mod.object=rig
        parts.append(o)
    if additions:
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
    rig.data.pose_position='POSE';bpy.context.scene.frame_set(0)
    write(key,group,base,'New shared body reconstruction; fitted color/body-width/detail variant with retained skeleton/actions.')

STATIC={
 'tree0':('pine',5.2,0,1,1),'tree1':('pine',5.7,24,.90,1),'tree2':('pine',5.0,-19,1.08,.96),
 'tree_bent':('pine',5.6,14,1.05,1),'tree_fork':('pine',6.2,-32,.94,1),'tree_wide':('pine',5.8,75,1.14,1),
 'rock0':('rock',1.4,0,1,1),'rock1':('rock',1.1,62,.90,1.08),'rock2':('rock',1.75,-46,1.08,.89),
 'rock_0':('rock',1.5,23,1,1),'rock_1':('rock',1.2,-35,1.05,.94),'rock_2':('rock',1.8,74,.88,1.04),
 'cliff':('rock',2.8,-25,1.15,.95),'cliff1':('rock',2.4,0,1.7,.45),
 'shrub':('shrub',.78,0,1,1),'shrub_briar':('shrub',.68,26,1.06,.9),'shrub_laurel':('shrub',.83,-40,.94,1.1),
 'fern':('fern',.66,0,1,1),'grass':('grass',.43,0,1,1),'sedge':('grass',.52,35,.88,1),'leaf_litter':('leaf_litter',.045,0,1,1),
 'house':('house',4.2,0,1,1),'watchtower':('watchtower',6.0,90,1,1),
 'dead_tree':('dead_tree',4.8,0,1,1),'log':('fallen_log',.70,0,1,1),'fallen_wood':('fallen_log',.65,55,1,1),
 'shrine':('shrine',2.2,0,1,1),'tent':('tent',2.1,0,1,1),'ruin_arch':('ruin_arch',4.0,0,1,1),
 'ruin':('ruin_arch',1.8,68,1,1),'crate':('crate',.85,0,1,1),'bridge':('bridge',1.8,0,1,1),
 'flowers':('flowers',.42,0,1,1),'mushroom':('mushroom',.40,0,1,1),'eggs':('eggs',.35,0,1,1),
 'bones':('bones',.23,0,1,1),'web':('web',2.15,0,1,1),'banner':('banner',2.15,0,1,1),
 'fire':('fire',.18,0,1,1),'pouch':('pouch',.17,0,1,1),
 'market_stall':('market_stall',2.68,0,1,1),'well':('well',2.35,0,1,1),
 'fence':('fence',1.30,0,1,1),'gate':('gate',3.42,0,1,1),'anvil':('anvil',1.03,0,1,1)}

def static_variant(key,spec):
    base,height,yaw,xscale,yscale=spec;source=ROOT/'blender/multiview_rebuild/prepared'/f'{base}.blend'
    if not source.exists():return
    bpy.ops.wm.open_mainfile(filepath=str(source));parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in parts:
        o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
        o.data.transform(Matrix.Rotation(math.radians(yaw),4,'Z'))
        if base in ['shrine','tent']:
            lo,hi=bridge.bounds([o]);height_source=hi.z-lo.z
            bm=bmesh.new();bm.from_mesh(o.data)
            floor=[f for f in bm.faces if max(v.co.z for v in f.verts)<lo.z+height_source*.035 and abs(f.normal.z)>.80]
            bmesh.ops.delete(bm,geom=floor,context='FACES')
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
            bm.to_mesh(o.data);bm.free()
        if base=='crate':
            lo,hi=bridge.bounds([o]);h=hi.z-lo.z
            body=[v.co for v in o.data.vertices if lo.z+h*.15<v.co.z<hi.z-h*.10]
            xlo=min(v.x for v in body);xhi=max(v.x for v in body);ylo=min(v.y for v in body);yhi=max(v.y for v in body)
            bm=bmesh.new();bm.from_mesh(o.data)
            discard=[v for v in bm.verts if v.co.z<lo.z+h*.06 and (v.co.x<xlo or v.co.x>xhi or v.co.y<ylo or v.co.y>yhi)]
            bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(o.data);bm.free()
    lo,hi=bridge.bounds(parts);factor=height/(hi.z-lo.z);center=(lo+hi)*.5
    for o in parts:
        for v in o.data.vertices:v.co=Vector(((v.co.x-center.x)*factor*xscale,(v.co.y-center.y)*factor*yscale,(v.co.z-lo.z)*factor))
        o.name='MV_'+key
        if key=='tree_bent':
            for v in o.data.vertices:v.co.x+=.38*(v.co.z/height)**2
    # Collapse fire parts by their shared surfaces before instancing.
    if len(parts)>1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
    write(key,'world',base,'Metric uniform-height fit of new reconstruction/clean repair, modest authored shape/yaw variant.')

def coin():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/prepared/coin.blend'))
    parts=[o for o in bpy.context.scene.objects if o.type=='MESH'];lo,hi=bridge.bounds(parts);center=(lo+hi)*.5;factor=.126/(hi.x-lo.x)
    for o in parts:
        o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
        for v in o.data.vertices:v.co=(v.co-center)*factor
        bm=bmesh.new();bm.from_mesh(o.data)
        # True square aperture: white studio pixels reconstructed inside the
        # hole are removed, while the newly reconstructed minting is retained.
        discard=[f for f in bm.faces if abs(f.calc_center_median().x)<.013 and abs(f.calc_center_median().z)<.013]
        bmesh.ops.delete(bm,geom=discard,context='FACES')
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
        bm.to_mesh(o.data);bm.free();o.data.transform(Matrix.Rotation(math.pi/2,4,'X'))
        for mat in o.data.materials:
            p=mat.node_tree.nodes['Principled BSDF'];p.inputs['Metallic'].default_value=.9;p.inputs['Roughness'].default_value=.34
    write('gold_coin','equipment','coin','Reconstructed minted relief retained; white filled aperture cut out, flat loot orientation and 126 mm metric diameter.')

def fracture():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/prepared/fracture.blend'))
    source=next(o for o in bpy.context.scene.objects if o.type=='MESH');source.data.transform(source.matrix_world);source.parent=None;source.matrix_world=Matrix.Identity(4)
    lo,hi=bridge.bounds([source]);factor=4.6/(hi.z-lo.z);center=(lo+hi)*.5
    for v in source.data.vertices:v.co=Vector(((v.co.x-center.x)*factor,(v.co.y-center.y)*factor,(v.co.z-lo.z)*factor))
    color_source=source.copy();color_source.data=source.data.copy();bpy.context.collection.objects.link(color_source)
    color_source.name='NewNativeFractureColorSource'
    labels={f.index:int(((math.atan2(f.center.y,f.center.x)-.18)%math.tau)/math.tau*7)%7 for f in source.data.polygons}
    source.data.update()
    # Recompute after coordinate changes; Polygon.center may be cached.
    labels={f.index:int(((math.atan2(f.center.y,f.center.x)-.18)%math.tau)/math.tau*7)%7 for f in source.data.polygons}
    for i in range(7):
        o=source.copy();o.data=source.data.copy();bpy.context.collection.objects.link(o);o.name=f'Rib_{i}'
        bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table()
        # Keep only the reconstructed roots. The native upper cage fuses its
        # interior into a solid post, hiding the core even after a narrow cut.
        remove=[f for f in bm.faces if labels[f.index]!=i or f.calc_center_median().z>.58]
        bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
        bm.to_mesh(o.data);bm.free()
        bark=clean.material('ScarBark_'+str(i),(.15+.008*(i%3),.070,.027),rough=.88)
        ridge=clean.material('ScarBarkRidge_'+str(i),(.075,.032,.011),rough=.95)
        points=[];radii=[]
        for j,(radius,z,width) in enumerate([(1.24,.38,.26),(1.30,.83,.25),(1.17,1.47,.22),(1.04,2.16,.20),(.88,2.88,.18),(.62,3.49,.15),(.31,4.08,.10),(.16,4.52,.001)]):
            angle=i*math.tau/7+.18+.10*math.sin(j*.8+i)
            points.append(Vector((radius*math.cos(angle),radius*math.sin(angle),z)));radii.append(width)
        new_parts=[clean.tube('OpenCageRib',points,radii,bark,12)]
        for side in [-1,1]:
            groove=[p+Vector((math.cos(i*math.tau/7+.18),math.sin(i*math.tau/7+.18),0))*r*.91+Vector((0,0,side*.028)) for p,r in zip(points[:-1],radii[:-1])]
            new_parts.append(clean.tube('BarkGroove',groove,[.028,.031,.025,.023,.018,.013,.001],ridge,5))
        twig_start=points[3]
        outward=Vector((math.cos(i*math.tau/7+.18),math.sin(i*math.tau/7+.18),.6))
        new_parts.append(clean.tube('BrokenBranch',[twig_start,twig_start+outward*.42,twig_start+outward*.67],[.065,.041,.001],bark,7))
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
        for part in new_parts:part.select_set(True)
        bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.name=f'Rib_{i}'
        # The native upper cage has empty-space paint across its ribs. Baking
        # it onto the repaired cage produces black/yellow bands. Author bark
        # colors on the clean surface instead of projecting that defect.
        for attribute in list(o.data.color_attributes):o.data.color_attributes.remove(attribute)
        colors=o.data.color_attributes.new(name='RepairedBarkColor',type='FLOAT_COLOR',domain='CORNER')
        for face in o.data.polygons:
            dark='Ridge' in o.data.materials[face.material_index].name
            for loop in face.loop_indices:
                p=o.data.vertices[o.data.loops[loop].vertex_index].co
                variation=.84+.12*math.sin(p.z*7.1+p.x*17)+.06*math.sin(p.y*23-p.z*3)
                base=(.11,.048,.018) if dark else (.24,.115,.038)
                colors.data[loop].color=(*[c*variation for c in base],1)
            face.material_index=0
        o.data.materials.clear();mat=clean.material('RepairedBark',(1,1,1),rough=.91);o.data.materials.append(mat)
        node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name=colors.name
        mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    bpy.data.objects.remove(source,do_unlink=True)
    bpy.data.objects.remove(color_source,do_unlink=True)
    amber=clean.material('FloatingAmber',(.72,.16,.015),.1,.28);p=amber.node_tree.nodes['Principled BSDF'];p.inputs['Emission Color'].default_value=(1,.20,.014,1);p.inputs['Emission Strength'].default_value=1.2
    vertices=[];faces=[]
    for radius,z in [(0,1.35),(.34,1.69),(.28,2.33),(0,2.66)]:
        for i in range(10):a=i*math.tau/10;vertices.append((radius*math.cos(a),radius*math.sin(a),z))
    for j in range(3):
        for i in range(10):a=j*10+i;b=j*10+(i+1)%10;faces.append((a,b,b+10,a+10))
    clean.mesh('Core_0',vertices,faces,amber,False)
    write('fracture','world','fracture','Native roots retained; seven fused upper ribs remodeled as clean open bark cage from the four references, with floating emissive crystal. Rib/Core gameplay node contract retained.')

plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets']
base_by_family={'wolf':'meadow_wolf','boar':'ironhide_boar','spider':'reed_spider','mossling':'mossling','stonekin':'stonekin','wisp':'wisp','bandit':'bandit'}
coats=dict(re.findall(r'&"([a-z_]+)": "([0-9a-f]{6})"',(ROOT/'game/scripts/visuals/creature_materials.gd').read_text()))
for e in plan:
    if e['category']!='mob':continue
    key=e['mob_id'];base=base_by_family[e['family']]
    if only and key not in only and base not in only:continue
    resource=(ROOT/'game/data/enemies'/f'{key}.tres').read_text();tier=int(re.search(r'tier = (\d+)',resource).group(1));hexcolor=coats.get(key,'ffffff')
    # Approximate albedo factors in linear space without over-darkening fur.
    color=tuple(int(hexcolor[i:i+2],16)/255 for i in [0,2,4])
    skinned_variant(key,base,'mobs',e['family'],tier,color)
for key,base in [('smith','blacksmith'),('keeper','keeper'),('stablemaster','stablemaster'),('mara','keeper'),('apothecary','keeper'),('artificer','stablemaster'),('armorer','blacksmith'),('weapons','blacksmith'),('warden','stablemaster'),('ash_scout','stablemaster')]:
    if only and key not in only and base not in only:continue
    skinned_variant(key,base,'npcs','humanoid',1,{'mara':(.93,.80,.71),'apothecary':(.78,.93,.81),'warden':(.8,.85,.99),'artificer':(.92,.77,.98)}.get(key,(1,1,1)))
for key,spec in STATIC.items():
    if only and key not in only and spec[0] not in only:continue
    static_variant(key,spec)
if not only or 'coin' in only:coin()
if not only or 'fracture' in only:fracture()
