"""Visibility-checked orthographic color projection, retaining native coverage.

Uses the reviewed angle labels, foreground masks, mesh normals and BVH ray tests.
Does not sculpt geometry or claim calibrated cameras. Review texture alignment
at eyes, joints and seams before accepting approximate AI turnaround projections.
"""
import json
import math
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np

VIEWS = {'front':((0,0,-1),(0,1,0)), 'back':((0,0,1),(0,1,0)),
         'left':((-1,0,0),(0,1,0)), 'right':((1,0,0),(0,1,0)),
         'top':((0,1,0),(0,0,-1))}


def main(request):
    started = time.monotonic()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=request['source'])
    records = []
    prepared = []
    for view in request['views']:
        if view['angle'] not in VIEWS:
            continue  # Perspective views require camera calibration; don't misproject them.
        image = bpy.data.images.load(view['mask'])
        w,h = image.size
        pixels = np.empty(w*h*4,dtype=np.float32)
        image.pixels.foreach_get(pixels)
        pixels = pixels.reshape(h,w,4)
        ys,xs = np.where(pixels[:,:,3]>.8)
        if not len(xs):
            raise RuntimeError('Empty foreground mask: ' + view['angle'])
        prepared.append((view['angle'], pixels, (xs.min(),ys.min(),xs.max(),ys.max())))
    if len(prepared)<2:
        raise RuntimeError('At least two orthographic masked views are required for color projection')
    for obj in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        mesh = obj.data
        count = len(mesh.vertices)
        positions = np.empty(count*3,dtype=np.float32)
        normals = np.empty_like(positions)
        mesh.vertices.foreach_get('co',positions)
        mesh.vertices.foreach_get('normal',normals)
        positions = positions.reshape(count,3)
        normals = normals.reshape(count,3)
        # glTF import converts Y-up into Blender Z-up. Angle labels describe
        # Godot/glTF world coordinates, not local Blender mesh coordinates.
        # Apply object transforms and convert back before projection/ray tests.
        transform=np.asarray(obj.matrix_world,dtype=np.float32)
        positions=positions@transform[:3,:3].T+transform[:3,3]
        normals=normals@np.linalg.inv(transform[:3,:3])
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
        positions=positions[:,[0,2,1]]*np.array([1,1,-1],dtype=np.float32)
        normals=normals[:,[0,2,1]]*np.array([1,1,-1],dtype=np.float32)
        tree = BVHTree.FromPolygons([Vector(p) for p in positions],
            [tuple(p.vertices) for p in mesh.polygons],all_triangles=True)
        extent = float((positions.max(0)-positions.min(0)).max())
        original = mesh.color_attributes.active_color or (mesh.color_attributes[0] if len(mesh.color_attributes) else None)
        native = np.ones((count,4),dtype=np.float32)
        if original and original.domain=='POINT':
            original.data.foreach_get('color',native.reshape(-1))
        elif original and original.domain=='CORNER':
            corner=np.empty(len(mesh.loops)*4,dtype=np.float32)
            original.data.foreach_get('color',corner)
            vertex_ids=np.empty(len(mesh.loops),dtype=np.int32)
            mesh.loops.foreach_get('vertex_index',vertex_ids)
            native=np.zeros((count,4),dtype=np.float32)
            np.add.at(native,vertex_ids,corner.reshape(-1,4))
            totals=np.bincount(vertex_ids,minlength=count)
            native/=np.maximum(totals,1)[:,None]
        color_sum = np.zeros((count,3),dtype=np.float32)
        weight_sum = np.zeros(count,dtype=np.float32)
        hits_by_view = {}
        for angle,pixels,box in prepared:
            direction,up = map(lambda v:np.asarray(v,dtype=np.float32),VIEWS[angle])
            right = np.cross(up,direction)
            x, y = positions@right, positions@up
            u=(x-x.min())/max(float(x.max()-x.min()),1e-6)
            v=(y-y.min())/max(float(y.max()-y.min()),1e-6)
            px=np.clip(np.rint(box[0]+u*(box[2]-box[0])).astype(int),0,pixels.shape[1]-1)
            py=np.clip(np.rint(box[1]+v*(box[3]-box[1])).astype(int),0,pixels.shape[0]-1)
            rgba=pixels[py,px]
            weights=np.maximum(normals@direction,0)**4*rgba[:,3]
            candidates=np.flatnonzero((weights>.025)&(rgba[:,3]>.8))
            direction_v=Vector(direction)
            ray_direction=-direction_v
            visible=[]
            # Occluded legs/backfaces must not receive foreground color from a nearer leg.
            for index in candidates:
                vertex=Vector(positions[index])
                point,_,_,_=tree.ray_cast(vertex+direction_v*extent*2,ray_direction,extent*4)
                if point is not None and (point-vertex).length<extent*.008:
                    visible.append(index)
            ids=np.asarray(visible,dtype=int)
            color_sum[ids]+=rgba[ids,:3]*weights[ids,None]
            weight_sum[ids]+=weights[ids]
            hits_by_view[angle]=len(ids)
        covered=weight_sum>0
        native[covered,:3]=color_sum[covered]/weight_sum[covered,None]
        native[:,3]=1
        # Godot uses COLOR_0 only. Blender may export both the old and new layer,
        # placing the requested material layer in COLOR_1; retain one final layer.
        for attribute in list(mesh.color_attributes):
            mesh.color_attributes.remove(attribute)
        projected=mesh.color_attributes.new(name='ReviewedReferenceColors',type='FLOAT_COLOR',domain='POINT')
        projected.data.foreach_set('color',native.reshape(-1))
        mesh.color_attributes.active_color=projected
        mesh.color_attributes.render_color_index=0
        material=bpy.data.materials.new('Reviewed reference color-vcol')
        material.use_nodes=True
        shader=material.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value=.95
        attr=material.node_tree.nodes.new('ShaderNodeVertexColor')
        attr.layer_name=projected.name
        material.node_tree.links.new(attr.outputs['Color'],shader.inputs['Base Color'])
        mesh.materials.clear();mesh.materials.append(material)
        records.append({'mesh':obj.name,'vertices':count,'covered_vertices':int(covered.sum()),'visible_samples':hits_by_view})
    bpy.ops.export_scene.gltf(filepath=request['output'],export_format='GLB',
        export_materials='EXPORT',export_attributes=True,export_vertex_color='ACTIVE',export_normals=True,
        export_yup=True)
    report={'method':'Approximate orthographic projection with BVH visibility and normal-weighted blending',
        'mesh_changed':False,'coordinates':'glTF Y-up world; Blender import transform accounted for',
        'source':request['source'],'views':request['views'],'meshes':records,
        'elapsed_seconds':round(time.monotonic()-started,2),
        'remaining_review':['Eye and limb registration','Texture seams','Generated view consistency'],
        'uncovered_surface':'Native generated colors retained'}
    Path(request['report']).write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    main(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8')))
