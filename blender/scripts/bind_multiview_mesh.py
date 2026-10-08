"""Fit inspected replacements to preserved gameplay skeletons and actions.

All output surface geometry comes from the new reconstruction or named clean
repairs. Template surfaces are disposable guides and are never exported.
"""
import bpy,bmesh,importlib.util,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).with_name('forge_bind_export.py'))
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
spec=importlib.util.spec_from_file_location('clean_geometry',Path(__file__).with_name('rebuild_clean_sections.py'))
clean_geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(clean_geometry)

def rebuild_boar_legs(parts):
    """Preserve the reconstructed coat; replace fused lower-leg geometry."""
    for o in parts:
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<.51 and v.co.y<.68],context='VERTS')
        bm.to_mesh(o.data);bm.free()
    hide=clean_geometry.material('BoarLowerLegHide',(.09,.072,.050),rough=.93)
    hoof=clean_geometry.material('BoarClovenHoof',(.025,.021,.017),rough=.72)
    made=[]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,location=(0,-.10,.60))
    belly=bpy.context.object;belly.name='CleanBoarBelly';belly.scale=(.30,.66,.17)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    belly.data.materials.append(hide);made.append(belly)
    for station,y in [('Front',.34),('Hind',-.58)]:
        for side,x in [('L',-.22),('R',.22)]:
            tag=station+'.'+side
            points=[(x,y,.72),(x,y,.58),(x,y+(.035 if station=='Front' else -.04),.40),
                (x,y+.035,.28),(x,y,.16),(x,y+.02,.09)]
            o=clean_geometry.tube('CleanLeg_'+tag,points,[.115,.103,.082,.064,.057,.071],hide,12)
            o['clean_leg']=tag;made.append(o)
            for toe in [-1,1]:
                o=clean_geometry.tube('ClovenToe_'+tag+'_'+str(toe),
                    [(x+toe*.035,y+.035,.025),(x+toe*.035,y+.065,.10),(x+toe*.035,y+.025,.13)],
                    [.049,.05,.037],hoof,8)
                o['clean_leg']=tag;made.append(o)
    return made

def rebuild_horse_tail(parts):
    for o in parts:
        bm=bmesh.new();bm.from_mesh(o.data)
        # Tail is a flat pale studio-background ribbon. The hind legs stand
        # outside this narrow centerline, so retain their new native surfaces.
        discard=[v for v in bm.verts if v.co.z<.73 or (abs(v.co.x)<.19 and ((v.co.y<-.91 and v.co.z<1.43) or (v.co.y<-.81 and v.co.z<1.05)))]
        bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(o.data);bm.free()
    hair=clean_geometry.material('BayBlackTail',(.018,.017,.014),rough=.90)
    points=[(0,-.83,1.40),(0,-.96,1.23),(0,-1.03,.93),(.02,-1.08,.60),(.055,-1.17,.29)]
    o=clean_geometry.tube('CleanVolumetricTail',points,[.090,.110,.090,.070,.003],hair,12)
    o['clean_bone']='Tail';made=[o]
    for i in range(9):
        angle=i*math.tau/9
        strands=[Vector(p)+Vector((math.cos(angle)*r,math.sin(angle)*r*.28,0)) for p,r in zip(points,[.086,.106,.085,.067,.016])]
        o=clean_geometry.tube('TailHairStrand',strands,[.013,.013,.011,.010,.001],hair,5)
        o['clean_bone']='Tail';made.append(o)
    hoof=clean_geometry.material('BayCleanHoof',(.075,.069,.049),rough=.83)
    for side in [-1,1]:
        for front in [True,False]:
            points=[(side*.16,.39,.80),(side*.17,.42,.62),(side*.22,.55,.37),(side*.25,.64,.19),(side*.266,.67,.11)] if front else [(side*.23,-.65,.80),(side*.24,-.73,.62),(side*.26,-.80,.38),(side*.266,-.81,.19),(side*.266,-.79,.11)]
            made.append(clean_geometry.tube('CleanHorseLowerLeg',points,[.072,.055,.043,.047,.060],hair,12))
            x,y,_=points[-1]
            made.append(clean_geometry.tube('CleanHorseHoof',[(x,y+.015,.012),(x,y+.012,.070),(x,y,.13)],[.075,.071,.052],hoof,12))
    return made

