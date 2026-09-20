"""Original Ironfield assets. Run via tools/build_assets.ps1, Blender 5.x.

Meters, Z up, +Y facing; glTF conversion gives Godot Y up / -Z facing.
No downloaded geometry, textures, rig generators, or add-ons are used.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector, Quaternion, Euler

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "blender" / "characters"
EXPORT = ROOT / "game" / "assets" / "characters"
FPS = 60
MANIFEST = {"schema": 1, "generator": "blender/scripts/build_characters.py",
            "units": "meters", "godot_forward": "-Z", "assets": {}}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.preferences.filepaths.file_preview_type = "NONE"


def material(name, color, metal=0.0, rough=0.8):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = rough
    return result


def mesh_object(name, vertices, faces, surface, weights=None, rig=None):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(surface)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if rig:
        obj.parent = rig
        modifier = obj.modifiers.new("Skin", "ARMATURE")
        modifier.object = rig
        for index, vertex_weights in enumerate(weights):
            for bone, weight in vertex_weights.items():
                group = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
                group.add([index], weight, "REPLACE")
    return obj


def ellipsoid(name, center, scale, surface, bone=None, rig=None, segments=12, rings=8):
    # Ring topology with single pole vertices, no doubled UV seams or zero-area faces.
    vertices = [(center[0], center[1], center[2] - scale[2])]
    for j in range(1, rings):
        lat = -math.pi / 2 + j * math.pi / rings
        for i in range(segments):
            angle = i * math.tau / segments
            vertices.append((center[0] + scale[0] * math.cos(lat) * math.cos(angle),
                             center[1] + scale[1] * math.cos(lat) * math.sin(angle),
                             center[2] + scale[2] * math.sin(lat)))
    vertices.append((center[0], center[1], center[2] + scale[2]))
    faces = []
    for i in range(segments):
        faces.append((0, 1 + (i + 1) % segments, 1 + i))
    for j in range(rings - 2):
        for i in range(segments):
            a = 1 + j * segments + i
            b = 1 + j * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    last = 1 + (rings - 2) * segments
    for i in range(segments):
        faces.append((last + i, last + (i + 1) % segments, len(vertices) - 1))
    return mesh_object(name, vertices, faces, surface,
                       [{bone: 1.0}] * len(vertices) if bone else None, rig)


def tube(name, centers, radii, surface, ring_weights=None, rig=None, sides=10):
    """Closed tapered tube; adjacent rings share vertices, weights blend at joints."""
    vertices, faces, weights = [], [], []
    for j, (center, radius) in enumerate(zip(centers, radii)):
        center = Vector(center)
        tangent = Vector(centers[min(j + 1, len(centers) - 1)]) - Vector(centers[max(j - 1, 0)])
        tangent.normalize()
        guide = Vector((0, 1, 0)) if abs(tangent.y) < 0.9 else Vector((1, 0, 0))
        axis_x = guide.cross(tangent).normalized()
        axis_y = tangent.cross(axis_x).normalized()
        rx, ry = radius if isinstance(radius, tuple) else (radius, radius)
        for i in range(sides):
            angle = i * math.tau / sides
            vertices.append(center + axis_x * rx * math.cos(angle) + axis_y * ry * math.sin(angle))
            if ring_weights:
                weights.append(ring_weights[j])
    for j in range(len(centers) - 1):
        for i in range(sides):
            a, b = j * sides + i, j * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces += [tuple(reversed(range(sides))), tuple((len(centers) - 1) * sides + i for i in range(sides))]
    return mesh_object(name, vertices, faces, surface, weights, rig)


def rig_definition(creature=False):
    if creature:
        hips, waist, chest, neck, head = (0, 0, .65), (0, -.06, .88), (0, -.03, 1.10), (0, .10, 1.20), (0, .20, 1.32)
    else:
        hips, waist, chest, neck, head = (0, 0, .94), (0, 0, 1.14), (0, 0, 1.37), (0, 0, 1.52), (0, 0, 1.65)
    definition = [("Root", (0, 0, 0), (0, 0, .18), None),
                  ("Hips", hips, waist, "Root"), ("Spine", waist, chest, "Hips"),
                  ("Chest", chest, neck, "Spine"), ("Neck", neck, head, "Chest"),
                  ("Head", head, (0, head[1], head[2] + .2), "Neck")]
    for side, sign in [("R", 1), ("L", -1)]:
        if creature:
            shoulder, elbow, wrist = (sign * .31, 0, 1.1), (sign * .49, .06, .78), (sign * .58, .23, .51)
            hip, knee, ankle = (sign * .19, 0, .64), (sign * .23, .05, .36), (sign * .25, 0, .10)
        else:
            shoulder, elbow, wrist = (sign * .24, 0, 1.43), (sign * .36, 0, 1.16), (sign * .40, .015, .92)
            hip, knee, ankle = (sign * .135, 0, .95), (sign * .14, .015, .53), (sign * .14, 0, .14)
        hand_end = (wrist[0], wrist[1] + .035, wrist[2] - .10)
        definition.extend([(f"UpperArm.{side}", shoulder, elbow, "Chest"),
                           (f"Forearm.{side}", elbow, wrist, f"UpperArm.{side}"),
                           (f"Hand.{side}", wrist, hand_end, f"Forearm.{side}"),
                           (f"Thigh.{side}", hip, knee, "Hips"),
                           (f"Shin.{side}", knee, ankle, f"Thigh.{side}"),
                           (f"Foot.{side}", ankle, (ankle[0], .2, .08), f"Shin.{side}")])
    return definition


def armature(creature):
    data = bpy.data.armatures.new("IronfieldRig")
    rig = bpy.data.objects.new("Rig", data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in rig_definition(creature):
        bone = data.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        if parent:
            bone.parent = data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.show_in_front = True
    return rig


def limb(rig, side, upper, lower, surface, radius):
    a = rig.data.bones[f"{upper}.{side}"]
    b = rig.data.bones[f"{lower}.{side}"]
    centers = [a.head_local.lerp(a.tail_local, t) for t in [0, .3, .65, .87, 1]]
    centers += [b.head_local.lerp(b.tail_local, t) for t in [.13, .35, .7, 1]]
    weights = [{a.name: 1}, {a.name: 1}, {a.name: 1}, {a.name: .85, b.name: .15},
               {a.name: .5, b.name: .5}, {a.name: .15, b.name: .85}, {b.name: 1}, {b.name: 1}, {b.name: 1}]
    radii = [radius * f for f in [.9, 1, .87, .75, .71, .74, .79, .62, .48]]
    tube(f"Body_{upper}_{side}", centers, radii, surface, weights, rig)


def character(creature):
    reset()
    rig = armature(creature)
    skin = material("BarkHide" if creature else "WarmSkin", (.23, .31, .12) if creature else (.56, .34, .22))
    cloth = material("MossHide" if creature else "IndigoLinen", (.17, .23, .07) if creature else (.065, .16, .21))
    leather = material("DarkLeather", (.085, .052, .03))
    trim = material("AgedBronze", (.34, .22, .085), .55, .5)
    bone_mat = material("HornIvory", (.53, .46, .27))
    eye = material("AmberEyes" if creature else "Eyes", (.75, .38, .05) if creature else (.06, .095, .095))
    if creature:
        centers = [(0, 0, .58), (0, -.03, .73), (0, -.09, .92), (0, -.06, 1.12), (0, .03, 1.22)]
        radii = [(.23, .19), (.30, .24), (.39, .29), (.36, .25), (.19, .15)]
    else:
        centers = [(0, 0, .89), (0, 0, 1), (0, 0, 1.15), (0, 0, 1.30), (0, 0, 1.43), (0, 0, 1.48)]
        radii = [(.22, .135), (.20, .12), (.17, .11), (.225, .145), (.26, .13), (.15, .1)]
    weights = []
    for _, _, z in centers:
        lo, hi = ((.73, 1.05) if creature else (1.0, 1.38))
        t = max(0, min(1, (z - lo) / (hi - lo)))
        weights.append({"Hips": 1 - t * 2, "Spine": t * 2} if t < .5 else {"Spine": 2 - t * 2, "Chest": t * 2 - 1})
    tube("Body_Tunic" if not creature else "Body_Hide", centers, radii, cloth, weights, rig, 16)
    neck = rig.data.bones["Neck"]
    tube("Body_Neck", [neck.head_local, neck.tail_local], [.08, .085], skin, [{"Neck": 1}] * 2, rig)
    head = rig.data.bones["Head"].head_local
    face_center = head + Vector((0, .005, .035))
    face_scale = (.22, .18, .20) if creature else (.125, .115, .165)
    ellipsoid("Body_Head", face_center, face_scale, skin, "Head", rig, 16, 10)
    for side, sign in [("R", 1), ("L", -1)]:
        limb(rig, side, "UpperArm", "Forearm", skin if creature else cloth, .135 if creature else .082)
        limb(rig, side, "Thigh", "Shin", skin if creature else leather, .135 if creature else .112)
        hand = rig.data.bones[f"Hand.{side}"].head_local
        ellipsoid("Body_Hand_" + side, hand + Vector((0, .035, -.06)), (.09, .08, .11) if creature else (.045, .048, .075), skin if creature else leather, f"Hand.{side}", rig)
        foot = rig.data.bones[f"Foot.{side}"].head_local
        ellipsoid("Body_Boot_" + side, (foot.x, .085, .095), (.115, .20, .095) if creature else (.082, .17, .095), skin if creature else leather, f"Foot.{side}", rig)
        eye_pos = face_center + Vector((sign * (.087 if creature else .045), .158 if creature else .103, .04))
        ellipsoid("Eye_" + side, eye_pos, (.047, .022, .027) if creature else (.023, .013, .012), eye, "Head", rig, 8, 6)
        # Brow and nose give a readable face rather than a blank primitive head.
        ellipsoid("Brow_" + side, eye_pos + Vector((0, -.003, .027)), (.064, .033, .022) if creature else (.032, .018, .009), cloth if creature else leather, "Head", rig)
        if creature:
            tube("RootHorn_" + side, [face_center + Vector((sign * .14, -.015, .1)),
                 face_center + Vector((sign * .23, -.05, .3)), face_center + Vector((sign * .32, .01, .42))],
                 [.075, .045, .003], bone_mat, [{"Head": 1}] * 3, rig, 7)
            for finger in range(3):
                x = hand.x + (finger - 1) * .06
                tube(f"Claw_{side}_{finger}", [(x, hand.y + .07, hand.z - .04), (x, hand.y + .16, hand.z - .11),
                     (x, hand.y + .24, hand.z - .17)], [.035, .023, .001], bone_mat, [{f"Hand.{side}": 1}] * 3, rig, 6)
            shoulder = rig.data.bones[f"UpperArm.{side}"].head_local
            ellipsoid("MossShoulder_" + side, shoulder + Vector((sign * .01, -.03, .065)), (.20, .21, .10), cloth, "Chest", rig, 9, 6)
        else:
            # Separate coat panels deform with the hips/upper legs, leaving a split.
            x = sign * .12
            tube("CoatPanel_" + side, [(x, -.01, .72), (x, 0, .83), (x, 0, .99)],
                 [(.125, .155), (.12, .15), (.105, .13)], cloth,
                 [{f"Thigh.{side}": .65, "Hips": .35}, {f"Thigh.{side}": .25, "Hips": .75}, {"Hips": 1}], rig)
            shin = rig.data.bones[f"Shin.{side}"]
            tube("BootCuff_" + side, [shin.head_local.lerp(shin.tail_local, .38), shin.head_local.lerp(shin.tail_local, .78)],
                 [.081, .068], leather, [{f"Shin.{side}": 1}] * 2, rig)
            forearm = rig.data.bones[f"Forearm.{side}"]
            tube("Bracer_" + side, [forearm.head_local.lerp(forearm.tail_local, .35), forearm.head_local.lerp(forearm.tail_local, .9)],
                 [.068, .048], leather, [{f"Forearm.{side}": 1}] * 2, rig)
            ellipsoid("Ear_" + side, face_center + Vector((sign * .123, -.006, -.005)), (.025, .03, .055), skin, "Head", rig)
    ellipsoid("Nose", face_center + Vector((0, .174 if creature else .118, -.015)),
              (.095, .065, .058) if creature else (.027, .034, .041), skin, "Head", rig)
    ellipsoid("LowerLip", face_center + Vector((0, .143 if creature else .10, -.075)),
              (.105, .035, .018) if creature else (.033, .012, .009), leather, "Head", rig)
    if creature:
        for i in range(5):
            ellipsoid("BackBurl_%d" % i, ((i % 2 - .5) * .28, -.32, .72 + i * .105), (.14, .09, .12), leather, "Chest", rig, 8, 6)
    else:
        hair = material("ChestnutHair", (.055, .028, .015))
        ellipsoid("Hair_Crown", face_center + Vector((0, -.03, .10)), (.139, .118, .115), hair, "Head", rig)
        for i in range(5):
            x = (i - 2) * .051
            tube("Hair_Lock_%d" % i, [(x, .086, 1.81), (x + .015, .119, 1.75), (x + .021, .113, 1.70 + .01 * (i % 2))],
                 [.036, .031, .003], hair, [{"Head": 1}] * 3, rig, 6)
        tube("Belt", [(0, 0, 1.005), (0, 0, 1.075)], [(.205, .13), (.19, .125)], leather, [{"Hips": 1}] * 2, rig, 16)
        ellipsoid("BeltClasp", (0, .132, 1.04), (.055, .018, .04), trim, "Hips", rig, 8, 6)
        tube("Collar", [(0, 0, 1.47), (0, 0, 1.52)], [(.135, .105), (.092, .08)], leather, [{"Chest": 1}] * 2, rig, 12)
    animations(rig, creature)
    return rig


def world_rotation(rig, bone, degrees):
    basis = rig.data.bones[bone].matrix_local.to_quaternion()
    q = Euler(tuple(math.radians(value) for value in degrees), "XYZ").to_quaternion()
    return basis.inverted() @ q @ basis


def mix_pose(a, b, t):
    return {name: tuple((1-t) * a.get(name, (0, 0, 0))[i] + t * b.get(name, (0, 0, 0))[i]
                       for i in range(3)) for name in a.keys() | b.keys()}


def lowest_boot_height(rig):
    """Evaluate the two rigid-weighted boot meshes without advancing Blender's timeline."""
    matrices = {}
    for bone in rig.data.bones:
        local_rest = bone.parent.matrix_local.inverted() @ bone.matrix_local if bone.parent else bone.matrix_local
        local_pose = local_rest @ rig.pose.bones[bone.name].matrix_basis
        matrices[bone.name] = matrices[bone.parent.name] @ local_pose if bone.parent else local_pose
    heights = []
    for side in ["L", "R"]:
        name = "Foot." + side
        skin_matrix = matrices[name] @ rig.data.bones[name].matrix_local.inverted()
        heights.extend((skin_matrix @ v.co).z for v in bpy.data.objects["Body_Boot_" + side].data.vertices)
    return min(heights)


