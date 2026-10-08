"""Create a separate candidate for corrected material projection."""
import json
from pathlib import Path
import httpx

FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
SOURCE=FORGE/'data/assets/9bd5513739b9/generated/2e7a500bfc46/projected_yup.glb'
with httpx.Client(base_url='http://127.0.0.1:8743/api',headers={'X-Forge-Request':'1'},timeout=120) as client:
    with SOURCE.open('rb') as stream:
        result=client.post('/assets/9bd5513739b9/import',files={'file':('boar_four_views_yup.glb',stream,'model/gltf-binary')},data={'license_note':'Derived from native four-view TRELLIS job 2e7a500bfc46, seed 42, 25 steps. Corrected Blender Z-up to glTF Y-up reference color projection; no geometry change. Source and original candidate retained. MIT model/code, Apache FlexiCubes; AI turnaround references.'})
    result.raise_for_status();print(json.dumps(result.json()))
    response=client.post('/assets/9bd5513739b9/jobs',json={'operation':'process','options':{},'reason':'Separate material correction candidate: project in glTF world axes, bake high-detail color to texture, then simplify within 18000 triangle budget.'})
    response.raise_for_status();print(json.dumps({'job':response.json()['id']}))