def hand_regions(mesh,cutoff=1.23,threshold=.23,min_height=.60):
    """Separate dangling hands from the connected skirt below the elbows."""
    # Reposing an A-pose brings wrists inward to 0.25–0.34 m. The previous
    # 0.35 m threshold missed both hands and assigned them to the coat/pelvis.
    eligible={v.index for v in mesh.vertices if v.co.z<cutoff}
    adjacent={i:[] for i in eligible}
    for edge in mesh.edges:
        a,b=edge.vertices
        if a in eligible and b in eligible:adjacent[a].append(b);adjacent[b].append(a)
    owners={}
    while eligible:
        todo=[eligible.pop()];indices=[]
        while todo:
            i=todo.pop();indices.append(i)
            for n in adjacent[i]:
                if n in eligible:eligible.remove(n);todo.append(n)
        if len(indices)<15:continue
        center=sum((mesh.vertices[i].co for i in indices),Vector())/len(indices)
        if abs(center.x)>threshold and center.z>min_height:
            for i in indices:owners[i]='R' if center.x>0 else 'L'
    return owners

def rebuild_bandit_arms(parts,rig):
    """Replace generated cuff loops; keep the new body, cloak and hands."""
    for o in parts:
        regions=hand_regions(o.data)
        retained=set()
        for side in ['L','R']:
            fingers=[v for v in o.data.vertices if regions.get(v.index)==side and v.co.z<1.03]
            if not fingers:continue
            retained.update(v.index for v in fingers)
            center=sum((v.co for v in fingers),Vector())/len(fingers)
            target=rig.data.bones['Hand.'+side].head_local+Vector((0,.02,-.035))
            for v in fingers:v.co+=target-center
        # Save ownership before deleting; reconstruct sleeves over the actual
        # rig segments instead of transferring the hollow neural cuffs.
        bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
        discard=[v for v in bm.verts if v.index not in retained and
            (v.index in regions or (1.03<v.co.z<1.50 and abs(v.co.x)>.27))]
        bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(o.data);bm.free()
    cloth=clean_geometry.material('BanditCleanSleeve',(.052,.043,.033),rough=.94)
    leather=clean_geometry.material('BanditLeatherBracer',(.095,.057,.030),rough=.76)
    made=[]
    for side in ['L','R']:
        for name,mat,radii in [('UpperArm',cloth,[.087,.093,.077,.067]),('Forearm',leather,[.073,.075,.058,.045])]:
            bone=rig.data.bones[name+'.'+side];a=bone.head_local;b=bone.tail_local
            o=clean_geometry.tube('CleanBandit'+name+'.'+side,[a,a.lerp(b,.28),a.lerp(b,.78),b],radii,mat,12)
            o['clean_bone']=name+'.'+side;made.append(o)
    return made

