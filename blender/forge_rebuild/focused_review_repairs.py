"""One recorded Codex-assisted pass on diagnosed regions, not a generic remesher."""
import bpy,bmesh,sys,json,math,time
from pathlib import Path
from mathutils import Vector
FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D');sys.path.insert(0,str(FORGE/'blender'))
from diagnose import load_source,audit
from pipeline import export,verify_clip_timing
ROOT=Path(r'D:\Games\Metin2Clone');OUT=ROOT/'docs/asset_review/benchmarks'


def material(name,color,texture=None):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.84
    if texture:
        image=bpy.data.images.load(str(texture),check_existing=True);image.pack()
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
    return mat


def beam(name,a,b,width,depth,mat):
    a,b=Vector(a),Vector(b);length=(b-a).length
    bpy.ops.mesh.primitive_cube_add(size=1,location=(a+b)*.5);o=bpy.context.object;o.name=name
    o.dimensions=(width,depth,length);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    bevel=o.modifiers.new('Small timber bevel','BEVEL');bevel.width=.012;bevel.segments=1
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o


def boar():
    key='mob_ironhide_boar';source=ROOT/'game/assets/forge_rebuild/mobs/ironhide_boar.glb';load_source(source)
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Forge_'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    names=[b.name for b in arm.data.bones];oldweights={v.index:[(obj.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in obj.data.vertices}
    obj.vertex_groups.clear();groups={n:obj.vertex_groups.new(name=n) for n in names}
    count=0
    for v in obj.data.vertices:
        x,y,z=v.co
        # Preserve head/ruff as rigid head + chest surfaces; limb weights are
        # confined below shoulder height. Source body detail stays unchanged.
        chest=max(0,min(1,(y+.35)/.7));weights={'Chest':chest,'Hips':1-chest}
        if y>.53 and z>.47:
            head=max(0,min(1,(y-.53)/.20));weights={n:w*(1-head) for n,w in weights.items()};weights['Head']=head
        if y<-.88 and z>.66:
            tail=max(0,min(.9,(-y-.88)/.25));weights={n:w*(1-tail) for n,w in weights.items()};weights['Tail']=tail
        if z<.70 and abs(x)>.10:
            limb=max(0,min(1,(.70-z)/.23));side='L' if x<0 else 'R';pair='Front' if y>.04 else 'Hind'
            lower=max(0,min(1,(.43-z)/.22));weights={n:w*(1-limb) for n,w in weights.items()}
            weights[pair+'Upper.'+side]=limb*(1-lower);weights[pair+'Lower.'+side]=limb*lower
        weights={n:w for n,w in weights.items() if w>.00001};weights=dict(sorted(weights.items(),key=lambda t:-t[1])[:4]);total=sum(weights.values())
        for n,w in weights.items():groups[n].add([v.index],w/total,'REPLACE')
        count+=1
    return key,source,{'focus':'Correct broad torso/spine vertices influenced by moving leg bones; preserve geometry, UVs, materials, skeleton and clips.',
        'vertices_reweighted':count,'previous_weights_preserved_in_source':True,'requires_review':'Joint positions remain the existing game skeleton; no claim of artist-authored topology.'}


def tower():
    key='watchtower';source=ROOT/'game/assets/world_kit/watchtower.glb';load_source(source)
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');original=len(obj.data.polygons)
    # Keep the distinctive reconstructed roof and balcony. Remove deformed
    # lower structure and corner posts, then rebuild only those timber regions.
    bm=bmesh.new();bm.from_mesh(obj.data)
    delete=[]
    for f in bm.faces:
        center=f.calc_center_median()
        corner=abs(abs(center.x)-1.3)<.35 and abs(abs(center.y)-1.15)<.38 and center.z<6.65
        if center.z<4.25 or corner:delete.append(f)
    bmesh.ops.delete(bm,geom=delete,context='FACES');bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    loose=[v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm,geom=loose,context='VERTS');bm.to_mesh(obj.data);bm.free()
    wood=material('RepairTimber',(.28,.16,.075),ROOT/'game/assets/world_kit/watchtower_Deadwood_albedo.png')
    stone=material('RepairStone',(.29,.30,.28))
    for x in [-1.3,1.3]:
        for y in [-1.15,1.15]:
            beam('Straight_support', (x,y,.35),(x,y,6.6),.23,.23,wood)
            beam('Stone_foot',(x,y,.04),(x,y,.42),.57,.57,stone)
    for y in [-1.15,1.15]:
        beam('Platform_crossbeam',(-1.4,y,4.3),(1.4,y,4.3),.22,.22,wood)
        beam('Brace',(-1.3,y,.7),(1.3,y,3.5),.12,.12,wood)
    for x in [-1.3,1.3]:
        beam('Side_crossbeam',(x,-1.3,4.3),(x,1.3,4.3),.22,.22,wood)
        beam('Side_brace',(x,-1.15,.7),(x,1.15,3.5),.12,.12,wood)
    for x in [1.12,1.82]:beam('Ladder_rail',(x,-2.1,.18),(x,-1.0,4.5),.11,.11,wood)
    for i in range(14):
        t=(i+1)/15;y=-2.1+1.1*t;z=.18+4.32*t
        beam('Ladder_rung',(1.1,y,z),(1.84,y,z),.085,.085,wood)
    return key,source,{'focus':'Rebuild four straight supports, stone feet, braces and a readable ladder; retain source roof, balcony and their textures.',
        'source_faces':original,'retained_faces':len(obj.data.polygons),'deleted_region':'lower structure and corner posts only','manual_passes':1}


