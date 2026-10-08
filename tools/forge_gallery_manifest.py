from forge_rebuild import ROOT,OUT,atomic
import argparse,json
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('keys',nargs='+');p.add_argument('--raw',action='store_true');a=p.parse_args()
plan=json.loads((OUT/'plan.json').read_text());assets=[]
for key in a.keys:
 e=next(e for e in plan['assets'] if e['key']==key)
 target=ROOT/e['target']
 if a.raw:
  import shutil
  target=ROOT/'game/assets/forge_rebuild/raw'/f'{key}.glb';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(e['generated_source'],target)
 assets.append({'name':e['name'],'path':'res://'+target.relative_to(ROOT/'game').as_posix()})
atomic(ROOT/'docs/forge_rebuild'/f'{a.name}.json',{'assets':assets,'output':str(ROOT/'docs/forge_rebuild'/f'{a.name}.png')})
