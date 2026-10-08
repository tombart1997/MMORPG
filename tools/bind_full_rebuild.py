"""Bind mesh orientations established by opening the Godot review sheets."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPECS={
 'warrior':{'rig_template':'warden_high','family':'humanoid','height':1.90,'yaw':180,'arm_repose_degrees':18},
 'meadow_wolf':{'rig_template':'wolf','family':'wolf','height':1.45,'yaw':-90},
 'reed_spider':{'rig_template':'spider','family':'spider','height':1.05,'yaw':0},
 'blacksmith':{'rig_template':'townfolk_kit','family':'humanoid','height':1.90,'yaw':0},
 'ironhide_boar':{'rig_template':'boar','family':'boar','height':1.30,'yaw':0},
 'bay_horse':{'rig_template':'trail_horse','family':'horse','height':1.98,'yaw':0},
 'mossling':{'rig_template':'briarling','family':'mossling','height':1.70,'yaw':0},
 'stonekin':{'rig_template':'stonekin','family':'stonekin','height':1.90,'yaw':0},
 'wisp':{'rig_template':'wisp','family':'wisp','height':1.55,'yaw':0},
 'bandit':{'rig_template':'warden_high','family':'bandit','height':1.90,'yaw':0,'arm_repose_degrees':18},
 'keeper':{'rig_template':'townfolk_kit','family':'humanoid','height':1.90,'yaw':0},
 'stablemaster':{'rig_template':'townfolk_kit','family':'humanoid','height':1.90,'yaw':180},
}
parser=argparse.ArgumentParser();parser.add_argument('keys',nargs='+');args=parser.parse_args()
assets=[]
for key in args.keys:
    source=ROOT/'blender/multiview_rebuild/prepared'/f'{key}.blend'
    settings=dict(SPECS[key]);name=settings.pop('rig_template')
    settings['rig_source']=f'blender/multiview_rebuild/binding_templates/{name}.blend'
    settings['binding_guide']=f'blender/multiview_rebuild/binding_templates/{name}.weights.json'
    assets.append({'key':key,'source':str(source),**settings})
request=ROOT/'.local/full_asset_rebuild/bind.json';request.write_text(json.dumps({'assets':assets}))
subprocess.run(['C:/Program Files/Blender Foundation/Blender 5.2/blender.exe','--background','--threads','6',
    '--python-exit-code','1','--python',str(ROOT/'blender/scripts/bind_multiview_mesh.py'),'--',str(request)],check=True)
