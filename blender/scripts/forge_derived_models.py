"""Replace legacy paths with fitted variants of the new reconstructed geometry."""
import bpy,bmesh,json,sys,math,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('forge_bind',Path(__file__).with_name('forge_bind_export.py'));bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text());entries={e['key']:e for e in plan['assets']}
only=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
static_only='--static-only' in only;only.discard('--static-only')
lineage=json.loads((ROOT/'docs/forge_rebuild/derived_lineage.json').read_text()) if only else []

def fit_variant(source,target,key,tint=None,region=None):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 original=ROOT/'.local/forge_rebuild/baseline'/target
 bpy.ops.import_scene.gltf(filepath=str(original));lo,hi=bridge.bounds([o for o in bpy.context.scene.objects if o.type=='MESH'])
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/source))
 parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for o in parts:
  o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4);o.vertex_groups.clear()
  for mod in list(o.modifiers):o.modifiers.remove(mod)
 if key=='weapon_jade':
  sl,sh=bridge.bounds(parts)
  source_axis=max(range(3),key=lambda i:sh[i]-sl[i]);target_axis=max(range(3),key=lambda i:hi[i]-lo[i])
  if source_axis!=target_axis:
   source_direction=Vector([int(i==source_axis) for i in range(3)])
   target_direction=Vector([int(i==target_axis) for i in range(3)])
   rotation=source_direction.rotation_difference(target_direction).to_matrix().to_4x4()
   for o in parts:o.data.transform(rotation)
 if region:
  source_lo,source_hi=bridge.bounds(parts);height=source_hi.z-source_lo.z
  for o in parts:
   bm=bmesh.new();bm.from_mesh(o.data)
   remove=[f for f in bm.faces if not region((f.calc_center_median().z-source_lo.z)/height,f.calc_center_median())]
   bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free()
  for o in list(parts):
   if not o.data.polygons:bpy.data.objects.remove(o,do_unlink=True);parts.remove(o)
 sl,sh=bridge.bounds(parts)
 for o in parts:
  for v in o.data.vertices:v.co=Vector([(v.co[i]-sl[i])/max(.000001,sh[i]-sl[i])*(hi[i]-lo[i])+lo[i] for i in range(3)])
  o.name='ForgeDerived_'+Path(target).stem
  for mat in o.data.materials:
   if mat and tint:
    shader=mat.node_tree.nodes.get('Principled BSDF')
    if shader:
     texture=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'),None)
     if texture:
      mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1)
      mat.node_tree.links.new(texture.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(mix.outputs[0],shader.inputs['Base Color'])
 for o in list(bpy.data.objects):
  if o not in parts:bpy.data.objects.remove(o,do_unlink=True)
 dst=ROOT/target;dst.parent.mkdir(parents=True,exist_ok=True)
 editable=ROOT/'blender/forge_rebuild/derived'/f'{Path(target).parent.name}_{Path(target).stem}.blend';editable.parent.mkdir(parents=True,exist_ok=True)
 bridge.save_editable(editable)
 bridge.export_runtime(dst,export_animations=False,export_skins=False)
 lineage.append({'target':target,'reconstruction':key,'source':source,'method':'Fitted newly reconstructed geometry to original metric bounds; optional material tint/region extraction.'})
 print('FORGE_DERIVED',target,flush=True)

original=json.loads((ROOT/'docs/forge_rebuild/original_model_inventory.json').read_text())['models'];direct={e['target'] for e in plan['assets']}
for item in original:
 target=item['path']
 if target in direct:continue
 name=Path(target).stem;group=Path(target).parent.name
 if group=='characters' and item['skins'] and name!='townfolk_kit':
  if static_only:continue
  base=entries['mob_young' if name=='briarling' else 'hero_ironvow'];e=dict(base)
  if only and base['key'] not in only:continue
  e.update(key='legacy_'+name,target=target,rig_source='blender/characters/'+name+'.blend',category='mob' if name=='briarling' else 'hero')
  bridge.bind(e);lineage.append({'target':target,'reconstruction':base['key'],'method':'New neural geometry fitted and bound to this legacy model’s original rig/actions.'});continue
 if group=='characters' and name=='townfolk_kit':
  if static_only:continue
  if only and 'npc_smith' not in only:continue
  base=entries['npc_smith'];__import__('shutil').copy2(ROOT/base['target'],ROOT/target)
  lineage.append({'target':target,'reconstruction':base['key'],'method':'Reconstructed full-body fallback with the original 18-bone rig and three idle clips; named residents use their own catalogue scenes.'});continue
 if group=='creatures':
  base=entries[{'wolf':'mob_meadow_wolf','boar':'mob_bristle_boar','spider':'mob_reed_spider','stonekin':'mob_cairn_sentinel','wisp':'mob_grave_wisp'}[name]]
  if only and base['key'] not in only:continue
  __import__('shutil').copy2(ROOT/base['target'],ROOT/target)
  lineage.append({'target':target,'reconstruction':base['key'],'method':'Family fallback uses the rebuilt representative with identical rig contract.'});continue
 source_key=''
 if group in ['world_kit','benchmark']:
  if name.startswith('tree'):source_key='tree_pine'
  elif name.startswith('rock') or name.startswith('cliff'):source_key='rock_slate'
  elif name.startswith('shrub'):source_key='shrub_reference'
  elif name in ['sedge','leaf_litter','grass']:source_key='grass'
  elif name in ['log','fallen_wood']:source_key='fallen_log'
  else:source_key={'fern':'fern_reference','dead_tree':'dead_tree','briarwake':'fracture','shrine':'shrine','watchtower':'watchtower','tent':'tent','ruin_arch':'ruin_arch'}.get(name,'')
 elif group=='weapons' or (group=='characters' and 'sword' in name):source_key='weapon_jade'
 elif name=='warden_insignia':source_key='coin'
 elif name in ['traveler_guard','jade_ironback_mantle']:source_key='hero_ironvow'
 if not source_key:raise ValueError('Unmapped original model: '+target)
 if only and source_key not in only:continue
 base=entries[source_key];region=(lambda z,p:.59<z<.82 and abs(p.x)<.28) if name in ['traveler_guard','jade_ironback_mantle'] else None
 fit_variant(base['target'],target,source_key,region=region)
# Seven further residents use the freshly reconstructed base shapes, retaining
# their existing names, appearance stature, dialogue, items, and idle clips.
for identity,key in [('mara','npc_keeper'),('apothecary','npc_keeper'),('artificer','npc_stablemaster'),('armorer','npc_smith'),('weapons','npc_smith'),('warden','npc_stablemaster'),('ash_scout','npc_stablemaster')]:
 if static_only:continue
 if only and key not in only:continue
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/forge_rebuild/editable'/f'{key}.blend'))
 target=f'game/assets/forge_rebuild/npcs/{identity}.glb';dst=ROOT/target
 bridge.export_runtime(dst,export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True)
 lineage.append({'target':target,'reconstruction':key,'method':'Resident variant of newly reconstructed base character; original gameplay appearance supplies stature.'})
(ROOT/'docs/forge_rebuild/derived_lineage.json').write_text(json.dumps(list({r['target']:r for r in lineage}.values()),indent=2))
