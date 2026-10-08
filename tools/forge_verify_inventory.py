"""Audit every replaced legacy GLB and reconstructed catalogue entry."""
from forge_rebuild import ROOT,glb_info,atomic
from pathlib import Path
import json,hashlib,struct,math

def validate_binary(path):
 raw=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
 assert magic==b'glTF' and version==2 and length==len(raw),(path,'invalid GLB header')
 n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);offset=20+n
 size,kind=struct.unpack_from('<II',raw,offset);blob=raw[offset+8:offset+8+size]
 assert kind==0x004e4942 and doc.get('meshes'),(path,'missing geometry')
 vertices=0
 for mesh in doc['meshes']:
  for primitive in mesh['primitives']:
   for semantic in ['POSITION','NORMAL','WEIGHTS_0']:
    if semantic not in primitive['attributes']:continue
    a=doc['accessors'][primitive['attributes'][semantic]];view=doc['bufferViews'][a['bufferView']]
    assert a['componentType']==5126,(path,semantic,'unexpected component type')
    width={'VEC3':3,'VEC4':4}[a['type']];stride=view.get('byteStride',width*4)
    start=view.get('byteOffset',0)+a.get('byteOffset',0)
    for i in range(a['count']):
     values=struct.unpack_from('<'+'f'*width,blob,start+i*stride)
     assert all(math.isfinite(v) for v in values),(path,semantic,'non-finite data')
     if semantic=='WEIGHTS_0':assert abs(sum(values)-1)<.002,(path,'unnormalized skin weights')
    if semantic=='POSITION':vertices+=a['count']
   assert 'material' in primitive,(path,'missing material')
 assert doc.get('images'),(path,'missing reconstructed texture')
 return vertices

inventory=json.loads((ROOT/'docs/forge_rebuild/original_model_inventory.json').read_text())['models']
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())
lineage=json.loads((ROOT/'docs/forge_rebuild/derived_lineage.json').read_text())
sources={x['target']:x['key'] for x in plan['assets']};sources.update({x['target']:x['reconstruction'] for x in lineage})
rows=[]
for old in inventory:
 target=old['path'];p=ROOT/target;baseline=ROOT/'.local/forge_rebuild/baseline'/target
 info=glb_info(p);assert p.read_bytes()!=baseline.read_bytes(),(target,'unchanged legacy model')
 assert target in sources,(target,'missing lineage')
 assert info['bones']==old['bones'],(target,'changed rig bones',info['bones'],old['bones'])
 assert set(info['clips'])==set(old['clips']),(target,'changed animation clips',info['clips'],old['clips'])
 assert info['skins']==old['skins'],(target,'changed skin count')
 rows.append(dict(info,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),reconstruction=sources[target],verified_vertices=validate_binary(p)))
for e in plan['assets']:
 assert e['status']=='succeeded' and Path(e['generated_source']).is_file(),(e['key'],'missing neural candidate')
 info=glb_info(ROOT/e['target']);validate_binary(ROOT/e['target'])
 if e['category']=='mob':assert set(['idle','run','attack_01','hit','death'])<=set(info['clips']),(e['key'],'missing creature animation')
for record in lineage:
 if '/npcs/' in record['target']:validate_binary(ROOT/record['target'])
atomic(ROOT/'docs/forge_rebuild/inventory_validation.json',{'legacy_models_replaced':len(rows),'neural_candidates':len(plan['assets']),'mob_variants':sum(e['category']=='mob' for e in plan['assets']),'resident_variants':len(list((ROOT/'game/assets/forge_rebuild/npcs').glob('*.glb'))),'all_bone_and_animation_contracts_preserved':True,'all_mesh_buffers_finite_and_weights_normalized':True,'models':rows})
print('Inventory validation passed:',len(rows),'legacy replacements;',len(plan['assets']),'neural candidates.')
