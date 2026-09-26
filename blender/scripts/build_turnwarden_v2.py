"""
Ironfield Turnwarden V2 visual prototype.

Place this file beside the existing:
    blender/scripts/build_characters.py

Run from the repository root with Blender 5.x:
    blender --background --python blender/scripts/build_turnwarden_v2.py

It deliberately REUSES build_characters.py's humanoid skeleton and animation
functions, so bone names/hierarchy, NLA clip names, Godot orientation, and the
existing gameplay animation contract remain unchanged.

Output:
    blender/characters/turnwarden_v2.blend
    game/assets/characters/turnwarden_v2.glb
"""

import math
from pathlib import Path
import importlib.util

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "build_characters.py"
spec = importlib.util.spec_from_file_location("ironfield_base_assets", BASE_PATH)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def mat(name, color, metal=0.0, rough=0.65):
    return base.material(name, color, metal, rough)


def rigid_mesh(name, vertices, faces, surface, bone, rig, smooth=False):
    obj = base.mesh_object(
        name, vertices, faces, surface,
        [{bone: 1.0} for _ in vertices], rig
    )
    for p in obj.data.polygons:
        p.use_smooth = smooth
    return obj


def wedge(name, center, size, surface, bone, rig, flare=0.0, forward=0.0):
    """Eight-vertex tapered armor plate. +Y is character forward."""
    cx, cy, cz = center
    sx, sy, sz = size
    top = sx
    bottom = max(0.01, sx + flare)
    y0 = cy - sy
    y1 = cy + sy + forward
    verts = [
        (cx-top, y0, cz+sz), (cx+top, y0, cz+sz),
        (cx-bottom, y0, cz-sz), (cx+bottom, y0, cz-sz),
        (cx-top, y1, cz+sz), (cx+top, y1, cz+sz),
        (cx-bottom, y1, cz-sz), (cx+bottom, y1, cz-sz),
    ]
    faces = [
        (0,1,3,2), (4,6,7,5), (0,4,5,1),
        (2,3,7,6), (0,2,6,4), (1,5,7,3)
    ]
    return rigid_mesh(name, verts, faces, surface, bone, rig)


def diamond_plate(name, center, width, height, depth, surface, bone, rig):
    cx, cy, cz = center
    verts = [
        (cx, cy+depth, cz+height),
        (cx+width, cy+depth, cz),
        (cx, cy+depth, cz-height),
        (cx-width, cy+depth, cz),
        (cx, cy-depth, cz+height*.82),
        (cx+width*.82, cy-depth, cz),
        (cx, cy-depth, cz-height*.82),
        (cx-width*.82, cy-depth, cz),
    ]
    faces = [
        (0,1,2,3), (4,7,6,5),
        (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)
    ]
    return rigid_mesh(name, verts, faces, surface, bone, rig)


def blade_mesh(name, surface, edge):
    """Large readable fantasy longsword, grip centered around origin."""
    # x half-width, y longitudinal coordinate, z thickness.
    profile = [
        (0.035, 0.12, 0.018),
        (0.090, 0.19, 0.022),
        (0.105, 0.72, 0.020),
        (0.082, 1.02, 0.016),
        (0.000, 1.30, 0.006),
    ]
    verts = []
    for w, y, z in profile:
        verts += [(-w, y, z), (w, y, z), (-w, y, -z), (w, y, -z)]
    faces = []
    for i in range(len(profile)-1):
        a = i*4
        b = (i+1)*4
        faces += [
            (a, b, b+1, a+1),       # top
            (a+2, a+3, b+3, b+2),   # bottom
            (a, a+2, b+2, b),       # left edge
            (a+1, b+1, b+3, a+3),   # right edge
        ]
    faces += [(0,1,3,2)]
    obj = base.mesh_object(name, verts, faces, surface)
    obj.data.materials.append(edge)
    for p in obj.data.polygons:
        p.use_smooth = False
        if p.index % 4 in (2,3):
            p.material_index = 1
    return obj


