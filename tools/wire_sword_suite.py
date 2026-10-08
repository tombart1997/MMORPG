"""Bind existing item IDs to the authored suite; statistics and saves are untouched."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1];GAME=ROOT/'game'
manifest=json.loads((GAME/'assets/generated/weapon_contracts.json').read_text())
mapping={'wayfarer_blade':'wayfarer','marchguard_sword':'marchguard','briarsteel_edge':'briarsteel','cairnwarden_sword':'cairnwarden','wakecleaver':'wakecleaver','ember_fang':'ember','glass_sabre':'glass','rift_cleaver':'rift'}
for path in (GAME/'data/items').glob('*.tres'):
    if path.stem.startswith('frontier_blade'):mapping[path.stem]='frontier'
    elif path.stem.startswith('relic_blade'):mapping[path.stem]='relic'
for name,data in manifest.items():
    if name=='gold_coin':continue
    x,y,z=data['tip']
    text='[gd_scene load_steps=2 format=3]\n[ext_resource type="PackedScene" path="res://assets/generated/weapons/'+name+'.glb" id="1"]\n[node name="ForgedSword" type="Node3D"]\nmetadata/two_handed = '+str(data['two_handed']).lower()+'\n[node name="Model" parent="." instance=ExtResource("1")]\n[node name="Grip" type="Marker3D" parent="."]\n[node name="Tip" type="Marker3D" parent="."]\nposition = Vector3(%s, %s, %s)\n'%(x,y,z)
    if data['two_handed']:text+='[node name="OffhandGrip" type="Marker3D" parent="."]\nposition = Vector3(0, 0, 0.18)\n'
    (GAME/'scenes/visuals'/('forged_'+name+'.tscn')).write_text(text)
for item,name in mapping.items():
    path=GAME/'data/items'/(item+'.tres');text=path.read_text()
    text=re.sub(r'path="res://scenes/visuals/[^"\n]+"', 'path="res://scenes/visuals/forged_'+name+'.tscn"',text,count=1);path.write_text(text)
(GAME/'scenes/visuals/iron_sword.tscn').write_text((GAME/'scenes/visuals/forged_wayfarer.tscn').read_text())
(GAME/'scenes/visuals/cairnwarden_sword.tscn').write_text((GAME/'scenes/visuals/forged_cairnwarden.tscn').read_text())
print('Bound',len(mapping),'existing sword items to',len(manifest),'new authored models')
