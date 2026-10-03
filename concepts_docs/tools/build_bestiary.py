"""Create the full mob design sheet from the recorded resource snapshot."""
from pathlib import Path
import csv
import json
from build_balance import ART

BASE=Path(__file__).resolve().parents[1]

def build():
    data=json.loads((BASE/'tables/project_snapshot.json').read_text(encoding='utf-8'))
    text=['# Mob bestiary — concepts, levels, EXP and drops','',
          '**Current resource baseline:** 37 unique mob IDs across 38 enemy resources. `young_mosslings.tres` aliases `young.tres`; it is not a second creature. Art describes the intended model direction; numerical rows reproduce the current resources. Proposed logarithmic scaling is applied separately.','',
          'Use the [illustrated mob cards](../bestiary.html) for a portrait, stats and full drop list on every creature. [mobs.csv](../tables/mobs.csv) and [mob_drops.csv](../tables/mob_drops.csv) are the editable tables. The source catalogue JSON still contains some older rates: runtime `.tres` drop resources are the baseline here.','',
          '## Threat tiers','',
          '| Tier | Proposed encounter reading |','| --- | --- |','| T1 | Ordinary pack enemy |','| T2 | Stronger pack / dangerous individual |','| T3 | Elite or local leader |','| T4 | Major boss or regional threat |','| T5 | Regional climax / future group variant |','',
          'Tier and level are separate. A level-8 T3 leader can be tougher than a level-9 ordinary creature. The current prototype has no online raid system. Base EXP is not secretly changed by the proposed item-drop function.','',
          '## Concept plates','',
          'Panels are numbered left to right across the top row, then left to right across the bottom. The remaining-variants sheet has four top panels and three bottom panels; all other bestiary sheets use three per row.','']
    for plate in dict.fromkeys(v[0] for v in ART.values()):
        names=[f"{panel}: {next(m['display_name'] for m in data['enemies'] if m['id']==mid)}" for mid,(p,panel,_) in ART.items() if p==plate]
        text += [f"### {plate.removesuffix('.png').replace('bestiary_','').replace('_',' ').title()}",'',f'![Creature production sheet](../art/{plate})','', '; '.join(names)+'.','']
    text+=['## Creature catalogue','',
           'All item rates below are independent, equal-level base chances. Multiply each by the factor in [loot scaling](06_loot_and_level_scaling.md). Several entries can succeed on one kill. Gold is a separate uniformly rolled reward before the proposed multiplier.','',
           'Cinderfall variants deliberately reuse existing drop resources: Ember Hound uses Bloodfang loot, Glass Spider uses Venom Spider loot, Ash Wisp uses Grave Wisp loot, and Rift Sentinel uses Cairn Sentinel loot. Keep those names accurate until distinct loot is authored. Current enemy resources have no configured direct leader reward; old fixture camps may still grant one and must be treated separately.','']
    for m in sorted(data['enemies'],key=lambda m:(m['level'],m['tier'],m['id'])):
        plate,panel,brief=ART[m['id']]
        text += [f"### {m['display_name']} (`{m['id']}`)",'',
                 f"**Level {m['level']} · Tier {m['tier']} · {m['xp']} EXP · {m['maximum_health']:g} HP · Defense {m['defense']:g} · Gold {m['gold_min']}–{m['gold_max']}. Family: {m['family']}.",'',
                 f"Appearance: {brief} [Concept plate, panel {panel}](../art/{plate}).",'',
                 '| Item | Base drop chance | Quantity on successful roll |','| --- | ---: | ---: |']
        for d in m['drops']:
            qty=str(d['min']) if d['min']==d['max'] else f"{d['min']}–{d['max']}"
            text.append(f"| {d['name']} (`{d['item_id']}`) | {100*d['chance']:g}% | {qty} |")
        text += ['',f"Source: `{m['source']}`; drop table `{m['drop_source']}`.",'']
    text += ['## Production notes','',
             'Use shared rigs within a family while preserving the per-creature shape, coat, carapace or stone silhouette shown above. All spiders require eight actual articulated walking legs; overlap in a painted pose must not lead to a six-legged production model. Elite wolves need more than a recolour: neck/shoulder silhouette, scars and attack tells should identify them. Wisps need a physical charm/core with sparse surrounding ribbons.','',
             'Review every model at the ordinary gameplay camera, front/side/three-quarter views and through attack/death states. Existing scalar differences are tuning facts, not final art approval.']
    (BASE/'sheets/05_mob_bestiary.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print('Built complete 37-mob Markdown bestiary.')

if __name__=='__main__':
    build()
