import bpy
import math
import importlib
import numpy as np
import art_helpers
importlib.reload(art_helpers)
from art_helpers import blade, remove, mesh_object

steel = bpy.data.materials['Sword_Steel']
edge = bpy.data.materials['Sword_HonedEdge']
fuller = bpy.data.materials['Sword_Fuller']
remove('Sword_Blade')
blade('Sword_Blade', [(.015,.057,.013,1),(.08,.057,.013,1),(.125,.062,.013,1),
                     (.32,.055,.011,1),(.62,.042,.009,1),(.70,.035,.008,.15),
                     (.73,.032,.008,0),(.81,.020,.005,0),(.89,.0007,.0007,0)], [steel,edge,fuller])

# Reduce redundant subdivisions in the wrapping, then use smooth side normals.
old = bpy.data.objects['Sword_GripWrap']
verts = [tuple(v.co) for i,v in enumerate(old.data.vertices) if (i//4)%2 == 0]
steps = len(verts)//4 - 1
faces = [(3,2,1,0)]
for i in range(steps):
    for j in range(4):
        faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
faces.append(tuple(steps*4+j for j in range(4)))
wrapmat = bpy.data.materials['Sword_LeatherWrap']
remove('Sword_GripWrap')
wrap = mesh_object('Sword_GripWrap', verts, faces, [wrapmat], bevel=.00025)
for p in wrap.data.polygons:
    p.use_smooth = True
wrap.modifiers['Forged edge radius'].segments = 2

# Baked, packed PBR images, not procedural-only shaders lost at glTF export.
# Low contrast surface grain supplies roughness/material separation at close range.
rng = np.random.default_rng(42)
size = 256
yy, xx = np.mgrid[0:size,0:size]
noise = rng.random((size,size)).astype(np.float32)
grain = .6*noise + .4*np.sin(xx*.95 + np.sin(yy*.047)*.7)*.5 + .2

def texture(mat, base, roughness, strength, leather=False):
    field = noise if leather else grain
    variation = 1 + (field-.5)*strength
    color = np.ones((size,size,4), dtype=np.float32)
    for c in range(3):
        color[:,:,c] = np.clip(base[c]*variation,0,1)**(1/2.2)
    rough = np.ones((size,size,4), dtype=np.float32)
    for c in range(3):
        rough[:,:,c] = np.clip(roughness + (field-.5)*.12, .05, .95)
    bsdf = mat.node_tree.nodes['Principled BSDF']
    for suffix, pixels, socket in [('Color',color,'Base Color'),('Roughness',rough,'Roughness')]:
        image = bpy.data.images.new(mat.name+'_'+suffix, width=size,height=size,alpha=True)
        image.colorspace_settings.name = 'sRGB' if suffix=='Color' else 'Non-Color'
        image.pixels.foreach_set(pixels.ravel())
        image.pack()
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs[socket])

texture(wrapmat, (.037,.009,.006), .68, .40, True)
texture(bpy.data.materials['Sword_Leather'], (.025,.006,.004), .72, .3, True)
texture(steel, (.30,.37,.43), .31, .10)
texture(bpy.data.materials['Sword_Brass'], (.34,.205,.068), .30, .15)

# Dominant-plane UVs in object space, consistent texel scale on these small parts.
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH' or not ob.name.startswith('Sword_'):
        continue
    uv = ob.data.uv_layers.new(name='SurfaceUV')
    for poly in ob.data.polygons:
        normal = poly.normal
        dominant = max(range(3), key=lambda i: abs(normal[i]))
        axes = [(1,2),(0,2),(0,1)][dominant]
        for index in poly.loop_indices:
            p = ob.data.vertices[ob.data.loops[index].vertex_index].co
            uv.data[index].uv = (p[axes[0]]*5,p[axes[1]]*5)
    # Correct bevel shading while retaining deliberate broad planar facets.
    if any(m.type == 'BEVEL' for m in ob.modifiers) and ob != wrap:
        normal = ob.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
        normal.keep_sharp = True

print('Finish: fuller terminates before point; darker grained leather, brushed PBR surfaces, cleaner bevel normals')
