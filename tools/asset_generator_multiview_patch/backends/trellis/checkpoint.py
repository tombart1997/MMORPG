"""Resume expensive native inference only when exact retained inputs still match."""
import hashlib
import json
from pathlib import Path


def signature(references, settings):
    adapter=Path(__file__).resolve().parent
    code={name:hashlib.sha256((adapter/name).read_bytes()).hexdigest()
          for name in ['runner.py','export_glb.py','sdpa.py','patch_upstream.py','tensor_checks.py']}
    return {'inputs':[hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in references],
        'geometry_adapter':code,
        'seed':settings.get('generation_seed',42),'steps':settings.get('trellis_steps',25),
        'guidance':settings.get('trellis_guidance',5.0),'mode':settings.get('multiview_mode','multidiffusion'),
        'angles':settings.get('reference_view_angles',[])}


def save(output, identity):
    output=Path(output)
    files=[output/'source.glb',output/'generation.json',*[output/f'foreground_{i:02d}.png' for i in range(len(identity['inputs']))]]
    if not all(p.is_file() for p in files):raise RuntimeError('Native checkpoint lacks required mesh, metadata or masks')
    record={'signature':identity,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.name!='generation.json'}}
    (output/'native_checkpoint.json').write_text(json.dumps(record,indent=2),encoding='utf-8')


def matches(output, identity):
    output=Path(output);path=output/'native_checkpoint.json'
    if not path.is_file():return False
    try:
        record=json.loads(path.read_text(encoding='utf-8'))
        return record['signature']==identity and (output/'generation.json').is_file() and all(
            (output/name).is_file() and hashlib.sha256((output/name).read_bytes()).hexdigest()==digest
            for name,digest in record['files'].items())
    except (OSError, ValueError, KeyError):return False
