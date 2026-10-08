"""Import inspected production sheets as new Forge assets; never alter game mappings.

Run with the Forge server running. Whole sheets are archived as interpretation
references; distinct prepared views are the inputs. The catalog names the views
excluded during visual inspection and the original concept authority.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

import httpx
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forge.store import atomic_json, digest

GAME=Path('D:/Games/Metin2Clone')
ART=GAME/'concepts_docs/art/asset_turnarounds_v2'
SPECS=[
 {'key':'ironhide_boar','plan_key':'mob_ironhide_boar','preset':'creature','split':None,
  'boxes':{'front':[70,5,340,495],'left':[445,0,691,500],'back':[1185,3,300,497],
           'right':[5,540,645,453],'three_quarter':[655,543,505,457],'top':[1245,540,220,475]},
  'used':['front','left','back','three_quarter'],
  'notes':'Opened original, sheet and extracted views. Stocky boar identity, paired tusks, four legs, dorsal reed plates, brown gray hide and neutral stance agree. Fine plates on hidden sides are inferred. Top and opposite side remain supplementary.'},
 {'key':'bay_horse','plan_key':'horse_bay','preset':'creature','split':512,
  'used':['front','left','back','three_quarter'],
  'notes':'Opened original and corrected sheet. Removed invented white facial blaze; plain bay face, black mane/tail/lower legs, neutral stance and realistic hoof proportions agree. Tack and rider are separate. Hidden markings and individual muscle details are inferred.'},
 {'key':'warrior','plan_key':'hero_ironvow','preset':'humanoid','split':534,
  'used':['front','left','back','three_quarter'],
  'notes':'Opened original and sheet. Adult proportions, black topknot, green lamellar armor, brass trim, red sash and black cloth agree. Neutral A-pose with empty hands and separated feet. Side arms appear vertical by projection; rear costume is an inferred continuation. Hand topology needs mesh review.'},
 {'key':'meadow_wolf','plan_key':'mob_meadow_wolf','preset':'creature','split':510,
  'used':['front','left','back','three_quarter'],
  'notes':'Opened original and all sheet angles. Gray taupe fur, cream chest and inner legs, golden eyes, lupine muzzle, pointed ears, bushy tail and neutral four-paw pose agree. Fine fur patterns are interpretations, not verified hidden surfaces.'},
 {'key':'watchtower','plan_key':'watchtower','preset':'environment','split':506,'second_angle':'right',
  'used':['front','right','three_quarter'],'excluded':{'back':'Initial sheet omitted the ladder in the rear view. Do not condition on this panel until corrected.'},
  'notes':'Opened original and sheet. Front, right side and three-quarter agree on four posts, stone feet, raised railing deck, right-side ladder, front-left banner and curved tile roof. Excluded rear panel because its ladder is absent. Orthographic posts align by occlusion; straight structural parts still require mesh inspection.'},
 {'key':'fern','plan_key':'fern_reference','preset':'environment','split':489,'third_angle':'top',
  'used':['front','top'],'excluded':{'left':'Too similar to the front camera to add reliable angle evidence.','three_quarter':'Nearly repeats the front view; supplementary appearance study only.'},
  'notes':'Opened original and sheet. Front and overhead show the same compact crown, seven principal green fronds, paired leaflets and weathered brown stems. Use only those distinct angles; other panels are redundant interpretations. Thin leaves may be better built as clean cards instead of neural solid geometry.'},
 {'key':'reed_spider','plan_key':'mob_reed_spider','preset':'creature','split':475,'third_angle':'top','rotate_top':180,
  'used':['front','left','top','three_quarter'],
  'notes':'Opened original and sheet. Removed cropped human and neighboring creature. Overhead shows exactly eight walking legs, four each side; front palps and fangs are distinct. Straw abdomen and brown chitin agree. Rotated overhead input so nose points image up. Some far legs are occluded in side view; inspect leg attachment and foot grounding in mesh.'},
 {'key':'blacksmith','plan_key':'npc_smith','preset':'humanoid','split':503,'second_angle':'right',
  'used':['front','right','back','three_quarter'],
  'notes':'Opened original and sheet. Same adult smith, graying beard/topknot, linen shirt, leather apron, dark trousers and boots; separated neutral limbs and empty hands. Tools need independent models and attachments. Rear apron straps are inferred.'},
]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8743');args=parser.parse_args()
    catalog_path=ART/'catalog.json'
    catalog=json.loads(catalog_path.read_text()) if catalog_path.exists() else {'schema':1,'created':'2026-10-07','assets':[]}
    plans={a['key']:a for a in json.loads((GAME/'blender/forge_rebuild/plan.json').read_text())['assets']}
    with httpx.Client(base_url=args.url+'/api',headers={'X-Forge-Request':'1'},timeout=90) as client:
        def request(method,path,**kwargs):
            response=client.request(method,path,**kwargs);response.raise_for_status();return response.json()
        for spec in SPECS:
            sheet=ART/spec['key']/'turnaround.png'
            if not sheet.exists():continue
            if any(a['key']==spec['key'] for a in catalog['assets']):continue
            plan=plans[spec['plan_key']]
            asset=request('POST','/assets',json={'name':'MV · '+plan['name'],'preset':spec['preset'],
                'design_requirements':plan.get('design','')+' Practical neutral multi-view interpretation; preserve concept silhouette and materials.',
                'license':'Original project concept plus AI-generated turnaround interpretation. Backend MIT weights/code; FlexiCubes Apache 2.0.'})
            aid=asset['id']
            settings={**asset['settings'],'optimization_mode':'simplify','triangle_budget':18000 if spec['preset']=='creature' else 24000 if spec['preset']=='humanoid' else 8000,
                'trellis_steps':25,'trellis_guidance':5,'multiview_mode':'multidiffusion','project_reference_colors':False,
                'bypass_rigging':True,'render_preview':False,'generate_lods':False,'collision':'none'}
            request('PUT',f'/assets/{aid}/settings',json=settings)
            def upload(path,role):
                with Path(path).open('rb') as stream:
                    return request('POST',f'/assets/{aid}/references',data={'role':role},files={'file':(Path(path).name,stream,'image/png')})
            authority=upload(plan['prepared_reference'],'primary')
            full=upload(sheet,'turnaround_pending')
            with Image.open(sheet) as im:
                width,height=im.size
            split=spec.get('split') or height//2
            half=width//2
            boxes=spec.get('boxes') or {'front':[0,0,half,split],spec.get('second_angle','left'):[half,0,width-half,split],
                spec.get('third_angle','back'):[0,split,half,height-split],'three_quarter':[half,split,width-half,height-split]}
            views=[]; all_views=[]
            for angle,box in boxes.items():
                prepared=request('POST',f'/assets/{aid}/prepare',json={'reference_id':full['id'],'crop':box,'role':'additional',
                    'rotation_degrees':spec.get('rotate_top',0) if angle=='top' else 0})
                # Copy deterministic prepared inputs into the game reference collection for browsing.
                response=client.get(f"/assets/{aid}/files/{prepared['path']}");response.raise_for_status()
                path=sheet.parent/(angle+'.png');path.write_bytes(response.content)
                all_views.append({'angle':angle,'reference_id':prepared['id'],'path':str(path.relative_to(GAME)),
                    'sha256':digest(path),'resolution':prepared['resolution'],'used':angle in spec['used']})
                if angle in spec['used']:views.append({'angle':angle,'reference_id':prepared['id']})
            viewset=request('POST',f'/assets/{aid}/reference-sets',json={'name':'Neutral production interpretation',
                'source_reference_id':authority['id'],'pose':'One neutral pose; no action or attachment changes between views.',
                'scale_notes':'Consistent object proportions; primary views orthographic. Front is -Z; overhead nose points image up. Generated hidden details remain inferred.',
                'views':views})
            request('PUT',f"/assets/{aid}/reference-sets/{viewset['id']}/review",json={'approved':True,'notes':spec['notes']})
            catalog['assets'].append({'key':spec['key'],'name':plan['name'],'plan_key':spec['plan_key'],'forge_asset_id':aid,
                'source_asset_id':plan['forge_asset_id'],'source_reference':plan['prepared_reference'],
                'sheet':str(sheet.relative_to(GAME)),'sheet_sha256':digest(sheet),'views':all_views,
                'reference_set_id':viewset['id'],'review_notes':spec['notes'],'excluded_views':spec.get('excluded',{}),
                'game_replacement':'None; generated candidates require separate geometry, rig and runtime acceptance.'})
            atomic_json(catalog_path,catalog)
            print(spec['key'],aid,viewset['id'],len(views),'active views',flush=True)


if __name__=='__main__':main()
