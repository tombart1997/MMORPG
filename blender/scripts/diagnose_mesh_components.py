import bpy,bmesh,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for key in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/prepared'/f'{key}.blend'))
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
        unseen=set(bm.verts);records=[]
        while unseen:
            todo=[unseen.pop()];group=[]
            while todo:
                v=todo.pop();group.append(v)
                for e in v.link_edges:
                    n=e.other_vert(v)
                    if n in unseen:unseen.remove(n);todo.append(n)
            if len(group)>15:
                lo=[min(v.co[i] for v in group) for i in range(3)];hi=[max(v.co[i] for v in group) for i in range(3)]
                records.append({'vertices':len(group),'bounds':[lo,hi]})
        bm.free();print('COMPONENTS',key,json.dumps(sorted(records,key=lambda r:-r['vertices'])[:15]),flush=True)
