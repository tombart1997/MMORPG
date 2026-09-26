import bpy
import math
from art_helpers import material, prism, mesh_object, remove

steel = bpy.data.materials['Sword_Steel']
brass = material('Sword_Brass', (.33, .19, .055), .82, .3)
dark = bpy.data.materials['Sword_BlackenedSteel']
leather = material('Sword_Leather', (.075, .012, .012), 0, .60)
fuller = material('Sword_Fuller', (.18, .24, .29), .85, .36)
wrap = material('Sword_LeatherWrap', (.11, .023, .018), 0, .56)
garnet = material('Sword_Garnet', (.23, .016, .008), .25, .2)
bpy.data.objects['Sword_Blade'].data.materials[2] = fuller
remove('Sword_Guard', 'Sword_Pommel')
outline = [(-.184, -.054), (-.171, -.003), (-.107, .046), (-.046, .058),
           (0, .036), (.046, .058), (.107, .046), (.171, -.003), (.184, -.054),
           (.145, -.035), (.090, .006), (.037, .010), (0, -.026),
           (-.037, .010), (-.090, .006), (-.145, -.035)]
prism('Sword_Guard', outline, .043, dark, .003)
# Raised brass edging follows the structural sweep; both sides are authored.
strip = [(.030, .044), (.047, .060), (.108, .048), (.173, -.002), (.184, -.049),
         (.164, -.027), (.156, -.004), (.099, .031), (.049, .041)]
for side in (-1, 1):
    for face in (-1, 1):
        trim = prism('Sword_GuardTrim_' + ('L' if side < 0 else 'R') + ('Front' if face < 0 else 'Back'),
                     [(x*side, z) for x,z in strip], .004, brass, .0008)
        trim.location.y = face*.022

pommel_outline = [(-.025, -.214), (0, -.204), (.025, -.214), (.038, -.249),
                  (.021, -.278), (0, -.295), (-.021, -.278), (-.038, -.249)]
prism('Sword_Pommel', pommel_outline, .044, brass, .002)
for face in (-1, 1):
    inset = prism('Sword_PommelInset_' + ('Front' if face < 0 else 'Back'),
                  [(x*.77, -.25+(z+.25)*.77) for x,z in pommel_outline], .004, dark, .001)
    inset.location.y = face*.023
    seal = prism('Sword_SealBorder_' + ('Front' if face < 0 else 'Back'),
                 [(-.018, .034), (0, .050), (.018, .034), (.014, .001), (0, -.014), (-.014, .001)],
                 .003, brass, .0007)
    seal.location.y = face*.035
    # Faceted gemstone, restrained warm focal point, no emissive shader.
    verts = [(0, face*.045, .021), (-.010, face*.038, .020), (0, face*.038, .039),
             (.010, face*.038, .020), (0, face*.038, .001), (0, face*.036, .020)]
    faces = [(0,1,2),(0,2,3),(0,3,4),(0,4,1),(5,2,1),(5,3,2),(5,4,3),(5,1,4)]
    mesh_object('Sword_Crest_' + ('Front' if face < 0 else 'Back'), verts, faces, [garnet])
    pin = prism('Sword_PommelPin_' + ('Front' if face < 0 else 'Back'),
                [(-.007,-.249),(0,-.236),(.007,-.249),(0,-.265)], .003, brass, .0005)
    pin.location.y = face*.026

# A closed helical leather strip with a narrow seam, conforming to tapered grip.
verts = []
steps = 320
turns = 7.5
pitch = .153/turns
width = pitch*.82
for i in range(steps+1):
    angle = 2*math.pi*turns*i/steps
    z = -.196 + .153*i/steps
    for radial, dz in [(0,-width/2),(.0012,-width/2),(.0012,width/2),(0,width/2)]:
        zz = z+dz
        radius = .024 + (zz+.208)/.18*.004 + radial
        verts.append((radius*math.cos(angle), radius*math.sin(angle), zz))
faces = [(3,2,1,0)]
for i in range(steps):
    for j in range(4):
        faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
faces.append(tuple(steps*4+j for j in range(4)))
mesh_object('Sword_GripWrap', verts, faces, [wrap], bevel=.00025)
print('Craft revision: layered swept steel/brass guard, wrap, crest and framed pommel; softer fuller')
