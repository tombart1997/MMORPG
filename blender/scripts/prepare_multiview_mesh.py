"""Bake native multi-image colors onto a bounded clean runtime mesh.

Retained neural geometry is immutable. This is a simplification stage, not a
claim of authored retopology. Actual surface-error checks come from Asset Forge.
"""
import bpy, importlib.util, json, sys
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
spec=importlib.util.spec_from_file_location('optimizer',FORGE/'blender/optimize.py')
optimizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(optimizer)

def prepare(entry):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=entry['source'])
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objects:
        o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
        o.name='MV_'+entry['key']
    work=ROOT/'.local/full_asset_rebuild'/entry['key'];work.mkdir(parents=True,exist_ok=True)
    report=optimizer.optimize(objects,{'optimization_mode':entry.get('mode','simplify'),
        'triangle_budget':entry.get('budget',18000),'max_surface_error':entry.get('surface_error',.025),
        'texture_resolution':entry.get('texture_size',1024),'bake_normal_map':True},
        lambda stage,**data:print(stage,data,flush=True),work)
    if report['achieved_triangles']>entry.get('budget',18000)*1.1:
        raise RuntimeError('Reduction rejected; source retained: '+json.dumps(report))
    for o in objects:
        o.data.validate(clean_customdata=False)
        if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        for f in o.data.polygons:f.use_smooth=True
    output=ROOT/'blender/multiview_rebuild/prepared'/entry['key']
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix('.blend')))
    runtime=ROOT/'game/review_assets/full_rebuild'/entry['key']/'runtime.glb'
    runtime.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(runtime),export_format='GLB',export_animations=False,
        export_skins=False,export_yup=True)
    (ROOT/'docs/full_asset_rebuild'/f"{entry['key']}_optimization.json").write_text(json.dumps(report,indent=2))
    print('PREPARED',entry['key'],report['achieved_triangles'],flush=True)

if __name__=='__main__':
    request=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
    for entry in request['assets']:prepare(entry)
