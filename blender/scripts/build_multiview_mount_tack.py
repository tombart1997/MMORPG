"""Fit the new saddle reconstruction and clean bridle to the reviewed bay horse."""
import bpy,importlib.util,math,json
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('clean',Path(__file__).with_name('rebuild_clean_sections.py'))
clean=importlib.util.module_from_spec(spec);spec.loader.exec_module(clean)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/prepared/saddle.blend'))
parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in parts:
    o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
    o.data.transform(Matrix.Rotation(-math.pi/2,4,'Z'))
coords=[v.co for o in parts for v in o.data.vertices]
lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);center=(lo+hi)*.5
for o in parts:
    for v in o.data.vertices:
        v.co=Vector(((v.co.x-center.x)*.92/(hi.x-lo.x),(v.co.y-center.y)*.90/(hi.y-lo.y),(v.co.z-lo.z)*.82/(hi.z-lo.z)+.87))
    o.name='MV_FittedSaddle'
dest=ROOT/'blender/multiview_rebuild/equipment/saddle.blend';dest.parent.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'game/assets/generated/equipment/saddle.glb'),export_format='GLB',export_yup=True,export_animations=False)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/rigged/bay_horse.blend'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
leather=clean.material('BayBridleLeather',(.052,.025,.013),rough=.72)
brass=clean.material('BayBridleBrass',(.32,.16,.048),metal=.45,rough=.4)
made=[]
def strap(points,radius=.014,bone='Head',mat=leather):
    o=clean.tube('NewHorseTack',points,[radius]*len(points),mat,6)
    o.parent=rig;o.matrix_parent_inverse=rig.matrix_world.inverted()
    for b in rig.data.bones:o.vertex_groups.new(name=b.name)
    o.vertex_groups[bone].add(list(range(len(o.data.vertices))),1,'REPLACE')
    modifier=o.modifiers.new('HorseTackSkin','ARMATURE');modifier.object=rig;made.append(o)
strap([(-.12,.80,1.87),(-.14,.94,1.85),(-.12,1.05,1.72),(-.11,1.17,1.58)])
strap([(.12,.80,1.87),(.14,.94,1.85),(.12,1.05,1.72),(.11,1.17,1.58)])
strap([(-.12,1.14,1.64),(-.08,1.23,1.64),(0,1.25,1.65),(.08,1.23,1.64),(.12,1.14,1.64)])
strap([(-.14,.94,1.85),(-.07,1.005,1.85),(0,1.025,1.85),(.07,1.005,1.85),(.14,.94,1.85)])
strap([(-.11,1.17,1.58),(0,1.205,1.565),(.11,1.17,1.58)],.008,mat=brass)
for side in [-1,1]:
    strap([(side*.115,1.17,1.59),(side*.18,.93,1.52),(side*.20,.65,1.49),(side*.18,.38,1.61),(-.15,.22,1.83)],.008,bone='Body')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in made:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
rig.data.pose_position='POSE';bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/multiview_rebuild/rigged/bay_horse.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'game/assets/generated/bay_horse.glb'),export_format='GLB',export_yup=True,export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False)
(ROOT/'docs/full_asset_rebuild/mount_tack_fit.json').write_text(json.dumps({'saddle_source':'saddle shared four-view reconstruction','saddle_bounds_m':{'width':.92,'length':.90,'lowest_stirrup':.87,'highest_pommel':1.69},'seat_rest_m':[0,1.535,0],'bridle':'clean leather and brass geometry fitted to new head','old_geometry_reused':False},indent=2))
