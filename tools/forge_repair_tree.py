"""Replace the failed u2net tree segmentation with a complete alpha cutout."""
from forge_rebuild import ROOT,OUT,FORGE,request,upload,atomic
import json
path=OUT/'plan.json';plan=json.loads(path.read_text());e=next(x for x in plan['assets'] if x['key']=='tree_pine')
assert e['reference']!='concepts_docs/art/forge_references/tree_cutout.png','Tree repair is already queued.'
e['reference']='concepts_docs/art/forge_references/tree_cutout.png';aid=e['forge_asset_id']
ref=upload('/assets/'+aid+'/references',ROOT/e['reference'],{'role':'primary'})
prepared=request('/assets/'+aid+'/prepare',{'reference_id':ref['id'],'remove_background':False,'role':'primary'})
e['prepared_reference']=str(FORGE/'data/assets'/aid/prepared['path']);e['previous_generation_job']=e['generation_job']
job=request('/assets/'+aid+'/jobs',{'operation':'generate','options':{'backend':'triposr'},'reason':'Opened Godot three-view renders and the saved foreground: u2net removed the whole canopy. Supplied complete transparent tree reference to bypass background segmentation.'})
e.update(generation_job=job['id'],status='queued');e.pop('generated_source',None)
report=ROOT/'docs/forge_rebuild/tree_pine.json';report.rename(report.with_suffix('.missing_canopy.json'))
atomic(path,plan);print('Tree canopy reconstruction queued',job['id'],flush=True)
