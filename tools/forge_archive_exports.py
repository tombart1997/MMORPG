"""Keep fitted GLBs and editable sources beside their neural candidates in Forge."""
from forge_rebuild import ROOT,OUT,FORGE,upload,request,atomic
import json,hashlib
path=OUT/'plan.json';plan=json.loads(path.read_text());receipts=[]
def archive(e,p,note):
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 asset=request('/assets/'+e['forge_asset_id'])
 found=next((c for c in reversed(asset['candidates']) if c.get('origin')=='imported' and c.get('sha256')==digest and c.get('original_filename')==p.name),None)
 return found or upload('/assets/'+e['forge_asset_id']+'/import',p,{'license_note':note})
for e in plan['assets']:
 note='Final project export derived from local TripoSR candidate '+e['candidate_id']+'. Project concept reference; original runtime rig/actions preserved. Horse tack refitted. This is a fitted import, not a second neural generation. Automated project checks and agent visual inspection; no human acceptance asserted.'
 if not e.get('finalized_candidate_id'):
  blend=ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend"
  editable=archive(e,blend,note)
  runtime=archive(e,ROOT/e['target'],note)
  e.update(finalized_candidate_id=runtime['id'],editable_candidate_id=editable['id'],archived_generation_job=e['generation_job'])
  atomic(path,plan)
 receipts.append({'key':e['key'],'asset_id':e['forge_asset_id'],'neural_candidate':e['candidate_id'],'generation_job':e['generation_job'],'finalized_candidate':e['finalized_candidate_id'],'editable_candidate':e['editable_candidate_id'],'runtime':e['target'],'reference':e['reference'],'generated_source':e['generated_source'],'generation_metadata':json.loads((__import__('pathlib').Path(e['generated_source']).parent/'generation.json').read_text())})
 print('Archived final rigged export',e['key'],flush=True)
atomic(ROOT/'docs/forge_rebuild/forge_export_receipts.json',{'generator':str(FORGE),'backend':'Local TripoSR','assets':receipts,'visual_acceptance':'Agent inspected Godot renders. Forge human review remains pending.'})