def attack_pose(t, number, creature):
    ready = {"UpperArm.R": (12, 0, 0), "Forearm.R": (15, 0, 0), "Hand.R": (-22, 0, 0),
             "UpperArm.L": (8, 0, -8), "Forearm.L": (15, 0, 0)}
    if creature:
        wind = {"Chest": (-12, 0, -24), "UpperArm.R": (72, -10, -65), "Forearm.R": (30, 0, 0),
                "Hand.R": (-30, 0, 0), "UpperArm.L": (42, 0, 25), "Forearm.L": (35, 0, 0), "Head": (12, 0, 10)}
        end = {"Chest": (15, 0, 30), "UpperArm.R": (82, 0, 58), "Forearm.R": (5, 0, 0),
               "Hand.R": (-25, 0, 0), "UpperArm.L": (20, 0, -18), "Head": (-8, 0, -10)}
    elif number == 1:
        wind = {"Chest": (0, -6, -25), "UpperArm.R": (78, 0, -60), "Forearm.R": (22, 0, -8),
                "Hand.R": (-95, 0, 0), "UpperArm.L": (35, 0, 20), "Forearm.L": (50, 0, 0), "Head": (0, 0, 15)}
        end = {"Chest": (6, 4, 30), "UpperArm.R": (80, 0, 62), "Forearm.R": (12, 0, 5),
               "Hand.R": (-88, 0, 0), "UpperArm.L": (12, 0, -20), "Forearm.L": (30, 0, 0), "Head": (0, 0, -15)}
    elif number == 2:
        wind = {"Chest": (4, 6, 27), "UpperArm.R": (76, 0, 60), "Forearm.R": (35, 0, 8),
                "Hand.R": (-100, 0, 0), "UpperArm.L": (20, 0, -15), "Forearm.L": (50, 0, 0)}
        end = {"Chest": (0, -5, -30), "UpperArm.R": (85, 0, -62), "Forearm.R": (8, 0, 0),
               "Hand.R": (-90, 0, 0), "UpperArm.L": (30, 0, 15), "Forearm.L": (30, 0, 0)}
    else:
        wind = {"Chest": (-12, 0, -8), "UpperArm.R": (155, 0, -12), "Forearm.R": (15, 0, 0),
                "Hand.R": (-80, 0, 0), "UpperArm.L": (120, 0, 20), "Forearm.L": (40, 0, 0), "Head": (10, 0, 0)}
        end = {"Chest": (22, 0, 8), "UpperArm.R": (52, 0, 15), "Forearm.R": (5, 0, 0),
               "Hand.R": (-80, 0, 0), "UpperArm.L": (40, 0, -10), "Forearm.L": (45, 0, 0), "Head": (-8, 0, 0)}
    # Swing begins just before the active marker, not after damage has already fired.
    if t < .26:
        return mix_pose(ready, wind, min(1, t / .23))
    if t < .55:
        return mix_pose(wind, end, (t - .26) / .29)
    return mix_pose(end, ready, min(1, (t - .55) / .45))


