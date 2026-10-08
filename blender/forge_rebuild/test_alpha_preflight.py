"""Actual bpy proof: unsupported transparency fails before target mutation."""
import bpy,sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\Tom\Documents\2D_to_3D\blender')
from optimize import bake_materials
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add();source=bpy.context.object;source.name='Source'
mat=bpy.data.materials.new('LinkedAlpha');mat.use_nodes=True;source.data.materials.append(mat)
value=mat.node_tree.nodes.new('ShaderNodeValue');value.outputs[0].default_value=.3
mat.node_tree.links.new(value.outputs[0],mat.node_tree.nodes['Principled BSDF'].inputs['Alpha'])
target=source.copy();target.data=source.data.copy();target.name='Target';bpy.context.collection.objects.link(target)
uv_before=[[(p.uv.x,p.uv.y) for p in layer.data] for layer in target.data.uv_layers]
materials_before=list(target.data.materials)
try:bake_materials(source,target,128);raise AssertionError('Linked alpha unexpectedly accepted')
except ValueError as error:assert 'transparency' in str(error);reason=str(error)
assert list(target.data.materials)==materials_before
assert [[(p.uv.x,p.uv.y) for p in layer.data] for layer in target.data.uv_layers]==uv_before
assert mat.node_tree.nodes['Principled BSDF'].inputs['Alpha'].is_linked
out=Path(r'D:\Games\Metin2Clone\docs\asset_optimization\alpha_preflight.json')
out.write_text(json.dumps({'status':'passed','reason':reason,'target_uvs_unchanged':True,'target_materials_unchanged':True,'source_alpha_link_unchanged':True,'scope':'Real Blender bpy transparency guard; no remeshing or paid generation performed.'},indent=2))
print('ALPHA_PREFLIGHT passed')
