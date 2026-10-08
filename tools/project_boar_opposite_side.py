"""Targeted material correction: add inspected opposite side without new geometry."""
import json
from pathlib import Path
import urllib.request
from PIL import Image
from rembg import remove, new_session

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'concepts_docs/art/asset_turnarounds_v2'
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
GEN=FORGE/'data/assets/9bd5513739b9/generated/2e7a500bfc46'
catalog_path=ART/'catalog.json';catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
boar=next(a for a in catalog['assets'] if a['key']=='ironhide_boar')
right=next(v for v in boar['views'] if v['angle']=='right')
mask=GEN/'foreground_right_supplementary.png'
with Image.open(ROOT/right['path']) as im:
    remove(im.convert('RGB'),session=new_session('u2net')).save(mask)
request=json.loads((GEN/'projection_request.json').read_text())
request.update(output=str(GEN/'projected_all_sides.glb'),report=str(GEN/'reference_projection_all_sides.json'))
request['views'].append({'angle':'right','mask':str(mask)})
(GEN/'projection_all_sides_request.json').write_text(json.dumps(request,indent=2),encoding='utf-8')
def api(method,path,body=None):
    req=urllib.request.Request('http://127.0.0.1:8743/api'+path,data=json.dumps(body).encode() if body is not None else None,
        headers={'X-Forge-Request':'1','Content-Type':'application/json'},method=method)
    with urllib.request.urlopen(req,timeout=90) as response:return json.load(response)

if True:
    asset=api('GET','/assets/9bd5513739b9')
    original=next(s for s in asset['reference_sets'] if s['id']=='b78ccb97e84d')
    record=api('POST','/assets/9bd5513739b9/reference-sets',{
        'name':'Neutral views with opposite flank','source_reference_id':original['source_reference_id'],
        'pose':original['pose'],'scale_notes':original['scale_notes'],
        'views':[{'angle':v['angle'],'reference_id':v['reference_id']} for v in original['views']]+[{'angle':'right','reference_id':right['reference_id']}]})
    notes=boar['review_notes']+' Opened opposite-side crop; the same four legs, tusks, dorsal reeds and stocky proportions agree. Include right flank for color coverage; overhead remains supplementary.'
    api('PUT','/assets/9bd5513739b9/reference-sets/'+record['id']+'/review',{'approved':True,'notes':notes})
    boar.update(reference_set_id=record['id'],review_notes=notes)
    right['used']=True
    catalog_path.write_text(json.dumps(catalog,indent=2),encoding='utf-8')
    provenance={'geometry_job':'2e7a500bfc46','geometry_input_set':'b78ccb97e84d','geometry_inputs':4,
        'material_input_set':record['id'],'supplementary_right_reference':right,
        'mesh_changed':False,'note':'Right image repairs color coverage only in this candidate. Future generation from the five-view set consumes all five images.'}
    (GEN/'all_sides_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
print(json.dumps({'reference_set':record['id'],'request':str(GEN/'projection_all_sides_request.json')}))
