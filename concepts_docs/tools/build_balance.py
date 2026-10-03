"""Rebuild editable proposal tables from explicit design constants.

No runtime files are written. Current-resource facts come from project_snapshot.json.
"""
from pathlib import Path
import csv
import json
import math
import re

BASE = Path(__file__).resolve().parents[1]
TABLES = BASE / 'tables'
CHANCES = {
    1: [100,100,95,90,85,80,70,60,50],
    2: [100,95,90,85,75,65,55,45,35],
    3: [100,95,85,80,70,60,50,35,25],
    4: [98,92,83,78,68,58,45,30,20],
    5: [95,90,82,75,65,55,40,25,15],
}
GOLD = [15,30,55,95,150,230,350,520,760]
TIER_GOLD = {1:1,2:2,3:4,4:7,5:11}
POWER = [1,1.04,1.09,1.15,1.22,1.30,1.40,1.52,1.66,1.82]
ROUGHNESS = [.85,.80,.73,.65,.56,.46,.36,.28,.21,.16]
SPARK_DENSITY = {1:1,2:1.15,3:1.30,4:1.5,5:1.75}
TROPHIES = {1:'meadow_wolf_trophy',2:'grey_wolf_trophy',3:'blacktusk_trophy',4:'ironhide_boar_trophy',5:'obsidian_boar_trophy'}
LEGACY_LEVELS = {'wayfarer_blade':1,'marchguard_sword':6,'briarsteel_edge':11,'cairnwarden_sword':16,'wakecleaver':21,'travelers_vest':1,'quilted_jack':1,'briarhide_coat':6,'rootward_jack':16,'cairn_cap':11,'pathrunner_boots':6,'ember_fang':18,'glass_sabre':19,'rift_cleaver':25}
LEVEL_CAP = 50

ART = {
    'meadow_wolf':('bestiary_wolves_boars.png',1,'Lean grey-brown pelt; small low-tier silhouette.'),
    'moonfang':('bestiary_wolves_boars.png',2,'Midnight blue coat, pale cheek mane; larger pack leader.'),
    'ember_hound':('bestiary_wolves_boars.png',3,'Charcoal fur, orange fissures; den defender.'),
    'bristle_boar':('bestiary_wolves_boars.png',4,'Tawny bristles, compact body, short tusks.'),
    'blacktusk':('bestiary_wolves_boars.png',5,'Grey-black hide, strong shoulders, chipped black tusks.'),
    'obsidian_boar':('bestiary_wolves_boars.png',6,'Dark volcanic plates, restrained amber seams.'),
    'reed_spider':('bestiary_spiders_bandits.png',1,'Brown reed carapace; slender eight-legged stance.'),
    'silk_matron':('bestiary_spiders_bandits.png',2,'Pale bulky abdomen, broad stance, silk drapery.'),
    'glass_spider':('bestiary_spiders_bandits.png',3,'Smoky faceted carapace over dark articulated legs.'),
    'road_bandit':('bestiary_spiders_bandits.png',4,'Russet wraps, patched leather, short steel blade.'),
    'hollow_raider':('bestiary_spiders_bandits.png',5,'Grey hood, patched lamellar, curved blade.'),
    'exile_captain':('bestiary_spiders_bandits.png',6,'Battered oxblood/slate lamellar and empty banner pole.'),
    'young':('bestiary_roots_stone.png',1,'Small hunched root body, split feet, amber eyes.'),
    'grown':('bestiary_roots_stone.png',2,'Long knotty arms, ivy, taller root silhouette.'),
    'ironback':('bestiary_roots_stone.png',3,'Heavy bark shoulders, wedged slate, shelf fungus.'),
    'cairn_sentinel':('bestiary_roots_stone.png',4,'Stacked slate limbs; exposed small amber heart.'),
    'cairn_colossus':('bestiary_roots_stone.png',5,'Monumental low broad body, broken cairn crown.'),
    'rift_sentinel':('bestiary_roots_stone.png',6,'Fractured black stone with narrow violet seams.'),
    'grave_wisp':('bestiary_wisps_elites.png',1,'Broken stone charm with teal spectral ribbon.'),
    'storm_wisp':('bestiary_wisps_elites.png',2,'Reed talisman, slate core, pale blue lightning.'),
    'ash_wisp':('bestiary_wisps_elites.png',3,'Charred hanging charm, grey ash and sparse embers.'),
    'dusk_stalker':('bestiary_wisps_elites.png',4,'Very lean dark wolf, sharp predatory shoulder line.'),
    'widow_spider':('bestiary_wisps_elites.png',5,'Massive black spider, subtle burgundy abdomen.'),
    'ancient_warden':('bestiary_wisps_elites.png',6,'Tall slate construct with branching root crown.'),
    'blue_wolf':('bestiary_wolf_variants.png',1,'Small blue-grey coat with dark paws.'),
    'red_wolf':('bestiary_wolf_variants.png',2,'Copper coat, alert ears, charcoal muzzle.'),
    'grey_wolf':('bestiary_wolf_variants.png',3,'Rangy slate coat with pale belly and fur scars.'),
    'frost_wolf':('bestiary_wolf_variants.png',4,'White-grey coat, thick neck ruff, pale blue eyes.'),
    'thicket_wolf':('bestiary_wolf_variants.png',5,'Olive-brown bristles with caught burrs and leaves.'),
    'bloodfang':('bestiary_wolf_variants.png',6,'Large burgundy-black wolf, bone chest ruff, red fangs.'),
    'mire_boar':('bestiary_remaining_variants.png',1,'Low muddy brown body and bent pale tusks.'),
    'ironhide_boar':('bestiary_remaining_variants.png',2,'Rough grey hide, broad iron-coloured bristle ridge.'),
    'copper_spider':('bestiary_remaining_variants.png',3,'Copper-brown chitin and compact abdomen.'),
    'venom_spider':('bestiary_remaining_variants.png',4,'Olive-black carapace, narrow green fang droplets.'),
    'ash_bandit':('bestiary_remaining_variants.png',5,'Soot wraps and leather with ember-red sash.'),
    'cinder_wisp':('bestiary_remaining_variants.png',6,'Burned clay charm and narrow copper flame ribbon.'),
    'slate_guardian':('bestiary_remaining_variants.png',7,'Squared shoulders, etched pale face stone, heavy hands.'),
}