def constrain_weights(o,rig,family):
    names={g.index:g.name for g in o.vertex_groups}
    groups={g.name:g for g in o.vertex_groups}
    owners={}
    hands=hand_regions(o.data) if family in ['humanoid','bandit'] else hand_regions(o.data,.68,.30,.20) if family=='mossling' else hand_regions(o.data,1.25,.55,.35) if family=='stonekin' else {}
    if family in ['wolf','boar']:
        # Identify disconnected lower extremities in topology, so the hanging
        # tail cannot share a coordinate rule with the inner edge of a rear paw.
        eligible={v.index for v in o.data.vertices if v.co.z<(.24 if family=='boar' else .46)}
        adjacent_low={i:[] for i in eligible}
        for edge in o.data.edges:
            a,b=edge.vertices
            if a in eligible and b in eligible:adjacent_low[a].append(b);adjacent_low[b].append(a)
        components=[]
        while eligible:
            todo=[eligible.pop()];indices=[]
            while todo:
                index=todo.pop();indices.append(index)
                for n in adjacent_low[index]:
                    if n in eligible:eligible.remove(n);todo.append(n)
            if len(indices)>25:
                center=sum((o.data.vertices[i].co for i in indices),Vector())/len(indices)
                components.append((indices,center))
        components.sort(key=lambda pair:len(pair[0]),reverse=True)
        main=components[:(4 if family=='boar' else 5)]
        tail=min(main,key=lambda pair:pair[1].y) if main else None
        centers={}
        for indices,center in main:
            tag='Tail' if family=='wolf' and indices is tail[0] and abs(center.x)<.16 else ('Front' if center.y>0 else 'Hind')+'.'+('R' if center.x>0 else 'L')
            centers[tag]=center
            for i in indices:owners[i]=tag
        print('LIMB_REGIONS',family,[(tag,list(c)) for tag,c in centers.items()],flush=True)
        # Extend the observed component ownership toward the upper calves.
        for v in o.data.vertices:
            if v.index not in owners and v.co.z<.70 and centers:
                owners[v.index]=min(centers,key=lambda tag:(v.co.xy-centers[tag].xy).length_squared)
    for v in o.data.vertices:
        p=v.co;side='R' if p.x>=0 else 'L';weights=None
        if family in ['wolf','boar'] and owners.get(v.index)=='Tail':
            weights={'Tail':1}
        elif family=='boar':
            tag=owners.get(v.index)
            if p.y>.68:weights={'Head':1}
            elif tag and (p.z<.40 or (p.z<.62 and (p.xy-centers[tag].xy).length<.19)):
                station,side=tag.split('.')
                lower=station+'Lower.'+side;upper=station+'Upper.'+side
                joint=rig.data.bones[lower].head_local.z
                t=max(0,min(1,(p.z-joint+.07)/.22));t=t*t*(3-2*t)
                weights={lower:1-t,upper:t}
            elif p.y<-.90:weights={'Tail':1}
            elif p.y>.55:
                t=max(0,min(1,(p.y-.55)/.25));weights={'Chest':1-t,'Head':t}
            else:
                t=max(0,min(1,(p.y+.30)/.60));weights={'Hips':1-t,'Chest':t}
        elif family=='horse' and p.z<1.12 and abs(p.x)>.07:
            tag=('Fore' if p.y>-.20 else 'Hind')+'.'+side
            # Each observed leg stays on its own chain, including disconnected
            # atlas pieces at the hoof. The old guide has a wider chest.
            levels=[(.18,'Hoof'),(.49,'Ankle'),(.88,'Lower'),(1.12,'Upper')]
            weights={tag+'.Upper':1}
            for j,(height,bone) in enumerate(levels):
                if p.z<=height:
                    if j==0:weights={tag+'.Hoof':1}
                    else:
                        lower_height,lower_bone=levels[j-1]
                        t=max(0,min(1,(p.z-lower_height)/(height-lower_height)));t=t*t*(3-2*t)
                        weights={tag+'.'+lower_bone:1-t,tag+'.'+bone:t}
                    break
            t=max(0,min(1,(p.z-.84)/.28));t=t*t*(3-2*t)
            weights={n:w*(1-t) for n,w in weights.items()};weights['Body']=t
        elif family=='stonekin':
            if v.index in hands:
                side=hands[v.index]
                t=max(0,min(1,(p.z-.72)/.27));t=t*t*(3-2*t)
                weights={'Hand.'+side:1-t,'Forearm.'+side:t}
                u=max(0,min(1,(p.z-1.03)/.24));u=u*u*(3-2*u)
                weights={n:w*(1-u) for n,w in weights.items()};weights['UpperArm.'+side]=u
            elif p.z<.85:
                t=max(0,min(1,(p.z-.13)/.20));t=t*t*(3-2*t)
                u=max(0,min(1,(p.z-.34)/.28));u=u*u*(3-2*u)
                weights={'Foot.'+side:(1-t)*(1-u),'Shin.'+side:t*(1-u),'Thigh.'+side:u}
                h=max(0,min(1,(p.z-.62)/.23));weights={n:w*(1-h) for n,w in weights.items()};weights['Hips']=h
            else:
                # Broad new shoulders must not follow the narrow guide's head.
                arm=max(0,min(1,(abs(p.x)-.28)/.19));arm=arm*arm*(3-2*arm)
                head=max(0,min(1,(p.z-1.62)/.14))*max(0,min(1,(.29-abs(p.x))/.10))
                weights={'UpperArm.'+side:arm,'Head':head,'Chest':1-arm-head}
        elif v.index in hands:
            side=hands[v.index]
            if p.z<(.55 if family=='mossling' else 1.03):
                weights={'Hand.'+side:1}
            else:
                weights={'Forearm.'+side:1}
        elif family in ['humanoid','bandit'] and 1.20<p.z<1.50 and abs(p.x)>.27:
            # Upper sleeves must follow the shoulder/elbow chain, including
            # the section above the topology cut used to separate dangling
            # hands. Treating this section as coat fabric splits the sleeve
            # when the forearm rises.
            arm=max(0,min(1,(abs(p.x)-.27)/.065));arm=arm*arm*(3-2*arm)
            upper=max(0,min(1,(p.z-1.20)/.10));upper=upper*upper*(3-2*upper)
            weights={'UpperArm.'+side:arm*upper,'Forearm.'+side:arm*(1-upper),'Chest':1-arm}
        elif family in ['humanoid','bandit'] and p.z<.68 and p.y>-.19 and abs(p.x)>.03:
            # Calves inside the skirt slit belong to the knee chain, never Hips.
            if p.z<.25:
                t=max(0,min(1,(p.z-.10)/.15));weights={'Foot.'+side:1-t,'Shin.'+side:t}
            else:
                t=max(0,min(1,(p.z-.40)/.28));t=t*t*(3-2*t)
                weights={'Shin.'+side:1-t,'Thigh.'+side:t}
            calf=max(0,min(1,(p.y+.19)/.12))*max(0,min(1,(abs(p.x)-.03)/.10))*max(0,min(1,(.68-p.z)/.13))
            calf=calf*calf*(3-2*calf)
            skirt=max(0,min(1,(abs(p.x)-.08)/.20))
            weights={n:w*calf for n,w in weights.items()}
            weights['Thigh.'+side]=weights.get('Thigh.'+side,0)+(1-calf)*skirt
            weights['Hips']=(1-calf)*(1-skirt)
        elif family in ['humanoid','bandit'] and .25<p.z<1.30:
            # Native coat panels occupy the old guide's empty space beside the
            # hands. Nearest-neighbour skin transfer alone assigns them to the
            # fingers, producing a large fan during idle and attacks.
            t=max(0,min(1,(p.z-.87)/.20))
            lateral=max(0,min(1,(abs(p.x)-.08)/.20))
            if p.z<1.07:weights={'Thigh.'+side:(1-t)*lateral,'Hips':1-(1-t)*lateral}
            else:
                t=max(0,min(1,(p.z-1.06)/.25));weights={'Hips':1-t,'Spine':t}
        elif family in ['wolf','boar'] and p.z<.67 and abs(p.x)>.08:
            tag=owners.get(v.index)
            if not tag or tag=='Tail':continue
            station,side=tag.split('.')
            lower=station+'Lower.'+side;upper=station+'Upper.'+side
            old={names[g.group]:g.weight for g in v.groups}
            if p.y<-.80 and old.get('Tail',0)>.35:continue
            limb=sum(w for n,w in old.items() if 'Upper.' in n or 'Lower.' in n)
            if p.z>.42 and limb<.35:continue
            joint=rig.data.bones[lower].head_local.z
            t=max(0,min(1,(p.z-joint+.07)/.22));t=t*t*(3-2*t)
            weights={lower:1-t,upper:t}
        elif family in ['humanoid','bandit','mossling','stonekin'] and p.z<.35:
            foot='Foot.'+side;shin='Shin.'+side
            if foot not in groups:continue
            t=max(0,min(1,(p.z-.13)/.18));t=t*t*(3-2*t)
            weights={foot:1-t,shin:t}
        if weights:
            for g in o.vertex_groups:g.remove([v.index])
            for n,w in weights.items():
                if w>1e-6:groups[n].add([v.index],w,'REPLACE')
    # Smooth locally over topology; no mixing between disconnected limbs.
    adjacent=[set() for _ in o.data.vertices]
    for e in o.data.edges:
        a,b=e.vertices;adjacent[a].add(b);adjacent[b].add(a)
    fields=[{g.group:g.weight for g in v.groups} for v in o.data.vertices]
    for iteration in range(10):
        out=[]
        for v in o.data.vertices:
            if not adjacent[v.index]:out.append(fields[v.index]);continue
            acc={g:w*.65 for g,w in fields[v.index].items()}
            for n in adjacent[v.index]:
                for g,w in fields[n].items():acc[g]=acc.get(g,0)+w*.35/len(adjacent[v.index])
            top=sorted(acc.items(),key=lambda pair:-pair[1])[:4];total=sum(w for _,w in top)
            out.append({g:w/total for g,w in top})
        fields=out
    for v in o.data.vertices:
        for g in o.vertex_groups:g.remove([v.index])
        for index,w in fields[v.index].items():o.vertex_groups[index].add([v.index],w,'REPLACE')
    # Fingers and tail tips stay rigid within their owning bone. Smoothing at
    # nearby clothing boundaries must not pull extremities toward unrelated joints.
    for v in o.data.vertices:
        p=v.co;owner=None
        if v.index in hands and p.z<(.53 if family=='mossling' else .70 if family=='stonekin' else 1.01):owner='Hand.'+hands[v.index]
        if family=='horse' and p.z<.16 and abs(p.x)>.07:owner=('Fore' if p.y>-.20 else 'Hind')+'.'+('R' if p.x>0 else 'L')+'.Hoof'
        if family in ['wolf','boar'] and owners.get(v.index)=='Tail':owner='Tail'
        if owner:
            for g in o.vertex_groups:g.remove([v.index])
            groups[owner].add([v.index],1,'REPLACE')

