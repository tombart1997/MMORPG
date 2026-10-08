import json,struct
import numpy as np
import pytest
from forge.glb_cleanup import remove_degenerate_triangles
from forge.validation import read_glb,accessor,validate_glb
from forge.store import digest
from test_contracts import triangle_glb

def test_cleanup_preserves_vertices_materials_and_original_binary(tmp_path):
    source=triangle_glb(tmp_path/'source.glb');doc,binary=read_glb(source)
    ids=np.array([0,1,2,0,0,1],dtype='<u4').tobytes()
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(ids)})
    doc['accessors'].append({'bufferView':2,'componentType':5125,'count':6,'type':'SCALAR'})
    doc['meshes'][0]['primitives'][0]['indices']=2
    doc['materials']=[{'name':'Original','pbrMetallicRoughness':{'roughnessFactor':.82}}]
    binary+=ids;doc['buffers'][0]['byteLength']=len(binary)
    text=json.dumps(doc).encode();text+=b' '*((-len(text))%4)
    content=struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary
    source.write_bytes(struct.pack('<4sII',b'glTF',2,len(content)+12)+content)
    sha=digest(source);dest=tmp_path/'clean.glb'
    assert validate_glb(source)['technical_status']=='failed'
    report=remove_degenerate_triangles(source,dest);after,new_binary=read_glb(dest)
    assert digest(source)==sha and new_binary[:len(binary)]==binary
    assert after['materials']==doc['materials'] and after['nodes']==doc['nodes']
    assert np.array_equal(accessor(after,new_binary,after['meshes'][0]['primitives'][0]['indices']).ravel(),[0,1,2])
    assert report['changes'][0]['removed_zero_area_triangles']==1
    assert report['validation']['technical_status']=='passed'
    with pytest.raises(ValueError,match='original source'):remove_degenerate_triangles(source,source)

def test_wholly_degenerate_primitive_is_not_silently_removed(tmp_path):
    source=triangle_glb(tmp_path/'source.glb',degenerate=True)
    with pytest.raises(ValueError,match='entire primitive'):remove_degenerate_triangles(source,tmp_path/'bad.glb')
    assert not (tmp_path/'bad.glb').exists()
