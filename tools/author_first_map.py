"""Author the first-map resource catalogue from explicit species/encounter rows.

Run with Python 3.8+. Writes only expansion-owned resources; no art generation.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'game'
# id, display name, level, tier, family, tint, x, z
MONSTERS = [
 ('meadow_wolf','Meadow Wolf',1,1,'wolf','88816d',-25,-18),
 ('blue_wolf','Blue Wolf',3,1,'wolf','537eaa',-55,-22),
 ('red_wolf','Red Wolf',5,2,'wolf','a55442',-88,-22),
 ('bristle_boar','Bristle Boar',2,1,'boar','8e7150',55,-22),
 ('reed_spider','Reed Spider',4,1,'spider','74874c',88,-22),
 ('grey_wolf','Grey Wolf',6,1,'wolf','73828b',-88,-66),
 ('mire_boar','Mire Boar',7,2,'boar','5f795a',-57,-66),
 ('copper_spider','Copper Spider',8,1,'spider','a77d51',55,-66),
 ('road_bandit','Road Bandit',9,2,'bandit','a88c73',88,-66),
 ('moonfang','Moonfang',8,3,'wolf','b6cadb',-87,-104),
 ('thicket_wolf','Thicket Wolf',10,1,'wolf','60775e',-48,-108),
 ('blacktusk','Blacktusk Boar',11,2,'boar','46484f',-5,-112),
 ('venom_spider','Venom Spider',12,2,'spider','79629d',38,-110),
 ('hollow_raider','Hollow Raider',13,1,'bandit','ba754c',85,-110),
 ('cinder_wisp','Cinder Wisp',14,1,'wisp','d08349',-87,-153),
 ('slate_guardian','Slate Guardian',12,3,'stonekin','70838f',-45,-154),
 ('frost_wolf','Frost Wolf',15,2,'wolf','a5c5cc',0,-155),
 ('ironhide_boar','Ironhide Boar',16,1,'boar','647380',44,-155),
 ('silk_matron','Silk Matron',16,4,'spider','936b9d',87,-153),
 ('ash_bandit','Ash Bandit',17,2,'bandit','b8a399',-87,-197),
 ('grave_wisp','Grave Wisp',18,1,'wisp','79ac98',-44,-199),
 ('cairn_sentinel','Cairn Sentinel',19,2,'stonekin','92886b',0,-199),
 ('bloodfang','Bloodfang',20,4,'wolf','a8444a',45,-198),
 ('dusk_stalker','Dusk Stalker',20,2,'wolf','625987',88,-198),
 ('obsidian_boar','Obsidian Boar',21,2,'boar','474254',-87,-244),
 ('widow_spider','Widow Spider',22,2,'spider','884a61',-44,-244),
 ('exile_captain','Exile Captain',23,3,'bandit','bc8557',0,-246),
 ('storm_wisp','Storm Wisp',24,2,'wisp','7b9bcf',43,-244),
 ('cairn_colossus','Cairn Colossus',25,5,'stonekin','928c7f',87,-253),
 ('ancient_warden','Ancient Warden',25,5,'stonekin','a1b086',-87,-279),
]

def write(path, text):
    dest = GAME / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text.strip()+'\n', encoding='utf-8')

def header(script):
    return '[gd_resource type="Resource" format=3]\n[ext_resource type="Script" path="res://scripts/'+script+'" id="script"]\n'

def color(hexcode):
    return 'Color('+', '.join(str(round(int(hexcode[i:i+2],16)/255,4)) for i in (0,2,4))+', 1)'

def item(identifier, title, kind, level=1, bonus=None, rare=False, description='', healing=0):
    icon = {'weapon':'sword','armor':'armor','consumable':'consumable','material':'material'}[kind]
    text = header('rpg/item_data.gd')+f'[ext_resource type="Texture2D" path="res://assets/icons/{icon}.svg" id="icon"]\n'
    if kind in ('weapon','armor'):
        visual = 'iron_sword' if kind=='weapon' else 'traveler_armor'
        text += f'[ext_resource type="PackedScene" path="res://scenes/visuals/{visual}.tscn" id="visual"]\n'
    if kind == 'weapon':
        text += '[ext_resource type="Script" path="res://scripts/combat/attack_data.gd" id="attack"]\n'
        for i, attack in enumerate(('player_sword','player_return','player_finisher')):
            text += f'[ext_resource type="Resource" path="res://data/attacks/{attack}.tres" id="a{i}"]\n'
    text += f'[resource]\nscript = ExtResource("script")\nid = &"{identifier}"\ndisplay_name = "{title}"\ndescription = "{description}"\nitem_type = "{kind}"\nicon = ExtResource("icon")\nrequired_level = {level}\nvalue = {max(1,level*3)}\n'
    if kind in ('weapon','armor'):
        text += f'stackable = false\nequipment_slot = &"'+('weapon' if kind=='weapon' else 'chest')+'"\nvisual = ExtResource("visual")\n'
        text += 'modifiers = '+json.dumps(bonus)+'\n'
    else: text += 'maximum_stack = 99\n'
    if rare: text += 'rarity = &"rare"\n'
    if kind == 'weapon': text += 'attacks = Array[ExtResource("attack")]([ExtResource("a0"), ExtResource("a1"), ExtResource("a2")])\n'
    if healing: text += f'healing = {float(healing)}\n'
    write('data/items/'+identifier+'.tres',text)

def shop(identifier,title,offers):
    text=header('npc/shop_data.gd')+'[ext_resource type="Script" path="res://scripts/npc/shop_offer.gd" id="offer"]\n'
    for i,(item_id,price,ingredients) in enumerate(offers):
        text+=f'[ext_resource type="Resource" path="res://data/items/{item_id}.tres" id="i{i}"]\n'
    for i,(_,price,ingredients) in enumerate(offers):
        text+=f'[sub_resource type="Resource" id="o{i}"]\nscript = ExtResource("offer")\nitem = ExtResource("i{i}")\nprice = {price}\ningredients = {json.dumps(ingredients)}\n'
    text+=f'[resource]\nscript = ExtResource("script")\nid = &"{identifier}"\ntitle = "{title}"\noffers = Array[ExtResource("offer")](['+', '.join(f'SubResource("o{i}")' for i in range(len(offers)))+'])\n'
    write(f'data/shops/{identifier}.tres',text)

def main():
    for band in range(5):
        level=band*5+1
        for rare in (False,True):
            prefix='relic' if rare else 'frontier'
            item(f'{prefix}_blade_{level}',f'{["Verge","Hollow","Highland","Ashen","Ancient"][band]} '+('Relic Blade' if rare else 'Steel Blade'),'weapon',level,{'attack':22+band*15 if rare else 14+band*10},rare,'A weapon forged for this hunting band.')
            item(f'{prefix}_coat_{level}',f'{["Verge","Hollow","Highland","Ashen","Ancient"][band]} '+('Relic Coat' if rare else 'Field Coat'),'armor',level,{'defense':4+band*4 if rare else 2+band*3,'max_hp':20+band*25 if rare else 10+band*15},rare,'Armor for the outer hunting grounds.')
    item('restoration_tonic','Restoration Tonic','consumable',6,healing=110,description='A stronger restorative. Shares the potion cooldown.')
    item('greater_tonic','Greater Tonic','consumable',16,healing=220,description='For dangerous northern hunts. Shares the potion cooldown.')
    recipes=[]
    manifest=[]
    for index,(identifier,title,level,tier,family,tint,x,z) in enumerate(MONSTERS):
        trophy=identifier+'_trophy'
        ingredient=title+' '+{'wolf':'Fang','boar':'Tusk','spider':'Silk','bandit':'Insignia','wisp':'Essence','stonekin':'Core'}[family]
        item(trophy,ingredient,'material',description=f'Harvested only from {title}. Bring to Ilyra\'s Relic Workshop to craft level-band equipment.')
        gearlevel=((level-1)//5)*5+1
        potion='field_tonic' if level<6 else 'restoration_tonic' if level<16 else 'greater_tonic'
        chance=.0015+tier*.0005
        entries=[(trophy,.45,1,2 if tier>=3 else 1),(potion,.08,1,1),(f'relic_blade_{gearlevel}',chance,1,1),(f'relic_coat_{gearlevel}',chance,1,1)]
        text=header('rpg/drop_table.gd')+'[ext_resource type="Script" path="res://scripts/rpg/drop_entry.gd" id="entry"]\n'
        for i,(drop,_,_,_) in enumerate(entries): text+=f'[ext_resource type="Resource" path="res://data/items/{drop}.tres" id="i{i}"]\n'
        for i,(_,rate,minimum,maximum) in enumerate(entries): text+=f'[sub_resource type="Resource" id="e{i}"]\nscript = ExtResource("entry")\nitem = ExtResource("i{i}")\nchance = {rate}\nminimum = {minimum}\nmaximum = {maximum}\n'
        text+='[resource]\nscript = ExtResource("script")\nentries = Array[ExtResource("entry")](['+', '.join(f'SubResource("e{i}")' for i in range(4))+'])'
        write(f'data/drops/{identifier}.tres',text)
        hp=round((65+level*18)*[0,1,1.35,2.5,3.8,6][tier])
        damage=round((8+level*1.5)*[0,1,1.15,1.4,1.6,1.85][tier],1)
        text=header('ai/enemy_data.gd')+'[ext_resource type="Script" path="res://scripts/combat/attack_data.gd" id="attack"]\n'
        visual='humanoid' if family=='bandit' else 'field_creature'
        text+=f'[ext_resource type="PackedScene" path="res://scenes/visuals/{visual}.tscn" id="visual"]\n[ext_resource type="Resource" path="res://data/drops/{identifier}.tres" id="drops"]\n'
        text+=f'[sub_resource type="Resource" id="strike"]\nscript = ExtResource("attack")\ndisplay_name = "{title} strike"\ndamage = {damage}\nwindup = {0.52 if tier>=3 else .38}\nactive = 0.16\nrecovery = {0.55 if tier>=3 else .85}\nreach = 2.15\ncone_degrees = 100.0\nlunge_distance = 0.4\n'
        xp=round((12+8*level)*[0,1,1.2,2,3,5][tier])
        text+=f'[resource]\nscript = ExtResource("script")\nid = &"{identifier}"\ndisplay_name = "{title}"\nlevel = {level}\ntier = {tier}\nfamily = &"{family}"\ntint = {color(tint)}\nmaximum_health = {float(hp)}\ndefense = {round(level*.22+(tier-1)*.8,2)}\nattack = SubResource("strike")\nvisual = ExtResource("visual")\nvisual_scale = {1+(tier-1)*.13}\nspeed = {4.6+(tier-3)*.3 if tier>=3 else 3.1}\naggro_radius = {10+(tier-3)*1.5 if tier>=3 else 0}.0\nxp = {xp}\ngold_min = {2+level*2}\ngold_max = {4+level*3+tier*3}\ndrops = ExtResource("drops")\n'
        # Numeric formatting above must not append a second decimal for elite radii.
        text=text.replace('11.5.0','11.5').replace('13.0.0','13.0').replace('10.0.0','10.0')
        write(f'data/enemies/{identifier}.tres',text)
        recipes.append((f'relic_blade_{gearlevel}' if index%2==0 else f'relic_coat_{gearlevel}',120+level*25,{trophy:20+tier*5}))
        manifest.append(dict(id=identifier,name=title,level=level,tier=tier,family=family,position=[x,z],hp=hp,damage=damage,xp=xp,group=1 if tier>=3 else 3 if tier==1 else 4,gold=[2+level*2,4+level*3+tier*3],loot=[dict(item=e[0],chance=e[1],minimum=e[2],maximum=e[3]) for e in entries]))
    shop('frontier_weapons',"Darin's Weaponry",[(f'frontier_blade_{l}',60+l*35,{}) for l in (1,6,11,16,21)])
    shop('frontier_armory',"Hessa's Armory",[(f'frontier_coat_{l}',50+l*30,{}) for l in (1,6,11,16,21)])
    shop('frontier_apothecary',"Sera's Apothecary",[('field_tonic',6,{}),('restoration_tonic',24,{}),('greater_tonic',65,{})])
    shop('frontier_stable',"Bram's Stables",[('trail_bridle',240,{})])
    for species in ('young','grown','ironback'):
        recipes.append(('relic_coat_1',180,{species+'_trophy':25}))
    shop('frontier_workshop',"Ilyra's Relic Workshop",recipes)
    for identifier,title,stock,shade in [('weapons','Darin - Weapons','frontier_weapons','9a654c'),('armorer','Hessa - Armor','frontier_armory','5e8191'),('apothecary','Sera - Potions','frontier_apothecary','729365'),('stablemaster','Bram - Mounts','frontier_stable','b1a070'),('artificer','Ilyra - Relic Crafting','frontier_workshop','9471a5')]:
        text=header('npc/npc_data.gd')+f'[ext_resource type="Resource" path="res://data/shops/{stock}.tres" id="shop"]\n[ext_resource type="Script" path="res://scripts/npc/dialogue_page.gd" id="page"]\n[sub_resource type="Resource" id="welcome"]\nscript = ExtResource("page")\ntext = "Specialist supplies for the outer March. Inspect the level and material requirements before buying."\nresponses = Array[Dictionary]([{{"text":"Show your wares.","action":"shop"}},{{"text":"Farewell.","action":"close"}}])\n[resource]\nscript = ExtResource("script")\nid = &"{identifier}"\ndisplay_name = "{title}"\nrole = &"merchant"\nclothing_color = {color(shade)}\nshop = ExtResource("shop")\npages = Array[ExtResource("page")]([SubResource("welcome")])'
        write(f'data/npcs/{identifier}.tres',text)
    points=', '.join(f'Vector3({r[6]},0,{r[7]})' for r in MONSTERS)
    ids=', '.join('"'+r[0]+'"' for r in MONSTERS)
    write('scripts/world/first_map_content.gd',f'class_name FirstMapContent\nextends RefCounted\nconst POINTS: Array[Vector3] = [{points}]\nconst IDS: Array[String] = [{ids}]')
    write('data/first_map_catalogue.json',json.dumps(manifest,indent=2))
    print('Authored 30 expansion monsters, per-species materials/loot, 5 specialist shops and NPCs')

if __name__=='__main__': main()
