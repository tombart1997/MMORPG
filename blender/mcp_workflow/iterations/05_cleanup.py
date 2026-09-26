import bpy
import numpy as np
import importlib
import art_helpers
importlib.reload(art_helpers)
from art_helpers import blade, remove

# The render exposed regular striping: replace periodic grain with subtle noise.
rng = np.random.default_rng(1907)
for name, base, roughness in [('Sword_Steel',(.30,.37,.43),.31),('Sword_Brass',(.34,.205,.068),.30)]:
    field = rng.random((256,256)).astype(np.float32)-.5
    for suffix in ('Color','Roughness'):
        image = bpy.data.images[name+'_'+suffix]
        pixels = np.ones((256,256,4),dtype=np.float32)
        for c in range(3):
            pixels[:,:,c] = (base[c]*(1+field*.035))**(1/2.2) if suffix=='Color' else roughness+field*.035
        image.pixels.foreach_set(pixels.ravel())
        image.pack()

remove('Sword_Blade')
ob = blade('Sword_Blade', [(.015,.057,.013,1),(.08,.057,.013,1),(.125,.062,.013,1),
                         (.32,.055,.011,1),(.62,.042,.009,1),(.70,.035,.008,.15),
                         (.73,.032,.008,0),(.81,.020,.005,0),(.89,.0007,.0007,0)],
           [bpy.data.materials[n] for n in ['Sword_Steel','Sword_HonedEdge','Sword_Fuller']])
uv = ob.data.uv_layers.new(name='SurfaceUV')
for p in ob.data.polygons:
    for i in p.loop_indices:
        co = ob.data.vertices[ob.data.loops[i].vertex_index].co
        uv.data[i].uv = (co.x*5,co.z*5)

# Put the attachment origin in the center of the one-handed grip.
for ob in bpy.context.scene.objects:
    if ob.type == 'MESH' and ob.name.startswith('Sword_'):
        for v in ob.data.vertices:
            v.co = ob.matrix_world @ v.co
            v.co.z += .118
        ob.location = (0,0,0)
        ob.rotation_euler = (0,0,0)
        ob.scale = (1,1,1)
bpy.context.scene.cursor.location = (0,0,0)

# Reload the small operations module after the selected static-export extension.
import operations
importlib.reload(operations)
print('Removed periodic surface stripes, tapered fuller termination, grip-centered attachment origin')
