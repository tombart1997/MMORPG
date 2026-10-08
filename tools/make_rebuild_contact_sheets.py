"""Arrange actual Godot angle renders for readable, human visual inspection."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--group');parser.add_argument('--keys',nargs='*');args=parser.parse_args()
folder=ROOT/'docs/full_asset_rebuild/evidence';files=[]
if args.keys:keys=args.keys
else:
    targets=(ROOT/'game/assets/generated'/args.group).glob('*.glb') if args.group else (ROOT/'game/assets/generated').rglob('*.glb')
    keys=sorted(set(path.stem for path in targets))
missing=[]
for key in keys:
    path=folder/(key+'_runtime.png')
    if not path.exists():missing.append(key);continue
    files.append((key,path))
pages=[]
for start in range(0,len(files),4):
    chunk=files[start:start+4];page=Image.new('RGB',(1280,len(chunk)*348),'#515d66');draw=ImageDraw.Draw(page)
    for row,(key,path) in enumerate(chunk):
        draw.text((10,row*348+6),key+' | front / side / back / three-quarter',fill='white')
        im=Image.open(path).convert('RGB');page.paste(im.crop((0,0,1280,320)),(0,row*348+28))
    name='angles_'+(args.group or 'selection')+'_'+str(start//4)+'.png';page.save(folder/name);pages.append(name)
print(json.dumps({'pages':pages,'missing':missing}))
