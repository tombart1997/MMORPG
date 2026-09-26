import bpy
from art_helpers import material, prism, cylinder, blade, remove

steel = bpy.data.materials['Sword_Steel']
brass = bpy.data.materials['Sword_Brass']
leather = bpy.data.materials['Sword_Leather']
edge = material('Sword_HonedEdge', (.62, .70, .75), .90, .24)
dark = material('Sword_BlackenedSteel', (.055, .077, .095), .8, .34)
remove('Sword_Blade', 'Sword_Guard', 'Sword_Grip', 'Sword_Pommel')
blade('Sword_Blade', [(.015, .057, .013), (.105, .057, .013), (.14, .063, .013),
                      (.36, .055, .011), (.64, .042, .009), (.76, .030, .007),
                      (.89, .0007, .0007)], [steel, edge, dark])
prism('Sword_Guard', [(-.19, -.065), (-.183, -.015), (-.11, .055), (-.045, .063),
                      (0, .043), (.045, .063), (.11, .055), (.183, -.015), (.19, -.065),
                      (.148, -.039), (.092, .006), (.036, .007), (0, -.028),
                      (-.036, .007), (-.092, .006), (-.148, -.039)], .052, brass, .003)
cylinder('Sword_Grip', -.118, .18, .024, leather, vertices=16, radius_top=.028)
cylinder('Sword_GripTop', -.03, .024, .031, dark)
cylinder('Sword_GripBase', -.211, .021, .027, brass)
prism('Sword_Pommel', [(-.031, -.218), (0, -.206), (.031, -.218), (.039, -.252),
                       (0, -.295), (-.039, -.252)], .052, dark, .004)
prism('Sword_GuardSeal', [(-.027, .038), (0, .063), (.027, .038), (.021, -.005),
                         (0, -.025), (-.021, -.005)], .068, dark, .002)
print('Structural revision: closed joint, tapered fullered blade, swept guard, shorter grip, faceted pommel')
