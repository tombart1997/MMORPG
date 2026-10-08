"""Normalize only invalid zero-area faces; retain every original fallback."""
from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[1];FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
sys.path.insert(0,str(FORGE))
from forge.glb_cleanup import remove_degenerate_triangles
from forge.store import atomic_json,digest
rows=json.loads((ROOT/'docs/asset_review/fallback_inventory.json').read_text())['assets'];done={};receipts=[]
for row in rows:
    if row['key'] not in ('hero_ironvow','horse_bay','mob_road_bandit','mob_hollow_raider','mob_ash_bandit','mob_exile_captain'):continue
    old=row['fallback_path']
    if old not in done:
        source=ROOT/'game'/old[6:];dest=source.with_stem(source.stem+'_clean');start=time.monotonic()
        receipt=remove_degenerate_triangles(source,dest);receipt['elapsed_seconds']=round(time.monotonic()-start,3);receipt['cost_credits']=0
        receipt.update(source=str(source),result=str(dest));receipts.append(receipt)
        done[old]={'fallback_path':'res://'+dest.relative_to(ROOT/'game').as_posix(),'fallback_sha256':digest(dest),'uncleaned_fallback_path':old,'uncleaned_fallback_sha256':row['fallback_sha256']}
    row.update(done[old])
atomic_json(ROOT/'docs/asset_review/fallback_inventory.json',{'assets':rows})
atomic_json(ROOT/'docs/asset_review/fallback_cleanup.json',{'receipts':receipts})
reqpath=ROOT/'docs/asset_review/fallback_render_request.json';req=json.loads(reqpath.read_text())
for entry in req['assets']:
    row=next(x for x in rows if x['key']==entry['key'])
    entry['path']=row['fallback_path']
req['assets']=[x for x in req['assets'] if x['key'] in ['horse_bay','mob_road_bandit']]
req['report']=str(ROOT/'docs/asset_review/fallback_clean_render_report.json')
atomic_json(ROOT/'docs/asset_review/fallback_clean_render_request.json',req)
print('Removed only zero-area triangles:',[(r['changes'],r['elapsed_seconds']) for r in receipts])