def skill_pose(t, clip):
    """Original Turnwarden poses; combat owns timing and world displacement."""
    ready = {"UpperArm.R": (12, 0, 0), "Forearm.R": (15, 0, 0), "Hand.R": (-22, 0, 0)}
    poses = {
        "skill_guard": ({"Chest": (4, 0, -12), "UpperArm.R": (82, 0, 20), "Forearm.R": (65, 0, -35), "Hand.R": (-70, 0, 0), "UpperArm.L": (70, 0, -15), "Forearm.L": (60, 0, 0), "Thigh.L": (15, 0, 0), "Shin.L": (-20, 0, 0)},
                        {"Chest": (-6, 0, -8), "UpperArm.R": (90, 0, 15), "Forearm.R": (65, 0, -35), "Hand.R": (-70, 0, 0), "UpperArm.L": (70, 0, -15), "Forearm.L": (60, 0, 0)}),
        "skill_step": ({"Chest": (12, 0, -10), "Hips": (8, 0, 0), "Thigh.R": (25, 0, -12), "Shin.R": (-35, 0, 0), "UpperArm.R": (30, 0, -25), "Hand.R": (-50, 0, 0)},
                       {"Chest": (10, 0, 18), "Thigh.L": (-30, 0, 15), "Shin.L": (-20, 0, 0), "Thigh.R": (32, 0, -8), "UpperArm.R": (45, 0, 25), "Hand.R": (-60, 0, 0)}),
        "skill_plant": ({"Chest": (-8, 0, -5), "UpperArm.R": (138, 0, -12), "Forearm.R": (55, 0, 0), "Hand.R": (-85, 0, 0), "UpperArm.L": (85, 0, 20), "Forearm.L": (50, 0, 0)},
                        {"Chest": (27, 0, 0), "UpperArm.R": (18, 0, 8), "Forearm.R": (5, 0, 0), "Hand.R": (10, 0, 0), "UpperArm.L": (20, 0, -15), "Thigh.L": (25, 0, 0), "Shin.L": (-30, 0, 0)}),
        "skill_riposte": ({"Chest": (0, 0, -30), "UpperArm.R": (55, 0, -30), "Forearm.R": (95, 0, 0), "Hand.R": (-90, 0, 0), "UpperArm.L": (40, 0, 35), "Thigh.L": (15, 0, 0)},
                          {"Chest": (13, 0, 15), "UpperArm.R": (95, 0, 0), "Forearm.R": (0, 0, 0), "Hand.R": (-95, 0, 0), "UpperArm.L": (15, 0, -25), "Thigh.L": (25, 0, 0), "Shin.L": (-25, 0, 0)})}
    wind, end = poses[clip]
    if t < .3: return mix_pose(ready, wind, min(1, t / .25))
    if t < .55: return mix_pose(wind, end, (t - .3) / .25)
    return mix_pose(end, ready, (t - .55) / .45)


