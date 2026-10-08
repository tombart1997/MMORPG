"""Apply the vertex-albedo import contract without changing Godot's LOD settings."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def configure(directory,script):
    count=0
    for model in directory.rglob('*.glb'):
        settings=Path(str(model)+'.import')
        if not settings.exists():continue
        text=settings.read_text();updated=re.sub(r'import_script/path="[^"]*"','import_script/path="'+script+'"',text)
        if updated!=text:settings.write_text(updated);count+=1
    return count
if __name__=='__main__':print('Updated import contracts:',configure(ROOT/'game/assets/generated','res://scripts/visuals/generated_asset_import.gd'))
