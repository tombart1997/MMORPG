"""Curated local static repairs. Explicit regions; no semantic part inference."""
import bpy,bmesh,math
from mathutils import Vector


def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.88
    return m


def mesh_object(name,vertices,faces,mat):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        for i in p.loop_indices:
            v=mesh.vertices[mesh.loops[i].vertex_index].co;uv.data[i].uv=(v.x*.5+.5,v.z*.5+.5)
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(mat);return obj


def beam(name,a,b,width,mat):
    a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=axis.cross(Vector((0,0,1)))
    if side.length<.01:side=Vector((1,0,0))
    side.normalize();up=axis.cross(side).normalized();vertices=[]
    for center in [a,b]:
        for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:vertices.append(center+side*x*width*.5+up*y*width*.5)
    return mesh_object(name,vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)


def remove_region(obj,predicate):
    bm=bmesh.new();bm.from_mesh(obj.data);faces=[f for f in bm.faces if predicate(f.calc_center_median())]
    bmesh.ops.delete(bm,geom=faces,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()


def join(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=active;bpy.ops.object.join()
    # One mesh, shared material slots. Repeated scenery must not get a separate
    # draw surface for every stem, rung or leaf.
    active.data.update();return active


def apply(obj,template,config):
    if obj.type!='MESH' or any(m.type=='ARMATURE' for m in obj.modifiers):raise ValueError('These rebuild templates support static meshes only')
    source_bounds=[list(min((v.co for v in obj.data.vertices),key=lambda p:p[i])) for i in range(3)]
    added=[]
    if template=='timber_supports':
        cutoff=config.get('cut_height',4.25);top=config.get('post_top',5.95)
        remove_region(obj,lambda c:c.z<cutoff or abs(abs(c.x)-1.3)<.35 and abs(abs(c.y)-1.15)<.38 and c.z<6.65)
        wood=material('RebuiltTimber',(.22,.12,.055));stone=material('RebuiltStone',(.28,.29,.27))
        for x in [-1.3,1.3]:
            for y in [-1.15,1.15]:
                added.append(beam('Clean_support',(x,y,.35),(x,y,top),.23,wood));added.append(beam('Stone_foot',(x,y,.04),(x,y,.42),.57,stone))
        for y in [-1.15,1.15]:
            added.append(beam('Platform_beam',(-1.4,y,4.3),(1.4,y,4.3),.22,wood));added.append(beam('Brace',(-1.3,y,.7),(1.3,y,3.5),.12,wood))
        for x in [-1.3,1.3]:
            added.append(beam('Side_beam',(x,-1.3,4.3),(x,1.3,4.3),.22,wood));added.append(beam('Side_brace',(x,-1.15,.7),(x,1.15,3.5),.12,wood))
        for x in [1.12,1.82]:added.append(beam('Ladder_rail',(x,-2.1,.18),(x,-1.0,4.5),.11,wood))
        for i in range(14):
            t=(i+1)/15;y=-2.1+1.1*t;z=.18+4.32*t;added.append(beam('Ladder_rung',(1.1,y,z),(1.84,y,z),.085,wood))
        policy='Keep reconstructed roof and balcony; replace bent lower timber and missing ladder; trim post ends to eaves.'
    elif template=='fern_fronds':
        remove_region(obj,lambda c:c.z>.15 or c.xy.length>.17)
        leaf=material('RebuiltFernLeaves',(.105,.27,.035));leaf.use_backface_culling=False
        stem=material('RebuiltFernStem',(.10,.18,.025));vertices=[];faces=[]
        fronds=int(config.get('fronds',12));pairs=int(config.get('pairs',16));spread=config.get('spread',.55);height=config.get('height',.45)
        for f in range(fronds):
            angle=f*math.tau/fronds+.17;direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-direction.y,direction.x,0));length=spread*(.85 if f%3 else .68)
            def center(t):return direction*(length*t)+Vector((0,0,.11+height*(.85 if f%3 else 1.12)*math.sin(t*math.pi*.76)))
            previous=center(0)
            for n in range(1,9):
                value=center(n/8);added.append(beam('Fern_stem',previous,value,.006,stem));previous=value
            for n in range(1,pairs+1):
                t=n/(pairs+2);base=center(t);span=.19*(1-t)*(.8+math.sin(t*math.pi))
                for sign in [-1,1]:
                    tip=base+side*sign*span+direction*.035+Vector((0,0,-.015));mid=base.lerp(tip,.48)+Vector((0,0,.015));width=.027*(1-t*.7)
                    offset=len(vertices);vertices.extend([base,mid-direction*width,tip,mid+direction*width,mid+Vector((0,0,.01))]);faces.extend([(offset,offset+1,offset+4),(offset+1,offset+2,offset+4),(offset+2,offset+3,offset+4),(offset+3,offset,offset+4)])
        leaves=mesh_object('Separated_leaflets',vertices,faces,leaf)
        colors=leaves.data.color_attributes.new(name='LeafVariation',type='FLOAT_COLOR',domain='CORNER')
        for i,value in enumerate(colors.data):
            brightness=.8+.25*math.sin(i*1.7);value.color=(brightness,brightness,brightness,1)
        added.append(leaves);policy='Keep source root crown; denser separated fronds and leaflets; 3 shared surfaces.'
    else:raise ValueError('Unsupported rebuild template')
    join([obj,*added],obj);obj.data.calc_loop_triangles()
    return {'operation':'rebuild_parts','template':template,'object':obj.name,'triangles':len(obj.data.loop_triangles),
        'material_slots':len(obj.data.materials),'retained_regions':policy,'automatic_anatomy_repair':False,'requires_visual_review':True}
