"""Locate long deformation seams in exported asset authoring sources."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for key in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/rigged'/f'{key}.blend'))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    result=[]
    for clip in ['run','attack_01','hit','death','canter','trot']:
        track=next((t for t in rig.animation_data.nla_tracks if t.name==clip),None)
        if track is None:continue
        strip=track.strips[0]
        for t in rig.animation_data.nla_tracks:t.mute=True
        rig.animation_data.action=strip.action
        if hasattr(strip,'action_slot'):rig.animation_data.action_slot=strip.action_slot
        for fraction in [.25,.75]:
            bpy.context.scene.frame_set(int(strip.frame_start+(strip.frame_end-strip.frame_start)*fraction))
            graph=bpy.context.evaluated_depsgraph_get();worst=[]
            for o in meshes:
                evaluated=o.evaluated_get(graph).to_mesh()
                names={g.index:g.name for g in o.vertex_groups}
                for edge in o.data.edges:
                    a,b=edge.vertices;base=(o.data.vertices[a].co-o.data.vertices[b].co).length
                    posed=(evaluated.vertices[a].co-evaluated.vertices[b].co).length
                    if base>.002 and posed>max(.05,base*2.5):
                        worst.append({'ratio':posed/base,'length':posed,'points':[list(o.data.vertices[i].co) for i in [a,b]],
                            'weights':[{names[g.group]:round(g.weight,3) for g in o.data.vertices[i].groups} for i in [a,b]]})
                o.evaluated_get(graph).to_mesh_clear()
            worst.sort(key=lambda e:-e['ratio'])
            result.append({'clip':clip,'fraction':fraction,'stretched_edges':len(worst),'worst':worst[:5]})
    (ROOT/'docs/full_asset_rebuild'/f'{key}_deformation.json').write_text(json.dumps(result,indent=2))
    print('DEFORMATION',key,json.dumps(result[:2]),flush=True)
    if key=='ironhide_boar':print('REST_BONES',[(b.name,list(b.head_local),list(b.tail_local)) for b in rig.data.bones],flush=True)
