"""Read the existing Godot resources without changing runtime data."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'concepts_docs' / 'tables' / 'project_snapshot.json'

def resource(path):
    text = path.read_text(encoding='utf-8-sig')
    body = text.split('[resource]', 1)[-1]
    fields = dict(re.findall(r'^([\w]+)\s*=\s*(.+)$', body, re.M))
    refs = dict((rid, p) for p, rid in re.findall(r'\[ext_resource[^\n]*path="([^"]+)"[^\n]*id="([^"]+)"\]', text))
    return text, fields, refs

def value(fields, key, default=None):
    v = fields.get(key)
    if v is None:
        return default
    if re.fullmatch(r'&?"[^"]*"', v):
        return v.lstrip('&')[1:-1]
    if v in ('true', 'false'):
        return v == 'true'
    try:
        return float(v) if '.' in v else int(v)
    except ValueError:
        return v

def ref_path(fields, refs, key):
    match = re.search(r'ExtResource\("([^"]+)"\)', fields.get(key, ''))
    return refs.get(match[1], '') if match else ''

def local(res_path):
    return ROOT / 'game' / res_path.removeprefix('res://')

def snapshot():
    items = {}
    for path in sorted((ROOT / 'game/data/items').glob('*.tres')):
        _, f, _ = resource(path)
        item_id = value(f, 'id', path.stem)
        items[item_id] = {k: value(f, k, d) for k, d in [('id',item_id),('display_name',path.stem),('item_type','misc'),('required_level',1),('rarity','common'),('value',1),('equipment_slot',''),('description','')]}
        items[item_id]['source'] = str(path.relative_to(ROOT)).replace('\\','/')
    enemies = []
    for path in sorted((ROOT / 'game/data/enemies').glob('*.tres')):
        _, f, refs = resource(path)
        row = {k: value(f, k, d) for k, d in [('id',path.stem),('display_name',path.stem),('level',1),('tier',1),('family','mossling'),('maximum_health',75),('defense',0),('speed',3.2),('xp',25),('gold_min',6),('gold_max',8)]}
        row['source'] = str(path.relative_to(ROOT)).replace('\\','/')
        row['drop_source'] = ref_path(f, refs, 'drops')
        row['leader_reward'] = ref_path(f, refs, 'leader_reward')
        row['drops'] = []
        if row['drop_source']:
            dt, _, dr = resource(local(row['drop_source']))
            for block in re.findall(r'\[sub_resource[^\]]*\]\n(.*?)(?=\n\[|\Z)', dt, re.S):
                df = dict(re.findall(r'^([\w]+)\s*=\s*(.+)$', block, re.M))
                if 'item' not in df:
                    continue
                ip = ref_path(df, dr, 'item')
                _, it, _ = resource(local(ip))
                item_id = value(it, 'id', Path(ip).stem)
                row['drops'].append({'item_id':item_id,'name':items[item_id]['display_name'],'chance':value(df,'chance',1),'min':value(df,'minimum',1),'max':value(df,'maximum',1)})
        enemies.append(row)
    unique = {}
    for enemy in enemies:
        if enemy['id'] in unique:
            unique[enemy['id']].setdefault('source_aliases', []).append(enemy['source'])
        else:
            unique[enemy['id']] = enemy
    resource_count = len(enemies)
    enemies = list(unique.values())
    skills = []
    for path in sorted((ROOT / 'game/data/skills').glob('*.tres')):
        _, f, _ = resource(path)
        skills.append({k:value(f,k,d) for k,d in [('id',path.stem),('display_name',path.stem),('description',''),('cooldown',0)]})
    npcs=[]
    for path in sorted((ROOT / 'game/data/npcs').glob('*.tres')):
        _,f,_=resource(path)
        npcs.append({k:value(f,k,d) for k,d in [('id',path.stem),('display_name',path.stem),('role',''),('description','')]})
    quests=[]
    for path in sorted((ROOT / 'game/data/quests').glob('*.tres')):
        _,f,_=resource(path)
        quests.append({k:value(f,k,d) for k,d in [('id',path.stem),('display_name',path.stem),('title',path.stem),('description','')]})
    result={'captured_on':'2026-10-03','enemy_resource_count':resource_count,'status':'Current prototype resource snapshot; not a claim that proposed design is implemented.','enemies':enemies,'items':list(items.values()),'skills':skills,'npcs':npcs,'quests':quests}
    DEST.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Snapshot: {len(enemies)} enemy resources, {len(items)} items, {len(skills)} skills.')
    for m in enemies:
        print(f"{m['id']:20} L{m['level']:2} T{m['tier']} {m['xp']:4}XP {m['family']:10} drops={len(m['drops'])}")
    print('NPCs:', ', '.join(f"{n['display_name']} ({n['role']})" for n in npcs))
    return result

if __name__=='__main__':
    snapshot()
