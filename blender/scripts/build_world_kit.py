"""Ironfield landscape kit. Original mesh authorship; existing project textures.
Run: blender --background --factory-startup --python-exit-code 1 --python blender/scripts/build_world_kit.py
One consolidated runtime mesh per asset; editable Blender source and budget manifest.
Blender coordinates are Z-up; GLB exports to Godot Y-up.
"""
import bpy
import math
import random
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'game/assets/world_kit'
SRC = ROOT / 'blender/world_kit'
TEX = ROOT / 'game/assets/benchmark/textures'
OUT.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)
REPORT = {}


def material(name, texture, tint, double=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*tint, 1)
    mat.use_backface_culling = not double
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*tint, 1)
    bsdf.inputs['Roughness'].default_value = .92
    bsdf.inputs['Specular IOR Level'].default_value = .15
    image = nodes.new('ShaderNodeTexImage')
    image.image = bpy.data.images.load(str(TEX / texture), check_existing=True)
    vertex_color = nodes.new('ShaderNodeVertexColor')
    vertex_color.layer_name = 'Color'
    multiply = nodes.new('ShaderNodeMixRGB')
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = 1
    links.new(image.outputs['Color'], multiply.inputs[1])
    links.new(vertex_color.outputs['Color'], multiply.inputs[2])
    links.new(multiply.outputs[0], bsdf.inputs['Base Color'])
    return mat


def reset(seed):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    random.seed(seed)


