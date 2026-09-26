import bpy
from art_helpers import material, prism, cylinder

# Preserve all existing scenes and create a separate editable study.
study = bpy.data.scenes.new('Oathkeeper_Sword_Study')
bpy.context.window.scene = study
bpy.context.scene.unit_settings.system = 'METRIC'
steel = material('Sword_Steel', (.32, .38, .43), .82, .34)
brass = material('Sword_Brass', (.40, .24, .075), .75, .32)
leather = material('Sword_Leather', (.045, .013, .008), 0, .65)
prism('Sword_Blade', [(-.044, .05), (.044, .05), (.038, .74), (0, .96), (-.038, .74)], .024, steel)
prism('Sword_Guard', [(-.16, -.015), (.16, -.015), (.16, .027), (-.16, .027)], .065, brass)
cylinder('Sword_Grip', -.13, .22, .026, leather)
cylinder('Sword_Pommel', -.27, .065, .042, brass)
print('Rough sword created; ready for first visual inspection')
