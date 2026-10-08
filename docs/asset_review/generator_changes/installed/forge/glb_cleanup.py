"""Lossless retained-source cleanup of zero-area GLB triangles.

Only index lists change. Vertex arrays, UVs, weights, materials, textures,
animation channels and the entire original binary payload remain byte-identical.
This is a technical preflight, not anatomy repair or retopology.
"""
import copy,json,struct
from pathlib import Path
import numpy as np
from .validation import read_glb,accessor,validate_glb
from .store import digest

def remove_degenerate_triangles(source,destination):
    source,destination=Path(source),Path(destination)
    if source.resolve()==destination.resolve():raise ValueError('Preserve the original source; use a new destination')
    doc,binary=read_glb(source);original=copy.deepcopy(doc);payload=bytearray(binary);removed=[]
    for mesh in doc.get('meshes',[]):
        for primitive in mesh['primitives']:
            if primitive.get('mode',4)!=4:continue
            pos=accessor(original,binary,primitive['attributes']['POSITION'])
            ids=accessor(original,binary,primitive['indices']).reshape(-1) if 'indices' in primitive else np.arange(len(pos),dtype=np.uint32)
            faces=ids.reshape(-1,3);tri=pos[faces]
            keep=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>=1e-12
            count=int(np.count_nonzero(~keep))
            if not count:continue
            new=faces[keep].reshape(-1).astype('<u4')
            if not len(new):raise ValueError('Cleanup would remove an entire primitive')
            payload.extend(b'\0'*((-len(payload))%4));offset=len(payload);payload.extend(new.tobytes())
            view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':new.nbytes,'target':34963})
            idx=len(doc['accessors']);doc['accessors'].append({'bufferView':view,'componentType':5125,'count':len(new),'type':'SCALAR','min':[int(new.min())],'max':[int(new.max())]})
            primitive['indices']=idx;removed.append({'mesh':mesh.get('name'),'removed_zero_area_triangles':count})
    doc['buffers'][0]['byteLength']=len(payload)
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);payload.extend(b'\0'*((-len(payload))%4))
    blob=struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(payload))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(payload),0x004e4942)+payload
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(blob)
    validation=validate_glb(destination)
    if validation['technical_status']!='passed':raise ValueError('Remaining defects: '+str(validation['errors']))
    assert bytes(payload[:len(binary)])==binary
    return {'operation':'remove_degenerate_triangles','source_sha256':digest(source),'result_sha256':digest(destination),'changes':removed,'preserved_original_binary_prefix':True,'validation':validation}
