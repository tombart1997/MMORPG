"""Repeatable front/side/three-quarter studio review of editable mount assets."""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
label = args[0] if args else 'horse_baseline'
dest = ROOT/'docs/screenshots/horse-reference'/label
dest.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
for obj in list(scene.objects):
    if obj.type in {'CAMERA', 'LIGHT'}: bpy.data.objects.remove(obj, do_unlink=True)
for obj in scene.objects:
    if obj.type == 'ARMATURE':
        if obj.animation_data:
            obj.animation_data.action = None
            for tr in obj.animation_data.nla_tracks: tr.mute = True
        for pb in obj.pose.bones: pb.matrix_basis.identity()
scene.frame_set(0)
bpy.context.view_layer.update()
meshes = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render]
points = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
minimum = Vector(tuple(min(p[i] for p in points) for i in range(3)))
maximum = Vector(tuple(max(p[i] for p in points) for i in range(3)))
center = (minimum+maximum)/2
print('ASSET_BOUNDS', list(minimum), list(maximum), flush=True)
print('OBJECTS', [(o.name, len(o.data.vertices)) for o in meshes], flush=True)
for rig in [o for o in scene.objects if o.type == 'ARMATURE']:
    print('BONES', [(b.name, list(b.head_local), list(b.tail_local)) for b in rig.data.bones], flush=True)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 1000
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.24,.27,.30,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
scene.view_settings.view_transform = 'AgX'
for name, pos, energy, size in [('Key',(3,4,6),700,5),('Fill',(-4,2,3),450,4),('Rim',(1,-4,5),650,3)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob)
    ob.location=pos; ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',data)
scene.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO'
data.ortho_scale=max(maximum.z-minimum.z,maximum.y-minimum.y)*1.24
for name,direction in [('front',(0,6,.1)),('side',(6,0,.05)),('threequarter',(5,6,1.2))]:
    cam.location=center+Vector(direction)
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(dest/(name+'.png'));bpy.ops.render.render(write_still=True)
(dest/'bounds.json').write_text(json.dumps({'minimum':list(minimum),'maximum':list(maximum)},indent=2))
