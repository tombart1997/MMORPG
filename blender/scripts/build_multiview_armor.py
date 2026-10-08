"""New socket-sized armor sections derived from the reviewed outfit palette."""
import bpy,json,importlib.util,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('clean',Path(__file__).with_name('rebuild_clean_sections.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def save(key):
    c.collapse_colors(key)
    source=ROOT/'blender/multiview_rebuild/equipment'/f'{key}.blend';source.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source))
    dest=ROOT/'game/assets/generated/equipment'/f'{key}.glb';dest.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_animations=False)
    (ROOT/'docs/full_asset_rebuild'/f'{key}_equipment.json').write_text(json.dumps({
        'key':key,'method':'clean_socket_equipment','old_geometry_reused':False,
        'reference':'concepts_docs/art/asset_turnarounds_v2/warrior/turnaround.png',
        'authority':'Reviewed lamellar/brass/leather palette; independent fitted equipment, not extracted legacy armor.'},indent=2))
for key in ['warden_insignia','traveler_guard','jade_ironback_mantle']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    brass=c.material('WardenBrass',(.42,.27,.073),.35,.46);leather=c.material('ArmorLeather',(.086,.046,.025));jade=c.material('JadeLamellae',(.023,.12,.064),.2,.49)
    if key=='warden_insignia':
        c.tube('Medallion',[(0,.175,-.05),(0,.185,-.05)],.061,brass,24)
        c.tube('EmbossedRim',[(.056*math.sin(i*math.tau/24),.188,-.05+.056*math.cos(i*math.tau/24)) for i in range(25)],.0024,brass,5)
        c.tube('RaisedPine',[(0,.191,-.087),(0,.191,-.012)],.003,jade,6)
        for z in [-.032,-.049,-.066]:
            for side in [-1,1]:c.tube('PineBranch',[(0,.191,z),(side*.023,.191,z-.013)],.002,jade,5)
        c.tube('BadgeCord',[(-.06,.17,.02),(0,.18,-.005),(.06,.17,.02)],.003,leather,5)
    elif key=='traveler_guard':
        for side in [-1,1]:
            for row in range(3):
                x=side*(.20+row*.018);z=.15-row*.046
                c.ellipsoid('LayeredChestGuard',(x,.105,z),(.075,.039,.053),leather,12,6)
                c.tube('BrassTrim',[(x-.065,.142,z),(x,.149,z-.025),(x+.065,.142,z)],.0035,brass,6)
        for x in [-.075,0,.075]:
            c.ellipsoid('FrontLamellarPlate',(x,.185,-.105),(.033,.013,.073),jade,10,5)
    else:
        for row in range(3):
            for side in [-1,1]:
                x=side*(.09+row*.07);z=.18-row*.07
                c.ellipsoid('BackRidgePlate',(x,-.21,z),(.075,.035,.092),jade,10,5)
                c.tube('CarvedRidgeTrim',[(x-.045,-.244,z+.05),(x,-.250,z+.075),(x+.045,-.244,z+.05)],.004,brass,6)
        for side in [-1,1]:c.tube('LeatherHarness',[(side*.21,-.22,.17),(side*.24,-.03,.19),(side*.19,.20,.07)],[.017,.02,.017],leather,8)
    save(key)
