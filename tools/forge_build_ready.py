"""Resume Blender finishing as neural reconstruction candidates become available."""
from forge_rebuild import ROOT,OUT,request,atomic
import argparse,json,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');a=p.parse_args()
while True:
 plan=json.loads((OUT/'plan.json').read_text());jobs={j['id']:j for j in request('/jobs')};ready=[]
 for e in plan['assets']:
  job=jobs.get(e.get('generation_job'),{})
  if job.get('state')=='succeeded' and not (ROOT/'docs/forge_rebuild'/f"{e['key']}.json").exists():
   asset=request('/assets/'+e['forge_asset_id']);candidate=next(c for c in asset['candidates'] if c['id']==asset['selected_candidate'])
   ready.append(e['key'])
 if ready:
  # Refresh persisted candidate paths in one bounded sequential operation.
  subprocess.run(['py','-3.12',str(ROOT/'tools/forge_rebuild.py'),'status'],cwd=ROOT,check=True)
  log=ROOT/'docs/forge_rebuild'/f'build_{int(time.time())}.log'
  with log.open('w',encoding='utf-8') as output:
   result=subprocess.run(['blender','--background','--factory-startup','--threads','4','--python-exit-code','1','--python',str(ROOT/'blender/scripts/forge_bind_export.py'),'--',*ready],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
  print('Finished batch',ready,'exit',result.returncode,'log',log.name,flush=True)
  if result.returncode:break
 pending=[e for e in plan['assets'] if jobs.get(e.get('generation_job'),{}).get('state') in ['running','queued']]
 if not a.watch or not pending:break
 time.sleep(15)
