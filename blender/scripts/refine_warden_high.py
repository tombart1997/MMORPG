"""Second live art pass: anatomical CC0 head, fitted shoulders, controlled highlights."""
import bpy,bmesh,math,importlib.util
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('wh',Path(__file__).with_name('build_warden_high.py'))
wh=importlib.util.module_from_spec(spec);spec.loader.exec_module(wh)
wh.RIG=bpy.data.objects['WardenRig']
wh.PARTS=[o for o in bpy.context.scene.objects if o.type=='MESH']
wh.MATS={m.name.removeprefix('Warden_'):m for m in bpy.data.materials if m.name.startswith('Warden_')}

def refine():
    for o in list(wh.PARTS):
        if o.vertex_groups.get('Head') or o.name=='Neck':
            wh.PARTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
    verts=[];faces=[];group='';uvs=[]
    for l in (ROOT/'blender/reference/makehuman/base.obj').read_text().splitlines():
        if l.startswith('v '):verts.append(Vector(map(float,l.split()[1:])))
        elif l.startswith('vt '):uvs.append(tuple(map(float,l.split()[1:3])))
        elif l.startswith('g '):group=l[2:]
        elif l.startswith('f '):faces.append((group,[tuple(int(v)-1 for v in p.split('/')[:2]) for p in l.split()[1:]]))
    for l in (ROOT/'blender/reference/makehuman/male-young.target').read_text().splitlines():
        if l and not l.startswith('#'):
            a=l.split();verts[int(a[0])]+=Vector(map(float,a[1:]))
    def transform(v):return (v.x*.112,v.z*.110-.074,v.y*.115+.807)
    for group in ['body','helper-l-eye','helper-r-eye']:
        chosen=[f for g,f in faces if g==group and all(verts[p[0]].y>6.24 for p in f)]
        used=sorted(set(p[0] for f in chosen for p in f));indices={i:j for j,i in enumerate(used)}
        weights=[]
        for i in used:
            w=max(0,min(1,(verts[i].y-6.5)/.85));weights.append({'Head':w,'Neck':1-w})
        mat=wh.MATS['Skin'] if group=='body' else wh.MATS['EyeWhite']
        obj=wh.mesh('AnatomicalHead' if group=='body' else 'AnatomicalEye',[transform(verts[i]) for i in used],[[indices[p[0]] for p in f] for f in chosen],mat,weights=weights)
        if group=='body':
            for poly,f in zip(obj.data.polygons,chosen):
                for li,p in zip(poly.loop_indices,f):obj.data.uv_layers.active.data[li].uv=uvs[p[1]]
            sub=obj.modifiers.new('AnatomicalSubdivision','SUBSURF');sub.levels=2
            bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_move_up(modifier=sub.name)
            bpy.ops.object.modifier_apply(modifier=sub.name)
        else:
            sub=obj.modifiers.new('EyeSubdivision','SUBSURF');sub.levels=2
            bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name)
    # Iris placement is derived from the authored eyeball joint centers.
    for s in [-1,1]:
        center=Vector((s*.293125*.112,1.30435*.110-.074,8.2164*.115+.807))
        wh.ell('FittedIris',center+Vector((0,.010,0)),(.0054,.002,.0054),wh.MATS['Iris'],'Head',32,20)
        wh.ell('FittedPupil',center+Vector((0,.0117,0)),(.0025,.0008,.0027),wh.MATS['Pupil'],'Head',24,16)
    # A close-cropped scalp follows anatomical cranium geometry, including hairline.
    def hair_vertex(v):
        threshold=8.60 if v.z>.45 else 7.95
        if abs(v.x)>.65:threshold=max(threshold,8.1)
        return v.y>threshold
    chosen=[f for g,f in faces if g=='body' and all(hair_vertex(verts[p[0]]) for p in f)]
    used=sorted(set(p[0] for f in chosen for p in f));ix={i:j for j,i in enumerate(used)}
    hv=[]
    for i in used:
        v=Vector(transform(verts[i]));c=Vector((0,-.03,1.80));v=c+(v-c)*1.025
        v.z+=.002+max(0,v.z-1.84)*.11;hv.append(v)
    hair=wh.mesh('CroppedHair',hv,[[ix[p[0]] for p in f] for f in chosen],wh.MATS['Hair'],'Head')
    sub=hair.modifiers.new('HairSubdivision','SUBSURF');sub.levels=2
    bpy.context.view_layer.objects.active=hair;bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name)
    # Short beard uses the lower face itself, so it conforms to lips and jaw.
    def beard(v):return 7.08<v.y<7.8 and v.z>.55 and (v.y<7.43 or abs(v.x)>.20)
    chosen=[f for g,f in faces if g=='body' and all(beard(verts[p[0]]) for p in f)]
    used=sorted(set(p[0] for f in chosen for p in f));ix={i:j for j,i in enumerate(used)}
    bv=[]
    for i in used:
        v=Vector(transform(verts[i]));v.y+=.0008;bv.append(v)
    beard_obj=wh.mesh('CloseBeard',bv,[[ix[p[0]] for p in f] for f in chosen],wh.MATS['Hair'],'Head')
    sub=beard_obj.modifiers.new('BeardSubdivision','SUBSURF');sub.levels=2
    bpy.context.view_layer.objects.active=beard_obj;bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name)
    for obj in wh.PARTS:
        if obj.name.startswith('PauldronLame'):
            center=sum((v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
            for v in obj.data.vertices:
                d=v.co-center;d.x*=.88;d.y*=.88;d.z*=.72;v.co=center+d
        # Restore outward normals, including the clockwise loft sections.
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(obj.data);bm.free()
    for key in ['Hair','HairHighlight','Leather','Cloth','Skin']:
        mat=wh.MATS[key];shader=mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Specular IOR Level'].default_value=.24
        shader.inputs['Roughness'].default_value=.72 if key!='Skin' else .58
    print('Anatomical head fitted; shoulders refined; normals repaired')

if __name__=='__main__':refine()
