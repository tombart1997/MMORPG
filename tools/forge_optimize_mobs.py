"""Generate comparable 12k candidates for ordinary grouped enemies only."""
import csv,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'concepts_docs/tables/mobs.csv').open(encoding='utf-8-sig')))
for row in rows:
 if int(row['tier'])>2:continue
 result=subprocess.run([sys.executable,str(ROOT/'tools/forge_optimize_study.py'),'--asset','mob_'+row['mob_id'],'--mode','simplify','--budget','12000','--revision','final'],cwd=ROOT)
 if result.returncode:raise SystemExit(result.returncode)
print('ORDINARY_MOB_STUDIES_COMPLETE',flush=True)