def animations(rig, creature, only_skills=False):
    rig.animation_data_create()
    clips = {"idle": 2.0, "run": .6, "attack_01": 1.0, "hit": .30, "death": 1.2}
    if not creature:
        clips.update({"attack_02": 1.0, "attack_03": 1.0, "skill_guard": 1.0, "skill_step": 1.0, "skill_plant": 1.0, "skill_riposte": 1.0})
    if only_skills:
        clips = {name: duration for name, duration in clips.items() if name.startswith("skill_")}
    for clip, duration in clips.items():
        action = bpy.data.actions.new(clip)
        rig.animation_data.action = action
        last_frame = round(duration * FPS)
        for frame in range(last_frame + 1):
            t = frame / last_frame
            pose, root_height = {}, 0
            if clip == "idle":
                pose = {"Chest": (math.sin(t * math.tau) * 1.4, 0, 0), "Head": (0, 0, math.sin(t * math.tau) * 2),
                        "UpperArm.R": (12, 0, 0), "Forearm.R": (15, 0, 0), "Hand.R": (-22, 0, 0),
                        "Forearm.L": (10, 0, 0)}
            elif clip == "run":
                cycle = t * math.tau
                pose["Hips"] = (5, 0, math.sin(cycle) * 3)
                pose["Chest"] = (5, 0, -math.sin(cycle) * 5)
                for side, sign in [("R", 1), ("L", -1)]:
                    wave = math.sin(cycle) * sign
                    pose[f"Thigh.{side}"] = (wave * 38, 0, 0)
                    pose[f"Shin.{side}"] = (-max(0, -wave) * 65, 0, 0)
                    pose[f"Foot.{side}"] = (-5 - wave * 38 + max(0, -wave) * 65, 0, 0)
                    pose[f"UpperArm.{side}"] = (-wave * 25 + 12, 0, 0)
                    pose[f"Forearm.{side}"] = (30, 0, 0)
                    pose[f"Hand.{side}"] = (-25, 0, 0)
            elif clip.startswith("attack"):
                pose = attack_pose(t, int(clip[-2:]), creature)
                pose["Thigh.L"] = (8 * math.sin(math.pi * t), 0, 0)
                pose["Shin.L"] = (-12 * math.sin(math.pi * t), 0, 0)
            elif clip.startswith("skill_"):
                pose = skill_pose(t, clip)
            elif clip == "hit":
                pulse = math.sin(math.pi * t) ** 2
                pose = {"Chest": (-15 * pulse, 0, -7 * pulse), "Head": (-12 * pulse, 0, 6 * pulse),
                        "UpperArm.L": (10 * pulse, 0, -12 * pulse)}
            elif clip == "death":
                collapse = max(0, min(1, (t - .15) / .6))
                pose = {"Root": (collapse * 88, 0, collapse * 12), "Hips": (-10 * math.sin(t * math.pi), 0, 0),
                        "UpperArm.R": (15, 0, -35 * collapse), "UpperArm.L": (10, 0, 40 * collapse),
                        "Shin.L": (-30 * collapse, 0, 0), "Shin.R": (-15 * collapse, 0, 0)}
                root_height = .14 * collapse
            for bone in rig.pose.bones:
                bone.rotation_mode = "QUATERNION"
                bone.rotation_quaternion = world_rotation(rig, bone.name, pose.get(bone.name, (0, 0, 0)))
                bone.location = (0, 0, 0)
                if bone.name == "Root":
                    bone.location = rig.data.bones[bone.name].matrix_local.to_3x3().inverted() @ Vector((0, 0, root_height))
            if clip == "run":
                # Keep the lowest sole close to the floor rather than jogging in midair.
                # This is vertical pose motion only; forward locomotion stays in Godot.
                height = -lowest_boot_height(rig) + .015 * abs(math.sin(t * math.tau * 2))
                rig.pose.bones["Root"].location = rig.data.bones["Root"].matrix_local.to_3x3().inverted() @ Vector((0, 0, height))
            for bone in rig.pose.bones:
                bone.keyframe_insert("rotation_quaternion", frame=frame, group=bone.name)
                bone.keyframe_insert("location", frame=frame, group=bone.name)
        # One NLA track per named clip is the explicit glTF export contract.
        track = rig.animation_data.nla_tracks.new()
        track.name = clip
        strip = track.strips.new(clip, 0, action)
        strip.action_frame_start = 0
        strip.action_frame_end = last_frame
        track.mute = True
    rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.rotation_quaternion = Quaternion()
        bone.location = (0, 0, 0)
    bpy.context.scene.frame_set(0)
    return clips


