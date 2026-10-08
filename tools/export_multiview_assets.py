"""Build the final runtime catalogue solely from new, reviewed editable scenes."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--asset');parser.add_argument('--inventory-only',action='store_true');args=parser.parse_args()
out=ROOT/'game/assets/generated';authoring=ROOT/'blender/multiview_rebuild'
manifest=authoring/'export_manifest.json'
# Keep declared targets even if an export was deleted. A rebuild must be able
# to recreate it from its retained source rather than shrinking the catalogue.
declared=json.loads(manifest.read_text(encoding='utf-8'))['models'] if manifest.exists() else []
models_by_target={record['target']:record for record in declared}
for target in sorted(out.rglob('*.glb')):
    relative=target.relative_to(out);key=target.stem
    if len(relative.parts)==1:
        if key not in ['warrior','bay_horse']:continue
        source=authoring/'rigged'/f'{key}.blend'
    else:
        source=authoring/'variants'/relative.parent/f'{key}.blend'
        if not source.exists():source=authoring/'equipment'/f'{key}.blend'
    if not source.exists():raise ValueError('Missing editable final model: '+str(target))
    record={'key':key,'source':source.relative_to(ROOT).as_posix(),'target':target.relative_to(ROOT).as_posix()}
    models_by_target[record['target']]=record
models=[models_by_target[target] for target in sorted(models_by_target)]
for record in models:
    source=(ROOT/record['source']).resolve();target=(ROOT/record['target']).resolve()
    source.relative_to(authoring.resolve());target.relative_to(out.resolve())
    if not source.exists():raise ValueError('Missing current editable source: '+str(source))
manifest.write_text(json.dumps({'schema':1,'models':models},indent=2),encoding='utf-8')
selected=[record for record in models if not args.asset or record['key']==args.asset]
if args.asset and not selected:raise ValueError('Unknown new asset '+args.asset)
if not args.inventory_only:
    request=ROOT/'.local/full_asset_rebuild/export.json';request.parent.mkdir(parents=True,exist_ok=True);request.write_text(json.dumps({'models':selected}))
    subprocess.run(['C:/Program Files/Blender Foundation/Blender 5.2/blender.exe','--background','--threads','6',
        '--python-exit-code','1','--python',str(ROOT/'blender/scripts/export_multiview_runtime.py'),'--',str(request)],check=True)
print('NEW_CATALOGUE',len(models),'models')
