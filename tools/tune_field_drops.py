"""Explicit common-drop budget; rare gear, currencies and guaranteed camp rewards unchanged."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/'game/data/drops').glob('*.tres'):
    text=path.read_text();items=dict(re.findall(r'path="res://data/items/([^"/]+).tres" id="([^"]+)"',text))
    items={value:key for key,value in items.items()}
    def tune(match):
        block=match.group(0);item=re.search(r'item = ExtResource\("([^"]+)"\)',block)
        if not item:return block
        name=items.get(item.group(1),'');chance=None
        if name.endswith('_trophy'):chance=.225
        elif name=='field_tonic':chance=.25 if path.stem=='fracture' else .04
        elif name=='moss_shard':chance=.80 if path.stem=='fracture' else .45 if path.stem=='young' else .35
        elif path.stem=='mossling':chance={'briarsteel_edge':.05,'briarhide_coat':.05,'cairnwarden_sword':.02,'cairn_cap':.025,'pathrunner_boots':.025}.get(name)
        if chance is None:return block
        if re.search(r'^chance =',block,re.M):block=re.sub(r'^chance = .*$',f'chance = {chance}',block,flags=re.M)
        else:block=block.rstrip()+f'\nchance = {chance}\n'
        if name in ['moss_shard','field_tonic']:
            maximum=2 if name=='moss_shard' and path.stem=='fracture' else 1
            block=re.sub(r'^(minimum|maximum) = .*\n','',block,flags=re.M)
            block=block.rstrip()+f'\nminimum = 1\nmaximum = {maximum}\n'
        return block
    updated=re.sub(r'\[sub_resource[^\n]*\]\n[^\[]*',tune,text)
    if updated!=text:path.write_text(updated);print('Retuned',path.stem)
