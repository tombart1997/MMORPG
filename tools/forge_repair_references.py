from forge_rebuild import ROOT,OUT,request,upload,atomic
import json
from PIL import Image
path=OUT/'plan.json';plan=json.loads(path.read_text())
fix={'mob_road_bandit':.395,'mob_hollow_raider':.395,'mob_exile_captain':.38,'mob_cairn_sentinel':.46,'mob_rift_sentinel':.46,'mob_ancient_warden':.41}
for e in plan['assets']:
 if e['key'] not in fix:continue
 aid=e['forge_asset_id'];source=ROOT/e['reference'];ref=upload('/assets/'+aid+'/references',source,{'role':'primary'})
 l,t,r,b=e['rect'];t=fix[e['key']]
 with Image.open(source) as im:w,h=im.size
 prepared=request('/assets/'+aid+'/prepare',{'reference_id':ref['id'],'crop':[int(l*w),int(t*h),int((r-l)*w),int((1-t)*h)],'remove_background':False,'role':'primary'})
 e['previous_generation_job']=e['generation_job'];e['rect']=[l,t,r,1]
 e['prepared_reference']=str(__import__('pathlib').Path(r'C:\Users\Tom\Documents\2D_to_3D\data\assets')/aid/prepared['path'])
 job=request('/assets/'+aid+'/jobs',{'operation':'generate','options':{'backend':'triposr'},'reason':'Opened Godot front/side/three-quarter renders. The lower-row crop cut off the head/hood/antlers. Corrected full-height primary crop; final third generation attempt.'})
 e['generation_job']=job['id'];e['status']='queued';e.pop('generated_source',None)
 report=ROOT/'docs/forge_rebuild'/f"{e['key']}.json"
 if report.exists():report.rename(report.with_suffix('.superseded.json'))
 atomic(path,plan);print('Head crop repaired',e['key'],flush=True)
