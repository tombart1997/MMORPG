"""Cancel only this rebuild's unstarted jobs; resubmit with suitable source density.

128 geometry extraction precedes 14k crowd exports; 1024 atlases preserve the
backend's 512 conditioning without spending minutes packing 300k triangles.
"""
from forge_rebuild import ROOT,OUT,request,atomic
import json,time
path=OUT/'plan.json';plan=json.loads(path.read_text());jobs={j['id']:j for j in request('/jobs')};cancelled=[]
for e in plan['assets']:
 j=jobs.get(e.get('generation_job'),{})
 if j.get('state')=='queued':
  request('/jobs/'+j['id']+'/cancel',{});e['cancelled_generation_job']=j['id'];cancelled.append(e)
atomic(path,plan)
print('Cancelled unstarted oversized jobs:',len(cancelled),flush=True)
while any(j['id'] in {e['cancelled_generation_job'] for e in cancelled} and j['state']=='queued' for j in request('/jobs')):time.sleep(3)
for e in cancelled:
 asset=request('/assets/'+e['forge_asset_id']);settings=asset['settings'];settings.update(mc_resolution=128,texture_resolution=1024)
 request('/assets/'+e['forge_asset_id']+'/settings',settings,'PUT')
 job=request('/assets/'+e['forge_asset_id']+'/jobs',{'operation':'generate','options':{'backend':e['backend']},'reason':'Unstarted first job cancelled. Use 128 extraction and 1024 atlas for 14k crowd models; 512 conditioning limits useful image detail. Dense 297k meshes took four minutes to UV-pack without improving runtime geometry.'})
 e['generation_job']=job['id'];e['status']='queued';atomic(path,plan);print('Resubmitted',e['key'],flush=True)
