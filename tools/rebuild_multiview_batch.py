"""Serial GPU queue for the inspected whole-game reference catalog.

Jobs go through Asset Forge's ordinary provenance and candidate budget gates.
Run again to resume; existing successful jobs are not regenerated.
"""
import argparse, json, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8743')
    parser.add_argument('--keys',nargs='*')
    parser.add_argument('--report',default='generation_queue.json')
    args=parser.parse_args()
    report=ROOT/'docs/full_asset_rebuild'/args.report
    report.parent.mkdir(parents=True,exist_ok=True)
    state=json.loads(report.read_text()) if report.exists() else {}
    def api(route,data=None,method=None):
        req=urllib.request.Request(args.url+'/api'+route,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'X-Forge-Request':'1','Content-Type':'application/json'},
            method=method or ('POST' if data is not None else 'GET'))
        with urllib.request.urlopen(req,timeout=90) as response:return json.load(response)
    def save():report.write_text(json.dumps(state,indent=2)+'\n')
    catalog=json.loads((ROOT/'concepts_docs/art/asset_turnarounds_v2/catalog.json').read_text())
    for entry in catalog['assets']:
        key=entry['key']
        if args.keys and key not in args.keys:continue
        asset=api('/assets/'+entry['forge_asset_id'])
        info=state.setdefault(key,{'asset_id':asset['id']})
        if info.get('state')=='succeeded':continue
        settings={**asset['settings'],'multiview_mode':'stochastic','trellis_steps':25,
                  'project_reference_colors':False}
        if not info.get('job_id'):
            api('/assets/'+asset['id']+'/settings',settings,'PUT')
            job=api('/assets/'+asset['id']+'/jobs',{'operation':'generate',
                'options':{'backend':'trellis','reference_set_id':entry['reference_set_id']},
                'reason':'User authorized replacing every game asset from inspected multi-angle concept translations.'})
            info['job_id']=job['id'];save()
        while True:
            job=next(j for j in api('/jobs') if j['id']==info['job_id'])
            info.update(state=job['state'],stage=job.get('stage'),message=job.get('message'))
            save()
            if job['state'] not in ('queued','running'):break
            print(key,job['state'],job.get('stage'),flush=True)
            time.sleep(20)
        print(key,job['state'],job.get('message'),flush=True)
        if job['state']!='succeeded':continue
        asset=api('/assets/'+asset['id'])
        candidate=next(c for c in asset['candidates'] if c['id']==asset['selected_candidate'])
        info['source']=str(Path('C:/Users/Tom/Documents/2D_to_3D/data/assets')/asset['id']/candidate['path'])
        save()

if __name__=='__main__':main()