def bind(e):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/e['rig_source']))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
    if e.get('family')=='stonekin':
        # The reconstructed giant has longer arms and a higher shoulder than
        # the old sparse guide. Fit joint centers before skinning, preserving
        # the named skeleton and its local rotation clips.
        bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
        for side,sign in [('L',-1),('R',1)]:
            for name,head,tail in [
                ('UpperArm',(sign*.50,0,1.45),(sign*.72,.02,1.00)),
                ('Forearm',(sign*.72,.02,1.00),(sign*.76,.02,.65)),
                ('Hand',(sign*.76,.02,.65),(sign*.76,.09,.55))]:
                bone=rig.data.edit_bones[name+'.'+side];bone.head=head;bone.tail=tail
        for name,head,tail in [('Spine',(0,-.06,.88),(0,0,1.24)),('Chest',(0,0,1.24),(0,0,1.55)),('Neck',(0,0,1.55),(0,0,1.69)),('Head',(0,0,1.69),(0,0,1.87))]:
            bone=rig.data.edit_bones[name];bone.head=head;bone.tail=tail
        bpy.ops.object.mode_set(mode='OBJECT')
    old=[o for o in bpy.context.scene.objects if o.type=='MESH']
    if e.get('binding_guide'):
        samples=json.loads((ROOT/e['binding_guide']).read_text())['samples']
        records=[(Vector(point),weights) for point,weights in samples]
        tree=KDTree(len(records))
        for i,(point,_) in enumerate(records):tree.insert(point,i)
        tree.balance();guide=(tree,records)
    else:guide=bridge.weights_guide(old,rig)
    before=set(bpy.data.objects)
    if e['source'].endswith('.blend'):
        with bpy.data.libraries.load(e['source'],link=False) as (src,dst):
            dst.objects=list(src.objects)
        for o in dst.objects:
            if o:bpy.context.collection.objects.link(o)
        bpy.context.view_layer.update()
    else:bpy.ops.import_scene.gltf(filepath=e['source'])
    parts=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    bake_source=None
    assert parts
    for o in parts:
        o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
        o.data.transform(Matrix.Rotation(math.radians(e.get('yaw',0)),4,'Z'))
    lo,hi=bridge.bounds(parts)
    factor=e.get('height',1.90)/max(.00001,hi.z-lo.z)
    center=(lo+hi)*.5
    for o in parts:
        for v in o.data.vertices:
            v.co=Vector(((v.co.x-center.x)*factor,(v.co.y-center.y)*factor,(v.co.z-lo.z)*factor+.006))
        o.name='MV_'+e['key']
        if e.get('family')=='boar':
            bake_source=o.copy();bake_source.data=o.data.copy();bake_source.parent=None
            bpy.context.collection.objects.link(bake_source);bake_source.name='RetainedNativeBoarColorSource'
        # GLB import splits points at atlas seams; topology regions must see
        # the underlying connected surface, while per-corner UVs are retained.
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
        if e['key'] in ['keeper','blacksmith','stablemaster']:
            unseen=set(bm.verts);discard=[]
            while unseen:
                todo=[unseen.pop()];component=[]
                while todo:
                    v=todo.pop();component.append(v)
                    for edge in v.link_edges:
                        n=edge.other_vert(v)
                        if n in unseen:unseen.remove(n);todo.append(n)
                low=Vector([min(v.co[i] for v in component) for i in range(3)])
                high=Vector([max(v.co[i] for v in component) for i in range(3)])
                center=(low+high)*.5
                if abs(center.x)>.46 and high.z-low.z>.24 and min(high.x-low.x,high.y-low.y)<.055:discard.extend(component)
                elif len(component)<25 and high.z<.10:discard.extend(component)
            bmesh.ops.delete(bm,geom=discard,context='VERTS')
            floor=[f for f in bm.faces if max(v.co.z for v in f.verts)<.035 and abs(f.normal.z)>.78]
            bmesh.ops.delete(bm,geom=floor,context='FACES')
        if e.get('family')=='mossling':
            unseen=set(bm.verts);discard=[]
            while unseen:
                todo=[unseen.pop()];component=[]
                while todo:
                    v=todo.pop();component.append(v)
                    for edge in v.link_edges:
                        n=edge.other_vert(v)
                        if n in unseen:unseen.remove(n);todo.append(n)
                if max(v.co.z for v in component)<.09 and (len(component)<60 or max(v.co.z for v in component)-min(v.co.z for v in component)<.025):discard.extend(component)
            bmesh.ops.delete(bm,geom=discard,context='VERTS')
            # Painted studio floor attached to roots is not anatomical geometry.
            floor_faces=[f for f in bm.faces if max(v.co.z for v in f.verts)<.04 and abs(f.normal.z)>.45 and abs(f.calc_center_median().x)>.42]
            bmesh.ops.delete(bm,geom=floor_faces,context='FACES')
        if e.get('family')=='boar':
            # The reconstruction contains a thin false surface connecting the
            # four legs across empty air. Preserve paws, torso, tusks and tail.
            discard=[v for v in bm.verts if v.co.z<.46 and abs(v.co.x)<.12 and -.88<v.co.y<.70]
            bmesh.ops.delete(bm,geom=discard,context='VERTS')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    if e.get('arm_repose_degrees'):
        for o in parts:
            hands=hand_regions(o.data)
            for v in o.data.vertices:
                p=v.co;side=1 if p.x>0 else -1
                if v.index in hands or (1.23<=p.z<1.50 and abs(p.x)>.29):
                    anchor=Vector((side*.28,0,1.45))
                    blend=min(1,max(0,(abs(p.x)-.29)/.09))
                    turn=Matrix.Rotation(math.radians(e['arm_repose_degrees']*side*blend),3,'Y')
                    v.co=anchor+turn@(p-anchor)
    if e.get('family')=='boar':parts.extend(rebuild_boar_legs(parts))
    if e.get('family')=='horse':parts.extend(rebuild_horse_tail(parts))
    if e.get('family')=='bandit':parts.extend(rebuild_bandit_arms(parts,rig))
    # Surfaces on either side of a skirt slit must follow their own thigh.
    for o in parts:
        bridge.apply_weights(o,rig,*guide)
        if o.get('clean_bone'):
            for g in o.vertex_groups:g.remove(list(range(len(o.data.vertices))))
            o.vertex_groups[o['clean_bone']].add(list(range(len(o.data.vertices))),1,'REPLACE')
        elif o.get('clean_leg'):
            station,side=o['clean_leg'].split('.')
            lower=station+'Lower.'+side;upper=station+'Upper.'+side
            for v in o.data.vertices:
                t=max(0,min(1,(v.co.z-.28)/.20));t=t*t*(3-2*t)
                for g in o.vertex_groups:g.remove([v.index])
                if t>0:o.vertex_groups[upper].add([v.index],t,'REPLACE')
                if t<1:o.vertex_groups[lower].add([v.index],1-t,'REPLACE')
        else:constrain_weights(o,rig,e.get('family','humanoid'))
        o.data.validate(clean_customdata=False)
        if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        for f in o.data.polygons:f.use_smooth=True
    for o in old:bpy.data.objects.remove(o,do_unlink=True)
    for o in list(bpy.data.objects):
        if o not in parts and o!=rig and o!=bake_source:bpy.data.objects.remove(o,do_unlink=True)
    if len(parts)>1:
        # Keep a single skinned mesh with shared material surfaces per actor.
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
        parts=[bpy.context.object];parts[0].name='MV_'+e['key']
    if bake_source:
        # Transfer the actual new reconstruction's coat onto the remodeled
        # legs. Uniform flat patches are visibly inconsistent with the body.
        spec=importlib.util.spec_from_file_location('forge_optimizer',Path('C:/Users/Tom/Documents/2D_to_3D/blender/optimize.py'))
        optimizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(optimizer)
        optimizer.bake_materials(bake_source,parts[0],1024,normal_map=True)
        bpy.data.objects.remove(bake_source,do_unlink=True)
    rig.data.pose_position='POSE';bpy.context.scene.frame_set(0)
    bpy.context.preferences.filepaths.save_version=0
    source=ROOT/'blender/multiview_rebuild/rigged'/f"{e['key']}.blend"
    source.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    runtime=ROOT/'game/assets/generated'/f"{e['key']}.glb";runtime.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(runtime),export_format='GLB',export_yup=True,
        export_animations=True,export_skins=True,export_animation_mode='NLA_TRACKS',
        export_force_sampling=True,export_frame_range=False,export_extras=True)
    report={**e,'output':str(runtime),'bounds':[list(v) for v in bridge.bounds(parts)],
        'bones':len(rig.data.bones),'clips':[t.name for t in rig.animation_data.nla_tracks],
        'template_geometry_exported':False,'review_status':'requires_deformation_review'}
    if e.get('family')=='boar':report['repair']='Reconstructed upper coat retained; fused lower legs removed and four continuous tapered legs with cloven hooves remodeled and skinned from scratch.'
    (ROOT/'docs/full_asset_rebuild'/f"{e['key']}_rig.json").write_text(json.dumps(report,indent=2))
    print('RIGGED',e['key'],len(rig.data.bones),flush=True)

if __name__=='__main__':
    request=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
    for e in request['assets']:bind(e)
