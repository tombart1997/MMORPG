"""Save inspected prototype limitations against the exact runtime hash."""
import json
from pathlib import Path
import shutil
import httpx

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
aid='9bd5513739b9';asset_root=FORGE/'data/assets'/aid
evidence=asset_root/'reviews/multiview_followup';evidence.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'.local/multiview_benchmarks/validation/results/boar_corrected_runtime.png',evidence/'four_angles.png')
with httpx.Client(base_url='http://127.0.0.1:8743/api',headers={'X-Forge-Request':'1'},timeout=30) as client:
    asset=client.get('/assets/'+aid).json()
    diagnosis={'status':'PARTIAL REBUILD','source_sha256':asset['artifacts']['runtime_sha256'],
        'criteria':['Stocky boar silhouette; paired tusks; four separated legs; dorsal reeds; neutral ground contact',
            'Preserve concept colors at runtime budget; verify exported materials in Godot',
            'Species rig and required gait/combat clips before production creature mapping'],
        'confidence':'High for technical export and static silhouette; moderate for fine anatomy/material fidelity; animation unverified',
        'evidence':[{'kind':'mesh','path':'processed/595d28bcc72d/processing.json'},
            {'kind':'render','path':'reviews/multiview_followup/four_angles.png'},
            {'kind':'runtime','path':'godot/10c1eef84a8e/results/technical.json'},
            {'kind':'reference','path':asset['references'][0]['path']}],
        'defects':[{'region':'head','description':'Eye and muzzle detail remain soft; reference color registration is approximate.'},
            {'region':'body','description':'Some fine armor plates and spike/underbody details need local geometry/material cleanup.'},
            {'region':'rig','description':'Static candidate has no species skeleton or idle/run/attack/hit/death clips.'}],
        'plan':[],
        'remaining_review':['Author species rig and deformation loops; validate all required animations.',
            'Inspect eye registration, plate coverage and spike tips at normal game distance.',
            'Profile skinning and animated combat before production replacement.'],
        'future_work':['Keep the successful silhouette and atlas; repair specific defects instead of increasing generation resolution blindly.']}
    result=client.put('/assets/'+aid+'/diagnosis',json=diagnosis);result.raise_for_status()
    (ROOT/'docs/multiview_pipeline/evidence/boar_diagnosis.json').write_text(json.dumps(diagnosis,indent=2),encoding='utf-8')
    print(result.json()['reviewflow']['status'])