def sword():
    reset()
    steel = material("SwordSteel", (.38, .47, .52), .75, .3)
    edge = material("SwordEdge", (.65, .72, .74), .8, .25)
    bronze = material("SwordBronze", (.39, .25, .075), .65, .4)
    grip = material("WrappedGrip", (.07, .035, .023))
    # Grip origin at zero; blade extends +Y (Godot -Z). Broad diamond section.
    centers = [(0, y, 0) for y in [.11, .20, .86, 1.08]]
    blade = tube("Blade", centers, [(.065, .016), (.072, .017), (.038, .013), (.001, .001)], steel, sides=4)
    blade.data.materials.append(edge)
    for face in blade.data.polygons:
        face.use_smooth = False
        face.material_index = face.index % 2
    tube("Grip", [(0, -.14, 0), (0, .09, 0)], [.024, .025], grip, sides=10)
    tube("Crossguard", [(-.18, .12, -.02), (-.09, .10, 0), (.09, .10, 0), (.18, .12, -.02)], [.024] * 4, bronze, sides=6)
    ellipsoid("Pommel", (0, -.17, 0), (.035, .045, .025), bronze, segments=8, rings=6)
    for i in range(6):
        tube("GripWrap_%d" % i, [(0, -.12 + i * .032, 0), (0, -.11 + i * .032, 0)], [.026, .026], bronze, sides=8)


