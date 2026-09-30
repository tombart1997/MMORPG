"""Reviewed fit and material corrections after the second studio render."""
import bpy, math, importlib.util
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('wh',Path(__file__).with_name('build_warden_high.py'))
wh=importlib.util.module_from_spec(spec);spec.loader.exec_module(wh)
wh.RIG=bpy.data.objects['WardenRig'];wh.PARTS=[o for o in bpy.context.scene.objects if o.type=='MESH']
wh.MATS={m.name.removeprefix('Warden_'):m for m in bpy.data.materials if m.name.startswith('Warden_')}

def finish():
    beard=bpy.data.objects.get('CloseBeard')
    if beard:wh.PARTS.remove(beard);bpy.data.objects.remove(beard,do_unlink=True)
    # Fit the lower neck inside the collar. This corrects the loose shoulder cutoff.
    for o in wh.PARTS:
        if o.name=='AnatomicalHead':
            for v in o.data.vertices:
                z=v.co.z
                if z<1.61:
                    t=max(0,min(1,(1.61-z)/.09))
                    v.co.x*=1-.66*t
                    v.co.y*=1-.22*t
                    v.co.z-=.05*t
        if o.name.startswith('FittedIris') or o.name.startswith('FittedPupil'):
            for v in o.data.vertices:v.co.y+=.0073
    # Stubble coloration is blended across the face, rather than a separate beard shell.
    face=bpy.data.objects['AnatomicalHead']
    colors=face.data.color_attributes.new(name='SkinTint',type='FLOAT_COLOR',domain='POINT')
    for i,v in enumerate(face.data.vertices):
        x,y,z=v.co
        lower=max(0,min(1,(1.710-z)/.035))*max(0,min(1,(z-1.622)/.025))
        front=max(0,min(1,(y-.025)/.025))
        mouth=math.exp(-((x/.028)**2)-((z-1.663)/.017)**2)
        amount=lower*front*(1-mouth)*.56
        colors.data[i].color=(1-amount,1-amount*.91,1-amount*.83,1)
    mat=wh.MATS['Skin'];nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bsdf=nodes.get('Principled BSDF');tex=next(n for n in nodes if n.type=='TEX_IMAGE')
    attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='SkinTint'
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    links.new(tex.outputs['Color'],mix.inputs[1]);links.new(attr.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
    hair=wh.MATS['Hair'];shader=hair.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(.004,.0025,.0018,1)
    shader.inputs['Roughness'].default_value=.94;shader.inputs['Specular IOR Level'].default_value=.06
    # Fine physical surface variation catches light as short hair, not a polished cap.
    obj=bpy.data.objects['CroppedHair']
    for v in obj.data.vertices:
        wave=math.sin(v.co.x*2300+v.co.z*390)*math.sin(v.co.y*1800+v.co.x*400)
        v.co+=v.normal*wave*.00032
    # Brows follow the eye sockets with tapered strands, also visible at gameplay range.
    for s in [-1,1]:
        wh.line('NaturalBrow',[(s*(.015+i*.0024),.077-i*.00035,1.770+.004*math.sin(i/15*math.pi)) for i in range(16)],.0027,hair,'Head')
    for m in [wh.MATS['Steel'],wh.MATS['DarkSteel']]:
        m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.43
    print('Neck fitted into collar; visible pupils; blended stubble; cropped hair detail')

if __name__=='__main__':finish()
