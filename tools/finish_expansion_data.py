"""Upgrade the original encounter tables without changing quest material IDs."""
from pathlib import Path
import re
root = Path(__file__).resolve().parents[1] / 'game'
for name, level, tier in [('young',1,1),('grown',4,1),('ironback',7,2)]:
    path = root / ('data/enemies/'+name+'.tres')
    text = path.read_text()
    text = re.sub(r'^leader_reward = .*\n', '', text, flags=re.M)
    if '\nlevel = ' not in text:
        text = text.replace('[resource]\n', '[resource]\nlevel = %d\ntier = %d\n' % (level,tier))
    path.write_text(text)
    # Moss shards remain the original quest/reinforcement material; species trophies
    # make each original monster useful to the new crafting workshop too.
    import author_first_map as author
    trophy = name+'_trophy'
    author.item(trophy, {'young':'Young Mossling Sap','grown':'Grown Mossling Bark','ironback':'Ironback Plate'}[name], 'material', description='Species-specific crafting material. Bring to the Relic Workshop.')
    entries = [('moss_shard',1.0 if name=='young' else .8),('field_tonic',.08),('relic_blade_1',.002),('relic_coat_1',.002),(trophy,.45)]
    text = author.header('rpg/drop_table.gd')+'[ext_resource type="Script" path="res://scripts/rpg/drop_entry.gd" id="entry"]\n'
    for i,(item,_) in enumerate(entries): text += '[ext_resource type="Resource" path="res://data/items/%s.tres" id="i%d"]\n' % (item,i)
    for i,(_,rate) in enumerate(entries): text += '[sub_resource type="Resource" id="e%d"]\nscript = ExtResource("entry")\nitem = ExtResource("i%d")\nchance = %s\n' % (i,i,rate)
    text += '[resource]\nscript = ExtResource("script")\nentries = Array[ExtResource("entry")](['+', '.join('SubResource("e%d")'%i for i in range(len(entries)))+'])\n'
    (root / ('data/drops/'+name+'.tres')).write_text(text)