def armor():
    reset()
    leather = material("GuardLeather", (.17, .095, .04))
    bronze = material("GuardBronze", (.37, .25, .1), .45, .55)
    # Origin is Chest bone head. Rigid upper-body guard, independent of base tunic.
    ellipsoid("Breastguard", (0, .125, -.035), (.22, .055, .16), leather, segments=12, rings=8)
    for sign in [-1, 1]:
        ellipsoid("ShoulderGuard", (sign * .235, -.01, .065), (.13, .15, .07), leather, segments=10, rings=6)
        for i in range(3):
            ellipsoid("Rivet", (sign * (.055 + .045 * i), .176, .035), (.013, .009, .013), bronze, segments=6, rings=4)


def validate(rig=None):
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for obj in meshes:
        obj.data.calc_loop_triangles()
        assert all(p.area > 1e-10 for p in obj.data.polygons), f"Degenerate face: {obj.name}"
        assert tuple(round(v, 6) for v in obj.scale) == (1, 1, 1), obj.name
        if rig:
            for vertex in obj.data.vertices:
                total = sum(group.weight for group in vertex.groups)
                assert abs(total - 1) < .001 and len(vertex.groups) <= 4, (obj.name, vertex.index, total)
    return {"vertices": sum(len(o.data.vertices) for o in meshes),
            "triangles": sum(len(o.data.loop_triangles) for o in meshes), "meshes": len(meshes)}