def build_character():
    base.reset()
    rig = base.armature(False)

    # More deliberate palette than the prototype: cool steel, dark leather,
    # muted crimson cloth, warm skin, restrained brass accents.
    skin = mat("TW_Skin", (0.48, 0.285, 0.19), 0.0, 0.72)
    skin_shadow = mat("TW_SkinShadow", (0.30, 0.15, 0.10), 0.0, 0.78)
    cloth = mat("TW_Cloth", (0.18, 0.035, 0.028), 0.0, 0.86)
    cloth_dark = mat("TW_ClothDark", (0.045, 0.055, 0.060), 0.0, 0.90)
    leather = mat("TW_Leather", (0.075, 0.040, 0.024), 0.0, 0.70)
    steel = mat("TW_Steel", (0.25, 0.29, 0.31), 0.82, 0.27)
    steel_dark = mat("TW_DarkSteel", (0.085, 0.105, 0.115), 0.78, 0.34)
    brass = mat("TW_Brass", (0.36, 0.22, 0.065), 0.62, 0.34)
    hair = mat("TW_Hair", (0.025, 0.014, 0.010), 0.0, 0.82)
    eye = mat("TW_Eye", (0.035, 0.055, 0.060), 0.0, 0.40)

    # Athletic human base. Same skeleton; geometry is less tube-like and the
    # silhouette is driven by layered clothing/armor.
    torso_centers = [(0,0,.90),(0,0,1.02),(0,0,1.16),(0,0,1.31),(0,0,1.43),(0,0,1.48)]
    torso_radii = [(.185,.115),(.195,.115),(.175,.105),(.225,.125),(.245,.120),(.135,.090)]
    torso_weights = []
    for _,_,z in torso_centers:
        t = max(0.0, min(1.0, (z-1.0)/.38))
        torso_weights.append(
            {"Hips":1-t*2, "Spine":t*2} if t < .5
            else {"Spine":2-t*2, "Chest":t*2-1}
        )
    base.tube("TW_UnderTunic", torso_centers, torso_radii, cloth_dark,
              torso_weights, rig, 18)

    # Neck/head.
    neck = rig.data.bones["Neck"]
    base.tube("TW_Neck", [neck.head_local, neck.tail_local],
              [.073,.079], skin, [{"Neck":1}]*2, rig, 12)
    head = rig.data.bones["Head"].head_local
    fc = head + Vector((0,.006,.035))
    base.ellipsoid("TW_Head", fc, (.112,.105,.158), skin, "Head", rig, 18, 12)

    # Jaw/chin gives a less spherical face.
    base.ellipsoid("TW_Jaw", fc + Vector((0,.018,-.078)),
                   (.094,.097,.075), skin, "Head", rig, 16, 8)
    base.ellipsoid("TW_Nose", fc + Vector((0,.110,-.008)),
                   (.022,.030,.038), skin_shadow, "Head", rig, 8, 6)
    for side, sign in [("R",1),("L",-1)]:
        ep = fc + Vector((sign*.040,.101,.036))
        base.ellipsoid("TW_Eye_"+side, ep, (.018,.010,.010),
                       eye, "Head", rig, 8, 5)
        base.ellipsoid("TW_Brow_"+side, ep + Vector((0,-.003,.028)),
                       (.031,.014,.008), hair, "Head", rig, 8, 5)
        base.ellipsoid("TW_Ear_"+side, fc + Vector((sign*.112,-.004,-.004)),
                       (.018,.024,.044), skin, "Head", rig, 8, 6)

    # Hair mass + swept locks; stronger silhouette without anime proportions.
    base.ellipsoid("TW_HairCap", fc + Vector((0,-.020,.100)),
                   (.121,.105,.105), hair, "Head", rig, 16, 9)
    for i in range(7):
        x = (i-3)*.035
        base.tube("TW_HairLock_%02d"%i,
                  [(x,.080,1.795),(x + .010*(1 if i%2 else -1),.108,1.745),
                   (x + .018*(1 if i%2 else -1),.100,1.685 + .008*(i%3))],
                  [.025,.020,.002], hair, [{"Head":1}]*3, rig, 6)

    # Limbs retain blended weights and exact existing bones.
    for side, sign in [("R",1),("L",-1)]:
        base.limb(rig, side, "UpperArm", "Forearm", cloth_dark, .075)
        base.limb(rig, side, "Thigh", "Shin", cloth_dark, .098)

        hand = rig.data.bones[f"Hand.{side}"].head_local
        base.ellipsoid("TW_Hand_"+side, hand + Vector((0,.034,-.057)),
                       (.043,.047,.072), skin, f"Hand.{side}", rig, 10, 7)

        foot = rig.data.bones[f"Foot.{side}"].head_local
        base.ellipsoid("Body_Boot_"+side, (foot.x,.090,.090),
                       (.080,.185,.090), leather, f"Foot.{side}", rig, 12, 7)

        # Tall armored boots.
        shin = rig.data.bones[f"Shin.{side}"]
        base.tube("TW_Greave_"+side,
                  [shin.head_local.lerp(shin.tail_local,.28),
                   shin.head_local.lerp(shin.tail_local,.56),
                   shin.head_local.lerp(shin.tail_local,.86)],
                  [.087,.079,.064], steel_dark,
                  [{f"Shin.{side}":1}]*3, rig, 10)
        diamond_plate("TW_Knee_"+side,
                      (sign*.14,.085,.535), .080,.070,.025,
                      steel, f"Shin.{side}", rig)

        # Forearm vambraces.
        fore = rig.data.bones[f"Forearm.{side}"]
        base.tube("TW_Vambrace_"+side,
                  [fore.head_local.lerp(fore.tail_local,.35),
                   fore.head_local.lerp(fore.tail_local,.62),
                   fore.head_local.lerp(fore.tail_local,.90)],
                  [.071,.064,.049], steel_dark,
                  [{f"Forearm.{side}":1}]*3, rig, 10)

        # Layered shoulder armor. R is deliberately larger/asymmetric.
        shoulder = rig.data.bones[f"UpperArm.{side}"].head_local
        scale = 1.15 if side == "R" else .92
        base.ellipsoid("TW_Pauldron_"+side,
                       shoulder + Vector((sign*.025,-.010,.035)),
                       (.145*scale,.135,.070), steel,
                       f"UpperArm.{side}", rig, 12, 7)
        base.ellipsoid("TW_PauldronLower_"+side,
                       shoulder + Vector((sign*.050,.000,-.025)),
                       (.125*scale,.120,.050), steel_dark,
                       f"UpperArm.{side}", rig, 12, 6)

    # Breastplate: several rigid pieces create readable layering and highlights.
    wedge("TW_Breastplate", (0,.105,1.315), (.215,.030,.155),
          steel, "Chest", rig, flare=-.035, forward=.015)
    diamond_plate("TW_ChestBoss", (0,.150,1.335), .085,.095,.018,
                  steel_dark, "Chest", rig)
    # Central brass motif, intentionally original and simple.
    diamond_plate("TW_ChestSigil", (0,.171,1.335), .032,.050,.009,
                  brass, "Chest", rig)

    # Collar / gorget.
    base.tube("TW_Gorget", [(0,0,1.445),(0,0,1.505)],
              [(.145,.105),(.102,.083)], steel_dark,
              [{"Chest":1}]*2, rig, 14)

    # Belt and buckle.
    base.tube("TW_Belt", [(0,0,1.005),(0,0,1.075)],
              [(.205,.125),(.195,.122)], leather,
              [{"Hips":1}]*2, rig, 18)
    diamond_plate("TW_Buckle", (0,.134,1.040), .045,.038,.012,
                  brass, "Hips", rig)

    # Split faulds / coat tails: large silhouette improvement at game camera.
    for side, sign in [("R",1),("L",-1)]:
        base.tube("TW_CoatTail_"+side,
                  [(sign*.115,-.015,.985),(sign*.135,-.010,.840),
                   (sign*.155,-.005,.665)],
                  [(.105,.135),(.125,.145),(.105,.120)], cloth,
                  [{"Hips":1},{f"Thigh.{side}":.35,"Hips":.65},
                   {f"Thigh.{side}":.72,"Hips":.28}], rig, 10)
        # Hip armor plate over the cloth.
        wedge("TW_HipPlate_"+side,
              (sign*.175,.085,.915), (.075,.022,.105),
              steel_dark, "Hips", rig, flare=.020)

    # Small back mantle gives another material layer without a cape simulation.
    wedge("TW_BackMantle", (0,-.125,1.325), (.230,.022,.125),
          cloth, "Chest", rig, flare=.025)

    base.animations(rig, False)
    return rig


