"""Export shaded, colored glTF with explicit physical base material for Godot."""
import json
import struct
from pathlib import Path


def export_mesh(mesh, path):
    payload = mesh.export(file_type='glb', include_normals=True)
    json_size = struct.unpack_from('<I',payload,12)[0]
    data = json.loads(payload[20:20+json_size])
    # ColorVisuals exports COLOR_0 but no material. Godot's implicit default
    # material does not enable vertex-color albedo; specify one explicitly.
    # Godot 4.7 no longer enables color albedo by default on imported materials.
    # Its documented -vcol import hint survives the GLB and enables both flags.
    data['materials'] = [{'name':'Native base color-vcol', 'doubleSided':False,
        'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1], 'metallicFactor':0,
                              'roughnessFactor':0.95}}]
    for entry in data['meshes']:
        for primitive in entry['primitives']:
            primitive['material'] = 0
    chunk = json.dumps(data,separators=(',',':')).encode('utf-8')
    chunk += b' '*((-len(chunk))%4)
    remainder = payload[20+json_size:]
    header = struct.pack('<III',0x46546c67,2,20+len(chunk)+len(remainder))
    Path(path).write_bytes(header+struct.pack('<II',len(chunk),0x4e4f534a)+chunk+remainder)
