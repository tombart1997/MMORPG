"""Register inspected additional sheets through the installed Forge API."""
import importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
sys.path.insert(0,str(FORGE))
spec=importlib.util.spec_from_file_location('turnarounds',FORGE/'scripts/seed_turnarounds.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.SPECS=json.loads((ROOT/'concepts_docs/art/asset_turnarounds_v2/full_game_specs.json').read_text())
module.main()