def build_sword():
    base.reset()
    steel = mat("TW_SwordSteel", (.30,.34,.36), .86,.23)
    edge = mat("TW_SwordEdge", (.62,.66,.67), .90,.18)
    dark = mat("TW_SwordDark", (.055,.065,.070), .72,.32)
    brass = mat("TW_SwordBrass", (.40,.24,.055), .70,.30)
    grip = mat("TW_SwordGrip", (.055,.025,.018), 0.0,.78)

    blade_mesh("TW_Blade", steel, edge)
    base.tube("TW_Grip", [(0,-.19,0),(0,.10,0)], [.027,.028],
              grip, sides=12)
    # Wide, slightly swept crossguard.
    base.tube("TW_Crossguard",
              [(-.235,.125,-.025),(-.125,.105,0),(0,.100,.012),
               (.125,.105,0),(.235,.125,-.025)],
              [.025,.030,.032,.030,.025], dark, sides=8)
    base.ellipsoid("TW_RainGuard", (0,.145,0), (.075,.040,.032),
                   brass, segments=10, rings=6)
    base.ellipsoid("TW_Pommel", (0,-.235,0), (.043,.052,.034),
                   brass, segments=10, rings=6)
    for i in range(7):
        base.tube("TW_GripWrap_%02d"%i,
                  [(0,-.175+i*.037,0),(0,-.160+i*.037,0)],
                  [.029,.029], brass if i in (0,6) else dark, sides=8)


if __name__ == "__main__":
    rig = build_character()
    base.save_export("turnwarden_v2", rig)

    # Save the weapon separately so the existing equipment/attachment system can
    # swap it exactly like the current Wayfarer sword.
    build_sword()
    base.save_export("turnwarden_v2_sword")

    print("IRONFIELD TURNWARDEN V2 VISUAL BUILD COMPLETE")
