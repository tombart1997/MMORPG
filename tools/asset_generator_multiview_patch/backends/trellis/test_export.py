"""Regression for shaded vertex colors surviving a real glTF export."""
import json
import struct
import numpy as np
import trimesh
from export_glb import export_mesh


def test_export_is_shaded_colored_and_godot_import_hint_is_explicit(tmp_path):
    mesh=trimesh.creation.icosphere(subdivisions=1)
    mesh.visual.vertex_colors=np.tile([100,70,40,255],(len(mesh.vertices),1))
    path=tmp_path/'colored.glb';export_mesh(mesh,path)
    blob=path.read_bytes()
    assert struct.unpack_from('<I',blob,8)[0]==len(blob)
    size=struct.unpack_from('<I',blob,12)[0]
    doc=json.loads(blob[20:20+size])
    primitive=doc['meshes'][0]['primitives'][0]
    assert {'POSITION','NORMAL','COLOR_0'}<=primitive['attributes'].keys()
    assert 'COLOR_1' not in primitive['attributes']
    material=doc['materials'][primitive['material']]
    assert material['name'].endswith('-vcol')
    assert material['pbrMetallicRoughness']['metallicFactor']==0
    loaded=trimesh.load(path,force='mesh')
    np.testing.assert_allclose(loaded.bounds,mesh.bounds,atol=1e-6)