def mesh(name, verts, faces, mat, smooth=False, colors=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    uv = data.uv_layers.new(name='LandscapeUV')
    col = data.color_attributes.new(name='Color', type='BYTE_COLOR', domain='CORNER')
    for poly in data.polygons:
        poly.use_smooth = smooth
        axis = max(range(3), key=lambda i: abs(poly.normal[i]))
        for li in poly.loop_indices:
            vi = data.loops[li].vertex_index
            p = data.vertices[vi].co
            pair = (p.y, p.z) if axis == 0 else ((p.x, p.z) if axis == 1 else (p.x, p.y))
            uv.data[li].uv = (pair[0] * .55, pair[1] * .55)
            col.data[li].color = colors[vi] if colors else (1, 1, 1, 1)
    return obj


def branch(name, points, radii, mat, sides=9):
    verts, faces = [], []
    for j, p in enumerate(points):
        center = Vector(p)
        tangent = Vector(points[min(j+1, len(points)-1)]) - Vector(points[max(0,j-1)])
        tangent.normalize()
        across = tangent.cross(Vector((0,1,0))).normalized()
        if across.length < .1:
            across = Vector((1,0,0))
        other = tangent.cross(across).normalized()
        for k in range(sides):
            a = k * math.tau/sides
            r = radii[j] * (1 + .14*math.sin(k*2.4+j*.6))
            verts.append(center + (across*math.cos(a)+other*math.sin(a))*r)
        if j:
            for k in range(sides):
                n = (k+1) % sides
                faces.append(((j-1)*sides+k, (j-1)*sides+n, j*sides+n, j*sides+k))
    faces.extend([tuple(reversed(range(sides))), tuple(range(len(verts)-sides,len(verts)))])
    return mesh(name, verts, faces, mat, True)


def leaves(name, centers, mat, count=60, extent=(.8,.7,.45), leaf_size=.55):
    verts, faces, colors = [], [], []
    for center in centers:
        for i in range(count):
            a = random.random()*math.tau
            r = math.sqrt(random.random())
            p = Vector(center)+Vector((math.cos(a)*extent[0]*r, math.sin(a)*extent[1]*r, random.uniform(-1,1)*extent[2]))
            direction = Vector((math.cos(a),math.sin(a),random.uniform(-.25,.45)))
            length = leaf_size * random.uniform(.65,1.25)
            side = Vector((-math.sin(a),math.cos(a),0)) * length * .26
            tip = p + direction*length
            middle = p.lerp(tip,.45)
            ridge = middle + Vector((0,0,length*.13))
            n = len(verts)
            verts.extend([p, middle+side, tip, middle-side, ridge])
            faces.extend([(n,n+1,n+4),(n+1,n+2,n+4),(n+2,n+3,n+4),(n+3,n,n+4)])
            # Value changes by spray and leaf, giving readable canopy planes.
            tone = random.uniform(.7,1.15)
            colors.extend([(tone*.92,tone,tone*.83,1)]*5)
    return mesh(name,verts,faces,mat,False,colors)


def fractured(name, center, size, mat, seed, tilt=0, shelf=False):
    rng = random.Random(seed)
    verts, faces, colors = [], [], []
    sides = 11
    # Tilted fractured shelves with unequal facets; never a scaled sphere.
    profile = [(-.12,.83),(.12,1.05),(.47,.96),(.78,.81),(1,.48)]
    if shelf:
        profile = [(-.12,.9),(.15,1.05),(.47,.97),(.73,.92),(1,.83)]
    angles = [k*math.tau/sides+rng.uniform(-.12,.12) for k in range(sides)]
    widths = [rng.uniform(.8,1.16) for _ in range(sides)]
    for j,(h,r) in enumerate(profile):
        for k,a in enumerate(angles):
            x = math.cos(a)*r*widths[k]*size[0] + h*tilt
            y = math.sin(a)*r*widths[k]*size[1]
            z = (h + rng.uniform(-.08,.08))*size[2]
            verts.append(Vector(center)+Vector((x,y,z)))
            tone = rng.uniform(.82,1.08)*(1 if j<3 else 1.05)
            colors.append((tone,tone,tone,1))
            if j:
                n = (k+1)%sides
                faces.append(((j-1)*sides+k,(j-1)*sides+n,j*sides+n,j*sides+k))
    faces.append(tuple(range(len(verts)-sides,len(verts))))
    faces.append(tuple(reversed(range(sides))))
    return mesh(name,verts,faces,mat,False,colors)


def block(name, center, size, mat, bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new('WornEdges','BEVEL')
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    uv = obj.data.uv_layers.active
    for loop in uv.data:
        loop.uv *= 2
    return obj


def roof(center, width, depth, mat):
    verts,faces=[],[]
    xs=[0,.45,.83,1]
    hs=[1.0,.46,.1,.18]
    for sign in [-1,1]:
        for i in range(3):
            for j in range(4):
                n=len(verts)
                for ix,jz in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]:
                    y=(jz/4-.5)*depth
                    verts.append(Vector(center)+Vector((sign*xs[ix]*width*.5,y,hs[ix]+.12*abs(y/(depth*.5))**3)))
                faces.append(tuple(range(n,n+4)) if sign>0 else tuple(reversed(range(n,n+4))))
    return mesh('SweptTileRoof',verts,faces,mat)


def export(name):
    objects = [o for o in bpy.context.scene.objects if o.type=='MESH']
    editable = len(objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/(name+'.blend')))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects)>1:
        bpy.ops.object.join()
    obj = bpy.context.object
    # A zero origin makes Godot instance transforms predictable.
    bpy.context.scene.cursor.location = (0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.name = name
    obj.data.calc_loop_triangles()
    REPORT[name] = {'triangles':len(obj.data.loop_triangles),'surfaces':len(set(p.material_index for p in obj.data.polygons)),'editable_parts':editable,'runtime_meshes':1}
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',export_yup=True,export_animations=False,export_materials='EXPORT',export_all_vertex_colors=True)
    print('WORLD_KIT',name,json.dumps(REPORT[name]),flush=True)


bark=material('MarchBark','GroveBark_albedo.png',(.34,.29,.2))
foliage=material('MarchLeaves','GroveLeaves_albedo.png',(.3,.43,.16),True)
under=material('MarchUnderstory','UnderstoryLeaves_albedo.png',(.25,.38,.14),True)
slate=material('MarchSlate','BlueSlate_albedo.png',(.38,.44,.44))
lichen=material('MarchLichen','SlateLichen_albedo.png',(.4,.47,.3))
wood=material('MarchTimber','Deadwood_albedo.png',(.4,.31,.19))
tiles=material('MarchTiles','BlueSlate_albedo.png',(.32,.4,.4))
cloth=material('MarchCanvas','cloth_color.png',(.5,.32,.18),True)

for variant in range(3):
    reset(2600+variant)
    height=[7.2,8.5,6.4][variant]
    bend=[-1.4,.8,1.9][variant]
    branch('RootedTrunk',[(0,0,-.2),(.05,0,.5),(.15,.05,2),(bend*.32,.1,3.6),(bend*.75,.1,height*.75),(bend,.3,height)], [.65,.48,.32,.26,.13,.025],bark,12)
    for i in range(5):
        a=i*math.tau/5+.2
        branch('ExposedRoot',[(math.cos(a)*1.25,math.sin(a)*1.25,-.04),(math.cos(a)*.65,math.sin(a)*.65,.15),(0,0,.8)],[.025,.18,.25],bark,7)
    sprays=[]
    for i in range(12):
        a=i*2.399+variant*.7
        h=height*(.46+.032*i)
        start=Vector((bend*h/height*.65,.05,h))
        spread=[2.3,1.8,2.7][variant]*(1-.35*i/12)
        tip=start+Vector((math.cos(a)*spread,math.sin(a)*spread,.8))
        middle=start.lerp(tip,.58)+Vector((0,0,.2))
        branch('CrookedLimb',[start,middle,tip],[.16-i*.007,.085,.015],bark,8)
        sprays.extend([tip,middle+Vector((math.cos(a+.7)*.6,math.sin(a+.7)*.6,.3))])
    leaves('LeafSprays',sprays,foliage,count=40,extent=(.85,.85,.38),leaf_size=.56)
    export('tree%d'%variant)

for variant in range(3):
    reset(370+variant)
    fractured('SlateShoulder',(0,0,0),(1.15,.8,1.25),slate,40+variant,.5-variant*.3)
    fractured('SplitShelf',(.55,-.18,.16),(.7,.55,.78),lichen,60+variant,-.25)
    fractured('BrokenFoot',(-.6,.3,-.06),(.55,.55,.42),slate,70+variant,.1)
    export('rock%d'%variant)

for variant in range(2):
    reset(880+variant)
    for i in range(4):
        fractured('StratifiedFace',(i*1.8-2.7,math.sin(i)*.35,.1),(1.45,1.1,1.7+(i%3)*.48),slate,150+i+variant*13,.36,True)
        fractured('UpperShelf',(i*1.8-2.6,.38,1.45),(1.25,.9,.8+(i%2)*.55),slate,180+i+variant*13,.2,True)
        fractured('Talus',(i*1.8-2.7,-1.0,-.12),(1.0,.8,.65),lichen,170+i,.2)
    export('cliff' if variant==0 else 'cliff1')

reset(812)
branch('DeadTrunk',[(0,0,-.1),(.2,0,1.6),(-.3,.15,3.1),(.3,.4,5.3)],[.5,.32,.22,.02],bark,10)
for i in range(5):
    a=i*2.4
    branch('BrokenBough',[(.1,0,1.8+i*.5),(math.sin(a)*1.4,math.cos(a)*1.1,2.8+i*.4),(math.sin(a)*1.8,math.cos(a)*1.4,3.4+i*.4)],[.18,.09,.015],bark,7)
export('dead_tree')

reset(804)
branch('SplinteredFallenTrunk',[(-1.8,0,.22),(-.7,.15,.34),(.5,.05,.3),(1.7,.2,.45)],[.2,.3,.24,.08],wood,10)
for i in range(4):
    branch('BrokenStubs',[(-1+i*.65,.1,.4),(-.7+i*.65,(-1)**i*.55,.65)],[.11,.025],bark,7)
export('log')

reset(814)
sprays=[]
for i in range(9):
    a=i*2.4
    tip=(math.sin(a)*.65,math.cos(a)*.65,.6+random.random()*.45)
    branch('ShrubStem',[(0,0,0),tip],[.025,.004],bark,5)
    sprays.append(tip)
leaves('ShrubLeaves',sprays,under,count=12,extent=(.23,.23,.14),leaf_size=.3)
export('shrub')

reset(815)
for i in range(7):
    a=i*2.4
    direction=Vector((math.sin(a),math.cos(a),0))
    side=Vector((math.cos(a),-math.sin(a),0))
    tip=direction*(.5+random.random()*.2)+Vector((0,0,.45))
    branch('FernStem',[(0,0,0),tip*.5+Vector((0,0,.22)),tip],[.012,.008,.002],under,5)
    centers=[]
    for j in range(1,8):
        center=tip*j/8+Vector((0,0,math.sin(j/8*math.pi)*.2))
        centers.extend([center+side*.1,center-side*.1])
    leaves('FernPinnae',centers,under,count=1,extent=(.03,.03,.01),leaf_size=.18)
export('fern')

reset(816)
verts,faces=[],[]
for i in range(13):
    a=i*2.4
    p=Vector((math.sin(a)*.15,math.cos(a)*.15,0))
    tip=p+Vector((math.sin(a)*.25,math.cos(a)*.25,random.uniform(.22,.6)))
    across=Vector((math.cos(a),-math.sin(a),0))*.025
    n=len(verts)
    verts.extend([p-across,p+across,tip*.65+Vector((0,0,.08))+across*.5,tip])
    faces.extend([(n,n+1,n+2),(n,n+2,n+3)])
mesh('BentGrassBlades',verts,faces,under)
export('grass')

reset(820)
# Broken arch: asymmetric piers, displaced voussoirs, open center.
for sign in [-1,1]:
    for i in range(4 if sign<0 else 3):
        block('ErodedPier',(sign*2,0,.4+i*.72),(1,.95,.7),slate,.13)
for i in range(9):
    a=.1+i*math.pi/10
    obj=block('ArchStone',(math.cos(a)*2,0,2.65+math.sin(a)*1.45),(.78,1.0,.62),lichen,.1)
    obj.rotation_euler.y=-(a-math.pi*.5)
fractured('FallenKeystone',(2.8,-.9,0),(.65,.7,.55),slate,881)
export('ruin_arch')

reset(822)
block('StonePlinth',(0,0,.15),(2.1,1.9,.3),slate,.12)
block('ShrineBase',(0,0,.6),(1.45,1.3,.65),lichen,.08)
block('RecessedTablet',(0,0,1.65),(.7,.5,1.65),slate,.1)
for x in [-.62,.62]:
    branch('ShrinePillar',[(x,-.4,.65),(x,-.4,2.55)],[.1,.09],wood,8)
roof((0,0,2.4),2.35,1.85,tiles)
block('TabletInset',(0,-.275,1.65),(.3,.04,1),wood,.02)
export('shrine')

reset(823)
for x in [-1.35,1.35]:
    for y in [-1.35,1.35]:
        branch('WatchPillar',[(x,y,0),(x*.93,y*.93,7.2)],[.18,.12],wood,8)
for z in [2.4,5.2]:
    block('Platform',(0,0,z),(3.1,3.1,.22),wood,.02)
    for side in [-1,1]:
        branch('CrossBrace',[(side*1.35,-1.35,z-2.3),(-side*1.35,-1.35,z)],[.09,.09],wood,6)
for sign in [-1,1]:
    block('Balustrade',(sign*1.35,0,6.05),(.12,2.7,.8),wood,.025)
    block('Balustrade',(0,sign*1.35,6.05),(2.7,.12,.8),wood,.025)
roof((0,0,7.0),4.6,4.4,tiles)
export('watchtower')

reset(827)
# Sagged, seamed canvas; irregular hem, open entrance and visible timber ridge.
verts,faces=[],[]
xs=[-1.6,-1.1,-.55,0,.55,1.1,1.6]
for side in [-1,1]:
    for i in range(3):
        for j in range(8):
            n=len(verts)
            for ix,jy in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]:
                x=xs[ix] if side<0 else -xs[ix]
                y=-1.8+jy*.45
                z=1.95*(1-abs(x)/1.8)-.12*math.sin(jy/8*math.pi)+.04*math.sin(jy*2.8+ix)
                verts.append((x,y,z))
            faces.append(tuple(reversed(range(n,n+4))) if side<0 else tuple(range(n,n+4)))
obj=mesh('SaggedCanvas',verts,faces,cloth,True)
for x in [-1.55,1.55]:
    for y in [-1.65,1.65]:
        branch('GuyRope',[(x,y,.35),(x*1.5,y*1.25,.02)],[.015,.015],wood,5)
        branch('TentPeg',[(x*1.5,y*1.25,-.05),(x*1.5,y*1.25,.17)],[.035,.022],wood,5)
for y in [-1.85,1.85]:
    branch('RidgeSupport',[(0,y,0),(0,y,2.05)],[.065,.05],wood,8)
branch('RidgePole',[(0,-1.9,1.98),(0,1.9,1.98)],[.055,.055],wood,8)
export('tent')

(OUT/'manifest.json').write_text(json.dumps(REPORT,indent=2)+'\n')