def save_export(name, rig=None, save_source=True):
    SOURCE.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    info = validate(rig)
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 120
    if save_source:
        bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / (name + ".blend")))
    bpy.ops.export_scene.gltf(filepath=str(EXPORT / (name + ".glb")), export_format="GLB",
                             export_yup=True, export_skins=True, export_animations=bool(rig),
                             export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                             export_apply=False, export_extras=True)
    if rig:
        info["bones"] = [b.name for b in rig.data.bones]
        info["clips"] = {track.name: (track.strips[0].action_frame_end - track.strips[0].action_frame_start) / FPS
                         for track in rig.animation_data.nla_tracks if len(track.strips) == 1}
        info["attack_markers_normalized"] = {"active": .30, "recovery": .55}
        info["run_reference_speed"] = 3.2 if name == "briarling" else 5.5
    MANIFEST["assets"][name] = info
    print("VALIDATED", name, json.dumps(info))


if __name__ == "__main__":
    player = character(False)
    save_export("traveler", player)
    enemy = character(True)
    save_export("briarling", enemy)
    sword()
    save_export("wayfarer_sword")
    armor()
    save_export("traveler_guard")
    (EXPORT / "manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n", encoding="utf-8")
    print("IRONFIELD ASSET BUILD COMPLETE")
