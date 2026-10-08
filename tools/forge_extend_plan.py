from forge_rebuild import ROOT, OUT, atomic
import json
path=OUT/'plan.json';plan=json.loads(path.read_text())
extras=[
 {'key':'hero_ironvow','category':'hero','name':'Ironvow rider','preset':'humanoid','reference':'concepts_docs/art/forge_references/hero_ironvow.png','rig_source':'blender/characters/warden_high.blend','target':'game/assets/characters/warden_high.glb'},
 {'key':'horse_bay','category':'horse','name':'Bay trail horse','preset':'creature','reference':'concepts_docs/art/forge_references/horse_bay.png','rig_source':'blender/mounts/trail_horse.blend','target':'game/assets/mounts/trail_horse.glb'},
 {'key':'tree_pine','category':'environment','name':'Frontier pine','preset':'environment','reference':'concepts_docs/art/forge_references/tree_reference.png','target':'game/assets/world_kit/tree0.glb'},
 {'key':'rock_slate','category':'environment','name':'Mossy slate boulder','preset':'environment','reference':'concepts_docs/art/forge_references/rock_reference.png','target':'game/assets/world_kit/rock0.glb'},
 {'key':'shrub_reference','category':'environment','name':'Bramble shrub','preset':'environment','reference':'concepts_docs/art/forge_references/shrub_reference.png','target':'game/assets/world_kit/shrub.glb','triangle_budget':1600},
 {'key':'fern_reference','category':'environment','name':'Woodland fern','preset':'environment','reference':'concepts_docs/art/forge_references/fern_reference.png','target':'game/assets/world_kit/fern.glb','triangle_budget':900},
 {'key':'house_reference','category':'environment','name':'Frontier house','preset':'environment','reference':'concepts_docs/art/forge_references/house_reference.png','target':'game/assets/forge_rebuild/world/house.glb','dimensions':[4.3,3.9,4.2],'triangle_budget':8000},
 {'key':'npc_keeper','category':'npc','name':'Sella keeper','preset':'humanoid','reference':'concepts_docs/art/forge_references/npc_keeper.png','rig_source':'blender/characters/townfolk_kit.blend','target':'game/assets/forge_rebuild/npcs/keeper.glb','triangle_budget':18000},
 {'key':'dead_tree','category':'environment','name':'Dead pine','preset':'environment','reference':'concepts_docs/art/forge_references/dead_tree.png','target':'game/assets/world_kit/dead_tree.glb','triangle_budget':2200},
 {'key':'fallen_log','category':'environment','name':'Fallen pine log','preset':'environment','reference':'concepts_docs/art/forge_references/fallen_log.png','target':'game/assets/world_kit/log.glb','triangle_budget':1400},
 {'key':'watchtower','category':'environment','name':'Timber watchtower','preset':'environment','reference':'concepts_docs/art/forge_references/watchtower.png','target':'game/assets/world_kit/watchtower.glb','triangle_budget':6000},
 {'key':'npc_smith','category':'npc','name':'Oren blacksmith','preset':'humanoid','reference':'concepts_docs/art/forge_references/npc_smith.png','rig_source':'blender/characters/townfolk_kit.blend','target':'game/assets/forge_rebuild/npcs/smith.glb','triangle_budget':18000},
 {'key':'shrine','category':'environment','name':'Roadside shrine','preset':'environment','reference':'concepts_docs/art/forge_references/shrine.png','target':'game/assets/world_kit/shrine.glb','triangle_budget':4500},
 {'key':'tent','category':'environment','name':'Camp tent','preset':'environment','reference':'concepts_docs/art/forge_references/tent.png','target':'game/assets/world_kit/tent.glb','triangle_budget':2400},
 {'key':'ruin_arch','category':'environment','name':'Ruined stone arch','preset':'environment','reference':'concepts_docs/art/forge_references/ruin_arch.png','target':'game/assets/world_kit/ruin_arch.glb','triangle_budget':4500},
 {'key':'npc_stablemaster','category':'npc','name':'Bram stablemaster','preset':'humanoid','reference':'concepts_docs/art/forge_references/npc_stablemaster.png','rig_source':'blender/characters/townfolk_kit.blend','target':'game/assets/forge_rebuild/npcs/stablemaster.glb','triangle_budget':18000},
 {'key':'grass','category':'environment','name':'Woodland sedge','preset':'environment','reference':'concepts_docs/art/forge_references/grass.png','target':'game/assets/world_kit/grass.glb','triangle_budget':500},
 {'key':'fracture','category':'environment','name':'Briarwake Fracture','preset':'environment','reference':'concepts_docs/art/forge_references/fracture.png','target':'game/assets/benchmark/briarwake.glb','triangle_budget':6500},
 {'key':'coin','category':'environment','name':'Cloud brass coin','preset':'static_prop','reference':'concepts_docs/art/forge_references/coin.png','target':'game/assets/weapons/gold_coin.glb','triangle_budget':1400},
 {'key':'crate','category':'environment','name':'Timber shipping crate','preset':'static_prop','reference':'concepts_docs/art/forge_references/crate.png','target':'game/assets/forge_rebuild/world/crate.glb','dimensions':[.85,.75,.8],'triangle_budget':1200},
 {'key':'bridge','category':'environment','name':'Rope footbridge','preset':'environment','reference':'concepts_docs/art/forge_references/bridge.png','target':'game/assets/forge_rebuild/world/bridge.glb','dimensions':[2.6,6.0,1.6],'triangle_budget':4500},
]
known={e['key'] for e in plan['assets']}
for e in extras:
 if e['key'] in known:
  old=next(x for x in plan['assets'] if x['key']==e['key']);old.update({k:v for k,v in e.items() if k not in ['backend','status']});continue
 e.update(backend='triposr',design='Reconstruct the isolated concept reference. Preserve anatomical silhouette, authored texture, and gameplay rig contracts; inspect all views after fitting.')
 plan['assets'].append(e)
atomic(path,plan)
print('Plan assets:',len(plan['assets']))
