"""Render actual Godot imports at four angles, clay, wire and clip samples."""
import argparse,json,shutil,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
GODOT='C:/Program Files/Godot/Godot_console.exe'
parser=argparse.ArgumentParser();parser.add_argument('keys',nargs='+');parser.add_argument('--runtime',action='store_true');parser.add_argument('--native',action='store_true');parser.add_argument('--group');args=parser.parse_args()
project=ROOT/'.local/full_asset_rebuild/validation';(project/'assets').mkdir(parents=True,exist_ok=True)
(project/'project.godot').write_text('[application]\nconfig/name="Full asset review"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n')
shutil.copy2(FORGE/'godot_validation/evidence.gd',project/'evidence.gd')
shutil.copy2(ROOT/'game/scripts/visuals/generated_asset_import.gd',project/'generated_asset_import.gd')
catalog={e['key']:e for e in json.loads((ROOT/'concepts_docs/art/asset_turnarounds_v2/catalog.json').read_text())['assets']}
assets=[]
queue={}
for file in (ROOT/'docs/full_asset_rebuild').glob('*generation_queue.json'):queue.update(json.loads(file.read_text()))
for key in args.keys:
    source=ROOT/('game/assets/generated/'+key+'.glb' if args.runtime else 'game/review_assets/full_rebuild/'+key+'/runtime.glb')
    if args.runtime and args.group:source=ROOT/'game/assets/generated'/args.group/f'{key}.glb'
    if args.runtime and not source.exists():
        for group in ['weapons','world','mobs','npcs','equipment']:
            candidate=ROOT/'game/assets/generated'/group/f'{key}.glb'
            if candidate.exists():source=candidate;break
    if args.native:source=Path(queue[key]['source'])
    shutil.copy2(source,project/'assets'/f'{key}.glb')
    entry=catalog.get(key,{})
    if not entry and source.parent.name=='weapons':entry=catalog['jade']
    if not entry:
        lineage=ROOT/'docs/full_asset_rebuild/variant_lineage.json'
        for r in json.loads(lineage.read_text()) if lineage.exists() else []:
            if r['key']==key and r['group']==source.parent.name:entry=catalog.get(r['base'],{})
    reference=str(ROOT/entry['sheet']) if entry else str(ROOT/'concepts_docs/art/world_briarwood.png')
    assets.append({'key':key,'path':f'res://assets/{key}.glb','reference':reference,
        'output':str(ROOT/'docs/full_asset_rebuild/evidence'/(key+('_native' if args.native else '_runtime' if args.runtime else '_prepared')+'.png'))})
    if args.runtime and (source.parent.name=='weapons' or key in ['gold_coin','leaf_litter']):assets[-1]['inspection_rotation']=[math.pi/2,0,0]
request=project/'request.json';request.write_text(json.dumps({'assets':assets,'report':str(ROOT/'docs/full_asset_rebuild/evidence/render_report.json')}))
(ROOT/'docs/full_asset_rebuild/evidence').mkdir(parents=True,exist_ok=True)
subprocess.run([GODOT,'--headless','--path',str(project),'--editor','--import','--quit'],check=True,stdout=subprocess.DEVNULL)
from configure_generated_imports import configure
if configure(project/'assets','res://generated_asset_import.gd'):
    subprocess.run([GODOT,'--headless','--path',str(project),'--editor','--import','--quit'],check=True,stdout=subprocess.DEVNULL)
subprocess.run([GODOT,'--path',str(project),'--rendering-method','gl_compatibility','--script','res://evidence.gd','--',str(request)],check=True)
