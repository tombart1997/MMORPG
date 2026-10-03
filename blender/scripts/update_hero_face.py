"""Adjust the preserved hero face and skin without changing rig, gear or animation."""
import bpy, importlib.util, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
spec=importlib.util.spec_from_file_location('hero',Path(__file__).with_name('build_warden_hero.py'))
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
skin=bpy.data.materials['Warden_Skin'];skin.node_tree.nodes.clear()
p=skin.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=skin.node_tree.nodes.new('ShaderNodeOutputMaterial')
skin.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
skin.diffuse_color=(.82,.65,.48,1);p.inputs['Base Color'].default_value=skin.diffuse_color;p.inputs['Roughness'].default_value=.72
head=bpy.data.objects['AnatomicalHead']
if not head.get('east_asian_face_pass'):
    # Subtle cheek planes, a less projecting bridge and softer lip volumes.
    # Keep the fitted eyes, hairline and head/socket bounds in place.
    for v in head.data.vertices:
        x,y,z=v.co
        front=max(0,min(1,(y-.025)/.045))
        cheek=math.exp(-((abs(x)-.074)/.036)**2-((z-1.625)/.05)**2)*front
        nose=math.exp(-(x/.024)**2-((z-1.647)/.058)**2)*front
        lip=math.exp(-(x/.038)**2-((z-1.575)/.021)**2)*front
        v.co.x+=math.copysign(.0035*cheek,x)
        v.co.y-=.006*nose+.003*lip
    head['east_asian_face_pass']=True
if not head.get('east_asian_eye_pass'):
    for v in head.data.vertices:
        x,y,z=v.co
        mask=math.exp(-((abs(x)-.035)/.020)**4-((z-1.687)/.011)**4)*max(0,min(1,(y-.025)/.040))
        v.co.z+=(.0012*(abs(x)-.035)/.017-.20*(z-1.687))*mask
    head['east_asian_eye_pass']=True
# Warm, clean-shaven facial planes and restrained lip/cheek coloration.
colors=head.data.color_attributes.get('SkinTint')
if colors:
    for v in head.data.vertices:
        x,y,z=v.co;front=max(0,min(1,(y-.025)/.045))
        lips=math.exp(-(x/.028)**4-((z-1.598)/.007)**2)*front
        cheek=math.exp(-((abs(x)-.062)/.035)**2-((z-1.636)/.035)**2)*front
        shade=.985-.035*math.sin(x*125+z*57)**2
        colors.data[v.index].color=(.82*shade*(1-.13*lips),.65*shade*(1-.27*lips-.055*cheek),.48*shade*(1-.25*lips-.07*cheek),1)
# COLOR_0 is requested only by the skin material. Set matching colors on
# every skin part, while armor keeps its own authored material surfaces.
for obj in hero.wh.PARTS:
    if obj == head or skin not in obj.data.materials[:]: continue
    attribute=obj.data.color_attributes.get('SkinTint') or obj.data.color_attributes.new(name='SkinTint',type='FLOAT_COLOR',domain='POINT')
    for color in attribute.data: color.color=skin.diffuse_color
attribute_node=skin.node_tree.nodes.new('ShaderNodeVertexColor');attribute_node.layer_name='SkinTint'
skin.node_tree.links.new(attribute_node.outputs['Color'],p.inputs['Base Color'])
# Fit eyebrows and lids to the actual head surface, rather than obsolete
# coordinates from the earlier head model. Preserve its continuous skin.
for obj in list(hero.wh.PARTS):
    if obj.name.startswith(('NaturalBrow','EastAsian_')):
        hero.wh.PARTS.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)
bvh=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices for p in head.data.polygons])
def face_point(x,z,lift=.0008):
    hit=bvh.ray_cast(Vector((x,.5,z)),Vector((0,-1,0)))[0]
    return (x,hit.y+lift if hit else .095,z)
hair=bpy.data.materials['Warden_Hair']
crease=hero.wh.material('FaceCrease',(.23,.105,.060),0,.85)
for s in [-1,1]:
    points=[face_point(s*(.014+i*.0023),1.711+.004*math.sin(i/17*math.pi)-.002*i/17,.0012) for i in range(18)]
    hero.wh.tube('EastAsian_Brow',points,[.00045+.00095*math.sin(i/17*math.pi)**.5 for i in range(18)],hair,'Head',8)
    hero.wh.line('EastAsian_LidCrease',[face_point(s*(.024+i*.0011),1.697+.0014*math.sin(i/20*math.pi),.0001) for i in range(21)],.00016,crease,'Head')
hero.wh.line('EastAsian_Mouth', [face_point(x/1000,1.598+.0009*math.cos(x/25*math.pi),.0001) for x in range(-25,26,2)],.00020,crease,'Head')
iris=bpy.data.materials['Warden_Iris']
iris.diffuse_color=(.043,.019,.007,1)
iris.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=iris.diffuse_color
for mat in bpy.data.materials:
    if mat.name in ['Warden_Hair','Warden_HairHighlight']:
        color=(.012,.009,.006,1) if mat.name=='Warden_Hair' else (.025,.020,.014,1)
        mat.diffuse_color=color
        shader=mat.node_tree.nodes['Principled BSDF']
        shader.inputs['Base Color'].default_value=color
        shader.inputs['Roughness'].default_value=.82
        shader.inputs['Specular IOR Level'].default_value=.18
hero.wh.export()
print('HERO_FACE_COMPLETE',flush=True)
