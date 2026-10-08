"""Versioned visual mappings for the configured local game; no entity mutations."""
import json,shutil
from pathlib import Path
from .store import digest,atomic_json,now
from .reviewflow import state

GAME=Path(r'D:\Games\Metin2Clone\game')


def apply_version(store,aid,vid):
    a=store.get(aid);flow=state(a);binding=flow.get('game_binding')
    if not binding:raise ValueError('No registered game target for this inventory asset')
    target=binding['target']
    if not target.startswith('res://assets/') or '..' in target or not target.endswith('.glb'):raise ValueError('Invalid registered game mapping')
    source=(GAME/target[6:]).resolve()
    if not source.is_relative_to(GAME.resolve()) or not source.is_file():raise ValueError('Game target missing')
    version=next((v for v in flow['versions'] if v['id']==vid),None)
    if not version or version.get('rejected'):raise ValueError('Only accepted retained versions can enter the game')
    if not version['review']['checks'].get('integration'):raise ValueError('Gameplay integration is required')
    runtime=store.file(aid,version['runtime'])
    if digest(runtime)!=version['sha256']:raise ValueError('Version hash changed')
    registry=GAME/'data/visuals/reviewed_versions.json'
    data=json.loads(registry.read_text()) if registry.exists() else {'schema':1,'mappings':{},'history':[]}
    old=data['mappings'].get(target)
    if old and old.get('version_id')==vid and old.get('sha256')==version['sha256']:
        active=(GAME/old['path'][6:]).resolve()
        if not active.is_relative_to(GAME.resolve()) or digest(active)!=version['sha256']:raise ValueError('Active version file changed')
        store.update(aid,lambda a:a['reviewflow'].update(game_version=vid))
        return old
    directory=GAME/'assets/reviewed'/aid/vid;directory.mkdir(parents=True,exist_ok=True)
    dest=directory/'runtime.glb'
    if dest.exists() and digest(dest)!=version['sha256']:raise ValueError('Immutable version export differs')
    if not dest.exists():shutil.copy2(runtime,dest)
    # A baseline version makes rollback immediate even for the first promotion.
    baseline=GAME/'assets/reviewed'/aid/'working_previous.glb'
    if not baseline.exists():shutil.copy2(source,baseline)
    record={'asset_id':aid,'version_id':vid,'path':'res://'+dest.relative_to(GAME).as_posix(),
        'sha256':version['sha256'],'previous':old or {'path':'res://'+baseline.relative_to(GAME).as_posix(),'sha256':digest(baseline)},
        'status':flow['status'],'fallback':version['review'].get('fallback',False),'applied_at':now()}
    data['mappings'][target]=record;data['history'].append({'target':target,**record});atomic_json(registry,data)
    store.update(aid,lambda a:a['reviewflow'].update(game_version=vid));return record


def rollback_game(store,aid):
    a=store.get(aid);binding=state(a).get('game_binding')
    if not binding:raise ValueError('Asset has no game binding')
    registry=GAME/'data/visuals/reviewed_versions.json';data=json.loads(registry.read_text())
    old=data['mappings'].get(binding['target'])
    if not old or not old.get('previous'):raise ValueError('No previous deployed mapping')
    previous=old['previous'];path=GAME/previous['path'][6:]
    if not path.resolve().is_relative_to(GAME.resolve()):raise ValueError('Rollback file leaves the game directory')
    if digest(path)!=previous['sha256']:raise ValueError('Rollback file changed')
    data['mappings'][binding['target']]=previous;data['history'].append({'operation':'rollback','target':binding['target'],'from':old['path'],'to':previous['path'],'timestamp':now()})
    atomic_json(registry,data)
    store.update(aid,lambda a:a['reviewflow'].update(game_version=previous.get('version_id')))
    return previous
