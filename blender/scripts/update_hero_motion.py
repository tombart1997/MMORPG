"""Rebake sword choreography on the current editable hero, preserving mesh/materials.

blender -b blender/characters/warden_high.blend -P blender/scripts/update_hero_motion.py
"""
import importlib.util
from pathlib import Path
import bpy

path=Path(__file__).with_name('build_warden_hero.py')
spec=importlib.util.spec_from_file_location('hero_motion',path)
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
bpy.context.scene.render.fps=60
hero.animate()
hero.wh.export()
