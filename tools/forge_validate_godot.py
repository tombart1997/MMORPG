"""Run affected gameplay contracts sequentially against imported assets."""
from forge_rebuild import ROOT,atomic
import subprocess,argparse
p=argparse.ArgumentParser();p.add_argument('tests',nargs='*');a=p.parse_args()
names=a.tests or ['forge_runtime_review','combat_smoke','route_mount','character_motion','settlement_loop','zone_loop','farming_loop','first_map_expansion','remaster_profile']
result_path=ROOT/'docs/forge_rebuild/gameplay_validation.json'
results=__import__('json').loads(result_path.read_text()).get('tests',[]) if result_path.exists() else []
results=[r for r in results if r['test'] not in names]
for name in names:
 log=ROOT/'docs/forge_rebuild'/f'test_{name}.log'
 with log.open('w',encoding='utf-8') as output:
  try:
   rendering=['--rendering-method','gl_compatibility'] if name=='remaster_profile' else ['--headless','--fixed-fps','60']
   command=['Godot_console.exe',*rendering,'--path',str(ROOT/'game'),'--script','res://tests/'+name+'.gd']
   if name=='remaster_profile':command+=['--','--label=forge_rebuild']
   r=subprocess.run(command,stdout=output,stderr=subprocess.STDOUT,cwd=ROOT,timeout=180);code=r.returncode
  except subprocess.TimeoutExpired:code=124
 errors=[line.strip() for line in log.read_text(encoding='utf-8',errors='replace').splitlines() if 'ERROR:' in line or 'FAIL:' in line or 'Parse Error:' in line]
 if code==124:errors.append('Test timed out after 180 seconds.')
 results.append({'test':name,'exit_code':code,'errors':errors});print(name,code,'errors',len(errors),flush=True)
 atomic(ROOT/'docs/forge_rebuild/gameplay_validation.json',{'tests':results,'all_passed':all(r['exit_code']==0 and not r['errors'] for r in results)})
 if code or errors:break
raise SystemExit(0 if results and all(r['exit_code']==0 and not r['errors'] for r in results) else 1)
