"""Snapshot installed source changes, with diffs only where a real backup exists."""
from pathlib import Path
import difflib, hashlib, json, shutil, zipfile

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
BEFORE=ROOT/'.local/forge_rebuild/optimization_baseline/generator'
OUT=ROOT/'docs/asset_review/generator_changes'
FILES=['README.md','docs/diagnosis_repair.md','config/presets.json',
       'forge/api.py','forge/jobs.py','forge/reviewflow.py','forge/game_bridge.py','forge/glb_cleanup.py',
       'blender/pipeline.py','blender/optimize.py','blender/remesh_worker.py','blender/diagnose.py',
       'blender/repair.py','blender/rebuild_parts.py','web/app.js','web/index.html','web/reviewflow.js',
       'web/style.css','tests/test_api.py','tests/test_contracts.py','tests/test_reviewflow.py','tests/test_glb_cleanup.py']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

OUT.mkdir(parents=True,exist_ok=True)
records=[];patch=[]
for relative in FILES:
    current=FORGE/relative
    assert current.is_file(),relative
    target=OUT/'installed'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current,target)
    baseline=BEFORE/relative
    record={'path':relative,'installed_sha256':sha(current),'bytes':current.stat().st_size,
            'baseline_available':baseline.is_file(),'note':'Installed snapshot; no assumed original contents.'}
    if baseline.is_file():
        original=OUT/'before'/relative;original.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(baseline,original)
        record.update(baseline_sha256=sha(baseline),changed=sha(baseline)!=sha(current),note='Diff against retained pre-change backup.')
        patch.extend(difflib.unified_diff(baseline.read_text(encoding='utf-8').splitlines(keepends=True),
             current.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='a/'+relative,tofile='b/'+relative))
    records.append(record)
(OUT/'backed_changes.patch').write_text(''.join(patch),encoding='utf-8')
manifest={'date':'2026-10-04','installed_root':str(FORGE),'files':records,
          'scope':'Source-only audit/backup package. Sources, generated assets, references, libraries, dependencies and credentials are not copied.',
          'restore':'Inspect backed_changes.patch and before/ for recorded prior files. Installed snapshots without a prior backup are not claimed to be new files. Build web/dist after copying reviewed changes. Never blanket-overwrite later local edits.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
archive=OUT.parent/'generator_changes.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in OUT.rglob('*'):
        if path.is_file():z.write(path,path.relative_to(OUT).as_posix())
print('Saved',len(records),'installed source files;',sum(r['baseline_available'] for r in records),'retained baselines.',archive)