def write_csv(name, rows):
    assert rows, name
    with (TABLES / name).open('w',encoding='utf-8-sig',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def drop_factor(player_level,mob_level):
    """Symmetric logarithmic falloff: no division by zero, no negative chance."""
    player_level=max(1,int(player_level))
    mob_level=max(1,int(mob_level))
    tolerance=max(10.0, .5*(player_level+mob_level))
    remaining=max(0.0,1.0-math.log1p(abs(player_level-mob_level))/math.log1p(tolerance))
    return remaining**2

def progress_at(level,xp):
    """Budget from level and within-level XP; quarter rewards are integers."""
    level=max(1,min(LEVEL_CAP,int(level)))
    if level==LEVEL_CAP:
        return 4*(LEVEL_CAP-1)
    requirement=600+180*(level-1)+35*(level-1)**2
    return 4*(level-1)+min(3,int(4*max(0,xp)/requirement))

def build():
    snapshot=json.loads((TABLES/'project_snapshot.json').read_text(encoding='utf-8'))
    upgrades=[]
    for tier,chances in CHANCES.items():
        cumulative=1.0
        for step,chance in enumerate(chances,1):
            cumulative*=chance/100
            upgrades.append(dict(status='PROPOSED',gear_tier=tier,from_plus=step-1,to_plus=step,success_pct=chance,failure_pct=100-chance,gold=GOLD[step-1]*TIER_GOLD[tier],moss_shard=step,trophy_item_id=TROPHIES[tier],tier_trophy=math.ceil(step/3)*tier,tempered_ore=0 if step<4 else math.ceil((step-3)/2),wakeglass=0 if step<7 else step-6,failure_result='DESTROY_ITEM_AND_SPEND_COSTS',base_item_power_multiplier=POWER[step],roughness=ROUGHNESS[step],spark_color='none' if step<7 else ['blue','red','violet'][step-7],spark_density_multiplier=SPARK_DENSITY[tier] if step>=7 else 0,route_survival_pct=round(cumulative*100,8),expected_base_items_for_this_plus=round(1/cumulative,4)))
    write_csv('smithing_upgrades.csv',upgrades)
    visual=[]
    for step in range(10):
        visual.append(dict(status='PROPOSED',upgrade=step,base_item_power_multiplier=POWER[step],roughness=ROUGHNESS[step],metallic_steel=.85,spark_color='none' if step<7 else ['blue','red','violet'][step-7],spark_density_note='gear tier scales density only; colour follows + level'))
    write_csv('gear_visuals.csv',visual)
    enemies=[]
    drops=[]
    for m in sorted(snapshot['enemies'],key=lambda m:(m['level'],m['tier'],m['id'])):
        plate,panel,brief=ART[m['id']]
        enemies.append(dict(status='CURRENT_RESOURCE_BASELINE',mob_id=m['id'],name=m['display_name'],family=m['family'],level=m['level'],tier=m['tier'],exp=m['xp'],hp=m['maximum_health'],defense=m['defense'],gold_min=m['gold_min'],gold_max=m['gold_max'],art_sheet=plate,art_panel=panel,appearance=brief,source=m['source'],source_aliases='; '.join(m.get('source_aliases',[]))))
        for d in m['drops']:
            drops.append(dict(status='CURRENT_BASE_RATE_PROPOSED_LEVEL_SCALING',mob_id=m['id'],mob_name=m['display_name'],mob_level=m['level'],item_id=d['item_id'],item=d['name'],base_drop_pct=round(100*d['chance'],5),minimum=d['min'],maximum=d['max'],drop_roll='independent per item',level_multiplier='drop_factor(player_level,mob_level)',source=m['drop_source']))
    write_csv('mobs.csv',enemies)
    write_csv('mob_drops.csv',drops)
    examples=[]
    for p,m in [(1,1),(5,5),(5,4),(10,8),(10,5),(20,18),(20,15),(20,10),(25,20),(25,15),(25,5),(5,25),(50,45),(50,25)]:
        factor=drop_factor(p,m)
        examples.append(dict(status='PROPOSED',player_level=p,mob_level=m,gap=abs(p-m),tolerance=max(10,.5*(p+m)),multiplier=round(factor,8),trophy_base_pct=22.5,trophy_effective_pct=round(22.5*factor,6),rare_gear_base_pct=.2,rare_gear_effective_pct=round(.2*factor,6)))
    write_csv('drop_scaling_examples.csv',examples)
    xp=[]
    for lv in range(1,LEVEL_CAP+1):
        req=600+180*(lv-1)+35*(lv-1)**2
        xp.append(dict(status='PROPOSED_QUARTER_POINTS_CURRENT_XP_CURVE',level=lv,xp_to_next=0 if lv==LEVEL_CAP else req,quarter_25=math.ceil(req/4) if lv<LEVEL_CAP else 0,quarter_50=math.ceil(req/2) if lv<LEVEL_CAP else 0,quarter_75=math.ceil(3*req/4) if lv<LEVEL_CAP else 0,quarter_100=req if lv<LEVEL_CAP else 0,stat_points_earned_on_arrival=4*(lv-1),skill_points_earned_on_arrival=lv))
    write_csv('level_progression.csv',xp)
    mastery=[]
    for rank in range(1,18):
        mastery.append(dict(status='PROPOSED',stage='M' if rank==17 else str(rank),previous_stage=str(rank-1),skill_point_cost=1,mastery_leaf_cost=0,cumulative_skill_points=rank,cumulative_mastery_leaves=0,result='Mastery I: M' if rank==17 else 'Basic skill rank',potency_multiplier=round(1+.02*(rank-1),2)))
    for master in range(1,11):
        mastery.append(dict(status='PROPOSED',stage='M'+str(master),previous_stage='M' if master==1 else 'M'+str(master-1),skill_point_cost=0,mastery_leaf_cost=master,cumulative_skill_points=17,cumulative_mastery_leaves=master*(master+1)//2,result='G: Mastery II / maximum' if master==10 else 'Mastery I progression',potency_multiplier=round(1.32+.03*master,2)))
    write_csv('skill_mastery.csv',mastery)
    gear=[]
    for item in snapshot['items']:
        if item['item_type'] not in ('weapon','armor') and not item['equipment_slot']:
            continue
        proposed_level=LEGACY_LEVELS.get(item['id'],item['required_level'])
        tier=1+sum(proposed_level>=breakpoint for breakpoint in [6,11,16,21])
        gear.append(dict(status='CURRENT_ITEMS_PROPOSED_TIER_AND_PLUS9',item_id=item['id'],name=item['display_name'],slot=item['equipment_slot'],required_level=item['required_level'],proposed_required_level=proposed_level,rarity=item['rarity'],proposed_gear_tier=tier,upgrade_max=9,smith_profile='Tier '+str(tier),trophy_item_id=TROPHIES[tier],source=item['source']))
    write_csv('equipment_catalogue.csv',gear)
    fractures=[
        dict(status='PROPOSED',id='briarwake',name='Briarwake Fracture',level=7,gear_tier=2,hp=1800,exp=100,gold_min=28,gold_max=42,mastery_leaf_base_pct=40,mastery_leaf_min=1,mastery_leaf_max=1,wakeglass_base_pct=18,tempered_ore_base_pct=35,respawn_seconds=180),
        dict(status='PROPOSED',id='cairnwake',name='Cairnwake Fracture',level=15,gear_tier=3,hp=6000,exp=300,gold_min=65,gold_max=95,mastery_leaf_base_pct=50,mastery_leaf_min=1,mastery_leaf_max=1,wakeglass_base_pct=22,tempered_ore_base_pct=45,respawn_seconds=240),
        dict(status='PROPOSED',id='ashwake',name='Ashwake Fracture',level=24,gear_tier=4,hp=14000,exp=700,gold_min=140,gold_max=210,mastery_leaf_base_pct=60,mastery_leaf_min=1,mastery_leaf_max=2,wakeglass_base_pct=28,tempered_ore_base_pct=55,respawn_seconds=300),
        dict(status='PROPOSED',id='crownwake',name='Crownwake Fracture',level=40,gear_tier=5,hp=36000,exp=1800,gold_min=360,gold_max=520,mastery_leaf_base_pct=65,mastery_leaf_min=1,mastery_leaf_max=2,wakeglass_base_pct=35,tempered_ore_base_pct=65,respawn_seconds=360),
    ]
    write_csv('fractures.csv',fractures)
    core_materials=[]
    for core in fractures:
        for tier in range(1,core['gear_tier']+1):
            core_materials.append(dict(status='PROPOSED',fracture_id=core['id'],fracture_level=core['level'],item_id=TROPHIES[tier],base_drop_pct=60,minimum=1,maximum=3,level_scaling=True))
        core_materials.append(dict(status='PROPOSED',fracture_id=core['id'],fracture_level=core['level'],item_id='moss_shard',base_drop_pct=80,minimum=1,maximum=2,level_scaling=True))
    write_csv('fracture_materials.csv',core_materials)
    class_skills=[]
    class_text=(BASE.parent/'CLASS_DESIGN.md').read_text(encoding='utf-8-sig')
    for match in re.finditer(r'^## (Ironvow|Threadseer|Cinderhand|Fenstrider): ([\w]+)[^\n]*\n(.*?)(?=^## |\Z)',class_text,re.M|re.S):
        base,spec,body=match.groups()
        table_rows=[line.strip('| ').split(' | ') for line in body.splitlines() if line.startswith('| ') and not line.startswith('| ---')]
        for cells in table_rows[1:7]:
            if spec=='Turnwarden':
                key,name,timing,effect=cells
                class_skills.append(dict(status='CURRENT_SKILL_PROPOSED_MASTERY',base_class=base,specialization=spec,skill=name,target_geometry='See effect',timing_scaling=timing,effect=effect,presentation='Existing runtime reference'))
            else:
                name,target,timing,effect,presentation=cells
                class_skills.append(dict(status='DESIGN_ONLY_EXISTING_CLASS_DOCUMENT',base_class=base,specialization=spec,skill=name,target_geometry=target,timing_scaling=timing,effect=effect,presentation=presentation))
    write_csv('class_skills.csv',class_skills)
    rules={
        'fixed_user_rules':{'equipment_max_plus':9,'upgrade_failure':'item destroyed, attempt costs consumed','higher_gear_tier':'risk increases','upgrade_visuals':{'7':'blue sparks','8':'red sparks','9':'violet sparks'},'stat_awards_per_completed_level':4,'stats':['VIT','STR','DEX','AGI'],'skill_points_per_level':1,'basic_rank_at_first_mastery':17,'mastery_leaf_source':'destruction of spawn points','mastery_max':'G upon M10'},
        'interpretations':{'quarter_100':'fourth stat point is awarded in the same transaction as the level-up','mastery_costs':'M -> M1 costs 1; M1 -> M2 costs 2; ... M9 -> M10 costs 10; M10 becomes G','two_masteries':'M and G are two mastery tiers, not a two-skill limit','everything_upgradeable':'every equippable weapon, armor piece and accessory, not consumables or loot materials','spark_tier_effect':'colour fixed by plus level, density and ornament intensity scale with gear tier'},
        'proposed_tuning':{'level_cap':LEVEL_CAP,'starting_skill_points':1,'starting_stat_values':{'VIT':10,'STR':10,'DEX':10,'AGI':10},'individual_stat_cap':100,'mastery_learning_chance_pct':100,'wakeglass_upgrade_guarantee':False,'gear_tier_level_thresholds':[1,6,11,16,21],'smithing_chances_pct':CHANCES,'gold_base':GOLD,'gold_tier_multiplier':TIER_GOLD,'power_multiplier':POWER,'roughness':ROUGHNESS,'drop_formula':'max(0,1-ln(1+abs(player_level-mob_level))/ln(1+max(10,(player_level+mob_level)/2)))^2','drop_applies_to':['ordinary item rolls','Fracture core item rolls','repeatable direct leader item rewards','gold'],'drop_does_not_apply_to':['one-time quest rewards'],'xp_formula_current':'600+180*(level-1)+35*(level-1)^2'},
    }
    (TABLES/'design_rules.json').write_text(json.dumps(rules,indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(upgrades)} smithing rows, {len(enemies)} mobs, {len(drops)} item drop rows, {len(gear)} equipment items, {len(class_skills)} class skills.')

if __name__=='__main__':
    build()
