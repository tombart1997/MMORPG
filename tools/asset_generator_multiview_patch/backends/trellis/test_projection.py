"""Actual Blender/glTF regression: angle labels use Y-up, even after import."""
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
from export_glb import export_mesh


def test_projection_respects_gltf_axes_and_keeps_unseen_native_color(tmp_path):
    mesh=trimesh.creation.box(extents=[1,2,3])
    vertices,faces=trimesh.remesh.subdivide(mesh.vertices,mesh.faces)
    mesh=trimesh.Trimesh(vertices,faces)
    mesh.visual.vertex_colors=np.tile([100,70,40,255],(len(vertices),1))
    source=tmp_path/'source.glb';export_mesh(mesh,source)
    views=[]
    for angle,color in [('front',(255,0,0,255)),('left',(0,0,255,255))]:
        mask=tmp_path/(angle+'.png');Image.new('RGBA',(32,32),color).save(mask)
        views.append({'angle':angle,'mask':str(mask)})
    output=tmp_path/'projected.glb'
    request=tmp_path/'request.json'
    request.write_text(json.dumps({'source':str(source),'output':str(output),'views':views,'report':str(tmp_path/'report.json')}))
    script=Path(__file__).resolve().parents[2]/'blender/project_reference_colors.py'
    result=subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','--background','--threads','2',
        '--python-exit-code','1','--python',str(script),'--',str(request)],capture_output=True,text=True,timeout=120)
    assert result.returncode==0,result.stdout[-4000:]+result.stderr[-4000:]
    projected=trimesh.load(output,force='mesh')
    np.testing.assert_allclose(projected.bounds,mesh.bounds,atol=1e-6)
    # Read accessors directly: trimesh drops COLOR_0 when a PBR material exists.
    import struct
    blob=output.read_bytes();size=struct.unpack_from('<I',blob,12)[0]
    doc=json.loads(blob[20:20+size]);attributes=doc['meshes'][0]['primitives'][0]['attributes']
    assert 'COLOR_0' in attributes and 'COLOR_1' not in attributes
    def accessor(name):
        a=doc['accessors'][attributes[name]];view=doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5123:'<u2',5121:'u1'}[a['componentType']])
        dims={'VEC3':3,'VEC4':4}[a['type']]
        values=np.ndarray((a['count'],dims),dtype=dtype,buffer=blob,
            offset=28+size+view.get('byteOffset',0)+a.get('byteOffset',0),
            strides=(view.get('byteStride',dtype.itemsize*dims),dtype.itemsize)).astype(float)
        if a.get('normalized'):values/=np.iinfo(dtype).max
        return values
    points=accessor('POSITION');rgba=accessor('COLOR_0')[:,:3]*255
    def sample(point):
        index=np.argmin(np.linalg.norm(points-np.array(point),axis=1))
        return rgba[index]
    # Front center must be red; unobserved top remains native brown. This
    # fails when projecting in Blender's imported Z-up local coordinates.
    np.testing.assert_allclose(sample([0,0,-1.5]),[255,0,0],atol=2)
    np.testing.assert_allclose(sample([0,1,0]),[100,70,40],atol=2)
