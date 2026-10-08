"""CPU mesh preparation after serial GPU jobs finish; no asset publication."""
import json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BUDGETS={'stonekin':18000,'wisp':12000,'bandit':24000,'dead_tree':6000,'fallen_log':6000,
 'shrine':8000,'tent':8000,'ruin_arch':8000,'crate':4000,'bridge':8000,
 'keeper':24000,'stablemaster':24000,'saddle':6000}
report_file=ROOT/'docs/full_asset_rebuild/preparation_queue.json'
report=json.loads(report_file.read_text()) if report_file.exists() else {}
while any(key not in report for key in BUDGETS):
    queue={}
    for p in (ROOT/'docs/full_asset_rebuild').glob('*generation_queue.json'):queue.update(json.loads(p.read_text()))
    for key,budget in BUDGETS.items():
        if key in report:continue
        job=queue.get(key,{})
        if job.get('state')=='succeeded':
            result=subprocess.run(['python',str(ROOT/'tools/prepare_full_rebuild.py'),key,'--budget',str(budget)],cwd=ROOT)
            report[key]={'state':'prepared' if result.returncode==0 else 'reduction_rejected','native_job':job['job_id'],'budget':budget}
            report_file.write_text(json.dumps(report,indent=2));print('PREPARATION',key,report[key]['state'],flush=True)
        elif job.get('state') in ['failed','interrupted']:
            report[key]={'state':'native_failed','native_job':job['job_id']};report_file.write_text(json.dumps(report,indent=2))
    time.sleep(15)