def fern():
    key='fern_reference';source=ROOT/'game/assets/world_kit/fern.glb';load_source(source)
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    bm=bmesh.new();bm.from_mesh(obj.data)
    # Retain the central reconstructed root crown; replace fused outer fronds.
    delete=[f for f in bm.faces if f.calc_center_median().z>.15 or f.calc_center_median().xy.length>.17]
    bmesh.ops.delete(bm,geom=delete,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
    leaf=material('RepairFernLeaf',(.12,.27,.06),ROOT/'game/assets/world_kit/fern_UnderstoryLeaves_albedo.png')
    leaf.surface_render_method='DITHERED';leaf.use_backface_culling=False
    stem=material('RepairFernStem',(.17,.21,.055));vertices=[];faces=[];uvs=[]
    for frond in range(8):
        angle=frond*math.tau/8+.17;direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-direction.y,direction.x,0));length=.58 if frond%3 else .44
        def center(t):return direction*(length*t)+Vector((0,0,.11+(.44 if frond%3 else .56)*math.sin(t*math.pi*.73)))
        prior=center(0)
        for segment in range(1,9):
            current=center(segment/8);beam('Fern_rachis',prior,current,.008,.008,stem);prior=current
        for n in range(1,13):
            t=n/14;base=center(t);span=.10*(1-t)*(.7+math.sin(t*math.pi))
            for sign in [-1,1]:
                tip=base+side*(sign*span)+direction*.042+Vector((0,0,-.01))
                mid=base.lerp(tip,.48)+Vector((0,0,.012));w=.017*(1-t*.65)
                offset=len(vertices);vertices.extend([base,mid-direction*w,tip,mid+direction*w,mid+Vector((0,0,.01))])
                faces.extend([(offset,offset+1,offset+4),(offset+1,offset+2,offset+4),(offset+2,offset+3,offset+4),(offset+3,offset,offset+4)])
    mesh=bpy.data.meshes.new('Separated_leaflets');mesh.from_pydata(vertices,[],faces);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        for loop in p.loop_indices:
            v=mesh.vertices[mesh.loops[loop].vertex_index].co;uv.data[loop].uv=(v.x*.7+.5,v.y*.7+.5)
    leaves=bpy.data.objects.new('Separated_fern_leaflets',mesh);bpy.context.scene.collection.objects.link(leaves);mesh.materials.append(leaf)
    return key,source,{'focus':'Retain root crown; replace fused leaf masses with eight curved fronds and distinct paired leaflets. Reuse retained leaf atlas.',
        'new_leaflets':8*12*2,'manual_passes':1,'remaining':'Small background foliage, not a hero botanical scan.'}


def main():
    selection=sys.argv[sys.argv.index('--')+1:]
    for fn in [boar,tower,fern]:
        if selection and fn.__name__ not in selection:continue
        start=time.monotonic();key,source,notes=fn();out=OUT/key/'assisted';out.mkdir(parents=True,exist_ok=True)
        for image in bpy.data.images:
            if image.has_data and image.source=='FILE':image.pack()
        for obj in bpy.context.scene.objects:
            if obj.type=='ARMATURE':obj.data.pose_position='POSE'
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'focused.blend'));export(out/'focused.glb')
        contract=verify_clip_timing(source,out/'focused.glb');(out/'animation_contract.json').write_text(json.dumps(contract,indent=2))
        notes.update(seconds=round(time.monotonic()-start,3),cost_credits=0,source=str(source),review='pending')
        (out/'modification.json').write_text(json.dumps(notes,indent=2));(out/'mesh_after.json').write_text(json.dumps(audit(),indent=2));print('FOCUSED_PASS',key,notes['seconds'],flush=True)


if __name__=='__main__':main()
