"""Prepare completed serial generations without publishing unreviewed meshes."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('keys',nargs='+');parser.add_argument('--budget',type=int);parser.add_argument('--mode',choices=['simplify','balanced','retopology'],default='simplify');parser.add_argument('--surface-error',type=float,default=.025);args=parser.parse_args()
queue={}
for file in (ROOT/'docs/full_asset_rebuild').glob('*generation_queue.json'):
    queue.update(json.loads(file.read_text()))
assets=[]
for key in args.keys:
    record=queue[key]
    if record['state']!='succeeded':raise ValueError(key+' has not completed generation')
    assets.append({'key':key,'source':record['source'],'budget':args.budget or (24000 if key in ['warrior','bandit','blacksmith','keeper','stablemaster'] else 8000 if key in ['pine','house','watchtower','rock','dead_tree','shrub','grass','fern'] else 18000),'texture_size':2048 if key in ['warrior','bandit','blacksmith','keeper','stablemaster'] else 1024,'mode':args.mode,'surface_error':args.surface_error})
request=ROOT/'.local/full_asset_rebuild'/('prepare_'+'_'.join(args.keys)+'.json');request.parent.mkdir(parents=True,exist_ok=True)
request.write_text(json.dumps({'assets':assets}))
subprocess.run(['C:/Program Files/Blender Foundation/Blender 5.2/blender.exe','--background',
    '--threads','6','--python-exit-code','1','--python',str(ROOT/'blender/scripts/prepare_multiview_mesh.py'),
    '--',str(request)],check=True)
