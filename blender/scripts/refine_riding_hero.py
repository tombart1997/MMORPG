"""Refine the rider independently, retaining the existing rig and combat clips.

blender -b --factory-startup -P blender/scripts/refine_riding_hero.py
"""
import bpy, math, importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/reference/rider/warden_riding_base.blend'))
rig=bpy.data.objects['WardenRig']
rig.animation_data.action=None
for pb in rig.pose.bones: pb.matrix_basis.identity()
parts=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.find_armature()==rig]
for obj in parts:
    name=obj.name
    # Slim the outer shell around each unchanged shoulder pivot. Hand reach,
    # sockets and attack timing remain defined by the original skeleton.
    if name.startswith(('HeroPauldron','ShoulderRolledLip','Jade_Shoulder','HeroBiceps','Tailored_UpperArm')):
        sign=1 if sum(v.co.x for v in obj.data.vertices)>0 else -1
        for v in obj.data.vertices:
            v.co.x=sign*.3144+(v.co.x-sign*.3144)*.73
            v.co.y*=.84
            if name.startswith(('HeroPauldron','ShoulderRolledLip','Jade_Shoulder')):
                v.co.z=1.43+(v.co.z-1.43)*.84
    if name.startswith(('Body_Boot','BootSole','Sabatons','HeroSabaton')):
        sign=1 if sum(v.co.x for v in obj.data.vertices)>0 else -1
        for v in obj.data.vertices:
            v.co.x=sign*.1498+(v.co.x-sign*.1498)*.82
            v.co.y=.015+(v.co.y-.015)*.82
    # Broad front robe panels used to stretch diagonally into the saddle. A
    # deeper riding split and shorter hems leave the articulated thighs clear.
    if name.startswith(('Jade_SilkFall','Jade_RobeBorder','Jade_CloudEmbroidery')):
        for v in obj.data.vertices:
            t=max(0,min(1,(.997-v.co.z)/.53))
            sign=1 if v.co.x>=0 else -1
            v.co.x+=sign*.018*t
            v.co.z+=.115*t
        for v in obj.data.vertices:
            side='R' if v.co.x>=0 else 'L'
            thigh=max(0,min(1,(.997-v.co.z)/.10))
            obj.vertex_groups['Thigh.'+side].add([v.index],thigh,'REPLACE')
            obj.vertex_groups['Hips'].add([v.index],1-thigh,'REPLACE')

# Warmer skin, muted jade steel, matte woven silk and worn leather read clearly
# under both studio illumination and Godot's outdoor lighting.
for mat in bpy.data.materials:
    if not mat.use_nodes: continue
    shader=mat.node_tree.nodes.get('Principled BSDF')
    if not shader: continue
    if 'Skin' in mat.name:
        for link in list(shader.inputs['Base Color'].links):mat.node_tree.links.remove(link)
        shader.inputs['Base Color'].default_value=(.47,.305,.19,1)
        mat.diffuse_color=(.47,.305,.19,1)
        shader.inputs['Roughness'].default_value=.68
    if any(s in mat.name for s in ['Silk','Undercloth','Cloth']):
        shader.inputs['Roughness'].default_value=.92
    if 'Leather' in mat.name: shader.inputs['Roughness'].default_value=.78
    if 'Steel' in mat.name: shader.inputs['Roughness'].default_value=.43

spec=importlib.util.spec_from_file_location('wh',Path(__file__).with_name('build_warden_high.py'))
wh=importlib.util.module_from_spec(spec);spec.loader.exec_module(wh)
wh.RIG=rig;wh.PARTS=parts
wh.export()
print('RIDER_REFINED',len(parts),flush=True)
