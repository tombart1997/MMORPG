"""End-to-end regression for color detail/appearance surviving simplification."""
import io
import json
import struct
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
from export_glb import export_mesh


def test_simplification_bakes_godot_color_to_texture_without_double_tint(tmp_path):
    mesh=trimesh.creation.icosphere(subdivisions=3)
    mesh.visual.vertex_colors=np.tile([100,70,40,255],(len(mesh.vertices),1))
    source=tmp_path/'source.glb';export_mesh(mesh,source)
    out=tmp_path/'processed';out.mkdir()
    request=tmp_path/'request.json'
    request.write_text(json.dumps({'source':str(source),'output':str(out),'stage':'process','settings':{
        'optimization_mode':'simplify','triangle_budget':500,'max_surface_error':.04,
        'texture_resolution':256,'bypass_rigging':True,'render_preview':False,'export_formats':['glb']}}))
    script=Path(__file__).resolve().parents[2]/'blender/pipeline.py'
    result=subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','--background','--threads','2',
        '--python-exit-code','1','--python',str(script),'--','--request',str(request)],capture_output=True,text=True,timeout=120)
    assert result.returncode==0,result.stdout[-4000:]+result.stderr[-4000:]
    report=json.loads((out/'optimization.json').read_text())
    assert report['objects'][0]['material_transfer']=='rebaked_atlas'
    blob=(out/'runtime.glb').read_bytes();size=struct.unpack_from('<I',blob,12)[0]
    doc=json.loads(blob[20:20+size]);attrs=doc['meshes'][0]['primitives'][0]['attributes']
    assert 'TEXCOORD_0' in attrs and 'COLOR_0' not in attrs and 'COLOR_1' not in attrs
    view=doc['bufferViews'][doc['images'][0]['bufferView']]
    start=28+size+view.get('byteOffset',0)
    with Image.open(io.BytesIO(blob[start:start+view['byteLength']])) as image:
        pixels=np.asarray(image.convert('RGB'))
    covered=pixels[:,:,0]>50
    assert covered.sum()>100
    np.testing.assert_allclose(np.median(pixels[covered],axis=0),[100,70,40],atol=3)
