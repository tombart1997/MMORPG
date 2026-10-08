from forge_rebuild import ROOT,OUT,atomic
import json,subprocess,argparse
p=argparse.ArgumentParser();p.add_argument('--only',nargs='*');p.add_argument('--clip',default='idle');p.add_argument('--legacy',action='store_true');p.add_argument('--residents',action='store_true');a=p.parse_args()
plan=json.loads((OUT/'plan.json').read_text());entries=[e for e in plan['assets'] if not a.only or e['key'] in a.only]
prefix='gallery'
if a.legacy:
 prefix='legacy';direct={e['target'] for e in entries}
 entries=[{'key':str(x['path']),'target':x['path'],'name':__import__('pathlib').Path(x['path']).stem.replace('_',' ').title()} for x in json.loads((ROOT/'docs/forge_rebuild/original_model_inventory.json').read_text())['models'] if x['path'] not in direct]
elif a.residents:
 prefix='residents';entries=[{'key':x.stem,'target':x.relative_to(ROOT).as_posix(),'name':x.stem.title()} for x in sorted((ROOT/'game/assets/forge_rebuild/npcs').glob('*.glb'))]
for offset in range(0,len(entries),3):
 group=entries[offset:offset+3];name=f'{prefix}_{a.clip}_{offset//3:02d}'
 manifest=ROOT/'docs/forge_rebuild'/f'{name}.json'
 assets=[{'name':e['name'],'path':'res://'+(ROOT/e['target']).relative_to(ROOT/'game').as_posix()} for e in group]
 atomic(manifest,{'assets':assets,'output':str(manifest.with_suffix('.png')),'clip':a.clip,'time':.25 if a.clip!='idle' else 0})
 with (ROOT/'docs/forge_rebuild'/f'{name}.log').open('w',encoding='utf-8') as log:
  r=subprocess.run(['Godot_console.exe','--path',str(ROOT/'game'),'--rendering-method','gl_compatibility','--script','res://tests/forge_asset_gallery.gd','--',str(manifest)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=90)
 if r.returncode:raise RuntimeError(name+' render failed')
 print('Rendered',name,[e['key'] for e in group],flush=True)
