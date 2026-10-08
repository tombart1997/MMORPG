"""Run the shipped gameplay gates against the final imported catalogue."""
import argparse,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('suites',nargs='*');args=parser.parse_args()
suites=args.suites or ['combat_smoke','melee_commitment','zone_loop','character_pipeline','rpg_progression','settlement_loop','mmorpg_loop','skill_combat','farming_loop','route_mount','first_map_expansion','combat_creation_review','second_region','remaster_streaming','remaster_traversal','townfolk_review','hero_combat_review','jade_visual_review','world_landscape','character_motion','presentation_upgrade','field_feedback_review','art_benchmark','forge_runtime_review','reviewed_replacement_integration']
out=ROOT/'.local/full_asset_rebuild/tests';out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
for key,directory in [('APPDATA','roaming'),('LOCALAPPDATA','local')]:
    path=out/directory;path.mkdir(exist_ok=True);env[key]=str(path)
report_path=ROOT/'docs/full_asset_rebuild/gameplay_checks.json'
reports=json.loads(report_path.read_text()) if args.suites and report_path.exists() else []
for name in suites:
    log=out/(name+'.log');started=time.monotonic()
    cmd=['C:/Program Files/Godot/Godot_console.exe','--headless','--path',str(ROOT/'game'),'--fixed-fps','60','--script','res://tests/'+name+'.gd']
    if name=='reviewed_replacement_integration':cmd+=['--','--deployed']
    with log.open('w',encoding='utf-8') as output:
        try:result=subprocess.run(cmd,stdout=output,stderr=subprocess.STDOUT,env=env,timeout=120);code=result.returncode
        except subprocess.TimeoutExpired:code=124
    content=log.read_text(encoding='utf-8');failures=[line for line in content.splitlines() if 'FAIL:' in line or 'SCRIPT ERROR:' in line or (line.startswith('ERROR:') and 'root certificate' not in line)]
    report={'suite':name,'passed':code==0 and not failures,'exit_code':code,'checks':content.count('PASS:'),'seconds':round(time.monotonic()-started,2),'failures':failures}
    reports=[item for item in reports if item['suite']!=name]
    reports.append(report);print(json.dumps(report),flush=True)
    report_path.write_text(json.dumps(reports,indent=2))
raise SystemExit(0 if all(r['passed'] for r in reports) else 1)
