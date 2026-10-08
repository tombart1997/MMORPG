"""Run real rendered world and mounted reviews sequentially."""
from forge_rebuild import ROOT,atomic
import subprocess,json,argparse
p=argparse.ArgumentParser();p.add_argument('tests',nargs='*');a=p.parse_args()
results=[]
for name in a.tests or ['townfolk_review','presentation_upgrade','jade_visual_review']:
 log=ROOT/'docs/forge_rebuild'/f'rendered_{name}.log'
 with log.open('w',encoding='utf-8') as output:
  r=subprocess.run(['Godot_console.exe','--path',str(ROOT/'game'),'--rendering-method','gl_compatibility','--script','res://tests/'+name+'.gd','--','--label','forge_rebuild'],stdout=output,stderr=subprocess.STDOUT,cwd=ROOT,timeout=180)
 errors=[line.strip() for line in log.read_text(encoding='utf-8',errors='replace').splitlines() if 'ERROR:' in line or 'FAIL:' in line or 'Parse Error:' in line]
 results.append({'test':name,'exit_code':r.returncode,'errors':errors})
 atomic(ROOT/'docs/forge_rebuild/rendered_validation.json',{'tests':results,'all_passed':all(r['exit_code']==0 and not r['errors'] for r in results)})
 print(name,r.returncode,'errors',len(errors),flush=True)
 if r.returncode or errors:break
raise SystemExit(0 if all(r['exit_code']==0 and not r['errors'] for r in results) else 1)
